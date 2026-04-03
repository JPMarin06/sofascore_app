import os
import signal
import datetime
import streamlit as st
import pandas as pd

from sofascore_client import SofascoreClient
from data_parser import parse_statistics
from charts import plot_mirror_bar_chart

st.set_page_config(page_title="Anelysis Football App", page_icon="⚽", layout="wide")

# ─── INICIALIZACIÓN DE ESTADOS ────────────────────────────────────────────────
if "client" not in st.session_state: st.session_state.client = SofascoreClient()
if "view" not in st.session_state: st.session_state.view = "search"
if "team_events" not in st.session_state: st.session_state.team_events = []
if "display_limit" not in st.session_state: st.session_state.display_limit = 10
if "current_api_page" not in st.session_state: st.session_state.current_api_page = 0

# ─── SIDEBAR: BOTONES DE CONTROL ─────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Sistema")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🧹 Liberar Memoria", width="stretch"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.session_state.team_events = []
            st.session_state.view = "search"
            st.toast("✅ Caché y memoria limpias.")
    with c2:
        if st.button("🛑 Cerrar App", type="primary", width="stretch"):
            st.session_state.client.quit()
            st.warning("Cerrando procesos...")
            os.kill(os.getpid(), signal.SIGINT)

    st.divider()
    st.markdown("### 🔍 Buscar Equipo")
    query = st.text_input("Ej: Barcelona...")

    if st.button("Buscar", width="stretch") and query:
        with st.spinner("Buscando..."):
            st.session_state.search_results = st.session_state.client.search(query)
            st.session_state.team_events = []
            st.session_state.current_api_page = 0
            st.session_state.display_limit = 10
            st.session_state.view = "search"

# ─── VISTA 1: BUSCADOR Y PARTIDOS PAGINADOS ──────────────────────────────────
if st.session_state.view == "search":
    st.title("⚽ Resultados de Búsqueda")
    
    if "search_results" in st.session_state and st.session_state.search_results:
        for team in st.session_state.search_results:
            eid = team["entity"]["id"]
            ename = team["entity"]["name"]
            ecountry = team["entity"].get("country", {}).get("name", "")
            logo_url = st.session_state.client.get_logo_url("team", eid)

            col_img, col_text, col_btn = st.columns([0.5, 4, 1.5])
            with col_img: st.image(logo_url, width=40)
            with col_text: st.markdown(f"**{ename}** <br> <small>{ecountry}</small>", unsafe_allow_html=True)
            with col_btn:
                if st.button("Ver Partidos", key=f"t_{eid}", width="stretch"):
                    st.session_state.selected_team = eid
                    st.session_state.current_api_page = 0
                    st.session_state.display_limit = 10
                    data = st.session_state.client.get_team_events_paginated(eid, 0)
                    events = sorted(data.get("events", []), key=lambda x: x.get("startTimestamp", 0), reverse=True)
                    st.session_state.team_events = events
                    st.rerun()
            st.markdown("---")

    if st.session_state.team_events:
        st.subheader("🏟️ Partidos")
        visible_events = st.session_state.team_events[:st.session_state.display_limit]
        
        for ev in visible_events:
            ts = ev.get('startTimestamp', 0)
            date_str = datetime.datetime.fromtimestamp(ts).strftime('%d/%m/%Y')
            h_team, a_team = ev['homeTeam']['name'], ev['awayTeam']['name']
            
            status = ev.get("status", {}).get("type", "unknown")
            if status == "notstarted":
                score_txt = "(Por comenzar)"
            elif status in ["postponed", "canceled"]:
                score_txt = "(Pospuesto/Cancelado)"
            else:
                h_score = ev.get('homeScore', {}).get('display', '-')
                a_score = ev.get('awayScore', {}).get('display', '-')
                score_txt = f"{h_score} - {a_score}"

            with st.expander(f"📅 {date_str} | {h_team} {score_txt} {a_team}"):
                if st.button("🚀 Analizar Partido", key=f"an_{ev['id']}", width="stretch"):
                    st.session_state.active_match_id = ev['id']
                    st.session_state.view = "analysis"
                    st.rerun()
        
        if st.button("➕ Cargar 10 más", width="stretch"):
            st.session_state.display_limit += 10
            if st.session_state.display_limit > len(st.session_state.team_events):
                with st.spinner("Descargando historial antiguo..."):
                    st.session_state.current_api_page += 1
                    more = st.session_state.client.get_team_events_paginated(
                        st.session_state.selected_team, 
                        st.session_state.current_api_page
                    )
                    new_events = sorted(more.get("events", []), key=lambda x: x.get("startTimestamp", 0), reverse=True)
                    st.session_state.team_events.extend(new_events)
            st.rerun()

# ─── VISTA 2: ANÁLISIS DEL PARTIDO ───────────────────────────────────────────
elif st.session_state.view == "analysis":
    if st.button("⬅️ Volver al Buscador", type="primary"):
        st.session_state.view = "search"
        st.rerun()

    mid = st.session_state.active_match_id
    with st.spinner("Procesando análisis..."):
        match_raw = st.session_state.client.get_match(mid)
        stats_raw = st.session_state.client.get_statistics(mid)
        
    ev = match_raw.get("event", {})
    home = ev.get("homeTeam", {}).get("name", "Local")
    away = ev.get("awayTeam", {}).get("name", "Visitante")
    status_type = ev.get("status", {}).get("type", "")

    # ─── EXTRACCIÓN SEGURA DEL MARCADOR ───
    h_score_data = ev.get("homeScore", {})
    a_score_data = ev.get("awayScore", {})
    
    h_val = h_score_data.get("display") if h_score_data.get("display") is not None else h_score_data.get("current", "")
    a_val = a_score_data.get("display") if a_score_data.get("display") is not None else a_score_data.get("current", "")
    
    h_score_str = str(h_val).strip()
    a_score_str = str(a_val).strip()
    
    if h_score_str != "" and a_score_str != "":
        title_text = f"{home} <span style='color:#f5c518;'>{h_score_str} - {a_score_str}</span> {away}"
    else:
        title_text = f"{home} vs {away}"

    st.markdown(f"<h1 style='text-align: center;'>{title_text}</h1>", unsafe_allow_html=True)
    
    if status_type == "notstarted":
        st.warning("⏳ Partido pendiente por comenzar. No hay estadísticas disponibles aún.")
    elif status_type in ["postponed", "canceled"]:
        st.error("🛑 Este partido ha sido pospuesto o cancelado.")
    else:
        if status_type == "inprogress":
            st.info("🟢 Partido en curso. Mostrando estadísticas en vivo.")
            
        df_stats = parse_statistics(stats_raw, home, away)
        
        if df_stats.empty:
            st.warning("⚠️ Estadísticas no disponibles para este partido.")
        else:
            tabs = st.tabs(["📊 Estadísticas Generales", "📄 Datos Crudos"])
            
            with tabs[0]:
                fig_mirror = plot_mirror_bar_chart(df_stats, home, away)
                if fig_mirror:
                    st.plotly_chart(fig_mirror, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.error("❌ Gráfico no disponible: Datos insuficientes para este partido.")
                    
            with tabs[1]:
                st.markdown("### Resumen Tabular")
                st.dataframe(df_stats, use_container_width=True, hide_index=True)