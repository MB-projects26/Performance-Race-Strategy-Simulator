"""Real-world tyre degradation calibration and cross-validation.

Validation uses historical FastF1 timing data and evaluates relative lap-time
change within each tyre stint. It does not claim to validate absolute Formula 1
lap time or the complete race simulator.
"""

from __future__ import annotations

import csv
import math
import os
import statistics

import config


def create_float_range(start, stop, step):
    values = []
    current = start
    while current <= stop + 1e-7:
        values.append(round(current, 8))
        current += step
    return values


def calculate_rmse(predicted, observed):
    errors = [(p - o) ** 2 for p, o in zip(predicted, observed)]
    return math.sqrt(statistics.mean(errors))


def calculate_mae(predicted, observed):
    errors = [abs(p - o) for p, o in zip(predicted, observed)]
    return statistics.mean(errors)


def calculate_real_fuel_gain(lap, actual_race_laps):
    # Illustrative fuel correction distributed across the observed race length.
    burn_per_lap = config.INITIAL_FUEL_MASS / actual_race_laps
    fuel_burned = burn_per_lap * (lap - 1)
    return fuel_burned * config.FUEL_TIME_PER_KG


def calculate_real_wear_increment(lap, actual_race_laps):
    remaining_fraction = 1.0 - ((lap - 1) / actual_race_laps)
    remaining_fraction = max(0.0, remaining_fraction)
    return 1.0 + config.FUEL_WEAR_SENSITIVITY * remaining_fraction


def apply_real_outlier_filter(rows):
    candidates = [row for row in rows if not row["removal_reasons"]]

    for index, row in enumerate(candidates):
        neighbours = []
        start = max(0, index - config.REAL_OUTLIER_WINDOW)
        end = min(len(candidates), index + config.REAL_OUTLIER_WINDOW + 1)

        for neighbour_index in range(start, end):
            if neighbour_index == index:
                continue
            neighbours.append(candidates[neighbour_index]["lap_time"])

        if len(neighbours) >= 2:
            local_median = statistics.median(neighbours)
            if abs(row["lap_time"] - local_median) > config.REAL_OUTLIER_THRESHOLD:
                row["removal_reasons"].append("Local lap-time outlier")

    return rows


