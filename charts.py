import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.patches import FancyArrowPatch
from mplsoccer import Pitch, VerticalPitch

COLORS = {
    "home": "#00d4ff",
    "away": "#ff6b6b",
    "accent": "#f5c518",
    "bg": "#0d1117",
    "card": "#161b22",
    "surface": "#21262d",
    "text": "#e6edf3",
    "muted": "#8b949e",
    "green": "#3fb950",
    "goal": "#ffd700",
}

plt.rcParams.update({
    "font.family": "monospace",
    "text.color": COLORS["text"],
    "axes.labelcolor": COLORS["muted"],
    "xtick.color": COLORS["muted"],
    "ytick.color": COLORS["muted"],
})

# ─── SOFASCORE COORD CONVERSION ───────────────────────────────────────────────
# Sofascore: x=0-100 (left→right), y=0-100 (top→bottom)
# Statsbomb: x=0-120 (left→right), y=0-80 (top→bottom)
def _ss_to_sb(x, y):
    """Convert Sofascore 0-100 coords to Statsbomb 0-120/0-80."""
    sx = float(x) * 1.2 if pd.notna(x) else 60.0
    sy = float(y) * 0.8 if pd.notna(y) else 40.0
    return sx, sy


# ─── MATCH STATS BAR CHART ────────────────────────────────────────────────────
def plot_match_stats(df_stats, home_team, away_team):
    df = df_stats[df_stats["period"] == "ALL"].copy()
    df["hv"] = pd.to_numeric(df["home_value"], errors="coerce").fillna(0)
    df["av"] = pd.to_numeric(df["away_value"], errors="coerce").fillna(0)
    df = df[df["hv"] + df["av"] > 0]

    key = ["Ball possession", "Total shots", "Shots on target", "Passes",
           "Accurate passes", "Tackles", "Corner kicks", "Yellow cards",
           "Fouls", "Offsides", "Big chances", "Clearances"]
    df_p = df[df["stat"].isin(key)]
    if df_p.empty:
        df_p = df.head(12)

    n = len(df_p)
    fig, ax = plt.subplots(figsize=(10, max(4, n * 0.7)), facecolor=COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])

    for i, (_, row) in enumerate(df_p.iterrows()):
        tot = row["hv"] + row["av"]
        if tot == 0:
            continue
        hp = row["hv"] / tot
        ap = row["av"] / tot
        ax.barh(i, -1.0, color=COLORS["surface"], height=0.55, alpha=0.4)
        ax.barh(i,  1.0, color=COLORS["surface"], height=0.55, alpha=0.4)
        ax.barh(i, -hp, color=COLORS["home"], height=0.55, alpha=0.9)
        ax.barh(i,  ap, color=COLORS["away"], height=0.55, alpha=0.9)
        fmt = lambda v: int(v) if v == int(v) else round(v, 1)
        ax.text(-0.03, i, str(fmt(row["hv"])), ha="right", va="center",
                color="white", fontsize=10, fontweight="bold")
        ax.text(0.03, i, str(fmt(row["av"])), ha="left", va="center",
                color="white", fontsize=10, fontweight="bold")
        ax.text(0, i, row["stat"], ha="center", va="center",
                color=COLORS["muted"], fontsize=8,
                bbox=dict(boxstyle="round,pad=0.3", facecolor=COLORS["bg"], alpha=0.95, linewidth=0))

    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-0.8, n - 0.2)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.spines[:].set_visible(False)
    ax.axvline(0, color=COLORS["surface"], linewidth=1)
    fig.text(0.22, 0.97, home_team, ha="center", va="top",
             color=COLORS["home"], fontsize=12, fontweight="bold")
    fig.text(0.78, 0.97, away_team, ha="center", va="top",
             color=COLORS["away"], fontsize=12, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    return fig


# ─── TIMELINE ─────────────────────────────────────────────────────────────────
def plot_timeline(df_incidents, home_team, away_team, home_score, away_score):
    fig, ax = plt.subplots(figsize=(14, 7), facecolor=COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])

    ax.axhspan(-0.08, 0.08, color="#1a3a1a", alpha=0.6, zorder=0)
    ax.axhline(0, color="#2ea043", linewidth=2.5, zorder=1)

    for minute, label in [(45, "45'"), (90, "90'")]:
        ax.axvline(minute, color=COLORS["surface"], linewidth=1.5,
                   linestyle="--", alpha=0.7, zorder=2)
        ax.text(minute, -0.72, label, ha="center", color=COLORS["muted"],
                fontsize=8, fontweight="bold")

    ax.text(-3, 0.45, home_team, color=COLORS["home"], fontsize=11,
            fontweight="bold", ha="left", va="center")
    ax.text(-3, -0.45, away_team, color=COLORS["away"], fontsize=11,
            fontweight="bold", ha="left", va="center")

    EVENT_STYLE = {
        "goal":          {"marker": "★", "color": COLORS["goal"],  "size": 220},
        "card":          {"marker": "■", "color": "#ffcc00",        "size": 130},
        "substitution":  {"marker": "⇄", "color": COLORS["muted"], "size": 100},
        "varDecision":   {"marker": "◈", "color": "#a78bfa",       "size": 110},
        "penaltyMissed": {"marker": "✕", "color": COLORS["away"],  "size": 130},
    }

    offsets = {}
    for _, row in df_incidents.iterrows():
        if pd.isna(row["minute"]):
            continue
        inc_type = row["type"]
        style = EVENT_STYLE.get(inc_type, {"marker": "•", "color": COLORS["muted"], "size": 60})
        minute = float(row["minute"])
        is_home = row.get("is_home", True)
        y_dir = 1 if is_home else -1
        y_base = 0.22 * y_dir
        key = (round(minute), is_home)
        off = offsets.get(key, 0)
        offsets[key] = off + 0.22
        y = y_base + off * y_dir

        ax.plot([minute, minute], [0, y], color=style["color"],
                linewidth=1, alpha=0.4, zorder=2)
        ax.scatter(minute, y, s=style["size"], color=style["color"],
                   zorder=5, alpha=0.95, marker="o",
                   edgecolors="white", linewidths=0.5)
        ax.text(minute, y, style["marker"], ha="center", va="center",
                fontsize=7, color="white", fontweight="bold", zorder=6)

        player = row.get("player", "") or ""
        player_in = row.get("player_in", "") or ""
        player_out = row.get("player_out", "") or ""

        if inc_type == "substitution":
            # FIX: show "out ↓ / in ↑" without repeating player
            if player_in and player_out:
                label_txt = f"↑{player_in.split()[-1]}\n↓{player_out.split()[-1]}"
            elif player_in:
                label_txt = f"↑{player_in.split()[-1]}"
            elif player_out:
                label_txt = f"↓{player_out.split()[-1]}"
            else:
                label_txt = ""
            if label_txt:
                label_y = y + 0.18 * y_dir
                ax.text(minute, label_y, label_txt,
                        ha="center", fontsize=6, color=style["color"],
                        bbox=dict(boxstyle="round,pad=0.2", facecolor=COLORS["bg"],
                                  edgecolor=style["color"], linewidth=0.7, alpha=0.9),
                        zorder=7)

        elif player and inc_type in ["goal", "card", "penaltyMissed"]:
            name_short = player.split()[-1]
            label_y = y + 0.18 * y_dir
            ax.text(minute, label_y, f"{name_short}\n{int(minute)}'",
                    ha="center", fontsize=6.5, color=style["color"], fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.25", facecolor=COLORS["bg"],
                              edgecolor=style["color"], linewidth=0.8, alpha=0.9),
                    zorder=7)

    ax.set_xlim(-8, 97)
    ax.set_ylim(-1.35, 1.35)
    ax.set_xticks([0, 15, 30, 45, 60, 75, 90])
    ax.set_xticklabels(["0'", "15'", "30'", "45'", "60'", "75'", "90'"],
                       color=COLORS["muted"], fontsize=9)
    ax.set_yticks([])
    ax.spines[:].set_visible(False)
    legend_items = [
        mpatches.Patch(color=COLORS["goal"], label="Gol ★"),
        mpatches.Patch(color="#ffcc00", label="Tarjeta ■"),
        mpatches.Patch(color=COLORS["muted"], label="Sustitución ⇄"),
        mpatches.Patch(color="#a78bfa", label="VAR ◈"),
    ]
    ax.legend(handles=legend_items, loc="upper right", fontsize=8,
              facecolor=COLORS["card"], labelcolor=COLORS["text"],
              edgecolor=COLORS["surface"], framealpha=0.9)
    ax.set_title(f"{home_team}  {home_score} – {away_score}  {away_team}",
                 color="white", fontsize=14, fontweight="bold", pad=14)
    plt.tight_layout()
    return fig


