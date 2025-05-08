# Opereta Use-of-Funds Dashboard – Upgrade Plan  

This document captures the concrete work-plan to turn the current Streamlit model & memo into a *VC-grade financial sandbox*.

---
## Phase 0  • Code Clean-Up & Data Separation (today)
| Item | Deliverable |
|------|-------------|
| **Budget YAML** | Single `budget_data.yaml` with fixed & monthly costs (source of truth). |
| **Pydantic Validation** | Lightweight schema ensuring every YAML entry has a name, amount > 0, and category. |
| **Refactor `UOF.py`** | Load YAML into dicts, remove hard-coded numbers, fail fast on validation errors. |
| **Unit Tests** | `pytest` check: totals equal expected, contingency calc >= 20 % in base case. |

---
## Phase 1  • Revenue & Headcount Modules
* Sidebar inputs for monthly MRR start, growth, churn; sliders for extra engineers / AEs.
* `calculate_cash_flow()` produces month-by-month cash balance, net burn.
* New chart: cash balance & burn-rate lines.

---
## Phase 2  • Scenario Presets & Export Tools
* JSON presets (Base, Stretch, Aggressive).
* Buttons to load a preset & Streamlit `download_button` for CSV / PNG exports.

---
## Phase 3  • Visual Upgrades
* Waterfall chart of raise → spend → contingency.
* Spider sensitivity chart (runway vs two variables).
* Theme toggle (light / dark) matching deck colours.

---
## Phase 4  • Cap Table & KPI Tracker
* Simple pre-/post-money dilution view.
* KPI milestone input grid & heat-map.

---
## Phase 5  • Packaging & Deployment
* `requirements.txt`, `Dockerfile`, GitHub CI with `pytest` + `flake8`.
* Streamlit Cloud link & README instructions.

---
### Timeline & Effort
| Phase | Est. Effort | Target Date |
|-------|-------------|-------------|
| 0 | 0.5 day | **Today** |
| 1 | 1 day | +1 day |
| 2 | 0.5 day | +1.5 days |
| 3 | 0.5 day | +2 days |
| 4 | 0.5 day | +2.5 days |
| 5 | 0.5 day | +3 days |

> We will ship after each phase so investors always have a working, value-add tool. 