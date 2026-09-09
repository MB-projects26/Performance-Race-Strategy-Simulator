# =============================================================
# RACE STRATEGY & PERFORMANCE SIMULATOR
# FINAL PORTFOLIO VERSION
#
# Includes:
#
# - Nonlinear tyre degradation
# - Fuel effect
# - Warm-up
# - Tyre cliff
# - One-stop optimisation
# - Two-stop optimisation
# - Safety Car uncertainty
# - Monte Carlo simulation
# - Small multi-car field
# - Dirty air
# - Simplified overtaking aid
# - Sensitivity analysis
# - REAL F1 DATA validation using FastF1
# - Data cleaning
# - Whole-stint cross-validation
# - Results/plot export
#
# IMPORTANT:
#
# The race-strategy simulator remains a simplified engineering
# model. Real-world validation below specifically evaluates the
# RELATIVE TYRE-DEGRADATION behaviour, not an entire professional
# F1 lap-time model.
#
# =============================================================


import matplotlib.pyplot as plt
import random
import statistics
import math
import os
import csv


# =============================================================
# OUTPUT SETTINGS
# =============================================================

results_folder = "results"
plots_folder = "plots"
fastf1_cache_folder = "fastf1_cache"

save_plots = True
show_plots = True

os.makedirs(
    results_folder,
    exist_ok=True
)

os.makedirs(
    plots_folder,
    exist_ok=True
)

os.makedirs(
    fastf1_cache_folder,
    exist_ok=True
)


# =============================================================
# RACE MODEL SETTINGS
# =============================================================

race_laps = 50

normal_pit_loss = 22.0

minimum_stint = 5


# =============================================================
# FUEL MODEL
# =============================================================

initial_fuel_mass = 100.0

fuel_burn_per_lap = 2.0

fuel_time_per_kg = 0.03

fuel_wear_sensitivity = 0.25


# =============================================================
# TYRE DEGRADATION SCALE
# =============================================================

tyre_degradation_scale = 1.0


# =============================================================
# SAFETY CAR MODEL
# =============================================================

safety_car_probability = 0.40

safety_car_min_start = 5

safety_car_max_start = 45

safety_car_min_duration = 2

safety_car_max_duration = 5

safety_car_lap_time = 120.0

safety_car_pit_loss = 10.0

safety_car_tyre_wear_multiplier = 0.35


# =============================================================
# MONTE CARLO SETTINGS
# =============================================================

monte_carlo_runs = 1000

random_seed = 42


# =============================================================
# DIRTY AIR
# =============================================================

dirty_air_enabled = True

dirty_air_range = 1.5

dirty_air_max_penalty = 0.65

overtake_margin = 0.25

minimum_following_gap = 0.15


# =============================================================
# GENERIC OVERTAKING-AID MODEL
# =============================================================
#
# This is deliberately NOT claimed to reproduce the exact
# regulations of a particular championship season.
#
# =============================================================

drs_enabled = True

drs_activation_lap = 3

drs_detection_range = 1.0

drs_time_gain = 0.45

drs_overtake_margin_reduction = 0.15


# =============================================================
# TYRE MODEL
# =============================================================
#
# Tuple:
#
# 0 = base lap time
# 1 = linear degradation coefficient
# 2 = quadratic degradation coefficient
# 3 = initial warm-up penalty
# 4 = warm-up recovery rate
# 5 = cliff threshold
# 6 = cliff severity
#
# These baseline numbers are modelling assumptions.
#
# =============================================================

tyres = {

    "Soft": (
        89.0,
        0.10,
        0.006,
        0.30,
        0.15,
        18.0,
        0.04
    ),

    "Medium": (
        90.0,
        0.06,
        0.0025,
        0.50,
        0.15,
        28.0,
        0.02
    ),

    "Hard": (
        92.0,
        0.03,
        0.001,
        0.70,
        0.15,
        38.0,
        0.01
    )
}


# =============================================================
# REAL-WORLD VALIDATION SETTINGS
# =============================================================
#
# The script downloads an actual historical F1 race.
#
# Austria 2024 is used by default because it provides a useful
# dry-race tyre dataset.
#
# "AUTO" makes the script choose the dry compound with the
# largest number of suitable fresh-tyre stints.
#
# =============================================================

real_validation_enabled = True

real_validation_year = 2024

real_validation_event = "Austria"

real_validation_session = "R"

real_validation_compound = "AUTO"


# Only use stints beginning on a fresh tyre where possible.

real_require_fresh_tyre = True


# Minimum clean observations per stint.

real_minimum_clean_laps = 7


# Remove the early warm-up phase from physical-degradation
# validation.
#
# Out-laps are already removed separately.

real_minimum_tyre_age = 2


# Maximum number of stints used for cross-validation.
#
# One representative long stint is selected per driver first.
#
# This keeps the calculation fast while providing driver
# diversity.

real_maximum_validation_stints = 10


# Lap-time outlier detection.

real_outlier_threshold = 1.50

real_outlier_window = 2


# =============================================================
# REAL-WORLD CALIBRATION SEARCH
# =============================================================
#
# We fit only:
#
# - linear degradation
# - quadratic degradation
#
# Absolute car pace is NOT fitted because different cars have
# different performance.
#
# =============================================================

real_linear_min = 0.000

real_linear_max = 0.150

real_linear_step = 0.005


real_quadratic_min = 0.000

real_quadratic_max = 0.008

real_quadratic_step = 0.00025


# =============================================================
# APPLY REAL COEFFICIENTS TO STRATEGY SIMULATOR?
# =============================================================
#
# Leave False initially.
#
# The real-data calibration is event-specific and validates
# relative stint degradation, not the entire simulator.
#
# =============================================================

apply_real_calibration_to_strategy_model = False


# =============================================================
# SMALL FIELD CONFIGURATION
# =============================================================

field_configuration = [

    {
        "name": "Leader",
        "start_gap": 0.0,
        "tyre_sequence": [
            "Medium",
            "Soft"
        ],
        "pit_laps": [
            31
        ],
        "pace_offset": -0.05
    },

    {
        "name": "Car B",
        "start_gap": 0.8,
        "tyre_sequence": [
            "Medium",
            "Soft"
        ],
        "pit_laps": [
            30
        ],
        "pace_offset": 0.03
    },

    {
        "name": "Our Car",
        "start_gap": 1.4,
        "tyre_sequence": [
            "Medium",
            "Soft"
        ],
        "pit_laps": [
            29
        ],
        "pace_offset": 0.0
    },

    {
        "name": "Car D",
        "start_gap": 2.0,
        "tyre_sequence": [
            "Medium",
            "Soft"
        ],
        "pit_laps": [
            28
        ],
        "pace_offset": 0.08
    },

    {
        "name": "Car E",
        "start_gap": 2.7,
        "tyre_sequence": [
            "Hard",
            "Soft"
        ],
        "pit_laps": [
            34
        ],
        "pace_offset": 0.06
    },

    {
        "name": "Car F",
        "start_gap": 3.4,
        "tyre_sequence": [
            "Medium",
            "Hard"
        ],
        "pit_laps": [
            26
        ],
        "pace_offset": 0.15
    }
]


field_pit_search_start = 24

field_pit_search_end = 34


# =============================================================
# BASIC HELPERS
# =============================================================

def create_float_range(
        start,
        stop,
        step):

    values = []

    current = start

    while (
        current
        <= stop + 0.0000001
    ):

        values.append(
            round(
                current,
                8
            )
        )

        current += step

    return values


def calculate_rmse(
        predicted,
        observed):

    squared_errors = []

    for i in range(
        len(observed)
    ):

        error = (
            predicted[i]
            - observed[i]
        )

        squared_errors.append(
            error ** 2
        )

    return math.sqrt(
        statistics.mean(
            squared_errors
        )
    )


def calculate_mae(
        predicted,
        observed):

    absolute_errors = []

    for i in range(
        len(observed)
    ):

        absolute_errors.append(
            abs(
                predicted[i]
                - observed[i]
            )
        )

    return statistics.mean(
        absolute_errors
    )


# =============================================================
# SAFETY CAR CHECK
# =============================================================

def is_safety_car_lap(
        lap,
        safety_car_start,
        safety_car_end):

    if safety_car_start is None:

        return False

    return (
        lap >= safety_car_start
        and lap <= safety_car_end
    )


# =============================================================
# PIT LOSS
# =============================================================

