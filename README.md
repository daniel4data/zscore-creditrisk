# 📊 Z-Score Credit Risk Modeling

Este proyecto construye una base de datos longitudinal limpia a partir de información financiera histórica (2019–2023) extraída de **S&P Capital IQ Pro**, con el objetivo de evaluar el riesgo de quiebra empresarial utilizando modelos clásicos de **Z-Score** y extensiones como **Z-Logit** (regresión logística).

---

## 🎯 Objetivo

Desarrollar una muestra robusta, trazable y reproducible que sirva como insumo para modelos de riesgo crediticio aplicables a clientes reales, considerando tanto empresas públicas como privadas.

---

## 📁 Estructura del proyecto

zscore-creditrisk/
├── data/ # Archivos originales .csv por año (sin encabezados limpios)
├── notebooks/
│ ├── exploracion_zscore.ipynb # Exploración, validación y cálculos
│ └── archivos_antiguos/ # Notebooks de trabajo previos
├── outputs/ # Resultados intermedios (e.g., panel limpio en formato largo)
├── src/
│ └── procesar_zscore.py # Funciones reutilizables para limpieza y transformación
├── original_xlsx/ # Archivos Excel originales descargados desde CIQ
├── .gitignore # Exclusión de archivos sensibles/pesados
└── README.md # Documentación del proyecto

---

## ⚙️ Procesamiento de datos

1. **Carga de archivos .xlsx sin encabezados** desde Capital IQ Pro.
2. **Renombrado de columnas** con claves IQ + año fiscal.
3. **Conversión de texto a numérico**, manejo de paréntesis contables y etiquetas no numéricas.
4. **Transformación a formato panel largo** (una fila por empresa-año).
5. **Cálculo de ratios financieros clave** para modelos Z-Score:

   - `X1 = Working Capital / Total Assets`
   - `X2 = Retained Earnings / Total Assets`
   - `X3 = EBIT / Total Assets`
   - `X4 = Market Value of Equity / Total Liabilities`
   - `X5 = Sales / Total Assets`

6. **Winsorización de outliers extremos**:
   - `X1` a `X3` y `X5`: método IQR
   - `X4`: percentiles (p1, p99)

7. **Construcción de variable binaria `is_distressed`** como proxy de quiebra, basada en múltiples señales financieras (lógica replicable inspirada en Altman, 2016 y Barboza, 2017).

---

## 📦 Dataset final

- Archivo limpio para modelado: `outputs/zscore_base_modelo.csv`
- Observaciones válidas para entrenamiento: **31,361**
- Periodo cubierto: **2019–2023**
- Empresas públicas y privadas de todo el mundo
- Variables: financieros estandarizados, ratios Z-Score, bandera de distress (`is_distressed`)

---

## 🔍 Variable objetivo: `is_distressed`

Como la base no incluye una columna explícita de quiebra, se construyó una variable binaria utilizando criterios financieros severos.  
Cada condición suma 1 punto:

- Patrimonio contable negativo → `Total Liabilities > Total Assets`
- EBIT / Activos < -0.5
- Retained Earnings / Activos < -1.0
- Working Capital / Activos < -0.2
- Deuda Total / Activos > 1.0
- Intereses > EBIT

**Regla final**:  
Si se cumplen **2 o más condiciones**, entonces `is_distressed = 1`; en caso contrario, `is_distressed = 0`.

Esta estrategia ha sido validada empíricamente y genera una proporción razonable de empresas en distress (~9%).

---

## 📊 Próximos pasos

- Estimar modelo clásico Z-Score (versión lineal de Altman).
- Entrenar modelo Z-Logit con regresión logística.
- Evaluar performance (precisión, recall, ROC, etc.).
- Aplicar modelo a nuevas empresas o periodos posteriores.
- Documentar findings y preparar entregables para consultoría.

---

## 👤 Autor

**Daniel Capitán Lobato**  
[GitHub @daniel4data](https://github.com/daniel4data)  
Proyecto personal desarrollado para uso profesional interno en **Élan Zaak, S.C.**

---