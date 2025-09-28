#  Dashboard de Análisis de Ventas - Streamlit App

Esta aplicación web interactiva fue desarrollada en **Python** utilizando el framework **Streamlit**. Su objetivo es facilitar el análisis de datos de ventas mediante un enfoque visual, intuitivo y técnico, con soporte para modelos de predicción, análisis de productos y exploración de patrones de consumo.

##  Descripción General

La aplicación se estructura en diferentes páginas, cada una con una función específica:

###  Página de Bienvenida

- **Animación inicial** de un fantasma animado acompañado de un mensaje de presentación.
- Un **botón de acceso** permite ingresar a la siguiente pantalla.

###  Pantalla de Acceso

- Muestra una **campana animada**. Al hacer clic sobre ella:
  - Se ilumina una **clave de acceso secreta**.
  - Permite avanzar hacia el dashboard principal.

---

## Página Principal: Dashboard de Análisis de Ventas

El núcleo de la aplicación se encuentra en el dashboard, donde se despliegan distintos módulos de análisis:

### Encabezado de KPIs
- Métricas clave de ventas como:
  - Total de ventas
  - Volumen de productos vendidos
  - Ticket promedio
  - Ventas por canal o región

### Módulos de Análisis

1. **Análisis de Ventas**
   - Evolución temporal
   - Comparativas por períodos

2. **Análisis por Producto**
   - Productos más vendidos
   - Categorías destacadas
   - Rotación de stock

3. **Forecast de Ventas**
   - Predicción de ventas usando modelos:
     - **ARIMA**
     - **VAR**

4. **Estadística Descriptiva - Indicadores Técnicos y Osciladores**
   - Linea de tendencia
   - Stochastic 
   - RSI, MACD, Bollinger Bands aplicados al comportamiento de ventas

5. **Modelado Predictivo y Clustering**
   - **Regresión Lineal**
   - **Regresión Logística**
   - **K-Means Clustering**
   - **Market Basket Analysis**
   - **Predicción de ventas por perfiles de clientes**

---

### Página de Salida

- Muestra una animación y mensaje de despedida.
- Permite finalizar la sesión de análisis de forma elegante.

---

## Tecnologías Utilizadas

- **Python**
- **Streamlit**
- **Pandas / NumPy**
- **Scikit-learn / Statsmodels**
- **Plotly / Matplotlib / Seaborn**
- **ARIMA / VAR Models**
- **ML Algorithms: Regresión, KMeans, MBA**

---

## ▶️ Cómo Ejecutar la Aplicación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/gekko/app-dashboard-ventas
   cd tu_repositorio