# ─── SHOTMAP (partido completo) ────────────────────────────────────────────────
def plot_shotmap(df_shots, home_team, away_team):
    if df_shots.empty:
        return None

    fig, axes = plt.subplots(1, 2, figsize=(14, 8), facecolor=COLORS["bg"])

    for ax, (tname, color, flag) in zip(
        axes, [(home_team, COLORS["home"], True), (away_team, COLORS["away"], False)]
    ):
        # Vertical half-pitch, attacking upward
        pitch = VerticalPitch(
            pitch_type="statsbomb", half=True,
            pitch_color=COLORS["bg"], line_color="#3a5a3a",
            linewidth=1.5, spot_scale=0.005,
        )
        pitch.draw(ax=ax)
        ax.set_facecolor(COLORS["bg"])

        # Attack direction arrow
        ax.annotate("", xy=(3, 62), xytext=(3, 74),
                    arrowprops=dict(arrowstyle="->", color=color, lw=2))
        ax.text(3, 58, "Ataque", color=color, fontsize=7, ha="center", va="top", alpha=0.8)

        ts = df_shots[df_shots["is_home"] == flag].copy()
        if not ts.empty:
            # FIX: convert coords properly for VerticalPitch statsbomb
            # Statsbomb vertical: x=0-80 (width), y=0-120 (length)
            # VerticalPitch with half=True shows y from 60-120 (attacking half)
            # Sofascore: x=0-100 left-right, y=0-100 top-bottom
            # For attacking team: x → statsbomb_x (width 0-80), y → statsbomb_y (length 60-120)
            ts["sb_x"] = ts["player_coord_x"].fillna(50).astype(float) * 0.8
            ts["sb_y"] = 60 + ts["player_coord_y"].fillna(50).astype(float) * 0.6

            goals = ts[ts["is_goal"]]
            ng = ts[~ts["is_goal"]]

            if not ng.empty:
                xg = pd.to_numeric(ng["xg"], errors="coerce").fillna(0.05)
                pitch.scatter(
                    ng["sb_x"], ng["sb_y"],
                    s=xg * 900 + 80,
                    color="none", edgecolors=color,
                    linewidths=1.8, alpha=0.8, ax=ax, zorder=3
                )
            if not goals.empty:
                xg = pd.to_numeric(goals["xg"], errors="coerce").fillna(0.1)
                pitch.scatter(
                    goals["sb_x"], goals["sb_y"],
                    s=xg * 1100 + 200,
                    color=COLORS["goal"], edgecolors="white",
                    linewidths=1.5, marker="*", ax=ax, zorder=5
                )

        n_goals = int(ts["is_goal"].sum()) if not ts.empty else 0
        n_shots = len(ts)
        txg = float(pd.to_numeric(ts["xg"], errors="coerce").sum()) if not ts.empty else 0.0
        xgot_col = "xgot" if "xgot" in ts.columns else None
        txgot = float(pd.to_numeric(ts[xgot_col], errors="coerce").sum()) if xgot_col and not ts.empty else None

        xgot_str = f"  ·  xGoT {txgot:.2f}" if txgot is not None else ""
        ax.set_title(
            f"{tname}\n{n_goals} goles  ·  {n_shots} tiros  ·  xG {txg:.2f}{xgot_str}",
            color="white", fontsize=11, fontweight="bold", pad=10
        )

    leg = [
        plt.scatter([], [], c="none", edgecolors="white", s=80, linewidths=1.5, label="Tiro"),
        plt.scatter([], [], c=COLORS["goal"], marker="*", s=200, label="Gol ⭐"),
    ]
    fig.legend(handles=leg, loc="lower center", ncol=2,
               facecolor=COLORS["card"], labelcolor="white",
               edgecolor=COLORS["surface"], fontsize=9, framealpha=0.9)
    fig.suptitle("Mapa de Tiros", color="white", fontsize=15, fontweight="bold", y=1.01)
    plt.tight_layout()
    return fig