def load_real_world_stints(cache_folder="fastf1_cache"):
    try:
        import fastf1
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            "FastF1 and pandas are required for real-world validation. "
            "Install the versions listed in requirements.txt."
        ) from exc

    os.makedirs(cache_folder, exist_ok=True)
    fastf1.Cache.enable_cache(cache_folder)

    session = fastf1.get_session(
        config.REAL_VALIDATION_YEAR,
        config.REAL_VALIDATION_EVENT,
        config.REAL_VALIDATION_SESSION,
    )
    session.load(
        laps=True,
        telemetry=False,
        weather=False,
        messages=False,
    )

    laps = session.laps.copy()
    if len(laps) == 0:
        raise RuntimeError("FastF1 returned no lap data.")

    actual_race_laps = int(laps["LapNumber"].dropna().max())
    grouped_stints = {}

    grouped = laps.groupby(["Driver", "Stint"], dropna=True)
    for (driver, stint_number), group in grouped:
        group = group.sort_values("LapNumber")
        compounds = group["Compound"].dropna().astype(str)
        if len(compounds) == 0:
            continue

        compound = compounds.mode().iloc[0].upper()
        if compound not in {"SOFT", "MEDIUM", "HARD"}:
            continue

        fresh_tyre = None
        if "FreshTyre" in group.columns:
            fresh_values = group["FreshTyre"].dropna()
            if len(fresh_values) > 0:
                fresh_tyre = bool(fresh_values.iloc[0])

        if config.REAL_REQUIRE_FRESH_TYRE and fresh_tyre is not True:
            continue

        tyre_age = 0
        tyre_wear = 0.0
        processed_rows = []

        for _, lap_row in group.iterrows():
            if pd.isna(lap_row["LapNumber"]):
                continue

            lap_number = int(lap_row["LapNumber"])
            reasons = []

            if pd.isna(lap_row["LapTime"]):
                lap_time = None
                reasons.append("Missing lap time")
            else:
                lap_time = lap_row["LapTime"].total_seconds()

            if lap_number == 1:
                reasons.append("Race-start lap")

            if "PitInTime" in group.columns and pd.notna(lap_row["PitInTime"]):
                reasons.append("Pit in-lap")

            if "PitOutTime" in group.columns and pd.notna(lap_row["PitOutTime"]):
                reasons.append("Pit out-lap")

            if "IsAccurate" in group.columns:
                accurate = lap_row["IsAccurate"]
                if pd.isna(accurate) or not bool(accurate):
                    reasons.append("FastF1 inaccurate lap")

            if "TrackStatus" in group.columns:
                track_status = str(lap_row["TrackStatus"])
                if track_status != "1":
                    reasons.append("Non-green track status")

            row_compound = str(lap_row["Compound"]).upper()
            if row_compound != compound:
                reasons.append("Compound inconsistency")

            if tyre_age < config.REAL_MINIMUM_TYRE_AGE:
                reasons.append("Early warm-up phase")

            processed_rows.append(
                {
                    "driver": str(driver),
                    "stint": int(stint_number),
                    "compound": compound,
                    "lap_number": lap_number,
                    "lap_time": lap_time,
                    "tyre_age": tyre_age,
                    "tyre_wear": tyre_wear,
                    "fresh_tyre": fresh_tyre,
                    "removal_reasons": reasons,
                }
            )

            tyre_age += 1
            tyre_wear += calculate_real_wear_increment(
                lap_number, actual_race_laps
            )

        rows_with_times = [row for row in processed_rows if row["lap_time"] is not None]
        apply_real_outlier_filter(rows_with_times)

        clean_rows = [
            row
            for row in processed_rows
            if row["lap_time"] is not None and not row["removal_reasons"]
        ]

        if len(clean_rows) >= config.REAL_MINIMUM_CLEAN_LAPS:
            key = (str(driver), int(stint_number), compound)
            grouped_stints[key] = clean_rows

    if not grouped_stints:
        raise RuntimeError("No suitable real tyre stints remained after cleaning.")

    return grouped_stints, actual_race_laps


def choose_real_validation_stints(all_stints):
    compound_stints = {"SOFT": [], "MEDIUM": [], "HARD": []}
    for key in all_stints:
        if key[2] in compound_stints:
            compound_stints[key[2]].append(key)

    if config.REAL_VALIDATION_COMPOUND != "AUTO":
        selected_compound = config.REAL_VALIDATION_COMPOUND.upper()
    else:
        selected_compound = max(
            compound_stints,
            key=lambda compound: len({key[0] for key in compound_stints[compound]}),
        )

    candidates = list(compound_stints[selected_compound])
    if len(candidates) < 2:
        raise RuntimeError(
            f"Not enough {selected_compound} stints for cross-validation."
        )

    # Prefer the longest suitable stint from each different driver.
    candidates.sort(key=lambda key: len(all_stints[key]), reverse=True)
    selected = []
    used_drivers = set()

    for key in candidates:
        if key[0] not in used_drivers:
            selected.append(key)
            used_drivers.add(key[0])
        if len(selected) >= config.REAL_MAXIMUM_VALIDATION_STINTS:
            break

    if len(selected) < 2:
        for key in candidates:
            if key not in selected:
                selected.append(key)
            if len(selected) >= 2:
                break

    return selected_compound, selected


def calculate_real_model_component(row, linear_coefficient,
                                   quadratic_coefficient,
                                   actual_race_laps):
    tyre_loss = (
        linear_coefficient * row["tyre_wear"]
        + quadratic_coefficient * row["tyre_wear"] ** 2
    )
    fuel_gain = calculate_real_fuel_gain(row["lap_number"], actual_race_laps)
    return tyre_loss - fuel_gain


