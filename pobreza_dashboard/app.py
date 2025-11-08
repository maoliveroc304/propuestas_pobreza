import streamlit as st
import pandas as pd
import plotly.express as px
from scraping_ipe import descargar_datos_pobreza_peru
from utils import match_columns, validate_dataframe, peru_total, fmt_int

st.set_page_config(
    page_title="📊 Plataforma ciudadana de pobreza (Perú)",
    page_icon="📉",
    layout="wide"
)

# --- Estilos ---
st.markdown("""
<style>
:root { --text: #0F172A; --muted:#475569; --brand:#0EA5E9; }
h1, h2, h3 { font-weight: 700; letter-spacing: .2px; }
.section { padding: .6rem 1rem; border-left: 4px solid var(--brand); background: #F8FAFC; margin-bottom: .6rem; }
.kpi { border-radius: 16px; padding: 1rem; border: 1px solid #E2E8F0; background: white; }
.source { color: var(--muted); font-size: .9rem; }
.caption { color: var(--muted); font-size: .85rem; }
hr { border: none; border-top: 1px solid #E2E8F0; margin: .6rem 0; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.title("📊 Plataforma ciudadana")
    st.markdown("""
    Fuente de datos combinada del **Banco Mundial**, **IPE** y **ENAHO–INEI**  
    para analizar la evolución de la pobreza y realizar comparaciones regionales.
    """)
    modo = st.radio("Selecciona fuente de datos:", ["Automático (Banco Mundial)", "Manual (Excel ENAHO–INEI)"])
    st.markdown("---")

# --- Tabs ---
PRESENTACION, DASHBOARD, COMPARADOR = st.tabs([
    "Presentación general",
    "Dashboard de pobreza",
    "Comparador de propuestas"
])

# -----------------------------------------------------------
# TAB 1: Presentación
# -----------------------------------------------------------
with PRESENTACION:
    st.header("📈 Plataforma ciudadana de datos sobre pobreza en el Perú")
    st.markdown("""
    Esta herramienta combina **fuentes oficiales y abiertas** para ofrecer un panorama actualizado sobre la pobreza.  
    Permite explorar indicadores por región, año y nivel de vulnerabilidad.
    """)

# -----------------------------------------------------------
# TAB 2: Dashboard principal
# -----------------------------------------------------------
with DASHBOARD:
    if modo == "Automático (Banco Mundial)":
        st.subheader("Datos de pobreza (Banco Mundial)")
        with st.spinner("Descargando datos oficiales..."):
            try:
                df = descargar_datos_pobreza_peru()
                st.success("Datos descargados correctamente.")

                fig = px.line(df, x="Año", y="Pobreza (%)", title="Evolución de la pobreza – Perú (Banco Mundial)")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)
                st.caption("*Fuente:* Banco Mundial – Indicador SI.POV.DDAY")
            except Exception as e:
                st.error("Error al descargar los datos del Banco Mundial.")
                st.exception(e)

    else:
        st.subheader("Dashboard de pobreza (ENAHO–INEI)")
        uploaded = st.file_uploader("Sube tu Excel (XLSX)", type=["xlsx","xls"])
        if not uploaded:
            st.info("Sube un archivo con las columnas: region, year, nvpov, vpov, pov, epov")
        else:
            try:
                raw = pd.read_excel(uploaded)
                df = match_columns(raw)
                ok, msgs = validate_dataframe(df)
                if not ok:
                    st.error("Archivo inválido.")
                    for m in msgs:
                        st.write("•", m)
                else:
                    if msgs:
                        for m in msgs:
                            st.warning(m)

                    total_pe = peru_total(df)
                    df_all = pd.concat([total_pe, df.copy()], ignore_index=True)
                    regiones = ["Perú (suma nacional)"] + sorted(df['region'].unique().tolist())

                    c1, c2 = st.columns([2,1])
                    region_sel = c1.selectbox("Ámbito", regiones)
                    years = sorted(df['year'].dropna().unique())
                    rango = c2.slider("Años", int(min(years)), int(max(years)), (int(min(years)), int(max(years))))

                    view = total_pe if region_sel == "Perú (suma nacional)" else df[df['region']==region_sel]
                    view = view[(view['year']>=rango[0]) & (view['year']<=rango[1])].sort_values('year')

                    # KPIs
                    last_year = int(view['year'].max())
                    base_year = int(view['year'].min())
                    last_row = view[view['year']==last_year].iloc[0]
                    base_row = view[view['year']==base_year].iloc[0]

                    k1, k2, k3, k4 = st.columns(4)
                    k1.metric("No pobres no vulnerables", fmt_int(last_row['nvpov']), f"Δ {base_year}: {fmt_int(last_row['nvpov']-base_row['nvpov'])}")
                    k2.metric("No pobres vulnerables", fmt_int(last_row['vpov']), f"Δ {base_year}: {fmt_int(last_row['vpov']-base_row['vpov'])}")
                    k3.metric("Pobres", fmt_int(last_row['pov']), f"Δ {base_year}: {fmt_int(last_row['pov']-base_row['pov'])}")
                    k4.metric("Pobreza extrema", fmt_int(last_row['epov']), f"Δ {base_year}: {fmt_int(last_row['epov']-base_row['epov'])}")

                    long = view.melt(id_vars=["year"], value_vars=["nvpov","vpov","pov","epov"],
                                     var_name="variable", value_name="personas")
                    fig = px.line(long, x="year", y="personas", color="variable", markers=True,
                                  title=f"{region_sel}: evolución de pobreza")
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption("*Fuente*: ENAHO – INEI")
            except Exception as e:
                st.error("Error al procesar el archivo.")
                st.exception(e)

# -----------------------------------------------------------
# TAB 3: Comparador de propuestas
# -----------------------------------------------------------
with COMPARADOR:
    st.subheader("Comparador de propuestas (ficticias)")
    st.markdown("""
    **Candidata A – Mariana Quispe (Andes Unido):** meta epov = 0.  
    **Candidato B – Ricardo Navarro (Perú Futuro):** reducir pov a la mitad.
    """)

    uploaded = st.file_uploader("Sube nuevamente tu Excel", type=["xlsx","xls"], key="cmp_uploader")
    if uploaded:
        df2 = pd.read_excel(uploaded)
        df2 = match_columns(df2)
        ok2, msgs2 = validate_dataframe(df2)
        if ok2:
            total_pe2 = peru_total(df2)
            regiones2 = ["Perú (suma nacional)"] + sorted(df2['region'].unique().tolist())
            region_sel2 = st.selectbox("Ámbito", regiones2, key="cmp_region")
            base_view = total_pe2 if region_sel2 == "Perú (suma nacional)" else df2[df2['region']==region_sel2]
            last_year = int(base_view['year'].max())
            base_row = base_view[base_view['year']==last_year].iloc[0]
            target_epov = 0
            target_pov = base_row['pov'] * 0.5

            cA, cB = st.columns(2)
            with cA:
                st.markdown("### Candidata A – epov = 0")
                figA = px.bar(x=["Actual","Meta"], y=[base_row['epov'], target_epov])
                st.plotly_chart(figA, use_container_width=True)
                st.info(f"Brecha: {fmt_int(base_row['epov'])} personas por eliminar pobreza extrema.")
            with cB:
                st.markdown("### Candidato B – reducir pov 50%")
                figB = px.bar(x=["Actual","Meta"], y=[base_row['pov'], target_pov])
                st.plotly_chart(figB, use_container_width=True)
                st.info(f"Brecha: {fmt_int(base_row['pov']-target_pov)} personas por salir de pobreza.")
