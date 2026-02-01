"""
Verify Weave tracing is set up correctly.
Run this after setting up your WANDB_API_KEY.
"""

import os
from dotenv import load_dotenv

load_dotenv()

def verify():
    print("🔍 Verifying Weave Setup...")
    print()

    # Check API key
    wandb_key = os.environ.get("WANDB_API_KEY")
    if not wandb_key:
        print("❌ WANDB_API_KEY not set")
        print("   Get your key from: https://wandb.ai/authorize")
        return False
    else:
        print(f"✅ WANDB_API_KEY found ({wandb_key[:8]}...)")

    # Try importing weave
    try:
        import weave
        print("✅ Weave imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import weave: {e}")
        print("   Run: pip install weave")
        return False

    # Try initializing
    try:
        weave.init("loopism-audio-refinement")
        print("✅ Weave initialized: loopism-audio-refinement")
    except Exception as e:
        print(f"❌ Failed to initialize weave: {e}")
        return False

    print()
    print("=" * 50)
    print("✅ Weave setup complete!")
    print()
    print("After running Loopism, you'll see traces at:")
    print("   https://wandb.ai/")
    print()
    print("Traces will include:")
    print("   - run() traces (parent)")
    print("   - refine_prompt() traces (LLM calls)")
    print("   - generate_audio() traces (Replicate calls)")
    print("=" * 50)

    return True


if __name__ == "__main__":
    verify()
