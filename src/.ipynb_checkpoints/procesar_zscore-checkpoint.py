# ====================== LIBRERÍAS ====================== #
import pandas as pd

# ====================== FUNCIONES ====================== #

# --------------------------------------------------------
# Función: construir_nombre_col
# Objetivo: generar nombres únicos y consistentes para las columnas,
# combinando código IQ, año fiscal (FY202X o LFY) y nombre legible.
# --------------------------------------------------------

def construir_nombre_col(col_idx, header_0, header_1, header_2, year):
    cod_iq = str(header_1[col_idx]).strip()
    anio = str(header_2[col_idx]).strip()

    if cod_iq.startswith("SP_"):
        return cod_iq
    elif cod_iq.startswith("IQ_") and cod_iq != "nan":
        if anio != "nan" and anio != "":
            return f"{cod_iq}_{anio}"
        else:
            return f"{cod_iq}_{year}"  # SIEMPRE lleva el año
    else:
        return f"UNKNOWN_{col_idx}"

# --------------------------------------------------------
# Función: procesar_archivo
# Objetivo: transformar el CSV de Capital IQ en un DataFrame limpio
# Acciones:
# - Extrae encabezados (3 primeras filas)
# - Aplica construir_nombre_col a cada columna
# - Detecta y renombra duplicados (_dup1, _dup2, ...)
# - Agrega columna "year"
# --------------------------------------------------------

def procesar_archivo(file_path, year, header_row=14):
    import pandas as pd

    # Leer encabezados IQ (línea 14)
    with open(file_path) as f:
        for _ in range(header_row):
            next(f)
        header_1 = [col.strip().replace('"', '') for col in next(f).strip().split(",")]

    # Leer los datos reales (línea 15 en adelante)
    df = pd.read_csv(file_path, header=None, skiprows=header_row+1)
    df.columns = header_1

    # Renombrar columnas con año, excepto las columnas estáticas
    cols_rename = {}
    for col in df.columns:
        if col.startswith("IQ_") and col not in ['IQ_INDUSTRY_CLASSIFICATION']:
            cols_rename[col] = f"{col}_{year}"
    df = df.rename(columns=cols_rename)

    # Agrega la columna de año
    df['year'] = year

    # Limpieza opcional de nombre de entidad
    if "SP_ENTITY_NAME" in df.columns:
        df["SP_ENTITY_NAME"] = df["SP_ENTITY_NAME"].astype(str).str.replace('""', '"').str.replace(r'^"|"$', '', regex=True).str.strip()

    # Conversión de columnas numéricas
    for col in df.columns:
        if col.startswith("IQ_") and col not in ['IQ_INDUSTRY_CLASSIFICATION']:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# --------------------------------------------------------
# Función: transformar_a_formato_largo
# Objetivo: convertir columnas anuales en un panel tipo largo
# - Detecta columnas con sufijos de año (_2020, _2021, ...)
# - Renombra quitando el sufijo
# - Agrega columna "year"
# --------------------------------------------------------

def transformar_a_formato_largo(df_panel):
    import re

    # Detectamos los años presentes en los nombres de columnas (e.g., _2021)
    years_detected = sorted({
        re.search(r'_(\d{4})$', col).group(1)
        for col in df_panel.columns if re.search(r'_(\d{4})$', col)
    })

    panel_largo = []

    for year in years_detected:
        # Columnas específicas de ese año
        cols_year = [col for col in df_panel.columns if col.endswith(f"_{year}")]
        cols_base = [re.sub(f"_{year}$", "", col) for col in cols_year]

        # Columnas que no cambian por año (ej. ID, país, tipo empresa)
        cols_static = [col for col in df_panel.columns if not re.search(r'_\d{4}$', col)]

        # Construimos DataFrame del año
        df_tmp = df_panel[cols_static + cols_year].copy()

        # Eliminamos filas vacías solo si todas las columnas anuales están vacías
        df_tmp.dropna(subset=cols_year, how='all', inplace=True)

        df_tmp.rename(columns=dict(zip(cols_year, cols_base)), inplace=True)
        df_tmp["year"] = int(year)

        panel_largo.append(df_tmp)

    # Unimos todos los años
    df_final = pd.concat(panel_largo, ignore_index=True)
    return df_final

# --------------------------------------------------------
# Función: validar_estructura
# Objetivo: verificar que todos los DataFrames anuales tienen 
# las mismas columnas (estructura homogénea)
# - Compara columnas del año base con el resto
# - Imprime diferencias si las hay
# --------------------------------------------------------

def validar_estructura(dfs, base_year=2019):
    base_cols = set(dfs[0].columns)
    for i, df in enumerate(dfs[1:], 1):
        diff = set(df.columns).symmetric_difference(base_cols)
        if diff:
            print(f"⚠️ Año {base_year + i}: columnas diferentes: {sorted(diff)}")
        else:
            print(f"✅ Año {base_year + i}: columnas consistentes")

from scipy.stats import zscore

# --------------------------------------------------------
# Función: detectar_outliers_zscore
# Objetivo: detectar outliers en una columna numérica mediante Z-score
# - Convierte la columna a float
# - Calcula el Z-score (ignora NaNs)
# - Devuelve solo las filas con |z| > threshold
# --------------------------------------------------------

def detectar_outliers_zscore(df, columna, threshold=3):
    """
    Detecta outliers en una columna numérica usando Z-score.
    
    Parámetros:
    - df: DataFrame de entrada
    - columna: nombre de la columna numérica
    - threshold: valor absoluto del Z-score a partir del cual se considera outlier (default: 3)

    Retorna:
    - DataFrame con solo las filas que son outliers
    """
    df = df.copy()
    z = zscore(df[columna].astype(float), nan_policy='omit')
    df["z"] = z
    return df[df["z"].abs() > threshold]

