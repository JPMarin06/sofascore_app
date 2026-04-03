import pandas as pd

# Diccionario de alias para unificar nombres de la API (Inglés/Español)
STAT_MAPPING = {
    "Ball possession": ["ball possession", "posesión", "posesión de balón"],
    "Expected goals (xG)": ["expected goals", "expected goals (xg)", "goles esperados", "xg"],
    "Distance covered": ["distance covered", "distancia recorrida"],
    "Big chances": ["big chances", "ocasiones claras", "grandes ocasiones"],
    "Total shots": ["total shots", "tiros totales", "remates totales", "remates"],
    "Shots on target": ["shots on target", "remates a puerta", "tiros a puerta", "remates al arco"],
    "Goalkeeper saves": ["goalkeeper saves", "paradas", "paradas del portero", "saves"],
    "Number of sprints": ["number of sprints", "sprints", "número de sprints"],
    "Corner kicks": ["corner kicks", "corners", "saques de esquina", "tiros de esquina"],
    "Fouls": ["fouls", "faltas"],
    "Passes": ["passes", "total passes", "pases", "pases totales"],
    "Tackles": ["tackles", "entradas", "tackles"],
    "Yellow cards": ["yellow cards", "tarjetas amarillas"]
}

def parse_statistics(raw, home_team, away_team):
    if not raw or "statistics" not in raw:
        return pd.DataFrame()
        
    extracted_stats = {}
    
    # Recorrer todos los periodos (ALL es el partido completo)
    for period in raw.get("statistics", []):
        if period.get("period") == "ALL":
            for group in period.get("groups", []):
                for s in group.get("statisticsItems", []):
                    name = str(s.get("name", "")).strip().lower()
                    extracted_stats[name] = {
                        "home": s.get("home"), 
                        "away": s.get("away")
                    }

    rows = []
    for display_name, aliases in STAT_MAPPING.items():
        found = False
        for alias in aliases:
            if alias in extracted_stats:
                # Extraemos y limpiamos símbolos como el % (si los hay) dejándolos como string
                h_val = str(extracted_stats[alias]["home"]).replace("%", "").strip()
                a_val = str(extracted_stats[alias]["away"]).replace("%", "").strip()
                
                rows.append({
                    "stat": display_name,
                    home_team: h_val,
                    away_team: a_val
                })
                found = True
                break
        
        # Si no existe la estadística, se marca como no disponible
        if not found:
            rows.append({
                "stat": display_name, 
                home_team: "Dato no disponible", 
                away_team: "Dato no disponible"
            })

    return pd.DataFrame(rows)

# Funciones vacías para mantener compatibilidad si app.py las requiere en el futuro
def parse_incidents(raw, home_team, away_team): return pd.DataFrame()
def parse_shotmap(raw, home_team, away_team): return pd.DataFrame()
def parse_lineups(raw, home_team, away_team): return pd.DataFrame()