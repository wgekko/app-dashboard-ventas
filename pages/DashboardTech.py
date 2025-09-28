
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
from bumplot import bumplot
from matplotlib import cm
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.api import VAR
import pandas_ta as ta
import plotly.graph_objs as go
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, accuracy_score
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
import plotly.express as px

# --- CONFIGURACIÓN DE LA PÁGINA ---
# Configura el título de la pestaña del navegador y el layout de la página a "wide" para aprovechar todo el ancho.
st.set_page_config(page_title="Dashboard Store Tech",layout="wide")

# Título principal del dashboard que se mostrará en la aplicación.
st.title(":material/qr_code_2: Dashboard Store Tech 2024")

# ----- Cargar estilos CSS -----
css_file = Path("assets/bstyle.css")
if css_file.exists():
    st.markdown(f"<style>{css_file.read_text()}</style>",
                unsafe_allow_html=True)
else:
    st.error("No se encontró el archivo CSS.")
    
# --- ESTILOS PERSONALIZADOS ---
# Se obtienen los colores del tema actual de Streamlit para que los gráficos y estilos coincidan.
chartCategoricalColors = st.get_option("theme.chartCategoricalColors")
secondaryBackgroundColor = st.get_option("theme.secondaryBackgroundColor")
textColor = st.get_option("theme.textColor")

# Se define un bloque de CSS para personalizar el fondo de algunos componentes de Streamlit (métricas y gráficos).
# Esto se hace para que el diseño sea más cohesivo y atractivo.
st.write('<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">', unsafe_allow_html=True)
estilos = """
<style>
    div[class*='st-key-chart'],
    .stMetric, .stMetric svg{
        background-color: #032063!important
    }
    div.st-key-numeroproductos div[data-testid="stMetricValue"]>div::before {
        content: "\\e1b1";
        font-family: 'Material Icons'; 
        vertical-align: -20%;
        color:#FF8C00;
    }
    div.st-key-numerotiendas div[data-testid="stMetricValue"]>div::before {
        content: "\\e8d1";
        font-family: 'Material Icons'; 
        vertical-align: -20%;   
        color:#FF8C00;
    }
</style>
"""
st.html(estilos)

# --- FUNCIONES ---

@st.cache_data 
def cargarDatos():
    dfDatosVentas = pd.read_excel("data/TechShopSales.xlsx")
    return dfDatosVentas


def generarMetrica(df, campo, titulo, grafica="linea", prefijo="$"):
    # Se extrae el último dato de la columna para mostrarlo como valor principal.
    UltDato = df.iloc[-1][campo]
    # Se extrae el penúltimo dato para calcular la variación.
    AntDato = df.iloc[-2][campo]
    # Se calcula la variación porcentual entre el último y el penúltimo dato.
    variacion = (UltDato - AntDato) / AntDato
    # Se convierte la columna entera en una lista para usarla en el mini-gráfico.
    arrDatosVentas = df[campo].to_list()
    # Se utiliza el componente st.metric para mostrar la información formateada.
    st.metric(label=titulo, value=f"{prefijo}{UltDato:,.0f}", delta=f"{variacion:.2%}", chart_data=arrDatosVentas, delta_color="normal", chart_type=grafica, border=True, width=300)

def aplicarBackgroundChart(fig, color):
    # Actualiza el layout del gráfico para cambiar el color del área de trazado y el papel.
    return fig.update_layout({
        "plot_bgcolor": color,
        "paper_bgcolor": color,
    })

# --- CARGA Y TRANSFORMACIÓN DE DATOS ---

# Carga el DataFrame principal usando la función cacheada.
dfDatosVentas = cargarDatos()
#st.write(dfDatosVentas)
# 1. Creación de nuevas columnas
# Se calcula la columna 'Sales' multiplicando la cantidad de la transacción por el precio unitario.
dfDatosVentas["Sales"] = dfDatosVentas["transaction_qty"] * dfDatosVentas["unit_price"]
# o se puede si el archivo ya tiene  una columna directamene en el excel no es necesario 

