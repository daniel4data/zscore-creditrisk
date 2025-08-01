# --------------------------------------------------------
# Function: construir_nombre_col
# Purpose:
# Generate unique, consistent column names combining IQ code, fiscal year and readable label.
# Handles both static and annual columns.
# --------------------------------------------------------

def construir_nombre_col(col_idx, header_0, header_1, header_2, year):
    """
    Generate consistent column names for Capital IQ files.

    Parameters:
        col_idx (int): Column index.
        header_0, header_1, header_2 (list): Header rows.
        year (int or str): Fiscal year.

    Returns:
        str: Unique column name.
    """
    cod_iq = str(header_1[col_idx]).strip()
    anio = str(header_2[col_idx]).strip()

    if cod_iq.startswith("SP_"):
        return cod_iq
    elif cod_iq.startswith("IQ_") and cod_iq != "nan":
        if anio != "nan" and anio != "":
            return f"{cod_iq}_{anio}"
        else:
            return f"{cod_iq}_{year}"  # Always attach year for IQ columns
    else:
        return f"UNKNOWN_{col_idx}"

# --------------------------------------------------------
# Function: procesar_archivo
# Purpose:
# Transform Capital IQ CSV into a clean DataFrame.
# - Extract headers and build unique names
# - Rename duplicates
# - Add year column
# - Clean entity names and convert numerics
# --------------------------------------------------------

def procesar_archivo(file_path, year, header_row=14):
    """
    Process a Capital IQ export file into a clean DataFrame.

    Parameters:
        file_path (str): Path to the CSV file.
        year (int or str): Fiscal year.
        header_row (int): Row number of the main header.

    Returns:
        pd.DataFrame: Cleaned and formatted DataFrame.
    """
    with open(file_path) as f:
        for _ in range(header_row):
            next(f)
        header_1 = [col.strip().replace('"', '') for col in next(f).strip().split(",")]

    df = pd.read_csv(file_path, header=None, skiprows=header_row+1)
    df.columns = header_1

    cols_rename = {}
    for col in df.columns:
        if col.startswith("IQ_") and col not in ['IQ_INDUSTRY_CLASSIFICATION']:
            cols_rename[col] = f"{col}_{year}"
    df = df.rename(columns=cols_rename)

    df['year'] = year

    if "SP_ENTITY_NAME" in df.columns:
        df["SP_ENTITY_NAME"] = (
            df["SP_ENTITY_NAME"].astype(str)
            .str.replace('""', '"')
            .str.replace(r'^"|"$', '', regex=True)
            .str.strip()
        )

    for col in df.columns:
        if col.startswith("IQ_") and col not in ['IQ_INDUSTRY_CLASSIFICATION']:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# --------------------------------------------------------
# Function: transformar_a_formato_largo
# Purpose:
# Convert wide-format DataFrame to long panel, one row per year-entity.
# Useful for multi-year S&P/Capital IQ data.
# --------------------------------------------------------

def transformar_a_formato_largo(df_panel):
    """
    Convert wide panel to long format by extracting year-suffix columns.

    Parameters:
        df_panel (pd.DataFrame): Wide format DataFrame.

    Returns:
        pd.DataFrame: Long-format panel.
    """
    import re

    years_detected = sorted({
        re.search(r'_(\d{4})$', col).group(1)
        for col in df_panel.columns if re.search(r'_(\d{4})$', col)
    })

    panel_largo = []
    for year in years_detected:
        cols_year = [col for col in df_panel.columns if col.endswith(f"_{year}")]
        cols_base = [re.sub(f"_{year}$", "", col) for col in cols_year]
        cols_static = [col for col in df_panel.columns if not re.search(r'_\d{4}$', col)]
        df_tmp = df_panel[cols_static + cols_year].copy()
        df_tmp.dropna(subset=cols_year, how='all', inplace=True)
        df_tmp.rename(columns=dict(zip(cols_year, cols_base)), inplace=True)
        df_tmp["year"] = int(year)
        panel_largo.append(df_tmp)
    df_final = pd.concat(panel_largo, ignore_index=True)
    return df_final

# --------------------------------------------------------
# Function: filtrar_no_financieras
# Purpose:
# Exclude financial sector firms from the DataFrame (e.g., for Z-Score).
# --------------------------------------------------------

def filtrar_no_financieras(df, col_industria='IQ_INDUSTRY_CLASSIFICATION'):
    """
    Remove financial sector companies from the DataFrame.

    Parameters:
        df (pd.DataFrame): Input DataFrame.
        col_industria (str): Name of the industry column.

    Returns:
        pd.DataFrame: Filtered DataFrame (non-financials only).
    """
    financial_codes = ["Financials"]
    return df[~df[col_industria].str.strip().isin(financial_codes)].copy()