def calculate_pit_loss(
        lap,
        safety_car_start=None,
        safety_car_end=None):

    if is_safety_car_lap(
        lap,
        safety_car_start,
        safety_car_end
    ):

        return safety_car_pit_loss

    return normal_pit_loss


# =============================================================
# FUEL MODEL
# =============================================================

def calculate_fuel_mass(
        lap):

    fuel_mass = (
        initial_fuel_mass
        - fuel_burn_per_lap
        * (lap - 1)
    )

    if fuel_mass < 0:

        fuel_mass = 0.0

    return fuel_mass


def calculate_fuel_time_gain(
        lap):

    current_fuel = (
        calculate_fuel_mass(
            lap
        )
    )

    fuel_burned = (
        initial_fuel_mass
        - current_fuel
    )

    return (
        fuel_burned
        * fuel_time_per_kg
    )


def calculate_fuel_wear_increment(
        lap,
        safety_car_start=None,
        safety_car_end=None):

    current_fuel = (
        calculate_fuel_mass(
            lap
        )
    )

    fuel_fraction = (
        current_fuel
        / initial_fuel_mass
    )

    wear_increment = (
        1.0
        + fuel_wear_sensitivity
        * fuel_fraction
    )

    if is_safety_car_lap(
        lap,
        safety_car_start,
        safety_car_end
    ):

        wear_increment *= (
            safety_car_tyre_wear_multiplier
        )

    return wear_increment


# =============================================================
# TYRE MODEL
# =============================================================

def calculate_cliff_penalty(
        tyre_wear,
        cliff_threshold,
        cliff_severity):

    if tyre_wear <= cliff_threshold:

        return 0.0

    excess_wear = (
        tyre_wear
        - cliff_threshold
    )

    return (
        cliff_severity
        * (excess_wear ** 2)
    )


def calculate_tyre_loss(
        tyre_data,
        tyre_wear):

    linear_deg = tyre_data[1]

    quadratic_deg = tyre_data[2]

    cliff_threshold = tyre_data[5]

    cliff_severity = tyre_data[6]

    normal_loss = (
        linear_deg * tyre_wear
        + quadratic_deg
        * (tyre_wear ** 2)
    )

    cliff_loss = (
        calculate_cliff_penalty(
            tyre_wear,
            cliff_threshold,
            cliff_severity
        )
    )

    return (
        (
            normal_loss
            + cliff_loss
        )
        * tyre_degradation_scale
    )


def calculate_warmup_penalty(
        tyre_data,
        tyre_age):

    initial_penalty = tyre_data[3]

    recovery_rate = tyre_data[4]

    penalty = (
        initial_penalty
        - recovery_rate
        * tyre_age
    )

    if penalty < 0:

        penalty = 0.0

    return penalty


def calculate_lap_time(
        tyre_data,
        tyre_age,
        tyre_wear,
        lap,
        safety_car_start=None,
        safety_car_end=None,
        pace_offset=0.0):

    if is_safety_car_lap(
        lap,
        safety_car_start,
        safety_car_end
    ):

        return safety_car_lap_time

    tyre_loss = (
        calculate_tyre_loss(
            tyre_data,
            tyre_wear
        )
    )

    warmup_penalty = (
        calculate_warmup_penalty(
            tyre_data,
            tyre_age
        )
    )

    fuel_gain = (
        calculate_fuel_time_gain(
            lap
        )
    )

    return (
        tyre_data[0]
        + tyre_loss
        + warmup_penalty
        - fuel_gain
        + pace_offset
    )


# =============================================================
# PIT PLAN LEGALITY
# =============================================================

def pit_plan_is_legal(
        pit_laps):

    for i in range(
        len(pit_laps) - 1
    ):

        if (
            pit_laps[i]
            >= pit_laps[i + 1]
        ):

            return False

    if len(pit_laps) == 0:

        return True

    stint_lengths = [
        pit_laps[0]
    ]

    for i in range(
        1,
        len(pit_laps)
    ):

        stint_lengths.append(
            pit_laps[i]
            - pit_laps[i - 1]
        )

    stint_lengths.append(
        race_laps
        - pit_laps[-1]
    )

    for stint_length in stint_lengths:

        if stint_length < minimum_stint:

            return False

    return True


# =============================================================
# FIXED STRATEGY SIMULATION
# =============================================================

def simulate_fixed_strategy(
        tyre_sequence,
        pit_laps,
        safety_car_start=None,
        safety_car_end=None,
        pace_offset=0.0,
        return_trace=False):

    if (
        len(pit_laps)
        != len(tyre_sequence) - 1
    ):

        return None

    if not pit_plan_is_legal(
        pit_laps
    ):

        return None

    total_time = 0.0

    tyre_age = 0

    tyre_wear = 0.0

    stint_number = 0

    pit_number = 0

    lap_times = []

    cumulative_times = []

    for lap in range(
        1,
        race_laps + 1
    ):

        tyre_name = (
            tyre_sequence[
                stint_number
            ]
        )

        tyre_data = tyres[
            tyre_name
        ]

        lap_time = (
            calculate_lap_time(
                tyre_data,
                tyre_age,
                tyre_wear,
                lap,
                safety_car_start,
                safety_car_end,
                pace_offset
            )
        )

        total_time += lap_time

        tyre_age += 1

        tyre_wear += (
            calculate_fuel_wear_increment(
                lap,
                safety_car_start,
                safety_car_end
            )
        )

        if (
            pit_number < len(pit_laps)
            and lap
            == pit_laps[pit_number]
        ):

            total_time += (
                calculate_pit_loss(
                    lap,
                    safety_car_start,
                    safety_car_end
                )
            )

            tyre_age = 0

            tyre_wear = 0.0

            stint_number += 1

            pit_number += 1

        if return_trace:

            lap_times.append(
                lap_time
            )

            cumulative_times.append(
                total_time
            )

    if return_trace:

        return (
            total_time,
            lap_times,
            cumulative_times
        )

    return total_time


# =============================================================
# ONE-STOP OPTIMISATION
# =============================================================

def calculate_one_stop_strategy(
        first_tyre,
        second_tyre):

    tyre_sequence = [
        first_tyre,
        second_tyre
    ]

    pit_laps_tested = []

    race_times = []

    for pit_lap in range(
        minimum_stint,
        race_laps
        - minimum_stint
        + 1
    ):

        race_time = (
            simulate_fixed_strategy(
                tyre_sequence,
                [pit_lap]
            )
        )

        pit_laps_tested.append(
            pit_lap
        )

        race_times.append(
            race_time
        )

    best_time = min(
        race_times
    )

    best_index = race_times.index(
        best_time
    )

    return (
        pit_laps_tested[
            best_index
        ],
        best_time,
        pit_laps_tested,
        race_times
    )


# =============================================================
# TWO-STOP OPTIMISATION
# =============================================================

def calculate_two_stop_strategy(
        first_tyre,
        second_tyre,
        third_tyre):

    tyre_sequence = [
        first_tyre,
        second_tyre,
        third_tyre
    ]

    best_time = None

    best_pit_1 = None

    best_pit_2 = None

    for pit_lap_1 in range(
        minimum_stint,
        race_laps
        - (2 * minimum_stint)
        + 1
    ):

        for pit_lap_2 in range(
            pit_lap_1
            + minimum_stint,
            race_laps
            - minimum_stint
            + 1
        ):

            race_time = (
                simulate_fixed_strategy(
                    tyre_sequence,
                    [
                        pit_lap_1,
                        pit_lap_2
                    ]
                )
            )

            if (
                best_time is None
                or race_time < best_time
            ):

                best_time = race_time

                best_pit_1 = pit_lap_1

                best_pit_2 = pit_lap_2

    return (
        best_pit_1,
        best_pit_2,
        best_time
    )


# =============================================================
# FIND BEST ONE-STOP
# =============================================================

def find_best_one_stop():

    tyre_names = list(
        tyres.keys()
    )

    best_time = None

    best_strategy = None

    best_pit = None

    all_results = {}

    for first_tyre in tyre_names:

        for second_tyre in tyre_names:

            if first_tyre == second_tyre:

                continue

            result = (
                calculate_one_stop_strategy(
                    first_tyre,
                    second_tyre
                )
            )

            strategy_name = (
                first_tyre
                + " -> "
                + second_tyre
            )

            all_results[
                strategy_name
            ] = result

            if (
                best_time is None
                or result[1] < best_time
            ):

                best_time = result[1]

                best_strategy = (
                    first_tyre,
                    second_tyre
                )

                best_pit = result[0]

    return (
        best_strategy,
        best_pit,
        best_time,
        all_results
    )


