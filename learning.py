"""
Loopism Learning Module

Self-learning system that:
- Scores refinements using LLM-as-judge
- Stores successful patterns in Weave Datasets
- Retrieves similar examples for few-shot learning
- Records user feedback to improve over time

All operations are traced with Weave for full observability.
"""

import os
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, asdict, field
from collections import Counter

import weave
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

DATASET_NAME = "successful-refinements"
FEEDBACK_DATASET_NAME = "user-feedback"
AUTO_LEARN_THRESHOLD = 75  # Auto-add refinements scoring >= this
USER_RATING_LEARN_THRESHOLD = 4  # Add refinements rated >= this

# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class RefinementRecord:
    """A learned refinement pattern stored in the Weave dataset."""
    id: str
    timestamp: str
    initial_prompt: str
    refined_prompt: str
    critique: str
    improvement_notes: str
    auto_score: float
    user_rating: Optional[int] = None
    audio_path: Optional[str] = None
    times_used_as_example: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "RefinementRecord":
        return cls(**data)


@dataclass
class ScoreResult:
    """Result from LLM scoring of a refinement."""
    specificity_gain: int
    musicality: int
    coherence: int
    creativity: int
    actionability: int
    overall: float
    reasoning: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class IntelligenceMetrics:
    """Dashboard metrics showing system intelligence."""
    total_examples: int = 0
    avg_score: float = 0.0
    avg_user_rating: float = 0.0
    score_trend: float = 0.0  # positive = improving
    examples_used_as_fewshot: int = 0
    recent_examples_24h: int = 0
    top_patterns: list = field(default_factory=list)
    top_keywords: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ═══════════════════════════════════════════════════════════════════════════════
