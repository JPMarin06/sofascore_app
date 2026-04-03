import streamlit as st
import pandas as pd
import numpy as np
import time

from sofascore_client import SofascoreClient
from data_parser import (
    parse_statistics, parse_incidents,
    parse_lineups, parse_shotmap,
)
from charts import (
    plot_match_stats, plot_timeline, plot_shotmap,
    plot_player_radar, plot_player_heatmap,
    plot_player_shots, plot_player_bars, plot_compare_radar,
)

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sofascore Analyzer",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0d1117;
    color: #e6edf3;
}

/* Hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }

/* Main container */
.block-container {
    padding: 1.5rem 2rem 2rem 2rem;
    max-width: 1400px;
}

/* Score card */
.score-card {
    background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
    border: 1px solid #21262d;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    text-align: center;
    margin-bottom: 1.5rem;
}

.score-main {
    font-family: 'JetBrains Mono', monospace;
    font-size: 3.5rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    line-height: 1;
    margin: 0.5rem 0;
}

.team-name-home { color: #00d4ff; font-size: 1.3rem; font-weight: 600; }
.team-name-away { color: #ff6b6b; font-size: 1.3rem; font-weight: 600; }
.score-home { color: #00d4ff; }
.score-dash  { color: #8b949e; margin: 0 0.4rem; }
.score-away { color: #ff6b6b; }
.competition-badge {
    display: inline-block;
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-size: 0.8rem;
    color: #8b949e;
    margin-top: 0.5rem;
    font-family: 'JetBrains Mono', monospace;
}

/* Stat pills */
.stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.4rem 0;
    border-bottom: 1px solid #21262d;
}
.stat-val-home { color: #00d4ff; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
.stat-val-away { color: #ff6b6b; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
.stat-name { color: #8b949e; font-size: 0.85rem; }

/* Player card */
.player-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    cursor: pointer;
    transition: border-color 0.2s;
}
.player-card:hover { border-color: #30363d; }
.player-card.selected { border-color: #00d4ff; background: #1c2a3a; }

.player-name { font-weight: 600; font-size: 0.95rem; }
.player-pos { color: #8b949e; font-size: 0.78rem; font-family: 'JetBrains Mono', monospace; }
.player-rating {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 1.1rem;
}
.rating-high { color: #3fb950; }
.rating-mid  { color: #f5c518; }
.rating-low  { color: #ff6b6b; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #161b22;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 8px;
    color: #8b949e;
    font-weight: 600;
    padding: 6px 16px;
}
.stTabs [aria-selected="true"] {
    background: #21262d !important;
    color: #e6edf3 !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #00d4ff22, #00d4ff11);
    border: 1px solid #00d4ff44;
    color: #00d4ff;
    border-radius: 8px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    padding: 0.5rem 1.5rem;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: #00d4ff22;
    border-color: #00d4ff;
}

/* Text input */
.stTextInput > div > div > input {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    color: #e6edf3;
    font-family: 'JetBrains Mono', monospace;
    font-size: 1rem;
    padding: 0.5rem 1rem;
}

/* Section headers */
.section-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 700;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin: 1.5rem 0 0.8rem 0;
    border-bottom: 1px solid #21262d;
    padding-bottom: 0.4rem;
}

/* Metric boxes */
.metric-box {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    text-align: center;
}
.metric-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
}
.metric-lbl { color: #8b949e; font-size: 0.75rem; margin-top: 2px; }

/* Divider */
hr { border-color: #21262d; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)


# ─── SESSION STATE ────────────────────────────────────────────────────────────
for key in ["client", "match_data", "match_id_loaded"]:
    if key not in st.session_state:
        st.session_state[key] = None


# ─── HELPERS ──────────────────────────────────────────────────────────────────
def rating_class(r):
    if r is None:
        return "rating-mid"
    r = float(r)
    if r >= 7.5:
        return "rating-high"
    if r >= 6.0:
        return "rating-mid"
    return "rating-low"


def get_or_create_client():
    if st.session_state.client is None:
        with st.spinner("🌐 Iniciando Chrome… (solo la primera vez, ~5s)"):
            st.session_state.client = SofascoreClient()
    return st.session_state.client


@st.cache_data(ttl=300, show_spinner=False)
def load_match(match_id: int):
    client = get_or_create_client()
    raw_match     = client.get_match(match_id)
    raw_stats     = client.get_statistics(match_id)
    raw_lineups   = client.get_lineups(match_id)
    raw_incidents = client.get_incidents(match_id)
    raw_shotmap   = client.get_shotmap(match_id)

    if not raw_match or "event" not in raw_match:
        return None

    event      = raw_match["event"]
    home_team  = event["homeTeam"]["name"]
    away_team  = event["awayTeam"]["name"]
    home_score = event.get("homeScore", {}).get("current", "?")
    away_score = event.get("awayScore", {}).get("current", "?")
    competition= event.get("tournament", {}).get("name", "")
    status     = event.get("status", {}).get("description", "")

    df_stats     = parse_statistics(raw_stats, home_team, away_team)
    df_incidents = parse_incidents(raw_incidents, home_team, away_team)
    df_players   = parse_lineups(raw_lineups, home_team, away_team)
    df_shots     = parse_shotmap(raw_shotmap, home_team, away_team)

    return dict(
        home_team=home_team, away_team=away_team,
        home_score=home_score, away_score=away_score,
        competition=competition, status=status,
        df_stats=df_stats, df_incidents=df_incidents,
        df_players=df_players, df_shots=df_shots,
        match_id=match_id,
    )


def get_heatmap(match_id, player_id):
    client = get_or_create_client()
    return client.get_heatmap(match_id, player_id)


# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:1.5rem">
  <span style="font-size:2rem">⚽</span>
  <span style="font-family:'JetBrains Mono',monospace;font-size:1.4rem;
               font-weight:700;color:#e6edf3;letter-spacing:0.05em">
    SOFASCORE ANALYZER
  </span>
  <span style="font-size:0.75rem;color:#8b949e;margin-left:4px;
               font-family:'JetBrains Mono',monospace">v2.0</span>
</div>
""", unsafe_allow_html=True)

# ─── MATCH LOADER ─────────────────────────────────────────────────────────────
with st.container():
    col_input, col_btn, col_spacer = st.columns([3, 1, 4])
    with col_input:
        match_id_input = st.text_input(
            "ID del partido",
            placeholder="Ej: 14083567",
            label_visibility="collapsed",
        )
    with col_btn:
        load_btn = st.button("⚡ Cargar", use_container_width=True)

if load_btn and match_id_input:
    try:
        mid = int(match_id_input.strip())
        with st.spinner("📡 Cargando datos del partido…"):
            data = load_match(mid)
        if data is None:
            st.error("❌ No se encontró el partido. Verifica el ID.")
            st.stop()
        st.session_state.match_data = data
        st.session_state.match_id_loaded = mid
    except ValueError:
        st.error("❌ El ID debe ser un número entero.")
        st.stop()

# ─── MAIN CONTENT ─────────────────────────────────────────────────────────────
if st.session_state.match_data is None:
    st.markdown("""
    <div style="text-align:center;padding:4rem 2rem;color:#8b949e">
        <div style="font-size:3rem;margin-bottom:1rem">⚽</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:1rem;
                    letter-spacing:0.1em;text-transform:uppercase">
            Introduce un ID de partido para comenzar
        </div>
        <div style="font-size:0.85rem;margin-top:0.5rem">
            Encuéntralo en la URL de Sofascore al final: <code style="color:#00d4ff">#id:XXXXXXXX</code>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

d = st.session_state.match_data
home_team  = d["home_team"]
away_team  = d["away_team"]
home_score = d["home_score"]
away_score = d["away_score"]
df_stats   = d["df_stats"]
df_players = d["df_players"]
df_shots   = d["df_shots"]
df_incidents = d["df_incidents"]
match_id   = d["match_id"]

# ─── SCORE CARD ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="score-card">
    <div style="display:flex;justify-content:center;align-items:center;gap:2rem">
        <span class="team-name-home">{home_team}</span>
        <span class="score-main">
            <span class="score-home">{home_score}</span>
            <span class="score-dash">–</span>
            <span class="score-away">{away_score}</span>
        </span>
        <span class="team-name-away">{away_team}</span>
    </div>
    <div class="competition-badge">{d['competition']}  ·  {d['status']}</div>
</div>
""", unsafe_allow_html=True)

# ─── MAIN TABS ────────────────────────────────────────────────────────────────
tab_resumen, tab_timeline, tab_shots, tab_players, tab_compare = st.tabs([
    "📊 Resumen", "⚡ Timeline", "🎯 Tiros", "👤 Jugadores", "⚖️ Comparador"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — RESUMEN
# ══════════════════════════════════════════════════════════════════════════════
with tab_resumen:
    if df_stats.empty:
        st.info("Estadísticas no disponibles para este partido.")
    else:
        col_chart, col_metrics = st.columns([3, 2])
        with col_chart:
            st.markdown('<div class="section-title">Estadísticas comparativas</div>',
                        unsafe_allow_html=True)
            fig = plot_match_stats(df_stats, home_team, away_team)
            st.pyplot(fig, use_container_width=True)

        with col_metrics:
            st.markdown('<div class="section-title">Métricas clave</div>',
                        unsafe_allow_html=True)
            df_all = df_stats[df_stats["period"] == "ALL"]
            key_metrics = {
                "Ball possession": "Posesión %",
                "Total shots": "Tiros totales",
                "Shots on target": "Tiros a puerta",
                "Passes": "Pases",
                "Corner kicks": "Córners",
                "Yellow cards": "Tarjetas amarillas",
            }
            for stat_key, label in key_metrics.items():
                row = df_all[df_all["stat"] == stat_key]
                if row.empty:
                    continue
                hv = row.iloc[0].get(home_team, "—")
                av = row.iloc[0].get(away_team, "—")
                st.markdown(f"""
                <div class="stat-row">
                    <span class="stat-val-home">{hv}</span>
                    <span class="stat-name">{label}</span>
                    <span class="stat-val-away">{av}</span>
                </div>
                """, unsafe_allow_html=True)

            # quick player ratings
            st.markdown('<div class="section-title" style="margin-top:1.5rem">Mejores ratings</div>',
                        unsafe_allow_html=True)
            if not df_players.empty:
                top = (df_players[df_players["rating"].notna()]
                       .nlargest(6, "rating")[["player_name", "team", "position", "rating"]])
                for _, row in top.iterrows():
                    r = float(row["rating"])
                    cls = rating_class(r)
                    color = "#00d4ff" if row["team"] == home_team else "#ff6b6b"
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;
                                align-items:center;padding:0.3rem 0;
                                border-bottom:1px solid #21262d">
                        <span style="font-size:0.9rem">{row['player_name']}</span>
                        <span style="font-size:0.75rem;color:{color};
                                     font-family:'JetBrains Mono',monospace">
                            {row['position']}
                        </span>
                        <span class="player-rating {cls}">{r:.2f}</span>
                    </div>
                    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TIMELINE
# ══════════════════════════════════════════════════════════════════════════════
with tab_timeline:
    if df_incidents.empty:
        st.info("Eventos no disponibles para este partido.")
    else:
        fig = plot_timeline(df_incidents, home_team, away_team, home_score, away_score)
        st.pyplot(fig, use_container_width=True)

        st.markdown('<div class="section-title">Todos los eventos</div>',
                    unsafe_allow_html=True)
        event_icons = {
            "goal": "⚽", "card": "🟨", "substitution": "🔄",
            "varDecision": "📺", "penaltyMissed": "❌",
        }
        if not df_incidents.empty:
            for _, row in df_incidents.iterrows():
                if pd.isna(row["minute"]):
                    continue
                icon = event_icons.get(row["type"], "•")
                color = "#00d4ff" if row.get("is_home") else "#ff6b6b"
                player = row.get("player", "") or ""
                detail = row.get("detail", "") or ""
                sub_info = ""
                if row["type"] == "substitution" and row.get("player_in"):
                    sub_info = f" ↑{row['player_in']} ↓{row['player_out']}"
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:1rem;
                            padding:0.35rem 0;border-bottom:1px solid #21262d">
                    <span style="font-family:'JetBrains Mono',monospace;
                                 color:{color};font-weight:700;min-width:38px">
                        {int(row['minute'])}'
                    </span>
                    <span>{icon}</span>
                    <span style="color:{color};font-weight:600">{row['team']}</span>
                    <span style="color:#e6edf3">{player}{sub_info}</span>
                    <span style="color:#8b949e;font-size:0.8rem">{detail}</span>
                </div>
                """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — TIROS
# ══════════════════════════════════════════════════════════════════════════════
with tab_shots:
    if df_shots.empty:
        st.info("Mapa de tiros no disponible para este partido.")
    else:
        fig = plot_shotmap(df_shots, home_team, away_team)
        if fig:
            st.pyplot(fig, use_container_width=True)

        st.markdown('<div class="section-title">Detalle de tiros</div>',
                    unsafe_allow_html=True)
        col_h, col_a = st.columns(2)
        for col, team, flag in [(col_h, home_team, True), (col_a, away_team, False)]:
            with col:
                color = "#00d4ff" if flag else "#ff6b6b"
                ts = df_shots[df_shots["is_home"] == flag]
                st.markdown(f"<span style='color:{color};font-weight:700'>{team}</span>",
                             unsafe_allow_html=True)
                if not ts.empty:
                    for _, s in ts.sort_values("minute").iterrows():
                        icon = "⭐" if s["is_goal"] else "○"
                        xg_val = f"{float(s['xg']):.2f}" if pd.notna(s.get("xg")) else "—"
                        xgot_val = f"{float(s['xgot']):.2f}" if pd.notna(s.get("xgot")) else "—"
                        xgot_str = f" · xGoT {xgot_val}" if xgot_val != "—" else ""
                        body = s.get("body_part", "") or ""
                        body_icon = "🦶" if "foot" in body.lower() else ("🤛" if "head" in body.lower() else "")
                        st.markdown(f"""
                        <div style="display:flex;gap:0.8rem;padding:0.3rem 0;
                                    border-bottom:1px solid #21262d;font-size:0.85rem;
                                    align-items:center">
                            <span style="font-family:'JetBrains Mono',monospace;
                                         color:{color};font-weight:700;min-width:32px">{int(s['minute'])}'</span>
                            <span>{icon}</span>
                            <span>{body_icon}</span>
                            <span style="flex:1">{s['player_name']}</span>
                            <span style="color:#8b949e;font-family:'JetBrains Mono',monospace;font-size:0.8rem">
                                xG {xg_val}{xgot_str}
                            </span>
                        </div>
                        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — JUGADORES
# ══════════════════════════════════════════════════════════════════════════════
with tab_players:
    if df_players.empty:
        st.info("Datos de jugadores no disponibles.")
    else:
        home_players = df_players[df_players["side"] == "home"].sort_values(
            "is_starter", ascending=False)
        away_players = df_players[df_players["side"] == "away"].sort_values(
            "is_starter", ascending=False)

        team_tab_home, team_tab_away = st.tabs([
            f"🔵 {home_team}", f"🔴 {away_team}"
        ])

        def render_player_tab(players_df, team_color):
            starters = players_df[players_df["is_starter"]]
            subs = players_df[~players_df["is_starter"]]

            col_list, col_detail = st.columns([1, 2])

            with col_list:
                st.markdown('<div class="section-title">Titulares</div>',
                            unsafe_allow_html=True)
                selected_id = st.session_state.get(f"sel_{team_color}", None)

                for _, p in starters.iterrows():
                    r = p.get("rating")
                    r_str = f"{float(r):.1f}" if r else "—"
                    r_cls = rating_class(r)
                    if st.button(
                        f"#{p['jersey_number'] or '—'}  {p['player_name']}  ·  {p['position']}",
                        key=f"btn_{p['player_id']}",
                        use_container_width=True,
                    ):
                        st.session_state[f"sel_{team_color}"] = p["player_id"]
                        st.rerun()

                st.markdown('<div class="section-title">Suplentes</div>',
                            unsafe_allow_html=True)
                for _, p in subs.iterrows():
                    if st.button(
                        f"#{p['jersey_number'] or '—'}  {p['player_name']}  ·  {p['position']}",
                        key=f"btn_{p['player_id']}",
                        use_container_width=True,
                    ):
                        st.session_state[f"sel_{team_color}"] = p["player_id"]
                        st.rerun()

            with col_detail:
                pid = st.session_state.get(f"sel_{team_color}")
                if pid is None:
                    st.markdown("""
                    <div style="text-align:center;padding:3rem;color:#8b949e">
                        ← Selecciona un jugador para ver su análisis
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    prow = players_df[players_df["player_id"] == pid]
                    if prow.empty:
                        st.info("Jugador no encontrado.")
                    else:
                        p = prow.iloc[0].to_dict()
                        name = p.get("player_name", "")
                        rating = p.get("rating")

                        # Quick stats strip
                        r_str = f"{float(rating):.2f}" if rating else "—"
                        mins = p.get("minutes_played") or "—"
                        st.markdown(f"""
                        <div style="display:flex;gap:1rem;margin-bottom:1rem;flex-wrap:wrap">
                            <div class="metric-box">
                                <div class="metric-val {rating_class(rating)}">{r_str}</div>
                                <div class="metric-lbl">Rating</div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-val">{mins}'</div>
                                <div class="metric-lbl">Minutos</div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-val">{int(p.get('goals') or 0)}</div>
                                <div class="metric-lbl">Goles</div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-val">{int(p.get('assists') or 0)}</div>
                                <div class="metric-lbl">Asistencias</div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-val">{p.get('pass_accuracy') or 0}%</div>
                                <div class="metric-lbl">% Pase</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Expandable charts
                        with st.expander("📊 Estadísticas detalladas", expanded=True):
                            c1, c2 = st.columns(2)
                            with c1:
                                fig = plot_player_radar(p)
                                st.pyplot(fig, use_container_width=True)
                            with c2:
                                fig2 = plot_player_bars(p)
                                if fig2:
                                    st.pyplot(fig2, use_container_width=True)

                        with st.expander("🔥 Mapa de calor"):
                            with st.spinner("Cargando heatmap…"):
                                hm = get_heatmap(match_id, pid)
                            fig3 = plot_player_heatmap(hm, name, side=p.get("side", "home"))
                            st.pyplot(fig3, use_container_width=True)

                        with st.expander("🎯 Mapa de tiros"):
                            fig4 = plot_player_shots(df_shots, pid, name, p.get("side", "home"))
                            st.pyplot(fig4, use_container_width=True)

                        # Full stats table
                        with st.expander("🗃️ Tabla completa (ML-ready)"):
                            ml_cols = [
                                "player_name", "team", "position", "is_starter",
                                "minutes_played", "rating", "goals", "assists",
                                "xg", "xa", "shots_on_target", "shots_off_target",
                                "passes_total", "passes_accurate", "pass_accuracy",
                                "key_passes", "tackles", "interceptions", "clearances",
                                "duels_won", "duels_lost", "duel_win_rate",
                                "dribbles_won", "dribbles_lost",
                                "aerial_won", "aerial_lost",
                                "yellow_cards", "red_cards",
                                "fouls_committed", "fouls_won",
                                "saves", "goals_conceded",
                            ]
                            cols = [c for c in ml_cols if c in prow.columns]
                            # FIX: convert all to string to avoid Arrow bool/type errors
                            tbl = prow[cols].T.rename(columns={prow.index[0]: "Valor"})
                            tbl["Valor"] = tbl["Valor"].astype(str)
                            st.dataframe(tbl, use_container_width=True)

        with team_tab_home:
            render_player_tab(home_players, "home")
        with team_tab_away:
            render_player_tab(away_players, "away")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — COMPARADOR
# ══════════════════════════════════════════════════════════════════════════════
with tab_compare:
    if df_players.empty:
        st.info("Datos de jugadores no disponibles.")
    else:
        player_options = {
            f"[{r['team']}] {r['player_name']} ({r['position']})": r.to_dict()
            for _, r in df_players.iterrows()
        }
        names = list(player_options.keys())

        col1, col2 = st.columns(2)
        with col1:
            p1_name = st.selectbox("Jugador 1", names, key="cmp_p1")
        with col2:
            p2_name = st.selectbox("Jugador 2", names,
                                   index=min(1, len(names) - 1), key="cmp_p2")

        p1 = player_options[p1_name]
        p2 = player_options[p2_name]

        c_radar, c_stats = st.columns([3, 2])
        with c_radar:
            fig = plot_compare_radar(p1, p2)
            st.pyplot(fig, use_container_width=True)

        with c_stats:
            st.markdown('<div class="section-title">Estadísticas frente a frente</div>',
                        unsafe_allow_html=True)
            compare_cols = [
                ("Rating", "rating"),
                ("Minutos", "minutes_played"),
                ("Goles", "goals"),
                ("Asistencias", "assists"),
                ("xG", "xg"),
                ("Pases prec.", "passes_accurate"),
                ("% Pase", "pass_accuracy"),
                ("Pases clave", "key_passes"),
                ("Tiros a puerta", "shots_on_target"),
                ("Regates gan.", "dribbles_won"),
                ("Tackles", "tackles"),
                ("Intercepciones", "interceptions"),
                ("Duelos gan.", "duels_won"),
                ("% Duelos", "duel_win_rate"),
            ]
            for label, col in compare_cols:
                v1 = p1.get(col, 0) or 0
                v2 = p2.get(col, 0) or 0
                try:
                    v1f, v2f = float(v1), float(v2)
                    c1_bold = "font-weight:700" if v1f >= v2f else "opacity:0.6"
                    c2_bold = "font-weight:700" if v2f >= v1f else "opacity:0.6"
                    v1_str = f"{v1f:.2f}" if isinstance(v1, float) and v1 != int(v1) else str(int(v1f))
                    v2_str = f"{v2f:.2f}" if isinstance(v2, float) and v2 != int(v2) else str(int(v2f))
                except Exception:
                    c1_bold = c2_bold = ""
                    v1_str, v2_str = str(v1), str(v2)

                st.markdown(f"""
                <div class="stat-row">
                    <span style="color:#00d4ff;{c1_bold};font-family:'JetBrains Mono',monospace">
                        {v1_str}
                    </span>
                    <span class="stat-name">{label}</span>
                    <span style="color:#ff6b6b;{c2_bold};font-family:'JetBrains Mono',monospace">
                        {v2_str}
                    </span>
                </div>
                """, unsafe_allow_html=True)

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:2rem 0 0.5rem;color:#8b949e;
            font-family:'JetBrains Mono',monospace;font-size:0.72rem;
            letter-spacing:0.08em;border-top:1px solid #21262d;margin-top:2rem">
    SOFASCORE ANALYZER  ·  DATOS VÍA API PÚBLICA  ·  USO PERSONAL
</div>
""", unsafe_allow_html=True)