# --------------------------------------------------------
# Function: validar_estructura
# Purpose:
# Check that all annual DataFrames have the same columns.
# Prints differences to help debugging.
# --------------------------------------------------------

def validar_estructura(dfs, base_year=2019):
    """
    Check that all DataFrames have the same column structure.

    Parameters:
        dfs (list of pd.DataFrame): List of DataFrames (one per year).
        base_year (int): The base year (for reporting).

    Returns:
        None. Prints inconsistencies.
    """
    base_cols = set(dfs[0].columns)
    for i, df in enumerate(dfs[1:], 1):
        diff = set(df.columns).symmetric_difference(base_cols)
        if diff:
            print(f"⚠️ Year {base_year + i}: different columns: {sorted(diff)}")
        else:
            print(f"✅ Year {base_year + i}: consistent columns")

# --------------------------------------------------------
# Function: detect_outliers_zscore
# Purpose:
# Detect outliers in a numeric column using Z-score method.
# --------------------------------------------------------

from scipy.stats import zscore

def detect_outliers_zscore(df, column, threshold=3):
    """
    Detect outliers in a numeric column using Z-score.

    Parameters:
        df (pd.DataFrame): DataFrame.
        column (str): Numeric column name.
        threshold (float): Z-score cutoff (default: 3).

    Returns:
        pd.DataFrame: Only rows where |z| > threshold.
    """
    df = df.copy()
    z = zscore(df[column].astype(float), nan_policy='omit')
    df["z"] = z
    return df[df["z"].abs() > threshold]

# --------------------------------------------------------
# Function: limpiar_columna_numerica
# Purpose:
# Clean text-formatted numeric columns (remove commas, signs, NA, etc.)
# Converts to float for analysis.
# --------------------------------------------------------

def limpiar_columna_numerica(col):
    """
    Clean up numeric columns imported as text.

    Parameters:
        col (pd.Series): Column with possible symbols or bad data.

    Returns:
        pd.Series: Numeric (float) column.
    """
    col_limpia = (
        col.astype(str)
           .str.replace(",", "", regex=False)
           .str.replace("(", "-", regex=False)
           .str.replace(")", "", regex=False)
           .str.replace(r"\b(NM|NA|--|n/a|N/A)\b", "", regex=True)
           .str.strip()
    )
    return pd.to_numeric(col_limpia.replace("", np.nan), errors="coerce")

# --------------------------------------------------------
# Function: calcular_ratios_zlogit
# Purpose:
# Calculate the five Z-Logit ratios (X1-X5) from financial columns.
# --------------------------------------------------------

def calcular_ratios_zlogit(df):
    """
    Calculate Z-Logit ratios X1-X5 from financial columns.

    Parameters:
        df (pd.DataFrame): DataFrame with financial columns.

    Returns:
        pd.DataFrame: DataFrame with new X1-X5 columns.
    """
    df = df.copy()
    eps = 1e-6

    df["X1"] = (df["IQ_TOTAL_CA"] - df["IQ_TOTAL_CL"]) / (df["IQ_TOTAL_ASSETS"] + eps)
    df["X2"] = df["IQ_RETAINED_EARNINGS"] / (df["IQ_TOTAL_ASSETS"] + eps)
    df["X3"] = df["IQ_EBIT"] / (df["IQ_TOTAL_ASSETS"] + eps)
    df["MARKET_VALUE_EQUITY"] = df["SP_PRICE_CLOSE"] * df["IQ_AVG_BASIC_SHARES_OUT"]
    df["X4"] = df["MARKET_VALUE_EQUITY"] / (df["IQ_TOTAL_LIAB"] + eps)
    df["X5"] = df["IQ_TOTAL_REV"] / (df["IQ_TOTAL_ASSETS"] + eps)

    return df

# --------------------------------------------------------
# Function: winsorize_iqr
# Purpose:
# Winsorize a numeric column based on IQR (k=2.5 by default).
# --------------------------------------------------------

def winsorize_iqr(df, col, k=2.5):
    """
    Winsorize a column using IQR.

    Parameters:
        df (pd.DataFrame): DataFrame.
        col (str): Column to winsorize.
        k (float): Multiplier for IQR (default 2.5).

    Returns:
        pd.DataFrame: DataFrame with winsorized column.
    """
    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - k * iqr
    upper = q3 + k * iqr
    df[col] = df[col].clip(lower, upper)
    print(f"{col}: Winsorized between {lower:.3f} and {upper:.3f}")
    return df