def calculate_stint_relative_values(rows, linear_coefficient,
                                    quadratic_coefficient,
                                    actual_race_laps):
    if len(rows) < 2:
        return [], []

    reference = rows[0]
    observed_reference = reference["lap_time"]
    predicted_reference = calculate_real_model_component(
        reference,
        linear_coefficient,
        quadratic_coefficient,
        actual_race_laps,
    )

    observed_deltas = []
    predicted_deltas = []

    for row in rows[1:]:
        observed_deltas.append(row["lap_time"] - observed_reference)
        predicted_deltas.append(
            calculate_real_model_component(
                row,
                linear_coefficient,
                quadratic_coefficient,
                actual_race_laps,
            )
            - predicted_reference
        )

    return observed_deltas, predicted_deltas


def evaluate_real_model(all_stints, stint_keys, linear_coefficient,
                        quadratic_coefficient, actual_race_laps):
    observed_all = []
    predicted_all = []

    for key in stint_keys:
        observed, predicted = calculate_stint_relative_values(
            all_stints[key],
            linear_coefficient,
            quadratic_coefficient,
            actual_race_laps,
        )
        observed_all.extend(observed)
        predicted_all.extend(predicted)

    return {
        "rmse": calculate_rmse(predicted_all, observed_all),
        "mae": calculate_mae(predicted_all, observed_all),
        "observed": observed_all,
        "predicted": predicted_all,
    }


def fit_real_degradation_model(all_stints, training_keys, actual_race_laps):
    linear_values = create_float_range(
        config.REAL_LINEAR_MIN,
        config.REAL_LINEAR_MAX,
        config.REAL_LINEAR_STEP,
    )
    quadratic_values = create_float_range(
        config.REAL_QUADRATIC_MIN,
        config.REAL_QUADRATIC_MAX,
        config.REAL_QUADRATIC_STEP,
    )

    best_rmse = None
    best_linear = None
    best_quadratic = None
    combinations_tested = 0

    for linear in linear_values:
        for quadratic in quadratic_values:
            combinations_tested += 1
            evaluation = evaluate_real_model(
                all_stints,
                training_keys,
                linear,
                quadratic,
                actual_race_laps,
            )
            if best_rmse is None or evaluation["rmse"] < best_rmse:
                best_rmse = evaluation["rmse"]
                best_linear = linear
                best_quadratic = quadratic

    return {
        "linear": best_linear,
        "quadratic": best_quadratic,
        "training_rmse": best_rmse,
        "combinations_tested": combinations_tested,
    }


