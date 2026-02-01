"""
Loopism Core Engine

Self-Refine Architecture:
- Iterative self-critique and revision loops
- Self-learning from successful refinements
- Replicate MusicGen: Fast cloud audio generation
- Weave: Full observability and tracing

The magic: AI generates audio, critiques its own prompt, refines, regenerates.
The system LEARNS from each session, getting smarter over time.
"""

import os
import sys
import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, Callable
from dotenv import load_dotenv

import weave
from openai import OpenAI

from audio_generator import ReplicateMusicGenerator
from learning import (
    get_learning_system,
    LearningSystem,
    ScoreResult,
    IntelligenceMetrics,
    RefinementRecord,
    AUTO_LEARN_THRESHOLD
)
from trace_learning import (
    get_trace_system,
    TraceLearningSystem,
    TraceRecord,
    MusicContext,
    ImplicitSignals,
    AgentDecision,
    AgentMetrics,
    LearningInsight
)

load_dotenv()

# Initialize Weave for tracing
WEAVE_PROJECT = os.environ.get("WEAVE_PROJECT", "loopism-audio-refinement")


@dataclass
class LoopIteration:
    """Single iteration of the refinement loop."""
    iteration_num: int
    input_prompt: str
    critique: str
    refined_prompt: str
    improvement_notes: str
    audio_path: str
    audio_url: str
    generation_time: float
    refinement_time: float
    # Learning fields
    record_id: Optional[str] = None
    auto_score: float = 0.0
    added_to_learning: bool = False
    examples_used: int = 0
    user_rating: Optional[int] = None
    score_details: Optional[dict] = None
    # Trace learning fields
    trace_id: Optional[str] = None
    music_context: Optional[dict] = None
    agent_decisions: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dict, ensuring all values are JSON-serializable."""
        return {
            "iteration_num": self.iteration_num,
            "input_prompt": self.input_prompt,
            "critique": self.critique,
            "refined_prompt": self.refined_prompt,
            "improvement_notes": self.improvement_notes,
            "audio_path": str(self.audio_path) if self.audio_path else "",
            "audio_url": str(self.audio_url) if self.audio_url else "",
            "generation_time": self.generation_time,
            "refinement_time": self.refinement_time,
            "record_id": self.record_id,
            "auto_score": self.auto_score,
            "added_to_learning": self.added_to_learning,
            "examples_used": self.examples_used,
            "user_rating": self.user_rating,
            "score_details": dict(self.score_details) if self.score_details else None,
            "trace_id": self.trace_id,
            "music_context": self.music_context,
            "agent_decisions": self.agent_decisions
        }


class LoopismEngine:
    """
    Self-improving audio generation engine with learning capabilities.

    Self-Refine Architecture:

    For each iteration:
        1. RETRIEVE: Get similar past successes for few-shot learning
        2. DRAFT: Current prompt (starts as user input)
        3. CRITIQUE: LLM analyzes what's missing/vague (with learned examples)
        4. REVISION: LLM creates improved prompt
        5. GENERATE: Replicate creates audio from revised prompt
        6. SCORE: Auto-score the refinement quality
        7. LEARN: Add high-quality refinements to the database
        8. LOOP: Revised prompt becomes input for next iteration

    Key insight: We GENERATE AUDIO at each step so improvement
    is AUDIBLE, not just readable. And we LEARN from each session.
    """

    # Base system prompt for the self-critique loop
    BASE_SYSTEM_PROMPT = """You are an expert audio producer and prompt engineer for AI music generation.

Your task is to iteratively refine music/audio prompts through self-critique.

CRITIQUE PHASE:
Analyze the current prompt for:
- Missing specificity (genre, subgenre, influences)
- Vague instrumentation (be specific: "grand piano with soft pedal" not just "piano")
- Undefined tempo (include BPM range)
- Missing mood descriptors (use precise words: "melancholic" not "sad")
- Lacking structure hints (intro, build, drop, outro)
- Missing key/scale information

REVISION PHASE:
Create an improved prompt that:
- Keeps the original intent
- Adds missing specificity
- Stays under 50 words (model limitation)
- Avoids contradictions (e.g., "fast and relaxing")
- Uses professional music production terminology

OUTPUT FORMAT (strict JSON):
{
    "critique": "What's missing or vague in the current prompt (1-2 sentences)",
    "refined_prompt": "The improved prompt (under 50 words)",
    "improvement_notes": "What you changed and why (1 sentence)"
}

