# --------------------------------------------------------
# Function: construir_nombre_col
# Purpose:
# Generate unique, consistent column names combining IQ code, fiscal year and readable label.
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
            return f"{cod_iq}_{year}"
    else:
        return f"UNKNOWN_{col_idx}"

# --------------------------------------------------------
# Function: procesar_archivo
# Purpose:
# Process Capital IQ CSV file: extract headers, clean numerics, rename, add year.
# --------------------------------------------------------
def procesar_archivo(file_path, year, header_row=14):
    import pandas as pd
    with open(file_path) as f:
        for _ in range(header_row): next(f)
        header_1 = [col.strip().replace('"', '') for col in next(f).strip().split(",")]
    df = pd.read_csv(file_path, header=None, skiprows=header_row+1)
    df.columns = header_1
    cols_rename = {col: f"{col}_{year}" for col in df.columns if col.startswith("IQ_") and col != 'IQ_INDUSTRY_CLASSIFICATION'}
    df.rename(columns=cols_rename, inplace=True)
    df['year'] = year
    if "SP_ENTITY_NAME" in df.columns:
        df["SP_ENTITY_NAME"] = (df["SP_ENTITY_NAME"].astype(str)
                                                  .str.replace('""', '"')
                                                  .str.replace(r'^"|"$', '', regex=True)
                                                  .str.strip())
    for col in df.columns:
        if col.startswith("IQ_") and col != 'IQ_INDUSTRY_CLASSIFICATION':
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# --------------------------------------------------------
# Function: transformar_a_formato_largo
# Purpose:
# Convert wide-format panel to long-format for panel analysis
# --------------------------------------------------------
def transformar_a_formato_largo(df_panel):
    import re
    import pandas as pd
    years_detected = sorted({re.search(r'_(\d{4})$', col).group(1) for col in df_panel.columns if re.search(r'_(\d{4})$', col)})
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
    return pd.concat(panel_largo, ignore_index=True)

# --------------------------------------------------------
# Function: filtrar_no_financieras
# Purpose:
# Remove firms classified as Financials from the DataFrame
# --------------------------------------------------------
def filtrar_no_financieras(df, col_industria='IQ_INDUSTRY_CLASSIFICATION'):
    financial_codes = ["Financials"]
    return df[~df[col_industria].str.strip().isin(financial_codes)].copy()

# --------------------------------------------------------
# Function: validar_estructura
# Purpose:
# Check consistency of column structure across all years
# --------------------------------------------------------
def validar_estructura(dfs, base_year=2019):
    base_cols = set(dfs[0].columns)
    for i, df in enumerate(dfs[1:], 1):
        diff = set(df.columns).symmetric_difference(base_cols)
        if diff:
            print(f"⚠️ Year {base_year + i}: different columns: {sorted(diff)}")
        else:
            print(f"✅ Year {base_year + i}: consistent columns")

# --------------------------------------------------------
# Function: construir_is_distressed_proxy
# Purpose:
# Construct distress label based on 6 accounting rules
# --------------------------------------------------------
def construir_is_distressed_proxy(df):
    import numpy as np
    req_cols = ["IQ_TOTAL_ASSETS", "IQ_TOTAL_LIAB", "IQ_EBIT", "IQ_RETAINED_EARNINGS",
                 "IQ_TOTAL_CA", "IQ_TOTAL_CL", "IQ_TOTAL_DEBT", "IQ_INTEREST_EXP"]
    faltantes = [c for c in req_cols if c not in df.columns]
    assert not faltantes, f"Faltan columnas requeridas para la proxy: {faltantes}"
    eps = 1e-9
    ta = df["IQ_TOTAL_ASSETS"].astype(float).fillna(0.0)
    tl = df["IQ_TOTAL_LIAB"].astype(float).fillna(0.0)
    ebit = df["IQ_EBIT"].astype(float).fillna(0.0)
    re = df["IQ_RETAINED_EARNINGS"].astype(float).fillna(0.0)
    ca = df["IQ_TOTAL_CA"].astype(float).fillna(0.0)
    cl = df["IQ_TOTAL_CL"].astype(float).fillna(0.0)
    debt = df["IQ_TOTAL_DEBT"].astype(float).fillna(0.0)
    int_exp = df["IQ_INTEREST_EXP"].astype(float).fillna(0.0)
    flags = np.column_stack([
        (tl > ta),
        (ebit / np.where(ta == 0, eps, ta) < -0.5),
        (re / np.where(ta == 0, eps, ta) < -1.0),
        ((ca - cl) / np.where(ta == 0, eps, ta) < -0.2),
        (debt / np.where(ta == 0, eps, ta) > 1.0),
        (ebit < 0) & (np.abs(int_exp) > np.abs(ebit))
    ])
    return pd.Series((flags.sum(axis=1) >= 2).astype(int), index=df.index, name="is_distressed_proxy")

