"""Run the complete race-strategy analysis.

Examples
--------
Run everything, including live FastF1 validation:
    python main.py

Run only the deterministic/Monte-Carlo/traffic model:
    python main.py --skip-real

Save plots without opening windows:
    python main.py --no-show
"""

import argparse
import os
import statistics

import matplotlib.pyplot as plt

import config
from strategy import (
    find_best_one_stop,
    find_best_two_stop,
    find_strategy_switch_point,
    run_degradation_sensitivity,
    run_pit_loss_sensitivity,
)
from traffic import find_best_field_pit
from uncertainty import run_monte_carlo
from validation import (
    calculate_stint_relative_values,
    export_real_validation_data,
    export_real_validation_summary,
    run_real_world_validation,
)

ROOT = os.path.dirname(os.path.abspath(__file__))
PLOTS = os.path.join(ROOT, "plots")
RESULTS = os.path.join(ROOT, "results")
DATA = os.path.join(ROOT, "data")
CACHE = os.path.join(ROOT, "fastf1_cache")

for folder in (PLOTS, RESULTS, DATA, CACHE):
    os.makedirs(folder, exist_ok=True)


def finish_plot(filename, show_plots):
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS, filename), dpi=300)
    if show_plots:
        plt.show()
    else:
        plt.close()


def write_baseline_results(path, one, two, field, mc, pit_switch):
    with open(path, "w", encoding="utf-8") as file:
        file.write("RACE STRATEGY & PERFORMANCE SIMULATOR\n")
        file.write("=====================================\n\n")
        file.write(f"Best one-stop: {' -> '.join(one[0])}\n")
        file.write(f"One-stop pit: lap {one[1]}\n")
        file.write(f"One-stop time: {one[2]:.3f} s\n\n")
        file.write(f"Best two-stop: {' -> '.join(two[0])}\n")
        file.write(f"Two-stop pits: laps {two[1]} and {two[2]}\n")
        file.write(f"Two-stop time: {two[3]:.3f} s\n")
        file.write(f"Two-stop advantage: {one[2] - two[3]:.3f} s\n\n")
        file.write(f"Traffic-aware best pit: lap {field[0]}\n")
        file.write(f"Traffic-aware finish: P{field[1]['final_position']}\n\n")
        file.write(
            f"One-stop fixed Monte Carlo mean: {statistics.mean(mc['fixed_one']):.3f} s\n"
        )
        file.write(
            "One-stop uncertainty-aware mean: "
            f"{statistics.mean(mc['reactive_one']):.3f} s\n"
        )
        file.write(
            f"Two-stop fixed Monte Carlo mean: {statistics.mean(mc['fixed_two']):.3f} s\n"
        )
        file.write(
            "Two-stop uncertainty-aware mean: "
            f"{statistics.mean(mc['reactive_two']):.3f} s\n"
        )
        if pit_switch is not None:
            file.write(f"\nOne/two-stop pit-loss crossover: {pit_switch:.2f} s\n")


def plot_strategy(one_stop_results, show_plots):
    plt.figure(figsize=(10, 6))
    for strategy_name, result in one_stop_results.items():
        plt.plot(result[2], result[3], label=strategy_name)
    plt.xlabel("Pit Lap")
    plt.ylabel("Race Time (seconds)")
    plt.title("One-Stop Strategy Optimisation")
    plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
    finish_plot("01_strategy_optimisation.png", show_plots)


def plot_monte_carlo(mc, show_plots):
    plt.figure(figsize=(10, 6))
    plt.hist(mc["reactive_one"], bins=30, alpha=0.6, label="One-Stop")
    plt.hist(mc["reactive_two"], bins=30, alpha=0.6, label="Two-Stop")
    plt.xlabel("Race Time (seconds)")
    plt.ylabel("Frequency")
    plt.title("Monte Carlo Safety Car Strategy Outcomes")
    plt.legend()
    finish_plot("02_monte_carlo.png", show_plots)


def plot_field(field_results, show_plots):
    pit_laps = [pit for pit, _ in field_results]
    positions = [result["final_position"] for _, result in field_results]
    plt.figure(figsize=(10, 6))
    plt.plot(pit_laps, positions, marker="o")
    plt.gca().invert_yaxis()
    plt.xlabel("Our Pit Lap")
    plt.ylabel("Final Position")
    plt.title("Traffic-Aware Pit Strategy")
    finish_plot("03_field_strategy.png", show_plots)


def plot_pit_sensitivity(pit_values, gaps, switch, show_plots):
    plt.figure(figsize=(10, 6))
    plt.plot(pit_values, gaps, marker="o")
    plt.axhline(0, linestyle="--", label="One-Stop = Two-Stop")
    if switch is not None:
        plt.axvline(switch, linestyle="--", label="Strategy Crossover")
    plt.xlabel("Pit-Stop Loss (seconds)")
    plt.ylabel("Two-Stop minus One-Stop (seconds)")
    plt.title("Strategy Robustness to Pit-Stop Loss")
    plt.legend()
    finish_plot("04_sensitivity.png", show_plots)


