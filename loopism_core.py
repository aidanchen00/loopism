"""
Loopism Core Engine

Combines:
- recursive-agents: Self-critique and revision loops
- deep-research: Iterative exploration architecture
- Replicate MusicGen: Fast cloud audio generation
- Weave: Full observability

The magic: AI generates audio, critiques its own prompt, refines, regenerates.
Judges can HEAR the improvement across iterations.
"""

import os
import sys
import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Callable
from dotenv import load_dotenv

# Add recursive-agents to path
sys.path.insert(0, str(Path(__file__).parent / "recursive-agents"))

import weave
from openai import OpenAI

from audio_generator import ReplicateMusicGenerator

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

    def to_dict(self) -> dict:
        return asdict(self)


class LoopismEngine:
    """
    Self-improving audio generation engine.

    Architecture (inspired by recursive-agents):

    For each iteration:
        1. DRAFT: Current prompt (starts as user input)
        2. CRITIQUE: LLM analyzes what's missing/vague
        3. REVISION: LLM creates improved prompt
        4. GENERATE: Replicate creates audio from revised prompt
        5. LOOP: Revised prompt becomes input for next iteration

    Key insight: Unlike text-only recursive-agents, we GENERATE AUDIO
    at each step so improvement is AUDIBLE, not just readable.
    """

    # System prompt for the self-critique loop
    SYSTEM_PROMPT = """You are an expert audio producer and prompt engineer for AI music generation.

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
        on_iteration_complete: Optional[Callable] = None
    ):
        """
        Initialize the Loopism engine.

        Args:
            max_iterations: Number of refinement iterations (2-5 recommended)
            audio_duration: Duration of each audio clip in seconds
            output_dir: Directory for generated audio
            llm_model: Model for refinement (gpt-4o-mini recommended for speed)
            on_iteration_complete: Optional callback after each iteration
        """
        self.max_iterations = max_iterations
        self.audio_duration = audio_duration
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.llm_model = llm_model
        self.on_iteration_complete = on_iteration_complete

        # Initialize components
        self.llm = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.audio_gen = ReplicateMusicGenerator(output_dir=str(self.output_dir))

        # Storage for iterations
        self.iterations: list[LoopIteration] = []
        self.session_id = f"loopism_{int(time.time())}"

        # Initialize Weave
        weave.init(WEAVE_PROJECT)
        print(f"✅ Weave initialized: {WEAVE_PROJECT}")

    @weave.op()
    def refine_prompt(self, current_prompt: str, iteration: int) -> dict:
        """
        Use LLM to critique and refine the audio prompt.

        This implements the CRITIQUE → REVISION phases from recursive-agents.
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
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=300
        )

        result = json.loads(response.choices[0].message.content)
        result["refinement_time"] = time.time() - start_time

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
        1. Critique current prompt
        2. Generate refined prompt
        3. Generate audio
        4. Store results
        5. Callback (if provided)

        Args:
            initial_prompt: User's original request (e.g., "happy piano")

        Returns:
            List of all iterations with audio paths
        """
        self.iterations = []
        current_prompt = initial_prompt

        print("\n" + "="*70)
        print("🔄 LOOPISM: Self-Improving Audio Generation")
        print("="*70)
        print(f"   Initial prompt: \"{initial_prompt}\"")
        print(f"   Iterations: {self.max_iterations}")
        print(f"   Audio duration: {self.audio_duration}s")
        print("="*70 + "\n")

        for i in range(self.max_iterations):
            print(f"\n{'─'*50}")
            print(f"ITERATION {i + 1}/{self.max_iterations}")
            print(f"{'─'*50}")

            # Phase 1: Critique and Refine
            print("\n📝 Phase 1: Critiquing and refining prompt...")
            refinement = self.refine_prompt(current_prompt, i)

            print(f"   💭 Critique: {refinement['critique']}")
            print(f"   ✨ Refined: {refinement['refined_prompt']}")
            print(f"   📈 Changes: {refinement['improvement_notes']}")

            # Phase 2: Generate Audio
            print("\n🎵 Phase 2: Generating audio...")
            audio_result = self.generate_audio(refinement['refined_prompt'], i)

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
                refinement_time=refinement['refinement_time']
            )
            self.iterations.append(iteration_data)

            # Callback for UI updates
            if self.on_iteration_complete:
                self.on_iteration_complete(iteration_data)

            # Update for next iteration
            current_prompt = refinement['refined_prompt']

        # Summary
        total_time = sum(it.generation_time + it.refinement_time for it in self.iterations)
        print(f"\n{'='*70}")
        print("✅ LOOPISM COMPLETE")
        print(f"   Total iterations: {len(self.iterations)}")
        print(f"   Total time: {total_time:.1f}s")
        print(f"   Initial: \"{initial_prompt}\"")
        print(f"   Final: \"{self.iterations[-1].refined_prompt}\"")
        print(f"   Outputs: {self.output_dir}")
        print(f"   Weave trace: https://wandb.ai/loopism/{WEAVE_PROJECT}/weave")
        print("="*70 + "\n")

        return self.iterations

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
            "iterations": [it.to_dict() for it in self.iterations]
        }


def test_engine():
    """Test the full Loopism pipeline."""
    print("\n" + "🧪 "*20)
    print("TESTING LOOPISM ENGINE")
    print("🧪 "*20 + "\n")

    engine = LoopismEngine(
        max_iterations=3,
        audio_duration=5,
        output_dir="test_loopism_outputs"
    )

    # Run with a simple prompt
    results = engine.run("happy summer vibes")

    # Print summary
    print("\n📊 RESULTS SUMMARY:")
    for it in results:
        print(f"\n   Iteration {it.iteration_num + 1}:")
        print(f"   Prompt: {it.refined_prompt[:60]}...")
        print(f"   Audio: {it.audio_path}")

    return results


if __name__ == "__main__":
    test_engine()
