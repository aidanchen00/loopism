"""
██╗      ██████╗  ██████╗ ██████╗ ██╗███████╗███╗   ███╗
██║     ██╔═══██╗██╔═══██╗██╔══██╗██║██╔════╝████╗ ████║
██║     ██║   ██║██║   ██║██████╔╝██║███████╗██╔████╔██║
██║     ██║   ██║██║   ██║██╔═══╝ ██║╚════██║██║╚██╔╝██║
███████╗╚██████╔╝╚██████╔╝██║     ██║███████║██║ ╚═╝ ██║
╚══════╝ ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚══════╝╚═╝     ╚═╝

LOOPISM - Self-Improving Audio Generation
Mission Control Interface for WeaveHacks 3

Aesthetic: Retrofuturist Terminal / Mission Control
- CRT phosphor glow effects
- Scanline overlay
- Mission timeline layout
- Self-learning intelligence dashboard
"""

import os
import time
import base64
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import streamlit as st
import streamlit.components.v1 as components

load_dotenv()

from loopism_core import LoopismEngine, LoopIteration
from learning import get_learning_system, get_metrics, record_feedback
from cache_loader import (
    is_prompt_cached,
    load_cached_metadata,
    load_cached_comparison_data,
    stream_cached_iterations,
    verify_cache_integrity
)
from local_storage import (
    get_stats as get_local_stats,
    save_learned_pattern,
    save_user_rating,
    get_all_patterns,
    get_all_ratings,
    get_all_sessions
)

# ═══════════════════════════════════════════════════════════════════════════════
# AUDIO VISUALIZER COMPONENT
# ═══════════════════════════════════════════════════════════════════════════════

def create_audio_visualizer(audio_path: str, component_id: str, height: int = 200) -> str:
    """
    Create an HTML/JS audio visualizer with frequency bars that respond to audio playback.
    Uses Web Audio API for real-time frequency analysis.
    """
    # Read and encode audio file as base64
    with open(audio_path, 'rb') as f:
        audio_data = base64.b64encode(f.read()).decode('utf-8')

    # Determine MIME type
    ext = Path(audio_path).suffix.lower()
    mime_types = {'.wav': 'audio/wav', '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.m4a': 'audio/mp4'}
    mime_type = mime_types.get(ext, 'audio/wav')

    html = f'''
    <div id="visualizer-container-{component_id}" style="
        background: #0a0a0a;
        border: 1px solid #333333;
        padding: 1rem;
        margin: 0.5rem 0;
        font-family: 'JetBrains Mono', monospace;
    ">
        <div style="
            font-size: 0.6rem;
            color: #00ff88;
            letter-spacing: 0.2em;
            margin-bottom: 0.5rem;
            text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
        ">◎ FREQUENCY SPECTRUM</div>

        <canvas id="canvas-{component_id}" width="400" height="{height}" style="
            width: 100%;
            height: {height}px;
            background: linear-gradient(180deg, #0a0a0a 0%, #0d0d0d 100%);
            border: 1px solid #222222;
        "></canvas>

        <div style="
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-top: 0.75rem;
            padding-top: 0.75rem;
            border-top: 1px solid #222222;
        ">
            <button id="playBtn-{component_id}" onclick="togglePlay_{component_id}()" style="
                background: linear-gradient(180deg, #1a1a1a 0%, #0d0d0d 100%);
                border: 1px solid #ffb000;
                color: #ffb000;
                padding: 0.5rem 1.5rem;
                font-family: 'Orbitron', sans-serif;
                font-size: 0.7rem;
                letter-spacing: 0.15em;
                cursor: pointer;
                text-transform: uppercase;
                box-shadow: 0 0 10px rgba(255, 176, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.05);
                transition: all 0.2s ease;
            ">▶ PLAY</button>

            <div style="flex: 1; display: flex; align-items: center; gap: 0.5rem;">
                <span id="currentTime-{component_id}" style="
                    font-size: 0.65rem;
                    color: #888888;
                    min-width: 35px;
                ">0:00</span>
                <div style="
                    flex: 1;
                    height: 4px;
                    background: #1a1a1a;
                    border: 1px solid #333333;
                    position: relative;
                    cursor: pointer;
                " id="progressBar-{component_id}" onclick="seek_{component_id}(event)">
                    <div id="progress-{component_id}" style="
                        height: 100%;
                        background: linear-gradient(90deg, #ffb000, #00ffff);
                        width: 0%;
                        box-shadow: 0 0 8px rgba(255, 176, 0, 0.6);
                        transition: width 0.1s linear;
                    "></div>
                </div>
                <span id="duration-{component_id}" style="
                    font-size: 0.65rem;
                    color: #888888;
                    min-width: 35px;
                ">0:00</span>
            </div>

            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 0.6rem; color: #555555;">VOL</span>
                <input type="range" id="volume-{component_id}" min="0" max="100" value="80"
                    oninput="setVolume_{component_id}(this.value)"
                    style="width: 60px; accent-color: #00ffff;">
            </div>
        </div>
    </div>

    <script>
    (function() {{
        const componentId = "{component_id}";
        const canvas = document.getElementById("canvas-" + componentId);
        const ctx = canvas.getContext("2d");
        const playBtn = document.getElementById("playBtn-" + componentId);
        const currentTimeEl = document.getElementById("currentTime-" + componentId);
        const durationEl = document.getElementById("duration-" + componentId);
        const progressEl = document.getElementById("progress-" + componentId);
        const progressBar = document.getElementById("progressBar-" + componentId);

        let audioContext = null;
        let analyser = null;
        let source = null;
        let audio = null;
        let isPlaying = false;
        let animationId = null;
        let dataArray = null;

        // Initialize audio
        audio = new Audio("data:{mime_type};base64,{audio_data}");
        audio.volume = 0.8;
        audio.crossOrigin = "anonymous";

        audio.addEventListener('loadedmetadata', function() {{
            durationEl.textContent = formatTime(audio.duration);
        }});

        audio.addEventListener('timeupdate', function() {{
            currentTimeEl.textContent = formatTime(audio.currentTime);
            const percent = (audio.currentTime / audio.duration) * 100;
            progressEl.style.width = percent + "%";
        }});

        audio.addEventListener('ended', function() {{
            isPlaying = false;
            playBtn.innerHTML = "▶ PLAY";
            playBtn.style.borderColor = "#ffb000";
            playBtn.style.color = "#ffb000";
            if (animationId) cancelAnimationFrame(animationId);
            drawIdleState();
        }});

        function formatTime(seconds) {{
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return mins + ":" + (secs < 10 ? "0" : "") + secs;
        }}

        function initAudioContext() {{
            if (!audioContext) {{
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                analyser = audioContext.createAnalyser();
                analyser.fftSize = 256;
                analyser.smoothingTimeConstant = 0.8;

                source = audioContext.createMediaElementSource(audio);
                source.connect(analyser);
                analyser.connect(audioContext.destination);

                dataArray = new Uint8Array(analyser.frequencyBinCount);
            }}
        }}

        function drawIdleState() {{
            const width = canvas.width;
            const height = canvas.height;
            ctx.clearRect(0, 0, width, height);

            // Draw subtle grid
            ctx.strokeStyle = "rgba(255, 176, 0, 0.05)";
            ctx.lineWidth = 1;
            for (let i = 0; i < width; i += 20) {{
                ctx.beginPath();
                ctx.moveTo(i, 0);
                ctx.lineTo(i, height);
                ctx.stroke();
            }}
            for (let i = 0; i < height; i += 20) {{
                ctx.beginPath();
                ctx.moveTo(0, i);
                ctx.lineTo(width, i);
                ctx.stroke();
            }}

            // Draw idle bars
            const barCount = 64;
            const barWidth = (width / barCount) - 2;
            const centerY = height / 2;

            for (let i = 0; i < barCount; i++) {{
                const x = i * (barWidth + 2);
                const idleHeight = 4 + Math.sin(i * 0.2) * 2;

                const gradient = ctx.createLinearGradient(0, centerY - idleHeight, 0, centerY + idleHeight);
                gradient.addColorStop(0, "rgba(255, 176, 0, 0.3)");
                gradient.addColorStop(0.5, "rgba(0, 255, 255, 0.2)");
                gradient.addColorStop(1, "rgba(255, 176, 0, 0.3)");

                ctx.fillStyle = gradient;
                ctx.fillRect(x, centerY - idleHeight, barWidth, idleHeight * 2);
            }}
        }}

        function draw() {{
            if (!isPlaying) return;

            animationId = requestAnimationFrame(draw);
            analyser.getByteFrequencyData(dataArray);

            const width = canvas.width;
            const height = canvas.height;
            ctx.clearRect(0, 0, width, height);

            // Draw grid
            ctx.strokeStyle = "rgba(255, 176, 0, 0.03)";
            ctx.lineWidth = 1;
            for (let i = 0; i < width; i += 20) {{
                ctx.beginPath();
                ctx.moveTo(i, 0);
                ctx.lineTo(i, height);
                ctx.stroke();
            }}

            // Draw frequency bars
            const barCount = 64;
            const barWidth = (width / barCount) - 2;
            const centerY = height / 2;

            for (let i = 0; i < barCount; i++) {{
                const dataIndex = Math.floor(i * (dataArray.length / barCount));
                const value = dataArray[dataIndex];
                const barHeight = (value / 255) * (height * 0.45);
                const x = i * (barWidth + 2);

                // Color based on frequency (rainbow spectrum like the reference image)
                const hue = (i / barCount) * 300 + 270; // Purple to red to yellow to green to cyan
                const saturation = 80 + (value / 255) * 20;
                const lightness = 45 + (value / 255) * 15;

                // Main bar gradient
                const gradient = ctx.createLinearGradient(0, centerY - barHeight, 0, centerY + barHeight);
                gradient.addColorStop(0, `hsla(${{hue}}, ${{saturation}}%, ${{lightness + 20}}%, 0.9)`);
                gradient.addColorStop(0.3, `hsla(${{hue}}, ${{saturation}}%, ${{lightness}}%, 1)`);
                gradient.addColorStop(0.5, `hsla(${{hue}}, ${{saturation + 10}}%, ${{lightness + 10}}%, 1)`);
                gradient.addColorStop(0.7, `hsla(${{hue}}, ${{saturation}}%, ${{lightness}}%, 1)`);
                gradient.addColorStop(1, `hsla(${{hue}}, ${{saturation}}%, ${{lightness + 20}}%, 0.9)`);

                ctx.fillStyle = gradient;

                // Draw bar (symmetric around center)
                ctx.fillRect(x, centerY - barHeight, barWidth, barHeight * 2);

                // Glow effect
                ctx.shadowColor = `hsla(${{hue}}, 100%, 60%, 0.5)`;
                ctx.shadowBlur = 8;
                ctx.fillRect(x, centerY - barHeight, barWidth, barHeight * 2);
                ctx.shadowBlur = 0;

                // Reflection (subtle)
                const reflectionGradient = ctx.createLinearGradient(0, centerY + barHeight, 0, centerY + barHeight + barHeight * 0.4);
                reflectionGradient.addColorStop(0, `hsla(${{hue}}, ${{saturation}}%, ${{lightness}}%, 0.3)`);
                reflectionGradient.addColorStop(1, "transparent");
                ctx.fillStyle = reflectionGradient;
                ctx.fillRect(x, centerY + barHeight, barWidth, barHeight * 0.4);
            }}
        }}

        window["togglePlay_" + componentId] = function() {{
            initAudioContext();

            if (audioContext.state === 'suspended') {{
                audioContext.resume();
            }}

            if (isPlaying) {{
                audio.pause();
                isPlaying = false;
                playBtn.innerHTML = "▶ PLAY";
                playBtn.style.borderColor = "#ffb000";
                playBtn.style.color = "#ffb000";
                if (animationId) cancelAnimationFrame(animationId);
            }} else {{
                audio.play();
                isPlaying = true;
                playBtn.innerHTML = "⏸ PAUSE";
                playBtn.style.borderColor = "#00ffff";
                playBtn.style.color = "#00ffff";
                draw();
            }}
        }};

        window["seek_" + componentId] = function(event) {{
            const rect = progressBar.getBoundingClientRect();
            const percent = (event.clientX - rect.left) / rect.width;
            audio.currentTime = percent * audio.duration;
        }};

        window["setVolume_" + componentId] = function(value) {{
            audio.volume = value / 100;
        }};

        // Initial idle state
        drawIdleState();

        // Resize handler
        function resizeCanvas() {{
            const container = canvas.parentElement;
            canvas.width = container.offsetWidth - 32;
        }}
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
    }})();
    </script>
    '''
    return html


