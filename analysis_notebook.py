"""
LOOPISM LEARNING ANALYTICS
Interactive analysis notebook powered by Marimo

Run with: marimo edit analysis_notebook.py
"""

import marimo

__generated_with = "0.5.0"
app = marimo.App(width="full")


@app.cell
def __():
    import marimo as mo
    import json
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from pathlib import Path
    from datetime import datetime
    return mo, json, pd, px, go, Path, datetime


@app.cell
def __(mo):
    mo.md("""
    # LOOPISM LEARNING ANALYTICS

    Interactive analysis of the self-improving audio generation system.

    **Data includes:**
    - Trace performance over time
    - Genre and mood effectiveness
    - Agent decision patterns
    - User rating impact on learning
    """)
    return


@app.cell
def __(json, Path, mo):
    # Load learning data
    data_path = Path("loopism_outputs/analytics/learning_data.json")

    if data_path.exists():
        with open(data_path) as f:
            data = json.load(f)
        status = f"Data loaded: {data.get('export_timestamp', 'Unknown')}"
    else:
        # Use demo data if file doesn't exist
        data = {
            "traces": [
                {"trace_id": "a1b2c3", "timestamp": "2026-02-01T12:15:00", "auto_score": 85.5, "user_rating": 4,
                 "music_context": {"genre": "EDM", "mood": "energetic", "bpm": 128}},
                {"trace_id": "b2c3d4", "timestamp": "2026-02-01T12:15:18", "auto_score": 88.2, "user_rating": 5,
                 "music_context": {"genre": "EDM", "mood": "euphoric", "bpm": 128}},
                {"trace_id": "c3d4e5", "timestamp": "2026-02-01T12:15:35", "auto_score": 91.0, "user_rating": 5,
                 "music_context": {"genre": "EDM", "mood": "euphoric", "bpm": 128}},
                {"trace_id": "d4e5f6", "timestamp": "2026-02-01T12:18:00", "auto_score": 82.8, "user_rating": 4,
                 "music_context": {"genre": "Rock", "mood": "aggressive", "bpm": 160}},
                {"trace_id": "e5f6a7", "timestamp": "2026-02-01T12:18:17", "auto_score": 87.5, "user_rating": 4,
                 "music_context": {"genre": "Rock", "mood": "intense", "bpm": 165}},
                {"trace_id": "f6a7b8", "timestamp": "2026-02-01T12:18:34", "auto_score": 90.2, "user_rating": 5,
                 "music_context": {"genre": "Rock", "mood": "explosive", "bpm": 165}},
            ],
            "ratings": [
                {"rating": 4, "timestamp": "2026-02-01T12:15:05", "auto_score": 85.5},
                {"rating": 5, "timestamp": "2026-02-01T12:15:22", "auto_score": 88.2},
                {"rating": 5, "timestamp": "2026-02-01T12:15:40", "auto_score": 91.0},
                {"rating": 4, "timestamp": "2026-02-01T12:18:05", "auto_score": 82.8},
                {"rating": 4, "timestamp": "2026-02-01T12:18:20", "auto_score": 87.5},
                {"rating": 5, "timestamp": "2026-02-01T12:18:38", "auto_score": 90.2},
            ],
            "summary": {"total_traces": 6, "avg_score": 87.5, "avg_rating": 4.5}
        }
        status = "Using demo data (export data to see real results)"

    mo.md(f"**Status:** {status}")
    return data, data_path, status


@app.cell
def __(mo):
    # Filters
    mo.md("## Filters")
    return


@app.cell
def __(mo):
    score_threshold = mo.ui.slider(
        start=50, stop=100, value=70, step=5,
        label="Minimum Score Threshold"
    )
    return score_threshold,


@app.cell
def __(mo):
    genre_filter = mo.ui.dropdown(
        options={"All": "all", "EDM": "EDM", "Rock": "Rock", "Ambient": "Ambient", "Lo-Fi": "Lo-Fi"},
        value="all",
        label="Genre Filter"
    )
    return genre_filter,


@app.cell
def __(score_threshold, genre_filter):
    score_threshold, genre_filter
    return


@app.cell
def __(data, pd, score_threshold, genre_filter):
    # Process traces into DataFrame
    traces = data.get("traces", [])

    if traces:
        df_traces = pd.DataFrame([
            {
                "trace_id": t.get("trace_id", ""),
                "timestamp": t.get("timestamp", ""),
                "score": t.get("auto_score", 0),
                "rating": t.get("user_rating", 0),
                "genre": t.get("music_context", {}).get("genre", "Unknown"),
                "mood": t.get("music_context", {}).get("mood", "Unknown"),
                "bpm": t.get("music_context", {}).get("bpm", 0),
            }
            for t in traces
        ])
        df_traces["timestamp"] = pd.to_datetime(df_traces["timestamp"])

        # Apply filters
        filtered_df = df_traces[df_traces["score"] >= score_threshold.value]
        if genre_filter.value != "all":
            filtered_df = filtered_df[filtered_df["genre"] == genre_filter.value]
    else:
        filtered_df = pd.DataFrame()

    filtered_df
    return traces, df_traces, filtered_df


