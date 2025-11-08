# modules/indicadores.py
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from scraping_ipe import descargar_datos_pobreza_peru

CACHE_TTL = 60 * 60 * 6  # 6 horas
LOCAL_BACKUP_CSV = "data/pobreza_wb_backup.csv"
LOCAL_BACKUP_XLSX = "data/pobreza_local_ejemplo.xlsx"

@st.cache_data(ttl=CACHE_TTL)
def _get_poverty_wb_cached():
    """Intentar descargar desde World Bank; si falla devuelve DataFrame vacío."""
    try:
        df = descargar_datos_pobreza_peru(compute_counts=True)
        return df
    except Exception:
        return pd.DataFrame()

def _try_load_local_backup():
    """Intentar cargar archivos de respaldo locales (CSV o XLSX)."""
    if os.path.exists(LOCAL_BACKUP_CSV):
        try:
            df = pd.read_csv(LOCAL_BACKUP_CSV)
            # Normalizar nombres de columnas esperadas
            if "year" not in df.columns:
                # aceptar 'Año' u otras variantes
                if "Año" in df.columns:
                    df = df.rename(columns={"Año":"year"})
            return df
        except Exception:
            return pd.DataFrame()
    if os.path.exists(LOCAL_BACKUP_XLSX):
        try:
            df = pd.read_excel(LOCAL_BACKUP_XLSX)
            if "Año" in df.columns and "Pobreza (%)" in df.columns:
                df = df.rename(columns={"Año":"year", "Pobreza (%)":"pov_pct"})
            return df
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def mostrar_indicadores():
    st.header("Indicadores básicos")
    st.markdown("Descarga indicadores oficiales y ofrece una vista rápida de la evolución.")

    df_wb = _get_poverty_wb_cached()

    # Si la descarga falló, intentar backups locales
    if df_wb is None or df_wb.empty:
        st.warning("No se pudo descargar la serie de pobreza desde el Banco Mundial (o la descarga falló).")
        st.info("Puedes subir un archivo de respaldo (CSV/XLSX) con la serie, o usar un backup local si existe.")
        # Intentar cargar backup local
        df_wb = _try_load_local_backup()
        if df_wb is not None and not df_wb.empty:
            st.success("Cargado backup local.")
        else:
            uploaded = st.file_uploader("Sube un CSV/XLSX con columnas [year,pov_pct,population (opcional),pov_count (opcional)]", type=["csv","xlsx","xls"], key="backup_ind")
            if uploaded:
                try:
                    if uploaded.name.lower().endswith(".csv"):
                        df_wb = pd.read_csv(uploaded)
                    else:
                        df_wb = pd.read_excel(uploaded)
                    st.success("Archivo cargado desde UI.")
                except Exception as e:
                    st.error("No se pudo leer el archivo subido.")
                    st.exception(e)
                    return
            else:
                st.info("No hay datos disponibles. Sube un archivo o revisa la conectividad con World Bank.")
                return

    # Ahora df_wb contiene datos para mostrar (si no, se habría retornado arriba)
    # Normalizar nombres (aceptar varias convenciones)
    if "year" not in df_wb.columns and "Año" in df_wb.columns:
        df_wb = df_wb.rename(columns={"Año":"year"})
    if "pov_pct" not in df_wb.columns and "Pobreza (%)" in df_wb.columns:
        df_wb = df_wb.rename(columns={"Pobreza (%)":"pov_pct"})
    if "population" not in df_wb.columns and "population" in df_wb.columns:
        pass  # nothing
    # Try to coerce types safely
    try:
        df_wb["year"] = pd.to_numeric(df_wb["year"], errors="coerce").astype("Int64")
    except Exception:
        pass

    years = sorted(df_wb["year"].dropna().unique().tolist())
    if not years:
        st.error("No hay años válidos en la serie cargada.")
        return

    rango = st.slider("Rango de años", int(min(years)), int(max(years)), (int(min(years)), int(max(years))))
    view = df_wb[(df_wb["year"] >= rango[0]) & (df_wb["year"] <= rango[1])].sort_values("year")

    st.subheader("Pobreza (%) - Serie")
    fig = px.line(view, x="year", y="pov_pct", markers=True, title="Pobreza (% de población) - World Bank (Perú)")
    st.plotly_chart(fig, width="stretch")

    st.subheader("Pobreza - Estimación de personas (si está disponible)")
    if "pov_count" in view.columns:
        fig2 = px.line(view, x="year", y="pov_count", markers=True, title="Personas en pobreza (estimadas)")
        st.plotly_chart(fig2, width="stretch")
    else:
        st.info("No se encontró columna 'pov_count'. Si quieres, sube un CSV que incluya población para calcular conteos.")

    st.markdown("**Tabla de datos**")
    # Friendly rename for display if necessary
    df_display = view.copy()
    rename_map = {}
    if "year" in df_display.columns:
        rename_map["year"] = "Año"
    if "pov_pct" in df_display.columns:
        rename_map["pov_pct"] = "Pobreza (%)"
    if "population" in df_display.columns:
        rename_map["population"] = "Población"
    if "pov_count" in df_display.columns:
        rename_map["pov_count"] = "Personas en pobreza"
    if rename_map:
        df_display = df_display.rename(columns=rename_map)
    st.dataframe(df_display, width="stretch")