# Se extraen componentes de la fecha para facilitar los agrupamientos posteriores.
# .dt es un accesor que permite usar métodos de fecha y hora en una Serie de pandas.
dfDatosVentas['Month_Name'] = dfDatosVentas['transaction_date'].dt.month_name(locale='es_ES') # Nombre del mes en español
dfDatosVentas['Month'] = dfDatosVentas['transaction_date'].dt.month # Número del mes
dfDatosVentas['Year'] = dfDatosVentas['transaction_date'].dt.year # Año
dfDatosVentas['Week'] = dfDatosVentas['transaction_date'].dt.isocalendar().week # Número de la semana del año

#st.write(dfDatosVentas['Month'])
# --- FILTROS INTERACTIVOS ---
# Se crea un selectbox (menú desplegable) para que el usuario pueda filtrar por categoría de producto.
# Las opciones incluyen "Todas" más la lista de categorías únicas del DataFrame.
parTipoProducto = st.selectbox("Categoría de producto", options=["Todas"] + list(dfDatosVentas["product_category"].unique()))

# Si el usuario elige una categoría específica (diferente de "Todas"), se filtra el DataFrame principal.
if parTipoProducto != "Todas":
    dfDatosVentas = dfDatosVentas[dfDatosVentas["product_category"] == parTipoProducto]

# --- AGRUPACIONES DE DATOS (DATA WRANGLING) ---
# Se crean diferentes DataFrames agregados que servirán como fuente para los gráficos y métricas.
# El patrón .groupby().agg().reset_index() es muy común en pandas para resumir datos.

# Agrupa las ventas y cantidades por Año, Mes y Nombre del Mes.
dfVentasMes = dfDatosVentas.groupby(['Year', 'Month', 'Month_Name']).agg({"Sales": "sum", "transaction_qty": "sum"}).reset_index()

# Agrupa las ventas y cantidades por Mes y por Tienda.
dfVentasMesTienda = dfDatosVentas.groupby(['Year', 'Month', 'Month_Name', 'store_location']).agg({"Sales": "sum", "transaction_qty": "sum"}).reset_index()

# Agrupa las ventas y cantidades por Semana.
dfVentasSemana = dfDatosVentas.groupby(['Year', 'Week']).agg({"Sales": "sum", "transaction_qty": "sum"}).reset_index()

# Se decide dinámicamente si agrupar por tipo de producto o categoría general, basado en el filtro.
if parTipoProducto != "Todas":
    campoGrupo = "product_type"
else:
    campoGrupo = "product_category"

# Agrupa las ventas por Mes y por la categoría/tipo de producto seleccionado.
dfVentasProducto = dfDatosVentas.groupby(['Year', 'Month', 'Month_Name', campoGrupo]).agg({"Sales": "sum", "transaction_qty": "sum"}).reset_index()

# Se pivotea la tabla para tener las tiendas como columnas y los productos como filas.
dfVentasProductoTienda = dfDatosVentas.groupby(['store_location', campoGrupo]).agg({"Sales": "sum"}).reset_index()
dfVentasProductoTienda = dfVentasProductoTienda.pivot(index=campoGrupo, columns='store_location', values='Sales').fillna(0).reset_index()

# Se prepara el DataFrame para el Bump Chart. Se pivotea para tener los productos como columnas y los meses como filas.
dfVentasProductoBump = dfVentasProducto.pivot(index=['Month_Name', 'Month'], columns=campoGrupo, values='Sales').fillna(0).reset_index()
dfVentasProductoBump = dfVentasProductoBump.sort_values(by="Month") # Se asegura que los meses estén ordenados.


# --- CÁLCULOS PARA MÉTRICAS Y GRÁFICOS ---
# Se obtienen datos específicos del último y penúltimo mes/semana para las métricas y etiquetas.
dfMesAnt = dfVentasMes.iloc[-2]
dfMesUlt = dfVentasMes.iloc[-1]
MesUltNombre = dfMesUlt["Month_Name"]

# Se filtran los datos de ventas por producto para el último mes.
dfVentasProductoUlt = dfVentasProducto[(dfVentasProducto["Month"] == dfMesUlt["Month"]) & (dfVentasProducto["Year"] == dfMesUlt["Year"])]
# Se calcula el ranking de ventas de productos para el último mes.
dfVentasProductoUlt["Sales_Rank"] = dfVentasProductoUlt["Sales"].rank(ascending=False, method="min").astype(int)
dfVentasProductoUlt = dfVentasProductoUlt.sort_values(by="Sales_Rank")

