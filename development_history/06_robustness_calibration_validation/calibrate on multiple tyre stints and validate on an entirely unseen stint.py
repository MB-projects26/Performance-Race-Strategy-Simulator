import matplotlib.pyplot as plt
import random
import statistics
import math
import csv
import os


# =============================================================
# RACE SETTINGS
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
# GLOBAL TYRE DEGRADATION SCALE
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
# DIRTY AIR MODEL
# =============================================================

dirty_air_enabled = True

dirty_air_range = 1.5
dirty_air_max_penalty = 0.65

overtake_margin = 0.25
minimum_following_gap = 0.15


# =============================================================
# OVERTAKING AID MODEL
# =============================================================

drs_enabled = True

drs_activation_lap = 3
drs_detection_range = 1.0

drs_time_gain = 0.45

drs_overtake_margin_reduction = 0.15


# =============================================================
# TYRE DATA
# =============================================================
#
# Tuple:
#
# 0 = base lap time
# 1 = linear degradation
# 2 = quadratic degradation
# 3 = initial warm-up penalty
# 4 = warm-up recovery
# 5 = cliff threshold
# 6 = cliff severity
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
# CALIBRATION SETTINGS
# =============================================================

calibration_compound = "Medium"

use_external_calibration_csv = False

calibration_csv_filename = (
    "calibration_data.csv"
)


# Minimum number of clean observations required
# before a stint can participate in cross-validation.

minimum_clean_laps_per_stint = 6


# =============================================================
# CLEANING SETTINGS
# =============================================================

exclude_race_start_lap = True
exclude_pit_laps = True
exclude_out_laps = True
exclude_safety_car_laps = True


outlier_threshold = 1.50
outlier_window = 2


# =============================================================
# CALIBRATION GRID
# =============================================================

calibration_base_min = 89.50
calibration_base_max = 90.50
calibration_base_step = 0.05


calibration_linear_min = 0.030
calibration_linear_max = 0.100
calibration_linear_step = 0.005


calibration_quadratic_min = 0.000
calibration_quadratic_max = 0.005
calibration_quadratic_step = 0.00025


# =============================================================
# APPLY FINAL CALIBRATION?
# =============================================================
#
# Keep False with synthetic data.
#
# Only consider True after checking cross-validation
# results using genuine external data.
#
# =============================================================

apply_calibrated_model = False


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
# SAFETY CAR CHECK
# =============================================================

def is_safety_car_lap(
        lap,
        safety_car_start,
        safety_car_end):

    if safety_car_start is None:
        return False

    if (
        lap >= safety_car_start
        and lap <= safety_car_end
    ):
        return True

    return False


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
# FUEL MASS
# =============================================================

def calculate_fuel_mass(lap):

    fuel_mass = (
        initial_fuel_mass
        - fuel_burn_per_lap
        * (lap - 1)
    )

    if fuel_mass < 0:
        fuel_mass = 0.0

    return fuel_mass


# =============================================================
# FUEL LAP-TIME GAIN
# =============================================================

def calculate_fuel_time_gain(lap):

    current_fuel = calculate_fuel_mass(
        lap
    )

    fuel_burned = (
        initial_fuel_mass
        - current_fuel
    )

    return (
        fuel_burned
        * fuel_time_per_kg
    )


# =============================================================
# FUEL EFFECT ON TYRE WEAR
# =============================================================

