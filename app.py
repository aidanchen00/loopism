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
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st

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
        --text-dim: #555555;

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

    /* Hide Streamlit branding */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}

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
        margin: 1rem 0;
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
    metrics = get_metrics()
    if metrics and metrics.total_examples > 0:
        st.markdown(f"""
        <div style="text-align: center;">
            <span class="learning-badge">
                LEARNING ACTIVE • {metrics.total_examples} PATTERNS LEARNED
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
# INTELLIGENCE DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

with st.expander("🧠 INTELLIGENCE DASHBOARD", expanded=False):
    try:
        metrics = get_metrics()

        if metrics and metrics.total_examples > 0:
            # Metrics Grid
            st.markdown("""
            <div class="intel-dashboard">
                <div class="intel-grid">
            """, unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                delta_class = "positive" if metrics.recent_examples_24h > 0 else ""
                delta_text = f"+{metrics.recent_examples_24h} today" if metrics.recent_examples_24h > 0 else "—"
                st.markdown(f"""
                <div class="intel-card">
                    <div class="intel-value">{metrics.total_examples}</div>
                    <div class="intel-label">Patterns Learned</div>
                    <div class="intel-delta {delta_class}">{delta_text}</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="intel-card">
                    <div class="intel-value">{metrics.avg_score:.0f}</div>
                    <div class="intel-label">Avg Score</div>
                    <div class="intel-delta">out of 100</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                rating_display = f"{metrics.avg_user_rating:.1f}" if metrics.avg_user_rating > 0 else "—"
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
                    <div class="intel-value">{metrics.examples_used_as_fewshot}</div>
                    <div class="intel-label">Times Reused</div>
                    <div class="intel-delta">as examples</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            # Top Patterns
            if metrics.top_patterns:
                st.markdown("""
                <div class="intel-patterns">
                    <div class="intel-pattern-title">◎ TOP LEARNED PATTERNS</div>
                """, unsafe_allow_html=True)

                for pattern in metrics.top_patterns[:3]:
                    st.markdown(f"""
                    <div class="intel-pattern-item">
                        "{pattern['initial']}" → "{pattern['refined']}"
                        <span class="intel-pattern-score">{pattern['score']:.0f}/100</span>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

            # Top Keywords
            if metrics.top_keywords:
                st.markdown('<div class="intel-patterns"><div class="intel-pattern-title">◎ TOP KEYWORDS</div></div>', unsafe_allow_html=True)
                st.markdown('<div class="intel-keywords">', unsafe_allow_html=True)
                for kw in metrics.top_keywords[:8]:
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
    # API Status
    st.markdown("### SYSTEM STATUS")

    replicate_key = os.environ.get("REPLICATE_API_TOKEN", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    wandb_key = os.environ.get("WANDB_API_KEY", "")

    # Show status indicators
    col1, col2 = st.columns(2)
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

    # Mission Parameters
    st.markdown("### MISSION PARAMETERS")

    max_iterations = st.slider(
        "ITERATIONS",
        min_value=2,
        max_value=5,
        value=3,
        help="Number of refinement cycles"
    )

    audio_duration = st.slider(
        "AUDIO DURATION (SEC)",
        min_value=3,
        max_value=10,
        value=5,
        help="Length of generated audio"
    )

    enable_learning = st.checkbox("🧠 ENABLE LEARNING", value=True, help="Use and contribute to learned patterns")

    st.markdown("---")

    # Quick Launch
    st.markdown("### QUICK LAUNCH")

    quick_prompts = [
        ("◎ SUMMER VIBES", "happy summer vibes"),
        ("◎ CINEMATIC", "epic cinematic trailer"),
        ("◎ LOFI BEATS", "chill lofi study beats"),
        ("◎ WORKOUT", "energetic workout music"),
        ("◎ AMBIENT", "ambient night atmosphere"),
    ]

    for label, prompt in quick_prompts:
        if st.button(label, key=f"quick_{prompt}", use_container_width=True):
            st.session_state.selected_prompt = prompt
            st.rerun()

    st.markdown("---")

    # Weave Link
    st.markdown("### TELEMETRY")
    st.markdown("""
    <a href="https://wandb.ai/" target="_blank" class="weave-link">
        ◎ OPEN WEAVE DASHBOARD
    </a>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ═══════════════════════════════════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════════════════════════════════
# GENERATION LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

if generate_btn and can_run:
    st.session_state.running = True
    st.session_state.iterations = []
    st.session_state.results = None
    st.session_state.ratings = {}
    st.session_state.using_cache = False

    # Check if this is a cached quick prompt
    prompt_is_cached = is_prompt_cached(user_prompt)

    # Clear selected prompt
    if "selected_prompt" in st.session_state:
        del st.session_state.selected_prompt

    try:
        if prompt_is_cached:
            # ═══════════════════════════════════════════════════════════════
            # CACHED QUICK PROMPT - Load with simulated delays
            # ═══════════════════════════════════════════════════════════════
            st.session_state.using_cache = True

            # Create placeholder for progressive loading
            progress_placeholder = st.empty()
            iteration_placeholders = []

            # Show loading status
            progress_placeholder.markdown("""
            <div style="text-align: center; padding: 2rem;">
                <div style="font-family: var(--font-display); color: var(--phosphor-amber); font-size: 1.2rem; margin-bottom: 1rem;">
                    ◎ LOADING CACHED DEMO
                </div>
                <div style="font-family: var(--font-mono); color: var(--text-secondary); font-size: 0.8rem;">
                    Pre-generated audio loading...
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Stream iterations with delays
            iterations_loaded = []
            for iteration in stream_cached_iterations(user_prompt, simulate_delay=True):
                iterations_loaded.append(iteration)
                st.session_state.iterations = iterations_loaded.copy()

                # Update progress
                progress_placeholder.markdown(f"""
                <div style="text-align: center; padding: 1rem;">
                    <div style="font-family: var(--font-mono); color: var(--success); font-size: 0.9rem;">
                        ◎ Loaded iteration {len(iterations_loaded)} of 3
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Load comparison data
            st.session_state.results = load_cached_comparison_data(user_prompt)

            # Clear progress placeholder
            progress_placeholder.empty()

            st.success("◎ DEMO LOADED — CACHED AUDIO READY")

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
    using_cache = st.session_state.get("using_cache", False)

    cache_badge = ""
    if using_cache:
        cache_badge = '<span style="background: rgba(0, 255, 255, 0.1); border: 1px solid var(--cyan-electric); color: var(--cyan-electric); padding: 0.2rem 0.5rem; font-size: 0.6rem; margin-left: 1rem;">⚡ CACHED DEMO</span>'

    st.markdown(f"""
    <div class="timeline-header">
        <span class="timeline-title">◎ ITERATION TIMELINE</span>
        {cache_badge}
        <span class="timeline-status">● COMPLETE</span>
    </div>
    """, unsafe_allow_html=True)

    # Show examples used indicator
    if using_cache:
        st.markdown("""
        <div class="examples-indicator" style="margin-bottom: 1rem; color: var(--cyan-electric);">
            ⚡ Pre-generated demo clips loaded instantly
        </div>
        """, unsafe_allow_html=True)
    elif examples_used > 0:
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
                    <div style="display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.5rem;">
                        <span class="score-badge {score_class}">◎ {score:.0f}/100</span>
                        {f'<span class="learning-indicator">🧠 Added to learning</span>' if iteration.added_to_learning else ''}
                    </div>
                    <div class="prompt-display">{iteration.refined_prompt}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Audio Player
            if os.path.exists(iteration.audio_path):
                st.markdown('<div class="audio-container">', unsafe_allow_html=True)
                st.audio(iteration.audio_path)
                st.markdown('</div>', unsafe_allow_html=True)

            # Expandable Details
            with st.expander("◎ VIEW CRITIQUE"):
                st.markdown(f"""
                <div class="critique-box">{iteration.critique}</div>
                <div class="improvement-note">{iteration.improvement_notes}</div>
                """, unsafe_allow_html=True)

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

                    if success:
                        st.session_state.ratings[rating_key] = rating
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

        # Weave Dashboard Link
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <a href="https://wandb.ai/" target="_blank" class="weave-link">
                ◎ VIEW FULL TRACE IN WEAVE DASHBOARD
            </a>
        </div>
        """, unsafe_allow_html=True)

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
