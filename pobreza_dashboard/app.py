import streamlit as st
import pandas as pd
import plotly.express as px
from scraping_ipe import descargar_datos_pobreza_peru

st.set_page_config(
    page_title="📊 Dashboard de Pobreza en Perú",
    page_icon="📉",
    layout="wide"
)

st.title("📉 Dashboard de Pobreza en Perú (Fuente: Banco Mundial)")

with st.spinner("Descargando y procesando datos..."):
    df = descargar_datos_pobreza_peru()

if df.empty:
    st.error("No se pudieron obtener los datos desde el Banco Mundial.")
else:
    st.success("Datos cargados correctamente ✅")

    # Mostrar tabla
    st.subheader("📋 Datos procesados")
    st.dataframe(df, width="stretch")

    # Gráfico de evolución
    fig = px.line(
        df,
        x="Año",
        y="Pobreza (%)",
        title="Evolución de la pobreza en Perú (línea internacional, 2.15 USD/día)",
        markers=True,
        line_shape="spline"
    )
    fig.update_traces(line_color="#007ACC", marker_color="#FF6B00", marker_size=8)
    fig.update_layout(
        yaxis_title="Porcentaje de población bajo la línea de pobreza",
        xaxis_title="Año",
        template="simple_white"
    )

    st.plotly_chart(fig, use_container_width=True)
