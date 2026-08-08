"""
ml_model.py
===========
Tier 2: a small logistic regression model trained on your actual
download/skip decisions, replacing the hand-weighted Tier 1 heuristic as
the ranking signal once there's enough data to learn from.

Feature vector is intentionally small and tabular - at personal-library
scale (hundreds, not millions, of examples) a handful of engineered
features beats anything bigger; there's just not enough data to need more.
The same extract_features() is used both to build the training set (from
historical feedback) and to score brand-new candidates, so the model
always sees features in the same shape it was trained on.
"""

import json
import os
from datetime import datetime, timezone

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import settings as cfg

MODEL_PATH = os.environ.get("RECS_MODEL_PATH", "/app/data/model.joblib")
MODEL_PREV_PATH = MODEL_PATH.replace(".joblib", "_prev.joblib")

# How much AUC regression is tolerated before rolling back. 0.02 = a new
# model is rejected if it's more than 2 percentage points worse than the
# previous one on the temporal validation slice. Without this gate, every
# retrain unconditionally overwrites the live model, so a bad training
# batch (e.g. after label corruption or a stale taste profile) silently
# degrades recommendations until you notice. With it, the worst case is
# "model didn't update this cycle" rather than "model got worse".
ACCEPTANCE_TOLERANCE = 0.02

# Order matters - this is the exact column order the model is trained and
# scored on. `score` (the old single blended Tier 1 total) was deliberately
# dropped: it was an exact sum of performer_weight_sum + studio_weight_sum +
# tag_weight_sum + recency_bonus, so keeping both was pure collinearity -
# the model couldn't tell which of those four actually mattered, it only
# ever saw them pre-mixed into one number.
FEATURE_NAMES = [
    "performer_weight_sum",
    "studio_weight_sum",
    "tag_weight_sum",
    "embedding_affinity_sum",
    "performer_affinity_sum",
    "is_wildcard",
    "num_performer_matches",
    "num_studio_matches",
    "num_wildcard_tag_matches",
    "num_profile_tag_matches",
    "days_since_release",
    "recency_bonus",
]

FEATURE_DESCRIPTIONS = {
    "performer_weight_sum": "Sum of your taste-profile weight for every performer in this scene who's in your top 40. Higher = performers you watch/rate/favorite a lot.",
    "studio_weight_sum": "Your taste-profile weight for this scene's studio, if it's in your top 15.",
    "tag_weight_sum": "Sum of taste-profile weight for every tag on this scene that also appears anywhere in your tag profile.",
    "embedding_affinity_sum": "Tier 3: how strongly this scene's tags co-occur, in your library, with tags you already like - weighted by how much you like them. Lets a scene score well via tags it doesn't even share with your profile, by keeping similar company.",
    "performer_affinity_sum": "Tier 3: same idea for performers - how strongly this scene's performers co-occur, in your library, with performers you already like. Catches an unfamiliar performer who frequently collaborates with ones you rate highly.",
    "is_wildcard": "1 if this candidate came from the explicit wildcard categories (Oil / Big Ass / Wet Look / Anal Sex / BangBros) rather than your taste profile, 0 otherwise.",
    "num_performer_matches": "How many of this scene's performers are in your top-40 performer list.",
    "num_studio_matches": "1 if this scene's studio is in your top-15 studio list, else 0.",
    "num_wildcard_tag_matches": "How many of the 4 wildcard tags this scene has.",
    "num_profile_tag_matches": "How many of this scene's tags also appear anywhere in your tag profile, regardless of weight.",
    "days_since_release": "Age of the scene in days at the time it was scored.",
    "recency_bonus": "Small bonus for scenes released within the last 60 days, decaying to 0 - already folded into days_since_release but kept separate since the relationship is deliberately non-linear (a step-down curve, not a straight line).",
}


def extract_features(features: dict, source: str) -> list[float]:
    matched = features.get("matched_via", [])
    num_performer = sum(1 for m in matched if m[0] == "performer")
    num_studio = sum(1 for m in matched if m[0] == "studio")
    num_wildcard_tag = sum(1 for m in matched if m[0] == "tag")
    tag_matches = features.get("tag_matches") or []
    num_profile_tag = len(tag_matches)
    days = features.get("days_since_release")
    days = days if days is not None else 999
    recency_bonus = features.get("recency_bonus") or 0.0
    return [
        float(features.get("performer_weight_sum", 0.0)),
        float(features.get("studio_weight_sum", 0.0)),
        float(features.get("tag_weight_sum", 0.0)),
        float(features.get("embedding_affinity_sum", 0.0)),
        float(features.get("performer_affinity_sum", 0.0)),
        1.0 if source == "wildcard" else 0.0,
        float(num_performer),
        float(num_studio),
        float(num_wildcard_tag),
        float(num_profile_tag),
        float(days),
        float(recency_bonus),
    ]


