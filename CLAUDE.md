# CLAUDE.md — Loan BRE System

> Archivo de contexto automático para Claude Code.
> Actualizar al cerrar cada sesión de trabajo.

---

## 0. Perfil del desarrollador

> Esta sección existe para que Claude adapte explicaciones, decisiones de arquitectura y recomendaciones al contexto real del desarrollador.

- **Rol actual:** Estudiante de Ingeniería en Sistemas, nivel Python básico→intermedio en progreso
- **Camino técnico principal:** FullStack Software Engineering · Network Engineering · Ciberseguridad (Red Team)
- **Camino secundario:** AI/ML · Automatización · Cloud/DevSecOps · Blue Team · Data Science
- **Lenguaje principal:** Python — próximos: JavaScript, Java
- **Certificaciones vigentes:** Cisco NetAcad — Network Technician, Switching/Routing/Wireless Essentials, Enterprise Networking Security & Automation
- **Eje del roadmap de certs:** APIs (IBM API Fundamentals → Postman Student Expert → APIsec → AWS/GCloud → Kong/MuleSoft → TryHackMe Jr Pentester)
- **Meta de portafolio:** API Security Scanner en Python (OWASP API Top 10 + CI/CD)

**Cómo conecta este proyecto con esa meta:**
Este BRE es el proyecto puente. La Fase 4 (FastAPI) produce una API real que luego puede ser objetivo del API Security Scanner — el mismo developer que construye la API aprende a atacarla. Eso es narrativa técnica de portafolio de alto valor.

---

## 1. Identidad del proyecto

**Nombre:** `loan-bre-system`
**Propósito:** Sistema de evaluación de solicitudes de préstamos bancarios mediante un Motor de Reglas de Negocio (BRE) explícito, trazable y extensible, construido sobre el Loan Prediction Problem Dataset de Kaggle.

**Stack tecnológico:**
- Lenguaje: Python 3.11+
- Datos: `pandas 2.2.1`, `numpy 1.26.4`
- Visualización: `matplotlib 3.8.3`, `seaborn 0.13.2`
- Testing: `pytest`
- API (próxima fase): `FastAPI`
- ML (próxima fase): `scikit-learn`
- Empaquetado: `setuptools` con `pip install -e .` (editable install)

**Fase actual:** Prototipo — Fase 1 completada / Fase 2 diseñada, pendiente de implementar

**Posición estratégica:** Fase 4 (API REST) es la fase más importante para el roadmap del desarrollador — no es un bonus, es el objetivo principal del proyecto desde la perspectiva de portafolio.

---

## 2. Arquitectura y módulos

```
loan-bre-system/
├── data/
│   ├── raw/                  # Dataset original Kaggle — NUNCA se modifica
│   └── processed/            # CSVs limpios + gráficas generadas por EDA
├── notebooks/
│   └── eda_analysis.py       # Script EDA ejecutable (no Jupyter)
├── src/
│   ├── __init__.py
│   ├── data_loader.py        # Carga, inspección, limpieza y feature engineering
│   ├── loan_application.py   # Dataclass de entrada del BRE + invariantes de dominio
│   ├── bre_rules.py          # Reglas individuales (hard y soft) + listas HARD_RULES / SOFT_RULES
│   └── bre_engine.py         # Orquestador: evalúa LoanApplication → DecisionResult
├── tests/
│   └── test_bre_engine.py    # Pruebas unitarias de reglas, engine e invariantes
├── pyproject.toml            # Paquete instalable con pip install -e .
├── requirements.txt
├── .gitignore
└── README.md
```

**Relaciones entre módulos:**
```
eda_analysis.py   →  data_loader.py
bre_engine.py     →  bre_rules.py  →  loan_application.py
bre_engine.py     →  loan_application.py
test_bre_engine.py → bre_engine.py, bre_rules.py, loan_application.py
```

**Imports:** siempre desde la raíz del proyecto usando `from src.modulo import ...`.
El proyecto está instalado como paquete editable (`pip install -e .`), por lo que `sys.path.append` está prohibido.

---

## 3. Módulo BRE (Business Rules Engine)

**Patrón de diseño:** Strategy Pattern simplificado — cada regla es una función pura independiente que recibe un `LoanApplication` y retorna un `RuleResult`. El `RuleEngine` las orquesta sin conocer su lógica interna (Open/Closed Principle).

**Cómo se define una regla:**
```python
def rule_nombre(app: LoanApplication) -> RuleResult:
    passed = <condición booleana>
    return RuleResult(
        rule_id="R##",
        name="NombreEnPascalCase",
        passed=passed,
        points=<int>,   # 0 para hard rules; +/- para soft rules
        reason="Texto legible por humanos explicando la decisión"
    )
```

