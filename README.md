# 🔄 LOOPISM

**Self-Improving Audio Generation**

Watch AI refine its own music through iterative self-critique.

## Quick Start

```bash
# 1. Copy and configure API keys
cp .env.template .env
# Edit .env with your keys

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
./run.sh
# Or: streamlit run app.py
```

## API Keys Required

- **REPLICATE_API_TOKEN** - Get from https://replicate.com/account/api-tokens
- **OPENAI_API_KEY** - Get from https://platform.openai.com/api-keys
- **WANDB_API_KEY** - Get from https://wandb.ai/authorize

## Architecture

1. **User Input** → Simple prompt (e.g., "happy piano")
2. **Critique Loop** (recursive-agents) → LLM critiques and refines prompt
3. **Audio Generation** (Replicate) → MusicGen creates audio
4. **Iterate** → Repeat with improved prompt
5. **Compare** → Hear all iterations side-by-side

## Tech Stack

- **recursive-agents**: Self-critique loops
- **deep-research**: Iterative exploration architecture
- **Replicate API**: Cloud-based MusicGen (no GPU needed)
- **W&B Weave**: Full observability and tracing
- **Streamlit**: Beautiful interactive UI

## Project Structure

```
loopism/
├── deep-research/          # Cloned repo (fractal exploration reference)
├── recursive-agents/       # Cloned repo (self-critique loops)
├── audio_generator.py      # Replicate MusicGen wrapper
├── loopism_core.py         # Main engine with Weave tracing
├── app.py                  # Streamlit UI
├── requirements.txt        # Dependencies
├── run.sh                  # Launch script
├── .env.template           # API keys template
└── loopism_outputs/        # Generated audio files
```

## Built for WeaveHacks 3
