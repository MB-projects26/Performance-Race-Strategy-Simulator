# Development History

This directory preserves **all 30 local Python development files** created before the project was packaged into its current modular GitHub form.

## Important context

The Git repository was created after the simulator had already been developed locally through standalone scripts. That is why the first public Git commit is much larger and more polished than the earliest code in this archive.

These files are included to show the actual technical progression of the project. They are **not retroactive Git commits**, and no dates or timestamps have been invented. The original local filenames have been preserved.

AI tools were used during parts of the project as a coding and learning assistant. This archive is not presented as proof of completely unaided coding. Its purpose is to make the development process transparent: the simulator began as a very small one-stop model and was repeatedly run, interpreted, extended, corrected and refactored.

## Development stages

### 1. Core strategy model

The earliest scripts begin with a simple 50-lap Soft → Medium one-stop model using linear degradation and brute-force pit-lap search. From there the work adds a Hard compound, fuel effects, two-stop logic, lap-time traces and cumulative-time comparisons.

### 2. Automatic strategy search

The next stage replaces manually listed combinations with automated strategy enumeration. Constraints are then added and refined so the optimiser does not accept obviously unsuitable stint structures.

### 3. Tyre model development

The tyre model is extended from simple linear degradation to nonlinear wear, warm-up behaviour, fuel-dependent effective wear and a late-stint tyre-cliff penalty.

### 4. Safety Car and uncertainty

Safety Car modelling develops in several steps: a known predetermined event, random scenarios with Monte Carlo simulation, a simple reactive strategy, and then an uncertainty-aware stay-out-versus-pit-now decision based on possible Safety Car end laps.

### 5. Traffic and field interaction

The simulator then moves beyond isolated race time. It adds post-stop traffic, explicit rival-car undercut/overcut analysis, dirty-air and overtaking restrictions, a small multi-car field, pit-rejoin position and a generic DRS-style overtaking aid.

### 6. Robustness, calibration and validation

The final local-development stage adds sensitivity analysis, calibration structure, data cleaning, multi-stint validation, leave-one-stint-out cross-validation and finally real historical F1 timing data through FastF1.

## Complete file index

The order below is the **technical development sequence used for this archive**, not a claim about precise historical timestamps.

| # | Stage | Original local filename |
|---:|---|---|
| 1 | `01_core_strategy` | `Base.py` |
| 2 | `01_core_strategy` | `Base With Hards.py` |
| 3 | `01_core_strategy` | `With Fuel.py` |
| 4 | `01_core_strategy` | `Two Stop Strategy.py` |
| 5 | `01_core_strategy` | `One Stop added with lap time Trace.py` |
| 6 | `01_core_strategy` | `Two Stop added with lap time Trace.py` |
| 7 | `01_core_strategy` | `Two Stop added with lap time Trace Fixed key on the graph.py` |
| 8 | `01_core_strategy` | `Two Stop Cumlative Time Graph.py` |
| 9 | `01_core_strategy` | `Two Stop New Test.py` |
| 10 | `02_automatic_strategy_search` | `Test each strategy as quickest.py` |
| 11 | `02_automatic_strategy_search` | `Test each strategy as quickest with constraints.py` |
| 12 | `02_automatic_strategy_search` | `Test each strategy as quickest with constraints V2.py` |
| 13 | `03_tyre_model_development` | `Added Tyre warm up.py` |
| 14 | `03_tyre_model_development` | `Fuel linked with Tire wear.py` |
| 15 | `03_tyre_model_development` | `Tire Cliff.py` |
| 16 | `04_safety_car_and_uncertainty` | `safety car modelling.py` |
| 17 | `04_safety_car_and_uncertainty` | `Random Safety car and Monte Carlo Simulatiohn.py` |
| 18 | `04_safety_car_and_uncertainty` | `reactive safety car strategy.py` |
| 19 | `04_safety_car_and_uncertainty` | `safety car decisions under uncertainty.py` |
| 20 | `05_traffic_and_field_interaction` | `Traffic after Pit Stop.py` |
| 21 | `05_traffic_and_field_interaction` | `Rival car simulation with overcut and undercut.py` |
| 22 | `05_traffic_and_field_interaction` | `Dirty air and overtaking difficulties.py` |
| 23 | `05_traffic_and_field_interaction` | `Rival Cars multiple and pit rejoin position.py` |
| 24 | `05_traffic_and_field_interaction` | `DRS Style addition.py` |
| 25 | `06_robustness_calibration_validation` | `sensitivity analysis and robustness testing.py` |
| 26 | `06_robustness_calibration_validation` | `calibration and validation structure.py` |
| 27 | `06_robustness_calibration_validation` | `real-data cleaning before calibration..py` |
| 28 | `06_robustness_calibration_validation` | `calibrate on multiple tyre stints and validate on an entirely unseen stint.py` |
| 29 | `06_robustness_calibration_validation` | `leave-one-stint-out cross-validation..py` |
| 30 | `06_robustness_calibration_validation` | `Real data validation.py` |

## Why every file is retained

Some snapshots differ only by plotting, graph labels, constraints or a relatively small modelling change. They are intentionally retained because this folder is a **development archive**, not a cleaned source package. The maintained code remains in the repository root.

The repetition also makes the learning process visible: early scripts duplicate logic and grow large before later work is refactored into the modular repository.

## Maintained version

These files are historical snapshots. For the current implementation, use the modular Python files in the repository root.
