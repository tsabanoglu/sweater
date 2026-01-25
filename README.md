# Sweater Pattern Generator

I'm a knitter and I enjoy creating things. When knitting a simple top-down raglan sweater, I found myself repeatedly reaching for spreadsheets to convert gauge, calculate increase schedules, and do all the rest of the math logic you typically have to deal with (or worse - do it all in my head and hope everything works out). This project started as an experiment: can the Excel charting workflow for a simple raglan pattern be automated in a modular fashion?

This library generates a complete top-down raglan sweater pattern from gauge and size inputs, producing human-readable instructions for cast-on, yoke shaping, separation, body, and sleeves.

## What it does

Given a stitch gauge, row gauge, and size, the generator calculates:

- **Cast-on stitch count** with marker placement for raglan lines
- **Yoke shaping** with increase rounds spread evenly
- **Back-neck short rows** (optional) for better fit
- **Separation** of body and sleeves with underarm cast-on stitches
- **Body** worked straight from underarm to hem
- **Sleeve shaping** with decreases spread from underarm to cuff

## Quick start

```python
from sweater import Sweater

sw = Sweater(
    sts_per_10cm=22,
    rows_per_10cm=30,
    size="M",
    rib_pref=1,           # 1x1 ribbing
    use_short_rows=True,  # optional back-neck shaping
)

print(sw.render_text())
```

Run the test demo:

```bash
python -m sweater.test
```

## Architecture

The library is organized around immutable plan objects that each handle one stage of the construction:

| Module | Class | Purpose |
|--------|-------|---------|
| `caston.py` | `CastOnPlan` | Neck stitch count and initial marker split |
| `shortrows.py` | `ShortRowPlan` | Back-neck short-row shaping |
| `yokeplan.py` | `YokePlan` | Raglan increase schedule and stitch counts |
| `separator.py` | `SeparatorPlan` | Split body/sleeves, underarm cast-on |
| `bodyplan.py` | `BodyPlan` | Body length and optional waist shaping |
| `sleeveplan.py` | `SleevePlan` | Sleeve decreases from underarm to cuff |

The `Sweater` class in `raglan.py` is the orchestrator that wires these plans together and produces the final pattern via `render_text()`.

Shared numeric helpers (gauge conversions, rounding, spacing) live in `helpers.py`. Size constants (neck and chest circumferences) are defined in `constants.py`.

## Configuration options

The `Sweater` class accepts the following parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `sts_per_10cm` | required | Stitch gauge per 10 cm |
| `rows_per_10cm` | required | Row gauge per 10 cm |
| `size` | required | Size key (XS, S, M, L, XL, XXL, XXXL) |
| `rib_pref` | 1 | Ribbing style: 0=none, 1=1x1, 2=2x2 |
| `body_length_cm` | 40.0 | Body length from underarm to hem |
| `sleeve_length_cm` | 45.0 | Sleeve length from underarm to cuff |
| `use_short_rows` | False | Enable back-neck short-row shaping |
| `short_row_depth_cm` | 5.0 | Depth of short-row section |
| `underarm_cm` | 2.5 | Underarm cast-on width in cm |

## TODO

- [ ] Add positive ease parameter (target range: 6-12 cm for bust)
- [ ] Account for underarm pickup stitches in sleeve construction
- [ ] Knit a test sweater using the generated instructions to validate the pattern
- [ ] Export to PDF or structured format