# =============================================================
# FIND BEST TWO-STOP
# =============================================================

def find_best_two_stop():

    tyre_names = list(
        tyres.keys()
    )

    best_time = None

    best_strategy = None

    best_pit_1 = None

    best_pit_2 = None

    for first_tyre in tyre_names:

        for second_tyre in tyre_names:

            for third_tyre in tyre_names:

                if (
                    first_tyre
                    == second_tyre
                    == third_tyre
                ):

                    continue

                result = (
                    calculate_two_stop_strategy(
                        first_tyre,
                        second_tyre,
                        third_tyre
                    )
                )

                if (
                    best_time is None
                    or result[2] < best_time
                ):

                    best_time = result[2]

                    best_strategy = (
                        first_tyre,
                        second_tyre,
                        third_tyre
                    )

                    best_pit_1 = result[0]

                    best_pit_2 = result[1]

    return (
        best_strategy,
        best_pit_1,
        best_pit_2,
        best_time
    )


# =============================================================
# SAFETY CAR SCENARIOS
# =============================================================

def generate_safety_car_scenarios(
        number_of_races):

    random.seed(
        random_seed
    )

    scenarios = []

    for simulation in range(
        number_of_races
    ):

        if (
            random.random()
            < safety_car_probability
        ):

            start_lap = random.randint(
                safety_car_min_start,
                safety_car_max_start
            )

            duration = random.randint(
                safety_car_min_duration,
                safety_car_max_duration
            )

            end_lap = (
                start_lap
                + duration
                - 1
            )

            if end_lap > race_laps:

                end_lap = race_laps

            scenarios.append(
                (
                    start_lap,
                    end_lap
                )
            )

        else:

            scenarios.append(
                (
                    None,
                    None
                )
            )

    return scenarios


# =============================================================
# POSSIBLE SAFETY CAR END LAPS
# =============================================================

def possible_safety_car_end_laps(
        safety_car_start,
        current_lap):

    possible_end_laps = []

    for duration in range(
        safety_car_min_duration,
        safety_car_max_duration + 1
    ):

        end_lap = (
            safety_car_start
            + duration
            - 1
        )

        if (
            end_lap >= current_lap
            and end_lap <= race_laps
        ):

            possible_end_laps.append(
                end_lap
            )

    return possible_end_laps


# =============================================================
# EXPECTED SAFETY CAR PLAN TIME
# =============================================================

def calculate_expected_plan_time(
        tyre_sequence,
        pit_laps,
        safety_car_start,
        current_lap):

    possible_ends = (
        possible_safety_car_end_laps(
            safety_car_start,
            current_lap
        )
    )

    predicted_times = []

    for possible_end in possible_ends:

        predicted_times.append(

            simulate_fixed_strategy(
                tyre_sequence,
                pit_laps,
                safety_car_start,
                possible_end
            )
        )

    return (
        statistics.mean(
            predicted_times
        )
    )


# =============================================================
# UNCERTAINTY-AWARE SAFETY CAR STRATEGY
# =============================================================

def simulate_uncertainty_strategy(
        tyre_sequence,
        planned_pit_laps,
        safety_car_start=None,
        safety_car_end=None):

    if safety_car_start is None:

        return simulate_fixed_strategy(
            tyre_sequence,
            planned_pit_laps
        )

    adjusted_pits = list(
        planned_pit_laps
    )

    for pit_index in range(
        len(adjusted_pits)
    ):

        planned_pit = (
            adjusted_pits[
                pit_index
            ]
        )

        for current_lap in range(
            safety_car_start,
            safety_car_end + 1
        ):

            if current_lap >= planned_pit:

                break

            pit_now_plan = list(
                adjusted_pits
            )

            pit_now_plan[
                pit_index
            ] = current_lap

            if not pit_plan_is_legal(
                pit_now_plan
            ):

                continue

            stay_expected = (
                calculate_expected_plan_time(
                    tyre_sequence,
                    adjusted_pits,
                    safety_car_start,
                    current_lap
                )
            )

            pit_expected = (
                calculate_expected_plan_time(
                    tyre_sequence,
                    pit_now_plan,
                    safety_car_start,
                    current_lap
                )
            )

            if (
                pit_expected
                < stay_expected
            ):

                adjusted_pits = (
                    pit_now_plan
                )

                break

    return simulate_fixed_strategy(
        tyre_sequence,
        adjusted_pits,
        safety_car_start,
        safety_car_end
    )


# =============================================================
# DIRTY AIR
# =============================================================

def calculate_dirty_air_penalty(
        gap_to_car_ahead):

    if not dirty_air_enabled:

        return 0.0

    if gap_to_car_ahead <= 0:

        return 0.0

    if gap_to_car_ahead > dirty_air_range:

        return 0.0

    gap_fraction = (
        gap_to_car_ahead
        / dirty_air_range
    )

    return (
        dirty_air_max_penalty
        * (1.0 - gap_fraction)
    )


# =============================================================
# OVERTAKING AID
# =============================================================

def calculate_drs_gain(
        lap,
        gap_to_car_ahead):

    if not drs_enabled:

        return 0.0

    if lap < drs_activation_lap:

        return 0.0

    if (
        gap_to_car_ahead <= 0
        or gap_to_car_ahead
        > drs_detection_range
    ):

        return 0.0

    return drs_time_gain


def calculate_required_overtake_margin(
        current_drs_gain):

    required_margin = (
        overtake_margin
    )

    if current_drs_gain > 0:

        required_margin -= (
            drs_overtake_margin_reduction
        )

    return max(
        0.0,
        required_margin
    )


# =============================================================
# FIELD COPY
# =============================================================

def copy_field_configuration(
        our_pit_lap):

    copied_field = []

    for car in field_configuration:

        new_car = {

            "name":
                car["name"],

            "start_gap":
                car["start_gap"],

            "tyre_sequence":
                list(
                    car[
                        "tyre_sequence"
                    ]
                ),

            "pit_laps":
                list(
                    car[
                        "pit_laps"
                    ]
                ),

            "pace_offset":
                car[
                    "pace_offset"
                ]
        }

        if (
            new_car["name"]
            == "Our Car"
        ):

            new_car[
                "pit_laps"
            ] = [
                our_pit_lap
            ]

        copied_field.append(
            new_car
        )

    return copied_field


# =============================================================
# SMALL FIELD SIMULATION
# =============================================================