# --------------------------------------------------------
# Function: winsorize_percentiles
# Purpose:
# Winsorize a numeric column between specific percentiles (default 1%–99%).
# --------------------------------------------------------

def winsorize_percentiles(df, col, lower_pct=0.01, upper_pct=0.99):
    """
    Winsorize a column using lower and upper percentiles.

    Parameters:
        df (pd.DataFrame): DataFrame.
        col (str): Column to winsorize.
        lower_pct (float): Lower percentile (default 0.01).
        upper_pct (float): Upper percentile (default 0.99).

    Returns:
        pd.DataFrame: DataFrame with winsorized column.
    """
    lower = df[col].quantile(lower_pct)
    upper = df[col].quantile(upper_pct)
    df.loc[:, col] = df[col].clip(lower, upper)
    print(f"{col}: Winsorized between p{int(lower_pct*100)} = {lower:.3f} and p{int(upper_pct*100)} = {upper:.3f}")
    return df

# --------------------------------------------------------
# Function: calcular_is_distressed
# Purpose:
# Build a binary variable proxy for financial distress (>=2 severe signs).
# --------------------------------------------------------

def calcular_is_distressed(df):
    """
    Create a binary proxy for financial distress (>=2 severe accounting signs).

    Parameters:
        df (pd.DataFrame): DataFrame with required columns.

    Returns:
        pd.Series: Binary column is_distressed (0 or 1).
    """
    score = 0
    score += (df["IQ_TOTAL_LIAB"] > df["IQ_TOTAL_ASSETS"]).astype(int)
    score += (df["IQ_EBIT"] / df["IQ_TOTAL_ASSETS"] < -0.5).astype(int)
    score += (df["IQ_RETAINED_EARNINGS"] / df["IQ_TOTAL_ASSETS"] < -1.0).astype(int)
    score += ((df["IQ_TOTAL_CA"] - df["IQ_TOTAL_CL"]) / df["IQ_TOTAL_ASSETS"] < -0.2).astype(int)
    score += (df["IQ_TOTAL_DEBT"] / df["IQ_TOTAL_ASSETS"] > 1.0).astype(int)
    score += ((df["IQ_INTEREST_EXP"] > df["IQ_EBIT"]) & (df["IQ_EBIT"] < 0)).astype(int)
    return (score >= 2).astype(int)

# --------------------------------------------------------
# Función: categorizar_riesgo_sector
# Objetivo: Generar una categoría de riesgo relativa
# ("Bajo riesgo", "Medio riesgo", "Alto riesgo") para cada
# empresa, comparando su probabilidad de distress individual
# (proba_distress) contra los percentiles internos
# (Mediana y P90) de su propio sector o segmento. Esto
# permite evaluar el riesgo en contexto, no absoluto.
# --------------------------------------------------------

def categorizar_riesgo_sector(row):
    """
    Categorize relative risk within industry using industry percentiles.
    Returns: "Low risk", "Medium risk", "High risk" (in English for consistency).
    """
    try:
        median = row["Median"]
        p90 = row["P90"]
        prob = row["proba_distress"]
        if pd.isna(median) or pd.isna(p90) or pd.isna(prob):
            return np.nan
        if prob < median:
            return "Low risk"
        elif prob < p90:
            return "Medium risk"
        else:
            return "High risk"
    except KeyError:
        # Si los nombres no existen, deja un mensaje útil para debuggear
        raise KeyError(f"Column missing in row: {row.index.tolist()}")

# --------------------------------------------------------
# Función: rating_altman
# Objetivo:
# Asigna un "rating crediticio" estimado según la probabilidad de distress,
# usando cortes basados en Altman (2016) y Damodaran.
# Devuelve escalas: "AAA/AA", "A", "BBB", "BB", "B", "CCC/D".
# --------------------------------------------------------

def rating_altman(prob):
    """
    Assign an estimated credit rating based on Altman/Damodaran probability thresholds.

    Parameters:
        prob (float): Estimated distress probability.

    Returns:
        str: Estimated credit rating ("AAA/AA", "A", "BBB", "BB", "B", "CCC/D") or np.nan if input missing.
    """
    if pd.isna(prob):
        return np.nan
    if prob < 0.02:
        return "AAA/AA"
    elif prob < 0.04:
        return "A"
    elif prob < 0.08:
        return "BBB"
    elif prob < 0.14:
        return "BB"
    elif prob < 0.25:
        return "B"
    else:
        return "CCC/D"


