# 📊 Z-Score Credit Risk Modeling

Proyecto para **evaluación avanzada de riesgo de quiebra empresarial** mediante modelos clásicos de **Z-Score** y su extensión moderna **Z-Logit** (regresión logística), utilizando información financiera histórica de empresas globales (2019–2023) extraída de **S&P Capital IQ Pro**.

---

## 🎯 Objetivo

Desarrollar un pipeline reproducible y trazable para modelar el **riesgo crediticio corporativo**, generando un scoring robusto y defendible, útil para consultoría financiera, pricing de deuda, benchmarking y análisis de portafolios de crédito.

---

## 🗂️ Estructura del proyecto

zscore-creditrisk/
├── data/ # CSVs originales (por año, sin encabezados limpios)
├── notebooks/
│ ├── exploracion_zscore.ipynb # Notebook principal de procesamiento y modelado
│ └── exploracion_zscore_segmentos.ipynb # (Opcional) Análisis por segmento/industria
│ └── archivos_antiguos/ # Notebooks de trabajo previos
├── outputs/ # Resultados intermedios y finales (panel limpio, modelos, figuras)
│ └── figures/ # Gráficas generadas (exploratorias y de resultados)
├── src/
│ └── procesar_zscore.py # Funciones modulares de limpieza y procesamiento
├── original_xlsx/ # Archivos .xlsx originales descargados desde CIQ
├── .gitignore # Exclusión de archivos sensibles/pesados
└── README.md # Documentación del proyecto


---

## ⚙️ Flujo de procesamiento y modelado

1. **Carga de archivos .xlsx** desde Capital IQ Pro.
2. **Limpieza y renombrado de columnas**: claves IQ + año fiscal.
3. **Conversión de texto a numérico**, manejo de formatos contables y etiquetas no numéricas.
4. **Transformación a formato panel longitudinal** (una fila por empresa-año).
5. **Cálculo de ratios financieros clave** para modelos Z-Score (X1–X5):

   - X1: Working Capital / Total Assets
   - X2: Retained Earnings / Total Assets
   - X3: EBIT / Total Assets
   - X4: Market Value of Equity / Total Liabilities
   - X5: Revenue / Total Assets

6. **Winsorización de outliers extremos**:
   - X1, X2, X3, X5: método IQR
   - X4: percentiles (p1, p99)

7. **Construcción de variable binaria `is_distressed`** como proxy de quiebra, basada en señales financieras graves (criterios replicables según Altman, 2016 y Barboza, 2017).

---

## 📦 Dataset final

- **Archivo principal para modelado:** `outputs/zscore_base_modelo.csv`
- **Observaciones válidas para entrenamiento:** 31,361
- **Periodo cubierto:** 2019–2023
- **Cobertura:** Empresas públicas y privadas, multisectoriales y multinacionales
- **Variables:** Ratios financieros estandarizados, bandera de distress (`is_distressed`), metadatos clave (país, industria, año, tipo de empresa)

---

## 🔍 Variable objetivo: `is_distressed` (proxy de quiebra)

Como la base no incluye una columna explícita de default, se construyó una variable binaria basada en múltiples señales financieras graves. Cada condición suma 1 punto:

- **Patrimonio neto negativo:** `Total Liabilities > Total Assets`
- **EBIT / Activos < -0.5**
- **Retained Earnings / Activos < -1.0**
- **Working Capital / Activos < -0.2**
- **Deuda Total / Activos > 1.0**
- **Intereses > EBIT** (si EBIT < 0)

**Regla de clasificación:**  
Si se cumplen **2 o más condiciones**, entonces `is_distressed = 1`; en caso contrario, `is_distressed = 0`.

Esta estrategia ha sido validada empíricamente y genera una proporción razonable de empresas en distress (~9% del total).

---

## 🧠 Modelado y validación

- **Modelos implementados:**  
  - Z-Score clásico (Altman, versión lineal)
  - Z-Logit (regresión logística binaria)
- **Evaluación de desempeño:**  
  - Precisión, recall, f1-score, curva ROC, AUC-ROC
  - Validación cruzada (5 folds) y análisis de estabilidad
- **Exportación de modelos y resultados:**  
  - Modelos guardados (`.pkl`), probabilidades de distress, clases y categorías de riesgo para cada empresa
- **Análisis segmentado:**  
  - Diagnóstico visual y estadístico de probabilidades de distress por industria, país, tipo de empresa (opcional)
  - Sugerencias para ajustar umbrales de riesgo y criterios de interpretación por segmento

---

## 📈 Próximos pasos y recomendaciones

- Ajustar umbrales de clasificación según percentiles internos por industria o país (evitar cortes universales).
- Incorporar equivalencias a ratings S&P/Moody's usando benchmarks recientes (Altman 2019).
- Aplicar y comparar con “Synthetic Rating/ICR” (Damodaran) para empresas privadas.
- Automatizar el pipeline para scoring masivo de nuevas empresas o portafolios.
- Documentar limitaciones, recomendaciones y posibles mejoras para futuras versiones.

---

## 👤 Autor

**Daniel Capitán Lobato**  
[GitHub @daniel4data](https://github.com/daniel4data)  
Proyecto profesional desarrollado para uso interno y consultoría en **Élan Zaak, S.C.**  
Contacto: danielcapitanlobato [at] gmail [dot] com

---

## 🏷️ Referencias clave

- Altman, E. I. (2016, 2019). “Z-Score Models and Their Applications: A Review.”  
- Barboza, F., Kimura, H., & Altman, E. I. (2017). “Machine learning models and bankruptcy prediction.”
- Damodaran, A. (2023). “Synthetic Ratings & Default Spreads by Country.”

---