"""
LOOPISM - Self-Improving Audio Generation
Streamlit UI for WeaveHacks Demo

Features:
- Real-time iteration display
- Side-by-side audio comparison
- Weave trace integration
- Beautiful dark theme
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

import streamlit as st

# Load environment variables
load_dotenv()

# Import Loopism engine
from loopism_core import LoopismEngine, LoopIteration

# Page configuration
st.set_page_config(
    page_title="Loopism - Self-Improving Audio",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');

    /* Global theme */
    .stApp {
        background: linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 50%, #0f0f1a 100%);
        font-family: 'Space Grotesk', sans-serif;
    }

    /* Title */
    .loopism-title {
        font-size: 4.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00d4ff 0%, #7b2ff7 50%, #ff0080 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0;
        text-shadow: 0 0 40px rgba(123, 47, 247, 0.3);
    }

    .loopism-subtitle {
        font-size: 1.3rem;
        color: #666;
        text-align: center;
        margin-top: 5px;
        letter-spacing: 2px;
    }

    /* Iteration cards */
    .iteration-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 20px;
        padding: 25px;
        margin: 15px 0;
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }

    .iteration-card:hover {
        transform: translateY(-5px);
        border-color: rgba(0, 212, 255, 0.5);
        box-shadow: 0 20px 40px rgba(0, 212, 255, 0.1);
    }

    .iteration-number {
        font-size: 5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00d4ff, #7b2ff7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        opacity: 0.2;
        position: absolute;
        top: 10px;
        right: 20px;
    }

    /* Audio player */
    audio {
        width: 100%;
        border-radius: 10px;
        margin: 15px 0;
    }

    audio::-webkit-media-controls-panel {
        background: linear-gradient(135deg, #1a1a2e, #2a2a4e);
    }

    /* Critique box */
    .critique-box {
        background: rgba(123, 47, 247, 0.1);
        border-left: 4px solid #7b2ff7;
        padding: 15px 20px;
        margin: 15px 0;
        border-radius: 0 12px 12px 0;
        font-style: italic;
        color: #a0a0ff;
    }

    /* Prompt display */
    .prompt-box {
        background: rgba(0, 212, 255, 0.08);
        border: 1px solid rgba(0, 212, 255, 0.2);
        padding: 20px;
        border-radius: 12px;
        font-family: 'JetBrains Mono', monospace;
        color: #00d4ff;
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* Progress indicator */
    .progress-container {
        display: flex;
        justify-content: center;
        gap: 15px;
        margin: 30px 0;
    }

    .progress-dot {
        width: 16px;
        height: 16px;
        border-radius: 50%;
        transition: all 0.3s ease;
    }

    .progress-dot.active {
        background: #00d4ff;
        box-shadow: 0 0 20px #00d4ff, 0 0 40px rgba(0, 212, 255, 0.5);
        animation: pulse 1s infinite;
    }

    .progress-dot.completed {
        background: linear-gradient(135deg, #7b2ff7, #00d4ff);
    }

    .progress-dot.pending {
        background: transparent;
        border: 2px solid #333;
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.2); }
    }

    /* Badges */
    .tech-badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 5px;
    }

    .badge-weave {
        background: linear-gradient(135deg, #ff6b35, #f7931e);
        color: white;
    }

    .badge-replicate {
        background: linear-gradient(135deg, #0066ff, #00d4ff);
        color: white;
    }

    .badge-recursive {
        background: linear-gradient(135deg, #7b2ff7, #ff0080);
        color: white;
    }

    /* Stats */
    .stat-box {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
    }

    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00d4ff, #7b2ff7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .stat-label {
        color: #666;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #7b2ff7 0%, #00d4ff 100%);
        color: white;
        border: none;
        padding: 15px 40px;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 30px;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 30px rgba(123, 47, 247, 0.4);
    }

    /* Input styling */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.05);
        border: 2px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        color: white;
        font-size: 1.1rem;
        padding: 15px 20px;
    }

    .stTextInput > div > div > input:focus {
        border-color: #00d4ff;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if "iterations" not in st.session_state:
    st.session_state.iterations = []
if "running" not in st.session_state:
    st.session_state.running = False
if "current_iteration" not in st.session_state:
    st.session_state.current_iteration = 0

# ============ HEADER ============
st.markdown('<h1 class="loopism-title">🔄 LOOPISM</h1>', unsafe_allow_html=True)
st.markdown('<p class="loopism-subtitle">SELF-IMPROVING AUDIO GENERATION</p>', unsafe_allow_html=True)

# Tech badges
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.markdown(
        '<div style="text-align: center; margin: 25px 0;">'
        '<span class="tech-badge badge-weave">⚡ W&B Weave</span>'
        '<span class="tech-badge badge-replicate">🎵 Replicate MusicGen</span>'
        '<span class="tech-badge badge-recursive">🔁 Recursive Agents</span>'
        '</div>',
        unsafe_allow_html=True
    )

# ============ SIDEBAR ============
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    # Check for API keys
    replicate_key = os.environ.get("REPLICATE_API_TOKEN", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")

    if not replicate_key:
        replicate_key = st.text_input("Replicate API Token", type="password")
        if replicate_key:
            os.environ["REPLICATE_API_TOKEN"] = replicate_key
    else:
        st.success("✅ Replicate API configured")

    if not openai_key:
        openai_key = st.text_input("OpenAI API Key", type="password")
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key
    else:
        st.success("✅ OpenAI API configured")

    st.markdown("---")

    max_iterations = st.slider(
        "🔄 Iterations",
        min_value=2,
        max_value=5,
        value=3,
        help="More iterations = more refinement"
    )

    audio_duration = st.slider(
        "⏱️ Audio Duration (sec)",
        min_value=3,
        max_value=10,
        value=5,
        help="Shorter = faster generation"
    )

    st.markdown("---")
    st.markdown("### 🎯 Quick Prompts")

    quick_prompts = [
        ("🌴", "happy summer vibes"),
        ("🎬", "epic cinematic trailer"),
        ("☕", "chill lofi study beats"),
        ("⚡", "energetic workout music"),
        ("🌙", "ambient night atmosphere"),
    ]

    for emoji, prompt in quick_prompts:
        if st.button(f"{emoji} {prompt}", key=f"quick_{prompt}", use_container_width=True):
            st.session_state.selected_prompt = prompt

    st.markdown("---")
    st.markdown("### 📊 Weave Dashboard")
    st.markdown("[Open Weave Traces →](https://wandb.ai/)")

# ============ MAIN CONTENT ============
st.markdown("---")

# Input section
col1, col2 = st.columns([4, 1])

with col1:
    default_prompt = st.session_state.get("selected_prompt", "")
    user_prompt = st.text_input(
        "🎵 Describe the audio you want to create:",
        value=default_prompt,
        placeholder="e.g., 'peaceful piano melody' or 'driving electronic beat'"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    generate_btn = st.button(
        "🚀 Generate",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.running or not user_prompt
    )

# Check if we can run
can_run = (
    os.environ.get("REPLICATE_API_TOKEN") and
    os.environ.get("OPENAI_API_KEY") and
    user_prompt
)

if generate_btn and can_run:
    st.session_state.running = True
    st.session_state.iterations = []
    st.session_state.current_iteration = 0

    # Progress display
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    iterations_placeholder = st.container()

    # Callback for live updates
    def on_iteration(iteration: LoopIteration):
        st.session_state.iterations.append(iteration)
        st.session_state.current_iteration = iteration.iteration_num + 1

    # Create and run engine
    try:
        engine = LoopismEngine(
            max_iterations=max_iterations,
            audio_duration=audio_duration,
            output_dir="loopism_outputs",
            on_iteration_complete=on_iteration
        )

        with st.spinner("🎵 Generating and refining audio..."):
            results = engine.run(user_prompt)

        st.session_state.results = engine.get_comparison_data()
        st.success("✅ Generation complete! Compare the iterations below.")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

    st.session_state.running = False

# ============ RESULTS DISPLAY ============
if st.session_state.iterations:
    st.markdown("---")
    st.markdown("## 🎧 Iteration Comparison")
    st.markdown("*Listen to how the audio improves with each refinement*")

    # Create columns for iterations
    cols = st.columns(len(st.session_state.iterations))

    for col, iteration in zip(cols, st.session_state.iterations):
        with col:
            # Card container
            st.markdown(f"""
            <div class="iteration-card" style="position: relative;">
                <span class="iteration-number">#{iteration.iteration_num + 1}</span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"### Iteration {iteration.iteration_num + 1}")

            # Audio player
            if os.path.exists(iteration.audio_path):
                st.audio(iteration.audio_path)
                st.caption(f"⏱️ Generated in {iteration.generation_time:.1f}s")

            # Critique
            with st.expander("💭 AI Critique", expanded=False):
                st.markdown(f'<div class="critique-box">{iteration.critique}</div>', unsafe_allow_html=True)

            # Refined prompt
            with st.expander("📝 Refined Prompt", expanded=True):
                st.markdown(f'<div class="prompt-box">{iteration.refined_prompt}</div>', unsafe_allow_html=True)

            # Changes
            with st.expander("📈 Improvements", expanded=False):
                st.write(iteration.improvement_notes)

    # Stats summary
    st.markdown("---")
    st.markdown("## 📊 Session Statistics")

    results = st.session_state.get("results", {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-value">{results.get('total_iterations', 0)}</div>
            <div class="stat-label">Iterations</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-value">{results.get('total_time', 0):.1f}s</div>
            <div class="stat-label">Total Time</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        avg_time = results.get('total_time', 0) / max(1, results.get('total_iterations', 1))
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-value">{avg_time:.1f}s</div>
            <div class="stat-label">Avg per Iteration</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-value">{audio_duration}s</div>
            <div class="stat-label">Clip Duration</div>
        </div>
        """, unsafe_allow_html=True)

    # Before/After comparison
    st.markdown("---")
    st.markdown("## 🔄 Before & After")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📥 Initial Request")
        st.info(results.get('initial_prompt', 'N/A'))

    with col2:
        st.markdown("### 📤 Final Refined Prompt")
        st.success(results.get('final_prompt', 'N/A'))

    # Weave link
    st.markdown("---")
    st.markdown("""
    ### 🔍 Full Trace in Weave

    Every LLM call and audio generation is traced with W&B Weave.
    View the complete execution graph, latencies, and costs.

    [**Open Weave Dashboard →**](https://wandb.ai/)
    """)

# ============ FOOTER ============
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #444; font-size: 0.85rem; padding: 20px;">
    <strong>LOOPISM</strong> • Built for WeaveHacks 3<br>
    Powered by Recursive Agents + Replicate MusicGen + W&B Weave<br>
    <em>Watch AI improve its own music through self-critique</em>
</div>
""", unsafe_allow_html=True)
