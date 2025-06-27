# ====================== LIBRERÍAS ====================== #
import pandas as pd


# ====================== FUNCIONES ====================== #

# --------------------------------------------------------
# Función: construir_nombre_col
# Objetivo: generar nombres únicos y consistentes para las columnas,
# combinando código IQ, año fiscal (FY202X o LFY) y nombre legible.
# --------------------------------------------------------

def construir_nombre_col(col, header_0, header_1, header_2, year):
    nombre_legible = header_0[col]  # Ej: "Total Revenue"
    cod = header_1[col]             # Ej: "IQ_TOTAL_REV"
    year_raw = header_2[col]        # Ej: "FY2022", "Latest Fiscal Year", o vacío

    # Normalizamos el año para construir nombres trazables
    if pd.notna(year_raw) and str(year_raw).startswith("FY"):
        year_final = str(year_raw).replace("FY", "")
    elif str(year_raw).strip() == "Latest Fiscal Year":
        year_final = "LFY"  # Le damos un identificador único
    else:
        year_final = str(year)  # Backup: usamos el año pasado como argumento

    # Lógica de construcción del nombre según los casos
    if pd.notna(cod) and year_final:
        return f"{cod}_{year_final}"  # Ej: IQ_TOTAL_REV_2022

    elif pd.notna(cod):
        return str(cod)  # Ej: IQ_ENTITY_ID, sin año porque no varía

    elif pd.notna(nombre_legible):
        return str(nombre_legible).strip()  # Si no hay código IQ pero sí nombre legible

    else:
        return f"col_{col}"  # Último recurso: nombre genérico

# --------------------------------------------------------
# Función: procesar_archivo
# Objetivo: transformar el CSV de Capital IQ en un DataFrame limpio
# Acciones:
# - Extrae encabezados (3 primeras filas)
# - Aplica `construir_nombre_col` a cada columna
# - Detecta y renombra duplicados (_dup1, _dup2, ...)
# - Agrega columna "year"
# --------------------------------------------------------

def procesar_archivo(file_path, year):
    # Cargamos el CSV completo sin encabezado
    df_raw = pd.read_csv(file_path, header=None, low_memory=False)

    # Extraemos los encabezados reales de la estructura CIQ
    header_0 = df_raw.iloc[0]  # Nombre legible (ej: "Total Revenue")
    header_1 = df_raw.iloc[1]  # Código IQ (ej: "IQ_TOTAL_REV")
    header_2 = df_raw.iloc[2]  # Año fiscal o etiqueta dinámica (ej: "FY2022")

    # Renombramos columnas asegurando unicidad
    nuevas_columnas = []
    seen = {}

    for col in df_raw.columns:
        nombre = construir_nombre_col(col, header_0, header_1, header_2, year)
        if nombre in seen:
            seen[nombre] += 1
            nombre = f"{nombre}_dup{seen[nombre]}"
        else:
            seen[nombre] = 0
        nuevas_columnas.append(nombre)

    # Eliminamos las 4 primeras filas (encabezados + metadatos)
    df_limpio = df_raw[4:].copy()
    df_limpio.columns = nuevas_columnas
    df_limpio.reset_index(drop=True, inplace=True)

    # Agregamos columna explícita del año
    df_limpio["year"] = year

    # Limpieza del nombre de entidad si existe
    col_entity = [col for col in df_limpio.columns if "ENTITY_NAME" in col.upper()]
    if col_entity:
        col_name = col_entity[0]
        df_limpio[col_name] = (
        df_limpio[col_name]
        .astype(str)
        .str.replace('""', '"', regex=False)
        .str.replace(r'^"|"$', '', regex=True)  # quita comillas solo al inicio o final
        .str.strip()
    )

    else:
        print(f"⚠️ {year}: No se encontró columna de nombre de entidad.")
    
    print(f"Columnas disponibles en {year}: {df_limpio.columns.tolist()}")

    return df_limpio

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