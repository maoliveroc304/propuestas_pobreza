import pandas as pd

def descargar_datos_pobreza_peru() -> pd.DataFrame:
    """
    Descarga los datos de pobreza (línea de 2.15 USD/día, SI.POV.DDAY)
    del Banco Mundial para Perú y los devuelve como DataFrame limpio.
    """
    url_csv = "https://api.worldbank.org/v2/en/indicator/SI.POV.DDAY?downloadformat=csv"

    # Descargamos y extraemos el CSV
    df_all = pd.read_csv(
        "https://api.worldbank.org/v2/en/country/PE/indicator/SI.POV.DDAY?downloadformat=csv",
        skiprows=4
    )

    # Limpiamos el DataFrame
    df = df_all[["Country Name", "Country Code", "Indicator Name", "Indicator Code"] +
                [c for c in df_all.columns if c.isdigit()]]
    df = df.melt(id_vars=["Country Name", "Country Code", "Indicator Name", "Indicator Code"],
                 var_name="year", value_name="pobreza")
    df["year"] = df["year"].astype(int)
    df = df[df["Country Code"] == "PER"].dropna(subset=["pobreza"])
    df = df[["year", "pobreza"]].sort_values("year")
    df.reset_index(drop=True, inplace=True)
    return df