Be specific and actionable. Each iteration should meaningfully improve the prompt."""

    def __init__(
        self,
        max_iterations: int = 3,
        audio_duration: int = 5,
        output_dir: str = "loopism_outputs",
        llm_model: str = "gpt-4o-mini",
        on_iteration_complete: Optional[Callable] = None,
        enable_learning: bool = True
    ):
        """
        Initialize the Loopism engine.

        Args:
            max_iterations: Number of refinement iterations (2-5 recommended)
            audio_duration: Duration of each audio clip in seconds
            output_dir: Directory for generated audio
            llm_model: Model for refinement (gpt-4o-mini recommended for speed)
            on_iteration_complete: Optional callback after each iteration
            enable_learning: Whether to use the learning system
        """
        self.max_iterations = max_iterations
        self.audio_duration = audio_duration
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.llm_model = llm_model
        self.on_iteration_complete = on_iteration_complete
        self.enable_learning = enable_learning

        # Initialize components
        self.llm = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.audio_gen = ReplicateMusicGenerator(output_dir=str(self.output_dir))

        # Learning systems
        self.learning: Optional[LearningSystem] = None
        self.trace_learning: Optional[TraceLearningSystem] = None
        if enable_learning:
            self.learning = get_learning_system()
            self.trace_learning = get_trace_system()

        # Storage for iterations
        self.iterations: list[LoopIteration] = []
        self.session_id = f"loopism_{int(time.time())}"

        # Learning state for current run
        self._current_examples: list[RefinementRecord] = []
        self._examples_text: str = ""

        # Initialize Weave
        weave.init(WEAVE_PROJECT)
        print(f"✅ Weave initialized: {WEAVE_PROJECT}")
        if enable_learning:
            print(f"🧠 Learning system active")

    def _build_system_prompt(self) -> str:
        """Build system prompt with learned examples if available."""
        prompt = self.BASE_SYSTEM_PROMPT

        if self._examples_text:
            prompt += self._examples_text

        return prompt

    @weave.op()
    def refine_prompt(self, current_prompt: str, iteration: int) -> dict:
        """
        Use LLM to critique and refine the audio prompt.

        This implements the CRITIQUE → REVISION phases of Self-Refine.
        Fully traced with Weave.

        Args:
            current_prompt: The prompt to critique
            iteration: Current iteration number (0-indexed)

        Returns:
            dict with critique, refined_prompt, improvement_notes
        """
        start_time = time.time()

        user_message = f"""ITERATION: {iteration + 1} of {self.max_iterations}

CURRENT PROMPT:
"{current_prompt}"

{"This is the initial user request. Transform it into a detailed audio generation prompt." if iteration == 0 else "Critique this prompt and make it more specific for audio generation."}