# --------------------------------------------------------
# Function: construir_etiqueta_tplus1
# Purpose:
# Create y_{t+1} by shifting proxy from year t+1 to t for same firm
# --------------------------------------------------------
def construir_etiqueta_tplus1(df_long):
    assert "SP_ENTITY_ID" in df_long.columns and "year" in df_long.columns
    df = df_long.copy().sort_values(["SP_ENTITY_ID", "year"]).reset_index(drop=True)
    df["proxy_t"] = construir_is_distressed_proxy(df)
    g = df.groupby("SP_ENTITY_ID", sort=False, group_keys=False)
    df["year_next"] = g["year"].shift(-1)
    df["proxy_next"] = g["proxy_t"].shift(-1)
    df["y_tplus1"] = np.where(df["year_next"] == df["year"] + 1, df["proxy_next"], np.nan)
    assert not df.columns.duplicated().any(), "Columnas duplicadas: posible merge incorrecto."
    ok_temporal = df.loc[df["y_tplus1"].notna(), "year_next"].eq(df.loc[df["y_tplus1"].notna(), "year"] + 1).all()
    assert ok_temporal, "y_tplus1 no está estrictamente alineada a year+1."
    return df.drop(columns=["proxy_t", "proxy_next"])

# --------------------------------------------------------
# Function: fit_winsor_limits
# Purpose:
# Percentile-based winsorization thresholds
# --------------------------------------------------------
def fit_winsor_limits(s, lower=0.01, upper=0.99):
    return float(s.quantile(lower)), float(s.quantile(upper))

# --------------------------------------------------------
# Function: fit_winsor_limits_iqr
# Purpose:
# IQR-based robust winsorization thresholds
# --------------------------------------------------------
def fit_winsor_limits_iqr(s, k=1.5):
    q1 = float(s.quantile(0.25)); q3 = float(s.quantile(0.75))
    iqr = q3 - q1
    return q1 - k*iqr, q3 + k*iqr

# --------------------------------------------------------
# Function: apply_winsor
# Purpose:
# Apply winsorization to a Series with given bounds
# --------------------------------------------------------
def apply_winsor(col, lo, hi):
    import numpy as np
    return np.clip(col, lo, hi)

# --------------------------------------------------------
# Function: compute_market_cap
# Purpose:
# Calculate market capitalization (price * shares outstanding)
# --------------------------------------------------------
def compute_market_cap(df):
    mktcap = df['SP_PRICE_CLOSE'] * df['IQ_AVG_BASIC_SHARES_OUT']
    return mktcap.where((mktcap > 0) & np.isfinite(mktcap))

# --------------------------------------------------------
# Function: compute_book_equity
# Purpose:
# Estimate book equity from TOTAL_EQUITY or ASSETS - LIABILITIES
# --------------------------------------------------------
def compute_book_equity(df):
    if 'IQ_TOTAL_EQUITY' in df.columns:
        be = df['IQ_TOTAL_EQUITY']
    else:
        be = df['IQ_TOTAL_ASSETS'] - df['IQ_TOTAL_LIAB']
    return be.where(np.isfinite(be))

# --------------------------------------------------------
# Function: calcular_ratios_zlogit_robusto
# Purpose:
# Compute X1–X5 ratios for logistic Z-Score with robust options
# --------------------------------------------------------
def calcular_ratios_zlogit_robusto(df):
    df = df.copy()
    eps = 1e-9
    wc = df['IQ_TOTAL_CA'] - df['IQ_TOTAL_CL']
    ta = df['IQ_TOTAL_ASSETS'].replace(0, np.nan)
    df['X1'] = wc / ta
    df['X2'] = df['IQ_RETAINED_EARNINGS'] / ta
    df['X3'] = df['IQ_EBIT'] / ta
    mktcap = compute_market_cap(df)
    be = compute_book_equity(df)
    num_x4 = mktcap.fillna(be)
    df['X4'] = num_x4 / df['IQ_TOTAL_LIAB'].replace(0, np.nan)
    df['X5'] = df['IQ_TOTAL_REV'] / ta
    return df

# --------------------------------------------------------
# Function: calcular_is_distressed_robusto
# Purpose:
# Alternative proxy using conservative thresholds
# --------------------------------------------------------
def calcular_is_distressed_robusto(df):
    interest = df['IQ_INTEREST_EXP'].abs()
    ebit = df['IQ_EBIT']
    rules = pd.DataFrame({
        'neg_net_worth': (df['IQ_TOTAL_LIAB'] > df['IQ_TOTAL_ASSETS']),
        'ebit_ta_low'  : (df['IQ_EBIT'] / df['IQ_TOTAL_ASSETS'] < -0.05),
        're_ta_low'    : (df['IQ_RETAINED_EARNINGS'] / df['IQ_TOTAL_ASSETS'] < -0.20),
        'wc_ta_low'    : ((df['IQ_TOTAL_CA'] - df['IQ_TOTAL_CL']) / df['IQ_TOTAL_ASSETS'] < -0.10),
        'lev_high'     : (df['IQ_TOTAL_DEBT'] / df['IQ_TOTAL_ASSETS'] > 0.80),
        'cov_bad'      : ((ebit <= 0) | ((ebit / interest.replace(0, np.nan)) < 1.0)),
    })
    return (rules.sum(axis=1) >= 2).astype(int)