dfSemanaAnt = dfVentasSemana.iloc[-2]
dfSemanaUlt = dfVentasSemana.iloc[-1]
SemanaUlt = dfSemanaUlt["Week"]

# Se calculan métricas generales.
numTiendas = dfDatosVentas["store_id"].nunique() # Cuenta el número de tiendas únicas.
numProductos = dfDatosVentas["product_id"].nunique() # Cuenta el número de productos únicos.

# --- RENDERIZADO DEL DASHBOARD ---

# Contenedor para las métricas principales (KPIs).
# with st.container(horizontal=True, horizontal_alignment="center", key="metricas", width='stretch'):
#     generarMetrica(dfVentasMes, "Sales", f"Ventas **{MesUltNombre}**", "line")
#     generarMetrica(dfVentasMes, "transaction_qty", f"Unidades Mes **{MesUltNombre}**", "area", "")
#     generarMetrica(dfVentasSemana, "Sales", f"Ventas semana **{SemanaUlt}**", "barra")
#     generarMetrica(dfVentasSemana, "transaction_qty", f"Unidades semana **{SemanaUlt}**", "area", "")
#     with st.container(gap='small',key="metricasAdicionales"):
#         # st.write(":material/store:")
#         with st.container(gap='small',key="numerotiendas"):
#             st.metric(label="Número de tiendas", value=f"{numTiendas}", delta="", border=True, width=180)
#         with st.container(gap='small',key="numeroproductos"):
#             st.metric(label="Número de Productos", value=f"{numProductos}", delta="", border=True, width=180)
# Crear columnas para cada métrica (ajusta el número de columnas según necesites)

#cols = st.columns(6)  # Puedes cambiar a más o menos columnas según tus elementos
with st.container(horizontal=True, horizontal_alignment="center", key="metricas"):
    cols = st.columns([1.3, 1.3, 1.3, 1.3, 0.9, 0.9])

    # Ventas del mes
    with cols[0]:
        generarMetrica(dfVentasMes, "Sales", f"Ventas **{MesUltNombre}**", "line")

    # Unidades del mes
    with cols[1]:
        generarMetrica(dfVentasMes, "transaction_qty", f"Unidades Mes **{MesUltNombre}**", "area", "")

    # Ventas de la semana
    with cols[2]:
        generarMetrica(dfVentasSemana, "Sales", f"Ventas semana **{SemanaUlt}**", "barra")

    # Unidades de la semana
    with cols[3]:
        generarMetrica(dfVentasSemana, "transaction_qty", f"Unidades semana **{SemanaUlt}**", "area", "")

    # Número de tiendas
    with cols[4]:
        st.metric(label="Número de tiendas", value=f"{numTiendas}", delta="", border=True, width=180)

    # Número de productos
    with cols[5]:
        st.metric(label="Número de Productos", value=f"{numProductos}", delta="", border=True, width=180)

st.divider()
with st.expander(":material/two_pager_store: Análisis por tiendas"):
    st.subheader(":material/two_pager_store: Análisis por tiendas")
    # Contenedor para los gráficos relacionados con las tiendas.
    with st.container(horizontal=True, horizontal_alignment="center", width='stretch'):
        with st.container(border=True, key="chart-ventasTienda", width='stretch'):
            # Gráfico de barras agrupadas de ventas por tienda y mes.
            figVentasTienda = px.bar(dfVentasMesTienda, x='Month_Name', y='Sales', color='store_location', barmode='group', title="Ventas por país y mes", color_discrete_sequence=chartCategoricalColors)
            st.plotly_chart(aplicarBackgroundChart(figVentasTienda, secondaryBackgroundColor), use_container_width=True, theme=None)
        
        with st.container(border=True, key="chart-sunburstTienda"):
            # Gráfico Sunburst para ver la distribución de ventas jerárquicamente: Tienda -> Categoría -> Tipo.
            fig = px.sunburst(dfDatosVentas, path=['store_location', 'product_category', 'product_type'], values='Sales', title="Ventas por ubicación y categoría", color_discrete_sequence=chartCategoricalColors)
            st.plotly_chart(aplicarBackgroundChart(fig, secondaryBackgroundColor), use_container_width=True, theme=None)
    st.write("###")    
    with st.container(border=True, key="chart-dataframe"):
            # Se muestra el DataFrame pivoteado como una tabla con un mapa de calor.
            columnas = dfVentasProductoTienda.columns[1:]
            # Se define un mapa de colores personalizado para el gradiente.
            colors = ["#8B0000", "#DAA520", "#228B22"]
            cmap_name = "my_custom_cmap"
            custom_cmap = LinearSegmentedColormap.from_list(cmap_name, colors, N=256)
            # Se aplica el estilo de gradiente al DataFrame y se formatea para que no tenga decimales.
            styled_df = dfVentasProductoTienda.style.background_gradient(subset=columnas, cmap=custom_cmap).format("{:,.0f}", subset=columnas)
            st.write("Ventas por producto y tienda")
            st.dataframe(styled_df, use_container_width=True, hide_index=True, width='stretch')
            
