# Repo overview & quick start

- **Purpose**: This small library generates top-down raglan sweater knitting plans (cast-on, yoke, separation, body, sleeves, optional short-rows) and renders a human-readable pattern via `Sweater.render_text()`.
- **Entry points**: instantiate `Sweater` in `raglan.py` or use plan classes directly: `CastOnPlan`, `YokePlan`, `SeparatorPlan`, `BodyPlan`, `SleevePlan`, `ShortRowPlan`.
- **Run tests / quick demo**: `python -m sweater.test` (calls the sample functions in `test.py`).

# Architecture & data flow (what to know quickly)

- **Orchestrator**: `raglan.Sweater` is the facade that wires the pipeline. It:
  - builds a `CastOnPlan` (neck + initial split),
  - builds a `YokePlan` from the split,
  - builds a `SeparatorPlan` to split body vs sleeves,
  - builds `BodyPlan` and `SleevePlan` from the separator output,
  - optionally creates a `ShortRowPlan` when `use_short_rows=True`.
- **Helpers & units**: `helpers.py` centralizes numeric helpers and conversions (cm↔rows, cm↔sts). Most functions expect/return integers; pay attention to rounding rules (`cm_to_rows`, `_even`, `_round_to_multiple`).
- **Conventions**:
  - Sizes keyed in `constants.py` (`NECK_SIZES`, `CHEST_SIZES`).
  - Gauge commonly provided as `sts_per_10cm` / `rows_per_10cm`; classes expose per-cm properties (`gauge_sts_per_cm`, `gauge_rows_per_cm`).
  - Plans are lightweight frozen dataclasses (immutable after creation) used as pure data + convenience methods like `summary()` or `stitch_map_at_separation()`.

# Project-specific patterns & examples

- Use plan objects as immutable data carriers. Example: to preview separation use:
  ```python
  sw = Sweater(22, 18, 'M')
  parts = sw.build()
  sep: SeparatorPlan = parts['separator']
  print(sep.summary())
  ```
- Short-row flow: `Sweater.build()` orchestrates short-row calculation using `calculate_short_rows()` from `helpers.py` (single source of truth). It computes the initial split, then passes pre-computed values to `CastOnPlan` (which is now a simple data holder). `ShortRowPlan` also uses `calculate_short_rows()` internally for consistency.
- Terminology: "rounds" for circular knitting (increase rounds, dec rounds), "rows" for short rows (worked flat). `short_row_count` returns individual rows (not RS/WS pairs).
- Scheduling booleans: several components produce boolean schedules (e.g. `_schedule`, `SleevePlan.schedule_rows()`); new shaping logic should emit the same boolean list format (index -> whether that row is an inc/dec).

# Developer workflows

- Quick run: `python -m sweater.test` prints sample patterns. Use `print(Sweater(...).render_text())` to inspect output.
- There are no external dependencies; normal dev flow is edit → run `python -m sweater.test` to sanity-check changes.

# When modifying code — rules for AI agents

- Keep public dataclass fields and constructor signatures stable where possible. Many modules instantiate plans by name.
- Follow the helper functions in `helpers.py` for rounding and spacing. Reuse `_even`, `_evenly_spaced_rows`, `_schedule` rather than reimplementing spacing logic.
- Maintain units: accept gauges as per-10cm where existing classes expect them; use provided per-cm properties for calculations.
- Tests / demos are in `test.py`; keep printed summaries stable (avoid changing `render_text()` line formats unless updating tests).

# Files to reference when coding

- `raglan.py` — orchestrator / `Sweater` API, short-row orchestration, and `render_text()` output.
- `caston.py` — data holder for neck stitch count and marker split.
- `helpers.py` — shared numeric helpers, conversions, and `calculate_short_rows()` (single source of truth for short-row count).
- `shortrows.py` — `ShortRowPlan` for generating short-row turn positions and instructions.
- `separator.py`, `yokeplan.py`, `sleeveplan.py`, `bodyplan.py` — plan data structures and formatting helpers.
- `sample_output.txt` — generated sample pattern output (run `python -m sweater.test` to regenerate).

# Safety notes

- Inputs are sometimes asserted (e.g. `_split_neck`), and several helpers raise `ValueError` on invalid gauge/length. Preserve those guards.
- Avoid changing public names or expected dict keys returned by methods like `stitch_map_at_separation()` and `build()` since other parts rely on them.
