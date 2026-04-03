# ⚽ Anelysis Football App

App web interactiva construida con **Streamlit** para buscar equipos, explorar sus historiales y analizar estadísticas avanzadas de partidos de fútbol extraídas de Sofascore.

---

## 🚀 Instalación y uso

### 1. Requisitos previos

* **Python 3.10+**
* **Google Chrome** instalado (el scraper lo usa internamente).

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar la app

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en `http://localhost:8501`.

---

## 📖 Cómo buscar y analizar un partido

Ya no es necesario buscar el ID manualmente en la web. El nuevo flujo está completamente integrado:

1. **Buscar Equipo:** Ve a la barra lateral izquierda bajo la sección 🔍 **Buscar Equipo**.
2. **Escribir nombre:** Ingresa el nombre del equipo (Ej: *Barcelona*) y presiona Buscar.
3. **Seleccionar:** Haz clic en **Ver Partidos** junto al escudo del equipo correcto.
4. **Analizar:** Despliega el partido que te interese en la lista y haz clic en 🚀 **Analizar Partido**.

---

## 🗂️ Estructura de archivos

```text
sofascore_app/
├── app.py                # App principal Streamlit
├── sofascore_client.py   # Cliente / Scraper para conexión con la API
├── data_parser.py        # Parseo de datos a DataFrames y limpieza
├── charts.py             # Funciones de gráficos (Plotly y Matplotlib)
├── requirements.txt      # Dependencias del proyecto
└── README.md             # Este archivo
```

---

## 📊 Secciones de la app

| Sección          | Contenido                                                                  |
| :--------------- | :------------------------------------------------------------------------- |
| **Buscador**     | Búsqueda por nombre de equipo y lista de resultados con logos e historial. |
| **Estadísticas** | Gráfico de barras espejo comparando xG, Posesión, Sprints y más.           |
| **Datos Crudos** | Tabla de métricas formateada (% para posesión, decimales para xG).         |
| **Otras vistas** | Timeline, Shot maps y estadísticas de jugadores.                           |

---

## ⚠️ Notas

* **Rendimiento:** La primera carga puede tardar unos segundos si Chrome arranca en segundo plano.
* **Memoria:** Se incluyó un botón de **🧹 Liberar Memoria** para limpiar la caché de Streamlit.
* **Cierre Seguro:** Usa el botón **🛑 Cerrar App** para detener los procesos de Python limpiamente.
* **Bloqueos (403):** Si hay errores persistentes, abre `sofascore.com` en Chrome manualmente y vuelve a intentarlo.

> **Aviso:** Los datos obtenidos son única y exclusivamente para uso personal/educativo.
