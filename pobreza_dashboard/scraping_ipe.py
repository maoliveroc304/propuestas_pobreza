import pandas as pd
import wbdata
import datetime

def descargar_datos_pobreza_peru():
    """Descarga datos de pobreza nacional desde el Banco Mundial."""
    indicador = {"SI.POV.DDAY": "Pobreza (%)"}
    pais = "PER"
    inicio = datetime.datetime(2000, 1, 1)
    fin = datetime.datetime.now()

    df = wbdata.get_dataframe(indicador, country=pais, data_date=(inicio, fin), convert_date=True)
    df.reset_index(inplace=True)
    df["Año"] = df["date"].dt.year
    df = df.sort_values("Año")
    df = df[["Año", "Pobreza (%)"]].reset_index(drop=True)
    return df