st.divider()

with st.expander(":material/qr_code_scanner: Análisis por Productos"):
    st.subheader(":material/qr_code_scanner: Análisis por Productos")
    # Contenedor para los gráficos relacionados con los productos.
    with st.container(horizontal=True, horizontal_alignment="center", gap="large", width='stretch'):
        # Se usan columnas para organizar mejor los gráficos en el espacio disponible.
        cols = st.columns([3, 3, 4])
        with cols[0]:
            with st.container(border=True, key="chart-ventasProducto"):
                # Gráfico de barras de ventas por categoría/tipo de producto y mes.
                figVentasProducto = px.bar(
                    dfVentasProducto,
                    x='Month_Name',  
                    y='Sales',
                    color=campoGrupo,
                    barmode='group',
                    title="Ventas por categoría y mes" if parTipoProducto == "Todas" else f"Ventas por categoría {parTipoProducto} y mes",
                    color_discrete_sequence=chartCategoricalColors
                )
                st.plotly_chart(aplicarBackgroundChart(figVentasProducto, secondaryBackgroundColor), use_container_width=True)

        with cols[1]:
            with st.container(border=True, key="chart-sunburstProducto"):
                # Gráfico Sunburst para ver la jerarquía de productos.
                fig = px.sunburst(dfDatosVentas, path=[ 'store_location','product_category', 'product_type'], values='Sales', title="Ventas por categoría y detalle", color_discrete_sequence=chartCategoricalColors)
                st.plotly_chart(aplicarBackgroundChart(fig, secondaryBackgroundColor), use_container_width=True, theme=None) 
        
        with cols[2]:
            # --- Creación del Bump Chart con Matplotlib y bumplot ---
            # Se extraen los nombres de las columnas que contienen las categorías/productos.
            camposCategorias = [x for x in dfVentasProductoBump.columns if "Month" not in x]
            categoriaProductos = dfVentasProductoUlt[campoGrupo].to_list()

            # Se crea la figura y los ejes de Matplotlib.
            fig, ax = plt.subplots(figsize=(8, 7))
            
            # Se llama a la función bumplot para generar el gráfico de ranking.
            bumplot(
                x="Month",
                y_columns=camposCategorias,
                data=dfVentasProductoBump,
                curve_force=0.5,
                plot_kwargs={"lw": 4},
                scatter_kwargs={"s": 150, "ec": "black", "lw": 2},
                colors=chartCategoricalColors,
            )
            
            # --- Personalización del gráfico de Matplotlib ---
            ax.set_title("Ranking de productos por mes" if parTipoProducto == "Todas" else f"Ranking de productos {parTipoProducto} por mes", fontsize=16)
            ax.set_facecolor(secondaryBackgroundColor)
            fig.patch.set_facecolor(secondaryBackgroundColor)
            
            ax.set_yticks(
                [i for i in range(1, len(categoriaProductos) + 1)],
            )
            
            # Se añaden etiquetas de texto al final de cada línea del bump chart.
            ultMes = dfVentasProductoBump["Month"].max()
            for i, categoria in enumerate(categoriaProductos):
                ax.text(
                    x=ultMes + 0.2,
                    y=i + 1,
                    s=categoria,
                    size=11,
                    va="center",
                    ha="left",
                    color="#FFA500" 
                )
            
            # Se establece la etiqueta del eje X como "Mes".
            ax.set_xlabel("Mes", fontsize=12)
            # Se ocultan los bordes (spines) superior, derecho, izquierdo y inferior del gráfico para un diseño más limpio.
            ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
            # Se agrega una cuadrícula con transparencia para mejorar la legibilidad.
            ax.grid(alpha=0.4)
            
            # Se ajustan los colores del texto para que coincidan con el tema de Streamlit.
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color(textColor)
            ax.title.set_color(textColor)
            ax.xaxis.label.set_color(textColor)
            
            # Se muestra el gráfico de Matplotlib en Streamlit.
            #with st.container(border=True, key="chart-bumpProducto"):
            st.pyplot(fig, use_container_width=True)
                
