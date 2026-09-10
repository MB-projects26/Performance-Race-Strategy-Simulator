# Data

`calibration_template.csv` is a simple template retained from the earlier manual-CSV calibration workflow.

The final real-world validation uses FastF1 directly. Running:

```bash
python main.py
```

generates:

```text
real_validation_clean_laps.csv
```

from the cleaned 2024 Austrian Grand Prix timing data.

`real_validation_clean_laps.csv` is generated locally at runtime from FastF1 and is therefore not committed to the repository.
