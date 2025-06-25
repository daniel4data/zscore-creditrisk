import pandas as pd

def construir_nombre_col(col, header_0, header_1, header_2):
    cod = header_1[col]
    anio = header_2[col]
    nombre_legible = header_0[col]

    if pd.notna(cod) and pd.notna(anio):
        anio_limpio = str(anio).replace("FY", "")
        return f"{cod}_{anio_limpio}"
    elif pd.notna(cod):
        return str(cod)
    elif pd.notna(nombre_legible):
        return str(nombre_legible).strip()
    else:
        return f"col_{col}"

def procesar_archivo(file_path, anio):
    df_raw = pd.read_csv(file_path, header=None)

    header_0 = df_raw.iloc[0]
    header_1 = df_raw.iloc[1]
    header_2 = df_raw.iloc[2]

    nuevas_columnas = [
        construir_nombre_col(col, header_0, header_1, header_2)
        for col in df_raw.columns
    ]

    df_limpio = df_raw[4:].copy()
    df_limpio.columns = nuevas_columnas
    df_limpio.reset_index(drop=True, inplace=True)
    df_limpio["anio"] = anio

    return df_limpio