def calculate_fuel_wear_increment(
        lap,
        safety_car_start=None,
        safety_car_end=None):

    current_fuel = calculate_fuel_mass(
        lap
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
# CALIBRATION WEAR INCREMENT
# =============================================================

def calculate_calibration_wear_increment(
        lap,
        safety_car):

    current_fuel = calculate_fuel_mass(
        lap
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

    if safety_car:

        wear_increment *= (
            safety_car_tyre_wear_multiplier
        )

    return wear_increment


# =============================================================
# TYRE CLIFF
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


# =============================================================
# TYRE DEGRADATION
# =============================================================

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


    cliff_loss = calculate_cliff_penalty(
        tyre_wear,
        cliff_threshold,
        cliff_severity
    )


    total_loss = (
        normal_loss
        + cliff_loss
    )


    return (
        total_loss
        * tyre_degradation_scale
    )


# =============================================================
# WARM-UP
# =============================================================

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


# =============================================================
# LAP TIME
# =============================================================

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


    base_time = tyre_data[0]


    tyre_loss = calculate_tyre_loss(
        tyre_data,
        tyre_wear
    )


    warmup_penalty = (
        calculate_warmup_penalty(
            tyre_data,
            tyre_age
        )
    )


    fuel_gain = calculate_fuel_time_gain(
        lap
    )


    return (
        base_time
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

        if (
            stint_length
            < minimum_stint
        ):

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


        lap_time = calculate_lap_time(
            tyre_data,
            tyre_age,
            tyre_wear,
            lap,
            safety_car_start,
            safety_car_end,
            pace_offset
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
            == pit_laps[
                pit_number
            ]
        ):


            total_time += calculate_pit_loss(
                lap,
                safety_car_start,
                safety_car_end
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
# SAFETY CAR END POSSIBILITIES
# =============================================================

def possible_safety_car_end_laps(
        safety_car_start,
        current_lap):


    possible_end_laps = []


    for duration in range(
        safety_car_min_duration,
        safety_car_max_duration + 1
    ):


        possible_end = (
            safety_car_start
            + duration
            - 1
        )


        if possible_end > race_laps:

            possible_end = race_laps


        if possible_end >= current_lap:

            possible_end_laps.append(
                possible_end
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


        predicted_time = (
            simulate_fixed_strategy(
                tyre_sequence,
                pit_laps,
                safety_car_start,
                possible_end
            )
        )


        predicted_times.append(
            predicted_time
        )


    return (
        statistics.mean(
            predicted_times
        ),
        possible_ends
    )


# =============================================================
# UNCERTAINTY-AWARE SAFETY CAR STRATEGY
# =============================================================

def simulate_uncertainty_strategy(
        tyre_sequence,
        planned_pit_laps,
        actual_safety_car_start=None,
        actual_safety_car_end=None):


    total_time = 0.0

    tyre_age = 0
    tyre_wear = 0.0

    stint_number = 0
    pit_number = 0


    actual_pit_laps = []
    decision_log = []


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


        lap_time = calculate_lap_time(
            tyre_data,
            tyre_age,
            tyre_wear,
            lap,
            actual_safety_car_start,
            actual_safety_car_end
        )


        total_time += lap_time


        tyre_age += 1


        tyre_wear += (
            calculate_fuel_wear_increment(
                lap,
                actual_safety_car_start,
                actual_safety_car_end
            )
        )


        should_pit = False


        if (
            pit_number
            < len(
                planned_pit_laps
            )
        ):


            planned_pit = (
                planned_pit_laps[
                    pit_number
                ]
            )


            if lap == planned_pit:

                should_pit = True


            elif (
                is_safety_car_lap(
                    lap,
                    actual_safety_car_start,
                    actual_safety_car_end
                )
                and lap < planned_pit
            ):


                stay_out_plan = (
                    actual_pit_laps
                    + planned_pit_laps[
                        pit_number:
                    ]
                )


                pit_now_plan = (
                    actual_pit_laps
                    + [lap]
                    + planned_pit_laps[
                        pit_number + 1:
                    ]
                )


                if pit_plan_is_legal(
                    pit_now_plan
                ):


                    (
                        expected_stay,
                        possible_ends

                    ) = calculate_expected_plan_time(
                        tyre_sequence,
                        stay_out_plan,
                        actual_safety_car_start,
                        lap
                    )


                    (
                        expected_pit,
                        ignored_ends

                    ) = calculate_expected_plan_time(
                        tyre_sequence,
                        pit_now_plan,
                        actual_safety_car_start,
                        lap
                    )


                    if (
                        expected_pit
                        < expected_stay
                    ):

                        should_pit = True
                        decision = "PIT"


                    else:

                        decision = "STAY OUT"


                    decision_log.append(
                        (
                            lap,
                            planned_pit,
                            possible_ends,
                            expected_stay,
                            expected_pit,
                            decision
                        )
                    )


        if should_pit:


            total_time += calculate_pit_loss(
                lap,
                actual_safety_car_start,
                actual_safety_car_end
            )


            actual_pit_laps.append(
                lap
            )


            tyre_age = 0
            tyre_wear = 0.0

            stint_number += 1
            pit_number += 1


    return (
        total_time,
        actual_pit_laps,
        decision_log
    )


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


        race_time = simulate_fixed_strategy(
            tyre_sequence,
            [pit_lap]
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
        round(
            best_time,
            6
        ),
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
        round(
            best_time,
            6
        )
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
                or result[1]
                < best_time
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
                    or result[2]
                    < best_time
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
# RANDOM SAFETY CAR SCENARIOS
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
# DRS-STYLE GAIN
# =============================================================

def calculate_drs_gain(
        lap,
        gap_to_car_ahead):


    if not drs_enabled:
        return 0.0


    if lap < drs_activation_lap:
        return 0.0


    if gap_to_car_ahead <= 0:
        return 0.0


    if (
        gap_to_car_ahead
        > drs_detection_range
    ):

        return 0.0


    return drs_time_gain


# =============================================================
# REQUIRED OVERTAKE MARGIN
# =============================================================

def calculate_required_overtake_margin(
        current_drs_gain):


    required_margin = (
        overtake_margin
    )


    if current_drs_gain > 0:


        required_margin -= (
            drs_overtake_margin_reduction
        )


    if required_margin < 0:

        required_margin = 0.0


    return required_margin


# =============================================================
# COPY FIELD CONFIGURATION
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


    field = copy_field_configuration(
        our_pit_lap
    )


    states = {}


    for car in field:


        states[
            car["name"]
        ] = {

            "total_time":
                car[
                    "start_gap"
                ],

            "tyre_age":
                0,

            "tyre_wear":
                0.0,

            "stint":
                0
        }


    our_position_history = []
    our_dirty_air_history = []
    our_drs_history = []

    pit_rejoin_positions = {}
    overtaking_events = []


    for lap in range(
        1,
        race_laps + 1
    ):


        running_order = sorted(

            field,

            key=lambda car:
                states[
                    car["name"]
                ][
                    "total_time"
                ]
        )


        effective_lap_times = {}
        dirty_air_penalties = {}
        drs_gains = {}
        cars_pitting = {}


        # =====================================================
        # CALCULATE EACH CAR
        # =====================================================

        for index in range(
            len(running_order)
        ):


            car = (
                running_order[
                    index
                ]
            )


            car_name = (
                car[
                    "name"
                ]
            )


            state = (
                states[
                    car_name
                ]
            )


            tyre_name = (
                car[
                    "tyre_sequence"
                ][
                    state[
                        "stint"
                    ]
                ]
            )


            tyre_data = tyres[
                tyre_name
            ]


            lap_time = calculate_lap_time(

                tyre_data,

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


            dirty_air_penalty = 0.0
            current_drs_gain = 0.0


            if index > 0:


                ahead_car = (
                    running_order[
                        index - 1
                    ]
                )


                ahead_name = (
                    ahead_car[
                        "name"
                    ]
                )


                gap = (

                    state[
                        "total_time"
                    ]

                    - states[
                        ahead_name
                    ][
                        "total_time"
                    ]
                )


                dirty_air_penalty = (
                    calculate_dirty_air_penalty(
                        gap
                    )
                )


                current_drs_gain = (
                    calculate_drs_gain(
                        lap,
                        gap
                    )
                )


                lap_time += (
                    dirty_air_penalty
                )


                lap_time -= (
                    current_drs_gain
                )


            is_pitting = (
                lap
                in car[
                    "pit_laps"
                ]
            )


            effective_time = (
                lap_time
            )


            if is_pitting:

                effective_time += (
                    normal_pit_loss
                )


            effective_lap_times[
                car_name
            ] = (
                effective_time
            )


            dirty_air_penalties[
                car_name
            ] = (
                dirty_air_penalty
            )


            drs_gains[
                car_name
            ] = (
                current_drs_gain
            )


            cars_pitting[
                car_name
            ] = (
                is_pitting
            )


        # =====================================================
        # PREDICT TOTAL TIMES
        # =====================================================

        predicted_times = {}


        for car in field:


            car_name = (
                car[
                    "name"
                ]
            )


            predicted_times[
                car_name
            ] = (

                states[
                    car_name
                ][
                    "total_time"
                ]

                + effective_lap_times[
                    car_name
                ]
            )


        adjusted_times = (
            predicted_times.copy()
        )


        # =====================================================
        # OVERTAKING
        # =====================================================

        for index in range(
            1,
            len(running_order)
        ):


            following_car = (
                running_order[
                    index
                ]
            )


            ahead_car = (
                running_order[
                    index - 1
                ]
            )


            following_name = (
                following_car[
                    "name"
                ]
            )


            ahead_name = (
                ahead_car[
                    "name"
                ]
            )


            if (
                not cars_pitting[
                    following_name
                ]
                and not cars_pitting[
                    ahead_name
                ]
            ):


                if (
                    adjusted_times[
                        following_name
                    ]

                    < adjusted_times[
                        ahead_name
                    ]
                ):


                    pace_advantage = (

                        effective_lap_times[
                            ahead_name
                        ]

                        - effective_lap_times[
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


                    else:


                        overtaking_events.append(
                            (
                                lap,
                                following_name,
                                ahead_name
                            )
                        )


        # =====================================================
        # UPDATE TIMES
        # =====================================================

        for car in field:


            car_name = (
                car[
                    "name"
                ]
            )


            states[
                car_name
            ][
                "total_time"
            ] = (
                adjusted_times[
                    car_name
                ]
            )


        # =====================================================
        # UPDATE TYRES
        # =====================================================

        wear_increment = (
            calculate_fuel_wear_increment(
                lap
            )
        )


        for car in field:


            car_name = (
                car[
                    "name"
                ]
            )


            states[
                car_name
            ][
                "tyre_age"
            ] += 1


            states[
                car_name
            ][
                "tyre_wear"
            ] += (
                wear_increment
            )


            if cars_pitting[
                car_name
            ]:


                states[
                    car_name
                ][
                    "tyre_age"
                ] = 0


                states[
                    car_name
                ][
                    "tyre_wear"
                ] = 0.0


                states[
                    car_name
                ][
                    "stint"
                ] += 1


        # =====================================================
        # NEW ORDER
        # =====================================================

        new_order = sorted(

            field,

            key=lambda car:
                states[
                    car["name"]
                ][
                    "total_time"
                ]
        )


        order_names = []


        for car in new_order:

            order_names.append(
                car[
                    "name"
                ]
            )


        our_position = (
            order_names.index(
                "Our Car"
            )
            + 1
        )


        our_position_history.append(
            our_position
        )


        our_dirty_air_history.append(
            dirty_air_penalties[
                "Our Car"
            ]
        )


        our_drs_history.append(
            drs_gains[
                "Our Car"
            ]
        )


        if cars_pitting[
            "Our Car"
        ]:


            pit_rejoin_positions[
                lap
            ] = (
                our_position
            )


    # =========================================================
    # FINAL ORDER
    # =========================================================

    final_order_raw = sorted(

        field,

        key=lambda car:
            states[
                car["name"]
            ][
                "total_time"
            ]
    )


    final_order = []


    for car in final_order_raw:


        car_name = (
            car[
                "name"
            ]
        )


        final_order.append(
            (
                car_name,

                states[
                    car_name
                ][
                    "total_time"
                ]
            )
        )


    final_names = []


    for result in final_order:

        final_names.append(
            result[0]
        )


    final_position = (
        final_names.index(
            "Our Car"
        )
        + 1
    )


    return {

        "final_position":
            final_position,

        "our_final_time":
            states[
                "Our Car"
            ][
                "total_time"
            ],

        "final_order":
            final_order,

        "position_history":
            our_position_history,

        "dirty_air_history":
            our_dirty_air_history,

        "drs_history":
            our_drs_history,

        "pit_rejoin_positions":
            pit_rejoin_positions,

        "overtaking_events":
            overtaking_events
    }


# =============================================================
# FIND BEST FIELD PIT
# =============================================================

def find_best_field_pit():


    results = []


    for candidate_pit in range(
        field_pit_search_start,
        field_pit_search_end + 1
    ):


        result = simulate_small_field(
            candidate_pit
        )


        results.append(
            (
                candidate_pit,
                result
            )
        )


    best_result = min(

        results,

        key=lambda entry:
            (
                entry[1][
                    "final_position"
                ],

                entry[1][
                    "our_final_time"
                ]
            )
    )


    return (
        best_result[0],
        best_result[1],
        results
    )


# =============================================================
# BOOLEAN CSV PARSER
# =============================================================

def parse_boolean(value):


    text = str(
        value
    ).strip().lower()


    if text in [
        "true",
        "1",
        "yes",
        "y"
    ]:

        return True


    if text in [
        "false",
        "0",
        "no",
        "n",
        ""
    ]:

        return False


    raise ValueError(
        "Cannot interpret boolean value: "
        + str(value)
    )


# =============================================================
# SYNTHETIC MULTI-STINT DATA
# =============================================================
#
# Three Medium stints:
#
# Stint 1 = laps 1-16
# Stint 2 = laps 17-33
# Stint 3 = laps 34-50
#
# Hidden generating model:
#
# Base       = 90.15
# Linear     = 0.055
# Quadratic  = 0.0035
#
# These hidden values are NOT supplied to the
# calibration optimiser.
#
# =============================================================

def create_synthetic_calibration_data():


    true_base = 90.15
    true_linear = 0.055
    true_quadratic = 0.0035


    medium_data = tyres[
        "Medium"
    ]


    pit_laps = {
        16,
        33
    }


    safety_car_laps = {
        8,
        9,
        24,
        25,
        39,
        40
    }


    out_laps = {
        17,
        34
    }


    abnormal_laps = {

        12: 2.2,

        29: 2.0,

        44: 2.3
    }


    random_generator = (
        random.Random(
            7
        )
    )


    rows = []


    tyre_age = 0
    tyre_wear = 0.0


    for lap in range(
        1,
        51
    ):


        pit_lap = (
            lap in pit_laps
        )


        safety_car = (
            lap
            in safety_car_laps
        )


        normal_loss = (

            true_linear
            * tyre_wear

            + true_quadratic
            * (tyre_wear ** 2)
        )


        cliff_loss = (
            calculate_cliff_penalty(
                tyre_wear,
                medium_data[5],
                medium_data[6]
            )
        )


        warmup_penalty = (
            calculate_warmup_penalty(
                medium_data,
                tyre_age
            )
        )


        fuel_gain = (
            calculate_fuel_time_gain(
                lap
            )
        )


        noise = (
            random_generator.uniform(
                -0.05,
                0.05
            )
        )


        lap_time = (

            true_base
            + normal_loss
            + cliff_loss
            + warmup_penalty
            - fuel_gain
            + noise
        )


        if safety_car:


            lap_time = (

                120.0

                + random_generator.uniform(
                    -0.05,
                    0.05
                )
            )


        if pit_lap:

            lap_time += 10.0


        if lap in out_laps:

            lap_time += 6.0


        if lap in abnormal_laps:


            lap_time += (
                abnormal_laps[
                    lap
                ]
            )


        rows.append(
            {
                "race_lap":
                    lap,

                "lap_time":
                    lap_time,

                "compound":
                    "Medium",

                "pit_lap":
                    pit_lap,

                "safety_car":
                    safety_car
            }
        )


        tyre_age += 1


        tyre_wear += (
            calculate_calibration_wear_increment(
                lap,
                safety_car
            )
        )


        if pit_lap:

            tyre_age = 0
            tyre_wear = 0.0


    return rows


# =============================================================
# LOAD EXTERNAL CSV
# =============================================================

def load_external_calibration_data():


    if not os.path.exists(
        calibration_csv_filename
    ):


        raise FileNotFoundError(

            "Could not find "
            + calibration_csv_filename
        )


    required_columns = [

        "race_lap",

        "lap_time",

        "compound",

        "pit_lap",

        "safety_car"
    ]


    rows = []


    with open(
        calibration_csv_filename,
        "r",
        newline=""
    ) as file:


        reader = csv.DictReader(
            file
        )


        if reader.fieldnames is None:

            raise ValueError(
                "CSV has no header."
            )


        for column in required_columns:


            if column not in reader.fieldnames:


                raise ValueError(

                    "Missing CSV column: "
                    + column
                )


        for row in reader:


            rows.append(
                {
                    "race_lap":
                        int(
                            row[
                                "race_lap"
                            ]
                        ),

                    "lap_time":
                        float(
                            row[
                                "lap_time"
                            ]
                        ),

                    "compound":
                        row[
                            "compound"
                        ].strip().title(),

                    "pit_lap":
                        parse_boolean(
                            row[
                                "pit_lap"
                            ]
                        ),

                    "safety_car":
                        parse_boolean(
                            row[
                                "safety_car"
                            ]
                        )
                }
            )


    rows.sort(
        key=lambda row:
            row[
                "race_lap"
            ]
    )


    if len(rows) < 10:

        raise ValueError(
            "Not enough race laps in CSV."
        )


    for i in range(
        1,
        len(rows)
    ):


        expected_lap = (

            rows[
                i - 1
            ][
                "race_lap"
            ]

            + 1
        )


        if (
            rows[i][
                "race_lap"
            ]
            != expected_lap
        ):


            raise ValueError(

                "Missing race lap between "
                + str(
                    rows[
                        i - 1
                    ][
                        "race_lap"
                    ]
                )
                + " and "
                + str(
                    rows[i][
                        "race_lap"
                    ]
                )
            )


    return rows


# =============================================================
# LOAD CALIBRATION DATA
# =============================================================

def load_calibration_data():


    if use_external_calibration_csv:


        return (
            load_external_calibration_data(),

            calibration_csv_filename
        )


    return (
        create_synthetic_calibration_data(),

        "Built-in synthetic multi-stint dataset"
    )


# =============================================================
# ASSIGN STINT AND TYRE STATES
# =============================================================

def assign_calibration_stint_states(
        raw_rows):


    processed_rows = []


    current_stint = 0

    tyre_age = 0
    tyre_wear = 0.0

    previous_pit = False
    previous_compound = None


    for index in range(
        len(raw_rows)
    ):


        row = (
            raw_rows[
                index
            ].copy()
        )


        new_stint = False


        if index == 0:

            new_stint = True


        elif previous_pit:

            new_stint = True


        elif (
            row[
                "compound"
            ]
            != previous_compound
        ):

            new_stint = True


        if new_stint:


            current_stint += 1

            tyre_age = 0
            tyre_wear = 0.0


        row[
            "stint_id"
        ] = (
            current_stint
        )


        row[
            "tyre_age"
        ] = (
            tyre_age
        )


        row[
            "tyre_wear"
        ] = (
            tyre_wear
        )


        row[
            "out_lap"
        ] = (
            previous_pit
        )


        row[
            "removal_reasons"
        ] = []


        processed_rows.append(
            row
        )


        tyre_age += 1


        tyre_wear += (
            calculate_calibration_wear_increment(

                row[
                    "race_lap"
                ],

                row[
                    "safety_car"
                ]
            )
        )


        previous_pit = (
            row[
                "pit_lap"
            ]
        )


        previous_compound = (
            row[
                "compound"
            ]
        )


    return processed_rows


# =============================================================
# BASIC FILTERS
# =============================================================

def apply_basic_calibration_filters(
        rows):


    for row in rows:


        reasons = (
            row[
                "removal_reasons"
            ]
        )


        if (
            row[
                "lap_time"
            ] <= 0
        ):

            reasons.append(
                "Invalid lap time"
            )


        if (
            exclude_race_start_lap
            and row[
                "race_lap"
            ] == 1
        ):

            reasons.append(
                "Race-start lap"
            )


        if (
            exclude_pit_laps
            and row[
                "pit_lap"
            ]
        ):

            reasons.append(
                "Pit lap"
            )


        if (
            exclude_out_laps
            and row[
                "out_lap"
            ]
        ):

            reasons.append(
                "Out-lap"
            )


        if (
            exclude_safety_car_laps
            and row[
                "safety_car"
            ]
        ):

            reasons.append(
                "Safety Car"
            )


    return rows


# =============================================================
# GROUP BY STINT
# =============================================================

def group_rows_by_stint(
        rows):


    groups = {}


    for row in rows:


        stint_id = (
            row[
                "stint_id"
            ]
        )


        if stint_id not in groups:

            groups[
                stint_id
            ] = []


        groups[
            stint_id
        ].append(
            row
        )


    return groups


# =============================================================
# LOCAL OUTLIER FILTER
# =============================================================

def apply_local_outlier_filter(
        stint_rows):


    candidate_rows = []


    for row in stint_rows:


        if (
            len(
                row[
                    "removal_reasons"
                ]
            ) == 0
        ):

            candidate_rows.append(
                row
            )


    for index in range(
        len(candidate_rows)
    ):


        row = (
            candidate_rows[
                index
            ]
        )


        neighbour_times = []


        start_index = max(
            0,
            index - outlier_window
        )


        end_index = min(
            len(candidate_rows),
            index
            + outlier_window
            + 1
        )


        for neighbour_index in range(
            start_index,
            end_index
        ):


            if (
                neighbour_index
                == index
            ):

                continue


            neighbour_times.append(
                candidate_rows[
                    neighbour_index
                ][
                    "lap_time"
                ]
            )


        if (
            len(
                neighbour_times
            ) >= 2
        ):


            local_median = (
                statistics.median(
                    neighbour_times
                )
            )


            deviation = abs(

                row[
                    "lap_time"
                ]

                - local_median
            )


            if (
                deviation
                > outlier_threshold
            ):


                row[
                    "removal_reasons"
                ].append(
                    "Local lap-time outlier"
                )


    return stint_rows


# =============================================================
# PREPROCESS ALL STINTS
# =============================================================

def preprocess_multi_stint_data(
        raw_rows):


    rows = (
        assign_calibration_stint_states(
            raw_rows
        )
    )


    rows = (
        apply_basic_calibration_filters(
            rows
        )
    )


    stint_groups = (
        group_rows_by_stint(
            rows
        )
    )


    for stint_id in stint_groups:


        apply_local_outlier_filter(
            stint_groups[
                stint_id
            ]
        )


    clean_stints = {}
    excluded_stints = {}


    for stint_id in stint_groups:


        clean_rows = []
        excluded_rows = []


        for row in stint_groups[
            stint_id
        ]:


            if (
                row[
                    "compound"
                ]
                != calibration_compound
            ):

                continue


            if (
                len(
                    row[
                        "removal_reasons"
                    ]
                ) == 0
            ):

                clean_rows.append(
                    row
                )


            else:

                excluded_rows.append(
                    row
                )


        if len(
            clean_rows
        ) > 0:


            clean_stints[
                stint_id
            ] = (
                clean_rows
            )


            excluded_stints[
                stint_id
            ] = (
                excluded_rows
            )


    return (
        rows,
        stint_groups,
        clean_stints,
        excluded_stints
    )


# =============================================================
# FIND ELIGIBLE STINTS
# =============================================================

def find_eligible_stints(
        clean_stints):


    eligible_stint_ids = []


    for stint_id in sorted(
        clean_stints.keys()
    ):


        if (
            len(
                clean_stints[
                    stint_id
                ]
            )
            >= minimum_clean_laps_per_stint
        ):


            eligible_stint_ids.append(
                stint_id
            )


    if len(
        eligible_stint_ids
    ) < 2:


        raise ValueError(

            "Leave-one-stint-out cross-validation "
            "requires at least two eligible stints."
        )


    return eligible_stint_ids


# =============================================================
# FLOAT RANGE
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


# =============================================================
# CALIBRATION PREDICTION
# =============================================================

def predict_calibration_rows(
        rows,
        candidate_base,
        candidate_linear,
        candidate_quadratic):


    tyre_data = tyres[
        calibration_compound
    ]


    predictions = []


    for row in rows:


        tyre_age = (
            row[
                "tyre_age"
            ]
        )


        tyre_wear = (
            row[
                "tyre_wear"
            ]
        )


        race_lap = (
            row[
                "race_lap"
            ]
        )


        normal_loss = (

            candidate_linear
            * tyre_wear

            + candidate_quadratic
            * (tyre_wear ** 2)
        )


        cliff_loss = (
            calculate_cliff_penalty(

                tyre_wear,

                tyre_data[5],

                tyre_data[6]
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
                race_lap
            )
        )


        predicted_time = (

            candidate_base
            + normal_loss
            + cliff_loss
            + warmup_penalty
            - fuel_gain
        )


        predictions.append(
            predicted_time
        )


    return predictions


# =============================================================
# OBSERVED TIMES
# =============================================================

def get_observed_times(
        rows):


    observed = []


    for row in rows:


        observed.append(
            row[
                "lap_time"
            ]
        )


    return observed


# =============================================================
# RMSE
# =============================================================

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


# =============================================================
# MAE
# =============================================================

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
# FIT COEFFICIENTS USING GRID SEARCH
# =============================================================

def fit_calibration_model(
        training_rows):


    observed = (
        get_observed_times(
            training_rows
        )
    )


    base_values = create_float_range(
        calibration_base_min,
        calibration_base_max,
        calibration_base_step
    )


    linear_values = create_float_range(
        calibration_linear_min,
        calibration_linear_max,
        calibration_linear_step
    )


    quadratic_values = create_float_range(
        calibration_quadratic_min,
        calibration_quadratic_max,
        calibration_quadratic_step
    )


    best_rmse = None

    best_base = None
    best_linear = None
    best_quadratic = None


    combinations_tested = 0


    for candidate_base in base_values:


        for candidate_linear in linear_values:


            for candidate_quadratic in quadratic_values:


                combinations_tested += 1


                predictions = (
                    predict_calibration_rows(

                        training_rows,

                        candidate_base,

                        candidate_linear,

                        candidate_quadratic
                    )
                )


                rmse = calculate_rmse(
                    predictions,
                    observed
                )


                if (
                    best_rmse is None
                    or rmse < best_rmse
                ):


                    best_rmse = rmse

                    best_base = (
                        candidate_base
                    )

                    best_linear = (
                        candidate_linear
                    )

                    best_quadratic = (
                        candidate_quadratic
                    )


    return {

        "base":
            best_base,

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
# EVALUATE COEFFICIENTS
# =============================================================

def evaluate_calibration_model(
        rows,
        base,
        linear,
        quadratic):


    observed = (
        get_observed_times(
            rows
        )
    )


    predictions = (
        predict_calibration_rows(
            rows,
            base,
            linear,
            quadratic
        )
    )


    return {

        "predictions":
            predictions,

        "rmse":
            calculate_rmse(
                predictions,
                observed
            ),

        "mae":
            calculate_mae(
                predictions,
                observed
            )
    }


# =============================================================
# LEAVE-ONE-STINT-OUT CROSS-VALIDATION
# =============================================================
#
# Suppose eligible stints are:
#
# [1, 2, 3]
#
# Fold 1:
# Train = [2, 3]
# Validate = [1]
#
# Fold 2:
# Train = [1, 3]
# Validate = [2]
#
# Fold 3:
# Train = [1, 2]
# Validate = [3]
#
# The validation stint is NEVER used when fitting
# that fold's coefficients.
#
# =============================================================

def run_leave_one_stint_out_cv():


    (
        raw_rows,
        data_source

    ) = load_calibration_data()


    (
        processed_rows,
        stint_groups,
        clean_stints,
        excluded_stints

    ) = preprocess_multi_stint_data(
        raw_rows
    )


    eligible_stint_ids = (
        find_eligible_stints(
            clean_stints
        )
    )


    tyre_data = tyres[
        calibration_compound
    ]


    fold_results = []


    # =========================================================
    # CROSS-VALIDATION FOLDS
    # =========================================================

    for validation_stint_id in (
        eligible_stint_ids
    ):


        training_stint_ids = []


        for stint_id in (
            eligible_stint_ids
        ):


            if (
                stint_id
                != validation_stint_id
            ):


                training_stint_ids.append(
                    stint_id
                )


        training_rows = []


        for stint_id in training_stint_ids:


            training_rows.extend(
                clean_stints[
                    stint_id
                ]
            )


        validation_rows = (
            clean_stints[
                validation_stint_id
            ]
        )


        # =====================================================
        # ORIGINAL MODEL PERFORMANCE
        # =====================================================

        original_training = (
            evaluate_calibration_model(

                training_rows,

                tyre_data[0],

                tyre_data[1],

                tyre_data[2]
            )
        )


        original_validation = (
            evaluate_calibration_model(

                validation_rows,

                tyre_data[0],

                tyre_data[1],

                tyre_data[2]
            )
        )


        # =====================================================
        # FIT ONLY ON TRAINING STINTS
        # =====================================================

        fitted_model = (
            fit_calibration_model(
                training_rows
            )
        )


        # =====================================================
        # CALIBRATED TRAINING PERFORMANCE
        # =====================================================

        calibrated_training = (
            evaluate_calibration_model(

                training_rows,

                fitted_model[
                    "base"
                ],

                fitted_model[
                    "linear"
                ],

                fitted_model[
                    "quadratic"
                ]
            )
        )


        # =====================================================
        # HELD-OUT VALIDATION PERFORMANCE
        # =====================================================

        calibrated_validation = (
            evaluate_calibration_model(

                validation_rows,

                fitted_model[
                    "base"
                ],

                fitted_model[
                    "linear"
                ],

                fitted_model[
                    "quadratic"
                ]
            )
        )


        fold_results.append(
            {
                "validation_stint":
                    validation_stint_id,

                "training_stints":
                    training_stint_ids,

                "training_rows":
                    training_rows,

                "validation_rows":
                    validation_rows,

                "base":
                    fitted_model[
                        "base"
                    ],

                "linear":
                    fitted_model[
                        "linear"
                    ],

                "quadratic":
                    fitted_model[
                        "quadratic"
                    ],

                "combinations_tested":
                    fitted_model[
                        "combinations_tested"
                    ],

                "original_training_rmse":
                    original_training[
                        "rmse"
                    ],

                "original_training_mae":
                    original_training[
                        "mae"
                    ],

                "original_validation_rmse":
                    original_validation[
                        "rmse"
                    ],

                "original_validation_mae":
                    original_validation[
                        "mae"
                    ],

                "calibrated_training_rmse":
                    calibrated_training[
                        "rmse"
                    ],

                "calibrated_training_mae":
                    calibrated_training[
                        "mae"
                    ],

                "calibrated_validation_rmse":
                    calibrated_validation[
                        "rmse"
                    ],

                "calibrated_validation_mae":
                    calibrated_validation[
                        "mae"
                    ]
            }
        )


    # =========================================================
    # CROSS-VALIDATION SUMMARY
    # =========================================================

    original_validation_rmse_values = []

    calibrated_validation_rmse_values = []

    calibrated_validation_mae_values = []


    fitted_base_values = []

    fitted_linear_values = []

    fitted_quadratic_values = []


    for fold in fold_results:


        original_validation_rmse_values.append(
            fold[
                "original_validation_rmse"
            ]
        )


        calibrated_validation_rmse_values.append(
            fold[
                "calibrated_validation_rmse"
            ]
        )


        calibrated_validation_mae_values.append(
            fold[
                "calibrated_validation_mae"
            ]
        )


        fitted_base_values.append(
            fold[
                "base"
            ]
        )


        fitted_linear_values.append(
            fold[
                "linear"
            ]
        )


        fitted_quadratic_values.append(
            fold[
                "quadratic"
            ]
        )


    average_original_validation_rmse = (
        statistics.mean(
            original_validation_rmse_values
        )
    )


    average_calibrated_validation_rmse = (
        statistics.mean(
            calibrated_validation_rmse_values
        )
    )


    average_calibrated_validation_mae = (
        statistics.mean(
            calibrated_validation_mae_values
        )
    )


    if len(
        calibrated_validation_rmse_values
    ) > 1:


        validation_rmse_std = (
            statistics.stdev(
                calibrated_validation_rmse_values
            )
        )


    else:


        validation_rmse_std = 0.0


    worst_validation_rmse = max(
        calibrated_validation_rmse_values
    )


    # =========================================================
    # FINAL MODEL FIT USING ALL ELIGIBLE STINTS
    # =========================================================
    #
    # This fit is NOT cross-validation.
    #
    # It is the model you would eventually deploy after
    # cross-validation has demonstrated acceptable
    # generalisation.
    #
    # =========================================================

    all_eligible_rows = []


    for stint_id in (
        eligible_stint_ids
    ):


        all_eligible_rows.extend(
            clean_stints[
                stint_id
            ]
        )


    final_model = (
        fit_calibration_model(
            all_eligible_rows
        )
    )


    final_evaluation = (
        evaluate_calibration_model(

            all_eligible_rows,

            final_model[
                "base"
            ],

            final_model[
                "linear"
            ],

            final_model[
                "quadratic"
            ]
        )
    )


    original_all_evaluation = (
        evaluate_calibration_model(

            all_eligible_rows,

            tyre_data[0],

            tyre_data[1],

            tyre_data[2]
        )
    )


    # =========================================================
    # RESIDUALS FOR FINAL FIT
    # =========================================================

    all_eligible_rows.sort(
        key=lambda row:
            row[
                "race_lap"
            ]
    )


    observed_all = (
        get_observed_times(
            all_eligible_rows
        )
    )


    original_all_predictions = (
        predict_calibration_rows(

            all_eligible_rows,

            tyre_data[0],

            tyre_data[1],

            tyre_data[2]
        )
    )


    final_all_predictions = (
        predict_calibration_rows(

            all_eligible_rows,

            final_model[
                "base"
            ],

            final_model[
                "linear"
            ],

            final_model[
                "quadratic"
            ]
        )
    )


    original_residuals = []

    final_residuals = []


    for i in range(
        len(
            observed_all
        )
    ):


        original_residuals.append(

            observed_all[i]

            - original_all_predictions[i]
        )


        final_residuals.append(

            observed_all[i]

            - final_all_predictions[i]
        )


    return {

        "source":
            data_source,

        "raw_rows":
            raw_rows,

        "processed_rows":
            processed_rows,

        "stint_groups":
            stint_groups,

        "clean_stints":
            clean_stints,

        "excluded_stints":
            excluded_stints,

        "eligible_stint_ids":
            eligible_stint_ids,

        "fold_results":
            fold_results,

        "average_original_validation_rmse":
            average_original_validation_rmse,

        "average_calibrated_validation_rmse":
            average_calibrated_validation_rmse,

        "average_calibrated_validation_mae":
            average_calibrated_validation_mae,

        "validation_rmse_std":
            validation_rmse_std,

        "worst_validation_rmse":
            worst_validation_rmse,

        "fold_base_values":
            fitted_base_values,

        "fold_linear_values":
            fitted_linear_values,

        "fold_quadratic_values":
            fitted_quadratic_values,

        "final_base":
            final_model[
                "base"
            ],

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
            ],

        "final_fit_mae":
            final_evaluation[
                "mae"
            ],

        "original_all_rmse":
            original_all_evaluation[
                "rmse"
            ],

        "all_eligible_rows":
            all_eligible_rows,

        "observed_all":
            observed_all,

        "original_all_predictions":
            original_all_predictions,

        "final_all_predictions":
            final_all_predictions,

        "original_residuals":
            original_residuals,

        "final_residuals":
            final_residuals
    }


# =============================================================
# APPLY FINAL CALIBRATED MODEL
# =============================================================

def apply_cross_validated_model(
        cv_result):


    old_data = tyres[
        calibration_compound
    ]


    tyres[
        calibration_compound
    ] = (

        cv_result[
            "final_base"
        ],

        cv_result[
            "final_linear"
        ],

        cv_result[
            "final_quadratic"
        ],

        old_data[3],

        old_data[4],

        old_data[5],

        old_data[6]
    )


# =============================================================
# PIT LOSS SENSITIVITY
# =============================================================

def run_pit_loss_sensitivity():


    global normal_pit_loss


    original_pit_loss = (
        normal_pit_loss
    )


    test_values = list(
        range(
            10,
            61,
            5
        )
    )


    strategy_gaps = []


    for test_value in test_values:


        normal_pit_loss = float(
            test_value
        )


        one_result = (
            find_best_one_stop()
        )


        two_result = (
            find_best_two_stop()
        )


        strategy_gaps.append(

            two_result[3]

            - one_result[2]
        )


    normal_pit_loss = (
        original_pit_loss
    )


    return (
        test_values,
        strategy_gaps
    )


# =============================================================
# FIND STRATEGY SWITCH
# =============================================================

def find_strategy_switch_point(
        x_values,
        y_values):


    for i in range(
        len(x_values) - 1
    ):


        first_gap = (
            y_values[i]
        )


        second_gap = (
            y_values[
                i + 1
            ]
        )


        if first_gap == 0:

            return x_values[i]


        if (
            first_gap
            * second_gap
            < 0
        ):


            first_x = (
                x_values[i]
            )


            second_x = (
                x_values[
                    i + 1
                ]
            )


            return (

                first_x

                + (
                    -first_gap
                    * (
                        second_x
                        - first_x
                    )
                    / (
                        second_gap
                        - first_gap
                    )
                )
            )


    return None


# =============================================================
# DEGRADATION SENSITIVITY
# =============================================================

def run_degradation_sensitivity():


    global tyre_degradation_scale


    original_scale = (
        tyre_degradation_scale
    )


    test_scales = [

        0.70,
        0.80,
        0.90,
        1.00,
        1.10,
        1.20,
        1.30
    ]


    strategy_gaps = []


    for scale in test_scales:


        tyre_degradation_scale = (
            scale
        )


        one_result = (
            find_best_one_stop()
        )


        two_result = (
            find_best_two_stop()
        )


        strategy_gaps.append(

            two_result[3]

            - one_result[2]
        )


    tyre_degradation_scale = (
        original_scale
    )


    return (
        test_scales,
        strategy_gaps
    )


# =============================================================
# OVERTAKING-AID SENSITIVITY
# =============================================================

def run_drs_sensitivity():


    global drs_time_gain


    original_gain = (
        drs_time_gain
    )


    test_values = [

        0.0,
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
        0.6,
        0.7,
        0.8
    ]


    best_pits = []
    final_positions = []


    for value in test_values:


        drs_time_gain = (
            value
        )


        (
            best_pit,
            best_result,
            ignored_results

        ) = find_best_field_pit()


        best_pits.append(
            best_pit
        )


        final_positions.append(
            best_result[
                "final_position"
            ]
        )


    drs_time_gain = (
        original_gain
    )


    return (
        test_values,
        best_pits,
        final_positions
    )


# =============================================================
# DIRTY AIR SENSITIVITY
# =============================================================

def run_dirty_air_sensitivity():


    global dirty_air_max_penalty


    original_penalty = (
        dirty_air_max_penalty
    )


    test_values = [

        0.0,
        0.2,
        0.4,
        0.6,
        0.8,
        1.0
    ]


    best_pits = []
    final_positions = []


    for value in test_values:


        dirty_air_max_penalty = (
            value
        )


        (
            best_pit,
            best_result,
            ignored_results

        ) = find_best_field_pit()


        best_pits.append(
            best_pit
        )


        final_positions.append(
            best_result[
                "final_position"
            ]
        )


    dirty_air_max_penalty = (
        original_penalty
    )


    return (
        test_values,
        best_pits,
        final_positions
    )


# =============================================================
# RUN LEAVE-ONE-STINT-OUT CROSS-VALIDATION
# =============================================================

print()

print(
    "Running leave-one-stint-out cross-validation..."
)


cv_result = (
    run_leave_one_stint_out_cv()
)


# =============================================================
# OPTIONALLY APPLY FINAL MODEL
# =============================================================

if apply_calibrated_model:


    if use_external_calibration_csv:


        apply_cross_validated_model(
            cv_result
        )


    else:


        print()

        print(
            "Calibration was NOT applied."
        )

        print(
            "Reason: built-in data is synthetic."
        )


# =============================================================
# BASELINE STRATEGY OPTIMISATION
# =============================================================

one_stop_search = (
    find_best_one_stop()
)


best_one_stop_strategy = (
    one_stop_search[0]
)

best_one_stop_pit = (
    one_stop_search[1]
)

best_one_stop_time = (
    one_stop_search[2]
)

one_stop_results = (
    one_stop_search[3]
)


best_one_stop_name = (

    best_one_stop_strategy[0]

    + " -> "

    + best_one_stop_strategy[1]
)


two_stop_search = (
    find_best_two_stop()
)


best_two_stop_strategy = (
    two_stop_search[0]
)

best_two_stop_pit_1 = (
    two_stop_search[1]
)

best_two_stop_pit_2 = (
    two_stop_search[2]
)

best_two_stop_time = (
    two_stop_search[3]
)


best_two_stop_name = (

    best_two_stop_strategy[0]

    + " -> "

    + best_two_stop_strategy[1]

    + " -> "

    + best_two_stop_strategy[2]
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
# MONTE CARLO
# =============================================================

scenarios = (
    generate_safety_car_scenarios(
        monte_carlo_runs
    )
)


fixed_one_times = []
uncertain_one_times = []

fixed_two_times = []
uncertain_two_times = []


safety_car_count = 0


for scenario in scenarios:


    safety_car_start = (
        scenario[0]
    )


    safety_car_end = (
        scenario[1]
    )


    if safety_car_start is not None:

        safety_car_count += 1


    fixed_one_time = (
        simulate_fixed_strategy(

            list(
                best_one_stop_strategy
            ),

            [
                best_one_stop_pit
            ],

            safety_car_start,

            safety_car_end
        )
    )


    fixed_one_times.append(
        fixed_one_time
    )


    (
        uncertain_one_time,
        ignored_pits,
        ignored_decisions

    ) = simulate_uncertainty_strategy(

        list(
            best_one_stop_strategy
        ),

        [
            best_one_stop_pit
        ],

        safety_car_start,

        safety_car_end
    )


    uncertain_one_times.append(
        uncertain_one_time
    )


    fixed_two_time = (
        simulate_fixed_strategy(

            list(
                best_two_stop_strategy
            ),

            [
                best_two_stop_pit_1,
                best_two_stop_pit_2
            ],

            safety_car_start,

            safety_car_end
        )
    )


    fixed_two_times.append(
        fixed_two_time
    )


    (
        uncertain_two_time,
        ignored_pits,
        ignored_decisions

    ) = simulate_uncertainty_strategy(

        list(
            best_two_stop_strategy
        ),

        [
            best_two_stop_pit_1,
            best_two_stop_pit_2
        ],

        safety_car_start,

        safety_car_end
    )


    uncertain_two_times.append(
        uncertain_two_time
    )


fixed_one_mean = (
    statistics.mean(
        fixed_one_times
    )
)


uncertain_one_mean = (
    statistics.mean(
        uncertain_one_times
    )
)


fixed_two_mean = (
    statistics.mean(
        fixed_two_times
    )
)


uncertain_two_mean = (
    statistics.mean(
        uncertain_two_times
    )
)


# =============================================================
# SENSITIVITY ANALYSES
# =============================================================

print(
    "Running pit-loss sensitivity..."
)


(
    pit_loss_values,
    pit_loss_strategy_gaps

) = run_pit_loss_sensitivity()


pit_loss_switch = (
    find_strategy_switch_point(

        pit_loss_values,

        pit_loss_strategy_gaps
    )
)


print(
    "Running degradation sensitivity..."
)


(
    degradation_scales,
    degradation_strategy_gaps

) = run_degradation_sensitivity()


print(
    "Running overtaking-aid sensitivity..."
)


(
    drs_test_values,
    drs_best_pits,
    drs_final_positions

) = run_drs_sensitivity()


print(
    "Running dirty-air sensitivity..."
)


(
    dirty_air_test_values,
    dirty_air_best_pits,
    dirty_air_final_positions

) = run_dirty_air_sensitivity()


# =============================================================
# PRINT CLEANING RESULTS
# =============================================================

print()

print(
    "========================================"
)

print(
    "DATA PREPROCESSING"
)

print(
    "========================================"
)

print()

print(
    "Data source:",
    cv_result[
        "source"
    ]
)

print(
    "Compound:",
    calibration_compound
)

print(
    "Eligible stints:",
    cv_result[
        "eligible_stint_ids"
    ]
)

print()


for stint_id in cv_result[
    "eligible_stint_ids"
]:


    clean_rows = (
        cv_result[
            "clean_stints"
        ][
            stint_id
        ]
    )


    excluded_rows = (
        cv_result[
            "excluded_stints"
        ].get(
            stint_id,
            []
        )
    )


    print(
        "STINT",
        stint_id
    )


    print(
        "Clean observations:",
        len(
            clean_rows
        )
    )


    print(
        "Excluded observations:",
        len(
            excluded_rows
        )
    )


    for row in excluded_rows:


        print(
            "  Lap",
            row[
                "race_lap"
            ],
            "-",
            ", ".join(
                row[
                    "removal_reasons"
                ]
            )
        )


    print()


# =============================================================
# PRINT CROSS-VALIDATION FOLDS
# =============================================================

print(
    "========================================"
)

print(
    "LEAVE-ONE-STINT-OUT CROSS-VALIDATION"
)

print(
    "========================================"
)

print()


for fold_number in range(
    len(
        cv_result[
            "fold_results"
        ]
    )
):


    fold = (
        cv_result[
            "fold_results"
        ][
            fold_number
        ]
    )


    print(
        "FOLD",
        fold_number + 1
    )


    print(
        "Training stints:",
        fold[
            "training_stints"
        ]
    )


    print(
        "Held-out validation stint:",
        fold[
            "validation_stint"
        ]
    )


    print()

    print(
        "Fitted base:",
        fold[
            "base"
        ]
    )


    print(
        "Fitted linear:",
        fold[
            "linear"
        ]
    )


    print(
        "Fitted quadratic:",
        fold[
            "quadratic"
        ]
    )


    print()

    print(
        f"Original validation RMSE: "
        f"{fold['original_validation_rmse']:.4f} s"
    )


    print(
        f"Calibrated validation RMSE: "
        f"{fold['calibrated_validation_rmse']:.4f} s"
    )


    print(
        f"Calibrated validation MAE: "
        f"{fold['calibrated_validation_mae']:.4f} s"
    )


    print()


# =============================================================
# PRINT CV SUMMARY
# =============================================================

print(
    "========================================"
)

print(
    "CROSS-VALIDATION SUMMARY"
)

print(
    "========================================"
)

print()

print(
    f"Average original validation RMSE: "
    f"{cv_result['average_original_validation_rmse']:.4f} s"
)

print(
    f"Average calibrated validation RMSE: "
    f"{cv_result['average_calibrated_validation_rmse']:.4f} s"
)

print(
    f"Average calibrated validation MAE: "
    f"{cv_result['average_calibrated_validation_mae']:.4f} s"
)

print(
    f"Validation RMSE standard deviation: "
    f"{cv_result['validation_rmse_std']:.4f} s"
)

print(
    f"Worst held-out validation RMSE: "
    f"{cv_result['worst_validation_rmse']:.4f} s"
)


# =============================================================
# PRINT FINAL ALL-STINT FIT
# =============================================================

print()

print(
    "========================================"
)

print(
    "FINAL ALL-STINT FIT"
)

print(
    "========================================"
)

print()

print(
    "IMPORTANT:"
)

print(
    "This final fit uses every eligible stint."
)

print(
    "It is NOT a validation result."
)

print()

print(
    "Final base:",
    cv_result[
        "final_base"
    ]
)

print(
    "Final linear:",
    cv_result[
        "final_linear"
    ]
)

print(
    "Final quadratic:",
    cv_result[
        "final_quadratic"
    ]
)

print()

print(
    f"Final all-data RMSE: "
    f"{cv_result['final_fit_rmse']:.4f} s"
)

print(
    f"Final all-data MAE: "
    f"{cv_result['final_fit_mae']:.4f} s"
)


if use_external_calibration_csv:


    print()

    print(
        "External data is being used."
    )


else:


    print()

    print(
        "The current dataset is synthetic."
    )

    print(
        "Cross-validation demonstrates the method, "
        "not real-world model validity."
    )


# =============================================================
# PRINT STRATEGY RESULTS
# =============================================================

print()

print(
    "========================================"
)

print(
    "STRATEGY RESULTS"
)

print(
    "========================================"
)

print()

print(
    "Best one-stop:",
    best_one_stop_name
)

print(
    "Pit lap:",
    best_one_stop_pit
)

print(
    f"Race time: "
    f"{best_one_stop_time:.3f} s"
)

print()

print(
    "Best two-stop:",
    best_two_stop_name
)

print(
    "Pit laps:",
    best_two_stop_pit_1,
    "and",
    best_two_stop_pit_2
)

print(
    f"Race time: "
    f"{best_two_stop_time:.3f} s"
)

print()

print(
    f"Two-stop advantage: "
    f"{best_one_stop_time - best_two_stop_time:.3f} s"
)

print()

print(
    "Best field pit:",
    best_field_pit
)

print(
    "Best field finish: P"
    + str(
        best_field_result[
            "final_position"
        ]
    )
)


# =============================================================
# PRINT MONTE CARLO
# =============================================================

print()

print(
    "========================================"
)

print(
    "MONTE CARLO"
)

print(
    "========================================"
)

print()

print(
    "Simulations:",
    monte_carlo_runs
)

print(
    "Safety Car races:",
    safety_car_count
)

print()

print(
    f"One-stop fixed mean: "
    f"{fixed_one_mean:.3f} s"
)

print(
    f"One-stop uncertainty mean: "
    f"{uncertain_one_mean:.3f} s"
)

print()

print(
    f"Two-stop fixed mean: "
    f"{fixed_two_mean:.3f} s"
)

print(
    f"Two-stop uncertainty mean: "
    f"{uncertain_two_mean:.3f} s"
)


# =============================================================
# PRINT SENSITIVITY
# =============================================================

print()

print(
    "========================================"
)

print(
    "SENSITIVITY SUMMARY"
)

print(
    "========================================"
)

print()


if pit_loss_switch is not None:


    print(
        "Estimated one/two-stop switch pit loss:",
        f"{pit_loss_switch:.2f} s"
    )


else:


    print(
        "No pit-loss strategy switch "
        "inside tested range."
    )


print()


for i in range(
    len(
        degradation_scales
    )
):


    print(
        "Degradation scale:",
        degradation_scales[i],
        "- two-stop minus one-stop:",
        f"{degradation_strategy_gaps[i]:.2f} s"
    )


# =============================================================
# PREPARE CROSS-VALIDATION GRAPH DATA
# =============================================================

fold_labels = []

original_cv_rmse = []

calibrated_cv_rmse = []


fold_base_values = []

fold_linear_values = []

fold_quadratic_values = []


for fold_number in range(
    len(
        cv_result[
            "fold_results"
        ]
    )
):


    fold = (
        cv_result[
            "fold_results"
        ][
            fold_number
        ]
    )


    fold_labels.append(

        "Stint "
        + str(
            fold[
                "validation_stint"
            ]
        )
    )


    original_cv_rmse.append(
        fold[
            "original_validation_rmse"
        ]
    )


    calibrated_cv_rmse.append(
        fold[
            "calibrated_validation_rmse"
        ]
    )


    fold_base_values.append(
        fold[
            "base"
        ]
    )


    fold_linear_values.append(
        fold[
            "linear"
        ]
    )


    fold_quadratic_values.append(
        fold[
            "quadratic"
        ]
    )


x_positions = list(
    range(
        len(
            fold_labels
        )
    )
)


left_positions = []

right_positions = []


for x in x_positions:


    left_positions.append(
        x - 0.18
    )


    right_positions.append(
        x + 0.18
    )


# =============================================================
# GRAPH 1
# CLEAN STINT DATA
# =============================================================

plt.figure(
    figsize=(10, 6)
)


for stint_id in cv_result[
    "eligible_stint_ids"
]:


    stint_rows = (
        cv_result[
            "clean_stints"
        ][
            stint_id
        ]
    )


    x_values = []
    y_values = []


    for row in stint_rows:


        x_values.append(
            row[
                "race_lap"
            ]
        )


        y_values.append(
            row[
                "lap_time"
            ]
        )


    plt.plot(
        x_values,
        y_values,
        marker="o",
        label=(
            "Stint "
            + str(
                stint_id
            )
        )
    )


plt.xlabel(
    "Race Lap"
)

plt.ylabel(
    "Observed Lap Time (seconds)"
)

plt.title(
    "Clean Tyre Stints Used for Cross-Validation"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 2
# CROSS-VALIDATION RMSE
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.bar(
    left_positions,
    original_cv_rmse,
    width=0.36,
    label="Original Model"
)


plt.bar(
    right_positions,
    calibrated_cv_rmse,
    width=0.36,
    label="Calibrated Model"
)


plt.xticks(
    x_positions,
    fold_labels
)


plt.ylabel(
    "Held-Out Validation RMSE (seconds)"
)

plt.title(
    "Leave-One-Stint-Out Validation Error"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 3
# BASE COEFFICIENT STABILITY
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    x_positions,
    fold_base_values,
    marker="o",
    label="Cross-Validation Fit"
)


plt.axhline(
    cv_result[
        "final_base"
    ],
    linestyle="--",
    label="Final All-Stint Fit"
)


plt.xticks(
    x_positions,
    fold_labels
)


plt.ylabel(
    "Base Lap Time (seconds)"
)

plt.title(
    "Base-Time Coefficient Across CV Folds"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 4
# LINEAR COEFFICIENT STABILITY
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    x_positions,
    fold_linear_values,
    marker="o",
    label="Cross-Validation Fit"
)


plt.axhline(
    cv_result[
        "final_linear"
    ],
    linestyle="--",
    label="Final All-Stint Fit"
)


plt.xticks(
    x_positions,
    fold_labels
)


plt.ylabel(
    "Linear Degradation Coefficient"
)

plt.title(
    "Linear Degradation Across CV Folds"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 5
# QUADRATIC COEFFICIENT STABILITY
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    x_positions,
    fold_quadratic_values,
    marker="o",
    label="Cross-Validation Fit"
)


plt.axhline(
    cv_result[
        "final_quadratic"
    ],
    linestyle="--",
    label="Final All-Stint Fit"
)


plt.xticks(
    x_positions,
    fold_labels
)


plt.ylabel(
    "Quadratic Degradation Coefficient"
)

plt.title(
    "Quadratic Degradation Across CV Folds"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 6
# FINAL ALL-STINT FIT
# =============================================================

all_clean_laps = []


for row in cv_result[
    "all_eligible_rows"
]:


    all_clean_laps.append(
        row[
            "race_lap"
        ]
    )


plt.figure(
    figsize=(10, 6)
)


plt.plot(
    all_clean_laps,
    cv_result[
        "observed_all"
    ],
    marker="o",
    label="Observed Clean Data"
)


plt.plot(
    all_clean_laps,
    cv_result[
        "original_all_predictions"
    ],
    label="Original Model"
)


plt.plot(
    all_clean_laps,
    cv_result[
        "final_all_predictions"
    ],
    label="Final All-Stint Fit"
)


plt.xlabel(
    "Race Lap"
)

plt.ylabel(
    "Lap Time (seconds)"
)

plt.title(
    "Final Model Fit Using All Eligible Stints"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 7
# FINAL FIT RESIDUALS
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    all_clean_laps,
    cv_result[
        "original_residuals"
    ],
    marker="o",
    label="Original Model"
)


plt.plot(
    all_clean_laps,
    cv_result[
        "final_residuals"
    ],
    marker="o",
    label="Final All-Stint Fit"
)


plt.axhline(
    0,
    linestyle="--",
    label="Perfect Prediction"
)


plt.xlabel(
    "Race Lap"
)

plt.ylabel(
    "Observed minus Predicted (seconds)"
)

plt.title(
    "Final Fit Residuals"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 8
# ONE-STOP OPTIMISATION
# =============================================================

plt.figure(
    figsize=(10, 6)
)


for strategy_name in one_stop_results:


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

plt.show()


# =============================================================
# GRAPH 9
# SMALL FIELD POSITION
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    list(
        range(
            1,
            race_laps + 1
        )
    ),
    best_field_result[
        "position_history"
    ]
)


plt.axvline(
    best_field_pit,
    linestyle="--",
    label="Our Pit"
)


plt.gca().invert_yaxis()


plt.xlabel(
    "Race Lap"
)

plt.ylabel(
    "Track Position"
)

plt.title(
    "Best Small-Field Strategy"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 10
# PIT-LOSS SENSITIVITY
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    pit_loss_values,
    pit_loss_strategy_gaps,
    marker="o"
)


plt.axhline(
    0,
    linestyle="--",
    label="Equal Strategy Time"
)


plt.axvline(
    22,
    linestyle="--",
    label="Baseline Pit Loss"
)


if pit_loss_switch is not None:


    plt.axvline(
        pit_loss_switch,
        linestyle="--",
        label="Strategy Switch"
    )


plt.xlabel(
    "Pit Loss (seconds)"
)

plt.ylabel(
    "Two-Stop minus One-Stop (seconds)"
)

plt.title(
    "Strategy Sensitivity to Pit Loss"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 11
# DEGRADATION SENSITIVITY
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    degradation_scales,
    degradation_strategy_gaps,
    marker="o"
)


plt.axhline(
    0,
    linestyle="--",
    label="Equal Strategy Time"
)


plt.axvline(
    1.0,
    linestyle="--",
    label="Baseline"
)


plt.xlabel(
    "Tyre Degradation Scale"
)

plt.ylabel(
    "Two-Stop minus One-Stop (seconds)"
)

plt.title(
    "Strategy Sensitivity to Tyre Degradation"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 12
# OVERTAKING-AID SENSITIVITY
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    drs_test_values,
    drs_best_pits,
    marker="o"
)


plt.axvline(
    0.45,
    linestyle="--",
    label="Baseline"
)


plt.xlabel(
    "Overtaking-Aid Gain (seconds/lap)"
)

plt.ylabel(
    "Best Field Pit Lap"
)

plt.title(
    "Field Strategy Sensitivity to Overtaking Aid"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 13
# OVERTAKING AID VS FINAL POSITION
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    drs_test_values,
    drs_final_positions,
    marker="o"
)


plt.gca().invert_yaxis()


plt.xlabel(
    "Overtaking-Aid Gain (seconds/lap)"
)

plt.ylabel(
    "Best Final Position"
)

plt.title(
    "Final Position Sensitivity to Overtaking Aid"
)

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 14
# DIRTY AIR SENSITIVITY
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    dirty_air_test_values,
    dirty_air_best_pits,
    marker="o"
)


plt.axvline(
    0.65,
    linestyle="--",
    label="Baseline"
)


plt.xlabel(
    "Maximum Dirty-Air Loss (seconds/lap)"
)

plt.ylabel(
    "Best Field Pit Lap"
)

plt.title(
    "Field Strategy Sensitivity to Dirty Air"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 15
# DIRTY AIR VS FINAL POSITION
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    dirty_air_test_values,
    dirty_air_final_positions,
    marker="o"
)


plt.gca().invert_yaxis()


plt.xlabel(
    "Maximum Dirty-Air Loss (seconds/lap)"
)

plt.ylabel(
    "Best Final Position"
)

plt.title(
    "Final Position Sensitivity to Dirty Air"
)

plt.tight_layout()

plt.show()