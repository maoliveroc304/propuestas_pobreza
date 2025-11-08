# app.py
import streamlit as st
from modules import indicadores, comparador
import modules.utils as utils

st.set_page_config(page_title="Plataforma Ciudadana - Observatorio de Pobreza", page_icon="📊", layout="wide")

st.sidebar.title("📊 Navegación")
opcion = st.sidebar.radio("Selecciona módulo:", ["Presentación", "Indicadores", "Comparador de propuestas"])

if opcion == "Presentación":
    st.header("Plataforma ciudadana - Observatorio de indicadores")
    st.markdown("""
    Esta plataforma integra **datos oficiales** y **propuestas públicas** para comparar diagnóstico y propuestas.
    - Fuente de indicadores: Banco Mundial (descarga automática).
    - Puedes subir tus propios paneles ENAHO (Excel) para tener comparaciones locales.
    - Las propuestas se guardan en `data/propuestas_candidatos.csv`.
    """)
    st.markdown("**Cómo usar:** selecciona 'Indicadores' para ver series oficiales o 'Comparador de propuestas' para contrastar declaraciones de candidatos con la evidencia.")
elif opcion == "Indicadores":
    indicadores.mostrar_indicadores()
else:
    comparador.mostrar_comparador()