Respond with JSON only. No markdown, no explanation outside the JSON."""

        response = self.llm.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=300
        )

        result = json.loads(response.choices[0].message.content)
        result["refinement_time"] = time.time() - start_time
        result["examples_used"] = len(self._current_examples)

        return result

    @weave.op()
    def generate_audio(self, prompt: str, iteration: int) -> dict:
        """
        Generate audio from prompt via Replicate.
        Fully traced with Weave.

        Args:
            prompt: The refined prompt
            iteration: Current iteration number

        Returns:
            Generation result dict
        """
        return self.audio_gen.generate(
            prompt=prompt,
            duration=self.audio_duration,
            output_name=f"{self.session_id}_iter_{iteration}"
        )

    @weave.op()
    def run(self, initial_prompt: str) -> list[LoopIteration]:
        """
        Execute the full self-improvement loop.

        This is the main entry point. For each iteration:
        1. Retrieve similar past successes (if learning enabled)
        2. Critique current prompt
        3. Generate refined prompt
        4. Generate audio
        5. Score the refinement
        6. Learn from high-quality refinements
        7. Store results
        8. Callback (if provided)

        Args:
            initial_prompt: User's original request (e.g., "happy piano")

        Returns:
            List of all iterations with audio paths
        """
        self.iterations = []
        current_prompt = initial_prompt
        self._current_examples = []
        self._examples_text = ""

        print("\n" + "="*70)
        print("🔄 LOOPISM: Self-Improving Audio Generation")
        print("="*70)
        print(f"   Initial prompt: \"{initial_prompt}\"")
        print(f"   Iterations: {self.max_iterations}")
        print(f"   Audio duration: {self.audio_duration}s")
        print(f"   Learning: {'ENABLED' if self.enable_learning else 'DISABLED'}")

        # Retrieve learned examples if learning is enabled
        if self.enable_learning and self.learning:
            print("\n🧠 Retrieving learned examples...")
            self._current_examples = self.learning.retrieve_similar_examples(initial_prompt)
            self._examples_text = self.learning.format_examples_for_prompt(self._current_examples)
            print(f"   📚 Found {len(self._current_examples)} relevant examples")
            
            # Log pattern retrieval
            if self._current_examples:
                from local_storage import log_learning_event
                pattern_ids = [ex.id for ex in self._current_examples]
                log_learning_event(
                    event_type="pattern_retrieved",
                    session_id=self.session_id,
                    prompt=initial_prompt,
                    details={
                        "patterns_retrieved": len(self._current_examples),
                        "pattern_ids": pattern_ids,
                        "pattern_scores": [ex.auto_score for ex in self._current_examples]
                    }
                )

        print("="*70 + "\n")

        for i in range(self.max_iterations):
            print(f"\n{'─'*50}")
            print(f"ITERATION {i + 1}/{self.max_iterations}")
            if self._current_examples:
                print(f"📚 Using {len(self._current_examples)} learned examples")
            print(f"{'─'*50}")

            # Phase 1: Critique and Refine
            print("\n📝 Phase 1: Critiquing and refining prompt...")
            refinement = self.refine_prompt(current_prompt, i)
            
            # Log that learned patterns were used in this iteration
            if self._current_examples and self.enable_learning:
                from local_storage import log_learning_event
                log_learning_event(
                    event_type="pattern_used",
                    session_id=self.session_id,
                    prompt=current_prompt,
                    details={
                        "iteration": i + 1,
                        "patterns_used": len(self._current_examples),
                        "refined_prompt": refinement['refined_prompt'],
                        "improvement_notes": refinement['improvement_notes']
                    }
                )

            print(f"   💭 Critique: {refinement['critique']}")
            print(f"   ✨ Refined: {refinement['refined_prompt']}")
            print(f"   📈 Changes: {refinement['improvement_notes']}")

            # Phase 2: Generate Audio
            print("\n🎵 Phase 2: Generating audio...")
            audio_result = self.generate_audio(refinement['refined_prompt'], i)

            # Phase 3: Score and Learn (if enabled)
            auto_score = 0.0
            score_details = None
            record_id = None
            added_to_learning = False
            trace_id = None
            music_context_dict = None
            agent_decisions_list = []

            if self.enable_learning and self.learning:
                print("\n🧠 Phase 3: Scoring and learning...")

                # Score the refinement
                score_result = self.learning.score_refinement(
                    current_prompt,
                    refinement['refined_prompt'],
                    refinement['critique'],
                    refinement['improvement_notes']
                )
                auto_score = score_result.overall
                score_details = score_result.to_dict()

                print(f"   📊 Auto-score: {auto_score}/100")
                print(f"   📋 {score_result.reasoning}")

                # Learn from it if high quality
                if auto_score >= AUTO_LEARN_THRESHOLD:
                    record_id = self.learning.learn_from_refinement(
                        current_prompt,
                        refinement['refined_prompt'],
                        refinement['critique'],
                        refinement['improvement_notes'],
                        auto_score,
                        audio_result['audio_path']
                    )
                    if record_id:
                        added_to_learning = True
                        print(f"   🧠 Added to learning database (ID: {record_id})")
                else:
                    # Generate a record_id anyway for potential future rating
                    import hashlib
                    content = f"{current_prompt}|{refinement['refined_prompt']}|{time.time()}"
                    record_id = hashlib.md5(content.encode()).hexdigest()[:12]

                # Record trace with trace_learning system
                if self.trace_learning:
                    # Simulate agent decisions (in real system, these would come from actual agents)
                    agent_decisions = [
                        AgentDecision(
                            agent_name="prompt_refiner",
                            decision_type="refinement",
                            parameters={
                                "critique_focus": "specificity",
                                "refinement_strategy": "additive"
                            },
                            confidence=min(auto_score / 100, 1.0),
                            success=auto_score >= 60,
                            feedback_score=auto_score
                        )
                    ]
                    agent_decisions_list = [d.to_dict() for d in agent_decisions]

                    trace_id = self.trace_learning.record_trace(
                        trace_id=f"{self.session_id}_iter_{i}",
                        session_id=self.session_id,
                        initial_prompt=current_prompt,
                        refined_prompt=refinement['refined_prompt'],
                        critique=refinement['critique'],
                        improvement_notes=refinement['improvement_notes'],
                        auto_score=auto_score,
                        audio_path=audio_result['audio_path'],
                        generation_time=audio_result['generation_time'],
                        agent_decisions=agent_decisions
                    )

                    if trace_id:
                        # Get the music context for UI display
                        music_context = self.trace_learning.extract_music_context(refinement['refined_prompt'])
                        music_context_dict = music_context.to_dict()
                        print(f"   📝 Trace recorded (ID: {trace_id})")
                        if music_context.genre:
                            print(f"   🎸 Detected: {music_context.genre} | {music_context.mood or 'N/A'}")

            # Store iteration
            iteration_data = LoopIteration(
                iteration_num=i,
                input_prompt=current_prompt,
                critique=refinement['critique'],
                refined_prompt=refinement['refined_prompt'],
                improvement_notes=refinement['improvement_notes'],
                audio_path=audio_result['audio_path'],
                audio_url=audio_result['audio_url'],
                generation_time=audio_result['generation_time'],
                refinement_time=refinement['refinement_time'],
                record_id=record_id,
                auto_score=auto_score,
                added_to_learning=added_to_learning,
                examples_used=len(self._current_examples),
                score_details=score_details,
                trace_id=trace_id,
                music_context=music_context_dict,
                agent_decisions=agent_decisions_list
            )
            self.iterations.append(iteration_data)

            # Callback for UI updates
            if self.on_iteration_complete:
                self.on_iteration_complete(iteration_data)

            # Update for next iteration
            current_prompt = refinement['refined_prompt']

        # Summary
        total_time = sum(it.generation_time + it.refinement_time for it in self.iterations)
        avg_score = sum(it.auto_score for it in self.iterations) / len(self.iterations) if self.iterations else 0
        learned_count = sum(1 for it in self.iterations if it.added_to_learning)

        print(f"\n{'='*70}")
        print("✅ LOOPISM COMPLETE")
        print(f"   Total iterations: {len(self.iterations)}")
        print(f"   Total time: {total_time:.1f}s")
        print(f"   Initial: \"{initial_prompt}\"")
        print(f"   Final: \"{self.iterations[-1].refined_prompt}\"")
        if self.enable_learning:
            print(f"   📊 Average score: {avg_score:.1f}/100")
            print(f"   🧠 Refinements learned: {learned_count}")
        print(f"   Outputs: {self.output_dir}")
        print(f"   Weave trace: https://wandb.ai/loopism/{WEAVE_PROJECT}/weave")
        print("="*70 + "\n")

        return self.iterations

    def record_user_rating(self, iteration_num: int, rating: int) -> bool:
        """
        Record a user rating for a specific iteration.

        Args:
            iteration_num: Which iteration (0-indexed)
            rating: 1-5 stars

        Returns:
            True if successful
        """
        if not self.enable_learning or not self.learning:
            return False

        if iteration_num < 0 or iteration_num >= len(self.iterations):
            return False

        iteration = self.iterations[iteration_num]

        if not iteration.record_id:
            return False

        # Record the feedback
        success = self.learning.record_user_feedback(
            iteration.record_id,
            rating,
            self.session_id
        )

        if success:
            iteration.user_rating = rating

            # Save to local storage for ratings tab
            from local_storage import save_user_rating
            try:
                save_user_rating(
                    pattern_id=iteration.record_id or f"iter_{iteration.iteration_num}",
                    rating=rating,
                    session_id=self.session_id,
                    refined_prompt=iteration.refined_prompt,
                    auto_score=iteration.auto_score
                )
            except Exception as e:
                print(f"Warning: Could not save rating to local storage: {e}")

            # Also update trace record with user rating
            if iteration.trace_id and self.trace_learning:
                import weave
                traces = self.trace_learning._get_traces()
                for trace_data in traces:
                    if trace_data.get('trace_id') == iteration.trace_id:
                        trace_data['user_rating'] = rating
                        # Re-save dataset
                        dataset = weave.Dataset(name=self.trace_learning.TRACE_DATASET, rows=traces)
                        weave.publish(dataset)
                        self.trace_learning._trace_cache = None
                        break

            # If high rating and not already learned, try to add it
            if rating >= 4 and not iteration.added_to_learning:
                record_id = self.learning.learn_from_refinement(
                    iteration.input_prompt,
                    iteration.refined_prompt,
                    iteration.critique,
                    iteration.improvement_notes,
                    iteration.auto_score,
                    iteration.audio_path,
                    rating
                )
                if record_id:
                    iteration.added_to_learning = True
                    # Log that a pattern was learned
                    from local_storage import log_learning_event
                    log_learning_event(
                        event_type="pattern_learned",
                        session_id=self.session_id,
                        prompt=iteration.input_prompt,
                        details={
                            "record_id": record_id,
                            "refined_prompt": iteration.refined_prompt,
                            "auto_score": iteration.auto_score,
                            "user_rating": rating
                        }
                    )

        return success

    def record_implicit_signal(self, trace_id: str, signal_type: str, value: int = 1) -> bool:
        """
        Record an implicit user signal (replay, save, export, edit).

        Args:
            trace_id: ID of the trace to update
            signal_type: Type of signal (replay, save, export, edit, regeneration)
            value: Amount to increment (default 1)

        Returns:
            True if successful
        """
        if not self.enable_learning or not self.trace_learning:
            return False

        return self.trace_learning.record_implicit_signal(trace_id, signal_type, value)

    def get_learning_metrics(self) -> Optional[IntelligenceMetrics]:
        """Get intelligence dashboard metrics."""
        if not self.enable_learning or not self.learning:
            return None

        return self.learning.get_intelligence_metrics()

    def get_agent_metrics(self) -> Optional[dict]:
        """Get agent performance metrics from trace learning."""
        if not self.enable_learning or not self.trace_learning:
            return None

        return self.trace_learning.get_agent_metrics()

    def get_learning_insights(self, lookback_hours: int = 24) -> list:
        """Get learning insights from recent traces."""
        if not self.enable_learning or not self.trace_learning:
            return []

        return self.trace_learning.generate_insights(lookback_hours)

    def get_results_json(self) -> str:
        """Export all iterations as JSON."""
        return json.dumps(
            [it.to_dict() for it in self.iterations],
            indent=2
        )

    def get_comparison_data(self) -> dict:
        """
        Return data formatted for UI comparison view.
        """
        if not self.iterations:
            return {"error": "No iterations run yet"}

        return {
            "session_id": self.session_id,
            "initial_prompt": self.iterations[0].input_prompt,
            "final_prompt": self.iterations[-1].refined_prompt,
            "total_iterations": len(self.iterations),
            "total_time": sum(it.generation_time + it.refinement_time for it in self.iterations),
            "iterations": [it.to_dict() for it in self.iterations],
            "examples_used": self.iterations[0].examples_used if self.iterations else 0,
            "avg_score": sum(it.auto_score for it in self.iterations) / len(self.iterations) if self.iterations else 0,
            "learned_count": sum(1 for it in self.iterations if it.added_to_learning),
            "learning_enabled": self.enable_learning
        }


def test_engine():
    """Test the full Loopism pipeline."""
    print("\n" + "🧪 "*20)
    print("TESTING LOOPISM ENGINE")
    print("🧪 "*20 + "\n")

    engine = LoopismEngine(
        max_iterations=3,
        audio_duration=5,
        output_dir="test_loopism_outputs",
        enable_learning=True
    )

    # Run with a simple prompt
    results = engine.run("happy summer vibes")

    # Print summary
    print("\n📊 RESULTS SUMMARY:")
    for it in results:
        print(f"\n   Iteration {it.iteration_num + 1}:")
        print(f"   Prompt: {it.refined_prompt[:60]}...")
        print(f"   Audio: {it.audio_path}")
        print(f"   Score: {it.auto_score}/100")
        print(f"   Learned: {it.added_to_learning}")

    # Test learning metrics
    metrics = engine.get_learning_metrics()
    if metrics:
        print("\n🧠 LEARNING METRICS:")
        print(f"   Total examples: {metrics.total_examples}")
        print(f"   Avg score: {metrics.avg_score}")

    return results


if __name__ == "__main__":
    test_engine()
