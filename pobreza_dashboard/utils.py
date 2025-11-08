import pandas as pd

def match_columns(df):
    """Normaliza nombres de columnas esperadas en el Excel."""
    cols = {c.lower().strip(): c for c in df.columns}
    mapping = {
        "region": "region",
        "departamento": "region",
        "año": "year",
        "year": "year",
        "nvpov": "nvpov",
        "vpov": "vpov",
        "pov": "pov",
        "epov": "epov"
    }
    new_df = {}
    for k, v in mapping.items():
        if k in cols:
            new_df[v] = df[cols[k]]
    return pd.DataFrame(new_df)

def validate_dataframe(df):
    required = ["region","year","nvpov","vpov","pov","epov"]
    msgs = []
    for r in required:
        if r not in df.columns:
            msgs.append(f"Falta columna: {r}")
    ok = len(msgs) == 0
    return ok, msgs

def peru_total(df):
    total = df.groupby("year")[["nvpov","vpov","pov","epov"]].sum().reset_index()
    total["region"] = "Perú (suma nacional)"
    cols = ["region","year","nvpov","vpov","pov","epov"]
    return total[cols]

def fmt_int(x):
    return f"{int(x):,}".replace(",", ".")
