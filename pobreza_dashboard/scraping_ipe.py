import pandas as pd
import io
import requests
import zipfile

def descargar_datos_pobreza_peru() -> pd.DataFrame:
    """
    Descarga los datos de pobreza (línea de 2.15 USD/día, SI.POV.DDAY)
    del Banco Mundial para Perú y los devuelve como DataFrame limpio.
    """

    # URL de descarga (ZIP que contiene los CSV)
    url = "https://api.worldbank.org/v2/en/indicator/SI.POV.DDAY?downloadformat=csv"

    # Descarga el archivo ZIP
    r = requests.get(url)
    if r.status_code != 200:
        raise ValueError("Error al descargar los datos del Banco Mundial.")

    # Extraemos el ZIP en memoria
    z = zipfile.ZipFile(io.BytesIO(r.content))

    # Buscamos el archivo principal (generalmente el que empieza con "API_")
    csv_name = [f for f in z.namelist() if f.startswith("API_") and f.endswith(".csv")][0]

    # Leemos el CSV con codificación correcta
    with z.open(csv_name) as f:
        df_all = pd.read_csv(f, skiprows=4, encoding="latin1")

    # Filtramos Perú
    df = df_all[df_all["Country Code"] == "PER"]

    # Reformateamos columnas
    df = df.melt(
        id_vars=["Country Name", "Country Code", "Indicator Name", "Indicator Code"],
        var_name="year",
        value_name="pobreza"
    )

    # Limpieza final
    df = df.dropna(subset=["pobreza"])
    df["year"] = df["year"].astype(int)
    df = df[["year", "pobreza"]].sort_values("year").reset_index(drop=True)

    return df