def simulate_small_field(
        our_pit_lap):

    field = (
        copy_field_configuration(
            our_pit_lap
        )
    )

    states = {}

    for car in field:

        states[
            car["name"]
        ] = {

            "total_time":
                car["start_gap"],

            "tyre_age":
                0,

            "tyre_wear":
                0.0,

            "stint":
                0
        }

    position_history = []

    for lap in range(
        1,
        race_laps + 1
    ):

        running_order = sorted(

            field,

            key=lambda car:
                states[
                    car["name"]
                ]["total_time"]
        )

        lap_times = {}

        drs_gains = {}

        pitting = {}

        for index in range(
            len(running_order)
        ):

            car = (
                running_order[
                    index
                ]
            )

            name = car["name"]

            state = states[name]

            tyre_name = (
                car[
                    "tyre_sequence"
                ][
                    state["stint"]
                ]
            )

            lap_time = (
                calculate_lap_time(
                    tyres[
                        tyre_name
                    ],
                    state[
                        "tyre_age"
                    ],
                    state[
                        "tyre_wear"
                    ],
                    lap,
                    pace_offset=
                        car[
                            "pace_offset"
                        ]
                )
            )

            current_drs = 0.0

            if index > 0:

                ahead_name = (
                    running_order[
                        index - 1
                    ]["name"]
                )

                gap = (
                    state["total_time"]
                    - states[
                        ahead_name
                    ]["total_time"]
                )

                lap_time += (
                    calculate_dirty_air_penalty(
                        gap
                    )
                )

                current_drs = (
                    calculate_drs_gain(
                        lap,
                        gap
                    )
                )

                lap_time -= current_drs

            car_pitting = (
                lap
                in car["pit_laps"]
            )

            if car_pitting:

                lap_time += (
                    normal_pit_loss
                )

            lap_times[name] = lap_time

            drs_gains[name] = current_drs

            pitting[name] = car_pitting

        predicted_times = {}

        for car in field:

            name = car["name"]

            predicted_times[name] = (
                states[name][
                    "total_time"
                ]
                + lap_times[name]
            )

        adjusted_times = (
            predicted_times.copy()
        )

        for index in range(
            1,
            len(running_order)
        ):

            following_name = (
                running_order[
                    index
                ]["name"]
            )

            ahead_name = (
                running_order[
                    index - 1
                ]["name"]
            )

            if (
                pitting[
                    following_name
                ]
                or pitting[
                    ahead_name
                ]
            ):

                continue

            if (
                adjusted_times[
                    following_name
                ]
                < adjusted_times[
                    ahead_name
                ]
            ):

                pace_advantage = (
                    lap_times[
                        ahead_name
                    ]
                    - lap_times[
                        following_name
                    ]
                )

                required_margin = (
                    calculate_required_overtake_margin(
                        drs_gains[
                            following_name
                        ]
                    )
                )

                if (
                    pace_advantage
                    < required_margin
                ):

                    adjusted_times[
                        following_name
                    ] = (
                        adjusted_times[
                            ahead_name
                        ]
                        + minimum_following_gap
                    )

        for car in field:

            name = car["name"]

            states[name][
                "total_time"
            ] = (
                adjusted_times[
                    name
                ]
            )

            states[name][
                "tyre_age"
            ] += 1

            states[name][
                "tyre_wear"
            ] += (
                calculate_fuel_wear_increment(
                    lap
                )
            )

            if pitting[name]:

                states[name][
                    "tyre_age"
                ] = 0

                states[name][
                    "tyre_wear"
                ] = 0.0

                states[name][
                    "stint"
                ] += 1

        new_order = sorted(

            field,

            key=lambda car:
                states[
                    car["name"]
                ]["total_time"]
        )

        names = [
            car["name"]
            for car in new_order
        ]

        position_history.append(
            names.index(
                "Our Car"
            )
            + 1
        )

    final_order = sorted(

        field,

        key=lambda car:
            states[
                car["name"]
            ]["total_time"]
    )

    names = [
        car["name"]
        for car in final_order
    ]

    return {

        "final_position":
            names.index(
                "Our Car"
            )
            + 1,

        "our_final_time":
            states[
                "Our Car"
            ]["total_time"],

        "position_history":
            position_history
    }


def find_best_field_pit():

    results = []

    for pit_lap in range(
        field_pit_search_start,
        field_pit_search_end + 1
    ):

        result = (
            simulate_small_field(
                pit_lap
            )
        )

        results.append(
            (
                pit_lap,
                result
            )
        )

    best = min(

        results,

        key=lambda item:
            (
                item[1][
                    "final_position"
                ],
                item[1][
                    "our_final_time"
                ]
            )
    )

    return (
        best[0],
        best[1],
        results
    )


# =============================================================
# SENSITIVITY ANALYSIS
# =============================================================

def run_pit_loss_sensitivity():

    global normal_pit_loss

    original_value = (
        normal_pit_loss
    )

    values = list(
        range(
            10,
            61,
            5
        )
    )

    gaps = []

    for value in values:

        normal_pit_loss = float(
            value
        )

        one = (
            find_best_one_stop()
        )

        two = (
            find_best_two_stop()
        )

        gaps.append(
            two[3]
            - one[2]
        )

    normal_pit_loss = (
        original_value
    )

    return (
        values,
        gaps
    )


def find_strategy_switch_point(
        x_values,
        y_values):

    for i in range(
        len(x_values) - 1
    ):

        first_y = y_values[i]

        second_y = y_values[
            i + 1
        ]

        if first_y == 0:

            return x_values[i]

        if (
            first_y
            * second_y
            < 0
        ):

            first_x = x_values[i]

            second_x = (
                x_values[
                    i + 1
                ]
            )

            return (
                first_x
                + (
                    -first_y
                    * (
                        second_x
                        - first_x
                    )
                    / (
                        second_y
                        - first_y
                    )
                )
            )

    return None


def run_degradation_sensitivity():

    global tyre_degradation_scale

    original_value = (
        tyre_degradation_scale
    )

    scales = [
        0.70,
        0.80,
        0.90,
        1.00,
        1.10,
        1.20,
        1.30
    ]

    gaps = []

    for scale in scales:

        tyre_degradation_scale = (
            scale
        )

        one = (
            find_best_one_stop()
        )

        two = (
            find_best_two_stop()
        )

        gaps.append(
            two[3]
            - one[2]
        )

    tyre_degradation_scale = (
        original_value
    )

    return (
        scales,
        gaps
    )


# =============================================================
# =============================================================
#
# REAL-WORLD VALIDATION
#
# =============================================================
# =============================================================


# =============================================================
# REAL-RACE FUEL MODEL
# =============================================================
#
# Instead of assuming 2 kg/lap for every circuit, the 100 kg
# illustrative starting fuel is distributed across the actual
# race distance.
#
# =============================================================

def calculate_real_fuel_gain(
        lap,
        actual_race_laps):

    burn_per_lap = (
        initial_fuel_mass
        / actual_race_laps
    )

    fuel_burned = (
        burn_per_lap
        * (lap - 1)
    )

    return (
        fuel_burned
        * fuel_time_per_kg
    )


def calculate_real_wear_increment(
        lap,
        actual_race_laps):

    remaining_fraction = (
        1.0
        - (
            (lap - 1)
            / actual_race_laps
        )
    )

    remaining_fraction = max(
        0.0,
        remaining_fraction
    )

    return (
        1.0
        + fuel_wear_sensitivity
        * remaining_fraction
    )


# =============================================================
# LOCAL OUTLIER FILTER
# =============================================================

def apply_real_outlier_filter(
        rows):

    candidates = []

    for row in rows:

        if len(
            row[
                "removal_reasons"
            ]
        ) == 0:

            candidates.append(
                row
            )

    for index in range(
        len(candidates)
    ):

        neighbours = []

        start = max(
            0,
            index
            - real_outlier_window
        )

        end = min(
            len(candidates),
            index
            + real_outlier_window
            + 1
        )

        for neighbour_index in range(
            start,
            end
        ):

            if (
                neighbour_index
                == index
            ):

                continue

            neighbours.append(
                candidates[
                    neighbour_index
                ][
                    "lap_time"
                ]
            )

        if len(neighbours) >= 2:

            local_median = (
                statistics.median(
                    neighbours
                )
            )

            difference = abs(
                candidates[
                    index
                ][
                    "lap_time"
                ]
                - local_median
            )

            if (
                difference
                > real_outlier_threshold
            ):

                candidates[
                    index
                ][
                    "removal_reasons"
                ].append(
                    "Local lap-time outlier"
                )

    return rows


# =============================================================
# DOWNLOAD AND CLEAN REAL F1 DATA
# =============================================================

