"""
Trace-Based Learning System for Loopism

Extends the base learning system with:
- Weave trace persistence and analysis
- Agent decision tracking
- Implicit signal detection (replays, saves, edits)
- Context-aware retrieval
- Musical pattern extraction
"""

import os
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict, field
from collections import Counter, defaultdict

import weave
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MusicContext:
    """Musical context metadata for a generation."""
    genre: Optional[str] = None
    mood: Optional[str] = None
    bpm: Optional[int] = None
    key: Optional[str] = None
    instruments: List[str] = field(default_factory=list)
    session_intent: Optional[str] = None  # "background", "hook", "soundtrack", etc.

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ImplicitSignals:
    """User behavior signals that indicate quality."""
    replay_count: int = 0
    save_count: int = 0
    export_count: int = 0
    edit_count: int = 0
    regeneration_count: int = 0
    session_duration: float = 0.0  # seconds user spent on this
    last_interaction: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    def get_quality_score(self) -> float:
        """
        Calculate implicit quality score (0-100).
        High replays/saves = good, high regenerations = bad
        """
        positive = (
            self.replay_count * 10 +
            self.save_count * 20 +
            self.export_count * 25 +
            min(self.session_duration / 10, 20)  # Cap at 20 points
        )
        negative = (
            self.regeneration_count * 15 +
            self.edit_count * 5
        )
        return min(100, max(0, positive - negative))


@dataclass
class AgentDecision:
    """A decision made by an agent during generation."""
    agent_name: str  # "melody", "harmony", "rhythm", "structure"
    decision_type: str  # "tempo_change", "chord_density", "drop", "transition"
    parameters: Dict
    confidence: float
    success: bool = True
    feedback_score: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TraceRecord:
    """
    Extended trace record with Weave trace ID and agent decisions.
    """
    trace_id: str
    session_id: str
    timestamp: str

    # Generation data
    initial_prompt: str
    refined_prompt: str
    critique: str
    improvement_notes: str

    # Quality metrics
    auto_score: float
    user_rating: Optional[int] = None
    implicit_signals: ImplicitSignals = field(default_factory=ImplicitSignals)

    # Musical context
    music_context: MusicContext = field(default_factory=MusicContext)

    # Agent decisions
    agent_decisions: List[AgentDecision] = field(default_factory=list)

    # Audio output
    audio_path: Optional[str] = None
    generation_time: float = 0.0

    # Learning metadata
    times_retrieved: int = 0
    influence_count: int = 0  # How many future gens this influenced

    def to_dict(self) -> dict:
        data = asdict(self)
        data['implicit_signals'] = self.implicit_signals.to_dict()
        data['music_context'] = self.music_context.to_dict()
        data['agent_decisions'] = [d.to_dict() for d in self.agent_decisions]
        return data

    def get_combined_quality(self) -> float:
        """Combine all quality signals into one score."""
        weights = {
            'auto': 0.3,
            'user': 0.4,
            'implicit': 0.3
        }

        auto = self.auto_score
        user = (self.user_rating * 20) if self.user_rating else 0
        implicit = self.implicit_signals.get_quality_score()

        return (
            auto * weights['auto'] +
            user * weights['user'] +
            implicit * weights['implicit']
        )


@dataclass
class AgentMetrics:
    """Performance metrics for a specific agent."""
    agent_name: str
    total_decisions: int = 0
    success_rate: float = 0.0
    avg_confidence: float = 0.0
    avg_feedback_score: float = 0.0
    top_decisions: List[Dict] = field(default_factory=list)
    trend: str = "stable"  # "improving", "declining", "stable"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LearningInsight:
    """A single insight derived from learning patterns."""
    insight_text: str
    confidence: float
    category: str  # "tempo", "genre", "structure", "instrumentation"
    supporting_examples: int
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)