**Cómo se ejecuta una regla:**
1. Agregar la función a `HARD_RULES` o `SOFT_RULES` en `bre_rules.py`.
2. El `RuleEngine.evaluate(app)` las itera automáticamente:
   - Hard rules primero → si `passed is False`, retorna `DecisionResult` de rechazo inmediato con `score=0`.
   - Soft rules después → acumula `points` en `score`.
   - `score >= APPROVAL_THRESHOLD (40)` → aprobado.

**Reglas implementadas:**

| ID  | Nombre | Tipo | Propósito |
|-----|--------|------|-----------|
| R01 | CreditHistoryRequired | Hard | Rechaza si credit_history == 0 |
| R02 | MinimumIncome | Hard | Rechaza si total_income < 2500 |
| R03 | LoanAmountSanity | Hard | Rechaza si loan_amount <= 0 |
| R04 | LowDebtRatio | Soft | +30 pts si loan_to_income_ratio <= 0.35 |
| R05 | ModerateDebtRatio | Soft | +10 pts si ratio entre 0.35 y 0.50 |
| R06 | HighDebtRatio | Soft | -20 pts si ratio > 0.50 |
| R07 | IsMarried | Soft | +15 pts si married == "Yes" |
| R08 | IsGraduate | Soft | +10 pts si education == "Graduate" |
| R09 | IsNotSelfEmployed | Soft | +10 pts si self_employed == "No" |
| R10 | HasNoDependents | Soft | +10 pts si dependents == "0" |
| R11 | LongLoanTerm | Soft | +5 pts si loan_amount_term >= 360 |

**Umbral de aprobación:** `APPROVAL_THRESHOLD = 40` definido en `bre_engine.py`.

---

## 4. Módulo de Auditoría

[PENDIENTE: módulo de auditoría no implementado aún. Diseñar en Fase 3 o antes de exponer la API.]

Decisiones ya tomadas sobre su diseño:
- La trazabilidad ya existe en `DecisionResult.rules_triggered` (lista de `RuleResult`).
- `DecisionResult.summary()` genera output legible por humanos.
- El log persistente (archivo / BD) está pendiente de implementar.

Campos mínimos esperados del registro de auditoría:
```
timestamp, applicant_id, approved, score, hard_rejection,
rules_triggered (JSON), model_version
```

[PENDIENTE: definir destino del log — archivo .jsonl, SQLite, o servicio externo.]

---

## 5. Convenciones de código

**Naming:**
- Archivos y módulos: `snake_case.py`
- Clases: `PascalCase` (`LoanApplication`, `RuleEngine`, `DecisionResult`)
- Funciones y variables: `snake_case`
- Funciones de regla: prefijo `rule_` + nombre descriptivo (`rule_credit_history`)
- IDs de reglas: `R##` con dos dígitos (`R01`, `R11`)
- Constantes: `UPPER_SNAKE_CASE` (`HARD_RULES`, `APPROVAL_THRESHOLD`)
- Columnas del dataset: `snake_case` en minúsculas tras limpieza (`applicantincome` → conservado tal cual del CSV limpio)

**Docstrings:** todas las funciones y clases públicas llevan docstring con Args y Returns.

**Inmutabilidad de datos:** siempre usar `.copy()` antes de modificar un DataFrame. Nunca modificar el original.

**Type hints:** obligatorios en todos los parámetros y retornos de funciones.

**Comentarios de sección:** usar bloques `# === SECCIÓN ===` para separar bloques lógicos dentro de un módulo largo.

**Estructura de carpetas:** respetar la separación `src/` (lógica reutilizable) vs `notebooks/` (scripts ejecutables de análisis).

**Patrones a seguir al generar código nuevo:**
- Nueva regla → función en `bre_rules.py` + agregarla a `HARD_RULES` o `SOFT_RULES`.
- Nueva feature de datos → función en `data_loader.py`, separada de las existentes.
- Nuevo test → clase `TestNombreDelModulo` dentro de `test_bre_engine.py` o nuevo archivo `test_<modulo>.py`.
- Fixtures de pytest para datos de prueba — nunca construir `LoanApplication` inline en múltiples tests.

---

## 6. Reglas para Claude

**NO hacer sin avisar:**
- No renombrar métodos o clases existentes sin notificarlo explícitamente.
- No cambiar `APPROVAL_THRESHOLD` sin preguntar — es una decisión de negocio.
- No reemplazar `@dataclass` por `__init__` manual salvo que haya razón técnica justificada.
- No usar `sys.path.append` — el proyecto usa `pip install -e .`.
- No modificar archivos en `data/raw/`.

**Formato de respuesta preferido:**
- Código completo y ejecutable, nunca fragmentos con `...` que impliquen "completa esto tú".
- Comentarios explicativos en el código cuando se introduce un concepto nuevo (el usuario está en nivel básico de Python).
- Siempre acompañar nuevo código con su test unitario correspondiente.
- Explicar los patrones de diseño usados con nombre técnico + justificación breve.