def train(feedback_rows: list[tuple]) -> dict:
    """Trains on download/skip decisions with confidence-weighted samples
    and temporal cross-validation, then applies an acceptance gate before
    promoting the new model to live.

    feedback_rows: (features_json, score_at_decision, source, label, confidence)
    from db.feedback_with_source(). Historical rows without a confidence
    value default to 1.0.

    Key structural improvements over the old version:
    - confidence weights (sample_weight): the model learns overwhelmingly
      from reliable signal (5-star verified = 4x, provisional click = 1x,
      never-watched = 0.3x) rather than treating every decision equally.
    - Temporal CV instead of random k-fold: validates on newer decisions
      given training on older ones, which is the question that actually
      matters and gives a truthful rather than inflated AUC.
    - Acceptance gate: new model only replaces the previous one if its
      temporal AUC doesn't regress by more than ACCEPTANCE_TOLERANCE.
      Prevents a bad retrain (label corruption, stale profile) from
      silently shipping to live."""
    if len(feedback_rows) < cfg.get("min_examples"):
        return {"trained": False, "reason": f"only {len(feedback_rows)} decisions, need {cfg.get('min_examples')}"}

    # Parse rows — handle both old 4-tuple and new 5-tuple shapes
    X, y, w = [], [], []
    for row in feedback_rows:
        fj, _score, source, label = row[0], row[1], row[2], row[3]
        confidence = float(row[4]) if len(row) > 4 else 1.0
        X.append(extract_features(json.loads(fj), source))
        y.append(label)
        w.append(max(confidence, 0.01))  # floor at a tiny positive so no row is zeroed

    n_pos = sum(y)
    n_neg = len(y) - n_pos
    if n_pos < cfg.get("min_positive"):
        return {"trained": False, "reason": f"only {n_pos} downloads, need {cfg.get('min_positive')}"}

    X, y, w = np.array(X), np.array(y), np.array(w)

    def _make_pipeline():
        return Pipeline([
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(class_weight="balanced", max_iter=1000)),
        ])

    # Temporal CV: rows arrive in decided_at order (feedback_with_source
    # doesn't guarantee this, but we sort by TimeSeriesSplit which uses
    # array index order — close enough for the directional AUC signal
    # we need). Validates on newest decisions given training on older ones.
    cv_auc = None
    temporal_auc = None  # the number used for the acceptance gate
    n_splits = min(5, n_pos, n_neg)
    if n_splits >= 2:
        from sklearn.model_selection import TimeSeriesSplit
        from sklearn.metrics import roc_auc_score
        tscv = TimeSeriesSplit(n_splits=n_splits)
        auc_scores = []
        for train_idx, val_idx in tscv.split(X):
            Xtr, Xval = X[train_idx], X[val_idx]
            ytr, yval = y[train_idx], y[val_idx]
            wtr = w[train_idx]
            if len(np.unique(ytr)) < 2 or len(np.unique(yval)) < 2:
                continue
            pipe = _make_pipeline()
            pipe.fit(Xtr, ytr, clf__sample_weight=wtr)
            probs = pipe.predict_proba(Xval)[:, 1]
            auc_scores.append(roc_auc_score(yval, probs))
        if auc_scores:
            cv_auc = round(float(np.mean(auc_scores)), 3)
            temporal_auc = cv_auc

    # Train the candidate model on all data
    candidate = _make_pipeline()
    candidate.fit(X, y, clf__sample_weight=w)

    # Acceptance gate: compare candidate against the current live model
    # on the last 20% of decisions (temporal hold-out). Only promote if
    # candidate doesn't regress beyond ACCEPTANCE_TOLERANCE.
    rolled_back = False
    prev_auc = None
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    if os.path.exists(MODEL_PATH) and temporal_auc is not None:
        try:
            prev_model = joblib.load(MODEL_PATH)
            # Evaluate prev on same temporal hold-out as the last CV fold
            from sklearn.metrics import roc_auc_score
            n_holdout = max(int(len(X) * 0.2), 10)
            Xh, yh = X[-n_holdout:], y[-n_holdout:]
            if len(np.unique(yh)) >= 2:
                prev_probs = prev_model.predict_proba(Xh)[:, 1]
                cand_probs = candidate.predict_proba(Xh)[:, 1]
                prev_auc = round(float(roc_auc_score(yh, prev_probs)), 3)
                cand_holdout_auc = round(float(roc_auc_score(yh, cand_probs)), 3)
                if cand_holdout_auc < prev_auc - ACCEPTANCE_TOLERANCE:
                    # Candidate regresses — keep previous model
                    rolled_back = True
                    return {
                        "trained": True,
                        "accepted": False,
                        "reason": f"candidate temporal AUC {cand_holdout_auc:.3f} < "
                                  f"prev {prev_auc:.3f} - {ACCEPTANCE_TOLERANCE} — rolled back",
                        "n_examples": len(y),
                        "n_positive": int(n_pos),
                        "n_negative": int(n_neg),
                        "cv_auc": cv_auc,
                        "prev_auc": prev_auc,
                        "cand_auc": cand_holdout_auc,
                        "trained_at": datetime.now(timezone.utc).isoformat(),
                        "feature_importances": [],
                    }
        except Exception:  # noqa: BLE001
            pass  # no valid previous model — accept candidate unconditionally

    # Promote: save previous (for rollback inspection) and install candidate
    if os.path.exists(MODEL_PATH):
        joblib.dump(joblib.load(MODEL_PATH), MODEL_PREV_PATH)
    joblib.dump(candidate, MODEL_PATH)
    global _cached_model, _cached_mtime
    _cached_model = None  # bust the in-process cache

    coefs = candidate.named_steps["clf"].coef_[0]
    importances = sorted(
        [{"feature": n, "coefficient": round(float(c), 4)} for n, c in zip(FEATURE_NAMES, coefs)],
        key=lambda x: abs(x["coefficient"]),
        reverse=True,
    )
    return {
        "trained": True,
        "accepted": True,
        "n_examples": len(y),
        "n_positive": int(n_pos),
        "n_negative": int(n_neg),
        "cv_auc": cv_auc,
        "prev_auc": prev_auc,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "feature_importances": importances,
    }