# ═══════════════════════════════════════════════════════════════════════════════
# TRACE-BASED LEARNING SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class TraceLearningSystem:
    """
    Advanced learning system with trace analysis and agent metrics.
    """

    TRACE_DATASET = "trace-records"
    INSIGHTS_DATASET = "learning-insights"

    def __init__(self, llm_model: str = "gpt-4o-mini"):
        self.llm = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.llm_model = llm_model
        self._trace_cache = None
        self._cache_time = None
        self._cache_ttl = 30  # 30 seconds

    def _get_traces(self) -> List[Dict]:
        """Get all trace records with caching."""
        now = time.time()
        if self._trace_cache and self._cache_time and (now - self._cache_time < self._cache_ttl):
            return self._trace_cache

        try:
            dataset = weave.ref(f"weave:///datasets/{self.TRACE_DATASET}").get()
            self._trace_cache = list(dataset.rows) if dataset else []
        except Exception:
            self._trace_cache = []

        self._cache_time = now
        return self._trace_cache

    def _save_trace(self, trace: TraceRecord):
        """Save trace record to Weave dataset."""
        try:
            existing = self._get_traces()
            existing.append(trace.to_dict())

            dataset = weave.Dataset(name=self.TRACE_DATASET, rows=existing)
            weave.publish(dataset)

            self._trace_cache = None
            return True
        except Exception as e:
            print(f"Warning: Could not save trace: {e}")
            return False

    @weave.op()
    def extract_music_context(self, prompt: str) -> MusicContext:
        """
        Use LLM to extract musical context from a prompt.
        """
        extraction_prompt = f"""Extract musical context from this prompt. Return JSON only.

Prompt: "{prompt}"

Extract:
- genre: music genre (if mentioned)
- mood: emotional tone
- bpm: tempo in BPM (if mentioned or implied)
- key: musical key (if mentioned)
- instruments: list of instruments mentioned
- session_intent: purpose ("background", "hook", "soundtrack", "experimental", etc.)

Return JSON with null for unknown fields."""

        try:
            response = self.llm.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": extraction_prompt}],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=200
            )

            data = json.loads(response.choices[0].message.content)
            return MusicContext(
                genre=data.get("genre"),
                mood=data.get("mood"),
                bpm=data.get("bpm"),
                key=data.get("key"),
                instruments=data.get("instruments", []),
                session_intent=data.get("session_intent")
            )
        except Exception:
            return MusicContext()

    @weave.op()
    def record_trace(
        self,
        trace_id: str,
        session_id: str,
        initial_prompt: str,
        refined_prompt: str,
        critique: str,
        improvement_notes: str,
        auto_score: float,
        audio_path: Optional[str] = None,
        generation_time: float = 0.0,
        agent_decisions: Optional[List[AgentDecision]] = None
    ) -> str:
        """
        Record a full trace with all metadata.
        """
        # Extract musical context
        music_context = self.extract_music_context(refined_prompt)

        trace = TraceRecord(
            trace_id=trace_id,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            initial_prompt=initial_prompt,
            refined_prompt=refined_prompt,
            critique=critique,
            improvement_notes=improvement_notes,
            auto_score=auto_score,
            music_context=music_context,
            agent_decisions=agent_decisions or [],
            audio_path=audio_path,
            generation_time=generation_time
        )

        if self._save_trace(trace):
            return trace_id
        return ""

    @weave.op()
    def record_implicit_signal(
        self,
        trace_id: str,
        signal_type: str,
        value: int = 1
    ):
        """
        Record an implicit user signal (replay, save, edit, etc.).
        """
        traces = self._get_traces()
        for trace_data in traces:
            if trace_data.get('trace_id') == trace_id:
                signals = trace_data.get('implicit_signals', {})
                signals[f"{signal_type}_count"] = signals.get(f"{signal_type}_count", 0) + value
                signals['last_interaction'] = datetime.now().isoformat()
                trace_data['implicit_signals'] = signals

                # Re-save dataset
                dataset = weave.Dataset(name=self.TRACE_DATASET, rows=traces)
                weave.publish(dataset)
                self._trace_cache = None
                return True
        return False

    @weave.op()
    def retrieve_similar_traces(
        self,
        prompt: str,
        music_context: Optional[MusicContext] = None,
        top_k: int = 5
    ) -> List[TraceRecord]:
        """
        Retrieve similar high-quality traces for learning.
        Uses context-aware matching.
        """
        traces = self._get_traces()
        if not traces:
            return []

        prompt_words = set(prompt.lower().split())
        scored_traces = []

        for trace_data in traces:
            try:
                # Calculate keyword relevance
                trace_words = set(
                    trace_data.get('initial_prompt', '').lower().split() +
                    trace_data.get('refined_prompt', '').lower().split()
                )
                keyword_overlap = len(prompt_words & trace_words) / max(1, len(prompt_words))

                # Calculate quality
                trace_obj = TraceRecord(**{k: v for k, v in trace_data.items() if k in TraceRecord.__annotations__})
                quality_score = trace_obj.get_combined_quality() / 100

                # Context matching bonus
                context_bonus = 0
                if music_context and trace_data.get('music_context'):
                    ctx = trace_data['music_context']
                    if ctx.get('genre') == music_context.genre:
                        context_bonus += 0.2
                    if ctx.get('mood') == music_context.mood:
                        context_bonus += 0.15
                    if ctx.get('session_intent') == music_context.session_intent:
                        context_bonus += 0.1

                # Combined score
                relevance = (
                    keyword_overlap * 0.3 +
                    quality_score * 0.5 +
                    context_bonus
                )

                scored_traces.append((relevance, trace_data))
            except Exception:
                continue

        # Sort and return top_k
        scored_traces.sort(key=lambda x: x[0], reverse=True)
        return [TraceRecord(**t) for _, t in scored_traces[:top_k]]

    @weave.op()
    def get_agent_metrics(self) -> Dict[str, AgentMetrics]:
        """
        Calculate performance metrics for each agent.
        """
        traces = self._get_traces()
        agent_stats = defaultdict(lambda: {
            'decisions': [],
            'confidences': [],
            'scores': []
        })

        for trace in traces:
            for decision_data in trace.get('agent_decisions', []):
                agent = decision_data['agent_name']
                agent_stats[agent]['decisions'].append(decision_data)
                agent_stats[agent]['confidences'].append(decision_data.get('confidence', 0))
                if decision_data.get('feedback_score'):
                    agent_stats[agent]['scores'].append(decision_data['feedback_score'])

        metrics = {}
        for agent_name, stats in agent_stats.items():
            total = len(stats['decisions'])
            success_count = sum(1 for d in stats['decisions'] if d.get('success', True))

            metrics[agent_name] = AgentMetrics(
                agent_name=agent_name,
                total_decisions=total,
                success_rate=success_count / total if total > 0 else 0,
                avg_confidence=sum(stats['confidences']) / len(stats['confidences']) if stats['confidences'] else 0,
                avg_feedback_score=sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0,
                top_decisions=self._get_top_decisions(stats['decisions']),
                trend="stable"  # TODO: Calculate trend from historical data
            )

        return metrics

    def _get_top_decisions(self, decisions: List[Dict], top_n: int = 3) -> List[Dict]:
        """Get the most successful decisions."""
        scored = [(d, d.get('feedback_score', 0)) for d in decisions if d.get('feedback_score')]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [
            {
                'type': d['decision_type'],
                'parameters': d.get('parameters', {}),
                'score': score
            }
            for d, score in scored[:top_n]
        ]

    @weave.op()
    def generate_insights(self, lookback_hours: int = 24) -> List[LearningInsight]:
        """
        Generate learning insights from recent traces.
        """
        traces = self._get_traces()
        cutoff = datetime.now() - timedelta(hours=lookback_hours)

        recent_traces = []
        for t in traces:
            try:
                ts = datetime.fromisoformat(t.get('timestamp', ''))
                if ts >= cutoff:
                    recent_traces.append(t)
            except Exception:
                continue

        insights = []

        # Insight 1: What genres/moods perform best?
        high_quality = [t for t in recent_traces if t.get('auto_score', 0) >= 75]
        if high_quality:
            moods = [t.get('music_context', {}).get('mood') for t in high_quality]
            moods = [m for m in moods if m]
            if moods:
                top_mood = Counter(moods).most_common(1)[0]
                insights.append(LearningInsight(
                    insight_text=f'"{top_mood[0]}" vibes are working well right now',
                    confidence=0.8,
                    category="mood",
                    supporting_examples=top_mood[1],
                    timestamp=datetime.now().isoformat()
                ))

        # Insight 2: Successful patterns
        if high_quality:
            all_words = []
            for t in high_quality:
                words = t.get('refined_prompt', '').lower().split()
                all_words.extend(words)

            common = Counter(all_words).most_common(5)
            if common and common[0][1] >= 3:
                insights.append(LearningInsight(
                    insight_text=f'High-scoring prompts often include "{common[0][0]}"',
                    confidence=0.7,
                    category="instrumentation",
                    supporting_examples=common[0][1],
                    timestamp=datetime.now().isoformat()
                ))

        return insights


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

_trace_system: Optional[TraceLearningSystem] = None

def get_trace_system() -> TraceLearningSystem:
    """Get singleton trace learning system."""
    global _trace_system
    if _trace_system is None:
        _trace_system = TraceLearningSystem()
    return _trace_system
