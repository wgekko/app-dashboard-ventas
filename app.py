import streamlit as st
import streamlit.components.v1 as components
import streamlit as st
from pathlib import Path
import os

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Analisis de datos",
    page_icon=":material/analytics:",
    layout="wide",  # 'wide' para ocupar todo el ancho
    initial_sidebar_state="collapsed",
)

# ----- Cargar estilos CSS -----
css_file = Path("assets/styles.css")
if css_file.exists():
    st.markdown(f"<style>{css_file.read_text()}</style>",
                unsafe_allow_html=True)
else:
    st.error("No se encontró el archivo CSS.")

# --- FUNCIÓN PARA CARGAR ARCHIVOS ---
def leer_archivo(ruta):
    """Lee el contenido de un archivo y lo devuelve como una cadena."""
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo en la ruta: {ruta}")
        return ""
    except Exception as e:
        st.error(f"Error al leer el archivo {ruta}: {e}")
        return ""

# --- RUTAS A TUS ARCHIVOS ---
# Asegúrate de que estos archivos estén en la misma carpeta que app.py
ruta_html = "assets/index.html"
ruta_css = "assets/estilos.css"
ruta_js = "assets/script.js"

# --- LECTURA DEL CONTENIDO DE LOS ARCHIVOS ---
html_content = leer_archivo(ruta_html)
css_content = leer_archivo(ruta_css)
js_content = leer_archivo(ruta_js)

# --- VERIFICACIÓN DE CONTENIDO ---
if not all([html_content, css_content, js_content]):
    st.warning("No se pudieron cargar todos los archivos necesarios (HTML, CSS, JS). La aplicación podría no funcionar como se espera.")
    st.stop()


html_final = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title></title>
    <style>
        {css_content}
    </style>
</head>
<body>
    {html_content}
    <script type="module">
        {js_content}
    </script>
</body>
</html>
"""
st.components.v1.html(html_final, height=600, scrolling=False)

col1, col2, col3 = st.columns([2, 2, 2])  # proporciones: izquierda, centro, derecha

with col2:
    if st.button("Entrar al enigmático mundo de Análisis de Datos", key="acceso", use_container_width=True):
        st.switch_page("pages/home.py")