# modules/utils.py
import unicodedata
import pandas as pd
from typing import Tuple, List

# Sinónimos de columnas
COL_SYNONYMS = {
    "region": ["region", "nombre", "departamento", "dpto", "ambito"],
    "year":   ["anio", "ano", "año", "year", "periodo"],
    "nvpov":  ["nvpov", "no pobres no vulnerables", "no_pobres_no_vulnerables", "nvpov"],
    "vpov":   ["vpov", "no pobres vulnerables", "no_pobres_vulnerables", "vpov"],
    "pov":    ["pov", "pobres", "pobreza", "num pobrez", "pov"],
    "epov":   ["epov", "pobreza extrema", "extrema_pobreza", "epov"]
}
REQUIRED_COLS = ["region", "year", "nvpov", "vpov", "pov", "epov"]


def normalize_str(s: str) -> str:
    s = str(s).strip().lower()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return s


def match_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols_norm = {normalize_str(c): c for c in df.columns}
    mapping = {}
    for target, syns in COL_SYNONYMS.items():
        for s in syns:
            if s in cols_norm:
                mapping[cols_norm[s]] = target
                break
    df2 = df.rename(columns=mapping)
    return df2


def validate_dataframe(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    msgs = []
    ok = True
    for c in REQUIRED_COLS:
        if c not in df.columns:
            ok = False
            msgs.append(f"Falta la columna obligatoria: '{c}'")
    if ok:
        # Validaciones básicas
        try:
            df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')
        except Exception:
            ok = False
            msgs.append("La columna 'year' debe ser numérica (ej. 2019).")
        for c in ["nvpov","vpov","pov","epov"]:
            if c in df.columns:
                try:
                    df[c] = pd.to_numeric(df[c], errors='coerce')
                except Exception:
                    ok = False
                    msgs.append(f"La columna '{c}' debe ser numérica.")
        df['region'] = df['region'].astype(str)
    return ok, msgs


def peru_total(df: pd.DataFrame) -> pd.DataFrame:
    agg = df.groupby('year', as_index=False)[["nvpov","vpov","pov","epov"]].sum()
    agg.insert(0, 'region', 'Perú (suma nacional)')
    return agg


def fmt_int(x) -> str:
    try:
        return f"{int(round(x)):,}".replace(",", ".")
    except Exception:
        return "—"
