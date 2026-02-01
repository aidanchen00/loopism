"""
Loopism Audio Generator
Uses Replicate's hosted MusicGen model for fast cloud-based generation.
No GPU required - runs on Replicate's infrastructure.

Speed: ~5-10 seconds per 5-second clip
Cost: ~$0.01 per generation
"""

import os
import replicate
import requests
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class ReplicateMusicGenerator:
    """
    Cloud-based music generation via Replicate API.
    Uses Meta's MusicGen model hosted on Replicate's GPUs.
    """

    # MusicGen model on Replicate (latest stable version)
    MODEL_ID = "meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb"

    def __init__(self, output_dir: str = "loopism_outputs"):
        """
        Initialize the generator.

        Args:
            output_dir: Directory to save generated audio files
        """
        self.api_token = os.environ.get("REPLICATE_API_TOKEN")
        if not self.api_token:
            raise ValueError(
                "REPLICATE_API_TOKEN not found!\n"
                "Get your token from: https://replicate.com/account/api-tokens\n"
                "Then set it: export REPLICATE_API_TOKEN='r8_...'"
            )

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Track generation stats
        self.total_generations = 0
        self.total_time = 0.0

    def generate(
        self,
        prompt: str,
        duration: int = 5,
        output_name: str = None,
        model_version: str = "stereo-large"
    ) -> dict:
        """
        Generate audio from text prompt via Replicate API.

        Args:
            prompt: Text description of desired audio
            duration: Length in seconds (1-30, default 5)
            output_name: Filename without extension (auto-generated if None)
            model_version: "stereo-large" (best) or "stereo-melody-large" (for melody conditioning)

        Returns:
            dict with keys: audio_path, audio_url, prompt, duration, generation_time
        """
        start_time = time.time()

        print(f"🎵 Generating audio: '{prompt[:50]}...'")
        print(f"   Duration: {duration}s | Model: {model_version}")

        try:
            # Call Replicate API - use the model without version hash to get latest
            output = replicate.run(
                "meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb",
                input={
                    "prompt": prompt,
                    "duration": duration,
                    "model_version": model_version,
                    "output_format": "wav",
                    "normalization_strategy": "loudness",
                    "top_k": 250,
                    "top_p": 0.0,
                    "temperature": 1.0,
                    "classifier_free_guidance": 3
                }
            )

            # output is a URL to the generated audio
            audio_url = output

            # Download the audio file
            if output_name is None:
                output_name = f"gen_{int(time.time())}"

            audio_path = self.output_dir / f"{output_name}.wav"

            response = requests.get(audio_url, timeout=30)
            response.raise_for_status()

            with open(audio_path, "wb") as f:
                f.write(response.content)

            generation_time = time.time() - start_time
            self.total_generations += 1
            self.total_time += generation_time

            print(f"   ✅ Generated in {generation_time:.1f}s → {audio_path}")

            return {
                "audio_path": str(audio_path),
                "audio_url": audio_url,
                "prompt": prompt,
                "duration": duration,
                "generation_time": generation_time,
                "model_version": model_version
            }

        except replicate.exceptions.ReplicateError as e:
            print(f"   ❌ Replicate error: {e}")
            raise
        except requests.RequestException as e:
            print(f"   ❌ Download error: {e}")
            raise

    def generate_batch(self, prompts: list[str], duration: int = 5) -> list[dict]:
        """
        Generate multiple audio clips.

        Args:
            prompts: List of text prompts
            duration: Duration for each clip

        Returns:
            List of generation results
        """
        results = []
        for i, prompt in enumerate(prompts):
            result = self.generate(
                prompt=prompt,
                duration=duration,
                output_name=f"batch_{i}"
            )
            results.append(result)
        return results

    def get_stats(self) -> dict:
        """Return generation statistics."""
        return {
            "total_generations": self.total_generations,
            "total_time": self.total_time,
            "average_time": self.total_time / max(1, self.total_generations)
        }


def test_generator():
    """Quick test of the generator."""
    print("\n" + "="*60)
    print("TESTING REPLICATE MUSIC GENERATOR")
    print("="*60 + "\n")

    gen = ReplicateMusicGenerator(output_dir="test_outputs")

    result = gen.generate(
        prompt="upbeat electronic music with synth arpeggios, 120 BPM",
        duration=5,
        output_name="test_clip"
    )

    print(f"\n✅ Test successful!")
    print(f"   Audio saved to: {result['audio_path']}")
    print(f"   Generation time: {result['generation_time']:.1f}s")

    return result


if __name__ == "__main__":
    test_generator()
