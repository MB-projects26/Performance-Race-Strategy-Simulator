"""Safety Car scenario generation and uncertainty-aware pit decisions."""

import random
import statistics

import config
from strategy import pit_plan_is_legal, simulate_fixed_strategy


def generate_safety_car_scenarios(number_of_races=None, seed=None):
    if number_of_races is None:
        number_of_races = config.MONTE_CARLO_RUNS
    if seed is None:
        seed = config.RANDOM_SEED

    generator = random.Random(seed)
    scenarios = []

    for _ in range(number_of_races):
        if generator.random() < config.SAFETY_CAR_PROBABILITY:
            start_lap = generator.randint(
                config.SAFETY_CAR_MIN_START,
                config.SAFETY_CAR_MAX_START,
            )
            duration = generator.randint(
                config.SAFETY_CAR_MIN_DURATION,
                config.SAFETY_CAR_MAX_DURATION,
            )
            end_lap = min(config.RACE_LAPS, start_lap + duration - 1)
            scenarios.append((start_lap, end_lap))
        else:
            scenarios.append((None, None))

    return scenarios


def possible_safety_car_end_laps(safety_car_start, current_lap):
    possible_ends = []
    for duration in range(
        config.SAFETY_CAR_MIN_DURATION,
        config.SAFETY_CAR_MAX_DURATION + 1,
    ):
        end_lap = safety_car_start + duration - 1
        if current_lap <= end_lap <= config.RACE_LAPS:
            possible_ends.append(end_lap)
    return possible_ends


def calculate_expected_plan_time(tyre_sequence, pit_laps,
                                 safety_car_start, current_lap):
    possible_ends = possible_safety_car_end_laps(
        safety_car_start, current_lap
    )
    if not possible_ends:
        return simulate_fixed_strategy(tyre_sequence, pit_laps)

    times = [
        simulate_fixed_strategy(
            tyre_sequence,
            pit_laps,
            safety_car_start,
            possible_end,
        )
        for possible_end in possible_ends
    ]
    return statistics.mean(times)


def simulate_uncertainty_strategy(tyre_sequence, planned_pit_laps,
                                  safety_car_start=None,
                                  safety_car_end=None):
    """Adapt planned pit laps while the Safety Car is active.

    Decisions use only the set of possible remaining Safety Car durations
    consistent with the current lap. The realised end lap is used only when the
    final race is simulated, not when evaluating the decision.
    """
    if safety_car_start is None:
        return simulate_fixed_strategy(tyre_sequence, planned_pit_laps)

    adjusted_pits = list(planned_pit_laps)

    for pit_index in range(len(adjusted_pits)):
        planned_pit = adjusted_pits[pit_index]

        for current_lap in range(safety_car_start, safety_car_end + 1):
            if current_lap >= planned_pit:
                break

            pit_now_plan = list(adjusted_pits)
            pit_now_plan[pit_index] = current_lap

            if not pit_plan_is_legal(pit_now_plan):
                continue

            stay_expected = calculate_expected_plan_time(
                tyre_sequence,
                adjusted_pits,
                safety_car_start,
                current_lap,
            )
            pit_expected = calculate_expected_plan_time(
                tyre_sequence,
                pit_now_plan,
                safety_car_start,
                current_lap,
            )

            if pit_expected < stay_expected:
                adjusted_pits = pit_now_plan
                break

    return simulate_fixed_strategy(
        tyre_sequence,
        adjusted_pits,
        safety_car_start,
        safety_car_end,
    )


def run_monte_carlo(best_one_strategy, best_one_pit,
                    best_two_strategy, best_two_pit_1, best_two_pit_2,
                    number_of_races=None):
    scenarios = generate_safety_car_scenarios(number_of_races)

    fixed_one = []
    reactive_one = []
    fixed_two = []
    reactive_two = []

    for sc_start, sc_end in scenarios:
        fixed_one.append(
            simulate_fixed_strategy(
                list(best_one_strategy), [best_one_pit], sc_start, sc_end
            )
        )
        reactive_one.append(
            simulate_uncertainty_strategy(
                list(best_one_strategy), [best_one_pit], sc_start, sc_end
            )
        )
        fixed_two.append(
            simulate_fixed_strategy(
                list(best_two_strategy),
                [best_two_pit_1, best_two_pit_2],
                sc_start,
                sc_end,
            )
        )
        reactive_two.append(
            simulate_uncertainty_strategy(
                list(best_two_strategy),
                [best_two_pit_1, best_two_pit_2],
                sc_start,
                sc_end,
            )
        )

    return {
        "scenarios": scenarios,
        "fixed_one": fixed_one,
        "reactive_one": reactive_one,
        "fixed_two": fixed_two,
        "reactive_two": reactive_two,
    }
