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
| Persistencia SQLAlchemy Core (Phase 3) | ✅ Implementado y consolidado en `v0.3.0` |
| Capa API FastAPI (Phase 4) | ✅ MVP integrada en `main` (camino a `v0.4.0`) |
| Tests unitarios | ✅ Cobertura modular activa |
| Release publico mas reciente | ✅ `v0.3.0` (Pre-release) |
| Estado actual de `main` | ✅ Integracion API + validacion `pytest` (62/62) |

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
│   ├── api/
│   │   ├── main.py        # App FastAPI y ruteo principal
│   │   ├── dependencies.py # Dependencias DB/JWT y guardas por rol
│   │   ├── routers/       # Endpoints auth, evaluate, audit y analyst
│   │   └── schemas/       # Contratos request/response de API
│   └── db/
│       ├── __init__.py    # Exportes publicos de la capa de persistencia
│       ├── schema.py      # Esquema SQLAlchemy Core (Phase 3)
│       ├── database.py    # Engine y bootstrap de persistencia (Phase 3)
│       └── repositories/  # Repositorios SQL para solicitudes y auditoria
├── tests/
│   ├── test_rule_engine_decisions.py
│   ├── test_bre_rules.py
│   ├── test_loan_application.py
│   ├── test_integral_dataset_flow.py
│   ├── test_batch_evaluator.py
│   ├── test_audit_logger.py
│   ├── test_data_loader.py
│   ├── test_db_repositories.py
│   ├── test_api_auth.py
│   ├── test_api_evaluate.py
│   └── test_api_audit.py
├── pyproject.toml
└── requirements.txt
```

---

## Fase actual en `main`: integracion de Phase 4 (camino a `v0.4.0`)

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
- Incluye: superficie API FastAPI en `src/api/` con endpoints de autenticacion, evaluacion individual/lote y auditoria por roles.
- Incluye: pruebas API dedicadas (`tests/test_api_auth.py`, `tests/test_api_evaluate.py`, `tests/test_api_audit.py`).
- Incluye: estandarizacion de release notes publicos (ES) y contexto interno (EN) alineada a `v0.3.0`.
- Excluye: publicacion formal de `v0.4.0`; el trabajo actual se concentra en hardening y cierre de criterios de release.

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
- `tests/test_db_repositories.py`: validacion de persistencia SQL (repositorios).
- `tests/test_api_auth.py`: autenticacion JWT por rol.
- `tests/test_api_evaluate.py`: evaluacion individual y batch por perfil.
- `tests/test_api_audit.py`: endpoints de auditoria y cola de analista.

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
- FastAPI
- python-jose
- passlib

---

## Proximos pasos

- Ejecutar retiro controlado de wrappers JSONL legacy tras validar estabilidad de la ruta SQL por defecto.
- Endurecer la capa API (auth, contratos y validaciones) y preparar release `v0.4.0`.
- Diseñar una fase ML complementaria a futuro sin romper la trazabilidad del BRE.
- Empaquetar despliegue con Docker y documentacion operativa final.

---

## Licencia

GNU General Public License v3.0 — ver [LICENSE](LICENSE) para más detalles.