# ========= Pestaña Forecast =========
# ======================= FUNCIONES DE FORECAST =======================
import matplotlib.pyplot as plt
import matplotlib as mpl

# Estilo global para todos los gráficos
mpl.rcParams.update({
    'axes.facecolor': '#0B0F2B',       # fondo del gráfico
    'figure.facecolor': '#0B0F2B',     # fondo del contenedor
    'axes.edgecolor': 'white',
    'axes.labelcolor': 'white',
    'xtick.color': 'white',
    'ytick.color': 'white',
    'text.color': 'white',
    'legend.edgecolor': 'white',
    'legend.facecolor': '#1a1a2e',
    'legend.fontsize': 'small',
    'grid.color': '#444444',
})

def forecast_tab(dfDatosVentas):
    st.header(":material/finance_mode: Forecast de Ventas Diarias")

    # --- Agrupación diaria ---
    dfVentasDia = dfDatosVentas.groupby("transaction_date").agg({
        "Sales": "sum",
        "transaction_qty": "sum",
        "unit_price": "mean"
    }).reset_index()

    # --- Preparar DataFrame ---
    dfForecast = dfVentasDia.set_index("transaction_date")[["Sales", "transaction_qty", "unit_price"]]
    dfForecast = dfForecast.asfreq("D").fillna(0)

    if not pd.api.types.is_datetime64_any_dtype(dfForecast.index):
        st.error("El índice del DataFrame no es de tipo datetime.")
        return

    st.markdown("""
    Selecciona el modelo de pronóstico:
    - **SARIMA**: Una sola serie.
    - **VAR**: Múltiples series relacionadas.
    """)

    model_choice = st.selectbox("Modelo de predicción", ["SARIMA", "VAR"])

    # === SARIMA ===
    if model_choice == "SARIMA":
        target = st.selectbox("Selecciona la variable", dfForecast.columns)
        steps = st.slider("Días a predecir", 7, 90, 30)

        serie = dfForecast[target].dropna()
        try:
            model = SARIMAX(serie, order=(1,1,1), seasonal_order=(1,1,1,7))
            results = model.fit(disp=False)

            forecast = results.get_forecast(steps=steps)
            forecast_index = pd.date_range(start=serie.index[-1] + pd.Timedelta(days=1),
                                        periods=steps, freq="D")
            forecast_series = pd.Series(forecast.predicted_mean, index=forecast_index)
            ci = forecast.conf_int()

            # Gráfico mejor proporcionado y con tema oscuro
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.plot(serie, label="Histórico", color="#FFD700")
            ax.plot(forecast_series, label="Forecast", color="orange")
            ax.fill_between(forecast_index, ci.iloc[:, 0], ci.iloc[:, 1], color="orange", alpha=0.2)
            ax.set_title(f"Forecast de {target} (SARIMA)", fontsize=14)
            ax.legend()
            st.pyplot(fig)

        except Exception as e:
            st.error(f"Error al ajustar SARIMA: {e}")

    # === VAR ===
    elif model_choice == "VAR":
        st.write("El modelo VAR requiere al menos 2 series numéricas.")
        default_vars = ["Sales", "transaction_qty", "unit_price"]
        cols = st.multiselect("Selecciona variables", dfForecast.columns, default=default_vars)

        steps = st.slider("Días a predecir", 7, 30, 15)

        if len(cols) >= 2:
            data = dfForecast[cols].dropna()
            try:
                model = VAR(data)
                results = model.fit(maxlags=15, ic="aic")

                forecast = results.forecast(data.values[-results.k_ar:], steps=steps)
                forecast_index = pd.date_range(start=data.index[-1] + pd.Timedelta(days=1),
                                            periods=steps, freq="D")
                forecast_df = pd.DataFrame(forecast, index=forecast_index, columns=cols)

                st.subheader("Forecast multivariado (VAR)")

                # Mostrar cada serie en su propio gráfico (en 3 columnas)
                columns = st.columns(len(cols))
                for i, col in enumerate(cols):
                    with columns[i]:
                        fig, ax = plt.subplots(figsize=(5, 4))
                        ax.plot(data[col], label="Histórico", color="#FFD700")
                        ax.plot(forecast_df[col], "--", label="Forecast", color="#39FF14")
                        ax.set_title(col, fontsize=12)
                        ax.legend()
                        st.pyplot(fig)

            except Exception as e:
                st.error(f"Error al ajustar VAR: {e}")
        else:
            st.warning("Selecciona al menos 2 variables para usar VAR.")


