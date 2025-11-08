# modules/comparador.py
import streamlit as st
import pandas as pd
import plotly.express as px
from modules.utils import match_columns, validate_dataframe, peru_total, fmt_int
from scraping_ipe import descargar_datos_pobreza_peru

PROPUES_CSV = "data/propuestas_candidatos.csv"

@st.cache_data(ttl=60*60*6)
def _load_proposals():
    try:
        df = pd.read_csv(PROPUES_CSV)
        return df
    except Exception:
        return pd.DataFrame()

def mostrar_comparador():
    st.header("Comparador de propuestas")

    proposals = _load_proposals()
    if proposals.empty:
        st.warning("No hay propuestas cargadas. Crea 'data/propuestas_candidatos.csv' con columnas: candidato, partido, tema, propuesta, fuente, fecha.")
    else:
        st.subheader("Propuestas cargadas")
        st.dataframe(proposals, use_container_width=True)

    st.markdown("---")
    st.subheader("Comparación: Pobreza")

    # Descargar serie oficial
    df_wb = descargar_datos_pobreza_peru(compute_counts=True)
    if df_wb.empty:
        st.error("No se pudo descargar los datos oficiales para comparación.")
        return

    # Candidate selector
    if not proposals.empty:
        candidato = st.selectbox("Selecciona un candidato (para ver su propuesta)", ["--Seleccionar--"] + proposals["candidato"].unique().tolist())
    else:
        candidato = "--Seleccionar--"

    # Upload ENAHO Excel optional to use local numbers
    uploaded = st.file_uploader("(Opcional) Sube tu Excel ENAHO para comparar (2019–2023)", type=["xlsx","xls"])
    df_enaho = None
    if uploaded:
        try:
            raw = pd.read_excel(uploaded)
            df_enaho = match_columns(raw)
            ok, msgs = validate_dataframe(df_enaho)
            if not ok:
                st.error("Archivo ENAHO inválido:")
                for m in msgs: st.write("•", m)
                df_enaho = None
            else:
                st.success("ENAHO cargado y validado.")
        except Exception as e:
            st.error("Error leyendo el archivo ENAHO.")
            st.exception(e)

    # Year for comparison
    years = sorted(df_wb["year"].unique())
    year_sel = st.selectbox("Año de referencia para la comparación", years, index=len(years)-1)

    # Official baseline
    wb_row = df_wb[df_wb["year"] == year_sel].iloc[0]
    wb_pct = wb_row["pov_pct"]
    wb_count = int(wb_row["pov_count"]) if "pov_count" in wb_row and not pd.isna(wb_row["pov_count"]) else None

    st.markdown(f"**Situación oficial ({year_sel}):** {wb_pct:.2f}% de la población en pobreza. " +
                (f"≈ {fmt_int(wb_count)} personas." if wb_count else ""))

    # Show candidate proposal
    if candidato != "--Seleccionar--":
        prop = proposals[proposals["candidato"] == candidato].iloc[0]
        st.markdown(f"### Propuesta de **{candidato}** ({prop.get('partido','sin partido')})")
        st.markdown(f"**Tema:** {prop.get('tema','pobreza')}")
        st.markdown(f"**Propuesta:** {prop.get('propuesta','-')}")
        st.markdown(f"**Fuente:** {prop.get('fuente','-')} - {prop.get('fecha','-')}")

        # Heurística simple: si la propuesta contiene palabras clave, damos una interpretación
        p_text = str(prop.get("propuesta","")).lower()
        if "reducir" in p_text or "mitad" in p_text or "50" in p_text:
            st.info("Meta cuantitativa detectada en la propuesta. Se puede modelar el impacto si se define el plazo.")
        elif "programa" in p_text or "focal" in p_text or "transfer" in p_text:
            st.info("Propuesta programática (transferencias/planes). Requiere presupuesto y diseño para evaluar impacto.")
        else:
            st.info("Propuesta descriptiva. Falta meta cuantitativa para evaluar impacto directo.")

        # Comparison chart: show official vs hypothetical target if candidate states one
        # Simple parse: buscar porcentaje objetivo en el texto
        import re
        m = re.search(r"(\b\d{1,3}(?:\.\d+)?\s?%|\bmitad|\b50\b)", p_text)
        if m:
            found = m.group(0)
            target_pct = None
            if "%" in found:
                target_pct = float(found.replace("%","").strip())
            elif "mitad" in found or "50" in found:
                target_pct = wb_pct * 0.5
            if target_pct is not None:
                st.markdown(f"**Meta detectada:** reducir pobreza a {target_pct:.2f}%")
                fig = px.bar(x=["Oficial","Meta (candidato)"], y=[wb_pct, target_pct], labels={"y":"% pobreza"})
                st.plotly_chart(fig, use_container_width=True)
                if wb_count and target_pct:
                    target_count = int((target_pct/100.0) * wb_row["population"])
                    st.info(f"Meta implicaría ≈ {fmt_int(target_count)} personas por salir de pobreza (si la población se mantiene).")
        else:
            st.info("No se detectó una meta cuantitativa clara en la propuesta. Se requiere especificación para modelar impacto.")

    # If user uploaded ENAHO, show comparison table (ENAHO vs World Bank)
    if df_enaho is not None:
        st.markdown("## Comparación ENAHO (usuario) vs World Bank (oficial)")
        # Aggregate ENAHO to national if needed
        t = peru_total(df_enaho)
        st.dataframe(t.sort_values("year").tail(6), use_container_width=True)