def load_real_world_stints():

    try:

        import fastf1
        import pandas as pd

    except ImportError:

        raise RuntimeError(
            "\nFastF1 is required for real-world validation.\n"
            "Install it with:\n\n"
            "py -3.12 -m pip install "
            "fastf1==3.8.3 pandas==2.3.3\n"
        )

    fastf1.Cache.enable_cache(
        fastf1_cache_folder
    )

    print()

    print(
        "Downloading real F1 race data..."
    )

    print(
        real_validation_year,
        real_validation_event,
        real_validation_session
    )

    session = fastf1.get_session(
        real_validation_year,
        real_validation_event,
        real_validation_session
    )

    session.load(
        laps=True,
        telemetry=False,
        weather=False,
        messages=False
    )

    laps = session.laps.copy()

    if len(laps) == 0:

        raise RuntimeError(
            "FastF1 returned no lap data."
        )

    actual_race_laps = int(
        laps[
            "LapNumber"
        ].dropna().max()
    )

    grouped_stints = {}

    group_columns = [
        "Driver",
        "Stint"
    ]

    grouped = laps.groupby(
        group_columns,
        dropna=True
    )

    for (
        driver,
        stint_number
    ), group in grouped:

        group = group.sort_values(
            "LapNumber"
        )

        available_compounds = (
            group[
                "Compound"
            ]
            .dropna()
            .astype(str)
        )

        if len(
            available_compounds
        ) == 0:

            continue

        compound = (
            available_compounds
            .mode()
            .iloc[0]
            .upper()
        )

        if compound not in [
            "SOFT",
            "MEDIUM",
            "HARD"
        ]:

            continue

        fresh_tyre = None

        if (
            "FreshTyre"
            in group.columns
        ):

            fresh_values = (
                group[
                    "FreshTyre"
                ].dropna()
            )

            if len(
                fresh_values
            ) > 0:

                fresh_tyre = bool(
                    fresh_values.iloc[0]
                )

        if (
            real_require_fresh_tyre
            and fresh_tyre is not True
        ):

            continue

        tyre_age = 0

        tyre_wear = 0.0

        processed_rows = []

        for row_index, lap_row in (
            group.iterrows()
        ):

            if pd.isna(
                lap_row[
                    "LapNumber"
                ]
            ):

                continue

            lap_number = int(
                lap_row[
                    "LapNumber"
                ]
            )

            reasons = []

            lap_time = None

            if pd.isna(
                lap_row[
                    "LapTime"
                ]
            ):

                reasons.append(
                    "Missing lap time"
                )

            else:

                lap_time = (
                    lap_row[
                        "LapTime"
                    ].total_seconds()
                )

            if lap_number == 1:

                reasons.append(
                    "Race-start lap"
                )

            if (
                "PitInTime"
                in group.columns
                and pd.notna(
                    lap_row[
                        "PitInTime"
                    ]
                )
            ):

                reasons.append(
                    "Pit in-lap"
                )

            if (
                "PitOutTime"
                in group.columns
                and pd.notna(
                    lap_row[
                        "PitOutTime"
                    ]
                )
            ):

                reasons.append(
                    "Pit out-lap"
                )

            if (
                "IsAccurate"
                in group.columns
            ):

                accurate_value = (
                    lap_row[
                        "IsAccurate"
                    ]
                )

                if (
                    pd.isna(
                        accurate_value
                    )
                    or not bool(
                        accurate_value
                    )
                ):

                    reasons.append(
                        "FastF1 inaccurate lap"
                    )

            if (
                "TrackStatus"
                in group.columns
            ):

                track_status = str(
                    lap_row[
                        "TrackStatus"
                    ]
                )

                if track_status != "1":

                    reasons.append(
                        "Non-green track status"
                    )

            row_compound = str(
                lap_row[
                    "Compound"
                ]
            ).upper()

            if row_compound != compound:

                reasons.append(
                    "Compound inconsistency"
                )

            if (
                tyre_age
                < real_minimum_tyre_age
            ):

                reasons.append(
                    "Early warm-up phase"
                )

            processed_rows.append(
                {
                    "driver":
                        str(
                            driver
                        ),

                    "stint":
                        int(
                            stint_number
                        ),

                    "compound":
                        compound,

                    "lap_number":
                        lap_number,

                    "lap_time":
                        lap_time,

                    "tyre_age":
                        tyre_age,

                    "tyre_wear":
                        tyre_wear,

                    "fresh_tyre":
                        fresh_tyre,

                    "removal_reasons":
                        reasons
                }
            )

            tyre_age += 1

            tyre_wear += (
                calculate_real_wear_increment(
                    lap_number,
                    actual_race_laps
                )
            )

        # Remove rows with no usable numeric lap time
        # before outlier calculation.

        usable_for_outlier = []

        for row in processed_rows:

            if row[
                "lap_time"
            ] is not None:

                usable_for_outlier.append(
                    row
                )

        apply_real_outlier_filter(
            usable_for_outlier
        )

        clean_rows = []

        for row in processed_rows:

            if (
                row[
                    "lap_time"
                ] is not None
                and len(
                    row[
                        "removal_reasons"
                    ]
                ) == 0
            ):

                clean_rows.append(
                    row
                )

        if (
            len(clean_rows)
            >= real_minimum_clean_laps
        ):

            key = (
                str(driver),
                int(stint_number),
                compound
            )

            grouped_stints[
                key
            ] = clean_rows

    if len(
        grouped_stints
    ) == 0:

        raise RuntimeError(
            "No suitable real tyre stints remained "
            "after cleaning."
        )

    return (
        grouped_stints,
        actual_race_laps
    )


# =============================================================
# CHOOSE REAL VALIDATION COMPOUND
# =============================================================

def choose_real_validation_stints(
        all_stints):

    compound_stints = {

        "SOFT": [],
        "MEDIUM": [],
        "HARD": []
    }

    for key in all_stints:

        compound = key[2]

        if compound in compound_stints:

            compound_stints[
                compound
            ].append(
                key
            )

    if (
        real_validation_compound
        != "AUTO"
    ):

        selected_compound = (
            real_validation_compound.upper()
        )

    else:

        selected_compound = max(

            compound_stints,

            key=lambda compound:
                len(
                    set(
                        key[0]
                        for key
                        in compound_stints[
                            compound
                        ]
                    )
                )
        )

    candidates = list(
        compound_stints[
            selected_compound
        ]
    )

    if len(candidates) < 2:

        raise RuntimeError(
            "Not enough "
            + selected_compound
            + " stints for validation."
        )

    # ---------------------------------------------------------
    # Prefer one long stint per different driver.
    # ---------------------------------------------------------

    candidates.sort(

        key=lambda key:
            len(
                all_stints[
                    key
                ]
            ),

        reverse=True
    )

    selected = []

    used_drivers = set()

    for key in candidates:

        driver = key[0]

        if driver not in used_drivers:

            selected.append(
                key
            )

            used_drivers.add(
                driver
            )

        if (
            len(selected)
            >= real_maximum_validation_stints
        ):

            break

    # If necessary, fill remaining places with
    # additional stints.

    if len(selected) < 2:

        for key in candidates:

            if key not in selected:

                selected.append(
                    key
                )

            if len(selected) >= 2:

                break

    return (
        selected_compound,
        selected
    )


# =============================================================
# REAL DEGRADATION COMPONENT
# =============================================================
#
# We deliberately exclude:
#
# - absolute base pace
# - dirty air
# - DRS
# - pit loss
#
# The validation target is RELATIVE tyre-stint evolution.
#
# =============================================================

def calculate_real_model_component(
        row,
        linear_coefficient,
        quadratic_coefficient,
        actual_race_laps):

    tyre_loss = (
        linear_coefficient
        * row[
            "tyre_wear"
        ]

        + quadratic_coefficient
        * (
            row[
                "tyre_wear"
            ] ** 2
        )
    )

    fuel_gain = (
        calculate_real_fuel_gain(
            row[
                "lap_number"
            ],
            actual_race_laps
        )
    )

    return (
        tyre_loss
        - fuel_gain
    )


# =============================================================
# CONVERT STINT TO RELATIVE LAP-TIME CHANGE
# =============================================================

def calculate_stint_relative_values(
        rows,
        linear_coefficient,
        quadratic_coefficient,
        actual_race_laps):

    if len(rows) < 2:

        return (
            [],
            []
        )

    reference_row = rows[0]

    observed_reference = (
        reference_row[
            "lap_time"
        ]
    )

    predicted_reference = (
        calculate_real_model_component(
            reference_row,
            linear_coefficient,
            quadratic_coefficient,
            actual_race_laps
        )
    )

    observed_deltas = []

    predicted_deltas = []

    # The reference itself is not included in RMSE,
    # because its delta is exactly zero by definition.

    for row in rows[1:]:

        observed_delta = (
            row[
                "lap_time"
            ]
            - observed_reference
        )

        predicted_component = (
            calculate_real_model_component(
                row,
                linear_coefficient,
                quadratic_coefficient,
                actual_race_laps
            )
        )

        predicted_delta = (
            predicted_component
            - predicted_reference
        )

        observed_deltas.append(
            observed_delta
        )

        predicted_deltas.append(
            predicted_delta
        )

    return (
        observed_deltas,
        predicted_deltas
    )


# =============================================================
# EVALUATE MODEL ACROSS MULTIPLE REAL STINTS
# =============================================================

def evaluate_real_model(
        all_stints,
        stint_keys,
        linear_coefficient,
        quadratic_coefficient,
        actual_race_laps):

    all_observed = []

    all_predicted = []

    for key in stint_keys:

        (
            observed,
            predicted

        ) = calculate_stint_relative_values(

            all_stints[
                key
            ],

            linear_coefficient,

            quadratic_coefficient,

            actual_race_laps
        )

        all_observed.extend(
            observed
        )

        all_predicted.extend(
            predicted
        )

    return {

        "rmse":
            calculate_rmse(
                all_predicted,
                all_observed
            ),

        "mae":
            calculate_mae(
                all_predicted,
                all_observed
            ),

        "observed":
            all_observed,

        "predicted":
            all_predicted
    }


