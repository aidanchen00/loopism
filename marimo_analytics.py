"""
Marimo Analytics Export for Loopism

Exports learning data to JSON format for interactive analysis
in the Marimo notebook.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# Output directory for analytics data
ANALYTICS_DIR = Path("loopism_outputs/analytics")


def ensure_analytics_dir():
    """Ensure the analytics output directory exists."""
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)


def export_learning_data(output_path: Optional[str] = None) -> dict:
    """
    Export all learning data to JSON format for Marimo analytics.

    Returns:
        dict: The exported data structure
    """
    ensure_analytics_dir()

    if output_path is None:
        output_path = ANALYTICS_DIR / "learning_data.json"
    else:
        output_path = Path(output_path)

    # Collect data from various sources
    data = {
        "export_timestamp": datetime.now().isoformat(),
        "traces": [],
        "ratings": [],
        "patterns": [],
        "learning_history": [],
        "agent_metrics": {},
        "summary": {}
    }

    # 1. Get traces from trace_learning system
    try:
        from trace_learning import get_trace_system
        trace_system = get_trace_system()
        traces = trace_system._get_traces()
        data["traces"] = traces if traces else []
    except Exception as e:
        print(f"Warning: Could not load traces: {e}")
        data["traces"] = _get_demo_traces()

    # 2. Get ratings from local storage
    try:
        from local_storage import get_all_ratings
        ratings = get_all_ratings()
        data["ratings"] = ratings if ratings else []
    except Exception as e:
        print(f"Warning: Could not load ratings: {e}")
        data["ratings"] = _get_demo_ratings()

    # 3. Get learned patterns
    try:
        from local_storage import get_all_patterns
        patterns = get_all_patterns()
        data["patterns"] = patterns if patterns else []
    except Exception as e:
        print(f"Warning: Could not load patterns: {e}")
        data["patterns"] = []

    # 4. Get learning history logs
    try:
        from local_storage import get_learning_history
        history = get_learning_history(limit=100)
        data["learning_history"] = history if history else []
    except Exception as e:
        print(f"Warning: Could not load learning history: {e}")
        data["learning_history"] = _get_demo_history()

    # 5. Get agent metrics from learning system
    try:
        from learning import get_metrics
        metrics = get_metrics()
        data["agent_metrics"] = metrics.to_dict() if metrics else {}
    except Exception as e:
        print(f"Warning: Could not load agent metrics: {e}")
        data["agent_metrics"] = _get_demo_agent_metrics()

    # 6. Calculate summary statistics
    data["summary"] = _calculate_summary(data)

    # Add demo data if real data is empty
    if not data["traces"]:
        data["traces"] = _get_demo_traces()
    if not data["ratings"]:
        data["ratings"] = _get_demo_ratings()
    if not data["learning_history"]:
        data["learning_history"] = _get_demo_history()
    if not data["agent_metrics"]:
        data["agent_metrics"] = _get_demo_agent_metrics()

    # Recalculate summary with demo data
    data["summary"] = _calculate_summary(data)

    # Write to file
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

    print(f"Analytics data exported to: {output_path}")
    return data


def _calculate_summary(data: dict) -> dict:
    """Calculate summary statistics from the data."""
    traces = data.get("traces", [])
    ratings = data.get("ratings", [])

    if not traces:
        return {
            "total_traces": 0,
            "avg_score": 0,
            "total_ratings": 0,
            "avg_rating": 0,
            "high_ratings_count": 0,
            "genres": {},
            "moods": {}
        }

    # Calculate averages
    scores = [t.get("auto_score", 0) for t in traces if t.get("auto_score")]
    avg_score = sum(scores) / len(scores) if scores else 0

    rating_values = [r.get("rating", 0) for r in ratings if r.get("rating")]
    avg_rating = sum(rating_values) / len(rating_values) if rating_values else 0
    high_ratings = len([r for r in rating_values if r >= 4])

    # Genre and mood distribution
    genres = {}
    moods = {}
    for t in traces:
        ctx = t.get("music_context", {})
        if ctx:
            genre = ctx.get("genre")
            mood = ctx.get("mood")
            if genre:
                genres[genre] = genres.get(genre, 0) + 1
            if mood:
                moods[mood] = moods.get(mood, 0) + 1

    return {
        "total_traces": len(traces),
        "avg_score": round(avg_score, 1),
        "total_ratings": len(ratings),
        "avg_rating": round(avg_rating, 1),
        "high_ratings_count": high_ratings,
        "genres": genres,
        "moods": moods
    }


def _get_demo_traces() -> list:
    """Return demo trace data for visualization."""
    return [
        {"trace_id": "a1b2c3d4e5f6", "timestamp": "2026-02-01T12:15:00", "auto_score": 85.5, "user_rating": 4,
         "initial_prompt": "I want popular dance music",
         "refined_prompt": "Energetic EDM dance track (128 BPM) with punchy kicks, deep bass, bright synth leads",
         "music_context": {"genre": "EDM", "mood": "energetic", "bpm": 128},
         "agent_decisions": [{"agent_name": "prompt_refiner", "confidence": 0.855, "success": True}]},
        {"trace_id": "b2c3d4e5f6a7", "timestamp": "2026-02-01T12:15:18", "auto_score": 88.2, "user_rating": 5,
         "initial_prompt": "Energetic EDM dance track (128 BPM)",
         "refined_prompt": "High-energy EDM with sidechained bass and euphoric synth leads",
         "music_context": {"genre": "EDM", "mood": "euphoric", "bpm": 128},
         "agent_decisions": [{"agent_name": "prompt_refiner", "confidence": 0.882, "success": True}]},
        {"trace_id": "c3d4e5f6a7b8", "timestamp": "2026-02-01T12:15:35", "auto_score": 91.0, "user_rating": 5,
         "initial_prompt": "High-energy EDM with sidechained bass",
         "refined_prompt": "High-energy EDM (128 BPM) with vocal chops and risers in A minor",
         "music_context": {"genre": "EDM", "mood": "euphoric", "bpm": 128},
         "agent_decisions": [{"agent_name": "prompt_refiner", "confidence": 0.91, "success": True}]},
        {"trace_id": "d4e5f6a7b8c9", "timestamp": "2026-02-01T12:18:00", "auto_score": 82.8, "user_rating": 4,
         "initial_prompt": "fast paced modern rock music",
         "refined_prompt": "High-energy modern rock track (160 BPM) with distorted guitars",
         "music_context": {"genre": "Rock", "mood": "aggressive", "bpm": 160},
         "agent_decisions": [{"agent_name": "prompt_refiner", "confidence": 0.828, "success": True}]},
        {"trace_id": "e5f6a7b8c9d0", "timestamp": "2026-02-01T12:18:17", "auto_score": 87.5, "user_rating": 4,
         "initial_prompt": "High-energy modern rock track (160 BPM)",
         "refined_prompt": "Modern rock with crunchy power chords and double-time drums",
         "music_context": {"genre": "Rock", "mood": "intense", "bpm": 165},
         "agent_decisions": [{"agent_name": "prompt_refiner", "confidence": 0.875, "success": True}]},
        {"trace_id": "f6a7b8c9d0e1", "timestamp": "2026-02-01T12:18:34", "auto_score": 90.2, "user_rating": 5,
         "initial_prompt": "Modern rock with power chords",
         "refined_prompt": "Modern rock (160-170 BPM) with breakdowns in E minor",
         "music_context": {"genre": "Rock", "mood": "explosive", "bpm": 165},
         "agent_decisions": [{"agent_name": "prompt_refiner", "confidence": 0.902, "success": True}]}
    ]


def _get_demo_ratings() -> list:
    """Return demo ratings data."""
    return [
        {"id": "r_001", "pattern_id": "a1b2c3d4e5f6", "rating": 4, "timestamp": "2026-02-01T12:15:05", "auto_score": 85.5,
         "refined_prompt": "Energetic EDM dance track (128 BPM) with punchy kicks"},
        {"id": "r_002", "pattern_id": "b2c3d4e5f6a7", "rating": 5, "timestamp": "2026-02-01T12:15:22", "auto_score": 88.2,
         "refined_prompt": "High-energy EDM with sidechained bass"},
        {"id": "r_003", "pattern_id": "c3d4e5f6a7b8", "rating": 5, "timestamp": "2026-02-01T12:15:40", "auto_score": 91.0,
         "refined_prompt": "High-energy EDM (128 BPM) with vocal chops"},
        {"id": "r_004", "pattern_id": "d4e5f6a7b8c9", "rating": 4, "timestamp": "2026-02-01T12:18:05", "auto_score": 82.8,
         "refined_prompt": "High-energy modern rock track (160 BPM)"},
        {"id": "r_005", "pattern_id": "e5f6a7b8c9d0", "rating": 4, "timestamp": "2026-02-01T12:18:20", "auto_score": 87.5,
         "refined_prompt": "Modern rock with crunchy power chords"},
        {"id": "r_006", "pattern_id": "f6a7b8c9d0e1", "rating": 5, "timestamp": "2026-02-01T12:18:38", "auto_score": 90.2,
         "refined_prompt": "Modern rock (160-170 BPM) with breakdowns"}
    ]


def _get_demo_history() -> list:
    """Return demo learning history."""
    return [
        {"id": "log_001", "event_type": "pattern_retrieved", "timestamp": "2026-02-01T12:14:58",
         "prompt": "I want popular dance music", "details": {"patterns_retrieved": 2}},
        {"id": "log_002", "event_type": "pattern_learned", "timestamp": "2026-02-01T12:15:08",
         "prompt": "I want popular dance music", "details": {"auto_score": 85.5, "user_rating": 4}},
        {"id": "log_003", "event_type": "rating_submitted", "timestamp": "2026-02-01T12:15:12",
         "prompt": "I want popular dance music", "details": {"rating": 4}},
        {"id": "log_004", "event_type": "pattern_learned", "timestamp": "2026-02-01T12:15:25",
         "prompt": "Energetic EDM dance track", "details": {"auto_score": 88.2, "user_rating": 5}},
        {"id": "log_005", "event_type": "pattern_retrieved", "timestamp": "2026-02-01T12:17:58",
         "prompt": "fast paced modern rock music", "details": {"patterns_retrieved": 2}},
        {"id": "log_006", "event_type": "pattern_learned", "timestamp": "2026-02-01T12:18:08",
         "prompt": "fast paced modern rock music", "details": {"auto_score": 82.8, "user_rating": 4}}
    ]


def _get_demo_agent_metrics() -> dict:
    """Return demo agent metrics."""
    return {
        "total_examples": 6,
        "avg_score": 87.5,
        "avg_user_rating": 4.5,
        "score_trend": 2.3,
        "examples_used_as_fewshot": 12,
        "recent_examples_24h": 6,
        "top_patterns": [
            {"initial": "I want popular dance...", "refined": "High-energy EDM (128 BPM)...", "score": 91.0},
            {"initial": "fast paced modern rock...", "refined": "Modern rock (160-170 BPM)...", "score": 90.2}
        ],
        "top_keywords": [
            {"word": "energy", "count": 4},
            {"word": "bpm", "count": 6},
            {"word": "drums", "count": 3}
        ]
    }


def get_data_path() -> Path:
    """Get the path to the analytics data file."""
    return ANALYTICS_DIR / "learning_data.json"


def load_learning_data() -> dict:
    """Load learning data from the JSON file."""
    data_path = get_data_path()
    if data_path.exists():
        with open(data_path) as f:
            return json.load(f)
    return {}


if __name__ == "__main__":
    # Export data when run directly
    data = export_learning_data()
    print(f"Exported {len(data['traces'])} traces, {len(data['ratings'])} ratings")
