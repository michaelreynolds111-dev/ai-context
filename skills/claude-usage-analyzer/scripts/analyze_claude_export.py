#!/usr/bin/env python3
"""
analyze_claude_export.py — Claude Usage Analyzer

Parses a Claude.ai data export (conversations.json) and produces structured
analysis reports: usage patterns, feature signals, temporal patterns, topic
clusters, repeat-task detection, and conversation-length distribution.

Designed to run locally. Does NOT send any data externally. Outputs aggregated
insights only — no raw conversation content is written to the reports.

Usage:
    python3 analyze_claude_export.py \
        --input /path/to/conversations.json \
        --output /path/to/analysis/

The script handles large files via streaming JSON parsing (ijson) if available,
falling back to standard json.load for smaller files.

Schema notes (Claude export format, verified Aug 2026):
    conversations.json is an array of conversation objects. Each has:
      - uuid: str
      - name: str (conversation title)
      - created_at: ISO timestamp
      - updated_at: ISO timestamp
      - chat_messages: array of message objects
        - sender: "human" | "assistant"
        - text: str (message content)
        - content: array (newer format, may contain text blocks, tool_use, etc.)
        - created_at: ISO timestamp
        - attachments: array (file upload metadata)
        - files: array (file references)
        - model: str (sometimes present)
      - project: str (project UUID, if part of a project) — may be absent
      - artifacts: array (if artifacts were created) — may be absent in some exports
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

# Optional: ijson for streaming large files
try:
    import ijson
    HAS_IJSON = True
except ImportError:
    HAS_IJSON = False

# ─── Helpers ────────────────────────────────────────────────────────────────

def extract_text(message):
    """Extract text from a message, handling both old (text) and new (content) formats."""
    if message.get("text"):
        return message["text"]
    if message.get("content"):
        parts = []
        for block in message["content"]:
            if isinstance(block, dict):
                if block.get("type") == "text" and block.get("text"):
                    parts.append(block["text"])
                elif block.get("type") == "tool_use":
                    parts.append(f"[TOOL_USE: {block.get('name', 'unknown')}]")
                elif block.get("type") == "tool_result":
                    parts.append("[TOOL_RESULT]")
            elif isinstance(block, str):
                parts.append(block)
        return " ".join(parts)
    return ""


def parse_timestamp(ts):
    """Parse an ISO timestamp, return datetime or None."""
    if not ts:
        return None
    try:
        # Handle 'Z' suffix
        ts = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


def load_conversations(filepath):
    """Load conversations from JSON. Uses ijson for streaming if available and file is large."""
    file_size = os.path.getsize(filepath)
    if HAS_IJSON and file_size > 50 * 1024 * 1024:  # > 50MB
        print(f"  [streaming] File is {file_size / 1024 / 1024:.1f} MB, using ijson...", file=sys.stderr)
        conversations = []
        with open(filepath, "rb") as f:
            for conv in ijson.items(f, "item"):
                conversations.append(conv)
        return conversations
    else:
        print(f"  [standard] Loading {file_size / 1024 / 1024:.1f} MB file...", file=sys.stderr)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "conversations" in data:
            return data["conversations"]
        else:
            return data if isinstance(data, list) else [data]


# ─── Analysis functions ─────────────────────────────────────────────────────

def analyze_basic_stats(conversations):
    """Basic counts and statistics."""
    total_convs = len(conversations)
    total_messages = 0
    total_human_msgs = 0
    total_assistant_msgs = 0
    total_chars = 0
    total_human_chars = 0
    conv_lengths = []  # messages per conversation
    char_lengths = []  # chars per conversation

    for conv in conversations:
        msgs = conv.get("chat_messages", [])
        conv_msg_count = len(msgs)
        conv_lengths.append(conv_msg_count)
        conv_chars = 0
        for msg in msgs:
            total_messages += 1
            text = extract_text(msg)
            msg_chars = len(text)
            total_chars += msg_chars
            conv_chars += msg_chars
            if msg.get("sender") == "human":
                total_human_msgs += 1
                total_human_chars += msg_chars
            elif msg.get("sender") == "assistant":
                total_assistant_msgs += 1
        char_lengths.append(conv_chars)

    return {
        "total_conversations": total_convs,
        "total_messages": total_messages,
        "total_human_messages": total_human_msgs,
        "total_assistant_messages": total_assistant_msgs,
        "total_characters": total_chars,
        "total_human_characters": total_human_chars,
        "avg_messages_per_conversation": round(total_messages / max(total_convs, 1), 1),
        "avg_chars_per_conversation": round(total_chars / max(total_convs, 1), 1),
        "median_messages_per_conversation": sorted(conv_lengths)[len(conv_lengths) // 2] if conv_lengths else 0,
        "longest_conversation_messages": max(conv_lengths) if conv_lengths else 0,
        "shortest_conversation_messages": min(conv_lengths) if conv_lengths else 0,
        "conversations_with_1_message": sum(1 for l in conv_lengths if l <= 1),
        "conversations_2_to_10_messages": sum(1 for l in conv_lengths if 2 <= l <= 10),
        "conversations_11_to_50_messages": sum(1 for l in conv_lengths if 11 <= l <= 50),
        "conversations_over_50_messages": sum(1 for l in conv_lengths if l > 50),
    }


def analyze_temporal_patterns(conversations):
    """When and how often the user works."""
    timestamps = []
    for conv in conversations:
        ts = parse_timestamp(conv.get("created_at"))
        if ts:
            timestamps.append(ts)

    if not timestamps:
        return {"error": "No valid timestamps found"}

    timestamps.sort()
    date_counts = Counter()
    hour_counts = Counter()
    weekday_counts = Counter()
    month_counts = Counter()

    for ts in timestamps:
        date_counts[ts.strftime("%Y-%m-%d")] += 1
        hour_counts[ts.hour] += 1
        weekday_counts[ts.strftime("%A")] += 1
        month_counts[ts.strftime("%Y-%m")] += 1

    # Session gaps (time between consecutive conversations)
    gaps_hours = []
    for i in range(1, len(timestamps)):
        gap = (timestamps[i] - timestamps[i - 1]).total_seconds() / 3600
        if gap < 720:  # ignore gaps > 30 days (likely separate usage periods)
            gaps_hours.append(gap)

    # Detect session clusters (conversations within 1 hour of each other)
    sessions = []
    if timestamps:
        current_session = [timestamps[0]]
        for i in range(1, len(timestamps)):
            gap = (timestamps[i] - timestamps[i - 1]).total_seconds() / 3600
            if gap <= 1:
                current_session.append(timestamps[i])
            else:
                sessions.append(current_session)
                current_session = [timestamps[i]]
        sessions.append(current_session)

    session_lengths = [len(s) for s in sessions]

    return {
        "date_range_start": timestamps[0].strftime("%Y-%m-%d"),
        "date_range_end": timestamps[-1].strftime("%Y-%m-%d"),
        "total_days_active": len(date_counts),
        "most_active_date": date_counts.most_common(1)[0] if date_counts else None,
        "most_active_date_count": date_counts.most_common(1)[0][1] if date_counts else 0,
        "hour_distribution": {str(h): hour_counts.get(h, 0) for h in range(24)},
        "peak_hour": hour_counts.most_common(1)[0][0] if hour_counts else None,
        "weekday_distribution": dict(weekday_counts),
        "most_active_weekday": weekday_counts.most_common(1)[0][0] if weekday_counts else None,
        "monthly_distribution": dict(sorted(month_counts.items())),
        "avg_conversations_per_active_day": round(len(timestamps) / max(len(date_counts), 1), 1),
        "estimated_session_count": len(sessions),
        "avg_conversations_per_session": round(sum(session_lengths) / max(len(sessions), 1), 1),
        "median_gap_between_conversations_hours": round(sorted(gaps_hours)[len(gaps_hours) // 2], 2) if gaps_hours else None,
    }


def analyze_feature_usage(conversations):
    """Detect which Claude features were used."""
    artifact_count = 0
    project_count = 0
    file_upload_count = 0
    web_search_signals = 0
    long_context_count = 0  # conversations with > 30 messages
    multi_turn_planning = 0  # conversations with > 10 human messages
    code_artifact_count = 0
    text_artifact_count = 0
    svg_artifact_count = 0
    html_artifact_count = 0
    react_artifact_count = 0
    projects_used = set()

    for conv in conversations:
        msgs = conv.get("chat_messages", [])

        # Artifacts — check both top-level and in messages
        artifacts = conv.get("artifacts", [])
        if artifacts:
            artifact_count += len(artifacts)
            for art in artifacts:
                art_type = ""
                if isinstance(art, dict):
                    art_type = art.get("type", "") or art.get("name", "")
                elif isinstance(art, str):
                    art_type = art
                art_type_lower = art_type.lower()
                if "code" in art_type_lower:
                    code_artifact_count += 1
                elif "svg" in art_type_lower:
                    svg_artifact_count += 1
                elif "html" in art_type_lower:
                    html_artifact_count += 1
                elif "react" in art_type_lower:
                    react_artifact_count += 1
                else:
                    text_artifact_count += 1

        # Also scan message text for artifact-like content (code blocks, SVG tags)
        for msg in msgs:
            text = extract_text(msg)
            if "<svg" in text.lower():
                svg_artifact_count += 1
            if "```html" in text.lower() or "<!DOCTYPE html" in text.lower():
                html_artifact_count += 1
            if "```react" in text.lower() or "```jsx" in text.lower():
                react_artifact_count += 1

        # Projects
        project = conv.get("project")
        if project:
            projects_used.add(project)
            project_count += 1

        # File uploads
        for msg in msgs:
            attachments = msg.get("attachments", [])
            files = msg.get("files", [])
            if attachments:
                file_upload_count += len(attachments)
            if files:
                file_upload_count += len(files)

        # Web search signals (heuristic: search-related keywords in human messages)
        for msg in msgs:
            if msg.get("sender") == "human":
                text = extract_text(msg).lower()
                if any(kw in text for kw in ["search the web", "search for", "look up", "find information about",
                                              "what's the latest", "current news", "recent research"]):
                    web_search_signals += 1
                    break

        # Long context
        if len(msgs) > 30:
            long_context_count += 1

        # Multi-turn planning
        human_count = sum(1 for m in msgs if m.get("sender") == "human")
        if human_count > 10:
            multi_turn_planning += 1

    return {
        "artifacts_total": artifact_count,
        "artifacts_by_type": {
            "code": code_artifact_count,
            "text": text_artifact_count,
            "svg": svg_artifact_count,
            "html": html_artifact_count,
            "react": react_artifact_count,
        },
        "conversations_with_artifacts": sum(1 for c in conversations if c.get("artifacts")),
        "projects_used_count": len(projects_used),
        "conversations_in_projects": project_count,
        "file_uploads_total": file_upload_count,
        "web_search_signals": web_search_signals,
        "long_context_conversations": long_context_count,
        "multi_turn_planning_conversations": multi_turn_planning,
    }


def analyze_topic_clusters(conversations, top_n=50):
    """Keyword frequency analysis to identify usage domains."""
    # Domain keyword sets for classification
    domain_keywords = {
        "coding/software": ["code", "function", "python", "javascript", "typescript", "react", "node",
                            "api", "bug", "error", "debug", "refactor", "class", "method", "variable",
                            "docker", "git", "npm", "package", "import", "compile", "runtime", "script"],
        "writing/drafting": ["draft", "write", "letter", "email", "document", "report", "summary",
                             "rewrite", "edit", "proofread", "tone", "paragraph", "outline"],
        "legal": ["legal", "court", "fcfcoa", "family law", "affidavit", "summons", "respondent",
                  "applicant", "parenting", "property", "settlement", "consent order", "statute",
                  "legislation", "section", "act", "regulation", "subpoena"],
        "clinical/health": ["clinical", "client", "therapy", "session", "mental health", "ndis",
                            "assessment", "case note", "progress note", "referral", "diagnosis",
                            "treatment", "psychologist", "counsellor", "soap"],
        "financial/forensic": ["bank", "statement", "transaction", "forensic", "dissipation",
                               "asset", "liability", "pool", "valuation", "nab", "transfer",
                               "audit", "reconciliation", "schedule"],
        "research/analysis": ["research", "analyze", "analysis", "compare", "study", "data",
                              "survey", "literature", "evidence", "findings", "methodology"],
        "household/admin": ["insurance", "bill", "utility", "mortgage", "rent", "lease",
                            "policy number", "renewal", "provider", "subscription", "account",
                            "password", "login"],
        "planning/project": ["plan", "project", "roadmap", "milestone", "task", "phase",
                             "step", "timeline", "deliverable", "scope", "requirement"],
        "ai/build": ["librechat", "goose", "agent", "skill", "mcp", "model", "endpoint",
                     "prompt", "rag", "embedding", "vector", "docker", "wsl", "librechat.yaml",
                     "build", "deploy", "config"],
    }

    domain_counts = Counter()
    keyword_freq = Counter()
    all_human_text = []

    for conv in conversations:
        conv_text = ""
        for msg in conv.get("chat_messages", []):
            if msg.get("sender") == "human":
                text = extract_text(msg)
                conv_text += " " + text
                all_human_text.append(text)

        conv_lower = conv_lower_text = conv_text.lower()

        # Domain classification
        for domain, keywords in domain_keywords.items():
            if any(kw in conv_lower for kw in keywords):
                domain_counts[domain] += 1

        # Keyword frequency (extract words from human messages)
        words = re.findall(r"\b[a-z]{4,}\b", conv_lower)
        # Filter common stop words
        stop_words = {"that", "this", "with", "have", "from", "they", "will", "would",
                       "there", "their", "what", "about", "which", "when", "your", "them",
                       "then", "also", "more", "some", "such", "only", "very", "just",
                       "like", "need", "make", "want", "been", "were", "into", "than",
                       "them", "these", "those", "here", "where", "should", "could",
                       "does", "done", "each", "both", "other", "most", "over", "under"}
        for w in words:
            if w not in stop_words:
                keyword_freq[w] += 1

    return {
        "domain_distribution": dict(domain_counts.most_common()),
        "top_keywords": keyword_freq.most_common(top_n),
        "total_unique_keywords": len(keyword_freq),
    }


def analyze_repeat_tasks(conversations):
    """Detect repeated task patterns (similar conversation titles or opening messages)."""
    title_counts = Counter()
    opening_msg_counts = Counter()

    for conv in conversations:
        title = conv.get("name", "").strip()
        if title:
            title_counts[title] += 1

        # First human message as task signature
        for msg in conv.get("chat_messages", []):
            if msg.get("sender") == "human":
                text = extract_text(msg).strip()
                # Use first 100 chars as signature
                if text:
                    signature = text[:100].lower()
                    opening_msg_counts[signature] += 1
                break

    repeated_titles = {t: c for t, c in title_counts.items() if c > 1}
    repeated_openings = {t: c for t, c in opening_msg_counts.items() if c > 1}

    return {
        "repeated_conversation_titles": dict(sorted(repeated_titles.items(), key=lambda x: -x[1])[:20]),
        "repeated_opening_messages": dict(sorted(repeated_openings.items(), key=lambda x: -x[1])[:20]),
        "total_repeated_titles": len(repeated_titles),
        "total_repeated_openings": len(repeated_openings),
    }


def analyze_conversation_titles(conversations, top_n=30):
    """Extract and analyze conversation titles for topic insights."""
    titles = [conv.get("name", "").strip() for conv in conversations if conv.get("name")]
    title_word_freq = Counter()
    for title in titles:
        words = re.findall(r"\b[a-z]{3,}\b", title.lower())
        for w in words:
            title_word_freq[w] += 1

    return {
        "total_titled_conversations": len(titles),
        "top_title_words": title_word_freq.most_common(top_n),
        "sample_titles": titles[:30],
    }


def analyze_message_length_distribution(conversations):
    """Distribution of human message lengths — reveals usage style."""
    human_msg_lengths = []
    for conv in conversations:
        for msg in conv.get("chat_messages", []):
            if msg.get("sender") == "human":
                human_msg_lengths.append(len(extract_text(msg)))

    if not human_msg_lengths:
        return {"error": "No human messages found"}

    human_msg_lengths.sort()
    n = len(human_msg_lengths)

    return {
        "total_human_messages": n,
        "avg_length_chars": round(sum(human_msg_lengths) / n, 1),
        "median_length_chars": human_msg_lengths[n // 2],
        "p90_length_chars": human_msg_lengths[int(n * 0.9)],
        "p99_length_chars": human_msg_lengths[int(n * 0.99)],
        "short_messages_under_100_chars": sum(1 for l in human_msg_lengths if l < 100),
        "medium_messages_100_to_1000_chars": sum(1 for l in human_msg_lengths if 100 <= l < 1000),
        "long_messages_1000_to_5000_chars": sum(1 for l in human_msg_lengths if 1000 <= l < 5000),
        "very_long_messages_over_5000_chars": sum(1 for l in human_msg_lengths if l >= 5000),
    }


# ─── Report generation ──────────────────────────────────────────────────────

def generate_markdown_report(stats, temporal, features, topics, repeats, titles, msg_lengths):
    """Generate a human-readable Markdown report."""
    lines = []
    lines.append("# Claude Usage Analysis Report")
    lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # Basic stats
    lines.append("## 1. Basic Statistics\n")
    lines.append(f"- **Total conversations:** {stats['total_conversations']:,}")
    lines.append(f"- **Total messages:** {stats['total_messages']:,}")
    lines.append(f"- **Human messages:** {stats['total_human_messages']:,}")
    lines.append(f"- **Assistant messages:** {stats['total_assistant_messages']:,}")
    lines.append(f"- **Total characters:** {stats['total_characters']:,}")
    lines.append(f"- **Avg messages per conversation:** {stats['avg_messages_per_conversation']}")
    lines.append(f"- **Avg characters per conversation:** {stats['avg_chars_per_conversation']}")
    lines.append(f"- **Median messages per conversation:** {stats['median_messages_per_conversation']}")
    lines.append(f"- **Longest conversation:** {stats['longest_conversation_messages']} messages")
    lines.append("")

    # Conversation length distribution
    lines.append("### Conversation Length Distribution\n")
    lines.append(f"- 1 message (single prompt): {stats['conversations_with_1_message']}")
    lines.append(f"- 2–10 messages: {stats['conversations_2_to_10_messages']}")
    lines.append(f"- 11–50 messages: {stats['conversations_11_to_50_messages']}")
    lines.append(f"- Over 50 messages: {stats['conversations_over_50_messages']}")
    lines.append("")

    # Temporal patterns
    lines.append("## 2. Temporal Patterns\n")
    if "error" not in temporal:
        lines.append(f"- **Date range:** {temporal['date_range_start']} → {temporal['date_range_end']}")
        lines.append(f"- **Active days:** {temporal['total_days_active']}")
        lines.append(f"- **Most active date:** {temporal['most_active_date']} ({temporal['most_active_date_count']} conversations)")
        lines.append(f"- **Peak hour:** {temporal['peak_hour']}:00")
        lines.append(f"- **Most active weekday:** {temporal['most_active_weekday']}")
        lines.append(f"- **Avg conversations per active day:** {temporal['avg_conversations_per_active_day']}")
        lines.append(f"- **Estimated sessions:** {temporal['estimated_session_count']}")
        lines.append(f"- **Avg conversations per session:** {temporal['avg_conversations_per_session']}")
        lines.append("")
        lines.append("### Hour Distribution\n")
        lines.append("```")
        for h in range(24):
            count = temporal["hour_distribution"].get(str(h), 0)
            bar = "█" * min(count, 50)
            lines.append(f"{h:02d}:00 | {bar} ({count})")
        lines.append("```\n")
        lines.append("### Monthly Distribution\n")
        for month, count in temporal["monthly_distribution"].items():
            lines.append(f"- {month}: {count} conversations")
        lines.append("")

    # Feature usage
    lines.append("## 3. Feature Usage\n")
    lines.append(f"- **Artifacts total:** {features['artifacts_total']}")
    lines.append(f"  - Code: {features['artifacts_by_type']['code']}")
    lines.append(f"  - Text: {features['artifacts_by_type']['text']}")
    lines.append(f"  - SVG: {features['artifacts_by_type']['svg']}")
    lines.append(f"  - HTML: {features['artifacts_by_type']['html']}")
    lines.append(f"  - React: {features['artifacts_by_type']['react']}")
    lines.append(f"- **Conversations with artifacts:** {features['conversations_with_artifacts']}")
    lines.append(f"- **Projects used:** {features['projects_used_count']}")
    lines.append(f"- **Conversations in projects:** {features['conversations_in_projects']}")
    lines.append(f"- **File uploads:** {features['file_uploads_total']}")
    lines.append(f"- **Web search signals:** {features['web_search_signals']}")
    lines.append(f"- **Long-context conversations (>30 msgs):** {features['long_context_conversations']}")
    lines.append(f"- **Multi-turn planning (>10 human msgs):** {features['multi_turn_planning_conversations']}")
    lines.append("")

    # Topic clusters
    lines.append("## 4. Topic / Domain Distribution\n")
    lines.append("| Domain | Conversations |")
    lines.append("|---|---|")
    for domain, count in topics["domain_distribution"].items():
        lines.append(f"| {domain} | {count} |")
    lines.append("")
    lines.append("### Top Keywords\n")
    lines.append("| Keyword | Frequency |")
    lines.append("|---|---|")
    for kw, count in topics["top_keywords"][:25]:
        lines.append(f"| {kw} | {count} |")
    lines.append("")

    # Repeat tasks
    lines.append("## 5. Repeat Tasks & Automation Opportunities\n")
    lines.append(f"- **Repeated conversation titles:** {repeats['total_repeated_titles']}")
    if repeats["repeated_conversation_titles"]:
        lines.append("\n| Title | Count |")
        lines.append("|---|---|")
        for title, count in list(repeats["repeated_conversation_titles"].items())[:10]:
            lines.append(f"| {title[:60]} | {count} |")
    lines.append(f"\n- **Repeated opening messages:** {repeats['total_repeated_openings']}")
    if repeats["repeated_openings"]:
        lines.append("\n| Opening (first 100 chars) | Count |")
        lines.append("|---|---|")
        for opening, count in list(repeats["repeated_openings"].items())[:10]:
            lines.append(f"| {opening[:60]}... | {count} |")
    lines.append("")

    # Message length distribution
    lines.append("## 6. Message Length Distribution (Human)\n")
    if "error" not in msg_lengths:
        lines.append(f"- **Avg length:** {msg_lengths['avg_length_chars']} chars")
        lines.append(f"- **Median length:** {msg_lengths['median_length_chars']} chars")
        lines.append(f"- **P90 length:** {msg_lengths['p90_length_chars']} chars")
        lines.append(f"- **P99 length:** {msg_lengths['p99_length_chars']} chars")
        lines.append(f"- Short (<100 chars): {msg_lengths['short_messages_under_100_chars']}")
        lines.append(f"- Medium (100–1000 chars): {msg_lengths['medium_messages_100_to_1000_chars']}")
        lines.append(f"- Long (1000–5000 chars): {msg_lengths['long_messages_1000_to_5000_chars']}")
        lines.append(f"- Very long (>5000 chars): {msg_lengths['very_long_messages_over_5000_chars']}")
    lines.append("")

    # Conversation titles
    lines.append("## 7. Conversation Titles Sample\n")
    if titles.get("sample_titles"):
        for t in titles["sample_titles"][:20]:
            lines.append(f"- {t}")
    lines.append("")

    lines.append("---")
    lines.append("\n*This report was generated locally. No conversation content was sent externally.*")

    return "\n".join(lines)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Analyze Claude.ai data export")
    parser.add_argument("--input", required=True, help="Path to conversations.json")
    parser.add_argument("--output", required=True, help="Output directory for reports")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing Claude export: {input_path}", file=sys.stderr)

    # Load
    conversations = load_conversations(str(input_path))
    print(f"  Loaded {len(conversations)} conversations", file=sys.stderr)

    # Analyze
    print("  Analyzing basic stats...", file=sys.stderr)
    stats = analyze_basic_stats(conversations)

    print("  Analyzing temporal patterns...", file=sys.stderr)
    temporal = analyze_temporal_patterns(conversations)

    print("  Analyzing feature usage...", file=sys.stderr)
    features = analyze_feature_usage(conversations)

    print("  Analyzing topic clusters...", file=sys.stderr)
    topics = analyze_topic_clusters(conversations)

    print("  Analyzing repeat tasks...", file=sys.stderr)
    repeats = analyze_repeat_tasks(conversations)

    print("  Analyzing conversation titles...", file=sys.stderr)
    titles = analyze_conversation_titles(conversations)

    print("  Analyzing message length distribution...", file=sys.stderr)
    msg_lengths = analyze_message_length_distribution(conversations)

    # Write outputs
    print("  Writing reports...", file=sys.stderr)

    # Summary JSON
    summary = {
        "basic_stats": stats,
        "temporal_patterns": temporal,
        "feature_usage": features,
        "topic_clusters": topics,
        "repeat_tasks": repeats,
        "conversation_titles": titles,
        "message_length_distribution": msg_lengths,
        "analysis_metadata": {
            "input_file": str(input_path),
            "analysis_date": datetime.now().isoformat(),
            "script_version": "1.0",
        },
    }
    with open(output_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)

    # Individual JSON files
    with open(output_dir / "feature_usage.json", "w", encoding="utf-8") as f:
        json.dump(features, f, indent=2, ensure_ascii=False, default=str)
    with open(output_dir / "temporal_patterns.json", "w", encoding="utf-8") as f:
        json.dump(temporal, f, indent=2, ensure_ascii=False, default=str)
    with open(output_dir / "topic_clusters.json", "w", encoding="utf-8") as f:
        json.dump(topics, f, indent=2, ensure_ascii=False, default=str)

    # Markdown report
    report = generate_markdown_report(stats, temporal, features, topics, repeats, titles, msg_lengths)
    with open(output_dir / "usage_report.md", "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n✓ Analysis complete. Reports written to: {output_dir}", file=sys.stderr)
    print(f"  - summary.json (full structured data)", file=sys.stderr)
    print(f"  - usage_report.md (human-readable report)", file=sys.stderr)
    print(f"  - feature_usage.json", file=sys.stderr)
    print(f"  - temporal_patterns.json", file=sys.stderr)
    print(f"  - topic_clusters.json", file=sys.stderr)


if __name__ == "__main__":
    main()