# =============================================================
# FIT REAL DEGRADATION MODEL
# =============================================================

def fit_real_degradation_model(
        all_stints,
        training_keys,
        actual_race_laps):

    linear_values = (
        create_float_range(
            real_linear_min,
            real_linear_max,
            real_linear_step
        )
    )

    quadratic_values = (
        create_float_range(
            real_quadratic_min,
            real_quadratic_max,
            real_quadratic_step
        )
    )

    best_rmse = None

    best_linear = None

    best_quadratic = None

    combinations_tested = 0

    for linear in linear_values:

        for quadratic in quadratic_values:

            combinations_tested += 1

            evaluation = (
                evaluate_real_model(
                    all_stints,
                    training_keys,
                    linear,
                    quadratic,
                    actual_race_laps
                )
            )

            if (
                best_rmse is None
                or evaluation[
                    "rmse"
                ] < best_rmse
            ):

                best_rmse = (
                    evaluation[
                        "rmse"
                    ]
                )

                best_linear = linear

                best_quadratic = (
                    quadratic
                )

    return {

        "linear":
            best_linear,

        "quadratic":
            best_quadratic,

        "training_rmse":
            best_rmse,

        "combinations_tested":
            combinations_tested
    }


# =============================================================
# LEAVE-ONE-STINT-OUT REAL CROSS-VALIDATION
# =============================================================

def run_real_world_validation():

    (
        all_stints,
        actual_race_laps

    ) = load_real_world_stints()

    (
        selected_compound,
        selected_keys

    ) = choose_real_validation_stints(
        all_stints
    )

    simulator_name = (
        selected_compound.title()
    )

    baseline_tyre = tyres[
        simulator_name
    ]

    baseline_linear = (
        baseline_tyre[1]
    )

    baseline_quadratic = (
        baseline_tyre[2]
    )

    fold_results = []

    print()

    print(
        "========================================"
    )

    print(
        "REAL-WORLD VALIDATION"
    )

    print(
        "========================================"
    )

    print()

    print(
        "Race:",
        real_validation_year,
        real_validation_event
    )

    print(
        "Observed race laps:",
        actual_race_laps
    )

    print(
        "Selected compound:",
        selected_compound
    )

    print(
        "Selected stints:",
        len(
            selected_keys
        )
    )

    print()

    for validation_key in (
        selected_keys
    ):

        training_keys = []

        for key in selected_keys:

            if key != validation_key:

                training_keys.append(
                    key
                )

        fitted_model = (
            fit_real_degradation_model(
                all_stints,
                training_keys,
                actual_race_laps
            )
        )

        baseline_validation = (
            evaluate_real_model(
                all_stints,
                [
                    validation_key
                ],
                baseline_linear,
                baseline_quadratic,
                actual_race_laps
            )
        )

        calibrated_validation = (
            evaluate_real_model(
                all_stints,
                [
                    validation_key
                ],
                fitted_model[
                    "linear"
                ],
                fitted_model[
                    "quadratic"
                ],
                actual_race_laps
            )
        )

        fold_results.append(
            {
                "validation_key":
                    validation_key,

                "linear":
                    fitted_model[
                        "linear"
                    ],

                "quadratic":
                    fitted_model[
                        "quadratic"
                    ],

                "baseline_rmse":
                    baseline_validation[
                        "rmse"
                    ],

                "calibrated_rmse":
                    calibrated_validation[
                        "rmse"
                    ],

                "calibrated_mae":
                    calibrated_validation[
                        "mae"
                    ]
            }
        )

    baseline_rmse_values = [
        fold[
            "baseline_rmse"
        ]
        for fold in fold_results
    ]

    calibrated_rmse_values = [
        fold[
            "calibrated_rmse"
        ]
        for fold in fold_results
    ]

    calibrated_mae_values = [
        fold[
            "calibrated_mae"
        ]
        for fold in fold_results
    ]

    mean_baseline_rmse = (
        statistics.mean(
            baseline_rmse_values
        )
    )

    mean_calibrated_rmse = (
        statistics.mean(
            calibrated_rmse_values
        )
    )

    mean_calibrated_mae = (
        statistics.mean(
            calibrated_mae_values
        )
    )

    if len(
        calibrated_rmse_values
    ) > 1:

        rmse_standard_deviation = (
            statistics.stdev(
                calibrated_rmse_values
            )
        )

    else:

        rmse_standard_deviation = 0.0

    improved_folds = 0

    for fold in fold_results:

        if (
            fold[
                "calibrated_rmse"
            ]
            < fold[
                "baseline_rmse"
            ]
        ):

            improved_folds += 1

    # ---------------------------------------------------------
    # Final fit using ALL selected real stints.
    #
    # This is the deployment fit.
    #
    # It is NOT a validation result.
    # ---------------------------------------------------------

    final_model = (
        fit_real_degradation_model(
            all_stints,
            selected_keys,
            actual_race_laps
        )
    )

    final_evaluation = (
        evaluate_real_model(
            all_stints,
            selected_keys,
            final_model[
                "linear"
            ],
            final_model[
                "quadratic"
            ],
            actual_race_laps
        )
    )

    improvement_percentage = (

        (
            mean_baseline_rmse
            - mean_calibrated_rmse
        )

        / mean_baseline_rmse

        * 100.0
    )

    return {

        "all_stints":
            all_stints,

        "selected_keys":
            selected_keys,

        "compound":
            selected_compound,

        "simulator_name":
            simulator_name,

        "actual_race_laps":
            actual_race_laps,

        "fold_results":
            fold_results,

        "mean_baseline_rmse":
            mean_baseline_rmse,

        "mean_calibrated_rmse":
            mean_calibrated_rmse,

        "mean_calibrated_mae":
            mean_calibrated_mae,

        "rmse_standard_deviation":
            rmse_standard_deviation,

        "worst_rmse":
            max(
                calibrated_rmse_values
            ),

        "improved_folds":
            improved_folds,

        "improvement_percentage":
            improvement_percentage,

        "final_linear":
            final_model[
                "linear"
            ],

        "final_quadratic":
            final_model[
                "quadratic"
            ],

        "final_fit_rmse":
            final_evaluation[
                "rmse"
            ]
    }


# =============================================================
# EXPORT CLEAN REAL DATA
# =============================================================

def export_real_validation_data(
        validation_result):

    filename = os.path.join(
        results_folder,
        "real_validation_clean_laps.csv"
    )

    with open(
        filename,
        "w",
        newline=""
    ) as file:

        writer = csv.writer(
            file
        )

        writer.writerow(
            [
                "driver",
                "stint",
                "compound",
                "lap_number",
                "lap_time",
                "tyre_age",
                "effective_tyre_wear"
            ]
        )

        for key in (
            validation_result[
                "selected_keys"
            ]
        ):

            rows = (
                validation_result[
                    "all_stints"
                ][
                    key
                ]
            )

            for row in rows:

                writer.writerow(
                    [
                        row[
                            "driver"
                        ],
                        row[
                            "stint"
                        ],
                        row[
                            "compound"
                        ],
                        row[
                            "lap_number"
                        ],
                        row[
                            "lap_time"
                        ],
                        row[
                            "tyre_age"
                        ],
                        row[
                            "tyre_wear"
                        ]
                    ]
                )


# =============================================================
# EXPORT REAL VALIDATION SUMMARY
# =============================================================