# LEARNING SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class LearningSystem:
    """
    Self-learning system for Loopism.

    Stores successful refinement patterns and retrieves them for few-shot learning.
    All operations are traced with Weave.
    """

    SCORING_PROMPT = """You are an expert evaluator of AI-generated music prompts.

Score this refinement on 5 dimensions (0-100 each):

1. SPECIFICITY_GAIN: How much more specific is the refined prompt vs the original?
   - 0-30: Minimal improvement
   - 31-60: Moderate improvement
   - 61-80: Good improvement
   - 81-100: Excellent, adds many concrete details

2. MUSICALITY: Does the refined prompt use proper music terminology?
   - Consider: genre, tempo/BPM, instrumentation, dynamics, structure

3. COHERENCE: Is the refined prompt internally consistent?
   - No contradictions (e.g., "fast and relaxing")
   - Logical flow of ideas

4. CREATIVITY: Does the refinement add interesting, non-obvious elements?
   - Not just generic additions
   - Shows musical understanding

5. ACTIONABILITY: Can MusicGen actually generate this?
   - Under 50 words
   - Clear, unambiguous instructions
   - Avoids impossible requests

OUTPUT FORMAT (JSON only):
{
    "specificity_gain": <0-100>,
    "musicality": <0-100>,
    "coherence": <0-100>,
    "creativity": <0-100>,
    "actionability": <0-100>,
    "reasoning": "<1-2 sentence explanation>"
}"""

    def __init__(self, llm_model: str = "gpt-4o-mini"):
        """Initialize the learning system."""
        self.llm = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.llm_model = llm_model
        self._dataset_cache = None
        self._cache_time = None
        self._cache_ttl = 60  # Refresh cache every 60 seconds

    def _generate_id(self, initial: str, refined: str) -> str:
        """Generate a unique ID for a refinement record."""
        content = f"{initial}|{refined}|{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _get_dataset(self) -> list[dict]:
        """Get the learning dataset, with caching."""
        now = time.time()

        # Return cached if fresh
        if self._dataset_cache is not None and self._cache_time is not None:
            if now - self._cache_time < self._cache_ttl:
                return self._dataset_cache

        # Try to load from Weave
        try:
            dataset = weave.ref(f"weave:///datasets/{DATASET_NAME}").get()
            if dataset and hasattr(dataset, 'rows'):
                self._dataset_cache = list(dataset.rows)
            else:
                self._dataset_cache = []
        except Exception:
            # Dataset doesn't exist yet
            self._dataset_cache = []

        self._cache_time = now
        return self._dataset_cache

    def _save_to_dataset(self, record: RefinementRecord):
        """Save a record to the Weave dataset."""
        try:
            # Get existing data
            existing = self._get_dataset()

            # Add new record
            existing.append(record.to_dict())

            # Create/update dataset
            dataset = weave.Dataset(name=DATASET_NAME, rows=existing)
            weave.publish(dataset)

            # Invalidate cache
            self._dataset_cache = None
            self._cache_time = None

            return True
        except Exception as e:
            print(f"Warning: Could not save to Weave dataset: {e}")
            return False

    def _update_record(self, record_id: str, updates: dict):
        """Update an existing record in the dataset."""
        try:
            existing = self._get_dataset()

            for i, record in enumerate(existing):
                if record.get('id') == record_id:
                    existing[i].update(updates)
                    break

            dataset = weave.Dataset(name=DATASET_NAME, rows=existing)
            weave.publish(dataset)

            # Invalidate cache
            self._dataset_cache = None
            self._cache_time = None

            return True
        except Exception as e:
            print(f"Warning: Could not update record: {e}")
            return False

    @weave.op()
    def score_refinement(
        self,
        initial_prompt: str,
        refined_prompt: str,
        critique: str,
        improvement_notes: str
    ) -> ScoreResult:
        """
        Score a refinement using LLM-as-judge.

        Returns scores for specificity, musicality, coherence, creativity, actionability.
        """
        user_message = f"""ORIGINAL PROMPT:
"{initial_prompt}"

REFINED PROMPT:
"{refined_prompt}"

CRITIQUE:
"{critique}"

IMPROVEMENTS MADE:
"{improvement_notes}"

Score this refinement. Respond with JSON only."""

        response = self.llm.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": self.SCORING_PROMPT},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=200
        )

        result = json.loads(response.choices[0].message.content)

        # Calculate overall score (weighted average)
        overall = (
            result.get("specificity_gain", 0) * 0.25 +
            result.get("musicality", 0) * 0.25 +
            result.get("coherence", 0) * 0.20 +
            result.get("creativity", 0) * 0.15 +
            result.get("actionability", 0) * 0.15
        )

        return ScoreResult(
            specificity_gain=result.get("specificity_gain", 0),
            musicality=result.get("musicality", 0),
            coherence=result.get("coherence", 0),
            creativity=result.get("creativity", 0),
            actionability=result.get("actionability", 0),
            overall=round(overall, 1),
            reasoning=result.get("reasoning", "")
        )

    @weave.op()
    def learn_from_refinement(
        self,
        initial_prompt: str,
        refined_prompt: str,
        critique: str,
        improvement_notes: str,
        auto_score: float,
        audio_path: Optional[str] = None,
        user_rating: Optional[int] = None
    ) -> Optional[str]:
        """
        Add a refinement to the learning database if it meets quality threshold.

        Returns the record_id if added, None otherwise.
        """
        # Check if meets threshold
        should_learn = auto_score >= AUTO_LEARN_THRESHOLD
        if user_rating is not None and user_rating >= USER_RATING_LEARN_THRESHOLD:
            should_learn = True

        if not should_learn:
            return None

        # Create record
        record_id = self._generate_id(initial_prompt, refined_prompt)
        record = RefinementRecord(
            id=record_id,
            timestamp=datetime.now().isoformat(),
            initial_prompt=initial_prompt,
            refined_prompt=refined_prompt,
            critique=critique,
            improvement_notes=improvement_notes,
            auto_score=auto_score,
            user_rating=user_rating,
            audio_path=audio_path,
            times_used_as_example=0
        )

        # Save to dataset
        if self._save_to_dataset(record):
            return record_id
        return None

    @weave.op()
    def retrieve_similar_examples(
        self,
        prompt: str,
        top_k: int = 3
    ) -> list[RefinementRecord]:
        """
        Retrieve similar past successes for few-shot learning.

        Uses keyword matching and score ranking.
        Returns top_k examples sorted by relevance and score.
        """
        dataset = self._get_dataset()

        if not dataset:
            return []

        # Extract keywords from prompt
        prompt_words = set(prompt.lower().split())

        # Score each example by relevance
        scored_examples = []
        for record_data in dataset:
            try:
                record = RefinementRecord.from_dict(record_data)

                # Calculate relevance score based on keyword overlap
                initial_words = set(record.initial_prompt.lower().split())
                refined_words = set(record.refined_prompt.lower().split())
                all_words = initial_words | refined_words

                overlap = len(prompt_words & all_words)

                # Combined score: relevance + quality
                quality_score = record.auto_score / 100
                user_boost = 0.2 if record.user_rating and record.user_rating >= 4 else 0
                relevance_score = overlap * 0.3 + quality_score * 0.5 + user_boost

                scored_examples.append((relevance_score, record))
            except Exception:
                continue

        # Sort by score descending
        scored_examples.sort(key=lambda x: x[0], reverse=True)

        # Return top_k
        results = [record for _, record in scored_examples[:top_k]]

        # Update times_used_as_example for retrieved records
        for record in results:
            self._update_record(record.id, {
                "times_used_as_example": record.times_used_as_example + 1
            })

        return results

    def format_examples_for_prompt(self, examples: list[RefinementRecord]) -> str:
        """Format retrieved examples as few-shot context for the system prompt."""
        if not examples:
            return ""

        formatted = "\n\n--- LEARNED EXAMPLES (use these as inspiration) ---\n"

        for i, ex in enumerate(examples, 1):
            formatted += f"""
EXAMPLE {i}:
Original: "{ex.initial_prompt}"
Refined: "{ex.refined_prompt}"
Why it worked: {ex.improvement_notes}
Score: {ex.auto_score}/100
"""

        formatted += "\n--- END EXAMPLES ---\n"
        return formatted

    @weave.op()
    def record_user_feedback(
        self,
        record_id: str,
        rating: int,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Record user rating for a refinement.

        If rating >= 4 and record doesn't exist, creates new record.
        If record exists, updates the rating.
        """
        # Validate rating
        rating = max(1, min(5, rating))

        # Try to find existing record
        dataset = self._get_dataset()
        record_found = False

        for record in dataset:
            if record.get('id') == record_id:
                record_found = True
                break

        if record_found:
            # Update existing record
            return self._update_record(record_id, {"user_rating": rating})

        # Record feedback separately for analytics
        try:
            feedback = {
                "record_id": record_id,
                "rating": rating,
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id
            }

            # Try to append to feedback dataset
            try:
                existing_feedback = weave.ref(f"weave:///datasets/{FEEDBACK_DATASET_NAME}").get()
                feedback_rows = list(existing_feedback.rows) if existing_feedback else []
            except Exception:
                feedback_rows = []

            feedback_rows.append(feedback)
            feedback_dataset = weave.Dataset(name=FEEDBACK_DATASET_NAME, rows=feedback_rows)
            weave.publish(feedback_dataset)

            return True
        except Exception as e:
            print(f"Warning: Could not record feedback: {e}")
            return False

    @weave.op()
    def get_intelligence_metrics(self) -> IntelligenceMetrics:
        """
        Calculate dashboard metrics showing system intelligence.
        """
        dataset = self._get_dataset()

        if not dataset:
            return IntelligenceMetrics()

        # Basic counts
        total = len(dataset)

        # Calculate averages
        scores = [r.get('auto_score', 0) for r in dataset if r.get('auto_score')]
        avg_score = sum(scores) / len(scores) if scores else 0

        ratings = [r.get('user_rating') for r in dataset if r.get('user_rating')]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0

        # Times used as few-shot
        times_used = sum(r.get('times_used_as_example', 0) for r in dataset)

        # Recent examples (last 24h)
        now = datetime.now()
        recent = 0
        for r in dataset:
            try:
                ts = datetime.fromisoformat(r.get('timestamp', ''))
                if now - ts < timedelta(hours=24):
                    recent += 1
            except Exception:
                pass

        # Score trend (compare recent vs older)
        sorted_by_time = sorted(
            [(r.get('timestamp', ''), r.get('auto_score', 0)) for r in dataset],
            key=lambda x: x[0]
        )
        if len(sorted_by_time) >= 4:
            mid = len(sorted_by_time) // 2
            older_avg = sum(s for _, s in sorted_by_time[:mid]) / mid
            newer_avg = sum(s for _, s in sorted_by_time[mid:]) / (len(sorted_by_time) - mid)
            trend = newer_avg - older_avg
        else:
            trend = 0

        # Top patterns (highest scoring)
        sorted_by_score = sorted(dataset, key=lambda r: r.get('auto_score', 0), reverse=True)
        top_patterns = []
        for r in sorted_by_score[:3]:
            top_patterns.append({
                "initial": r.get('initial_prompt', '')[:30] + "...",
                "refined": r.get('refined_prompt', '')[:50] + "...",
                "score": r.get('auto_score', 0)
            })

        # Top keywords from high-scoring refinements
        high_scoring = [r for r in dataset if r.get('auto_score', 0) >= 75]
        all_words = []
        for r in high_scoring:
            words = r.get('refined_prompt', '').lower().split()
            # Filter common words
            stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
            words = [w for w in words if w not in stopwords and len(w) > 2]
            all_words.extend(words)

        word_counts = Counter(all_words)
        top_keywords = [{"word": w, "count": c} for w, c in word_counts.most_common(5)]

        return IntelligenceMetrics(
            total_examples=total,
            avg_score=round(avg_score, 1),
            avg_user_rating=round(avg_rating, 1),
            score_trend=round(trend, 1),
            examples_used_as_fewshot=times_used,
            recent_examples_24h=recent,
            top_patterns=top_patterns,
            top_keywords=top_keywords
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

_learning_system: Optional[LearningSystem] = None

def get_learning_system() -> LearningSystem:
    """Get the singleton learning system instance."""
    global _learning_system
    if _learning_system is None:
        _learning_system = LearningSystem()
    return _learning_system


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def score_refinement(initial: str, refined: str, critique: str, notes: str) -> ScoreResult:
    """Convenience function to score a refinement."""
    return get_learning_system().score_refinement(initial, refined, critique, notes)

def retrieve_examples(prompt: str, top_k: int = 3) -> list[RefinementRecord]:
    """Convenience function to retrieve similar examples."""
    return get_learning_system().retrieve_similar_examples(prompt, top_k)

def learn_from(initial: str, refined: str, critique: str, notes: str, score: float,
               audio_path: str = None, rating: int = None) -> Optional[str]:
    """Convenience function to add a refinement to learning."""
    return get_learning_system().learn_from_refinement(
        initial, refined, critique, notes, score, audio_path, rating
    )

def record_feedback(record_id: str, rating: int, session_id: str = None) -> bool:
    """Convenience function to record user feedback."""
    return get_learning_system().record_user_feedback(record_id, rating, session_id)

def get_metrics() -> IntelligenceMetrics:
    """Convenience function to get intelligence metrics."""
    return get_learning_system().get_intelligence_metrics()
