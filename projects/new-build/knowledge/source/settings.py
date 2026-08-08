"""
settings.py
============
Every tunable knob in the recommendation engine, in one place, so they can
be adjusted from the dashboard's Settings page instead of requiring a code
change + rebuild each time. SETTINGS_SCHEMA is the single source of truth:
default value, type, slider bounds, and a plain-language explanation shown
on the page itself.

Values are stored as one JSON blob in db's meta table (key "settings").
Anything not yet saved falls back to its default - so adding a new
tunable here later doesn't require a migration, every existing deployment
just sees the new default until someone changes it.
"""

import json

import db

SETTINGS_SCHEMA = {
    "favorite_bonus": {"default": 5.0, "type": "float", "min": 0.0, "max": 50.0,
        "section": "Taste profile", "label": "Favorite bonus",
        "help": "Flat bonus added every time a favorited performer/studio/tag appears in a scene."},
    "rating_weight": {"default": 3.0, "type": "float", "min": 0.0, "max": 20.0,
        "section": "Taste profile", "label": "Rating weight",
        "help": "Multiplier on a scene's rating (0-1) when computing its interest score."},
    "play_weight": {"default": 0.4, "type": "float", "min": 0.0, "max": 5.0,
        "section": "Taste profile", "label": "Play count weight",
        "help": "Per-play bonus toward a scene's interest score, capped at the play cap below."},
    "play_cap": {"default": 10, "type": "int", "min": 0, "max": 100,
        "section": "Taste profile", "label": "Play count cap",
        "help": "Maximum plays counted toward the play-count bonus."},
    "o_weight": {"default": 0.4, "type": "float", "min": 0.0, "max": 5.0,
        "section": "Taste profile", "label": "O-counter weight",
        "help": "Per-count bonus toward a scene's interest score, capped at the cap below."},
    "o_cap": {"default": 10, "type": "int", "min": 0, "max": 100,
        "section": "Taste profile", "label": "O-counter cap",
        "help": "Maximum o-counter counted toward the bonus."},
    "entity_rating_weight": {"default": 1.5, "type": "float", "min": 0.0, "max": 5.0,
        "section": "Taste profile", "label": "Entity rating weight",
        "help": "How much a performer/studio's own Stash rating amplifies their contribution to your taste profile. 1.5 = a performer you rated 100 counts ~2.5x more per scene than one you never rated. Uses your 150 rated performers and any rated studios - previously completely ignored by the profile."},
    "entity_ocounter_weight": {"default": 0.5, "type": "float", "min": 0.0, "max": 5.0,
        "section": "Taste profile", "label": "Entity o-counter weight",
        "help": "Flat multiplier bonus if a performer has any o-counter recorded against them in Stash (performer-level, distinct from scene-level). Genuine engagement signal that was previously unused."},
    "volume_dampening_exponent": {"default": 0.5, "type": "float", "min": 0.1, "max": 1.0,
        "section": "Taste profile", "label": "Volume dampening",
        "help": "Compresses repeat-appearance volume so a studio you own 80 scenes of doesn't automatically outweigh one you've favorited but only own 3 of. 1.0 = no compression (raw sum, the old behavior); 0.5 = square root; lower = more aggressive. Doesn't touch the favorite bonus, which is now flat per entity regardless of appearance count."},
    "top_performers": {"default": 40, "type": "int", "min": 5, "max": 200,
        "section": "Candidate discovery", "label": "Top performers tracked",
        "help": "How many of your highest-weighted performers get queried against StashDB each refresh."},
    "top_studios": {"default": 15, "type": "int", "min": 1, "max": 100,
        "section": "Candidate discovery", "label": "Top studios tracked",
        "help": "How many of your highest-weighted studios get queried against StashDB each refresh."},
    "per_entity": {"default": 25, "type": "int", "min": 5, "max": 100,
        "section": "Candidate discovery", "label": "Scenes fetched per performer/studio",
        "help": "How many of each performer/studio's newest StashDB scenes are pulled as candidates."},
    "top_tags": {"default": 30, "type": "int", "min": 0, "max": 200,
        "section": "Candidate discovery", "label": "Top tags tracked",
        "help": "How many of your highest-weighted tags also get queried directly against StashDB each refresh - this is what lets a scene from a performer/studio you've never seen enter the pool at all, purely on tag match. 0 disables tag-based fetching."},

    "tag_match_weight": {"default": 1.0, "type": "float", "min": 0.0, "max": 5.0,
        "section": "Scoring", "label": "Tag match weight multiplier",
        "help": "Multiplier applied to tag-profile weight when a candidate's tags overlap yours."},
    "recency_window_days": {"default": 60, "type": "int", "min": 0, "max": 365,
        "section": "Scoring", "label": "Recency bonus window (days)",
        "help": "Scenes released within this many days get a bonus, decaying to 0 at the edge."},
    "recency_weight": {"default": 0.05, "type": "float", "min": 0.0, "max": 1.0,
        "section": "Scoring", "label": "Recency bonus strength",
        "help": "Per-day bonus inside the recency window."},

    "embedding_weight": {"default": 0.4, "type": "float", "min": 0.0, "max": 2.0,
        "section": "Content embeddings (Tier 3)", "label": "Embedding affinity weight",
        "help": "How much the Tier 1 heuristic score weighs tag co-occurrence affinity - whether a candidate's tags keep company, in your library, with tags you already like, even without exact overlap. 0 disables its contribution to the heuristic (Tier 2 can still learn from it as a feature either way)."},
    "performer_embedding_weight": {"default": 0.4, "type": "float", "min": 0.0, "max": 2.0,
        "section": "Content embeddings (Tier 3)", "label": "Performer affinity weight",
        "help": "Same idea, for performers instead of tags - whether a candidate's performers tend to appear in scenes alongside performers you already like, even with zero overlap. Catches an unfamiliar performer who frequently collaborates with ones you rate highly."},

    "wildcard_fraction": {"default": 0.2, "type": "float", "min": 0.0, "max": 1.0,
        "section": "Page composition", "label": "Wildcard slice of the page",
        "help": "Fraction of each /recommendations page reserved for wildcard categories."},
    "explore_fraction": {"default": 0.1667, "type": "float", "min": 0.0, "max": 1.0,
        "section": "Page composition", "label": "Explore slice of the page",
        "help": "Fraction of each page reserved for low-confidence (uncertain) picks - this is what lets feedback actually correct the model instead of just confirming it."},
    "wildcard_per_entity": {"default": 40, "type": "int", "min": 5, "max": 200,
        "section": "Page composition", "label": "Scenes fetched per wildcard category",
        "help": "How many newest scenes are pulled per wildcard tag/studio."},
    "wildcard_base_score": {"default": 5.0, "type": "float", "min": 0.0, "max": 50.0,
        "section": "Page composition", "label": "Wildcard base score",
        "help": "Flat score per matched wildcard category, before the recency bonus."},

    "min_examples": {"default": 50, "type": "int", "min": 10, "max": 1000,
        "section": "Tier 2 training", "label": "Min decisions to train",
        "help": "Tier 2 won't train until at least this many download/skip decisions are logged."},
    "min_positive": {"default": 10, "type": "int", "min": 2, "max": 200,
        "section": "Tier 2 training", "label": "Min downloads to train",
        "help": "Tier 2 won't train until at least this many of those decisions are downloads."},

    "max_download_gb": {"default": 20, "type": "int", "min": 1, "max": 500,
        "section": "Downloads", "label": "Max download size (GB)",
        "help": "Hard cap - releases larger than this are never grabbed, even when every "
                "search result exceeds it. The main defence against megapacks/siterips "
                "flooding TorBox and Stash with hundreds of scenes from one click."},
}


def get_all() -> dict:
    """Every setting, with anything unsaved falling back to its default."""
    raw = db.get_meta("settings")
    saved = json.loads(raw) if raw else {}
    return {key: saved.get(key, spec["default"]) for key, spec in SETTINGS_SCHEMA.items()}


def get(key: str):
    return get_all()[key]


def set_values(updates: dict) -> dict:
    """Validates + clamps each update to its schema bounds, merges into
    whatever's already saved, and persists. Unknown keys are ignored
    rather than raising - keeps this safe to call from a form post."""
    current = get_all()
    for key, raw_value in updates.items():
        spec = SETTINGS_SCHEMA.get(key)
        if spec is None:
            continue
        try:
            value = int(raw_value) if spec["type"] == "int" else float(raw_value)
        except (TypeError, ValueError):
            continue
        value = max(spec["min"], min(spec["max"], value))
        current[key] = value
    db.set_meta("settings", json.dumps(current))
    return current


def reset_defaults() -> dict:
    defaults = {k: v["default"] for k, v in SETTINGS_SCHEMA.items()}
    db.set_meta("settings", json.dumps(defaults))
    return defaults