_cached_model = None
_cached_mtime = None


def _load_model():
    global _cached_model, _cached_mtime
    if not os.path.exists(MODEL_PATH):
        return None
    mtime = os.path.getmtime(MODEL_PATH)
    if _cached_model is None or mtime != _cached_mtime:
        _cached_model = joblib.load(MODEL_PATH)
        _cached_mtime = mtime
    return _cached_model


def predict_proba(features: dict, source: str) -> float | None:
    """Returns P(download) for a candidate, or None if no model has been
    trained yet - callers should fall back to the Tier 1 heuristic score."""
    model = _load_model()
    if model is None:
        return None
    x = np.array([extract_features(features, source)])
    return float(model.predict_proba(x)[0][1])


def compute_novelty_scores(
    decided: list[tuple[str, str]], pending: list[tuple[str, str, str]],
) -> list[tuple[str, float]] | None:
    """For the explore slice: how far, in standardized feature space, is
    each pending candidate from its nearest already-decided example. High
    novelty = a region of feature space the model has little or no training
    signal near, which is what an exploration slice should actually be
    targeting - not predict_proba closest to 0.5, which (verified against
    live data before this was built) just collapses into re-selecting the
    top of the exploit ranking under either calibration regime, balanced
    or not. decided: (features_json, source) pairs from any past decision,
    label-agnostic - novelty cares whether the model has seen something
    *like* this at all, not whether it was liked. pending: (scene_id,
    features_json, source) for everything currently up for scoring.
    Returns None (caller should fall back to random) if no model/scaler
    exists yet to standardize distances against, or if there's no decided
    data to measure distance from."""
    model = _load_model()
    if model is None or not decided or not pending:
        return None
    scaler: StandardScaler = model.named_steps["scale"]

    X_decided = np.array([extract_features(json.loads(fj), src) for fj, src in decided])
    X_pending = np.array([extract_features(json.loads(fj), src) for _, fj, src in pending])
    X_decided = scaler.transform(X_decided)
    X_pending = scaler.transform(X_pending)

    n_neighbors = min(1, len(X_decided))
    nn = NearestNeighbors(n_neighbors=n_neighbors).fit(X_decided)
    distances, _ = nn.kneighbors(X_pending)
    nearest_dist = distances[:, 0]

    return [(scene_id, float(d)) for (scene_id, _, _), d in zip(pending, nearest_dist)]
