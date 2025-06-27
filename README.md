# 📊 Z-Score Credit Risk Modeling

Este proyecto construye una base de datos longitudinal limpia a partir de información financiera histórica (2019–2023) extraída de **S&P Capital IQ Pro**, con el objetivo de evaluar el riesgo de quiebra empresarial utilizando modelos clásicos de **Z-Score** y extensiones como **Z-Logit** (regresión logística).

## 🎯 Objetivo
Desarrollar una muestra robusta, trazable y reproducible que sirva como insumo para modelos de riesgo crediticio aplicables a clientes reales, considerando tanto empresas públicas como privadas.

---

## 📁 Estructura del proyecto

zscore-panel-project/
├── data/ # Archivos originales .csv por año (sin encabezados limpios)
├── notebooks/
│ ├── exploracion_zscore.ipynb # Exploración, validación y cálculos
│ └── archivos_antiguos/ # Notebooks de trabajo previos
├── outputs/ # Resultados intermedios (e.g., panel limpio en formato largo)
├── src/
│ └── procesar_zscore.py # Funciones reutilizables para limpieza y transformación
├── .gitignore # Exclusión de archivos sensibles/pesados
└── README.md


---

## ⚙️ Procesamiento de datos

1. **Carga de archivos** desde Capital IQ sin encabezado (formato CIQ raw).
2. **Limpieza y renombrado** de columnas (IQ codes + año fiscal).
3. **Unificación y transformación** a formato longitudinal tipo panel.
4. **Conversión de texto a numérico**: manejo de comas, paréntesis contables, etiquetas no numéricas.
5. **Cálculo de ratios clave** para modelos Z-Score:

   - Working Capital / Total Assets
   - Retained Earnings / Total Assets
   - EBIT / Total Assets
   - Sales / Total Assets

6. **Eliminación de outliers extremos** y observaciones sin datos relevantes.

---

## 📦 Dataset final

- Archivo limpio: `outputs/panel_zscore_largo.csv`
- Registros válidos para modelado Z-Score: **64,722**
- Período: **2019–2023**
- Variables: financieros estandarizados + ratios calculados

---

## 📊 Próximos pasos

- Estimación del modelo clásico Z-Score
- Construcción del modelo Z-Logit con regresión logística
- Evaluación de performance y validación cruzada
- Generación de scores para empresas actuales

---

## 👤 Autor

**Daniel Capitán Lobato**  
[GitHub @daniel4data](https://github.com/daniel4data)  
Proyecto personal para propuesta interna en **Élan Zaak, S.C.**

---