def plot_real_cross_validation(result, show_plots):
    labels = []
    baseline = []
    calibrated = []

    for fold in result["fold_results"]:
        driver, stint, _ = fold["validation_key"]
        labels.append(f"{driver}\nStint {stint}")
        baseline.append(fold["baseline_rmse"])
        calibrated.append(fold["calibrated_rmse"])

    x_positions = list(range(len(labels)))
    left = [x - 0.18 for x in x_positions]
    right = [x + 0.18 for x in x_positions]

    plt.figure(figsize=(11, 6))
    plt.bar(left, baseline, width=0.36, label="Baseline Model")
    plt.bar(right, calibrated, width=0.36, label="Calibrated Model")
    plt.xticks(x_positions, labels)
    plt.ylabel("Held-Out Stint RMSE (seconds)")
    plt.title("Real-World Leave-One-Stint-Out Validation")
    plt.legend()
    finish_plot("05_real_cross_validation.png", show_plots)


def plot_real_stints(result, show_plots):
    plt.figure(figsize=(11, 6))

    for key in result["selected_keys"]:
        rows = result["all_stints"][key]
        observed, predicted = calculate_stint_relative_values(
            rows,
            result["final_linear"],
            result["final_quadratic"],
            result["actual_race_laps"],
        )
        ages = [row["tyre_age"] for row in rows[1:]]
        label = f"{key[0]} Stint {key[1]}"
        plt.plot(ages, observed, marker="o", alpha=0.55, label=label)
        plt.plot(ages, predicted, linestyle="--", alpha=0.55)

    plt.xlabel("Tyre Age (laps)")
    plt.ylabel("Relative Lap-Time Change (seconds)")
    plt.title("Observed vs Modelled Real Tyre-Stint Evolution")
    plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
    finish_plot("06_real_stint_validation.png", show_plots)


def plot_coefficient_stability(result, show_plots):
    labels = []
    linear = []
    quadratic = []

    for fold in result["fold_results"]:
        driver, stint, _ = fold["validation_key"]
        labels.append(f"{driver}\nStint {stint}")
        linear.append(fold["linear"])
        quadratic.append(fold["quadratic"])

    x_positions = list(range(len(labels)))
    plt.figure(figsize=(11, 6))
    plt.plot(x_positions, linear, marker="o", label="Linear coefficient")
    plt.plot(x_positions, quadratic, marker="o", label="Quadratic coefficient")
    plt.xticks(x_positions, labels)
    plt.xlabel("Held-Out Stint")
    plt.ylabel("Fitted Degradation Coefficient")
    plt.title("Cross-Validation Coefficient Stability")
    plt.legend()
    finish_plot("07_coefficient_stability.png", show_plots)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-real",
        action="store_true",
        help="Skip FastF1 download/calibration and run the simulator only.",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Save plots without opening plotting windows.",
    )
    args = parser.parse_args()
    show_plots = not args.no_show

    print("Running deterministic strategy optimisation...")
    one = find_best_one_stop()
    two = find_best_two_stop()

    print("Running traffic-aware field optimisation...")
    field = find_best_field_pit()

    print("Running Monte Carlo Safety Car analysis...")
    mc = run_monte_carlo(one[0], one[1], two[0], two[1], two[2])

    print("Running sensitivity analysis...")
    pit_values, pit_gaps = run_pit_loss_sensitivity()
    pit_switch = find_strategy_switch_point(pit_values, pit_gaps)
    degradation_scales, degradation_gaps = run_degradation_sensitivity()

    write_baseline_results(
        os.path.join(RESULTS, "latest_simulator_results.txt"),
        one,
        two,
        field,
        mc,
        pit_switch,
    )

    plot_strategy(one[3], show_plots)
    plot_monte_carlo(mc, show_plots)
    plot_field(field[2], show_plots)
    plot_pit_sensitivity(pit_values, pit_gaps, pit_switch, show_plots)

    real_result = None
    if not args.skip_real:
        print("Running real-world FastF1 validation...")
        real_result = run_real_world_validation(CACHE)
        export_real_validation_data(
            real_result,
            os.path.join(DATA, "real_validation_clean_laps.csv"),
        )
        export_real_validation_summary(
            real_result,
            os.path.join(RESULTS, "real_validation_results.txt"),
        )
        plot_real_cross_validation(real_result, show_plots)
        plot_real_stints(real_result, show_plots)
        plot_coefficient_stability(real_result, show_plots)

    print("\nFINAL SUMMARY")
    print("-------------")
    print(f"Best one-stop: {' -> '.join(one[0])}, pit lap {one[1]}, {one[2]:.3f} s")
    print(
        f"Best two-stop: {' -> '.join(two[0])}, pits {two[1]}/{two[2]}, "
        f"{two[3]:.3f} s"
    )
    print(f"Two-stop advantage: {one[2] - two[3]:.3f} s")
    print(f"Traffic-aware optimum: lap {field[0]}, P{field[1]['final_position']}")
    if pit_switch is not None:
        print(f"Pit-loss crossover: {pit_switch:.2f} s")
    print(
        "Monte Carlo means: "
        f"one-stop {statistics.mean(mc['reactive_one']):.3f} s, "
        f"two-stop {statistics.mean(mc['reactive_two']):.3f} s"
    )

    if real_result is not None:
        print(
            "Real validation: "
            f"{real_result['mean_baseline_rmse']:.4f} -> "
            f"{real_result['mean_calibrated_rmse']:.4f} s/lap "
            f"({real_result['improvement_percentage']:.1f}% improvement; "
            f"{real_result['improved_folds']}/{len(real_result['fold_results'])} folds improved)"
        )

    print(f"Plots: {PLOTS}")
    print(f"Results: {RESULTS}")
    print(f"Data: {DATA}")


if __name__ == "__main__":
    main()