# --- Función para mostrar indicadores técnicos ---
def indicadores_tecnicos(dfForecast):
    st.subheader(":material/analytics: Indicadores Técnicos")
    
    series_disponibles = ["Sales", "transaction_qty", "unit_price"]
    serie_sel = st.selectbox("Selecciona serie para análisis", series_disponibles)

    df_ind = dfForecast[[serie_sel]].copy()

    # RSI
    df_ind["RSI"] = ta.rsi(df_ind[serie_sel], length=14)

    # Estocástico (K y D)
    stoch = ta.stoch(df_ind[serie_sel], df_ind[serie_sel], df_ind[serie_sel])
    df_ind["Stoch_K"] = stoch["STOCHk_14_3_3"]
    df_ind["Stoch_D"] = stoch["STOCHd_14_3_3"]

    df_ind["Linear_Trend"] = ta.linreg(df_ind[serie_sel], length=14)

    # 1) Gráfico principal: Serie base + Linear Trend
    fig1 = go.Figure()

    # Serie base
    fig1.add_trace(go.Scatter(
        x=df_ind.index, y=df_ind[serie_sel], mode='lines', name=serie_sel,
        line=dict(color='#FFD700')  # Amarillo dorado
    ))

    # Línea de tendencia
    fig1.add_trace(go.Scatter(
        x=df_ind.index, y=df_ind["Linear_Trend"], mode='lines', name='Linear Trend',
        line=dict(color='#39FF14', width=3)  # Verde flúor
    ))

    # Estilo del gráfico
    fig1.update_layout(
        title=f"Serie {serie_sel} con Linear Trend",
        xaxis_title="Fecha",
        yaxis_title="Valor",
        hovermode='x unified',

        # Leyenda con estilo coherente
        legend=dict(
            bgcolor='rgba(15,15,40,0.8)',       # Fondo oscuro semitransparente
            font=dict(color='white'),           # Texto blanco
            bordercolor='rgba(255,255,255,0.3)', 
            borderwidth=1
        ),

        # Fondos
        plot_bgcolor='#0B0F2B',   # Fondo del área de gráfico
        paper_bgcolor='#0B0F2B',  # Fondo general
        font=dict(color='white')  # Color de texto general
    )

    # Mostrar en Streamlit
    st.plotly_chart(fig1, use_container_width=True)
 
    # 2) Gráfico RSI
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df_ind.index, y=df_ind["RSI"], mode='lines', name='RSI',
                            line=dict(color="#39FF14")))  # Borravino
    fig2.update_layout(
        title="RSI (Índice de Fuerza Relativa)",
        xaxis_title="Fecha",
        yaxis_title="RSI",
        hovermode='x unified',
        legend=dict(bgcolor='rgba(255,255,255,0.8)', bordercolor='black', borderwidth=1)
    )
    st.plotly_chart(fig2, use_container_width=True )

    fig3 = go.Figure()

    # Líneas K y D
    fig3.add_trace(go.Scatter(
        x=df_ind.index, y=df_ind["Stoch_K"], mode='lines', name='Stoch K',
        line=dict(color='#39FF14', dash='dot'))
    )

    fig3.add_trace(go.Scatter(
        x=df_ind.index, y=df_ind["Stoch_D"], mode='lines', name='Stoch D',
        line=dict(color='#E6007E', dash='dash'))
    )

    # Configurar layout
    fig3.update_layout(
        title="Oscilador Estocástico (K y D)",
        xaxis_title="Fecha",
        yaxis_title="Valor",
        hovermode='x unified',

        # Estilo profesional para la leyenda
        legend=dict(
            bgcolor='rgba(15,15,40,0.8)',     # fondo oscuro semitransparente
            font=dict(color='white'),         # texto blanco
            bordercolor='rgba(255,255,255,0.3)', 
            borderwidth=1
        ),

        # Fondo general del gráfico
        plot_bgcolor='#0B0F2B',   # fondo del área del gráfico
        paper_bgcolor='#0B0F2B',  # fondo fuera del área del gráfico
        font=dict(color='white')  # texto general (títulos, ejes)
    )

    # Mostrar en Streamlit
    st.plotly_chart(fig3, use_container_width=True)