@app.cell
def __(mo, filtered_df):
    # Summary stats
    if not filtered_df.empty:
        mo.md(f"""
        ## Summary Statistics

        | Metric | Value |
        |--------|-------|
        | Total Traces | {len(filtered_df)} |
        | Average Score | {filtered_df['score'].mean():.1f} |
        | Average Rating | {filtered_df['rating'].mean():.1f} |
        | High Ratings (4-5) | {len(filtered_df[filtered_df['rating'] >= 4])} |
        """)
    else:
        mo.md("No data available for selected filters.")
    return


@app.cell
def __(mo):
    mo.md("## Score Trend Over Time")
    return


@app.cell
def __(filtered_df, px):
    # Score trend chart
    if not filtered_df.empty:
        fig_trend = px.line(
            filtered_df.sort_values("timestamp"),
            x="timestamp",
            y="score",
            color="genre",
            markers=True,
            title="Score Progression Over Time",
            template="plotly_dark"
        )
        fig_trend.update_layout(
            paper_bgcolor="#0a0a0a",
            plot_bgcolor="#1a1a1a",
            font_color="#e0e0e0",
            xaxis_title="Time",
            yaxis_title="Auto Score",
            yaxis_range=[50, 100]
        )
        fig_trend.update_traces(line=dict(width=2))
        fig_trend
    else:
        None
    return fig_trend,


@app.cell
def __(mo):
    mo.md("## Genre & Mood Performance")
    return


@app.cell
def __(filtered_df, px, go):
    # Genre/Mood heatmap
    if not filtered_df.empty and len(filtered_df) > 1:
        # Create pivot table for heatmap
        heatmap_data = filtered_df.groupby(["genre", "mood"])["score"].mean().reset_index()
        pivot = heatmap_data.pivot(index="genre", columns="mood", values="score")

        fig_heatmap = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale=[[0, "#1a1a1a"], [0.5, "#ffb000"], [1, "#00ff88"]],
            text=[[f"{v:.1f}" if not pd.isna(v) else "" for v in row] for row in pivot.values],
            texttemplate="%{text}",
            textfont={"size": 14},
            hoverongaps=False
        ))
        fig_heatmap.update_layout(
            title="Average Score by Genre & Mood",
            template="plotly_dark",
            paper_bgcolor="#0a0a0a",
            plot_bgcolor="#1a1a1a",
            font_color="#e0e0e0",
            xaxis_title="Mood",
            yaxis_title="Genre"
        )
        fig_heatmap
    else:
        None
    return fig_heatmap, heatmap_data, pivot


@app.cell
def __(mo):
    mo.md("## Rating Distribution")
    return


@app.cell
def __(filtered_df, px):
    # Rating distribution
    if not filtered_df.empty:
        fig_ratings = px.histogram(
            filtered_df,
            x="rating",
            color="genre",
            barmode="group",
            title="User Ratings Distribution by Genre",
            template="plotly_dark",
            nbins=5
        )
        fig_ratings.update_layout(
            paper_bgcolor="#0a0a0a",
            plot_bgcolor="#1a1a1a",
            font_color="#e0e0e0",
            xaxis_title="Rating (Stars)",
            yaxis_title="Count",
            bargap=0.2
        )
        fig_ratings
    else:
        None
    return fig_ratings,


@app.cell
def __(mo):
    mo.md("## Agent Performance")
    return


@app.cell
def __(data, go, pd):
    # Agent performance radar
    agent_metrics = data.get("agent_metrics", {})

    if agent_metrics:
        categories = ["Score Avg", "User Rating", "Trend", "Patterns Used", "Recent (24h)"]
        values = [
            min(agent_metrics.get("avg_score", 0) / 100, 1),
            agent_metrics.get("avg_user_rating", 0) / 5,
            min(max(agent_metrics.get("score_trend", 0) + 5, 0) / 10, 1),
            min(agent_metrics.get("examples_used_as_fewshot", 0) / 20, 1),
            min(agent_metrics.get("recent_examples_24h", 0) / 10, 1)
        ]

        fig_radar = go.Figure(data=go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            fillcolor="rgba(255, 176, 0, 0.3)",
            line=dict(color="#ffb000", width=2)
        ))
        fig_radar.update_layout(
            polar=dict(
                bgcolor="#1a1a1a",
                radialaxis=dict(visible=True, range=[0, 1], gridcolor="#333"),
                angularaxis=dict(gridcolor="#333")
            ),
            template="plotly_dark",
            paper_bgcolor="#0a0a0a",
            font_color="#e0e0e0",
            title="Agent Performance Metrics",
            showlegend=False
        )
        fig_radar
    else:
        None
    return agent_metrics, categories, values, fig_radar


