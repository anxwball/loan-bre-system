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
| Evaluacion por lotes BRE vs baseline | ✅ Operativo |
| Auditoria JSONL + rendimiento de archivos | ✅ Operativo |
| Persistencia SQLAlchemy Core (Phase 4b) | ✅ Implementado y consolidado en `v0.3.0` |
| Tests unitarios | ✅ Cobertura modular activa |
| Release publico actual (`main`) | ✅ `v0.3.0` (Pre-release) |

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
│   ├── bre_engine.py      # Evaluacion de solicitud -> DecisionResult
│   ├── batch_evaluator.py # Evaluacion por lotes BRE vs baseline historico
│   ├── audit_logger.py    # Persistencia JSONL para decisiones y lotes
│   └── db/
│       ├── __init__.py    # Exportes publicos de la capa de persistencia
│       ├── schema.py      # Esquema SQLAlchemy Core (Phase 4b)
│       ├── database.py    # Engine y bootstrap de persistencia (Phase 4b)
│       └── repositories/  # Repositorios SQL para solicitudes y auditoria
├── tests/
│   ├── test_rule_engine_decisions.py
│   ├── test_bre_rules.py
│   ├── test_loan_application.py
│   ├── test_integral_dataset_flow.py
│   ├── test_batch_evaluator.py
│   ├── test_audit_logger.py
│   ├── test_data_loader.py
│   └── test_db_repositories.py
├── pyproject.toml
└── requirements.txt
```

---

## Fase actual en `main`: cierre `v0.3.0` (Phase 4b)

### Fuente de datos

- Dataset: **Loan Prediction Problem Dataset**
- Plataforma: **Kaggle**
- Uso en este proyecto: dataset base para exploración, limpieza y generación de variables iniciales

### Alcance actual

- Incluye: limpieza, estandarizacion de columnas, separacion de etiquetas historicas y visualizacion base reproducible.
- Incluye: baseline bootstrap de `loan_status` para comparacion tecnica inicial del BRE.
- Incluye: evaluacion de una solicitud con salida de decision, score y razones trazables por regla.
- Incluye: benchmark por lotes BRE vs labels historicas con CSV de comparacion y resumen agregado.
- Incluye: auditoria persistente JSONL para decisiones y ejecuciones por lotes.
- Incluye: logging de rendimiento de procesamiento de archivos (batch y pipeline).
- Incluye: capa de persistencia SQLAlchemy Core (schema, engine y repositories) estabilizada en `main`.
- Incluye: estandarizacion de release notes publicos (ES) y contexto interno (EN) alineada a `v0.3.0`.
- Excluye: superficie API FastAPI de `v0.4.0`, que sigue en desarrollo fuera de este baseline.

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

## Ejecucion de pruebas

```bash
pytest -v
```

Estructura de pruebas actual:

- `tests/test_rule_engine_decisions.py`: flujo de decision (aprobacion, denegacion y casos borde).
- `tests/test_bre_rules.py`: reglas atomicas hard y soft.
- `tests/test_loan_application.py`: invariantes del dominio.
- `tests/test_integral_dataset_flow.py`: test integral usando `data/processed/loans_cleaned.csv` como entrada.
- `tests/test_batch_evaluator.py`: metricas de lote, salida CSV, auditoria JSONL y rendimiento.
- `tests/test_audit_logger.py`: persistencia JSONL y utilidades de path versionado.
- `tests/test_data_loader.py`: logging de rendimiento de archivos en `run_pipeline`.

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
- SQLAlchemy

---

## Proximos pasos

- Ejecutar retiro controlado de wrappers JSONL legacy tras validar estabilidad de la ruta SQL por defecto.
- Implementar capa API (FastAPI) para exponer evaluacion individual y batch.
- Diseñar la fase ML complementaria sin romper la trazabilidad del BRE.
- Empaquetar despliegue con Docker y documentacion operativa final.

---

## Licencia

GNU General Public License v3.0 — ver [LICENSE](LICENSE) para más detalles.
