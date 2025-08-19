# 📊 Z-Score Credit Risk Modeling

Proyecto de modelado crediticio corporativo basado en los modelos clásicos de **Altman Z-Score**, su versión moderna **Z-Logit** (regresión logística) y un modelo alternativo con **Random Forest**, utilizando información financiera histórica de empresas globales (2019–2023) proveniente de **S&P Capital IQ Pro**.

El objetivo es construir un pipeline automatizado y defendible para evaluar el riesgo de quiebra empresarial, generar un scoring probabilístico y categorizar el riesgo de forma relativa dentro de cada industria.

---

## 🎯 Objetivo

Desarrollar una herramienta robusta y reproducible para evaluar el **riesgo financiero y de default** de empresas multinacionales, útil para:

- Diagnóstico financiero y segmentación de portafolios
- Evaluación de crédito en pricing de deuda o financiamiento
- Benchmarking relativo dentro de sectores
- Reportes ejecutivos y dashboards de riesgo

---

## ⚙️ Flujo del pipeline

1. **Carga de archivos `.xlsx` desde Capital IQ Pro**
2. **Limpieza y estandarización de columnas numéricas por año**
3. **Transformación a formato panel longitudinal**
4. **Cálculo de ratios financieros** (X1–X5, siguiendo Altman):
   - X1: (CA – CL) / Total Assets
   - X2: Retained Earnings / Total Assets
   - X3: EBIT / Total Assets
   - X4: Market Value of Equity / Total Liabilities
   - X5: Revenue / Total Assets
5. **Winsorización robusta de outliers** (IQR o percentiles)
6. **Construcción de variable binaria `is_distressed`** como proxy de quiebra
7. **Modelado con:**
   - `Z-Logit` (regresión logística balanceada)
   - `Random Forest` (con ajuste de umbral óptimo por F1)
8. **Evaluación de métricas**: F1, Precision, Recall, AUC-ROC
9. **Exportación de resultados y modelos**
10. **Análisis por industria y estimación de riesgo relativo**
11. **Generación de dashboards, csvs y artefactos finales**

---

## 🤖 Modelos implementados

### 1. Z-Logit (Regresión logística binaria)
- Variables: X1 a X5
- Estandarización de features
- Balanceo de clases (`class_weight='balanced'`)
- Umbral optimizado por F1-score (≈ 0.55)

### 2. Random Forest
- Variables: X1, X2, X3, X4 (se excluye X5 por ruido)
- Tuning de `max_depth` = 10
- Umbral optimizado por F1-score (≈ 0.65)
- Importancias normalizadas: X2 > X3 > X1 > X4

Ambos modelos son evaluados en test set estratificado y permiten generar archivos de scoring y dashboards.

---

## 🔍 Variable objetivo: `is_distressed`

No se cuenta con una etiqueta explícita de default, por lo que se construyó una variable binaria basada en criterios financieros graves replicables.  
**Si cumple 2 o más condiciones, se considera distressed:**

- Patrimonio neto negativo (`Total Liabilities > Total Assets`)
- EBIT / Activos < -0.5
- Retained Earnings / Activos < -1.0
- Working Capital / Activos < -0.2
- Total Debt / Activos > 1.0
- Intereses > EBIT (si EBIT < 0)

Esta metodología ha sido validada con literatura y genera un ~9% de casos distressed.

---

## 📦 Estructura del repositorio

zscore-creditrisk/
├── data/ # Archivos CSV por año (brutos)
├── notebooks/ # Exploración, modelado y análisis por segmento
│ ├── exploracion_zscore_final.ipynb
│ └── exploracion_zscore_segmentos.ipynb
├── outputs/ # Outputs del pipeline
│ ├── modelo_zlogit.pkl
│ ├── modelo_rf_pipeline.pkl
│ ├── modelo_rf_metadata.json
│ ├── zscore_modelo_resultados.csv
│ ├── zscore_risk_dashboard.csv
│ └── figures/
├── original_xlsx/ # Archivos originales de Capital IQ
├── src/ # Módulos de funciones Python
│ └── procesar_zscore.py
├── .gitignore
└── README.md

---


---

## 📈 Outputs principales

| Archivo                              | Descripción                                                                 |
|--------------------------------------|-----------------------------------------------------------------------------|
| `zscore_modelo_resultados.csv`       | Resultados base con proba, predicción, entidad, año                         |
| `zscore_risk_dashboard.csv`          | Resultado final para dashboards: riesgo relativo, rating consultivo        |
| `modelo_zlogit.pkl`                  | Modelo logístico entrenado                                                 |
| `modelo_rf_pipeline.pkl`             | Pipeline Random Forest entrenado                                           |
| `modelo_rf_metadata.json`            | Metadatos de entrenamiento del Random Forest                               |
| `figures/`                           | Gráficas de métricas, importancias, distribución de probabilidades         |

---

## 🧪 Métricas de evaluación (test set)

| Modelo          | F1 Score (1) | AUC ROC | Threshold óptimo |
|-----------------|--------------|---------|------------------|
| Z-Logit         | ≈ 0.63       | ≈ 0.66  | ≈ 0.55           |
| Random Forest   | ≈ 0.63       | ≈ 0.66  | ≈ 0.65           |

---

## 🧠 Clasificación por industria

El archivo `zscore_risk_dashboard.csv` incluye:

- **Probabilidad de distress (`proba_distress`)**
- **Risk category** relativa: Low / Medium / High
- **Percentil por industria (`industry_percentile`)**
- **Rating consultivo (`estimated_rating`)** tipo S&P (AAA – CCC)

Esto permite segmentar el riesgo de forma contextual, evitando comparaciones sesgadas entre industrias.

---

## 📋 Glosario de columnas clave

| Columna              | Descripción                                                    |
|----------------------|----------------------------------------------------------------|
| SP_ENTITY_NAME       | Nombre de la empresa                                           |
| SP_COUNTRY_NAME      | País                                                           |
| IQ_INDUSTRY_CLASSIFICATION | Industria Capital IQ                                      |
| year                 | Año fiscal analizado                                           |
| X1–X5                | Ratios financieros de entrada                                  |
| is_distressed        | Bandera binaria construida (proxy de quiebra)                 |
| proba_distress       | Probabilidad estimada por modelo                              |
| pred_distress        | Predicción del modelo                                          |
| risk_category        | Riesgo relativo dentro de su industria (Low, Medium, High)    |
| estimated_rating     | Rating consultivo tipo S&P                                     |
| industry_percentile  | Percentil de riesgo de distress relativo dentro de la industria |

---

## 🛠️ Cómo usarlo

1. Carga `zscore_risk_dashboard.csv` en Excel, Power BI, Tableau o tu BI favorito.
2. Segmenta por industria, país o tipo de empresa.
3. Utiliza `risk_category`, `estimated_rating` y `proba_distress` para análisis de riesgo.
4. Puedes cargar los modelos `.pkl` para hacer scoring a nuevos datos.

---

## 📚 Referencias clave

- Altman, E. I. (2016). “Z-Score Models and Their Applications: A Review.”
- Barboza, F., Kimura, H., & Altman, E. I. (2017). “Machine Learning Models and Bankruptcy Prediction.”
- Damodaran, A. (2023). “Synthetic Ratings & Default Spreads by Country.”

---

## 👨‍💻 Autor

**Daniel Capitán Lobato**  
[GitHub @daniel4data](https://github.com/daniel4data)  
Consultor senior en modelación y análisis financiero.  
Este proyecto fue desarrollado como parte del equipo de consultoría en **Élan Zaak, S.C.**

---