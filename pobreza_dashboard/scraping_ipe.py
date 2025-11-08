# scraping_ipe.py
import io
import zipfile
import requests
import pandas as pd
from typing import Optional


def _download_wb_indicator_csv(indicator_code: str, country_code: str = "PE") -> pd.DataFrame:
    """
    Descarga el ZIP del World Bank para el indicador dado y devuelve el CSV principal como DataFrame.
    Maneja la codificación 'latin1' para evitar UnicodeDecodeError.
    """
    url = f"https://api.worldbank.org/v2/en/indicator/{indicator_code}?downloadformat=csv"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(resp.content))
    # Encontrar el archivo API_*.csv dentro del ZIP
    csv_files = [f for f in z.namelist() if f.startswith("API_") and f.endswith(".csv")]
    if not csv_files:
        raise FileNotFoundError("No se encontró el CSV dentro del ZIP del World Bank.")
    csv_name = csv_files[0]
    with z.open(csv_name) as f:
        df = pd.read_csv(f, skiprows=4, encoding="latin1")
    # Filtrar por país
    df = df[df["Country Code"] == country_code]
    return df


def descargar_datos_pobreza_peru(compute_counts: bool = True) -> pd.DataFrame:
    """
    Retorna DataFrame con columnas:
      - year (int)
      - pov_pct (float)  -> porcentaje de población bajo la línea internacional (SI.POV.DDAY)
      - population (int) -> si compute_counts=True: población total (SP.POP.TOTL)
      - pov_count (float)-> si compute_counts=True: aproximación = pov_pct/100 * population

    Si falla, devuelve DataFrame vacío.
    """
    try:
        # 1) Descargar indicador de pobreza (%)
        df_pov = _download_wb_indicator_csv("SI.POV.DDAY", "PER")
        # 2) Transformar ancho -> largo (years)
        value_cols = [c for c in df_pov.columns if c.isdigit()]
        df_pov_long = df_pov[["Country Name", "Country Code", "Indicator Name", "Indicator Code"] + value_cols]
        df_pov_long = df_pov_long.melt(
            id_vars=["Country Name", "Country Code", "Indicator Name", "Indicator Code"],
            var_name="year",
            value_name="pov_pct"
        )
        df_pov_long = df_pov_long.dropna(subset=["pov_pct"])
        df_pov_long["year"] = df_pov_long["year"].astype(int)
        df_pov_long["pov_pct"] = pd.to_numeric(df_pov_long["pov_pct"], errors="coerce")
        df_pov_long = df_pov_long[["year", "pov_pct"]].sort_values("year").reset_index(drop=True)

        if not compute_counts:
            return df_pov_long

        # 3) Descargar población total y calcular conteos aproximados
        df_pop = _download_wb_indicator_csv("SP.POP.TOTL", "PER")
        pop_value_cols = [c for c in df_pop.columns if c.isdigit()]
        df_pop_long = df_pop[["Country Code"] + pop_value_cols].melt(
            id_vars=["Country Code"], var_name="year", value_name="population"
        )
        df_pop_long = df_pop_long.dropna(subset=["population"])
        df_pop_long["year"] = df_pop_long["year"].astype(int)
        df_pop_long["population"] = pd.to_numeric(df_pop_long["population"], errors="coerce")

        # 4) Merge
        df = pd.merge(df_pov_long, df_pop_long, on="year", how="left")
        df["pov_count"] = (df["pov_pct"] / 100.0) * df["population"]
        # Round for presentation
        df["pov_pct"] = df["pov_pct"].round(3)
        df["pov_count"] = df["pov_count"].round(0)
        return df.reset_index(drop=True)

    except Exception as e:
        # En entornos productivos querrás loggear esto en un logger.
        print("Error descargando o procesando datos del Banco Mundial:", e)
        return pd.DataFrame()