def run_real_world_validation(cache_folder="fastf1_cache"):
    all_stints, actual_race_laps = load_real_world_stints(cache_folder)
    selected_compound, selected_keys = choose_real_validation_stints(all_stints)

    simulator_name = selected_compound.title()
    baseline_tyre = config.TYRES[simulator_name]
    baseline_linear = baseline_tyre[1]
    baseline_quadratic = baseline_tyre[2]

    fold_results = []

    for validation_key in selected_keys:
        training_keys = [key for key in selected_keys if key != validation_key]
        fitted_model = fit_real_degradation_model(
            all_stints, training_keys, actual_race_laps
        )
        baseline_validation = evaluate_real_model(
            all_stints,
            [validation_key],
            baseline_linear,
            baseline_quadratic,
            actual_race_laps,
        )
        calibrated_validation = evaluate_real_model(
            all_stints,
            [validation_key],
            fitted_model["linear"],
            fitted_model["quadratic"],
            actual_race_laps,
        )

        fold_results.append(
            {
                "validation_key": validation_key,
                "linear": fitted_model["linear"],
                "quadratic": fitted_model["quadratic"],
                "baseline_rmse": baseline_validation["rmse"],
                "calibrated_rmse": calibrated_validation["rmse"],
                "calibrated_mae": calibrated_validation["mae"],
            }
        )

    baseline_rmse_values = [fold["baseline_rmse"] for fold in fold_results]
    calibrated_rmse_values = [fold["calibrated_rmse"] for fold in fold_results]
    calibrated_mae_values = [fold["calibrated_mae"] for fold in fold_results]

    mean_baseline_rmse = statistics.mean(baseline_rmse_values)
    mean_calibrated_rmse = statistics.mean(calibrated_rmse_values)
    mean_calibrated_mae = statistics.mean(calibrated_mae_values)
    rmse_standard_deviation = (
        statistics.stdev(calibrated_rmse_values)
        if len(calibrated_rmse_values) > 1
        else 0.0
    )
    improved_folds = sum(
        fold["calibrated_rmse"] < fold["baseline_rmse"]
        for fold in fold_results
    )

    final_model = fit_real_degradation_model(
        all_stints, selected_keys, actual_race_laps
    )
    final_evaluation = evaluate_real_model(
        all_stints,
        selected_keys,
        final_model["linear"],
        final_model["quadratic"],
        actual_race_laps,
    )

    improvement_percentage = (
        (mean_baseline_rmse - mean_calibrated_rmse)
        / mean_baseline_rmse
        * 100.0
    )

    return {
        "all_stints": all_stints,
        "selected_keys": selected_keys,
        "compound": selected_compound,
        "simulator_name": simulator_name,
        "actual_race_laps": actual_race_laps,
        "fold_results": fold_results,
        "mean_baseline_rmse": mean_baseline_rmse,
        "mean_calibrated_rmse": mean_calibrated_rmse,
        "mean_calibrated_mae": mean_calibrated_mae,
        "rmse_standard_deviation": rmse_standard_deviation,
        "worst_rmse": max(calibrated_rmse_values),
        "improved_folds": improved_folds,
        "improvement_percentage": improvement_percentage,
        "final_linear": final_model["linear"],
        "final_quadratic": final_model["quadratic"],
        "final_fit_rmse": final_evaluation["rmse"],
    }


def export_real_validation_data(validation_result, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "driver",
                "stint",
                "compound",
                "lap_number",
                "lap_time",
                "tyre_age",
                "effective_tyre_wear",
            ]
        )
        for key in validation_result["selected_keys"]:
            for row in validation_result["all_stints"][key]:
                writer.writerow(
                    [
                        row["driver"],
                        row["stint"],
                        row["compound"],
                        row["lap_number"],
                        row["lap_time"],
                        row["tyre_age"],
                        row["tyre_wear"],
                    ]
                )


def export_real_validation_summary(result, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file:
        file.write("REAL-WORLD TYRE DEGRADATION VALIDATION\n")
        file.write("======================================\n\n")
        file.write(
            f"Race: {config.REAL_VALIDATION_YEAR} {config.REAL_VALIDATION_EVENT}\n"
        )
        file.write(f"Compound: {result['compound']}\n")
        file.write(f"Cross-validation stints: {len(result['selected_keys'])}\n\n")
        file.write(
            f"Mean baseline held-out RMSE: {result['mean_baseline_rmse']:.4f} s\n"
        )
        file.write(
            f"Mean calibrated held-out RMSE: {result['mean_calibrated_rmse']:.4f} s\n"
        )
        file.write(
            f"Mean calibrated held-out MAE: {result['mean_calibrated_mae']:.4f} s\n"
        )
        file.write(
            "Held-out RMSE standard deviation: "
            f"{result['rmse_standard_deviation']:.4f} s\n"
        )
        file.write(f"Worst held-out RMSE: {result['worst_rmse']:.4f} s\n")
        file.write(
            f"Folds improved: {result['improved_folds']}/{len(result['fold_results'])}\n"
        )
        file.write(
            f"Mean RMSE improvement: {result['improvement_percentage']:.2f}%\n\n"
        )
        file.write(f"Final all-data linear coefficient: {result['final_linear']}\n")
        file.write(
            f"Final all-data quadratic coefficient: {result['final_quadratic']}\n"
        )
        file.write(f"Final all-data fit RMSE: {result['final_fit_rmse']:.4f} s\n\n")
        file.write(
            "LIMITATION: Validation evaluates relative lap-time evolution through "
            "real tyre stints. It does not validate absolute F1 car pace or the "
            "complete race simulator.\n"
        )
