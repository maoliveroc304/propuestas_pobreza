# modules/indicadores.py
import streamlit as st
import pandas as pd
import plotly.express as px
from scraping_ipe import descargar_datos_pobreza_peru

@st.cache_data(ttl=60*60*6)  # cache 6 horas
def _get_poverty_wb_cached():
    return descargar_datos_pobreza_peru(compute_counts=True)

def mostrar_indicadores():
    st.header("Indicadores básicos")
    st.markdown("Descarga indicadores oficiales y ofrece una vista rápida de la evolución.")

    df_wb = _get_poverty_wb_cached()
    if df_wb.empty:
        st.error("No se pudo descargar la serie de pobreza desde el Banco Mundial.")
        return

    # Selector de rango
    years = df_wb["year"].dropna().astype(int).unique().tolist()
    years = sorted(years)
    if not years:
        st.warning("No hay años disponibles.")
        return
    rango = st.slider("Rango de años", int(min(years)), int(max(years)), (int(min(years)), int(max(years))))

    view = df_wb[(df_wb["year"] >= rango[0]) & (df_wb["year"] <= rango[1])]

    st.subheader("Pobreza - Tasa (%)")
    fig = px.line(view, x="year", y="pov_pct", markers=True, title="Pobreza (% de población) - World Bank (Perú)")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Pobreza - Estimación de personas")
    if "pov_count" in view.columns:
        fig2 = px.line(view, x="year", y="pov_count", markers=True, title="Personas en pobreza (estimadas)")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No se calculó el conteo de personas (falta población).")

    st.markdown("**Tabla de datos**")
    st.dataframe(view.rename(columns={"year":"Año","pov_pct":"Pobreza (%)","population":"Población","pov_count":"Personas en pobreza"}), use_container_width=True)
