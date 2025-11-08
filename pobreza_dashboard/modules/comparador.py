# modules/comparador.py
import os
import io
import pandas as pd
import re
import streamlit as st
import plotly.express as px
from modules.utils import match_columns, validate_dataframe, peru_total, fmt_int
from scraping_ipe import descargar_datos_pobreza_peru

PROPUES_CSV = "data/propuestas_candidatos.csv"
CACHE_TTL = 60 * 60 * 6

@st.cache_data(ttl=CACHE_TTL)
def _load_proposals_from_disk():
    """Intentar cargar CSV de propuestas desde disco (repo)."""
    if not os.path.exists(PROPUES_CSV):
        return pd.DataFrame()
    try:
        # Intentar UTF-8, fallback a latin1
        try:
            df = pd.read_csv(PROPUES_CSV)
        except Exception:
            df = pd.read_csv(PROPUES_CSV, encoding="latin1")
        return df
    except Exception:
        return pd.DataFrame()

def _normalize_proposals(df: pd.DataFrame) -> pd.DataFrame:
    # asegurar columnas mínimas con nombres lowercase
    df = df.rename(columns={c: c.strip() for c in df.columns})
    lowercase = {c: c.lower() for c in df.columns}
    df = df.rename(columns=lowercase)
    expected = ["candidato","partido","tema","propuesta","fuente","fecha"]
    for e in expected:
        if e not in df.columns:
            df[e] = ""
    return df

