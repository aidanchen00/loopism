"""
Local Storage for Loopism Learning System

Stores learned patterns and user ratings locally in JSON files
so they persist across sessions and are immediately accessible.
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict

STORAGE_DIR = Path("learning_data")
PATTERNS_FILE = STORAGE_DIR / "learned_patterns.json"
RATINGS_FILE = STORAGE_DIR / "user_ratings.json"
SESSIONS_FILE = STORAGE_DIR / "sessions.json"

# Ensure storage directory exists
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _load_json(filepath: Path) -> list:
    """Load JSON file or return empty list."""
    if filepath.exists():
        try:
            with open(filepath) as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_json(filepath: Path, data: list):
    """Save data to JSON file."""
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# LEARNED PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════

def save_learned_pattern(
    initial_prompt: str,
    refined_prompt: str,
    critique: str,
    improvement_notes: str,
    auto_score: float,
    audio_path: str = None,
    user_rating: int = None,
    session_id: str = None
) -> str:
    """Save a learned pattern to local storage. Returns pattern ID."""
    patterns = _load_json(PATTERNS_FILE)

    pattern_id = f"p_{int(time.time() * 1000)}"

    pattern = {
        "id": pattern_id,
        "timestamp": datetime.now().isoformat(),
        "initial_prompt": initial_prompt,
        "refined_prompt": refined_prompt,
        "critique": critique,
        "improvement_notes": improvement_notes,
        "auto_score": auto_score,
        "audio_path": audio_path,
        "user_rating": user_rating,
        "session_id": session_id,
        "times_used": 0
    }

    patterns.append(pattern)
    _save_json(PATTERNS_FILE, patterns)

    return pattern_id


def get_all_patterns() -> list:
    """Get all learned patterns."""
    return _load_json(PATTERNS_FILE)


def get_pattern_by_id(pattern_id: str) -> Optional[dict]:
    """Get a specific pattern by ID."""
    patterns = _load_json(PATTERNS_FILE)
    for p in patterns:
        if p.get("id") == pattern_id:
            return p
    return None


def update_pattern(pattern_id: str, updates: dict):
    """Update a pattern with new data."""
    patterns = _load_json(PATTERNS_FILE)
    for i, p in enumerate(patterns):
        if p.get("id") == pattern_id:
            patterns[i].update(updates)
            break
    _save_json(PATTERNS_FILE, patterns)


def increment_pattern_usage(pattern_id: str):
    """Increment the times_used counter for a pattern."""
    patterns = _load_json(PATTERNS_FILE)
    for i, p in enumerate(patterns):
        if p.get("id") == pattern_id:
            patterns[i]["times_used"] = p.get("times_used", 0) + 1
            break
    _save_json(PATTERNS_FILE, patterns)


def get_similar_patterns(prompt: str, top_k: int = 3) -> list:
    """Get similar patterns for few-shot learning."""
    patterns = _load_json(PATTERNS_FILE)
    if not patterns:
        return []

    # Simple keyword matching
    prompt_words = set(prompt.lower().split())

    scored = []
    for p in patterns:
        initial_words = set(p.get("initial_prompt", "").lower().split())
        refined_words = set(p.get("refined_prompt", "").lower().split())
        all_words = initial_words | refined_words

        overlap = len(prompt_words & all_words)
        quality = p.get("auto_score", 0) / 100
        rating_boost = 0.2 if p.get("user_rating", 0) >= 4 else 0

        score = overlap * 0.3 + quality * 0.5 + rating_boost
        scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = [p for _, p in scored[:top_k]]

    # Increment usage counters
    for p in results:
        increment_pattern_usage(p["id"])

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# USER RATINGS
# ═══════════════════════════════════════════════════════════════════════════════

def save_user_rating(
    pattern_id: str,
    rating: int,
    session_id: str = None,
    refined_prompt: str = None,
    auto_score: float = None
) -> str:
    """Save a user rating to local storage. Returns rating ID."""
    ratings = _load_json(RATINGS_FILE)

    rating_id = f"r_{int(time.time() * 1000)}"

    rating_data = {
        "id": rating_id,
        "pattern_id": pattern_id,
        "rating": rating,
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "refined_prompt": refined_prompt,
        "auto_score": auto_score
    }

    ratings.append(rating_data)
    _save_json(RATINGS_FILE, ratings)

    # Also update the pattern if it exists
    if pattern_id:
        update_pattern(pattern_id, {"user_rating": rating})

    return rating_id


def get_all_ratings() -> list:
    """Get all user ratings."""
    return _load_json(RATINGS_FILE)


def get_ratings_by_session(session_id: str) -> list:
    """Get ratings for a specific session."""
    ratings = _load_json(RATINGS_FILE)
    return [r for r in ratings if r.get("session_id") == session_id]


# ═══════════════════════════════════════════════════════════════════════════════
# SESSIONS
# ═══════════════════════════════════════════════════════════════════════════════

def save_session(
    session_id: str,
    initial_prompt: str,
    final_prompt: str,
    iterations: int,
    total_time: float,
    avg_score: float,
    patterns_learned: int
):
    """Save a session record."""
    sessions = _load_json(SESSIONS_FILE)

    session = {
        "id": session_id,
        "timestamp": datetime.now().isoformat(),
        "initial_prompt": initial_prompt,
        "final_prompt": final_prompt,
        "iterations": iterations,
        "total_time": total_time,
        "avg_score": avg_score,
        "patterns_learned": patterns_learned
    }

    sessions.append(session)
    _save_json(SESSIONS_FILE, sessions)


def get_all_sessions() -> list:
    """Get all sessions."""
    return _load_json(SESSIONS_FILE)


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTICS
# ═══════════════════════════════════════════════════════════════════════════════

def get_stats() -> dict:
    """Get overall statistics for the sidebar."""
    patterns = _load_json(PATTERNS_FILE)
    ratings = _load_json(RATINGS_FILE)
    sessions = _load_json(SESSIONS_FILE)

    # Calculate stats
    total_patterns = len(patterns)
    total_ratings = len(ratings)
    total_sessions = len(sessions)

    # Average score
    if patterns:
        avg_score = sum(p.get("auto_score", 0) for p in patterns) / len(patterns)
    else:
        avg_score = 0

    # Average user rating
    if ratings:
        avg_rating = sum(r.get("rating", 0) for r in ratings) / len(ratings)
    else:
        avg_rating = 0

    # Times reused
    times_reused = sum(p.get("times_used", 0) for p in patterns)

    # Top patterns (by score)
    top_patterns = sorted(patterns, key=lambda x: x.get("auto_score", 0), reverse=True)[:5]

    # Recent activity (last 5 sessions)
    recent_sessions = sorted(sessions, key=lambda x: x.get("timestamp", ""), reverse=True)[:5]

    # Top keywords from high-scoring patterns
    high_scoring = [p for p in patterns if p.get("auto_score", 0) >= 75]
    all_words = []
    stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'create', 'featuring'}
    for p in high_scoring:
        words = p.get("refined_prompt", "").lower().split()
        words = [w.strip(",.()[]") for w in words if w.strip(",.()[]") not in stopwords and len(w) > 2]
        all_words.extend(words)

    from collections import Counter
    word_counts = Counter(all_words)
    top_keywords = [{"word": w, "count": c} for w, c in word_counts.most_common(10)]

    return {
        "total_patterns": total_patterns,
        "total_ratings": total_ratings,
        "total_sessions": total_sessions,
        "avg_score": round(avg_score, 1),
        "avg_rating": round(avg_rating, 1),
        "times_reused": times_reused,
        "top_patterns": top_patterns,
        "recent_sessions": recent_sessions,
        "top_keywords": top_keywords
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MIGRATION - Import from precached data
# ═══════════════════════════════════════════════════════════════════════════════

def import_from_precached():
    """Import patterns from pre-generated cache into local storage."""
    # Direct file access to avoid circular imports with weave
    cache_dir = Path("precached")
    index_path = cache_dir / "index.json"

    if not index_path.exists():
        return 0

    with open(index_path) as f:
        index = json.load(f)

    imported = 0
    for prompt, info in index.items():
        metadata_path = Path(info.get("metadata_path", ""))
        if not metadata_path.exists():
            continue

        with open(metadata_path) as f:
            metadata = json.load(f)

        for it in metadata.get("iterations_data", []):
            # Check if already imported (by checking refined_prompt)
            existing = get_all_patterns()
            already_exists = any(
                p.get("refined_prompt") == it.get("refined_prompt")
                for p in existing
            )

            if not already_exists and it.get("auto_score", 0) >= 75:
                save_learned_pattern(
                    initial_prompt=it.get("input_prompt", ""),
                    refined_prompt=it.get("refined_prompt", ""),
                    critique=it.get("critique", ""),
                    improvement_notes=it.get("improvement_notes", ""),
                    auto_score=it.get("auto_score", 0),
                    audio_path=it.get("cached_audio_path", it.get("audio_path", "")),
                    session_id="precached"
                )
                imported += 1

    return imported