# ─── PLAYER RADAR ─────────────────────────────────────────────────────────────
def plot_player_radar(player_data):
    pos = (player_data.get("position") or "M")[0]
    BY_POS = {
        "G": {"Paradas": ("saves", 8), "Pases prec.": ("passes_accurate", 50),
              "Despejes": ("clearances", 8), "Duelos gan.": ("duels_won", 5),
              "G. concedidos": ("goals_conceded", 3)},
        "D": {"Tackles": ("tackles", 8), "Interc.": ("interceptions", 5),
              "Despejes": ("clearances", 10), "Duelos gan.": ("duels_won", 8),
              "Pases prec.": ("passes_accurate", 60), "Aéreos gan.": ("aerial_won", 5)},
        "M": {"Pases prec.": ("passes_accurate", 70), "Pases clave": ("key_passes", 5),
              "Tackles": ("tackles", 5), "Regates": ("dribbles_won", 5),
              "Tiros": ("shots_on_target", 3), "Asistencias": ("assists", 2)},
        "F": {"Goles": ("goals", 2), "Tiros": ("shots_on_target", 5),
              "xG": ("xg", 2), "Regates": ("dribbles_won", 6),
              "Asistencias": ("assists", 2), "Pases prec.": ("passes_accurate", 40)},
    }
    metrics = BY_POS.get(pos, BY_POS["M"])
    labels = list(metrics.keys())
    vals = [min(float(player_data.get(c, 0) or 0) / mx, 1.0)
            for _, (c, mx) in metrics.items()]
    N = len(labels)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    vp = vals + [vals[0]]
    ap = angles + [angles[0]]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True), facecolor=COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])
    for r in np.linspace(0.2, 1.0, 5):
        ax.plot(ap, [r] * (N + 1), color=COLORS["surface"], linewidth=0.8)
    for angle in angles:
        ax.plot([angle, angle], [0, 1], color=COLORS["surface"], linewidth=0.8)

    color = COLORS["home"] if player_data.get("side") == "home" else COLORS["away"]
    ax.fill(ap, vp, color=color, alpha=0.2)
    ax.plot(ap, vp, color=color, linewidth=2.5)
    ax.scatter(angles, vals, color=color, s=55, zorder=5, edgecolors="white", linewidths=0.8)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, color="white", fontsize=8.5, fontweight="bold")
    ax.set_yticks([])
    ax.spines["polar"].set_visible(False)

    for angle, vn, (_, (col, _)) in zip(angles, vals, metrics.items()):
        raw = player_data.get(col, 0) or 0
        try:
            disp = f"{float(raw):.2f}" if isinstance(raw, float) and raw != int(raw) else str(int(float(raw)))
        except Exception:
            disp = str(raw)
        ax.text(angle, vn + 0.14, disp, ha="center", va="center",
                color=color, fontsize=7.5, fontweight="bold")

    rating = player_data.get("rating")
    rs = f"  ·  Rating {float(rating):.2f}" if rating else ""
    ax.set_title(
        f"{player_data.get('player_name', '')}\n"
        f"{player_data.get('team', '')}  ·  {player_data.get('position', '')}{rs}",
        color="white", fontsize=10, fontweight="bold", pad=18
    )
    plt.tight_layout()
    return fig