**Antes de refactorizar:**
- Preguntar explícitamente si el usuario quiere refactorizar o solo agregar funcionalidad.
- Si una refactorización afecta la interfaz pública de un módulo, listar qué archivos se rompen.

**Idioma:**
- Conversación y comentarios de código: **español**.
- Nombres de variables, funciones, clases y archivos: **inglés**.
- Mensajes de commit: **inglés** con formato semántico (`feat:`, `fix:`, `docs:`, `test:`).

**Nivel del usuario:** Python básico → intermedio en progreso. Explicar conceptos nuevos (OOP, patrones, decoradores) cuando aparezcan por primera vez.

---

## 7. Estado actual y próximos pasos

**Funcionando:**
- ✅ Estructura completa del proyecto con empaquetado profesional
- ✅ Pipeline EDA: carga → limpieza → feature engineering → 5 visualizaciones
- ✅ Primer commit y post de LinkedIn publicado (Fase 1)

**Diseñado pero NO implementado (Fase 2):**
- 📐 `LoanApplication` con invariantes de dominio vía `__post_init__`
- 📐 BRE con 3 hard rules + 8 soft rules
- 📐 `RuleEngine` con flujo completo y `DecisionResult` trazable
- 📐 Suite de tests unitarios con fixtures (`pytest tests/ -v`)
- 📐 Archivos diseñados: `src/loan_application.py`, `src/bre_rules.py`, `src/bre_engine.py`, `tests/test_bre_engine.py`

**Pendiente (priorizado):**

1. **Evaluación batch** — correr el BRE sobre todos los registros del dataset limpio y comparar decisiones del motor vs `loan_status` real del CSV.
2. **Módulo de auditoría** — persistir `DecisionResult` en formato `.jsonl` o SQLite.
3. **Fase 3: ML complementario** — modelo `scikit-learn` que asiste al BRE como capa de scoring adicional.
4. **Fase 4: API REST** — exponer `RuleEngine.evaluate()` via `FastAPI`.
5. **Docker** — containerizar la aplicación para el README final.

**Bloqueos / decisiones pendientes:**
- [PENDIENTE: definir si el batch runner vive en `notebooks/` o en un nuevo `src/batch_evaluator.py`]
- [PENDIENTE: decidir destino del log de auditoría — .jsonl local vs SQLite]
- [PENDIENTE: definir si el modelo ML reemplaza soft rules o se suma como R12 con puntuación propia]

---

## 8. Glosario del dominio

| Término | Definición |
|---------|------------|
| **BRE** (Business Rules Engine) | Motor que evalúa reglas de negocio explícitas para tomar una decisión automatizada |
| **Hard Rule** | Regla de rechazo automático e irrevocable; si falla, no se evalúa ninguna regla más |
| **Soft Rule** | Regla que suma o resta puntos al score; el conjunto determina la decisión final |
| **APPROVAL_THRESHOLD** | Puntaje mínimo (40 pts) para aprobar una solicitud tras pasar las hard rules |
| **DecisionResult** | Objeto de salida del BRE con la decisión, score, razón y lista trazable de reglas disparadas |
| **LoanApplication** | Objeto de entrada del BRE con los datos del solicitante validados por invariantes |
| **loan_to_income_ratio** | Monto del préstamo dividido entre el ingreso total del hogar; indicador clave de riesgo |
| **total_income** | Suma de `applicantincome` + `coapplicantincome`; calculado en feature engineering |
| **credit_history** | Campo binario del dataset: 1 = historial positivo, 0 = historial negativo |
| **Auditabilidad** | Capacidad del sistema de reconstruir exactamente por qué se tomó una decisión |
| **Editable install** | `pip install -e .` instala el paquete apuntando al código fuente real para desarrollo |
| **Invariante de dominio** | Condición que debe cumplirse siempre para que un objeto sea válido (validada en `__post_init__`) |

---

## Historial de sesiones

### 2026-03-21
- Se diseñó la arquitectura completa del proyecto en 4 fases y se estableció el stack técnico profesional.
- Se implementó la Fase 1 completa: pipeline EDA con `data_loader.py`, 5 visualizaciones, empaquetado con `pyproject.toml`; primer commit y post de LinkedIn publicados.
- Se diseñó la Fase 2 completa (BRE, reglas, engine, tests) con código listo para implementar, pendiente de ser ejecutada; se crearon historias de usuario, `CLAUDE.md` y se sincronizó el proyecto con el perfil técnico y roadmap de portafolio del desarrollador.

### 2025-03-17
- Se diseñó la arquitectura completa del proyecto en 4 fases y se estableció el stack técnico profesional.
- Se implementó la Fase 1 completa: pipeline EDA con `data_loader.py`, 5 visualizaciones y estructura de proyecto con empaquetado via `pyproject.toml`; usuario realizó primer commit y publicó en LinkedIn.
- Se diseñó la Fase 2 completa (BRE, reglas, engine, tests) con código listo para implementar, pero **pendiente de ser ejecutada** por el usuario.
