import streamlit as st
import plotly.express as px
import pandas as pd
from scraping_ipe import descargar_datos_pobreza_peru

st.set_page_config(page_title="Dashboard de Pobreza – Perú", page_icon="📉", layout="wide")

st.title("📉 Dashboard de Pobreza en Perú (Banco Mundial)")

with st.spinner("Descargando y procesando datos..."):
    df = descargar_datos_pobreza_peru()

if df.empty:
    st.error("No se pudieron obtener los datos desde el Banco Mundial.")
else:
    st.success(f"Datos cargados correctamente ({len(df)} registros).")

    st.markdown("""
    **Fuente:** Banco Mundial – Indicador `SI.POV.DDAY`
    <br>Porcentaje de la población que vive con menos de **2.15 USD/día (PPA 2017)**.
    """, unsafe_allow_html=True)

    # Filtro de rango de años
    years = sorted(df["year"].unique())
    min_y, max_y = int(min(years)), int(max(years))
    rango = st.slider("Selecciona el rango de años", min_y, max_y, (min_y, max_y))

    view = df[(df["year"] >= rango[0]) & (df["year"] <= rango[1])]

    fig = px.line(
        view, x="year", y="pobreza",
        markers=True, title="Tendencia de la pobreza extrema en Perú",
        labels={"pobreza": "% población bajo línea de pobreza", "year": "Año"}
    )
    fig.update_layout(margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📊 Datos tabulados")
    st.dataframe(view, use_container_width=True)
