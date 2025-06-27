# Z-Score Panel Project

Este proyecto construye una base de datos limpia y longitudinal para modelar el riesgo de quiebra utilizando indicadores financieros como el **Z-Score** y el **Z-Logit**.

## Objetivo  
Construir una muestra robusta y comparable de empresas privadas y públicas con información financiera histórica (2019–2023), útil para análisis de riesgo crediticio y modelos predictivos.

## Origen de datos
Los datos fueron extraídos desde **S&P Capital IQ Pro**, aplicando filtros geográficos e industriales.

## Estructura del proyecto

zscore-panel-project/
├── data/ # Archivos CSV originales (sin encabezados limpios)
├── notebooks/ # Notebook principal con análisis y exploración
│ └── exploracion_zscore.ipynb
├── outputs/ # Resultados intermedios y panel limpio (opcional)
├── src/ # Funciones reutilizables
│ └── procesar_zscore.py
└── README.md

## Cómo usarlo
1. Coloca los archivos `.csv` en la carpeta `/data/`.
2. Ejecuta el notebook principal desde `/notebooks/`.
3. Las funciones de limpieza están en `src/procesar_zscore.py`.

## Autor
**Daniel Capitán  Lobato**
[@danielcapitanlobato](https://github.com/danielcapitanlobato)  
*Proyecto personal con fines de realizar una propuesta interna en Élan Zaak.*
