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

The lap-level CSV is not pre-populated in this packaged copy because the raw cleaned rows were generated on the user's local machine and were not uploaded into this chat. The repository therefore does not fabricate or substitute raw observations.