# --- Preparación de dfForecast para análisis ---
# Agrupar datos por día (asegúrate que transaction_date esté en formato datetime)
dfVentasDia = dfDatosVentas.groupby("transaction_date").agg({
    "Sales": "sum",
    "transaction_qty": "sum",
    "unit_price": "mean"
}).reset_index()

dfForecast = dfVentasDia.set_index("transaction_date")[["Sales", "transaction_qty", "unit_price"]]
dfForecast = dfForecast.asfreq("D").fillna(0)  # frecuencia diaria con llenado de 0

# --- Streamlit layout ---
st.divider()
with st.expander(":material/finance_mode: Forescast de Ventas - Modelos Arima / VAR"):    
    #st.subheader("Forecast de Ventas")
    # Aquí deberías tener definida tu función forecast_tab y pasarle dfDatosVentas
    forecast_tab(dfDatosVentas)
    
st.divider()    
with st.expander(":material/analytics: Estadistica Descriptiva - Indicadores Técnicos y Osciladores"):
    # Llamar a indicadores técnicos pasándole el DataFrame ya preparado
    indicadores_tecnicos(dfForecast)
    
st.divider() 
with st.expander(":material/browse_activity: Modelo de Regresión Lineal/Logística/Clustering (K-Means)/Market Basket Analysis - Predicción de Ventas"):    
    # --- REGRESIÓN LINEAL ---
    st.subheader(":material/ssid_chart: Modelo de Regresión Lineal - Predicción de Ventas")

    # Preparación de datos
    dfRL = dfDatosVentas[["transaction_qty", "unit_price", "Sales"]].dropna()
    X = dfRL[["transaction_qty", "unit_price"]]
    y = dfRL["Sales"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Entrenamiento
    modeloRL = LinearRegression()
    modeloRL.fit(X_train, y_train)
    y_pred = modeloRL.predict(X_test)
    scoreRL = r2_score(y_test, y_pred)

    # Mensaje explicativo
    st.write("Este modelo estima las ventas en función de la cantidad y el precio unitario del producto.")
    st.success(f"R² Score: {scoreRL:.2f}")

    # --- Visualización mejorada ---
    import numpy as np

    # Crear DataFrame para graficar
    error = y_test - y_pred
    dfRL_vis = pd.DataFrame({
        "Ventas Reales": y_test,
        "Ventas Predichas": y_pred,
        "Error Absoluto": np.abs(error)
    })

    # Gráfico de dispersión con escala de color
    figRL = px.scatter(
        dfRL_vis,
        x="Ventas Reales",
        y="Ventas Predichas",
        color="Error Absoluto",
        color_continuous_scale="RdYlGn_r",
        title="Regresión Lineal - Ventas Reales vs Predichas",
        labels={"Error Absoluto": "Error Absoluto"}
    )

    # Línea de predicción perfecta (y = x)
    min_val = min(dfRL_vis["Ventas Reales"].min(), dfRL_vis["Ventas Predichas"].min())
    max_val = max(dfRL_vis["Ventas Reales"].max(), dfRL_vis["Ventas Predichas"].max())

    figRL.add_scatter(
        x=[min_val, max_val],
        y=[min_val, max_val],
        mode='lines',
        line=dict(color='#00f0ff', dash='dash', width=3),
        name='Línea Perfecta'
    )

    # Mostrar gráfico
    st.plotly_chart(figRL)   
    st.subheader(":material/multiline_chart: Clustering (K-Means)-Segmentación de Productos")
    # Verificamos que 'product_type' exista en el DataFrame
    if "product_type" in dfDatosVentas.columns:
        
        # Agrupamos por tipo de producto (nombre comercial)
        dfCluster = dfDatosVentas.groupby("product_type").agg({
            "Sales": "sum",
            "transaction_qty": "sum",
            "unit_price": "mean"
        }).dropna()

        # Solo aplicamos clustering si hay al menos 3 productos
        if dfCluster.shape[0] >= 3:
            modeloKMeans = KMeans(n_clusters=3, random_state=42)
            dfCluster["Cluster"] = modeloKMeans.fit_predict(dfCluster)

            st.write("Segmenta productos según ventas totales, cantidad y precio unitario promedio.")
            st.dataframe(dfCluster.reset_index().head())

            # Gráfico 3D
            figCluster = px.scatter_3d(
                dfCluster.reset_index(),
                x="Sales",
                y="transaction_qty",
                z="unit_price",
                color=dfCluster["Cluster"].astype(str),
                hover_name="product_type",
                title="Clusters de Productos Tecnológicos"
            )
            st.plotly_chart(figCluster)
        
        else:
            st.warning("⚠️ No hay suficientes productos (mínimo 3) para aplicar clustering con KMeans.")
    else:
        st.warning("⚠️ La columna 'product_type' no existe en los datos.")

    # --- MARKET BASKET ANALYSIS ---    
    st.subheader(":material/network_intel_node: Market Basket Analysis - Productos que se compran juntos")

    # Asegurar que la columna 'product_type' existe
    if "product_type" in dfDatosVentas.columns:

        # Agrupar productos comprados por transacción
        dfBasket = dfDatosVentas.groupby("transaction_id")["product_type"].apply(list).tolist()

        # Codificación binaria de los productos en las transacciones
        te = TransactionEncoder()
        dfEncoded = te.fit_transform(dfBasket)
        dfTrans = pd.DataFrame(dfEncoded, columns=te.columns_)

        # Ejecutar algoritmo Apriori con soporte mínimo ajustado
        frequent_itemsets = apriori(dfTrans, min_support=0.005, use_colnames=True)

        # Generar reglas de asociación
        reglas = association_rules(frequent_itemsets, metric="lift", min_threshold=1)

        # Mostrar resultados o advertencia si está vacío
        if not reglas.empty:
            st.write("Muestra asociaciones frecuentes entre productos comprados juntos.")
            st.dataframe(reglas[["antecedents", "consequents", "support", "confidence", "lift"]].head())
        else:
            st.warning("⚠️ No se encontraron reglas de asociación con los parámetros actuales.")
    else:
        st.warning("⚠️ La columna 'product_type' no existe en los datos.")

# --------------- boton de salida ----------------------------
st.divider()
col1, col2, col3 = st.columns([2, 2, 2])  # proporciones: izquierda, centro, derecha


with col2:   
    if st.button("Salir de sistema", key="btnexit", use_container_width=True):
            st.switch_page("pages/exit-page.py")
                

# --------------- footer -----------------------------
st.divider()
with st.container():
    #st.write("---")
    st.write("&copy; - derechos reservados -  2025 -  Walter Gómez - FullStack Developer - Data Science - Business Intelligence")
    #st.write("##")
    left, right = st.columns(2, gap='small', vertical_alignment="bottom")
    with left:
    #st.write('##')
        st.link_button("Mi LinkedIn", "https://www.linkedin.com/in/walter-gomez-fullstack-developer-datascience-businessintelligence-finanzas-python/")
    with right: 
    #st.write('##') 
        st.link_button("Mi Porfolio", "https://walter-portfolio-animado.netlify.app/")