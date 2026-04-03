import plotly.graph_objects as go
import pandas as pd
import re

def plot_mirror_bar_chart(df, home_team, away_team):
    # Filtrar filas sin datos
    df_clean = df[df[home_team] != "Dato no disponible"].copy()
    if df_clean.empty:
        return None

    # Función segura para extraer solo los números de cualquier texto
    def extract_number(val):
        if pd.isna(val): return 0.0
        val_str = str(val).replace(',', '')
        match = re.search(r"[-+]?\d*\.\d+|\d+", val_str)
        return float(match.group()) if match else 0.0

    # Calcular valores numéricos absolutos
    home_abs = df_clean[home_team].apply(extract_number)
    away_abs = df_clean[away_team].apply(extract_number)
    totals = home_abs + away_abs

    # Calcular proporciones (0 a 100) para las barras
    home_props, away_props = [], []
    for h, a, t in zip(home_abs, away_abs, totals):
        if t == 0:
            home_props.append(0)
            away_props.append(0)
        else:
            home_props.append((h / t) * 100 * -1) # Negativo para invertir barra local
            away_props.append((a / t) * 100)

    stats_names = df_clean['stat']

    # Formatear los textos que se mostrarán en la gráfica (Ej: %, decimales o enteros)
    home_texts, away_texts = [], []
    for _, row in df_clean.iterrows():
        stat_name = str(row['stat']).lower()
        h_val = extract_number(row[home_team])
        a_val = extract_number(row[away_team])

        if "possession" in stat_name:
            home_texts.append(f"{int(h_val)}%")
            away_texts.append(f"{int(a_val)}%")
        elif "xg" in stat_name:
            home_texts.append(f"{h_val:.2f}")
            away_texts.append(f"{a_val:.2f}")
        elif "distance" in stat_name:
            home_texts.append(f"{h_val:.1f}")
            away_texts.append(f"{a_val:.1f}")
        else:
            home_texts.append(f"{int(h_val)}")
            away_texts.append(f"{int(a_val)}")

    fig = go.Figure()

    # Barra Local
    fig.add_trace(go.Bar(
        y=stats_names, x=home_props, name=home_team, orientation='h',
        marker=dict(color='#00d4ff'),
        text=home_texts, textposition='outside', hoverinfo='text',
        hovertext=[f"{home_team}: {t}" for t in home_texts]
    ))

    # Barra Visitante
    fig.add_trace(go.Bar(
        y=stats_names, x=away_props, name=away_team, orientation='h',
        marker=dict(color='#ff6b6b'),
        text=away_texts, textposition='outside', hoverinfo='text',
        hovertext=[f"{away_team}: {t}" for t in away_texts]
    ))

    fig.update_layout(
        barmode='relative', title="Comparativa", title_x=0.5,
        plot_bgcolor='#0d1117', paper_bgcolor='#0d1117', font=dict(color='#e6edf3'),
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=True, zerolinecolor='#30363d', range=[-115, 115]),
        yaxis=dict(showgrid=False, tickmode='linear'),
        margin=dict(l=150, r=20, t=50, b=20), height=600, showlegend=False,
        dragmode=False  # Bloquea movimiento y zoom
    )

    return fig