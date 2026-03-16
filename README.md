# Loan BRE System

Sistema de evaluación de solicitudes de préstamos construido alrededor de un **Business Rules Engine (BRE)**. El proyecto está en desarrollo activo y actualmente cubre la fase de exploración y preprocesamiento de datos (EDA).

La base de este trabajo utiliza el dataset de Kaggle **Loan Prediction Problem Dataset**, y el análisis actual está construido sobre esa referencia.

---

## Estado del proyecto

| Fase | Estado |
|---|---|
| EDA y preprocesamiento | ✅ Completo |
| Modelado del dominio BRE | 🔄 En desarrollo |
| Motor de reglas deterministas | 🔄 Pendiente |
| Tests unitarios | 🔄 Pendiente |

---

## Estructura del repositorio

```
loan-bre-system/
├── data/
│   ├── raw/               # Dataset original sin modificar
│   └── processed/         # Datos limpios con feature engineering aplicado
│                          # Incluye versiones por corrida (timestamp)
├── graphs/
│   ├── latest/            # Gráficos de la última corrida (acceso rápido)
│   └── YYYYMMDD_HHMMSS/   # Gráficos versionados por corrida
├── notebooks/
│   └── eda_analysis.py    # Pipeline de EDA y visualizaciones
├── src/
│   └── data_loader.py     # Carga, limpieza, feature engineering y guardado
├── tests/                 # Tests unitarios (pendiente)
├── pyproject.toml
└── requirements.txt
```

---

## Fase actual: EDA

### Fuente de datos

- Dataset: **Loan Prediction Problem Dataset**
- Plataforma: **Kaggle**
- Uso en este proyecto: dataset base para exploración, limpieza y generación de variables iniciales

### Pipeline de datos

El pipeline ejecuta las siguientes etapas en orden:

1. **Carga inteligente**: si ya existe data procesada versionada, la reutiliza directamente sin reprocesar desde el raw.
2. **Inspección**: dimensiones del dataset, tipos de columnas y reporte de valores nulos.
3. **Limpieza**: imputación por moda en variables categóricas, por mediana en numéricas.
4. **Feature engineering**: genera `total_income` (ingreso del solicitante + co-solicitante) y `loan_to_income_ratio` (ratio préstamo/ingreso total).
5. **Guardado con versionado**: guarda tanto una versión `latest` como una versión estampada con timestamp por corrida.
6. **Visualización**: 5 gráficos exportados a `graphs/latest/` y a la carpeta de la corrida activa.

### Visualizaciones generadas

| Gráfico | Pregunta analítica |
|---|---|
| `loan_approval_distribution.png` | ¿Cómo se distribuyen las aprobaciones y denegaciones? |
| `categorical_vs_target.png` | ¿Cómo se relacionan variables categóricas con el resultado? |
| `numerical_distributions.png` | ¿Cómo se distribuyen las variables numéricas? |
| `correlation_heatmap.png` | ¿Qué tan correlacionadas están las variables numéricas? |
| `loan_to_income_ratio_by_status.png` | ¿Cómo varía el ratio préstamo/ingreso por grupo de resultado? |

### Nota sobre `loan_status`

En esta fase, `loan_status` se construye usando `credit_history` como variable proxy (`credit_history == 1 → Approved`). Es una decisión temporal y deliberada: el objetivo del EDA es explorar patrones y calidad del dato, no modelar la decisión final. El estatus determinista completo, basado en múltiples características y reglas de negocio explícitas, será modelado en la fase del BRE.

---

## Instalación

```bash
git clone https://github.com/tu-usuario/loan-bre-system.git
cd loan-bre-system
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Ejecución del EDA

```bash
python notebooks/eda_analysis.py
```

La primera ejecución procesa desde el raw y guarda los artefactos. Las ejecuciones siguientes cargan automáticamente la última versión procesada.

---

## Stack

- Python 3.11+
- pandas
- numpy
- matplotlib
- seaborn
- pathlib

---

## Próximos pasos

- Modelado del dominio del BRE con reglas deterministas y trazables
- Definición del estatus de aprobación basado en múltiples variables
- Tests unitarios del motor de reglas

---

## Licencia

GNU General Public License v3.0 — ver [LICENSE](LICENSE) para más detalles.