def export_real_validation_summary(
        result):

    filename = os.path.join(
        results_folder,
        "real_validation_results.txt"
    )

    with open(
        filename,
        "w"
    ) as file:

        file.write(
            "REAL-WORLD TYRE DEGRADATION VALIDATION\n"
        )

        file.write(
            "======================================\n\n"
        )

        file.write(
            "Race: "
            + str(
                real_validation_year
            )
            + " "
            + str(
                real_validation_event
            )
            + "\n"
        )

        file.write(
            "Compound: "
            + result[
                "compound"
            ]
            + "\n"
        )

        file.write(
            "Cross-validation stints: "
            + str(
                len(
                    result[
                        "selected_keys"
                    ]
                )
            )
            + "\n\n"
        )

        file.write(
            "Mean baseline held-out RMSE: "
            + f"{result['mean_baseline_rmse']:.4f}"
            + " s\n"
        )

        file.write(
            "Mean calibrated held-out RMSE: "
            + f"{result['mean_calibrated_rmse']:.4f}"
            + " s\n"
        )

        file.write(
            "Mean calibrated held-out MAE: "
            + f"{result['mean_calibrated_mae']:.4f}"
            + " s\n"
        )

        file.write(
            "Held-out RMSE standard deviation: "
            + f"{result['rmse_standard_deviation']:.4f}"
            + " s\n"
        )

        file.write(
            "Worst held-out RMSE: "
            + f"{result['worst_rmse']:.4f}"
            + " s\n"
        )

        file.write(
            "Folds improved: "
            + str(
                result[
                    "improved_folds"
                ]
            )
            + "/"
            + str(
                len(
                    result[
                        "fold_results"
                    ]
                )
            )
            + "\n"
        )

        file.write(
            "Mean RMSE improvement: "
            + f"{result['improvement_percentage']:.2f}"
            + "%\n\n"
        )

        file.write(
            "Final all-data linear coefficient: "
            + str(
                result[
                    "final_linear"
                ]
            )
            + "\n"
        )

        file.write(
            "Final all-data quadratic coefficient: "
            + str(
                result[
                    "final_quadratic"
                ]
            )
            + "\n"
        )

        file.write(
            "Final all-data fit RMSE: "
            + f"{result['final_fit_rmse']:.4f}"
            + " s\n\n"
        )

        file.write(
            "IMPORTANT LIMITATION:\n"
        )

        file.write(
            "Validation evaluates relative lap-time "
            "evolution through real tyre stints. "
            "It does not validate absolute F1 car pace "
            "or the complete race simulator.\n"
        )


# =============================================================
# RUN REAL-WORLD VALIDATION
# =============================================================

real_validation_result = None

if real_validation_enabled:

    real_validation_result = (
        run_real_world_validation()
    )

    export_real_validation_data(
        real_validation_result
    )

    export_real_validation_summary(
        real_validation_result
    )

    # ---------------------------------------------------------
    # OPTIONAL: apply real fitted coefficients
    # ---------------------------------------------------------

    if (
        apply_real_calibration_to_strategy_model
    ):

        target_name = (
            real_validation_result[
                "simulator_name"
            ]
        )

        old_data = tyres[
            target_name
        ]

        tyres[
            target_name
        ] = (

            old_data[0],

            real_validation_result[
                "final_linear"
            ],

            real_validation_result[
                "final_quadratic"
            ],

            old_data[3],

            old_data[4],

            old_data[5],

            old_data[6]
        )


# =============================================================
# RUN BASELINE OPTIMISATION
# =============================================================

one_stop_result = (
    find_best_one_stop()
)

best_one_strategy = (
    one_stop_result[0]
)

best_one_pit = (
    one_stop_result[1]
)

best_one_time = (
    one_stop_result[2]
)

one_stop_results = (
    one_stop_result[3]
)


two_stop_result = (
    find_best_two_stop()
)

best_two_strategy = (
    two_stop_result[0]
)

best_two_pit_1 = (
    two_stop_result[1]
)

best_two_pit_2 = (
    two_stop_result[2]
)

best_two_time = (
    two_stop_result[3]
)


# =============================================================
# MONTE CARLO
# =============================================================

scenarios = (
    generate_safety_car_scenarios(
        monte_carlo_runs
    )
)

fixed_one_times = []

reactive_one_times = []

fixed_two_times = []

reactive_two_times = []


for (
    sc_start,
    sc_end
) in scenarios:

    fixed_one_times.append(

        simulate_fixed_strategy(
            list(
                best_one_strategy
            ),
            [
                best_one_pit
            ],
            sc_start,
            sc_end
        )
    )

    reactive_one_times.append(

        simulate_uncertainty_strategy(
            list(
                best_one_strategy
            ),
            [
                best_one_pit
            ],
            sc_start,
            sc_end
        )
    )

    fixed_two_times.append(

        simulate_fixed_strategy(
            list(
                best_two_strategy
            ),
            [
                best_two_pit_1,
                best_two_pit_2
            ],
            sc_start,
            sc_end
        )
    )

    reactive_two_times.append(

        simulate_uncertainty_strategy(
            list(
                best_two_strategy
            ),
            [
                best_two_pit_1,
                best_two_pit_2
            ],
            sc_start,
            sc_end
        )
    )


# =============================================================
# FIELD OPTIMISATION
# =============================================================

(
    best_field_pit,
    best_field_result,
    field_search_results

) = find_best_field_pit()


# =============================================================
# SENSITIVITY ANALYSIS
# =============================================================

(
    pit_loss_values,
    pit_loss_gaps

) = run_pit_loss_sensitivity()


pit_loss_switch = (
    find_strategy_switch_point(
        pit_loss_values,
        pit_loss_gaps
    )
)


(
    degradation_scales,
    degradation_gaps

) = run_degradation_sensitivity()


# =============================================================
# PRINT FINAL RESULTS
# =============================================================

print()

print(
    "========================================"
)

print(
    "FINAL RACE STRATEGY SIMULATOR"
)

print(
    "========================================"
)

print()

print(
    "BEST ONE-STOP"
)

print(
    "Strategy:",
    " -> ".join(
        best_one_strategy
    )
)

print(
    "Pit lap:",
    best_one_pit
)

print(
    f"Race time: "
    f"{best_one_time:.3f} s"
)

print()

print(
    "BEST TWO-STOP"
)

print(
    "Strategy:",
    " -> ".join(
        best_two_strategy
    )
)

print(
    "Pit laps:",
    best_two_pit_1,
    "and",
    best_two_pit_2
)

print(
    f"Race time: "
    f"{best_two_time:.3f} s"
)

print()

print(
    f"Two-stop advantage: "
    f"{best_one_time - best_two_time:.3f} s"
)

print()

print(
    "BEST SMALL-FIELD PIT:"
)

print(
    "Pit lap:",
    best_field_pit
)

print(
    "Finish: P"
    + str(
        best_field_result[
            "final_position"
        ]
    )
)

print()

print(
    "MONTE CARLO"
)

print(
    f"One-stop fixed mean: "
    f"{statistics.mean(fixed_one_times):.3f} s"
)

print(
    f"One-stop uncertainty-aware mean: "
    f"{statistics.mean(reactive_one_times):.3f} s"
)

print(
    f"Two-stop fixed mean: "
    f"{statistics.mean(fixed_two_times):.3f} s"
)

print(
    f"Two-stop uncertainty-aware mean: "
    f"{statistics.mean(reactive_two_times):.3f} s"
)

print()

if pit_loss_switch is not None:

    print(
        "Approximate one/two-stop pit-loss crossover:",
        f"{pit_loss_switch:.2f} s"
    )


# =============================================================
# PRINT REAL-WORLD VALIDATION
# =============================================================

