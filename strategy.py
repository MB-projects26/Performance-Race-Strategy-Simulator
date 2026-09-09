"""Deterministic race simulation and pit-stop optimisation."""

import config
from model import calculate_lap_time, calculate_fuel_wear_increment, calculate_pit_loss


def pit_plan_is_legal(pit_laps, race_laps=None, minimum_stint=None):
    if race_laps is None:
        race_laps = config.RACE_LAPS
    if minimum_stint is None:
        minimum_stint = config.MINIMUM_STINT

    for i in range(len(pit_laps) - 1):
        if pit_laps[i] >= pit_laps[i + 1]:
            return False

    if not pit_laps:
        return True

    stint_lengths = [pit_laps[0]]
    for i in range(1, len(pit_laps)):
        stint_lengths.append(pit_laps[i] - pit_laps[i - 1])
    stint_lengths.append(race_laps - pit_laps[-1])

    return all(stint >= minimum_stint for stint in stint_lengths)


def simulate_fixed_strategy(tyre_sequence, pit_laps,
                            safety_car_start=None, safety_car_end=None,
                            pace_offset=0.0, return_trace=False,
                            normal_pit_loss=None, degradation_scale=None):
    if len(pit_laps) != len(tyre_sequence) - 1:
        return None
    if not pit_plan_is_legal(pit_laps):
        return None

    total_time = 0.0
    tyre_age = 0
    tyre_wear = 0.0
    stint_number = 0
    pit_number = 0
    lap_times = []
    cumulative_times = []

    for lap in range(1, config.RACE_LAPS + 1):
        tyre_name = tyre_sequence[stint_number]
        tyre_data = config.TYRES[tyre_name]

        lap_time = calculate_lap_time(
            tyre_data,
            tyre_age,
            tyre_wear,
            lap,
            safety_car_start,
            safety_car_end,
            pace_offset,
            degradation_scale,
        )
        total_time += lap_time

        tyre_age += 1
        tyre_wear += calculate_fuel_wear_increment(
            lap, safety_car_start, safety_car_end
        )

        if pit_number < len(pit_laps) and lap == pit_laps[pit_number]:
            total_time += calculate_pit_loss(
                lap,
                safety_car_start,
                safety_car_end,
                normal_pit_loss,
            )
            tyre_age = 0
            tyre_wear = 0.0
            stint_number += 1
            pit_number += 1

        if return_trace:
            lap_times.append(lap_time)
            cumulative_times.append(total_time)

    if return_trace:
        return total_time, lap_times, cumulative_times
    return total_time


def calculate_one_stop_strategy(first_tyre, second_tyre,
                                normal_pit_loss=None,
                                degradation_scale=None):
    tyre_sequence = [first_tyre, second_tyre]
    pit_laps_tested = []
    race_times = []

    for pit_lap in range(
        config.MINIMUM_STINT,
        config.RACE_LAPS - config.MINIMUM_STINT + 1,
    ):
        race_time = simulate_fixed_strategy(
            tyre_sequence,
            [pit_lap],
            normal_pit_loss=normal_pit_loss,
            degradation_scale=degradation_scale,
        )
        pit_laps_tested.append(pit_lap)
        race_times.append(race_time)

    best_time = min(race_times)
    best_index = race_times.index(best_time)
    return (
        pit_laps_tested[best_index],
        best_time,
        pit_laps_tested,
        race_times,
    )


def calculate_two_stop_strategy(first_tyre, second_tyre, third_tyre,
                                normal_pit_loss=None,
                                degradation_scale=None):
    tyre_sequence = [first_tyre, second_tyre, third_tyre]
    best_time = None
    best_pit_1 = None
    best_pit_2 = None

    for pit_lap_1 in range(
        config.MINIMUM_STINT,
        config.RACE_LAPS - 2 * config.MINIMUM_STINT + 1,
    ):
        for pit_lap_2 in range(
            pit_lap_1 + config.MINIMUM_STINT,
            config.RACE_LAPS - config.MINIMUM_STINT + 1,
        ):
            race_time = simulate_fixed_strategy(
                tyre_sequence,
                [pit_lap_1, pit_lap_2],
                normal_pit_loss=normal_pit_loss,
                degradation_scale=degradation_scale,
            )
            if best_time is None or race_time < best_time:
                best_time = race_time
                best_pit_1 = pit_lap_1
                best_pit_2 = pit_lap_2

    return best_pit_1, best_pit_2, best_time


def find_best_one_stop(normal_pit_loss=None, degradation_scale=None):
    tyre_names = list(config.TYRES.keys())
    best_time = None
    best_strategy = None
    best_pit = None
    all_results = {}

    for first_tyre in tyre_names:
        for second_tyre in tyre_names:
            if first_tyre == second_tyre:
                continue
            result = calculate_one_stop_strategy(
                first_tyre,
                second_tyre,
                normal_pit_loss,
                degradation_scale,
            )
            strategy_name = f"{first_tyre} -> {second_tyre}"
            all_results[strategy_name] = result
            if best_time is None or result[1] < best_time:
                best_time = result[1]
                best_strategy = (first_tyre, second_tyre)
                best_pit = result[0]

    return best_strategy, best_pit, best_time, all_results


def find_best_two_stop(normal_pit_loss=None, degradation_scale=None):
    tyre_names = list(config.TYRES.keys())
    best_time = None
    best_strategy = None
    best_pit_1 = None
    best_pit_2 = None

    for first_tyre in tyre_names:
        for second_tyre in tyre_names:
            for third_tyre in tyre_names:
                if first_tyre == second_tyre == third_tyre:
                    continue
                result = calculate_two_stop_strategy(
                    first_tyre,
                    second_tyre,
                    third_tyre,
                    normal_pit_loss,
                    degradation_scale,
                )
                if best_time is None or result[2] < best_time:
                    best_time = result[2]
                    best_strategy = (first_tyre, second_tyre, third_tyre)
                    best_pit_1 = result[0]
                    best_pit_2 = result[1]

    return best_strategy, best_pit_1, best_pit_2, best_time


def run_pit_loss_sensitivity(values=None):
    if values is None:
        values = list(range(10, 61, 5))
    gaps = []
    for value in values:
        one = find_best_one_stop(normal_pit_loss=float(value))
        two = find_best_two_stop(normal_pit_loss=float(value))
        gaps.append(two[3] - one[2])
    return values, gaps


def run_degradation_sensitivity(scales=None):
    if scales is None:
        scales = [0.70, 0.80, 0.90, 1.00, 1.10, 1.20, 1.30]
    gaps = []
    for scale in scales:
        one = find_best_one_stop(degradation_scale=scale)
        two = find_best_two_stop(degradation_scale=scale)
        gaps.append(two[3] - one[2])
    return scales, gaps


def find_strategy_switch_point(x_values, y_values):
    for i in range(len(x_values) - 1):
        y1 = y_values[i]
        y2 = y_values[i + 1]
        if y1 == 0:
            return x_values[i]
        if y1 * y2 < 0:
            x1 = x_values[i]
            x2 = x_values[i + 1]
            return x1 + (-y1 * (x2 - x1) / (y2 - y1))
    return None
