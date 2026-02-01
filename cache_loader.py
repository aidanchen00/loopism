"""
Cache loader for pre-generated quick launch prompts.

Loads cached audio clips with simulated delays to create
the same progressive loading experience as live generation.
"""

import os
import json
import time
import random
from pathlib import Path
from typing import Optional, Callable, Generator
from dataclasses import dataclass

from loopism_core import LoopIteration

CACHE_DIR = Path("precached")
SIMULATED_DELAY_MIN = 4.0  # seconds
SIMULATED_DELAY_MAX = 6.0  # seconds


def get_cache_index() -> dict:
    """Load the cache index."""
    index_path = CACHE_DIR / "index.json"
    if not index_path.exists():
        return {}

    with open(index_path) as f:
        return json.load(f)


def is_prompt_cached(prompt: str) -> bool:
    """Check if a prompt has cached data."""
    index = get_cache_index()
    return prompt.lower() in [p.lower() for p in index.keys()]


def get_cached_prompt_key(prompt: str) -> Optional[str]:
    """Get the cache key for a prompt (case-insensitive match)."""
    index = get_cache_index()
    for cached_prompt in index.keys():
        if cached_prompt.lower() == prompt.lower():
            return cached_prompt
    return None


def load_cached_metadata(prompt: str) -> Optional[dict]:
    """Load metadata for a cached prompt."""
    cache_key = get_cached_prompt_key(prompt)
    if not cache_key:
        return None

    index = get_cache_index()
    info = index.get(cache_key)
    if not info:
        return None

    metadata_path = Path(info["metadata_path"])
    if not metadata_path.exists():
        return None

    with open(metadata_path) as f:
        return json.load(f)


def load_cached_iterations(
    prompt: str,
    on_iteration_loaded: Optional[Callable[[LoopIteration], None]] = None,
    simulate_delay: bool = True
) -> list[LoopIteration]:
    """
    Load cached iterations for a prompt.

    Args:
        prompt: The prompt to load
        on_iteration_loaded: Callback after each iteration loads
        simulate_delay: Whether to add delays between iterations

    Returns:
        List of LoopIteration objects
    """
    metadata = load_cached_metadata(prompt)
    if not metadata:
        return []

    iterations = []

    for it_data in metadata.get("iterations_data", []):
        # Simulate generation delay
        if simulate_delay:
            delay = random.uniform(SIMULATED_DELAY_MIN, SIMULATED_DELAY_MAX)
            time.sleep(delay)

        # Create LoopIteration from cached data
        iteration = LoopIteration(
            iteration_num=it_data.get("iteration_num", 0),
            input_prompt=it_data.get("input_prompt", ""),
            critique=it_data.get("critique", ""),
            refined_prompt=it_data.get("refined_prompt", ""),
            improvement_notes=it_data.get("improvement_notes", ""),
            audio_path=it_data.get("cached_audio_path", it_data.get("audio_path", "")),
            audio_url=it_data.get("audio_url", ""),
            generation_time=it_data.get("generation_time", 0),
            refinement_time=it_data.get("refinement_time", 0),
            record_id=it_data.get("record_id"),
            auto_score=it_data.get("auto_score", 0),
            added_to_learning=it_data.get("added_to_learning", False),
            examples_used=it_data.get("examples_used", 0),
            user_rating=it_data.get("user_rating"),
            score_details=it_data.get("score_details")
        )

        iterations.append(iteration)

        # Call callback
        if on_iteration_loaded:
            on_iteration_loaded(iteration)

    return iterations


def load_cached_comparison_data(prompt: str) -> Optional[dict]:
    """Load comparison data for a cached prompt."""
    metadata = load_cached_metadata(prompt)
    if not metadata:
        return None

    return metadata.get("comparison_data")


def stream_cached_iterations(
    prompt: str,
    simulate_delay: bool = True
) -> Generator[LoopIteration, None, None]:
    """
    Generator that yields cached iterations with delays.

    This allows for progressive UI updates.
    """
    metadata = load_cached_metadata(prompt)
    if not metadata:
        return

    for it_data in metadata.get("iterations_data", []):
        # Simulate generation delay
        if simulate_delay:
            delay = random.uniform(SIMULATED_DELAY_MIN, SIMULATED_DELAY_MAX)
            time.sleep(delay)

        # Create LoopIteration from cached data
        iteration = LoopIteration(
            iteration_num=it_data.get("iteration_num", 0),
            input_prompt=it_data.get("input_prompt", ""),
            critique=it_data.get("critique", ""),
            refined_prompt=it_data.get("refined_prompt", ""),
            improvement_notes=it_data.get("improvement_notes", ""),
            audio_path=it_data.get("cached_audio_path", it_data.get("audio_path", "")),
            audio_url=it_data.get("audio_url", ""),
            generation_time=it_data.get("generation_time", 0),
            refinement_time=it_data.get("refinement_time", 0),
            record_id=it_data.get("record_id"),
            auto_score=it_data.get("auto_score", 0),
            added_to_learning=it_data.get("added_to_learning", False),
            examples_used=it_data.get("examples_used", 0),
            user_rating=it_data.get("user_rating"),
            score_details=it_data.get("score_details")
        )

        yield iteration


def get_all_cached_prompts() -> list[str]:
    """Get list of all cached prompts."""
    index = get_cache_index()
    return list(index.keys())


def verify_cache_integrity() -> tuple[bool, str]:
    """Verify that all cached data is valid and complete."""
    index = get_cache_index()

    if not index:
        return False, "No cache found"

    issues = []

    for prompt, info in index.items():
        metadata_path = Path(info.get("metadata_path", ""))

        if not metadata_path.exists():
            issues.append(f"{prompt}: metadata missing")
            continue

        try:
            with open(metadata_path) as f:
                metadata = json.load(f)
        except Exception as e:
            issues.append(f"{prompt}: invalid JSON - {e}")
            continue

        for it in metadata.get("iterations_data", []):
            audio_path = it.get("cached_audio_path", it.get("audio_path", ""))
            if not audio_path or not Path(audio_path).exists():
                issues.append(f"{prompt}: missing audio for iteration {it.get('iteration_num', '?')}")

    if issues:
        return False, "; ".join(issues[:3]) + (f" (+{len(issues)-3} more)" if len(issues) > 3 else "")

    return True, f"Cache valid: {len(index)} prompts cached"