@app.cell
def __(mo):
    mo.md("## BPM vs Score Analysis")
    return


@app.cell
def __(filtered_df, px):
    # BPM scatter
    if not filtered_df.empty and filtered_df["bpm"].sum() > 0:
        fig_bpm = px.scatter(
            filtered_df,
            x="bpm",
            y="score",
            color="genre",
            size="rating",
            hover_data=["mood", "trace_id"],
            title="BPM vs Score (size = rating)",
            template="plotly_dark"
        )
        fig_bpm.update_layout(
            paper_bgcolor="#0a0a0a",
            plot_bgcolor="#1a1a1a",
            font_color="#e0e0e0",
            xaxis_title="BPM",
            yaxis_title="Auto Score"
        )
        fig_bpm
    else:
        None
    return fig_bpm,


@app.cell
def __(mo):
    mo.md("## Top Keywords in High-Scoring Prompts")
    return


@app.cell
def __(data, px, pd):
    # Top keywords bar chart
    agent_metrics_kw = data.get("agent_metrics", {})
    top_keywords = agent_metrics_kw.get("top_keywords", [])

    if top_keywords:
        df_keywords = pd.DataFrame(top_keywords)
        fig_keywords = px.bar(
            df_keywords,
            x="word",
            y="count",
            title="Most Common Keywords in High-Scoring Refinements",
            template="plotly_dark",
            color="count",
            color_continuous_scale=[[0, "#1a1a1a"], [0.5, "#00b4ff"], [1, "#00ff88"]]
        )
        fig_keywords.update_layout(
            paper_bgcolor="#0a0a0a",
            plot_bgcolor="#1a1a1a",
            font_color="#e0e0e0",
            xaxis_title="Keyword",
            yaxis_title="Frequency",
            showlegend=False
        )
        fig_keywords
    else:
        None
    return agent_metrics_kw, top_keywords, df_keywords, fig_keywords


@app.cell
def __(mo):
    mo.md("## Pattern Learning Velocity")
    return


@app.cell
def __(data, px, pd, datetime):
    # Pattern learning velocity (patterns learned per day)
    patterns = data.get("patterns", [])
    learning_history = data.get("learning_history", [])

    # Combine timestamps from patterns and learning history
    all_events = []
    for p in patterns:
        if p.get("timestamp"):
            all_events.append({"timestamp": p["timestamp"], "type": "pattern"})
    for h in learning_history:
        if h.get("event_type") == "pattern_learned" and h.get("timestamp"):
            all_events.append({"timestamp": h["timestamp"], "type": "learned"})

    if all_events:
        df_events = pd.DataFrame(all_events)
        df_events["timestamp"] = pd.to_datetime(df_events["timestamp"])
        df_events["date"] = df_events["timestamp"].dt.date

        # Count patterns per day
        velocity = df_events.groupby("date").size().reset_index(name="patterns_learned")
        velocity["date"] = pd.to_datetime(velocity["date"])
        velocity["cumulative"] = velocity["patterns_learned"].cumsum()

        fig_velocity = px.area(
            velocity,
            x="date",
            y="cumulative",
            title="Pattern Learning Velocity (Cumulative)",
            template="plotly_dark",
            markers=True
        )
        fig_velocity.update_traces(
            fill="tozeroy",
            fillcolor="rgba(0, 255, 136, 0.2)",
            line=dict(color="#00ff88", width=2)
        )
        fig_velocity.update_layout(
            paper_bgcolor="#0a0a0a",
            plot_bgcolor="#1a1a1a",
            font_color="#e0e0e0",
            xaxis_title="Date",
            yaxis_title="Total Patterns Learned"
        )
        fig_velocity
    else:
        None
    return patterns, learning_history, all_events, df_events, velocity, fig_velocity


@app.cell
def __(mo):
    mo.md("## Date Range Filter")
    return


@app.cell
def __(mo):
    date_range = mo.ui.date_range(
        start="2026-01-01",
        stop="2026-12-31",
        label="Filter by Date Range"
    )
    return date_range,


@app.cell
def __(date_range):
    date_range
    return


@app.cell
def __(mo):
    mo.md("""
    ---
    **Loopism Learning Analytics** | Powered by Marimo

    *Export new data from the Loopism app to refresh this analysis.*
    """)
    return


if __name__ == "__main__":
    app.run()
