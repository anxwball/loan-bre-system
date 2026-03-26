# Loan BRE System

Proyecto personal de evaluacion de solicitudes de prestamos centrado en la implementacion de un **Business Rules Engine (BRE)**.

La base de datos proviene de Kaggle (**Loan Prediction Problem Dataset**), pero el foco actual no es un analisis EDA exhaustivo, sino habilitar un flujo reproducible para construir, probar y comparar versiones del BRE.

---

## Estado del proyecto

| Fase | Estado |
|---|---|
| EDA y preprocesamiento minimo | ✅ Operativo |
| Baseline bootstrap de etiquetas | ✅ Operativo |
| Modelado del dominio BRE | ✅ Operativo |
| Motor de reglas deterministas | ✅ Primera version implementada |
| Tests unitarios | 🔄 Baseline implementado |

---

## Estructura del repositorio

```
loan-bre-system/
├── data/
│   ├── raw/               # Dataset original sin modificar
│   ├── processed/         # Dataset de features limpio (sin loan_status)
│   └── labels/            # Etiquetas historicas para benchmark (latest + versions)
├── graphs/
│   ├── latest/            # Gráficos de la última ejecución (acceso rápido)
│   └── YYYYMMDD_HHMMSS/   # Gráficos versionados por ejecución
├── notebooks/
│   └── eda_analysis.py    # Pipeline de EDA y visualizaciones
├── src/
│   ├── data_loader.py     # Carga, limpieza, split de labels y persistencia
│   ├── loan_application.py # Modelo de dominio para BRE (invariantes + campos derivados)
│   ├── bre_rules.py       # Reglas hard/soft trazables (R01-R11)
│   └── bre_engine.py      # Evaluacion de solicitud -> DecisionResult
├── tests/
│   └── test_bre_engine.py # Tests base del motor BRE
├── pyproject.toml
└── requirements.txt
```

---

## Fase actual: BRE v1 trazable + EDA base

### Fuente de datos

- Dataset: **Loan Prediction Problem Dataset**
- Plataforma: **Kaggle**
- Uso en este proyecto: dataset base para exploración, limpieza y generación de variables iniciales

### Alcance actual

- Incluye: limpieza, estandarizacion de columnas, separacion de etiquetas historicas y visualizacion base reproducible.
- Incluye: baseline bootstrap de `loan_status` para comparacion tecnica inicial del BRE.
- Incluye: evaluacion de una solicitud con salida de decision, score y razones trazables por regla.
- No incluye aun: benchmark por lotes BRE vs labels historicas ni modulo de auditoria persistente.

### Pipeline de datos

El pipeline ejecuta las siguientes etapas en orden:

1. Carga de dataset fuente.
2. Limpieza e imputacion.
3. Estandarizacion de nombres de columnas.
4. Paso de features base (sin derivar decision ni etiquetas).
5. Separacion de etiquetas historicas hacia archivo dedicado.
6. Guardado del dataset de features limpio y versionado local de artefactos.

### Visualizaciones generadas

| Gráfico | Pregunta analítica |
|---|---|
| `loan_approval_distribution.png` | ¿Cómo se distribuyen las aprobaciones y denegaciones? |
| `categorical_vs_target.png` | ¿Cómo se relacionan variables categóricas con el resultado? |
| `numerical_distributions.png` | ¿Cómo se distribuyen las variables numéricas? |
| `correlation_heatmap.png` | ¿Qué tan correlacionadas están las variables numéricas? |
| `loan_to_income_ratio_by_status.png` | ¿Cómo varía el ratio préstamo/ingreso por grupo de resultado? |

### Nota sobre `loan_status`

`loan_status` se mantiene como etiqueta de benchmark historico y se persiste en un archivo separado de las features. Actualmente se permite un baseline bootstrap para acelerar la implementacion del BRE.

Regla de alcance:
- `loan_status` no se usa como input del BRE.
- `loan_status` solo se usa para comparacion y metricas tecnicas.
- El objetivo principal es funcionalidad y trazabilidad del motor de reglas.

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

Cada ejecucion corre el pipeline desde raw, persiste features limpios y luego genera graficos. El merge de etiquetas para graficos supervisados se hace en memoria desde `data/labels/loan_labels_latest.csv`.

---

## Stack

- Python 3.11+
- pandas
- numpy
- matplotlib
- seaborn
- pathlib

---

## Proximos pasos

- Cerrar Issue #1 con baseline bootstrap congelado y documentado.
- Implementar Issue #2: primeras reglas trazables y flujo del motor BRE.
- Incorporar pruebas unitarias para validar escenarios de aprobacion, denegacion y borde.
- Agregar evaluacion por lotes BRE vs baseline bootstrap para comparar versiones de reglas.

---

## Licencia

GNU General Public License v3.0 — ver [LICENSE](LICENSE) para más detalles.
