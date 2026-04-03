# ⚽ Sofascore Match Analyzer

App web construida con Streamlit para analizar partidos de fútbol a partir del ID de Sofascore.

---

## 🚀 Instalación y uso

### 1. Requisitos previos
- Python 3.10+
- Google Chrome instalado (el scraper lo usa internamente)

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar la app

```bash
streamlit run app.py
```

Se abrirá automáticamente en `http://localhost:8501`

---

## 📖 Cómo encontrar el ID del partido

1. Ve a [sofascore.com](https://www.sofascore.com)
2. Busca el partido que quieras
3. Copia el número al final de la URL:

```
https://www.sofascore.com/es/real-madrid-barcelona/xDsb#id:14083567
                                                              ^^^^^^^^
                                                           Este es el ID
```

---

## 🗂️ Estructura de archivos

```
sofascore_app/
├── app.py                # App principal Streamlit
├── sofascore_client.py   # Cliente Selenium para scraping
├── data_parser.py        # Parseo de datos a DataFrames
├── charts.py             # Todas las funciones de gráficos
├── requirements.txt      # Dependencias
└── README.md             # Este archivo
```

---

## 📊 Secciones de la app

| Sección | Contenido |
|---------|-----------|
| **Resumen** | Marcador, stats comparativas en barras, métricas clave, mejores ratings |
| **Timeline** | Visualización temporal de goles, tarjetas, sustituciones y VAR |
| **Tiros** | Shot map por equipo con xG, detalle de cada tiro |
| **Jugadores** | Radar, heatmap, tiros y tabla ML-ready por jugador (tabs por equipo) |
| **Comparador** | Radar y tabla frente a frente de dos jugadores |

---

## ⚠️ Notas

- La primera carga de cada partido tarda ~10s (Chrome arranca en segundo plano)
- Los datos se cachean 5 minutos — cambiar el ID recarga todo
- Si hay errores 403 persistentes, abre `sofascore.com` en Chrome manualmente y vuelve a intentarlo
- Los datos son para uso personal/educativo
