import pandas as pd
import io
import requests
import zipfile

def descargar_datos_pobreza_peru() -> pd.DataFrame:
    """
    Descarga los datos de pobreza (línea internacional de pobreza, 2.15 USD/día)
    del Banco Mundial para Perú y devuelve un DataFrame limpio.
    """
    try:
        url = "https://api.worldbank.org/v2/en/indicator/SI.POV.DDAY?downloadformat=csv"
        r = requests.get(url)
        if r.status_code != 200:
            raise ValueError("Error al descargar datos desde el Banco Mundial.")

        # Extraer el ZIP en memoria
        z = zipfile.ZipFile(io.BytesIO(r.content))

        # Buscar el CSV principal
        csv_name = [f for f in z.namelist() if f.startswith("API_") and f.endswith(".csv")][0]

        # Leer CSV con codificación robusta
        with z.open(csv_name) as f:
            df_all = pd.read_csv(f, skiprows=4, encoding="latin1")

        # Filtrar Perú
        df = df_all[df_all["Country Code"] == "PER"]

        # Transformar formato ancho → largo
        df = df.melt(
            id_vars=["Country Name", "Country Code", "Indicator Name", "Indicator Code"],
            var_name="Año",
            value_name="Pobreza (%)"
        )

        # Limpieza
        df = df.dropna(subset=["Pobreza (%)"])
        df["Año"] = df["Año"].astype(int)
        df = df.sort_values("Año").reset_index(drop=True)
        df["Pobreza (%)"] = df["Pobreza (%)"].round(2)

        return df

    except Exception as e:
        print(f"Error al procesar los datos: {e}")
        return pd.DataFrame()