# ─── PLAYER HEATMAP ───────────────────────────────────────────────────────────
def plot_player_heatmap(heatmap_data, player_name, side="home"):
    """
    Heatmap preciso con dirección de ataque indicada.
    Sofascore heatmap coords: x=0-100 (izq→der), y=0-100 (arriba→abajo)
    Usamos pitch horizontal (Pitch), con el equipo local atacando hacia la derecha.
    """
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=COLORS["bg"])
    pitch = Pitch(
        pitch_type="statsbomb",
        pitch_color=COLORS["bg"],
        line_color="#3a5a3a",
        linewidth=1.5,
    )
    pitch.draw(ax=ax)
    ax.set_facecolor(COLORS["bg"])

    color = COLORS["home"] if side == "home" else COLORS["away"]

    # Attack direction arrows
    arrow_y = -3
    ax.annotate("", xy=(110, arrow_y), xytext=(90, arrow_y),
                arrowprops=dict(arrowstyle="->", color=color, lw=2.5))
    ax.text(100, arrow_y - 3, "Dirección de ataque", color=color,
            fontsize=8, ha="center", va="top", alpha=0.9)

    if heatmap_data and "heatmap" in heatmap_data:
        pts = heatmap_data["heatmap"]
        if pts:
            # Sofascore x=0-100 → statsbomb x=0-120, y=0-100 → statsbomb y=0-80
            xs = [float(p.get("x", 50)) * 1.2 for p in pts]
            ys = [float(p.get("y", 50)) * 0.8 for p in pts]

            # KDE with higher bandwidth for smoother, more accurate heatmap
            pitch.kdeplot(
                xs, ys, ax=ax,
                fill=True, levels=30,
                cmap="YlOrRd", alpha=0.82,
                thresh=0.03, bw_adjust=0.7,
            )
            # scatter dots for density feel
            ax.scatter(xs, ys, s=8, color=color, alpha=0.25, zorder=3)
    else:
        ax.text(60, 40, "Heatmap no disponible",
                ha="center", va="center", color=COLORS["muted"], fontsize=12)

    ax.set_title(f"Mapa de calor  —  {player_name}",
                 color="white", fontsize=12, fontweight="bold")
    plt.tight_layout()
    return fig