def mostrar_comparador():
    st.header("Comparador de propuestas")

    # 1) cargar propuestas desde disco (si existe)
    proposals = _load_proposals_from_disk()
    if proposals.empty:
        st.warning("No hay propuestas cargadas en 'data/propuestas_candidatos.csv'. Puedes subir un CSV temporalmente aquí o descargar una plantilla.")
    else:
        proposals = _normalize_proposals(proposals)
        st.subheader("Propuestas cargadas (desde repo)")
        st.dataframe(proposals, width="stretch")

    # Ofrecer plantilla de ejemplo para descargar
    if st.button("Descargar plantilla de propuestas (CSV)"):
        sample = pd.DataFrame({
            "candidato":["Mariana Quispe","Ricardo Navarro"],
            "partido":["Andes Unido","Perú Futuro"],
            "tema":["Pobreza","Pobreza"],
            "propuesta":["Reducir a 0 epov en 5 años","Reducir pov 50% en 8 años"],
            "fuente":["Programa oficial","Declaración pública"],
            "fecha":["2025-09-20","2025-09-25"]
        })
        csv_bytes = sample.to_csv(index=False).encode("utf-8")
        st.download_button("Descargar CSV plantilla", data=csv_bytes, file_name="propuestas_plantilla.csv", mime="text/csv")

    # 2) permitir subida temporal por UI (por si no quieres commitear el CSV)
    uploaded = st.file_uploader("O sube un CSV de propuestas (temporal)", type=["csv"], key="proposals_upl")
    if uploaded:
        try:
            try:
                df_uploaded = pd.read_csv(uploaded)
            except Exception:
                uploaded.seek(0)
                df_uploaded = pd.read_csv(io.TextIOWrapper(uploaded, encoding="latin1"))
            proposals = _normalize_proposals(df_uploaded)
            st.success("Archivo de propuestas cargado desde la UI.")
            st.dataframe(proposals, width="stretch")
        except Exception as e:
            st.error("No se pudo leer el CSV subido.")
            st.exception(e)
            return

    # 3) Mostrar tabla si sigue vacía
    if proposals.empty:
        st.info("Sigue sin propuestas disponibles. Sube un CSV o añade 'data/propuestas_candidatos.csv' al repo.")
    else:
        # continuar con el flujo de comparación
        st.markdown("---")
        st.subheader("Comparación: Pobreza (serie oficial)")

        # Obtener serie oficial (World Bank) con fallback silencioso
        df_wb = descargar_datos_pobreza_peru(compute_counts=True)
        if df_wb is None or df_wb.empty:
            st.error("No se pudo descargar la serie oficial para comparar. Sube un backup o revisa la conectividad.")
            # ofrecer uploader para una serie alternativa
            uploaded_series = st.file_uploader("Sube una serie alternativa (CSV/XLSX) con columnas year,pov_pct[,population]", type=["csv","xlsx","xls"], key="series_upl")
            if uploaded_series:
                try:
                    if uploaded_series.name.lower().endswith(".csv"):
                        df_wb = pd.read_csv(uploaded_series)
                    else:
                        df_wb = pd.read_excel(uploaded_series)
                    st.success("Serie alternativa cargada.")
                except Exception as e:
                    st.error("No se pudo leer la serie alternativa.")
                    st.exception(e)
                    return
            else:
                return

        # normalize df_wb columns
        if "year" not in df_wb.columns and "Año" in df_wb.columns:
            df_wb = df_wb.rename(columns={"Año":"year"})
        if "pov_pct" not in df_wb.columns and "Pobreza (%)" in df_wb.columns:
            df_wb = df_wb.rename(columns={"Pobreza (%)":"pov_pct"})
        if "population" not in df_wb.columns and "Population" in df_wb.columns:
            df_wb = df_wb.rename(columns={"Population":"population"})
        # coerce
        df_wb["year"] = pd.to_numeric(df_wb["year"], errors="coerce").astype("Int64")

        # selector de año (último disponible por defecto)
        years = sorted(df_wb["year"].dropna().unique().tolist())
        if not years:
            st.error("La serie oficial no contiene años válidos.")
            return
        year_sel = st.selectbox("Año de referencia para la comparación", years, index=len(years)-1)

        wb_row = df_wb[df_wb["year"] == year_sel].iloc[0]
        wb_pct = float(wb_row.get("pov_pct", float("nan")))
        population = int(wb_row.get("population", 0)) if not pd.isna(wb_row.get("population", None)) else None
        pov_count = int(wb_row.get("pov_count", 0)) if "pov_count" in wb_row and not pd.isna(wb_row.get("pov_count")) else None

        st.markdown(f"**Situación oficial ({year_sel}):** {wb_pct:.2f}% de la población en pobreza." + (f" ≈ {fmt_int(pov_count)} personas." if pov_count else (" (no hay conteo calculado)" if not population else "")))

        # candidato selector
        candidatos = proposals["candidato"].unique().tolist()
        candidato_sel = st.selectbox("Selecciona un candidato", ["--Seleccionar--"] + candidatos)

        if candidato_sel != "--Seleccionar--":
            prop = proposals[proposals["candidato"] == candidato_sel].iloc[0]
            st.markdown(f"### Propuesta de **{candidato_sel}** ({prop.get('partido','')})")
            st.markdown(f"**Tema:** {prop.get('tema','-')}")
            st.markdown(f"**Propuesta:** {prop.get('propuesta','-')}")
            st.markdown(f"**Fuente:** {prop.get('fuente','-')}  |  **Fecha:** {prop.get('fecha','-')}")

            p_text = str(prop.get("propuesta","")).lower()
            # heurística simple para detectar meta cuantitativa
            m = re.search(r"(\b\d{1,3}(?:\.\d+)?\s?%|\bmitad\b|\b50\b|\breducir\b)", p_text)
            target_pct = None
            if m:
                found = m.group(0)
                if "%" in found:
                    try:
                        target_pct = float(found.replace("%","").strip())
                    except:
                        target_pct = None
                elif "mitad" in found or "50" in found:
                    target_pct = wb_pct * 0.5
                elif "reducir" in found:
                    # no sabemos cuánto reducir; pedir claridad
                    st.info("La propuesta menciona reducir, pero no incluye una cifra clara (porcentaje).")
            else:
                st.info("No se detectó una meta cuantitativa clara en la propuesta. Se requiere especificación para evaluar impacto directo.")

            if target_pct is not None:
                st.success(f"Meta detectada: reducir pobreza a {target_pct:.2f}%")
                fig = px.bar(x=["Oficial","Meta (candidato)"], y=[wb_pct, target_pct], labels={"y":"% pobreza"})
                st.plotly_chart(fig, width="stretch")
                if population:
                    target_count = int((target_pct / 100.0) * population)
                    st.info(f"Meta implicaría ≈ {fmt_int(target_count)} personas por salir de pobreza (si la población se mantiene).")
            else:
                st.info("Sin meta cuantitativa detectable, solo se muestra la propuesta en texto.")