def render_audio_visualizer(audio_path: str, iteration_num: int):
    """Render the audio visualizer component for a given audio file."""
    try:
        if not os.path.exists(audio_path):
            st.warning(f"Audio file not found: {audio_path}")
            return

        component_id = f"viz_{iteration_num}_{hash(audio_path) % 10000}"
        html_content = create_audio_visualizer(audio_path, component_id, height=120)
        components.html(html_content, height=220)
    except Exception as e:
        st.error(f"Error loading audio visualizer: {str(e)}")
        # Fallback to native audio player
        st.audio(audio_path)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="LOOPISM // Mission Control",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM CSS - RETROFUTURIST TERMINAL AESTHETIC
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    /* ═══════════════════════════════════════════════════════════════════════
       FONTS
       ═══════════════════════════════════════════════════════════════════════ */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Orbitron:wght@400;500;600;700;800;900&display=swap');

    /* ═══════════════════════════════════════════════════════════════════════
       CSS VARIABLES
       ═══════════════════════════════════════════════════════════════════════ */
    :root {
        --bg-void: #0a0a0a;
        --bg-panel: #0d0d0d;
        --bg-elevated: #141414;
        --bg-hover: #1a1a1a;

        --phosphor-amber: #ffb000;
        --phosphor-amber-dim: #cc8c00;
        --phosphor-amber-glow: rgba(255, 176, 0, 0.6);
        --phosphor-amber-subtle: rgba(255, 176, 0, 0.1);

        --cyan-electric: #00ffff;
        --cyan-dim: #00cccc;
        --cyan-glow: rgba(0, 255, 255, 0.5);
        --cyan-subtle: rgba(0, 255, 255, 0.08);

        --text-primary: #e0e0e0;
        --text-secondary: #888888;
        --text-dim: #888888;

        --border-subtle: #222222;
        --border-active: #333333;

        --danger: #ff4444;
        --success: #00ff88;
        --warning: #ffaa00;

        --font-mono: 'JetBrains Mono', 'Consolas', monospace;
        --font-display: 'Orbitron', sans-serif;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       GLOBAL RESET & BASE
       ═══════════════════════════════════════════════════════════════════════ */
    .stApp {
        background: var(--bg-void);
        font-family: var(--font-mono);
    }

    /* Scanline overlay */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: repeating-linear-gradient(
            0deg,
            rgba(0, 0, 0, 0.15),
            rgba(0, 0, 0, 0.15) 1px,
            transparent 1px,
            transparent 2px
        );
        pointer-events: none;
        z-index: 9999;
    }

    /* CRT vignette */
    .stApp::after {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: radial-gradient(
            ellipse at center,
            transparent 0%,
            transparent 60%,
            rgba(0, 0, 0, 0.4) 100%
        );
        pointer-events: none;
        z-index: 9998;
    }

    /* Hide Streamlit branding but keep sidebar toggle */
    #MainMenu, footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* ═══════════════════════════════════════════════════════════════════════
       SIDEBAR FIX - Ensure sidebar toggle is always accessible
       ═══════════════════════════════════════════════════════════════════════ */
    /* Keep header visible so sidebar toggle button is accessible */
    header[data-testid="stHeader"] {
        visibility: visible !important;
        z-index: 99997 !important;
    }
    
    /* Make sure sidebar toggle button is always visible and styled */
    button[kind="header"] {
        visibility: visible !important;
        display: block !important;
        z-index: 99999 !important;
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border-subtle) !important;
        color: var(--phosphor-amber) !important;
        padding: 0.5rem !important;
        margin: 0.5rem !important;
    }
    
    button[kind="header"]:hover {
        background: var(--bg-hover) !important;
        box-shadow: 0 0 8px rgba(255, 176, 0, 0.3) !important;
    }
    
    /* Ensure sidebar can be toggled smoothly */
    .stSidebar {
        transition: margin-left 0.3s ease;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       TYPOGRAPHY
       ═══════════════════════════════════════════════════════════════════════ */
    h1, h2, h3, h4, h5, h6 {
        font-family: var(--font-display) !important;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }

    p, span, div, label {
        font-family: var(--font-mono);
    }

    /* ═══════════════════════════════════════════════════════════════════════
       HEADER
       ═══════════════════════════════════════════════════════════════════════ */
    .mission-header {
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-subtle);
        position: relative;
    }

    .mission-header::before {
        content: "◎ MISSION CONTROL ◎";
        display: block;
        font-family: var(--font-mono);
        font-size: 0.7rem;
        color: var(--phosphor-amber);
        letter-spacing: 0.4em;
        margin-bottom: 1rem;
        text-shadow: 0 0 10px var(--phosphor-amber-glow);
    }

    .logo-text {
        font-family: var(--font-display);
        font-size: 4rem;
        font-weight: 900;
        color: var(--phosphor-amber);
        letter-spacing: 0.2em;
        text-shadow:
            0 0 10px var(--phosphor-amber-glow),
            0 0 20px var(--phosphor-amber-glow),
            0 0 40px var(--phosphor-amber-glow),
            0 0 80px rgba(255, 176, 0, 0.3);
        animation: flicker 4s infinite;
    }

    @keyframes flicker {
        0%, 100% { opacity: 1; }
        92% { opacity: 1; }
        93% { opacity: 0.8; }
        94% { opacity: 1; }
        96% { opacity: 0.9; }
        97% { opacity: 1; }
    }

    .tagline {
        font-family: var(--font-mono);
        font-size: 0.85rem;
        color: var(--text-secondary);
        letter-spacing: 0.3em;
        margin-top: 0.5rem;
    }

    .tech-stack {
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        margin-top: 1.5rem;
    }

    .tech-badge {
        font-family: var(--font-mono);
        font-size: 0.65rem;
        padding: 0.4rem 0.8rem;
        border: 1px solid var(--border-active);
        color: var(--text-secondary);
        letter-spacing: 0.1em;
        background: var(--bg-panel);
    }

    .tech-badge.active {
        border-color: var(--cyan-electric);
        color: var(--cyan-electric);
        box-shadow: 0 0 10px var(--cyan-glow), inset 0 0 10px var(--cyan-subtle);
    }

    /* ═══════════════════════════════════════════════════════════════════════
       LEARNING STATUS BADGE
       ═══════════════════════════════════════════════════════════════════════ */
    .learning-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(0, 255, 136, 0.1);
        border: 1px solid var(--success);
        padding: 0.5rem 1rem;
        margin: 1rem auto;
        font-family: var(--font-mono);
        font-size: 0.75rem;
        color: var(--success);
        letter-spacing: 0.1em;
        animation: pulse-border 2s infinite;
    }

    @keyframes pulse-border {
        0%, 100% { box-shadow: 0 0 5px rgba(0, 255, 136, 0.3); }
        50% { box-shadow: 0 0 20px rgba(0, 255, 136, 0.6), 0 0 30px rgba(0, 255, 136, 0.3); }
    }

    .learning-badge::before {
        content: "🧠";
        animation: brain-pulse 1.5s infinite;
    }

    @keyframes brain-pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }

    /* ═══════════════════════════════════════════════════════════════════════
       INTELLIGENCE DASHBOARD
       ═══════════════════════════════════════════════════════════════════════ */
    .intel-dashboard {
        background: var(--bg-panel);
        border: 1px solid var(--success);
        margin: 1rem 0;
        padding: 0;
        position: relative;
    }

    .intel-dashboard::before {
        content: "◎ INTELLIGENCE DASHBOARD";
        position: absolute;
        top: -0.6rem;
        left: 1rem;
        background: var(--bg-panel);
        padding: 0 0.5rem;
        font-family: var(--font-display);
        font-size: 0.65rem;
        color: var(--success);
        letter-spacing: 0.2em;
    }

    .intel-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1px;
        background: var(--border-subtle);
        padding: 1px;
    }

    .intel-card {
        background: var(--bg-panel);
        padding: 1.2rem;
        text-align: center;
    }

    .intel-value {
        font-family: var(--font-display);
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--success);
        text-shadow: 0 0 15px rgba(0, 255, 136, 0.5);
    }

    .intel-label {
        font-family: var(--font-mono);
        font-size: 0.6rem;
        color: var(--text-secondary);
        letter-spacing: 0.15em;
        text-transform: uppercase;
        margin-top: 0.3rem;
    }

    .intel-delta {
        font-family: var(--font-mono);
        font-size: 0.65rem;
        margin-top: 0.3rem;
    }

    .intel-delta.positive {
        color: var(--success);
    }

    .intel-delta.negative {
        color: var(--danger);
    }

    .intel-patterns {
        padding: 1rem;
        border-top: 1px solid var(--border-subtle);
    }

    .intel-pattern-title {
        font-family: var(--font-mono);
        font-size: 0.7rem;
        color: var(--success);
        letter-spacing: 0.1em;
        margin-bottom: 0.8rem;
    }

    .intel-pattern-item {
        background: var(--bg-elevated);
        padding: 0.6rem 0.8rem;
        margin-bottom: 0.5rem;
        border-left: 2px solid var(--success);
        font-family: var(--font-mono);
        font-size: 0.75rem;
        color: var(--text-secondary);
    }

    .intel-pattern-score {
        float: right;
        color: var(--success);
    }

    .intel-keywords {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        padding: 0 1rem 1rem 1rem;
    }

    .intel-keyword {
        background: rgba(0, 255, 136, 0.1);
        border: 1px solid rgba(0, 255, 136, 0.3);
        padding: 0.3rem 0.6rem;
        font-family: var(--font-mono);
        font-size: 0.65rem;
        color: var(--success);
    }

    /* ═══════════════════════════════════════════════════════════════════════
       SIDEBAR
       ═══════════════════════════════════════════════════════════════════════ */
    [data-testid="stSidebar"] {
        background: var(--bg-panel) !important;
        border-right: 1px solid var(--border-subtle);
    }

    [data-testid="stSidebar"]::before {
        content: "◎ SYSTEM CONFIG";
        display: block;
        font-family: var(--font-display);
        font-size: 0.7rem;
        color: var(--phosphor-amber);
        letter-spacing: 0.2em;
        padding: 1rem 1rem 0.5rem 1rem;
        border-bottom: 1px solid var(--border-subtle);
        margin-bottom: 1rem;
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: var(--text-primary);
    }

    /* Sidebar headings */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        font-family: var(--font-display) !important;
        color: var(--phosphor-amber) !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.15em;
        border-bottom: 1px solid var(--border-subtle);
        padding-bottom: 0.5rem;
        margin-top: 1.5rem;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       INPUT ELEMENTS
       ═══════════════════════════════════════════════════════════════════════ */
    .stTextInput > div > div > input {
        background: var(--bg-void) !important;
        border: 1px solid var(--border-active) !important;
        color: var(--phosphor-amber) !important;
        font-family: var(--font-mono) !important;
        font-size: 1rem;
        padding: 0.8rem 1rem;
        caret-color: var(--phosphor-amber);
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--phosphor-amber) !important;
        box-shadow: 0 0 15px var(--phosphor-amber-glow), inset 0 0 5px var(--phosphor-amber-subtle) !important;
    }

    .stTextInput > div > div > input::placeholder {
        color: var(--text-dim) !important;
    }

    /* Sliders */
    .stSlider > div > div > div > div {
        background: var(--phosphor-amber) !important;
    }

    .stSlider [data-baseweb="slider"] {
        background: var(--border-active) !important;
    }

    /* Slider labels - make them brighter */
    .stSlider label,
    .stSlider [data-testid="stWidgetLabel"] {
        color: var(--text-primary) !important;
        font-family: var(--font-mono) !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.1em !important;
    }

    /* Checkbox labels - make them brighter */
    .stCheckbox label,
    .stCheckbox [data-testid="stWidgetLabel"] {
        color: var(--text-primary) !important;
    }

    /* Spinner text - make it brighter */
    .stSpinner > div > div {
        color: var(--phosphor-amber) !important;
    }

    /* Status/progress text */
    .stStatusWidget,
    [data-testid="stStatusWidget"] {
        color: var(--text-primary) !important;
    }

    /* Make all widget labels brighter */
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] span {
        color: var(--text-primary) !important;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       BUTTONS
       ═══════════════════════════════════════════════════════════════════════ */
    .stButton > button {
        font-family: var(--font-display) !important;
        font-weight: 600;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        background: transparent !important;
        border: 2px solid var(--phosphor-amber) !important;
        color: var(--phosphor-amber) !important;
        padding: 0.8rem 2rem;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background: var(--phosphor-amber) !important;
        color: var(--bg-void) !important;
        box-shadow: 0 0 30px var(--phosphor-amber-glow);
    }

    /* Primary button (Generate) */
    .stButton > button[kind="primary"] {
        background: var(--phosphor-amber) !important;
        color: var(--bg-void) !important;
        box-shadow: 0 0 20px var(--phosphor-amber-glow);
    }

    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 0 40px var(--phosphor-amber-glow), 0 0 60px rgba(255, 176, 0, 0.3);
    }

    /* Quick prompt buttons */
    [data-testid="stSidebar"] .stButton > button {
        font-family: var(--font-mono) !important;
        font-size: 0.75rem;
        padding: 0.5rem 0.8rem;
        border-width: 1px !important;
        letter-spacing: 0.05em;
        text-transform: none;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       MISSION PANEL (Main input area)
       ═══════════════════════════════════════════════════════════════════════ */
    .mission-input-panel {
        background: var(--bg-panel);
        border: 1px solid var(--border-subtle);
        padding: 2rem;
        margin: 1rem 0 2rem 0;
        position: relative;
    }

    .mission-input-panel::before {
        content: "◎ MISSION INPUT";
        position: absolute;
        top: -0.6rem;
        left: 1rem;
        background: var(--bg-panel);
        padding: 0 0.5rem;
        font-family: var(--font-display);
        font-size: 0.65rem;
        color: var(--cyan-electric);
        letter-spacing: 0.2em;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       ITERATION TIMELINE
       ═══════════════════════════════════════════════════════════════════════ */
    .timeline-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin: 2rem 0 1rem 0;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border-subtle);
    }

    .timeline-title {
        font-family: var(--font-display);
        font-size: 0.8rem;
        color: var(--phosphor-amber);
        letter-spacing: 0.2em;
        text-shadow: 0 0 10px var(--phosphor-amber-glow);
    }

    .timeline-status {
        font-family: var(--font-mono);
        font-size: 0.7rem;
        color: var(--success);
        letter-spacing: 0.1em;
        animation: blink 1s steps(1) infinite;
    }

    @keyframes blink {
        50% { opacity: 0; }
    }

    /* Iteration Card */
    .iteration-card {
        background: var(--bg-panel);
        border: 1px solid var(--border-subtle);
        padding: 0;
        margin-bottom: 1rem;
        position: relative;
        overflow: hidden;
    }

    .iteration-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: var(--phosphor-amber);
        box-shadow: 0 0 15px var(--phosphor-amber-glow);
    }

    .iteration-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 1.5rem;
        background: var(--bg-elevated);
        border-bottom: 1px solid var(--border-subtle);
    }

    .iteration-number {
        font-family: var(--font-display);
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--phosphor-amber);
        text-shadow: 0 0 10px var(--phosphor-amber-glow);
    }

    .iteration-phase {
        font-family: var(--font-mono);
        font-size: 0.65rem;
        color: var(--text-secondary);
        letter-spacing: 0.15em;
        text-transform: uppercase;
    }

    .iteration-time {
        font-family: var(--font-mono);
        font-size: 0.75rem;
        color: var(--cyan-electric);
        text-shadow: 0 0 5px var(--cyan-glow);
    }

    .iteration-body {
        padding: 1.5rem;
    }

    .prompt-display {
        background: var(--bg-void);
        border: 1px solid var(--border-active);
        padding: 1rem;
        margin: 1rem 0;
        font-family: var(--font-mono);
        font-size: 0.85rem;
        color: var(--phosphor-amber);
        line-height: 1.6;
        position: relative;
    }

    .prompt-display::before {
        content: "PROMPT >";
        font-size: 0.6rem;
        color: var(--text-dim);
        letter-spacing: 0.1em;
        display: block;
        margin-bottom: 0.5rem;
    }

    .critique-box {
        background: var(--cyan-subtle);
        border-left: 2px solid var(--cyan-electric);
        padding: 0.8rem 1rem;
        margin: 1rem 0;
        font-family: var(--font-mono);
        font-size: 0.8rem;
        color: var(--text-secondary);
        line-height: 1.5;
    }

    .critique-box::before {
        content: "◎ AI CRITIQUE";
        font-size: 0.6rem;
        color: var(--cyan-electric);
        letter-spacing: 0.15em;
        display: block;
        margin-bottom: 0.5rem;
    }

    .improvement-note {
        font-family: var(--font-mono);
        font-size: 0.75rem;
        color: var(--success);
        padding: 0.5rem 0;
    }

    .improvement-note::before {
        content: "+ ";
    }

    /* ═══════════════════════════════════════════════════════════════════════
       SCORE DISPLAY
       ═══════════════════════════════════════════════════════════════════════ */
    .score-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.3rem 0.6rem;
        font-family: var(--font-mono);
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 2px;
    }

    .score-badge.high {
        background: rgba(0, 255, 136, 0.2);
        border: 1px solid var(--success);
        color: var(--success);
    }

    .score-badge.medium {
        background: rgba(255, 170, 0, 0.2);
        border: 1px solid var(--warning);
        color: var(--warning);
    }

    .score-badge.low {
        background: rgba(255, 68, 68, 0.2);
        border: 1px solid var(--danger);
        color: var(--danger);
    }

    .learning-indicator {
        font-family: var(--font-mono);
        font-size: 0.7rem;
        color: var(--success);
        margin: 0.5rem 0;
    }

    .examples-indicator {
        font-family: var(--font-mono);
        font-size: 0.7rem;
        color: var(--cyan-electric);
        margin: 0.5rem 0;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       RATING WIDGET
       ═══════════════════════════════════════════════════════════════════════ */
    .rating-container {
        background: var(--bg-elevated);
        border: 1px solid var(--border-subtle);
        padding: 1rem;
        margin-top: 1rem;
    }

    .rating-label {
        font-family: var(--font-mono);
        font-size: 0.7rem;
        color: var(--text-secondary);
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
    }

    .rating-stars {
        display: flex;
        gap: 0.5rem;
    }

    .rating-star {
        font-size: 1.5rem;
        cursor: pointer;
        transition: all 0.2s ease;
        color: var(--text-dim);
    }

    .rating-star.active {
        color: var(--phosphor-amber);
        text-shadow: 0 0 10px var(--phosphor-amber-glow);
    }

    .rating-star:hover {
        transform: scale(1.2);
    }

    .rating-success {
        font-family: var(--font-mono);
        font-size: 0.75rem;
        color: var(--success);
        margin-top: 0.5rem;
        padding: 0.5rem;
        background: rgba(0, 255, 136, 0.1);
        border: 1px solid var(--success);
    }

    /* ═══════════════════════════════════════════════════════════════════════
       AUDIO PLAYER
       ═══════════════════════════════════════════════════════════════════════ */
    .audio-container {
        background: var(--bg-void);
        border: 1px solid var(--border-active);
        padding: 1rem;
        margin: 1rem 0 2rem 0;
    }

    .audio-container::before {
        content: "◎ AUDIO SIGNAL";
        font-family: var(--font-mono);
        font-size: 0.6rem;
        color: var(--success);
        letter-spacing: 0.2em;
        display: block;
        margin-bottom: 0.5rem;
    }

    audio {
        width: 100%;
        height: 40px;
        filter: sepia(20%) saturate(70%) hue-rotate(340deg);
    }

    audio::-webkit-media-controls-panel {
        background: var(--bg-elevated);
    }

    /* ═══════════════════════════════════════════════════════════════════════
       STATS PANEL
       ═══════════════════════════════════════════════════════════════════════ */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin: 2rem 0;
    }

    .stat-box {
        background: var(--bg-panel);
        border: 1px solid var(--border-subtle);
        padding: 1.5rem;
        text-align: center;
        position: relative;
    }

    .stat-box::before {
        content: "";
        position: absolute;
        top: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 30%;
        height: 2px;
        background: var(--phosphor-amber);
        box-shadow: 0 0 10px var(--phosphor-amber-glow);
    }

    .stat-value {
        font-family: var(--font-display);
        font-size: 2rem;
        font-weight: 700;
        color: var(--phosphor-amber);
        text-shadow: 0 0 20px var(--phosphor-amber-glow);
    }

    .stat-label {
        font-family: var(--font-mono);
        font-size: 0.65rem;
        color: var(--text-secondary);
        letter-spacing: 0.15em;
        text-transform: uppercase;
        margin-top: 0.5rem;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       BEFORE/AFTER COMPARISON
       ═══════════════════════════════════════════════════════════════════════ */
    .comparison-panel {
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        gap: 2rem;
        align-items: stretch;
        margin: 2rem 0;
    }

    .comparison-box {
        background: var(--bg-panel);
        border: 1px solid var(--border-subtle);
        padding: 1.5rem;
    }

    .comparison-box.before {
        border-left: 3px solid var(--text-dim);
    }

    .comparison-box.after {
        border-left: 3px solid var(--success);
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.1);
    }

    .comparison-label {
        font-family: var(--font-display);
        font-size: 0.7rem;
        color: var(--text-secondary);
        letter-spacing: 0.2em;
        margin-bottom: 1rem;
    }

    .comparison-box.after .comparison-label {
        color: var(--success);
    }

    .comparison-text {
        font-family: var(--font-mono);
        font-size: 0.9rem;
        color: var(--text-primary);
        line-height: 1.6;
    }

    .comparison-arrow {
        display: flex;
        align-items: center;
        font-family: var(--font-display);
        font-size: 1.5rem;
        color: var(--phosphor-amber);
        text-shadow: 0 0 20px var(--phosphor-amber-glow);
    }

    /* ═══════════════════════════════════════════════════════════════════════
       WEAVE LINK
       ═══════════════════════════════════════════════════════════════════════ */
    .weave-link {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        font-family: var(--font-mono);
        font-size: 0.8rem;
        color: var(--cyan-electric);
        text-decoration: none;
        padding: 0.8rem 1.2rem;
        border: 1px solid var(--cyan-electric);
        transition: all 0.2s ease;
    }

    .weave-link:hover {
        background: var(--cyan-electric);
        color: var(--bg-void);
        box-shadow: 0 0 20px var(--cyan-glow);
    }

    /* ═══════════════════════════════════════════════════════════════════════
       STATUS INDICATORS
       ═══════════════════════════════════════════════════════════════════════ */
    .status-online {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        font-family: var(--font-mono);
        font-size: 0.7rem;
        color: var(--success);
    }

    .status-online::before {
        content: "";
        width: 8px;
        height: 8px;
        background: var(--success);
        border-radius: 50%;
        box-shadow: 0 0 10px var(--success);
        animation: pulse-glow 2s infinite;
    }

    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 5px var(--success); }
        50% { box-shadow: 0 0 15px var(--success), 0 0 25px rgba(0, 255, 136, 0.5); }
    }

    .status-offline {
        color: var(--danger);
    }

    .status-offline::before {
        background: var(--danger);
        box-shadow: 0 0 10px var(--danger);
        animation: none;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       ALERTS & MESSAGES
       ═══════════════════════════════════════════════════════════════════════ */
    .stSuccess {
        background: rgba(0, 255, 136, 0.1) !important;
        border: 1px solid var(--success) !important;
        color: var(--success) !important;
    }

    .stError {
        background: rgba(255, 68, 68, 0.1) !important;
        border: 1px solid var(--danger) !important;
        color: var(--danger) !important;
    }

    .stSpinner > div {
        border-top-color: var(--phosphor-amber) !important;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       EXPANDERS
       ═══════════════════════════════════════════════════════════════════════ */
    .streamlit-expanderHeader {
        font-family: var(--font-mono) !important;
        font-size: 0.75rem !important;
        color: var(--text-secondary) !important;
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border-subtle) !important;
        margin-top: 1rem !important;
    }

    .streamlit-expanderContent {
        background: var(--bg-panel) !important;
        border: 1px solid var(--border-subtle) !important;
        border-top: none !important;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       FOOTER
       ═══════════════════════════════════════════════════════════════════════ */
    .mission-footer {
        text-align: center;
        padding: 2rem 0;
        margin-top: 3rem;
        border-top: 1px solid var(--border-subtle);
        font-family: var(--font-mono);
        font-size: 0.7rem;
        color: var(--text-dim);
        letter-spacing: 0.1em;
    }

    .mission-footer strong {
        color: var(--phosphor-amber);
    }

    /* ═══════════════════════════════════════════════════════════════════════
       TABS STYLING
       ═══════════════════════════════════════════════════════════════════════ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: var(--bg-panel);
        border-bottom: 1px solid var(--border-subtle);
        padding: 0 1rem;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: var(--font-display) !important;
        font-size: 0.75rem;
        letter-spacing: 0.1em;
        color: var(--text-secondary);
        background: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        padding: 1rem 1.5rem;
        margin: 0;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: var(--phosphor-amber);
        background: var(--bg-elevated);
    }

    .stTabs [aria-selected="true"] {
        color: var(--phosphor-amber) !important;
        border-bottom: 2px solid var(--phosphor-amber) !important;
        background: var(--bg-elevated) !important;
    }

    .stTabs [data-baseweb="tab-highlight"] {
        background: var(--phosphor-amber) !important;
    }

    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1.5rem;
    }

    /* History page cards */
    .history-card {
        background: var(--bg-panel);
        border: 1px solid var(--border-subtle);
        border-left: 3px solid var(--success);
        padding: 1.2rem 1.5rem;
        margin-bottom: 0.8rem;
    }

    .history-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.8rem;
    }

    .history-score {
        font-family: var(--font-display);
        font-size: 1.1rem;
        color: var(--success);
    }

    .history-date {
        font-size: 0.7rem;
        color: var(--text-dim);
    }

    .history-prompts {
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        gap: 0.8rem;
        align-items: center;
    }

    .history-prompt-box {
        background: var(--bg-void);
        border: 1px solid var(--border-subtle);
        padding: 0.8rem;
        font-size: 0.8rem;
        color: var(--text-secondary);
    }

    .history-prompt-box.refined {
        color: var(--phosphor-amber);
        border-color: var(--phosphor-amber);
    }

    .history-arrow {
        color: var(--phosphor-amber);
        font-size: 1.2rem;
    }

    .rating-card {
        background: var(--bg-panel);
        border: 1px solid var(--border-subtle);
        padding: 1rem 1.5rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 1.5rem;
    }

    .rating-stars-display {
        font-size: 1.3rem;
        color: var(--phosphor-amber);
    }

    .rating-prompt-text {
        flex: 1;
        font-size: 0.85rem;
        color: var(--text-primary);
    }

    .rating-meta-text {
        font-size: 0.7rem;
        color: var(--text-dim);
        text-align: right;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       RESPONSIVE
       ═══════════════════════════════════════════════════════════════════════ */
    @media (max-width: 768px) {
        .logo-text {
            font-size: 2.5rem;
        }

        .stats-grid {
            grid-template-columns: repeat(2, 1fr);
        }

        .comparison-panel {
            grid-template-columns: 1fr;
        }

        .comparison-arrow {
            transform: rotate(90deg);
            justify-content: center;
            padding: 1rem 0;
        }

        .intel-grid {
            grid-template-columns: repeat(2, 1fr);
        }

        .history-prompts {
            grid-template-columns: 1fr;
        }

        .history-arrow {
            transform: rotate(90deg);
            text-align: center;
        }
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════════

if "iterations" not in st.session_state:
    st.session_state.iterations = []
if "running" not in st.session_state:
    st.session_state.running = False
if "results" not in st.session_state:
    st.session_state.results = None
if "engine" not in st.session_state:
    st.session_state.engine = None
if "ratings" not in st.session_state:
    st.session_state.ratings = {}

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="mission-header">
    <div class="logo-text">LOOPISM</div>
    <div class="tagline">SELF-IMPROVING AUDIO GENERATION SYSTEM</div>
    <div class="tech-stack">
        <span class="tech-badge active">W&B WEAVE</span>
        <span class="tech-badge active">REPLICATE</span>
        <span class="tech-badge active">SELF-REFINE</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Learning Status Badge
try:
    badge_stats = get_local_stats()
    if badge_stats['total_patterns'] > 0:
        st.markdown(f"""
        <div style="text-align: center;">
            <span class="learning-badge">
                LEARNING ACTIVE • {badge_stats['total_patterns']} PATTERNS LEARNED
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center;">
            <span class="learning-badge" style="border-color: var(--warning); color: var(--warning); background: rgba(255, 170, 0, 0.1);">
                🧠 LEARNING READY • AWAITING FIRST SESSION
            </span>
        </div>
        """, unsafe_allow_html=True)
except Exception:
    pass

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TABS
# ═══════════════════════════════════════════════════════════════════════════════

tab_generate, tab_learning, tab_ratings, tab_sessions = st.tabs([
    "◎ GENERATE",
    "◎ LEARNING HISTORY",
    "◎ RATINGS",
    "◎ SESSIONS"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: GENERATE
# ═══════════════════════════════════════════════════════════════════════════════

with tab_generate:
    # ═══════════════════════════════════════════════════════════════════════════════
    # INTELLIGENCE DASHBOARD
    # ═══════════════════════════════════════════════════════════════════════════════

    with st.expander("🧠 INTELLIGENCE DASHBOARD", expanded=False):
        try:
            # Use local storage stats
            intel_stats = get_local_stats()

            if intel_stats['total_patterns'] > 0:
                # Metrics Grid
                st.markdown("""
                <div class="intel-dashboard">
                    <div class="intel-grid">
                """, unsafe_allow_html=True)

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.markdown(f"""
                    <div class="intel-card">
                        <div class="intel-value">{intel_stats['total_patterns']}</div>
                        <div class="intel-label">Patterns Learned</div>
                        <div class="intel-delta positive">ready to use</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div class="intel-card">
                        <div class="intel-value">{intel_stats['avg_score']}</div>
                        <div class="intel-label">Avg Score</div>
                        <div class="intel-delta">out of 100</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    rating_display = f"{intel_stats['avg_rating']}" if intel_stats['avg_rating'] > 0 else "—"
                    st.markdown(f"""
                    <div class="intel-card">
                        <div class="intel-value">{rating_display}</div>
                        <div class="intel-label">User Rating</div>
                        <div class="intel-delta">out of 5</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col4:
                    st.markdown(f"""
                    <div class="intel-card">
                        <div class="intel-value">{intel_stats['times_reused']}</div>
                        <div class="intel-label">Times Reused</div>
                        <div class="intel-delta">as examples</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

                # Top Patterns
                if intel_stats['top_patterns']:
                    st.markdown("""
                    <div class="intel-patterns">
                        <div class="intel-pattern-title">◎ TOP LEARNED PATTERNS</div>
                    """, unsafe_allow_html=True)

                    for pattern in intel_stats['top_patterns'][:3]:
                        initial = pattern.get('initial_prompt', '')[:30] + "..." if len(pattern.get('initial_prompt', '')) > 30 else pattern.get('initial_prompt', '')
                        refined = pattern.get('refined_prompt', '')[:50] + "..." if len(pattern.get('refined_prompt', '')) > 50 else pattern.get('refined_prompt', '')
                        score = pattern.get('auto_score', 0)
                        st.markdown(f"""
                        <div class="intel-pattern-item">
                            "{initial}" → "{refined}"
                            <span class="intel-pattern-score">{score:.0f}/100</span>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

                # Top Keywords
                if intel_stats['top_keywords']:
                    st.markdown('<div class="intel-patterns"><div class="intel-pattern-title">◎ TOP KEYWORDS</div></div>', unsafe_allow_html=True)
                    st.markdown('<div class="intel-keywords">', unsafe_allow_html=True)
                    for kw in intel_stats['top_keywords'][:8]:
                        st.markdown(f'<span class="intel-keyword">{kw["word"]} ({kw["count"]})</span>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

            else:
                st.markdown("""
                <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                    <p style="font-size: 1.5rem; margin-bottom: 0.5rem;">🧠</p>
                    <p>No patterns learned yet.</p>
                    <p style="font-size: 0.8rem; color: var(--text-dim);">
                        Generate audio and rate iterations to teach the system.
                    </p>
                </div>
                """, unsafe_allow_html=True)

        except Exception as e:
            st.markdown(f"""
            <div style="text-align: center; padding: 2rem; color: var(--text-dim);">
                Learning system initializing...
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    # ═══════════════════════════════════════════════════════════════
    # API STATUS
    # ═══════════════════════════════════════════════════════════════
    st.markdown("### CONNECTIONS")

    replicate_key = os.environ.get("REPLICATE_API_TOKEN", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    wandb_key = os.environ.get("WANDB_API_KEY", "")
    weave_project = os.environ.get("WEAVE_PROJECT", "loopism-audio-refinement")

    # Show status indicators
    col1, col2, col3 = st.columns(3)
    with col1:
        if replicate_key:
            st.markdown('<span class="status-online">REPLICATE</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-online status-offline">REPLICATE</span>', unsafe_allow_html=True)
    with col2:
        if openai_key:
            st.markdown('<span class="status-online">OPENAI</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-online status-offline">OPENAI</span>', unsafe_allow_html=True)
    with col3:
        if wandb_key:
            st.markdown('<span class="status-online">WEAVE</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-online status-offline">WEAVE</span>', unsafe_allow_html=True)

    # API Key inputs if not set
    if not replicate_key:
        replicate_key = st.text_input("REPLICATE TOKEN", type="password", key="rep_key")
        if replicate_key:
            os.environ["REPLICATE_API_TOKEN"] = replicate_key
            st.rerun()

    if not openai_key:
        openai_key = st.text_input("OPENAI KEY", type="password", key="oai_key")
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key
            st.rerun()

    st.markdown("---")

    # ═══════════════════════════════════════════════════════════════
    # LEARNING STATS (Local Storage)
    # ═══════════════════════════════════════════════════════════════
    st.markdown("### LEARNING STATS")

    # Get stats from local storage
    local_stats = get_local_stats()

    st.markdown(f"""
    <div style="background: var(--bg-elevated); padding: 0.8rem; margin-bottom: 0.5rem; border-left: 2px solid var(--success);">
        <div style="font-size: 0.65rem; color: var(--text-dim); letter-spacing: 0.1em;">PATTERNS LEARNED</div>
        <div style="font-size: 1.2rem; color: var(--success); font-family: var(--font-display);">{local_stats['total_patterns']}</div>
    </div>
    <div style="background: var(--bg-elevated); padding: 0.8rem; margin-bottom: 0.5rem; border-left: 2px solid var(--cyan-electric);">
        <div style="font-size: 0.65rem; color: var(--text-dim); letter-spacing: 0.1em;">TIMES REUSED</div>
        <div style="font-size: 1.2rem; color: var(--cyan-electric); font-family: var(--font-display);">{local_stats['times_reused']}</div>
    </div>
    <div style="background: var(--bg-elevated); padding: 0.8rem; margin-bottom: 0.5rem; border-left: 2px solid var(--phosphor-amber);">
        <div style="font-size: 0.65rem; color: var(--text-dim); letter-spacing: 0.1em;">AVG SCORE</div>
        <div style="font-size: 1.2rem; color: var(--phosphor-amber); font-family: var(--font-display);">{local_stats['avg_score']}</div>
    </div>
    <div style="background: var(--bg-elevated); padding: 0.8rem; margin-bottom: 0.5rem; border-left: 2px solid var(--warning);">
        <div style="font-size: 0.65rem; color: var(--text-dim); letter-spacing: 0.1em;">USER RATINGS</div>
        <div style="font-size: 1.2rem; color: var(--warning); font-family: var(--font-display);">{local_stats['total_ratings']} ({local_stats['avg_rating']} avg)</div>
    </div>
    """, unsafe_allow_html=True)

    # Top Keywords
    if local_stats['top_keywords']:
        st.markdown("""
        <div style="font-size: 0.65rem; color: var(--text-dim); letter-spacing: 0.1em; margin: 0.8rem 0 0.3rem 0;">TOP KEYWORDS</div>
        """, unsafe_allow_html=True)
        keywords_html = " ".join([
            f'<span style="background: rgba(0, 255, 136, 0.1); border: 1px solid rgba(0, 255, 136, 0.3); padding: 0.2rem 0.4rem; font-size: 0.65rem; color: var(--success); margin-right: 0.3rem; margin-bottom: 0.3rem; display: inline-block;">{kw["word"]}</span>'
            for kw in local_stats['top_keywords'][:5]
        ])
        st.markdown(f'<div style="margin-bottom: 0.5rem;">{keywords_html}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ═══════════════════════════════════════════════════════════════
    # HOW IT WORKS
    # ═══════════════════════════════════════════════════════════════
    st.markdown("### HOW IT WORKS")
    st.markdown("""
    <div style="font-size: 0.7rem; color: var(--text-dim); line-height: 1.6;">
        <strong style="color: var(--phosphor-amber);">Self-Refine:</strong> Each iteration critiques and improves the prompt, scored by AI judge.<br><br>
        <strong style="color: var(--success);">Auto-Learning:</strong> High-scoring refinements (≥75) are automatically saved for future use.<br><br>
        <strong style="color: var(--cyan-electric);">Your Ratings:</strong> Rate clips to teach the system — 4+ star ratings boost patterns.<br><br>
        <strong style="color: var(--warning);">Few-Shot:</strong> Past successes are used as examples for new generations.
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT (inside tab_generate)
# ═══════════════════════════════════════════════════════════════════════════════

with tab_generate:
    # Mission Input Panel
    st.markdown('<div class="mission-input-panel">', unsafe_allow_html=True)

    col1, col2 = st.columns([5, 1])

    with col1:
        default_prompt = st.session_state.get("selected_prompt", "")
        user_prompt = st.text_input(
            "DESCRIBE TARGET AUDIO",
            value=default_prompt,
            placeholder="e.g., peaceful piano melody, driving electronic beat...",
            label_visibility="collapsed"
        )

    with col2:
        can_run = bool(replicate_key and openai_key and user_prompt and not st.session_state.running)
        generate_btn = st.button(
            "◎ LAUNCH",
            type="primary",
            use_container_width=True,
            disabled=not can_run
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # Quick Launch Buttons (below search bar)
    st.markdown("""
    <div style="font-family: var(--font-mono); font-size: 0.7rem; color: var(--text-dim); letter-spacing: 0.1em; margin: 0.5rem 0;">
        QUICK START
    </div>
    """, unsafe_allow_html=True)

    quick_cols = st.columns(5)
    quick_prompts = [
        ("SUMMER VIBES", "happy summer vibes"),
        ("CINEMATIC", "epic cinematic trailer"),
        ("LOFI BEATS", "chill lofi study beats"),
        ("WORKOUT", "energetic workout music"),
        ("AMBIENT", "ambient night atmosphere"),
    ]

    for i, (label, prompt) in enumerate(quick_prompts):
        with quick_cols[i]:
            if st.button(label, key=f"main_quick_{prompt}", use_container_width=True):
                st.session_state.selected_prompt = prompt
                st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════════
    # GENERATION CONFIG (in main area)
    # ═══════════════════════════════════════════════════════════════════════════════

    st.markdown("""
    <div style="margin-top: 1.5rem; padding: 1rem; background: var(--bg-panel); border: 1px solid var(--border-subtle); position: relative;">
        <div style="position: absolute; top: -0.6rem; left: 1rem; background: var(--bg-panel); padding: 0 0.5rem; font-family: var(--font-display); font-size: 0.65rem; color: var(--cyan-electric); letter-spacing: 0.2em;">
            ◎ GENERATION CONFIG
        </div>
    </div>
    """, unsafe_allow_html=True)

    config_col1, config_col2, config_col3 = st.columns([2, 2, 1])

    with config_col1:
        max_iterations = st.slider(
            "ITERATIONS",
            min_value=2,
            max_value=5,
            value=3,
            help="Number of refinement cycles"
        )

    with config_col2:
        audio_duration = st.slider(
            "AUDIO DURATION (SEC)",
            min_value=3,
            max_value=10,
            value=5,
            help="Length of generated audio"
        )

    with config_col3:
        enable_learning = st.checkbox("🧠 LEARNING", value=True, help="Use and contribute to learned patterns")

    # ═══════════════════════════════════════════════════════════════════════════════
    # GENERATION LOGIC
    # ═══════════════════════════════════════════════════════════════════════════════

    if generate_btn and can_run:
        st.session_state.running = True
        st.session_state.iterations = []
        st.session_state.results = None
        st.session_state.ratings = {}

        # Check if this is a cached quick prompt
        prompt_is_cached = is_prompt_cached(user_prompt)

        # Clear selected prompt
        if "selected_prompt" in st.session_state:
            del st.session_state.selected_prompt

        try:
            if prompt_is_cached:
                # ═══════════════════════════════════════════════════════════════
                # CACHED QUICK PROMPT - Load with simulated delays
                # Appears identical to live generation
                # ═══════════════════════════════════════════════════════════════

                # Stream iterations with delays (looks like real generation)
                with st.spinner("◎ MISSION IN PROGRESS — GENERATING, SCORING, AND LEARNING..."):
                    iterations_loaded = []
                    for iteration in stream_cached_iterations(user_prompt, simulate_delay=True):
                        iterations_loaded.append(iteration)
                        st.session_state.iterations = iterations_loaded.copy()

                # Load comparison data
                st.session_state.results = load_cached_comparison_data(user_prompt)

                st.success("◎ MISSION COMPLETE — AUDIO GENERATION SUCCESSFUL")

                # Create a mock engine for ratings (won't actually generate)
                st.session_state.engine = None

            else:
                # ═══════════════════════════════════════════════════════════════
                # CUSTOM PROMPT - Generate live
                # ═══════════════════════════════════════════════════════════════
                def on_iteration(iteration: LoopIteration):
                    st.session_state.iterations.append(iteration)

                engine = LoopismEngine(
                    max_iterations=max_iterations,
                    audio_duration=audio_duration,
                    output_dir="loopism_outputs",
                    on_iteration_complete=on_iteration,
                    enable_learning=enable_learning
                )
                st.session_state.engine = engine

                with st.spinner("◎ MISSION IN PROGRESS — GENERATING, SCORING, AND LEARNING..."):
                    results = engine.run(user_prompt)

                st.session_state.results = engine.get_comparison_data()
                st.success("◎ MISSION COMPLETE — AUDIO GENERATION SUCCESSFUL")

        except Exception as e:
            st.error(f"◎ MISSION FAILED — {str(e)}")

        st.session_state.running = False
        st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════════
    # RESULTS DISPLAY
    # ═══════════════════════════════════════════════════════════════════════════════

    if st.session_state.iterations:
        # Timeline Header
        examples_used = st.session_state.iterations[0].examples_used if st.session_state.iterations else 0

        st.markdown(f"""
        <div class="timeline-header">
            <span class="timeline-title">◎ ITERATION TIMELINE</span>
            <span class="timeline-status">● COMPLETE</span>
        </div>
        """, unsafe_allow_html=True)

        # Show examples used indicator
        if examples_used > 0:
            st.markdown(f"""
            <div class="examples-indicator" style="margin-bottom: 1rem;">
                📚 Used {examples_used} learned patterns as examples
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="examples-indicator" style="margin-bottom: 1rem; color: var(--text-dim);">
                📚 No past examples used (fresh start)
            </div>
            """, unsafe_allow_html=True)

        # Iteration Cards
        cols = st.columns(len(st.session_state.iterations))

        for col, iteration in zip(cols, st.session_state.iterations):
            with col:
                phase_name = ["INITIAL", "REFINED", "OPTIMIZED", "ENHANCED", "FINAL"][min(iteration.iteration_num, 4)]
                total_time = iteration.generation_time + iteration.refinement_time

                # Determine score color
                score = iteration.auto_score
                if score >= 80:
                    score_class = "high"
                elif score >= 60:
                    score_class = "medium"
                else:
                    score_class = "low"

                # Get trace information
                music_ctx = iteration.music_context or {}
                genre = music_ctx.get('genre', '')
                mood = music_ctx.get('mood', '')
                bpm = music_ctx.get('bpm')
                trace_id = iteration.trace_id
                
                # Build context tags
                context_tags_html = ""
                if genre:
                    context_tags_html += f'<span style="background: rgba(255,176,0,0.1); border: 1px solid rgba(255,176,0,0.3); padding: 0.15rem 0.4rem; font-size: 0.6rem; color: var(--phosphor-amber); margin-right: 0.3rem; border-radius: 3px;">{genre}</span>'
                if mood:
                    context_tags_html += f'<span style="background: rgba(0,180,255,0.1); border: 1px solid rgba(0,180,255,0.3); padding: 0.15rem 0.4rem; font-size: 0.6rem; color: var(--cyan-electric); margin-right: 0.3rem; border-radius: 3px;">{mood}</span>'
                if bpm:
                    context_tags_html += f'<span style="background: rgba(255,0,255,0.1); border: 1px solid rgba(255,0,255,0.3); padding: 0.15rem 0.4rem; font-size: 0.6rem; color: var(--accent-magenta); border-radius: 3px;">{bpm} BPM</span>'

                st.markdown(f"""
                <div class="iteration-card">
                    <div class="iteration-header">
                        <div>
                            <span class="iteration-number">0{iteration.iteration_num + 1}</span>
                            <span class="iteration-phase">{phase_name}</span>
                        </div>
                        <span class="iteration-time">{total_time:.1f}s</span>
                    </div>
                    <div class="iteration-body">
                        <div style="display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.5rem; flex-wrap: wrap;">
                            <span class="score-badge {score_class}">◎ {score:.0f}/100</span>
                            {f'<span class="learning-indicator">🧠 Added to learning</span>' if iteration.added_to_learning else ''}
                            {f'<span style="font-size: 0.65rem; color: var(--text-dim);">📝 Trace: {trace_id[:8] if trace_id else "N/A"}</span>' if trace_id else ''}
                        </div>
                        {f'<div style="margin-bottom: 0.5rem; display: flex; gap: 0.3rem; flex-wrap: wrap;">{context_tags_html}</div>' if context_tags_html else ''}
                        <div class="prompt-display">{iteration.refined_prompt}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Audio Player with Visualizer
                if iteration.audio_path:
                    # Convert to absolute path if needed
                    audio_path = str(iteration.audio_path)
                    if not os.path.isabs(audio_path):
                        # Try to make it absolute relative to the output directory
                        from pathlib import Path
                        base_path = Path(audio_path)
                        if not base_path.exists():
                            # Try relative to loopism_outputs
                            audio_path = str(Path("loopism_outputs") / base_path.name)
                        if not os.path.isabs(audio_path):
                            audio_path = str(Path(audio_path).resolve())
                    
                    if os.path.exists(audio_path):
                        # Always show a simple, reliable audio player first
                        st.markdown("**🎵 Audio:**")
                        try:
                            # Use absolute path for audio player
                            st.audio(audio_path, format='audio/wav')
                        except Exception as e:
                            st.error(f"Error loading audio: {str(e)}")
                            st.text(f"Path: {audio_path}")
                            st.text(f"Exists: {os.path.exists(audio_path)}")
                        
                        # Try to show the visualizer (optional enhancement)
                        try:
                            render_audio_visualizer(audio_path, iteration.iteration_num)
                        except Exception as e:
                            # Visualizer failed, but we already have the audio player above
                            pass
                    else:
                        st.warning(f"Audio file not found: {audio_path}")
                        # Show debug info
                        with st.expander("Debug Info"):
                            st.text(f"Original path: {iteration.audio_path}")
                            st.text(f"Resolved path: {audio_path}")
                            st.text(f"Current dir: {os.getcwd()}")
                else:
                    st.info("No audio path available for this iteration")
                    
                    # Implicit signal buttons (replay, save, export)
                    if trace_id and st.session_state.engine:
                        signal_cols = st.columns(3)
                        with signal_cols[0]:
                            if st.button("🔁 Replay", key=f"replay_{iteration.iteration_num}", help="Track that you're replaying this"):
                                st.session_state.engine.record_implicit_signal(trace_id, "replay", 1)
                                st.success("Signal recorded!")
                        with signal_cols[1]:
                            if st.button("💾 Save", key=f"save_{iteration.iteration_num}", help="Mark this as saved"):
                                st.session_state.engine.record_implicit_signal(trace_id, "save", 1)
                                st.success("Signal recorded!")
                        with signal_cols[2]:
                            if st.button("📤 Export", key=f"export_{iteration.iteration_num}", help="Track export action"):
                                st.session_state.engine.record_implicit_signal(trace_id, "export", 1)
                                st.success("Signal recorded!")

                # Expandable Details
                with st.expander("◎ VIEW CRITIQUE"):
                    st.markdown(f"""
                    <div class="critique-box">{iteration.critique}</div>
                    <div class="improvement-note">{iteration.improvement_notes}</div>
                    """, unsafe_allow_html=True)
                
                # Trace Details (if available)
                if trace_id and (iteration.agent_decisions or music_ctx):
                    with st.expander("🔍 TRACE DETAILS"):
                        if music_ctx:
                            st.markdown("**Musical Context:**")
                            ctx_info = []
                            if genre:
                                ctx_info.append(f"🎸 Genre: {genre}")
                            if mood:
                                ctx_info.append(f"😊 Mood: {mood}")
                            if bpm:
                                ctx_info.append(f"⏱️ BPM: {bpm}")
                            if music_ctx.get('instruments'):
                                ctx_info.append(f"🎹 Instruments: {', '.join(music_ctx.get('instruments', []))}")
                            if ctx_info:
                                st.markdown(" | ".join(ctx_info))
                        
                        if iteration.agent_decisions:
                            st.markdown("**Agent Decisions:**")
                            for decision in iteration.agent_decisions[:3]:  # Show top 3
                                if isinstance(decision, dict):
                                    agent_name = decision.get('agent_name', 'Unknown')
                                    decision_type = decision.get('decision_type', 'N/A')
                                    confidence = decision.get('confidence', 0)
                                    success = decision.get('success', True)
                                    success_icon = "✓" if success else "✗"
                                    success_color = "var(--success)" if success else "var(--danger)"
                                    st.markdown(f"""
                                    <div style="background: var(--bg-elevated); padding: 0.5rem; margin: 0.3rem 0; border-left: 2px solid {success_color};">
                                        <strong>{agent_name}</strong>: {decision_type}<br>
                                        <span style="font-size: 0.75rem; color: var(--text-dim);">
                                            {success_icon} Confidence: {int(confidence * 100)}%
                                        </span>
                                    </div>
                                    """, unsafe_allow_html=True)
                        
                        st.markdown(f"<small style='color: var(--text-dim);'>Trace ID: {trace_id}</small>", unsafe_allow_html=True)

                # Rating Widget
                st.markdown('<div class="rating-container">', unsafe_allow_html=True)
                st.markdown('<div class="rating-label">RATE THIS REFINEMENT</div>', unsafe_allow_html=True)

                rating_key = f"rating_{iteration.iteration_num}"

                # Check if already rated
                if rating_key in st.session_state.ratings:
                    rating = st.session_state.ratings[rating_key]
                    stars = "★" * rating + "☆" * (5 - rating)
                    st.markdown(f"""
                    <div class="rating-success">
                        {stars} — Rating submitted! {"🧠 Teaching the system!" if rating >= 4 else ""}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Rating input
                    rating = st.slider(
                        "Stars",
                        min_value=1,
                        max_value=5,
                        value=3,
                        key=f"slider_{iteration.iteration_num}",
                        label_visibility="collapsed"
                    )

                    # Star display
                    stars_html = ""
                    for i in range(1, 6):
                        active = "active" if i <= rating else ""
                        stars_html += f'<span class="rating-star {active}">{"★" if i <= rating else "☆"}</span>'

                    st.markdown(f'<div class="rating-stars">{stars_html}</div>', unsafe_allow_html=True)

                    if st.button(f"Submit Rating", key=f"submit_{iteration.iteration_num}"):
                        success = False
                        if st.session_state.engine:
                            # Live generation - use engine
                            success = st.session_state.engine.record_user_rating(iteration.iteration_num, rating)
                        elif iteration.record_id:
                            # Cached prompt - use learning system directly
                            success = record_feedback(iteration.record_id, rating)
                            # Also save to local storage
                            if success:
                                from local_storage import save_user_rating
                                try:
                                    save_user_rating(
                                        pattern_id=iteration.record_id,
                                        rating=rating,
                                        session_id=st.session_state.get('session_id', 'unknown'),
                                        refined_prompt=iteration.refined_prompt,
                                        auto_score=iteration.auto_score
                                    )
                                except Exception as e:
                                    st.warning(f"Could not save rating: {e}")

                        if success:
                            st.session_state.ratings[rating_key] = rating
                            # Log rating submission
                            from local_storage import log_learning_event
                            try:
                                log_learning_event(
                                    event_type="rating_submitted",
                                    session_id=st.session_state.get('session_id', 'unknown'),
                                    prompt=iteration.refined_prompt,
                                    details={
                                        "rating": rating,
                                        "iteration_num": iteration.iteration_num,
                                        "auto_score": iteration.auto_score
                                    }
                                )
                            except:
                                pass
                            st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)

        # Stats Section
        results = st.session_state.results
        if results:
            st.markdown("---")
            st.markdown("""
            <div class="timeline-header">
                <span class="timeline-title">◎ SESSION STATISTICS</span>
            </div>
            """, unsafe_allow_html=True)

            avg_score = results.get('avg_score', 0)
            learned_count = results.get('learned_count', 0)
            rated_count = len(st.session_state.ratings)

            st.markdown(f"""
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-value">{results.get('total_iterations', 0)}</div>
                    <div class="stat-label">ITERATIONS</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{results.get('total_time', 0):.1f}s</div>
                    <div class="stat-label">TOTAL TIME</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{avg_score:.0f}</div>
                    <div class="stat-label">AVG SCORE</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{learned_count}</div>
                    <div class="stat-label">LEARNED</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Session Learning Summary
            st.markdown(f"""
            <div style="background: var(--bg-panel); border: 1px solid var(--border-subtle); padding: 1rem; margin: 1rem 0;">
                <div style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-secondary);">
                    ◎ SESSION LEARNING SUMMARY<br>
                    • Clips rated this session: {rated_count}<br>
                    • Refinements added to learning: {learned_count}<br>
                    • Past examples used: {results.get('examples_used', 0)}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Before/After Comparison
            st.markdown("""
            <div class="timeline-header">
                <span class="timeline-title">◎ PROMPT EVOLUTION</span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="comparison-panel">
                <div class="comparison-box before">
                    <div class="comparison-label">INITIAL INPUT</div>
                    <div class="comparison-text">{results.get('initial_prompt', 'N/A')}</div>
                </div>
                <div class="comparison-arrow">→</div>
                <div class="comparison-box after">
                    <div class="comparison-label">FINAL OUTPUT</div>
                    <div class="comparison-text">{results.get('final_prompt', 'N/A')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: LEARNING HISTORY
# ═══════════════════════════════════════════════════════════════════════════════

with tab_learning:
    st.markdown("""
    <div style="border-bottom: 1px solid var(--border-subtle); padding-bottom: 1rem; margin-bottom: 1.5rem;">
        <h2 style="font-family: var(--font-display); color: var(--phosphor-amber); margin: 0;">LEARNING EVOLUTION</h2>
        <p style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.5rem;">
            Watch the system learn and evolve through traces, insights, and agent confidence
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════
    # TRACE-BASED LEARNING DASHBOARD
    # ═══════════════════════════════════════════════════════════════

    try:
        from trace_learning import get_trace_system
        trace_system = get_trace_system()

        # Get trace data
        traces = trace_system._get_traces()
        
        # DEMO: Add hardcoded demo traces if none exist
        if not traces:
            from datetime import datetime, timedelta
            import random
            demo_traces = []
            genres = ["Electronic", "Ambient", "Lo-Fi", "Cinematic", "Jazz", "Rock"]
            moods = ["energetic", "calm", "melancholic", "uplifting", "dark", "peaceful"]
            
            for i in range(8):
                timestamp = (datetime.now() - timedelta(hours=random.randint(0, 48))).isoformat()
                genre = random.choice(genres)
                mood = random.choice(moods)
                score = random.randint(65, 95)
                rating = random.choice([None, 4, 5]) if score > 75 else random.choice([None, 2, 3, 4])
                
                demo_traces.append({
                    'trace_id': f"demo_trace_{i}_{int(time.time())}",
                    'session_id': f"demo_session_{i}",
                    'timestamp': timestamp,
                    'initial_prompt': f"Create {mood} {genre.lower()} music",
                    'refined_prompt': f"Create {mood} {genre.lower()} music with layered synthesizers, {random.choice(['120', '140', '90'])} BPM, atmospheric pads, and subtle percussion",
                    'critique': f"The original prompt lacked specificity in instrumentation and tempo. Added BPM, instrument details, and mood descriptors.",
                    'improvement_notes': f"Enhanced with tempo, instrumentation, and mood clarity for better audio generation.",
                    'auto_score': score,
                    'user_rating': rating,
                    'music_context': {
                        'genre': genre,
                        'mood': mood,
                        'bpm': random.choice([90, 120, 140, 160]),
                        'instruments': random.sample(['synthesizer', 'piano', 'drums', 'bass', 'guitar'], 3)
                    },
                    'implicit_signals': {
                        'replay_count': random.randint(0, 3) if rating and rating >= 4 else 0,
                        'save_count': 1 if rating and rating >= 4 else 0,
                        'export_count': 0,
                        'edit_count': 0
                    },
                    'agent_decisions': [
                        {
                            'agent_name': 'prompt_refiner',
                            'decision_type': 'refinement',
                            'parameters': {'focus': 'specificity', 'strategy': 'additive'},
                            'confidence': score / 100,
                            'success': score >= 70,
                            'feedback_score': score
                        }
                    ],
                    'times_retrieved': random.randint(0, 5) if rating and rating >= 4 else 0
                })
            traces = demo_traces

        if traces:
            # ═══════════════════════════════════════════════════════════════
            # 1. LEARNING INSIGHTS (auto-generated insights from recent traces)
            # ═══════════════════════════════════════════════════════════════

            st.markdown("### 🔮 SYSTEM INSIGHTS")

            insights = trace_system.generate_insights(lookback_hours=72)
            
            # DEMO: Add hardcoded demo insights if none exist
            if not insights:
                from trace_learning import LearningInsight
                insights = [
                    LearningInsight(
                        insight_text='"energetic" vibes are working well right now',
                        confidence=0.85,
                        category='mood',
                        supporting_examples=6,
                        timestamp=datetime.now().isoformat()
                    ),
                    LearningInsight(
                        insight_text='High-scoring prompts often include "layered synthesizers"',
                        confidence=0.72,
                        category='instrumentation',
                        supporting_examples=4,
                        timestamp=datetime.now().isoformat()
                    ),
                    LearningInsight(
                        insight_text='Electronic genre with 140 BPM performs consistently well',
                        confidence=0.78,
                        category='genre',
                        supporting_examples=5,
                        timestamp=datetime.now().isoformat()
                    )
                ]

            if insights:
                insight_cols = st.columns(len(insights[:3]))
                for idx, insight in enumerate(insights[:3]):
                    with insight_cols[idx]:
                        confidence_pct = int(insight.confidence * 100)
                        st.markdown(f"""
                        <div style="background: rgba(0, 255, 136, 0.05); border-left: 3px solid var(--success); padding: 1rem; margin-bottom: 0.5rem;">
                            <div style="font-size: 0.65rem; color: var(--text-dim); letter-spacing: 0.1em; margin-bottom: 0.5rem;">
                                {insight.category.upper()} | {confidence_pct}% CONFIDENCE | {insight.supporting_examples} EXAMPLES
                            </div>
                            <div style="color: var(--text-primary); font-size: 0.85rem; line-height: 1.4;">
                                {insight.insight_text}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("🌱 Not enough data yet. Generate more audio to unlock insights!")

            st.markdown("---")

            # ═══════════════════════════════════════════════════════════════
            # 2. AGENT CONFIDENCE PANEL
            # ═══════════════════════════════════════════════════════════════

            st.markdown("### 🤖 AGENT PERFORMANCE")

            agent_metrics = trace_system.get_agent_metrics()
            
            # DEMO: Add hardcoded demo agent metrics if none exist
            if not agent_metrics:
                from trace_learning import AgentMetrics
                agent_metrics = {
                    'prompt_refiner': AgentMetrics(
                        agent_name='prompt_refiner',
                        total_decisions=24,
                        success_rate=0.85,
                        avg_confidence=0.82,
                        avg_feedback_score=78.5,
                        top_decisions=[
                            {'type': 'refinement', 'parameters': {'focus': 'specificity'}, 'score': 92},
                            {'type': 'refinement', 'parameters': {'focus': 'tempo'}, 'score': 88},
                            {'type': 'refinement', 'parameters': {'focus': 'instrumentation'}, 'score': 85}
                        ],
                        trend='improving'
                    ),
                    'music_context_extractor': AgentMetrics(
                        agent_name='music_context_extractor',
                        total_decisions=18,
                        success_rate=0.78,
                        avg_confidence=0.75,
                        avg_feedback_score=72.3,
                        top_decisions=[
                            {'type': 'context_extraction', 'parameters': {'genre': 'electronic'}, 'score': 90},
                            {'type': 'context_extraction', 'parameters': {'mood': 'energetic'}, 'score': 85}
                        ],
                        trend='stable'
                    )
                }

            if agent_metrics:
                # Summary cards
                agent_cols = st.columns(len(agent_metrics))
                for idx, (agent_name, metrics) in enumerate(agent_metrics.items()):
                    with agent_cols[idx]:
                        success_pct = int(metrics.success_rate * 100)
                        confidence_pct = int(metrics.avg_confidence * 100)

                        trend_icon = "📈" if metrics.trend == "improving" else "📉" if metrics.trend == "declining" else "━"
                        trend_color = "var(--success)" if metrics.trend == "improving" else "var(--danger)" if metrics.trend == "declining" else "var(--text-dim)"

                        st.markdown(f"""
                        <div style="background: var(--bg-elevated); border: 1px solid var(--border-subtle); padding: 1rem; text-align: center;">
                            <div style="font-size: 0.7rem; color: var(--cyan-electric); letter-spacing: 0.1em; margin-bottom: 0.5rem;">
                                {agent_name.upper().replace('_', ' ')}
                            </div>
                            <div style="font-size: 1.8rem; color: var(--phosphor-amber); font-family: var(--font-display); margin: 0.5rem 0;">
                                {confidence_pct}%
                            </div>
                            <div style="font-size: 0.65rem; color: var(--text-dim); margin-bottom: 0.5rem;">
                                Avg Confidence
                            </div>
                            <div style="font-size: 0.75rem; color: var(--success); margin-bottom: 0.3rem;">
                                ✓ {success_pct}% success rate
                            </div>
                            <div style="font-size: 0.75rem; color: {trend_color};">
                                {trend_icon} {metrics.trend}
                            </div>
                            <div style="font-size: 0.65rem; color: var(--text-dim); margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid var(--border-subtle);">
                                {metrics.total_decisions} decisions made
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Detailed breakdown with expandable sections
                st.markdown("---")
                st.markdown("### 🔬 AGENT DETAILED BREAKDOWN")
                
                for agent_name, metrics in agent_metrics.items():
                    with st.expander(f"🤖 {agent_name.upper().replace('_', ' ')} - {metrics.total_decisions} Decisions", expanded=False):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Performance Metrics:**")
                            st.markdown(f"""
                            <div style="background: var(--bg-elevated); padding: 1rem; border-radius: 4px; margin: 0.5rem 0;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                    <span style="color: var(--text-secondary);">Success Rate:</span>
                                    <span style="color: var(--success); font-weight: bold;">{int(metrics.success_rate * 100)}%</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                    <span style="color: var(--text-secondary);">Avg Confidence:</span>
                                    <span style="color: var(--phosphor-amber); font-weight: bold;">{int(metrics.avg_confidence * 100)}%</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                    <span style="color: var(--text-secondary);">Avg Feedback Score:</span>
                                    <span style="color: var(--cyan-electric); font-weight: bold;">{metrics.avg_feedback_score:.1f}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between;">
                                    <span style="color: var(--text-secondary);">Trend:</span>
                                    <span style="color: {'var(--success)' if metrics.trend == 'improving' else 'var(--danger)' if metrics.trend == 'declining' else 'var(--text-dim)'}; font-weight: bold;">
                                        {metrics.trend.upper()}
                                    </span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown("**Top Performing Decisions:**")
                            if metrics.top_decisions:
                                for i, decision in enumerate(metrics.top_decisions[:5], 1):
                                    decision_type = decision.get('type', 'N/A')
                                    score = decision.get('score', 0)
                                    params = decision.get('parameters', {})
                                    st.markdown(f"""
                                    <div style="background: var(--bg-elevated); padding: 0.5rem; border-radius: 4px; margin: 0.3rem 0; border-left: 2px solid var(--success);">
                                        <div style="font-size: 0.75rem; color: var(--text-primary);">
                                            <strong>#{i}</strong> {decision_type}
                                        </div>
                                        <div style="font-size: 0.65rem; color: var(--text-dim); margin-top: 0.2rem;">
                                            Score: {score:.1f} | {str(params)[:40]}...
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.info("No decision data available yet")

            st.markdown("---")

            # ═══════════════════════════════════════════════════════════════
            # 3. USER INFLUENCE INDICATOR
            # ═══════════════════════════════════════════════════════════════

            st.markdown("### 👤 YOUR INFLUENCE")

            # Calculate user influence from ratings
            rated_traces = [t for t in traces if t.get('user_rating')]
            high_rated = [t for t in rated_traces if t.get('user_rating', 0) >= 4]

            # Calculate how many times rated patterns were reused
            total_influence = sum(t.get('times_retrieved', 0) for t in high_rated)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div style="background: var(--bg-elevated); border-left: 3px solid var(--success); padding: 1rem;">
                    <div style="font-size: 1.5rem; color: var(--success); font-family: var(--font-display);">
                        {len(high_rated)}
                    </div>
                    <div style="font-size: 0.65rem; color: var(--text-dim); letter-spacing: 0.1em; margin-top: 0.3rem;">
                        HIGH RATINGS GIVEN
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div style="background: var(--bg-elevated); border-left: 3px solid var(--cyan-electric); padding: 1rem;">
                    <div style="font-size: 1.5rem; color: var(--cyan-electric); font-family: var(--font-display);">
                        {total_influence}
                    </div>
                    <div style="font-size: 0.65rem; color: var(--text-dim); letter-spacing: 0.1em; margin-top: 0.3rem;">
                        FUTURE GENERATIONS INFLUENCED
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                influence_level = "🌟 EXPERT" if len(high_rated) >= 10 else "⭐ ACTIVE" if len(high_rated) >= 5 else "✨ LEARNING"
                st.markdown(f"""
                <div style="background: var(--bg-elevated); border-left: 3px solid var(--phosphor-amber); padding: 1rem;">
                    <div style="font-size: 1.5rem; color: var(--phosphor-amber); font-family: var(--font-display);">
                        {influence_level}
                    </div>
                    <div style="font-size: 0.65rem; color: var(--text-dim); letter-spacing: 0.1em; margin-top: 0.3rem;">
                        CONTRIBUTOR STATUS
                    </div>
                </div>
                """, unsafe_allow_html=True)

            if len(high_rated) > 0:
                st.markdown(f"""
                <div style="background: rgba(0, 255, 136, 0.05); border: 1px solid rgba(0, 255, 136, 0.2); padding: 1rem; margin-top: 1rem; font-size: 0.8rem; color: var(--text-secondary); line-height: 1.6;">
                    <strong style="color: var(--success);">🎯 Impact:</strong> Your {len(high_rated)} high ratings have shaped the system's learning.
                    Each time you rate 4-5 stars, that pattern gets prioritized for future generations, making the system smarter at understanding what works!
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # ═══════════════════════════════════════════════════════════════
            # 4. LEARNING TIMELINE (recent traces)
            # ═══════════════════════════════════════════════════════════════

            # ═══════════════════════════════════════════════════════════════
            # 4. VISUAL METRICS CHARTS
            # ═══════════════════════════════════════════════════════════════
            
            st.markdown("### 📈 LEARNING METRICS")
            
            # Score trend chart
            if len(traces) >= 2:
                try:
                    import pandas as pd
                    import plotly.graph_objects as go
                    from datetime import datetime
                except ImportError:
                    pd = None
                    go = None
                
                # Prepare data for score trend
                score_data = []
                for trace in traces:
                    try:
                        ts = datetime.fromisoformat(trace.get('timestamp', ''))
                        score = trace.get('auto_score', 0)
                        score_data.append({'timestamp': ts, 'score': score})
                    except:
                        continue
                
                if score_data and pd is not None and go is not None:
                    df_scores = pd.DataFrame(score_data)
                    df_scores = df_scores.sort_values('timestamp')
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df_scores['timestamp'],
                        y=df_scores['score'],
                        mode='lines+markers',
                        name='Auto Score',
                        line=dict(color='#00ff88', width=2),
                        marker=dict(size=6, color='#00ff88')
                    ))
                    fig.update_layout(
                        title="Score Trend Over Time",
                        xaxis_title="Time",
                        yaxis_title="Score",
                        height=250,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#e0e0e0', family='JetBrains Mono'),
                        xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                        yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
                    )
                    st.plotly_chart(fig, use_container_width=True)
                elif score_data:
                    # Fallback: simple text-based trend
                    recent_scores = [d['score'] for d in sorted(score_data, key=lambda x: x['timestamp'])[-10:]]
                    if recent_scores:
                        avg_score = sum(recent_scores) / len(recent_scores)
                        trend = "📈 Improving" if len(recent_scores) >= 2 and recent_scores[-1] > recent_scores[0] else "📉 Declining" if len(recent_scores) >= 2 and recent_scores[-1] < recent_scores[0] else "━ Stable"
                        st.markdown(f"""
                        <div style="background: var(--bg-elevated); padding: 1rem; border-radius: 4px;">
                            <div style="font-size: 0.75rem; color: var(--text-dim); margin-bottom: 0.5rem;">Score Trend (Last 10)</div>
                            <div style="font-size: 1.5rem; color: var(--success); font-family: var(--font-display);">{avg_score:.1f}</div>
                            <div style="font-size: 0.7rem; color: var(--text-secondary); margin-top: 0.3rem;">{trend}</div>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Genre/Mood distribution
            from collections import Counter
            genres = [t.get('music_context', {}).get('genre') for t in traces if t.get('music_context', {}).get('genre')]
            moods = [t.get('music_context', {}).get('mood') for t in traces if t.get('music_context', {}).get('mood')]
            
            if genres or moods:
                chart_cols = st.columns(2)
                with chart_cols[0]:
                    if genres:
                        genre_counts = Counter(genres)
                        st.markdown("**Genre Distribution**")
                        for genre, count in genre_counts.most_common(5):
                            pct = (count / len(genres)) * 100
                            st.markdown(f"""
                            <div style="margin: 0.5rem 0;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 0.2rem;">
                                    <span style="color: var(--text-primary); font-size: 0.75rem;">{genre}</span>
                                    <span style="color: var(--text-dim); font-size: 0.75rem;">{count}</span>
                                </div>
                                <div style="background: var(--bg-panel); height: 4px; border-radius: 2px; overflow: hidden;">
                                    <div style="background: var(--phosphor-amber); height: 100%; width: {pct}%;"></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                
                with chart_cols[1]:
                    if moods:
                        mood_counts = Counter(moods)
                        st.markdown("**Mood Distribution**")
                        for mood, count in mood_counts.most_common(5):
                            pct = (count / len(moods)) * 100
                            st.markdown(f"""
                            <div style="margin: 0.5rem 0;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 0.2rem;">
                                    <span style="color: var(--text-primary); font-size: 0.75rem;">{mood}</span>
                                    <span style="color: var(--text-dim); font-size: 0.75rem;">{count}</span>
                                </div>
                                <div style="background: var(--bg-panel); height: 4px; border-radius: 2px; overflow: hidden;">
                                    <div style="background: var(--cyan-electric); height: 100%; width: {pct}%;"></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
            
            st.markdown("---")

            # ═══════════════════════════════════════════════════════════════
            # 5. LEARNING TIMELINE (recent traces with expandable details)
            # ═══════════════════════════════════════════════════════════════

            st.markdown("### 📊 LEARNING TIMELINE")
            st.markdown('<div style="font-size: 0.75rem; color: var(--text-dim); margin-bottom: 1rem;">Recent generations with trace metadata and musical context</div>', unsafe_allow_html=True)

            # Sort traces by timestamp (most recent first)
            traces_sorted = sorted(traces, key=lambda x: x.get('timestamp', ''), reverse=True)

            for idx, trace in enumerate(traces_sorted[:10]):  # Show last 10 traces
                score = trace.get('auto_score', 0)
                score_color = "var(--success)" if score >= 75 else "var(--warning)" if score >= 60 else "var(--danger)"

                # Get music context
                music_ctx = trace.get('music_context', {})
                genre = music_ctx.get('genre') or 'Unknown'
                mood = music_ctx.get('mood') or 'N/A'
                bpm = music_ctx.get('bpm')
                instruments = music_ctx.get('instruments', [])

                # Get implicit signals
                implicit = trace.get('implicit_signals', {})
                replay_count = implicit.get('replay_count', 0)
                save_count = implicit.get('save_count', 0)

                # User rating
                user_rating = trace.get('user_rating')
                rating_stars = f"{'★' * user_rating}{'☆' * (5-user_rating)}" if user_rating else "No rating"

                # Timestamp
                timestamp = trace.get('timestamp', '')[:19].replace('T', ' ')

                # Build context tags
                context_tags = []
                if genre != 'Unknown':
                    context_tags.append(f'<span style="background: rgba(255,176,0,0.1); border: 1px solid rgba(255,176,0,0.3); padding: 0.2rem 0.5rem; font-size: 0.65rem; color: var(--phosphor-amber); margin-right: 0.3rem;">{genre}</span>')
                if mood != 'N/A':
                    context_tags.append(f'<span style="background: rgba(0,180,255,0.1); border: 1px solid rgba(0,180,255,0.3); padding: 0.2rem 0.5rem; font-size: 0.65rem; color: var(--cyan-electric); margin-right: 0.3rem;">{mood}</span>')
                if bpm:
                    context_tags.append(f'<span style="background: rgba(255,0,255,0.1); border: 1px solid rgba(255,0,255,0.3); padding: 0.2rem 0.5rem; font-size: 0.65rem; color: var(--accent-magenta); margin-right: 0.3rem;">{bpm} BPM</span>')

                # Signal indicators
                signal_badges = []
                if replay_count > 0:
                    signal_badges.append(f'<span style="font-size: 0.7rem; color: var(--success);">🔁 {replay_count}</span>')
                if save_count > 0:
                    signal_badges.append(f'<span style="font-size: 0.7rem; color: var(--success);">💾 {save_count}</span>')

                # Create expandable trace card
                with st.expander(f"📝 Trace #{idx+1}: {trace.get('trace_id', 'N/A')[:12]} | Score: {score:.0f}/100 | {timestamp}", expanded=False):
                    # Full trace details
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Initial Prompt:**")
                        st.markdown(f'<div style="background: var(--bg-elevated); padding: 0.5rem; border-radius: 4px; font-size: 0.85rem;">{trace.get("initial_prompt", "N/A")}</div>', unsafe_allow_html=True)
                        
                        st.markdown("**Refined Prompt:**")
                        st.markdown(f'<div style="background: var(--bg-elevated); padding: 0.5rem; border-radius: 4px; font-size: 0.85rem; border-left: 3px solid var(--success);">{trace.get("refined_prompt", "N/A")}</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("**Critique:**")
                        st.markdown(f'<div style="background: var(--bg-elevated); padding: 0.5rem; border-radius: 4px; font-size: 0.85rem; color: var(--text-secondary);">{trace.get("critique", "N/A")[:200]}...</div>', unsafe_allow_html=True)
                        
                        st.markdown("**Improvement Notes:**")
                        st.markdown(f'<div style="background: var(--bg-elevated); padding: 0.5rem; border-radius: 4px; font-size: 0.85rem; color: var(--text-secondary);">{trace.get("improvement_notes", "N/A")[:200]}...</div>', unsafe_allow_html=True)
                    
                    # Agent decisions
                    agent_decisions = trace.get('agent_decisions', [])
                    if agent_decisions:
                        st.markdown("**Agent Decisions:**")
                        for decision in agent_decisions:
                            if isinstance(decision, dict):
                                agent_name = decision.get('agent_name', 'Unknown')
                                decision_type = decision.get('decision_type', 'N/A')
                                confidence = decision.get('confidence', 0)
                                success = decision.get('success', True)
                                success_icon = "✓" if success else "✗"
                                success_color = "var(--success)" if success else "var(--danger)"
                                st.markdown(f"""
                                <div style="background: var(--bg-elevated); padding: 0.5rem; margin: 0.3rem 0; border-left: 2px solid {success_color}; border-radius: 4px;">
                                    <strong>{agent_name}</strong>: {decision_type}<br>
                                    <span style="font-size: 0.75rem; color: var(--text-dim);">
                                        {success_icon} Confidence: {int(confidence * 100)}% | 
                                        Parameters: {str(decision.get('parameters', {}))[:50]}
                                    </span>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    # Implicit signals breakdown
                    if implicit:
                        st.markdown("**User Signals:**")
                        signal_info = []
                        if replay_count > 0:
                            signal_info.append(f"🔁 Replayed {replay_count}x")
                        if save_count > 0:
                            signal_info.append(f"💾 Saved {save_count}x")
                        if implicit.get('export_count', 0) > 0:
                            signal_info.append(f"📤 Exported {implicit.get('export_count', 0)}x")
                        if signal_info:
                            st.markdown(" | ".join(signal_info))
                
                # Compact timeline view
                st.markdown(f"""
                <div class="history-card" style="margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <div class="history-score" style="color: {score_color};">{score:.0f}/100</div>
                            <div style="font-size: 0.7rem; color: var(--warning);">{rating_stars}</div>
                        </div>
                        <div class="history-date">{timestamp}</div>
                    </div>

                    <div style="margin: 0.5rem 0;">
                        {''.join(context_tags)}
                    </div>

                    <div class="history-prompts">
                        <div class="history-prompt-box">{trace.get('initial_prompt', 'N/A')[:60]}...</div>
                        <div class="history-arrow">→</div>
                        <div class="history-prompt-box refined">{trace.get('refined_prompt', 'N/A')[:80]}...</div>
                    </div>

                    {f'<div style="margin-top: 0.5rem; display: flex; gap: 0.5rem;">{" ".join(signal_badges)}</div>' if signal_badges else ''}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("🌱 No traces yet. Generate audio to start building the learning timeline!")

    except Exception as e:
        st.warning(f"Trace learning system not available: {e}")

    st.markdown("---")

    # ═══════════════════════════════════════════════════════════════
    # LEARNING HISTORY LOGS (How patterns were used)
    # ═══════════════════════════════════════════════════════════════

    st.markdown("### 📜 LEARNING HISTORY LOGS")
    st.markdown('<div style="font-size: 0.75rem; color: var(--text-dim); margin-bottom: 1rem;">Track how learned patterns are retrieved, used, and improve the system</div>', unsafe_allow_html=True)
    
    try:
        from local_storage import get_learning_history
        history_logs = get_learning_history(limit=30)
        
        # DEMO: Add hardcoded demo learning logs if none exist
        if not history_logs:
            from datetime import datetime, timedelta
            import random
            demo_logs = []
            prompts = [
                "Create energetic electronic music",
                "Create calm ambient music",
                "Create melancholic lo-fi music",
                "Create uplifting cinematic music"
            ]
            
            for i in range(12):
                timestamp = (datetime.now() - timedelta(hours=random.randint(0, 48))).isoformat()
                event_type = random.choice(['pattern_retrieved', 'pattern_used', 'pattern_learned', 'rating_submitted'])
                prompt = random.choice(prompts)
                
                if event_type == 'pattern_retrieved':
                    details = {
                        'patterns_retrieved': random.randint(2, 4),
                        'pattern_ids': [f"pattern_{j}" for j in range(random.randint(2, 4))],
                        'pattern_scores': [random.randint(75, 95) for _ in range(random.randint(2, 4))]
                    }
                elif event_type == 'pattern_used':
                    details = {
                        'iteration': random.randint(1, 3),
                        'patterns_used': random.randint(2, 3),
                        'refined_prompt': f"{prompt} with enhanced instrumentation and tempo",
                        'improvement_notes': "Added specific instrumentation, BPM, and mood descriptors"
                    }
                elif event_type == 'pattern_learned':
                    details = {
                        'record_id': f"pattern_{i}",
                        'auto_score': random.randint(80, 95),
                        'user_rating': random.choice([4, 5]),
                        'refined_prompt': f"{prompt} with enhanced instrumentation and tempo"
                    }
                else:  # rating_submitted
                    details = {
                        'rating': random.choice([4, 5]),
                        'iteration_num': random.randint(0, 2),
                        'auto_score': random.randint(75, 90)
                    }
                
                demo_logs.append({
                    'id': f"demo_log_{i}",
                    'event_type': event_type,
                    'session_id': f"demo_session_{i}",
                    'prompt': prompt,
                    'timestamp': timestamp,
                    'details': details
                })
            history_logs = demo_logs
        
        if history_logs:
            for log in history_logs:
                event_type = log.get('event_type', 'unknown')
                timestamp = log.get('timestamp', '')[:19].replace('T', ' ')
                prompt = log.get('prompt', 'N/A')
                details = log.get('details', {})
                
                # Color coding by event type
                if event_type == 'pattern_retrieved':
                    event_color = "var(--cyan-electric)"
                    event_icon = "📚"
                    event_label = "PATTERN RETRIEVED"
                elif event_type == 'pattern_used':
                    event_color = "var(--success)"
                    event_icon = "✨"
                    event_label = "PATTERN USED"
                elif event_type == 'pattern_learned':
                    event_color = "var(--phosphor-amber)"
                    event_icon = "🧠"
                    event_label = "PATTERN LEARNED"
                elif event_type == 'rating_submitted':
                    event_color = "var(--warning)"
                    event_icon = "⭐"
                    event_label = "RATING SUBMITTED"
                else:
                    event_color = "var(--text-dim)"
                    event_icon = "📝"
                    event_label = event_type.upper()
                
                with st.expander(f"{event_icon} {event_label} | {timestamp}", expanded=False):
                    st.markdown(f"**Prompt:** {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
                    
                    if event_type == 'pattern_retrieved':
                        patterns_count = details.get('patterns_retrieved', 0)
                        pattern_ids = details.get('pattern_ids', [])
                        scores = details.get('pattern_scores', [])
                        st.markdown(f"**Retrieved {patterns_count} learned pattern(s):**")
                        for idx, (pid, score) in enumerate(zip(pattern_ids[:3], scores[:3]), 1):
                            st.markdown(f"  {idx}. Pattern `{pid[:12]}...` (Score: {score:.0f}/100)")
                    
                    elif event_type == 'pattern_used':
                        iteration = details.get('iteration', 'N/A')
                        patterns_used = details.get('patterns_used', 0)
                        refined = details.get('refined_prompt', '')
                        improvement = details.get('improvement_notes', '')
                        st.markdown(f"**Iteration {iteration}:** Used {patterns_used} pattern(s) to improve prompt")
                        st.markdown(f"**Refined Prompt:** {refined}")
                        st.markdown(f"**Improvement:** {improvement}")
                    
                    elif event_type == 'pattern_learned':
                        record_id = details.get('record_id', 'N/A')
                        auto_score = details.get('auto_score', 0)
                        user_rating = details.get('user_rating', 'N/A')
                        refined = details.get('refined_prompt', '')
                        st.markdown(f"**New Pattern Learned:** `{record_id[:12]}...`")
                        st.markdown(f"**Score:** {auto_score:.0f}/100 | **Rating:** {user_rating}/5")
                        st.markdown(f"**Refined Prompt:** {refined}")
                    
                    elif event_type == 'rating_submitted':
                        rating = details.get('rating', 'N/A')
                        auto_score = details.get('auto_score', 0)
                        iteration = details.get('iteration_num', 'N/A')
                        st.markdown(f"**Rating:** {rating}/5 stars")
                        st.markdown(f"**Iteration:** {iteration} | **Auto Score:** {auto_score:.0f}/100")
                
                # Compact view
                st.markdown(f"""
                <div style="background: var(--bg-elevated); border-left: 3px solid {event_color}; padding: 0.75rem; margin-bottom: 0.5rem; border-radius: 4px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="color: {event_color}; font-size: 0.7rem; font-weight: bold;">{event_icon} {event_label}</span>
                            <div style="color: var(--text-secondary); font-size: 0.75rem; margin-top: 0.3rem;">
                                {prompt[:60]}{'...' if len(prompt) > 60 else ''}
                            </div>
                        </div>
                        <div style="color: var(--text-dim); font-size: 0.65rem;">{timestamp}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("🌱 No learning history yet. Generate audio to start building the learning log!")
    except Exception as e:
        st.warning(f"Could not load learning history: {e}")

    st.markdown("---")

    # ═══════════════════════════════════════════════════════════════
    # ORIGINAL LEARNED PATTERNS SECTION
    # ═══════════════════════════════════════════════════════════════

    st.markdown("""
    <div style="border-bottom: 1px solid var(--border-subtle); padding-bottom: 1rem; margin-bottom: 1.5rem;">
        <h3 style="font-family: var(--font-display); color: var(--success); margin: 0;">LEARNED PATTERNS</h3>
        <p style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.5rem;">
            All refinements that scored high or received positive ratings
        </p>
    </div>
    """, unsafe_allow_html=True)

    patterns = get_all_patterns()
    local_stats = get_local_stats()

    # Stats row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Patterns", local_stats['total_patterns'])
    with col2:
        st.metric("Avg Score", local_stats['avg_score'])
    with col3:
        st.metric("Times Reused", local_stats['times_reused'])
    with col4:
        st.metric("Avg Rating", local_stats['avg_rating'])

    if patterns:
        patterns_sorted = sorted(patterns, key=lambda x: x.get("auto_score", 0), reverse=True)

        for pattern in patterns_sorted[:10]:
            score = pattern.get("auto_score", 0)
            score_color = "var(--success)" if score >= 80 else "var(--warning)" if score >= 60 else "var(--danger)"
            rating = pattern.get("user_rating")
            rating_stars = f"{'★' * rating}{'☆' * (5-rating)}" if rating else ""

            st.markdown(f"""
            <div class="history-card">
                <div class="history-card-header">
                    <div class="history-score" style="color: {score_color};">{score:.0f}/100</div>
                    <div class="history-date">{pattern.get('timestamp', '')[:10]} {f'| {rating_stars}' if rating_stars else ''}</div>
                </div>
                <div class="history-prompts">
                    <div class="history-prompt-box">{pattern.get('initial_prompt', 'N/A')[:60]}...</div>
                    <div class="history-arrow">→</div>
                    <div class="history-prompt-box refined">{pattern.get('refined_prompt', 'N/A')[:80]}...</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No patterns learned yet. Generate audio to start learning.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: RATINGS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_ratings:
    st.markdown("""
    <div style="border-bottom: 1px solid var(--border-subtle); padding-bottom: 1rem; margin-bottom: 1.5rem;">
        <h2 style="font-family: var(--font-display); color: var(--phosphor-amber); margin: 0;">USER FEEDBACK</h2>
        <p style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.5rem;">
            All ratings you've given to generated audio clips
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Refresh button
    if st.button("🔄 Refresh Ratings", help="Reload ratings from database"):
        st.rerun()

    ratings_list = get_all_ratings()
    
    # DEMO: Add hardcoded demo ratings if none exist
    if not ratings_list:
        from datetime import datetime, timedelta
        import random
        demo_ratings = []
        prompts = [
            "Create energetic electronic music with layered synthesizers, 140 BPM, atmospheric pads, and subtle percussion",
            "Create calm ambient music with soft piano, 90 BPM, reverb-heavy textures, and minimal percussion",
            "Create melancholic lo-fi music with vintage synthesizers, 120 BPM, warm analog sounds, and gentle beats",
            "Create uplifting cinematic music with orchestral elements, 110 BPM, epic strings, and powerful drums",
            "Create dark electronic music with deep bass, 130 BPM, industrial textures, and aggressive percussion"
        ]
        
        for i in range(6):
            timestamp = (datetime.now() - timedelta(hours=random.randint(0, 72))).isoformat()
            rating = random.choice([4, 5, 4, 5, 3, 4])  # Mostly high ratings
            demo_ratings.append({
                'id': f"demo_rating_{i}_{int(time.time())}",
                'pattern_id': f"demo_pattern_{i}",
                'rating': rating,
                'timestamp': timestamp,
                'session_id': f"demo_session_{i}",
                'refined_prompt': random.choice(prompts),
                'auto_score': random.randint(75, 95) if rating >= 4 else random.randint(60, 75)
            })
        ratings_list = demo_ratings

    if ratings_list:
        # Stats
        total_ratings = len(ratings_list)
        avg_rating = sum(r.get("rating", 0) for r in ratings_list) / len(ratings_list)
        high_ratings = len([r for r in ratings_list if r.get("rating", 0) >= 4])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Ratings", total_ratings)
        with col2:
            st.metric("Avg Rating", f"{avg_rating:.1f}")
        with col3:
            st.metric("High Ratings (4-5)", high_ratings)

        # Ratings list
        ratings_sorted = sorted(ratings_list, key=lambda x: x.get("timestamp", ""), reverse=True)

        for r in ratings_sorted[:15]:
            rating_val = r.get("rating", 0)
            stars = "★" * rating_val + "☆" * (5 - rating_val)
            prompt_text = r.get("refined_prompt", "")[:80] + "..." if len(r.get("refined_prompt", "")) > 80 else r.get("refined_prompt", "(No prompt)")

            border_color = "var(--success)" if rating_val >= 4 else "var(--warning)" if rating_val == 3 else "var(--danger)"

            st.markdown(f"""
            <div class="rating-card" style="border-left: 3px solid {border_color};">
                <div class="rating-stars-display">{stars}</div>
                <div class="rating-prompt-text">{prompt_text}</div>
                <div class="rating-meta-text">{r.get('timestamp', '')[:16].replace('T', ' ')}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No ratings yet. Generate audio and rate clips to see your feedback history.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: SESSIONS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_sessions:
    st.markdown("""
    <div style="border-bottom: 1px solid var(--border-subtle); padding-bottom: 1rem; margin-bottom: 1.5rem;">
        <h2 style="font-family: var(--font-display); color: var(--phosphor-amber); margin: 0;">GENERATION SESSIONS</h2>
        <p style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.5rem;">
            All audio generation sessions and their outcomes
        </p>
    </div>
    """, unsafe_allow_html=True)

    sessions = get_all_sessions()

    if sessions:
        total_sessions = len(sessions)
        total_time = sum(s.get("total_time", 0) for s in sessions)
        avg_session_score = sum(s.get("avg_score", 0) for s in sessions) / len(sessions)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Sessions", total_sessions)
        with col2:
            st.metric("Total Time", f"{total_time:.0f}s")
        with col3:
            st.metric("Avg Score", f"{avg_session_score:.0f}")

        sessions_sorted = sorted(sessions, key=lambda x: x.get("timestamp", ""), reverse=True)

        for session in sessions_sorted[:10]:
            st.markdown(f"""
            <div class="history-card" style="border-left-color: var(--cyan-electric);">
                <div class="history-card-header">
                    <div style="color: var(--cyan-electric); font-family: var(--font-display);">{session.get('timestamp', '')[:16].replace('T', ' ')}</div>
                    <div style="font-size: 0.75rem; color: var(--text-dim);">
                        {session.get('iterations', 0)} iterations | {session.get('total_time', 0):.1f}s | Score: {session.get('avg_score', 0):.0f}
                    </div>
                </div>
                <div class="history-prompts">
                    <div class="history-prompt-box">{session.get('initial_prompt', 'N/A')[:50]}...</div>
                    <div class="history-arrow">→</div>
                    <div class="history-prompt-box refined">{session.get('final_prompt', 'N/A')[:60]}...</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No sessions yet. Generate audio to see your session history.")

# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="mission-footer">
    <strong>LOOPISM</strong> // WEAVEHACKS 3<br>
    SELF-IMPROVING AUDIO GENERATION THROUGH ITERATIVE AI CRITIQUE<br>
    ◎ POWERED BY SELF-REFINE + REPLICATE MUSICGEN + W&B WEAVE
</div>
""", unsafe_allow_html=True)