# ─── PLAYER SHOT MAP ──────────────────────────────────────────────────────────
def plot_player_shots(df_shots, player_id, player_name, side):
    ps = df_shots[df_shots["player_id"] == player_id].copy() if not df_shots.empty else pd.DataFrame()
    color = COLORS["home"] if side == "home" else COLORS["away"]

    fig, ax = plt.subplots(figsize=(8, 7), facecolor=COLORS["bg"])
    pitch = VerticalPitch(
        pitch_type="statsbomb", half=True,
        pitch_color=COLORS["bg"], line_color="#3a5a3a", linewidth=1.5,
    )
    pitch.draw(ax=ax)
    ax.set_facecolor(COLORS["bg"])

    # attack direction
    ax.annotate("", xy=(3, 62), xytext=(3, 74),
                arrowprops=dict(arrowstyle="->", color=color, lw=2))
    ax.text(3, 58, "Ataque", color=color, fontsize=7, ha="center", va="top", alpha=0.8)

    if not ps.empty:
        ps["sb_x"] = ps["player_coord_x"].fillna(50).astype(float) * 0.8
        ps["sb_y"] = 60 + ps["player_coord_y"].fillna(50).astype(float) * 0.6

        goals = ps[ps["is_goal"]]
        ng = ps[~ps["is_goal"]]

        if not ng.empty:
            xg = pd.to_numeric(ng["xg"], errors="coerce").fillna(0.05)
            pitch.scatter(ng["sb_x"], ng["sb_y"],
                          s=xg * 1200 + 80,
                          color="none", edgecolors=color,
                          linewidths=2, alpha=0.85, ax=ax, zorder=3)
        if not goals.empty:
            xg = pd.to_numeric(goals["xg"], errors="coerce").fillna(0.1)
            pitch.scatter(goals["sb_x"], goals["sb_y"],
                          s=xg * 1400 + 200,
                          color=COLORS["goal"], edgecolors="white",
                          linewidths=1.5, marker="*", ax=ax, zorder=5)

        txg = float(pd.to_numeric(ps["xg"], errors="coerce").sum())
        xgot_col = "xgot" if "xgot" in ps.columns else None
        txgot = float(pd.to_numeric(ps[xgot_col], errors="coerce").sum()) if xgot_col else None
        xgot_str = f"  ·  xGoT {txgot:.2f}" if txgot is not None else ""

        ax.set_title(
            f"Tiros  —  {player_name}\n"
            f"{len(goals)} gol(es)  ·  {len(ps)} tiros  ·  xG {txg:.2f}{xgot_str}",
            color="white", fontsize=11, fontweight="bold"
        )
    else:
        ax.text(40, 75, "Sin tiros registrados",
                ha="center", va="center", color=COLORS["muted"], fontsize=12)
        ax.set_title(f"Tiros  —  {player_name}", color="white",
                     fontsize=11, fontweight="bold")

    plt.tight_layout()
    return fig