if real_validation_result is not None:

    result = (
        real_validation_result
    )

    print()

    print(
        "========================================"
    )

    print(
        "REAL-WORLD VALIDATION SUMMARY"
    )

    print(
        "========================================"
    )

    print()

    print(
        "Source:",
        real_validation_year,
        real_validation_event,
        "Grand Prix race"
    )

    print(
        "Compound:",
        result[
            "compound"
        ]
    )

    print(
        "Whole stints cross-validated:",
        len(
            result[
                "selected_keys"
            ]
        )
    )

    print()

    for index in range(
        len(
            result[
                "fold_results"
            ]
        )
    ):

        fold = (
            result[
                "fold_results"
            ][
                index
            ]
        )

        key = (
            fold[
                "validation_key"
            ]
        )

        print(
            "Fold",
            index + 1,
            "- held out:",
            key[0],
            "stint",
            key[1]
        )

        print(
            "  Linear:",
            fold[
                "linear"
            ]
        )

        print(
            "  Quadratic:",
            fold[
                "quadratic"
            ]
        )

        print(
            f"  Baseline RMSE: "
            f"{fold['baseline_rmse']:.4f} s"
        )

        print(
            f"  Calibrated RMSE: "
            f"{fold['calibrated_rmse']:.4f} s"
        )

        print()

    print(
        f"Mean baseline held-out RMSE: "
        f"{result['mean_baseline_rmse']:.4f} s"
    )

    print(
        f"Mean calibrated held-out RMSE: "
        f"{result['mean_calibrated_rmse']:.4f} s"
    )

    print(
        f"Mean held-out MAE: "
        f"{result['mean_calibrated_mae']:.4f} s"
    )

    print(
        f"RMSE standard deviation: "
        f"{result['rmse_standard_deviation']:.4f} s"
    )

    print(
        f"Worst held-out RMSE: "
        f"{result['worst_rmse']:.4f} s"
    )

    print(
        "Improved folds:",
        result[
            "improved_folds"
        ],
        "/",
        len(
            result[
                "fold_results"
            ]
        )
    )

    print(
        f"Mean RMSE improvement: "
        f"{result['improvement_percentage']:.1f}%"
    )

    print()

    print(
        "FINAL REAL-DATA FIT"
    )

    print(
        "Linear coefficient:",
        result[
            "final_linear"
        ]
    )

    print(
        "Quadratic coefficient:",
        result[
            "final_quadratic"
        ]
    )

    print(
        f"All-data fit RMSE: "
        f"{result['final_fit_rmse']:.4f} s"
    )

    print()

    print(
        "NOTE:"
    )

    print(
        "Real-world validation measures relative "
        "lap-time evolution through a tyre stint."
    )

    print(
        "It does not claim the entire simulator "
        "predicts absolute F1 lap times."
    )


# =============================================================
# GRAPH 1
# STRATEGY OPTIMISATION
# =============================================================

plt.figure(
    figsize=(10, 6)
)

for strategy_name in (
    one_stop_results
):

    result = (
        one_stop_results[
            strategy_name
        ]
    )

    plt.plot(
        result[2],
        result[3],
        label=strategy_name
    )

plt.xlabel(
    "Pit Lap"
)

plt.ylabel(
    "Race Time (seconds)"
)

plt.title(
    "One-Stop Strategy Optimisation"
)

plt.legend(
    bbox_to_anchor=(
        1.02,
        1
    ),
    loc="upper left"
)

plt.tight_layout()

if save_plots:

    plt.savefig(
        os.path.join(
            plots_folder,
            "01_strategy_optimisation.png"
        ),
        dpi=300
    )

if show_plots:

    plt.show()

else:

    plt.close()


# =============================================================
# GRAPH 2
# MONTE CARLO
# =============================================================

plt.figure(
    figsize=(10, 6)
)

plt.hist(
    reactive_one_times,
    bins=30,
    alpha=0.6,
    label="One-Stop"
)

plt.hist(
    reactive_two_times,
    bins=30,
    alpha=0.6,
    label="Two-Stop"
)

plt.xlabel(
    "Race Time (seconds)"
)

plt.ylabel(
    "Frequency"
)

plt.title(
    "Monte Carlo Safety Car Strategy Outcomes"
)

plt.legend()

plt.tight_layout()

if save_plots:

    plt.savefig(
        os.path.join(
            plots_folder,
            "02_monte_carlo.png"
        ),
        dpi=300
    )

if show_plots:

    plt.show()

else:

    plt.close()


# =============================================================
# GRAPH 3
# FIELD PIT-STOP SEARCH
# =============================================================

field_pits = []

field_positions = []

for pit_lap, result in (
    field_search_results
):

    field_pits.append(
        pit_lap
    )

    field_positions.append(
        result[
            "final_position"
        ]
    )

plt.figure(
    figsize=(10, 6)
)

plt.plot(
    field_pits,
    field_positions,
    marker="o"
)

plt.gca().invert_yaxis()

plt.xlabel(
    "Our Pit Lap"
)

plt.ylabel(
    "Final Position"
)

plt.title(
    "Traffic-Aware Pit Strategy"
)

plt.tight_layout()

if save_plots:

    plt.savefig(
        os.path.join(
            plots_folder,
            "03_field_strategy.png"
        ),
        dpi=300
    )

if show_plots:

    plt.show()

else:

    plt.close()


# =============================================================
# GRAPH 4
# PIT LOSS SENSITIVITY
# =============================================================

plt.figure(
    figsize=(10, 6)
)

plt.plot(
    pit_loss_values,
    pit_loss_gaps,
    marker="o"
)

plt.axhline(
    0,
    linestyle="--",
    label="One-Stop = Two-Stop"
)

if pit_loss_switch is not None:

    plt.axvline(
        pit_loss_switch,
        linestyle="--",
        label="Strategy Crossover"
    )

plt.xlabel(
    "Pit-Stop Loss (seconds)"
)

plt.ylabel(
    "Two-Stop minus One-Stop (seconds)"
)

plt.title(
    "Strategy Robustness to Pit-Stop Loss"
)

plt.legend()

plt.tight_layout()

if save_plots:

    plt.savefig(
        os.path.join(
            plots_folder,
            "04_sensitivity.png"
        ),
        dpi=300
    )

if show_plots:

    plt.show()

else:

    plt.close()


# =============================================================
# GRAPH 5
# REAL CROSS-VALIDATION ERROR
# =============================================================

if real_validation_result is not None:

    fold_labels = []

    baseline_values = []

    calibrated_values = []

    for fold in (
        real_validation_result[
            "fold_results"
        ]
    ):

        key = (
            fold[
                "validation_key"
            ]
        )

        fold_labels.append(
            key[0]
            + "\nStint "
            + str(
                key[1]
            )
        )

        baseline_values.append(
            fold[
                "baseline_rmse"
            ]
        )

        calibrated_values.append(
            fold[
                "calibrated_rmse"
            ]
        )

    x_positions = list(
        range(
            len(
                fold_labels
            )
        )
    )

    left_positions = [
        x - 0.18
        for x in x_positions
    ]

    right_positions = [
        x + 0.18
        for x in x_positions
    ]

    plt.figure(
        figsize=(11, 6)
    )

    plt.bar(
        left_positions,
        baseline_values,
        width=0.36,
        label="Baseline Model"
    )

    plt.bar(
        right_positions,
        calibrated_values,
        width=0.36,
        label="Calibrated Model"
    )

    plt.xticks(
        x_positions,
        fold_labels
    )

    plt.ylabel(
        "Held-Out Stint RMSE (seconds)"
    )

    plt.title(
        "Real-World Leave-One-Stint-Out Validation"
    )

    plt.legend()

    plt.tight_layout()

    if save_plots:

        plt.savefig(
            os.path.join(
                plots_folder,
                "05_real_cross_validation.png"
            ),
            dpi=300
        )

    if show_plots:

        plt.show()

    else:

        plt.close()


# =============================================================
# GRAPH 6
# REAL STINT DEGRADATION
# =============================================================

if real_validation_result is not None:

    plt.figure(
        figsize=(11, 6)
    )

    result = (
        real_validation_result
    )

    for key in (
        result[
            "selected_keys"
        ]
    ):

        rows = (
            result[
                "all_stints"
            ][
                key
            ]
        )

        observed, predicted = (
            calculate_stint_relative_values(
                rows,
                result[
                    "final_linear"
                ],
                result[
                    "final_quadratic"
                ],
                result[
                    "actual_race_laps"
                ]
            )
        )

        ages = [
            row[
                "tyre_age"
            ]
            for row in rows[1:]
        ]

        label = (
            key[0]
            + " Stint "
            + str(
                key[1]
            )
        )

        plt.plot(
            ages,
            observed,
            marker="o",
            alpha=0.55,
            label=label
        )

        plt.plot(
            ages,
            predicted,
            linestyle="--",
            alpha=0.55
        )

    plt.xlabel(
        "Tyre Age (laps)"
    )

    plt.ylabel(
        "Relative Lap-Time Change (seconds)"
    )

    plt.title(
        "Observed vs Modelled Real Tyre-Stint Evolution"
    )

    plt.legend(
        bbox_to_anchor=(
            1.02,
            1
        ),
        loc="upper left"
    )

    plt.tight_layout()

    if save_plots:

        plt.savefig(
            os.path.join(
                plots_folder,
                "06_real_stint_validation.png"
            ),
            dpi=300
        )

    if show_plots:

        plt.show()

    else:

        plt.close()


# =============================================================
# END
# =============================================================

print()

print(
    "Analysis complete."
)

print(
    "Results saved in:",
    results_folder
)

print(
    "Portfolio plots saved in:",
    plots_folder
)