# ─── PLAYER STATS BARS ────────────────────────────────────────────────────────
def plot_player_bars(player_data):
    SM = {
        "Pases precisos": "passes_accurate",
        "% Pase":         "pass_accuracy",
        "Duelos gan.":    "duels_won",
        "% Duelos":       "duel_win_rate",
        "Tiros a puerta": "shots_on_target",
        "Regates gan.":   "dribbles_won",
        "Tackles":        "tackles",
        "Intercepciones": "interceptions",
        "Despejes":       "clearances",
        "Faltas":         "fouls_committed",
    }
    lb, vl = [], []
    for label, col in SM.items():
        v = float(player_data.get(col, 0) or 0)
        if v > 0:
            lb.append(label)
            vl.append(v)
    if not lb:
        return None

    color = COLORS["home"] if player_data.get("side") == "home" else COLORS["away"]
    fig, ax = plt.subplots(figsize=(7, max(3, len(lb) * 0.55)), facecolor=COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])
    ax.barh(lb, [max(vl) * 1.15] * len(vl), color=COLORS["surface"], height=0.55, alpha=0.3, zorder=0)
    bars = ax.barh(lb, vl, color=color, alpha=0.85, height=0.55)
    for bar, v in zip(bars, vl):
        ax.text(bar.get_width() + max(vl) * 0.03,
                bar.get_y() + bar.get_height() / 2,
                f"{v:.0f}", va="center", color="white", fontsize=10, fontweight="bold")
    ax.set_xlim(0, max(vl) * 1.25)
    ax.tick_params(colors=COLORS["muted"], labelsize=9)
    ax.spines[:].set_visible(False)
    ax.set_title("Estadísticas del partido", color="white", fontsize=11, fontweight="bold")
    plt.tight_layout()
    return fig


# ─── COMPARATOR RADAR ─────────────────────────────────────────────────────────
def plot_compare_radar(p1, p2):
    pos = (p1.get("position") or "M")[0]
    BY_POS = {
        "G": {"Paradas": ("saves", 8), "Pases prec.": ("passes_accurate", 50),
              "Despejes": ("clearances", 8), "Duelos gan.": ("duels_won", 5)},
        "D": {"Tackles": ("tackles", 8), "Interc.": ("interceptions", 5),
              "Despejes": ("clearances", 10), "Duelos gan.": ("duels_won", 8),
              "Pases prec.": ("passes_accurate", 60)},
        "M": {"Pases prec.": ("passes_accurate", 70), "Pases clave": ("key_passes", 5),
              "Tackles": ("tackles", 5), "Regates": ("dribbles_won", 5),
              "Tiros": ("shots_on_target", 3)},
        "F": {"Goles": ("goals", 2), "Tiros": ("shots_on_target", 5),
              "xG": ("xg", 2), "Regates": ("dribbles_won", 6),
              "Pases prec.": ("passes_accurate", 40)},
    }
    metrics = BY_POS.get(pos, BY_POS["M"])
    labels = list(metrics.keys())
    N = len(labels)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    ap = angles + [angles[0]]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True), facecolor=COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])
    for r in np.linspace(0.2, 1.0, 5):
        ax.plot(ap, [r] * (N + 1), color=COLORS["surface"], linewidth=0.8)
    for angle in angles:
        ax.plot([angle, angle], [0, 1], color=COLORS["surface"], linewidth=0.8)

    for player, color, label in [
        (p1, COLORS["home"], p1.get("short_name") or p1.get("player_name", "J1")),
        (p2, COLORS["away"], p2.get("short_name") or p2.get("player_name", "J2")),
    ]:
        vals = [min(float(player.get(c, 0) or 0) / mx, 1.0)
                for _, (c, mx) in metrics.items()]
        vp = vals + [vals[0]]
        ax.fill(ap, vp, color=color, alpha=0.18)
        ax.plot(ap, vp, color=color, linewidth=2.2, label=label)
        ax.scatter(angles, vals, color=color, s=45, zorder=5,
                   edgecolors="white", linewidths=0.6)

    ax.set_xticks(angles)
    ax.set_xticklabels(labels, color="white", fontsize=9, fontweight="bold")
    ax.set_yticks([])
    ax.spines["polar"].set_visible(False)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.15),
              facecolor=COLORS["card"], labelcolor="white",
              edgecolor=COLORS["surface"], fontsize=9)
    ax.set_title("Comparador de jugadores", color="white",
                 fontsize=11, fontweight="bold", pad=20)
    plt.tight_layout()
    return fig
