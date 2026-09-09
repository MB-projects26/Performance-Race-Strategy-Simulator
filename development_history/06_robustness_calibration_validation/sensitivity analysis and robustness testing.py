import matplotlib.pyplot as plt
import random
import statistics


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
# TYRE DEGRADATION SCALE
# =============================================================
#
# 1.0 = normal assumed degradation
#
# 0.8 = 20% less degradation
#
# 1.2 = 20% more degradation
#
# This is useful for sensitivity analysis.
#
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
# DRS-STYLE OVERTAKING AID
# =============================================================
#
# This is a simplified modelling aid.
#
# It is not intended to represent the exact
# regulations of any specific championship season.
#
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
# Each tyre contains:
#
# 0 = base lap time
# 1 = linear degradation
# 2 = quadratic degradation
# 3 = warm-up penalty
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


# =============================================================
# FIELD PIT SEARCH RANGE
# =============================================================

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

    fuel_time_gain = (
        fuel_burned
        * fuel_time_per_kg
    )

    return fuel_time_gain


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

        wear_increment = (
            wear_increment
            * safety_car_tyre_wear_multiplier
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

    cliff_excess = (
        tyre_wear
        - cliff_threshold
    )

    cliff_penalty = (
        cliff_severity
        * (cliff_excess ** 2)
    )

    return cliff_penalty


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


    cliff_loss = (
        calculate_cliff_penalty(
            tyre_wear,
            cliff_threshold,
            cliff_severity
        )
    )


    tyre_loss = (
        normal_loss
        + cliff_loss
    )


    tyre_loss = (
        tyre_loss
        * tyre_degradation_scale
    )


    return tyre_loss


# =============================================================
# TYRE WARM-UP
# =============================================================

def calculate_warmup_penalty(
        tyre_data,
        tyre_age):

    initial_penalty = tyre_data[3]

    recovery_rate = tyre_data[4]


    warmup_penalty = (
        initial_penalty
        - recovery_rate
        * tyre_age
    )


    if warmup_penalty < 0:

        warmup_penalty = 0.0


    return warmup_penalty


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


    lap_time = (
        base_time
        + tyre_loss
        + warmup_penalty
        - fuel_gain
        + pace_offset
    )


    return lap_time


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
            and lap == pit_laps[
                pit_number
            ]
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


    possible_end_laps = (
        possible_safety_car_end_laps(
            safety_car_start,
            current_lap
        )
    )


    predicted_times = []


    for possible_end in possible_end_laps:


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


    expected_time = statistics.mean(
        predicted_times
    )


    return (
        expected_time,
        possible_end_laps
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
            < len(planned_pit_laps)
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
                        expected_stay_time,
                        possible_ends

                    ) = calculate_expected_plan_time(

                        tyre_sequence,

                        stay_out_plan,

                        actual_safety_car_start,

                        lap
                    )


                    (
                        expected_pit_time,
                        ignored_ends

                    ) = calculate_expected_plan_time(

                        tyre_sequence,

                        pit_now_plan,

                        actual_safety_car_start,

                        lap
                    )


                    if (
                        expected_pit_time
                        < expected_stay_time
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
                            expected_stay_time,
                            expected_pit_time,
                            decision
                        )
                    )


        if should_pit:


            total_time += (
                calculate_pit_loss(
                    lap,
                    actual_safety_car_start,
                    actual_safety_car_end
                )
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


    best_pit_lap = pit_laps_tested[
        best_index
    ]


    return (
        best_pit_lap,
        round(best_time, 6),
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
        round(best_time, 6)
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

    legal_combinations = 0


    for first_tyre in tyre_names:

        for second_tyre in tyre_names:


            if first_tyre == second_tyre:

                continue


            legal_combinations += 1


            result = (
                calculate_one_stop_strategy(
                    first_tyre,
                    second_tyre
                )
            )


            pit_lap = result[0]

            race_time = result[1]


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
                or race_time < best_time
            ):


                best_time = race_time


                best_strategy = (
                    first_tyre,
                    second_tyre
                )


                best_pit = pit_lap


    return (
        best_strategy,
        best_pit,
        best_time,
        all_results,
        legal_combinations
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


    legal_combinations = 0


    for first_tyre in tyre_names:

        for second_tyre in tyre_names:

            for third_tyre in tyre_names:


                if (
                    first_tyre
                    == second_tyre
                    == third_tyre
                ):

                    continue


                legal_combinations += 1


                result = (
                    calculate_two_stop_strategy(
                        first_tyre,
                        second_tyre,
                        third_tyre
                    )
                )


                pit_1 = result[0]

                pit_2 = result[1]

                race_time = result[2]


                if (
                    best_time is None
                    or race_time < best_time
                ):


                    best_time = race_time


                    best_strategy = (
                        first_tyre,
                        second_tyre,
                        third_tyre
                    )


                    best_pit_1 = pit_1

                    best_pit_2 = pit_2


    return (
        best_strategy,
        best_pit_1,
        best_pit_2,
        best_time,
        legal_combinations
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
# DIRTY AIR PENALTY
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


    dirty_air_penalty = (
        dirty_air_max_penalty
        * (1.0 - gap_fraction)
    )


    return dirty_air_penalty


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


        required_margin = (
            required_margin
            - drs_overtake_margin_reduction
        )


    if required_margin < 0:

        required_margin = 0.0


    return required_margin


# =============================================================
# COPY FIELD
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

    gap_to_ahead_history = []

    gap_to_behind_history = []

    our_dirty_air_history = []

    our_drs_history = []


    overtaking_events = []

    drs_events = []

    pit_rejoin_positions = {}


    for lap in range(
        1,
        race_laps + 1
    ):


        # -----------------------------------------------------
        # Running order at start of lap
        # -----------------------------------------------------

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


        # -----------------------------------------------------
        # Calculate each car's lap
        # -----------------------------------------------------

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


            car_state = (
                states[
                    car_name
                ]
            )


            tyre_name = (
                car[
                    "tyre_sequence"
                ][
                    car_state[
                        "stint"
                    ]
                ]
            )


            tyre_data = tyres[
                tyre_name
            ]


            lap_time = (
                calculate_lap_time(

                    tyre_data,

                    car_state[
                        "tyre_age"
                    ],

                    car_state[
                        "tyre_wear"
                    ],

                    lap,

                    pace_offset=
                        car[
                            "pace_offset"
                        ]
                )
            )


            dirty_air_penalty = 0.0

            current_drs_gain = 0.0


            # -------------------------------------------------
            # Following-car effects
            # -------------------------------------------------

            if index > 0:


                car_ahead = (
                    running_order[
                        index - 1
                    ]
                )


                car_ahead_name = (
                    car_ahead[
                        "name"
                    ]
                )


                gap_to_car_ahead = (

                    car_state[
                        "total_time"
                    ]

                    - states[
                        car_ahead_name
                    ][
                        "total_time"
                    ]
                )


                dirty_air_penalty = (
                    calculate_dirty_air_penalty(
                        gap_to_car_ahead
                    )
                )


                lap_time += (
                    dirty_air_penalty
                )


                current_drs_gain = (
                    calculate_drs_gain(
                        lap,
                        gap_to_car_ahead
                    )
                )


                lap_time -= (
                    current_drs_gain
                )


                if current_drs_gain > 0:


                    drs_events.append(
                        (
                            lap,
                            car_name,
                            car_ahead_name
                        )
                    )


            # -------------------------------------------------
            # Pit stop
            # -------------------------------------------------

            is_pitting = (
                lap
                in car[
                    "pit_laps"
                ]
            )


            effective_lap_time = (
                lap_time
            )


            if is_pitting:


                effective_lap_time += (
                    normal_pit_loss
                )


            effective_lap_times[
                car_name
            ] = (
                effective_lap_time
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


        # -----------------------------------------------------
        # Predicted total times
        # -----------------------------------------------------

        predicted_total_times = {}


        for car in field:


            car_name = (
                car[
                    "name"
                ]
            )


            predicted_total_times[
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


        adjusted_total_times = (
            predicted_total_times.copy()
        )


        # -----------------------------------------------------
        # Overtaking restrictions
        # -----------------------------------------------------

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


            following_pits = (
                cars_pitting[
                    following_name
                ]
            )


            ahead_pits = (
                cars_pitting[
                    ahead_name
                ]
            )


            if (
                not following_pits
                and not ahead_pits
            ):


                if (
                    adjusted_total_times[
                        following_name
                    ]

                    < adjusted_total_times[
                        ahead_name
                    ]
                ):


                    lap_time_advantage = (

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
                        lap_time_advantage
                        < required_margin
                    ):


                        adjusted_total_times[
                            following_name
                        ] = (

                            adjusted_total_times[
                                ahead_name
                            ]

                            + minimum_following_gap
                        )


                    else:


                        used_drs = (
                            drs_gains[
                                following_name
                            ]
                            > 0
                        )


                        overtaking_events.append(
                            (
                                lap,
                                following_name,
                                ahead_name,
                                used_drs
                            )
                        )


        # -----------------------------------------------------
        # Update total times
        # -----------------------------------------------------

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
                adjusted_total_times[
                    car_name
                ]
            )


        # -----------------------------------------------------
        # Update tyres
        # -----------------------------------------------------

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


        # -----------------------------------------------------
        # New running order
        # -----------------------------------------------------

        new_running_order = sorted(

            field,

            key=lambda car:
                states[
                    car["name"]
                ][
                    "total_time"
                ]
        )


        order_names = []


        for car in new_running_order:


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


        our_index = (
            our_position - 1
        )


        our_total_time = (
            states[
                "Our Car"
            ][
                "total_time"
            ]
        )


        # -----------------------------------------------------
        # Gap ahead
        # -----------------------------------------------------

        if our_index == 0:


            gap_to_ahead = None


        else:


            car_ahead_name = (
                order_names[
                    our_index - 1
                ]
            )


            gap_to_ahead = (

                our_total_time

                - states[
                    car_ahead_name
                ][
                    "total_time"
                ]
            )


        # -----------------------------------------------------
        # Gap behind
        # -----------------------------------------------------

        if (
            our_index
            == len(order_names) - 1
        ):


            gap_to_behind = None


        else:


            car_behind_name = (
                order_names[
                    our_index + 1
                ]
            )


            gap_to_behind = (

                states[
                    car_behind_name
                ][
                    "total_time"
                ]

                - our_total_time
            )


        gap_to_ahead_history.append(
            gap_to_ahead
        )


        gap_to_behind_history.append(
            gap_to_behind
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

    final_running_order = sorted(

        field,

        key=lambda car:
            states[
                car["name"]
            ][
                "total_time"
            ]
    )


    final_order = []


    for car in final_running_order:


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


    our_final_time = (
        states[
            "Our Car"
        ][
            "total_time"
        ]
    )


    return {

        "final_position":
            final_position,

        "our_final_time":
            our_final_time,

        "final_order":
            final_order,

        "position_history":
            our_position_history,

        "gap_to_ahead_history":
            gap_to_ahead_history,

        "gap_to_behind_history":
            gap_to_behind_history,

        "dirty_air_history":
            our_dirty_air_history,

        "drs_history":
            our_drs_history,

        "overtaking_events":
            overtaking_events,

        "drs_events":
            drs_events,

        "pit_rejoin_positions":
            pit_rejoin_positions
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


        result = (
            simulate_small_field(
                candidate_pit
            )
        )


        results.append(
            (
                candidate_pit,
                result
            )
        )


    best_entry = min(

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
        best_entry[0],
        best_entry[1],
        results
    )


# =============================================================
# PIT LOSS SENSITIVITY
# =============================================================
#
# We vary the assumed normal pit-stop loss.
#
# For every value:
#
# 1. Re-run the one-stop optimiser.
# 2. Re-run the two-stop optimiser.
# 3. Compare the best race times.
#
# Gap:
#
# two-stop time - one-stop time
#
# Negative = two-stop faster
#
# Positive = one-stop faster
#
# =============================================================

def run_pit_loss_sensitivity():


    global normal_pit_loss


    original_pit_loss = (
        normal_pit_loss
    )


    pit_loss_values = list(
        range(
            10,
            61,
            5
        )
    )


    strategy_gaps = []

    best_one_strategies = []

    best_two_strategies = []


    for test_pit_loss in pit_loss_values:


        normal_pit_loss = (
            float(
                test_pit_loss
            )
        )


        one_result = (
            find_best_one_stop()
        )


        two_result = (
            find_best_two_stop()
        )


        one_time = (
            one_result[2]
        )


        two_time = (
            two_result[3]
        )


        strategy_gap = (
            two_time
            - one_time
        )


        strategy_gaps.append(
            strategy_gap
        )


        best_one_strategies.append(
            (
                one_result[0],
                one_result[1],
                one_time
            )
        )


        best_two_strategies.append(
            (
                two_result[0],
                two_result[1],
                two_result[2],
                two_time
            )
        )


    normal_pit_loss = (
        original_pit_loss
    )


    return (
        pit_loss_values,
        strategy_gaps,
        best_one_strategies,
        best_two_strategies
    )


# =============================================================
# FIND PIT-LOSS STRATEGY SWITCH
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
            y_values[i + 1]
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
                x_values[i + 1]
            )


            switch_point = (

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


            return switch_point


    return None


# =============================================================
# DEGRADATION SENSITIVITY
# =============================================================

def run_degradation_sensitivity():


    global tyre_degradation_scale


    original_scale = (
        tyre_degradation_scale
    )


    scale_values = [
        0.70,
        0.80,
        0.90,
        1.00,
        1.10,
        1.20,
        1.30
    ]


    strategy_gaps = []

    one_stop_pits = []

    two_stop_first_pits = []

    two_stop_second_pits = []


    for scale in scale_values:


        tyre_degradation_scale = (
            scale
        )


        one_result = (
            find_best_one_stop()
        )


        two_result = (
            find_best_two_stop()
        )


        strategy_gap = (
            two_result[3]
            - one_result[2]
        )


        strategy_gaps.append(
            strategy_gap
        )


        one_stop_pits.append(
            one_result[1]
        )


        two_stop_first_pits.append(
            two_result[1]
        )


        two_stop_second_pits.append(
            two_result[2]
        )


    tyre_degradation_scale = (
        original_scale
    )


    return (
        scale_values,
        strategy_gaps,
        one_stop_pits,
        two_stop_first_pits,
        two_stop_second_pits
    )


# =============================================================
# DRS SENSITIVITY
# =============================================================

def run_drs_sensitivity():


    global drs_time_gain


    original_drs_gain = (
        drs_time_gain
    )


    drs_values = [
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


    best_pit_laps = []

    final_positions = []

    final_times = []


    for test_drs_gain in drs_values:


        drs_time_gain = (
            test_drs_gain
        )


        (
            best_pit,
            best_result,
            ignored_results

        ) = find_best_field_pit()


        best_pit_laps.append(
            best_pit
        )


        final_positions.append(
            best_result[
                "final_position"
            ]
        )


        final_times.append(
            best_result[
                "our_final_time"
            ]
        )


    drs_time_gain = (
        original_drs_gain
    )


    return (
        drs_values,
        best_pit_laps,
        final_positions,
        final_times
    )


# =============================================================
# DIRTY AIR SENSITIVITY
# =============================================================

def run_dirty_air_sensitivity():


    global dirty_air_max_penalty


    original_dirty_air = (
        dirty_air_max_penalty
    )


    dirty_air_values = [
        0.0,
        0.2,
        0.4,
        0.6,
        0.8,
        1.0
    ]


    best_pit_laps = []

    final_positions = []

    final_times = []


    for test_dirty_air in dirty_air_values:


        dirty_air_max_penalty = (
            test_dirty_air
        )


        (
            best_pit,
            best_result,
            ignored_results

        ) = find_best_field_pit()


        best_pit_laps.append(
            best_pit
        )


        final_positions.append(
            best_result[
                "final_position"
            ]
        )


        final_times.append(
            best_result[
                "our_final_time"
            ]
        )


    dirty_air_max_penalty = (
        original_dirty_air
    )


    return (
        dirty_air_values,
        best_pit_laps,
        final_positions,
        final_times
    )


# =============================================================
# BASELINE OPTIMISATION
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
# BASELINE FIELD
# =============================================================

(
    best_field_pit,
    best_field_result,
    field_search_results

) = find_best_field_pit()


# =============================================================
# MONTE CARLO SAFETY CAR ANALYSIS
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


for scenario in scenarios:


    safety_car_start = (
        scenario[0]
    )


    safety_car_end = (
        scenario[1]
    )


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


# =============================================================
# RUN SENSITIVITY ANALYSES
# =============================================================

print()
print("Running pit-loss sensitivity...")


(
    pit_loss_values,
    pit_loss_strategy_gaps,
    pit_loss_one_results,
    pit_loss_two_results

) = run_pit_loss_sensitivity()


pit_loss_switch = (
    find_strategy_switch_point(
        pit_loss_values,
        pit_loss_strategy_gaps
    )
)


print(
    "Running tyre-degradation sensitivity..."
)


(
    degradation_scales,
    degradation_strategy_gaps,
    degradation_one_pits,
    degradation_two_pit_1,
    degradation_two_pit_2

) = run_degradation_sensitivity()


print(
    "Running DRS sensitivity..."
)


(
    drs_sensitivity_values,
    drs_best_pits,
    drs_final_positions,
    drs_final_times

) = run_drs_sensitivity()


print(
    "Running dirty-air sensitivity..."
)


(
    dirty_air_sensitivity_values,
    dirty_air_best_pits,
    dirty_air_final_positions,
    dirty_air_final_times

) = run_dirty_air_sensitivity()


# =============================================================
# PRINT BASELINE
# =============================================================

print()

print("==================================")

print("BASELINE RESULTS")

print("==================================")

print()

print("BEST ONE-STOP")

print()

print(
    "Strategy:",
    best_one_stop_name
)

print(
    "Pit lap:",
    best_one_stop_pit
)

print(
    f"Race time: "
    f"{best_one_stop_time:.1f} seconds"
)

print()

print("BEST TWO-STOP")

print()

print(
    "Strategy:",
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
    f"{best_two_stop_time:.1f} seconds"
)

print()

print(
    f"Two-stop advantage: "
    f"{best_one_stop_time - best_two_stop_time:.1f} seconds"
)

print()

print("BEST SMALL-FIELD STRATEGY")

print()

print(
    "Pit lap:",
    best_field_pit
)

print(
    "Final position: P"
    + str(
        best_field_result[
            "final_position"
        ]
    )
)

print(
    f"Final race time: "
    f"{best_field_result['our_final_time']:.3f} seconds"
)


# =============================================================
# PRINT PIT LOSS SENSITIVITY
# =============================================================

print()

print("==================================")

print("PIT LOSS SENSITIVITY")

print("==================================")

print()


for i in range(
    len(pit_loss_values)
):


    pit_loss_value = (
        pit_loss_values[i]
    )


    gap = (
        pit_loss_strategy_gaps[i]
    )


    if gap < 0:

        winner = "Two-stop"


    elif gap > 0:

        winner = "One-stop"


    else:

        winner = "Equal"


    print(
        "Pit loss:",
        pit_loss_value,
        "s"
    )

    print(
        f"Two-stop minus one-stop: "
        f"{gap:.2f} s"
    )

    print(
        "Best strategy type:",
        winner
    )

    print()


if pit_loss_switch is not None:


    print(
        "Estimated strategy-switch pit loss:",
        f"{pit_loss_switch:.2f} seconds"
    )


else:


    print(
        "No strategy switch occurred "
        "inside the tested range."
    )


# =============================================================
# PRINT DEGRADATION SENSITIVITY
# =============================================================

print()

print("==================================")

print("TYRE DEGRADATION SENSITIVITY")

print("==================================")

print()


for i in range(
    len(degradation_scales)
):


    scale = (
        degradation_scales[i]
    )


    gap = (
        degradation_strategy_gaps[i]
    )


    print(
        "Degradation scale:",
        scale
    )

    print(
        "Best one-stop pit:",
        degradation_one_pits[i]
    )

    print(
        "Best two-stop pits:",
        degradation_two_pit_1[i],
        "and",
        degradation_two_pit_2[i]
    )

    print(
        f"Two-stop minus one-stop: "
        f"{gap:.2f} seconds"
    )

    print()


# =============================================================
# PRINT DRS SENSITIVITY
# =============================================================

print()

print("==================================")

print("DRS-STYLE AID SENSITIVITY")

print("==================================")

print()


for i in range(
    len(drs_sensitivity_values)
):


    print(
        "DRS gain:",
        drs_sensitivity_values[i],
        "s/lap"
    )

    print(
        "Best pit lap:",
        drs_best_pits[i]
    )

    print(
        "Final position: P"
        + str(
            drs_final_positions[i]
        )
    )

    print(
        f"Final race time: "
        f"{drs_final_times[i]:.3f} seconds"
    )

    print()


# =============================================================
# PRINT DIRTY AIR SENSITIVITY
# =============================================================

print()

print("==================================")

print("DIRTY AIR SENSITIVITY")

print("==================================")

print()


for i in range(
    len(dirty_air_sensitivity_values)
):


    print(
        "Maximum dirty-air loss:",
        dirty_air_sensitivity_values[i],
        "s/lap"
    )

    print(
        "Best pit lap:",
        dirty_air_best_pits[i]
    )

    print(
        "Final position: P"
        + str(
            dirty_air_final_positions[i]
        )
    )

    print(
        f"Final race time: "
        f"{dirty_air_final_times[i]:.3f} seconds"
    )

    print()


# =============================================================
# GRAPH 1
# TYRE DEGRADATION
# =============================================================

plt.figure(
    figsize=(10, 6)
)


wear_values = []

wear = 0.0


while wear <= 45:


    wear_values.append(
        wear
    )

    wear += 0.5


for tyre_name in tyres:


    losses = []


    for tyre_wear in wear_values:


        losses.append(
            calculate_tyre_loss(
                tyres[
                    tyre_name
                ],
                tyre_wear
            )
        )


    plt.plot(
        wear_values,
        losses,
        label=tyre_name
    )


plt.xlabel(
    "Effective Tyre Wear"
)

plt.ylabel(
    "Lap-Time Loss (seconds)"
)

plt.title(
    "Baseline Tyre Degradation Model"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 2
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
    "Baseline One-Stop Optimisation"
)

plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 3
# FIELD POSITION
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
    label="Pit Stop"
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
# GRAPH 4
# PIT LOSS SENSITIVITY
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
    label="Equal Race Time"
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
    "Pit-Stop Loss (seconds)"
)

plt.ylabel(
    "Two-Stop minus One-Stop (seconds)"
)

plt.title(
    "Strategy Sensitivity to Pit-Stop Loss"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 5
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
    label="Equal Race Time"
)


plt.axvline(
    1.0,
    linestyle="--",
    label="Baseline Degradation"
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
# GRAPH 6
# DEGRADATION VS PIT TIMING
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    degradation_scales,
    degradation_one_pits,
    marker="o",
    label="One-Stop Pit"
)


plt.plot(
    degradation_scales,
    degradation_two_pit_1,
    marker="o",
    label="Two-Stop Pit 1"
)


plt.plot(
    degradation_scales,
    degradation_two_pit_2,
    marker="o",
    label="Two-Stop Pit 2"
)


plt.xlabel(
    "Tyre Degradation Scale"
)

plt.ylabel(
    "Optimal Pit Lap"
)

plt.title(
    "Pit Timing Sensitivity to Tyre Degradation"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 7
# DRS GAIN VS BEST PIT
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    drs_sensitivity_values,
    drs_best_pits,
    marker="o"
)


plt.axvline(
    0.45,
    linestyle="--",
    label="Baseline DRS Gain"
)


plt.xlabel(
    "DRS-Style Lap-Time Gain (seconds)"
)

plt.ylabel(
    "Best Pit Lap"
)

plt.title(
    "Field Strategy Sensitivity to Overtaking Aid"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 8
# DRS GAIN VS FINAL POSITION
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    drs_sensitivity_values,
    drs_final_positions,
    marker="o"
)


plt.axvline(
    0.45,
    linestyle="--",
    label="Baseline DRS Gain"
)


plt.gca().invert_yaxis()


plt.xlabel(
    "DRS-Style Lap-Time Gain (seconds)"
)

plt.ylabel(
    "Best Final Position"
)

plt.title(
    "Final Position Sensitivity to Overtaking Aid"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 9
# DIRTY AIR VS BEST PIT
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    dirty_air_sensitivity_values,
    dirty_air_best_pits,
    marker="o"
)


plt.axvline(
    0.65,
    linestyle="--",
    label="Baseline Dirty-Air Loss"
)


plt.xlabel(
    "Maximum Dirty-Air Loss (seconds/lap)"
)

plt.ylabel(
    "Best Pit Lap"
)

plt.title(
    "Field Strategy Sensitivity to Dirty Air"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 10
# DIRTY AIR VS FINAL POSITION
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    dirty_air_sensitivity_values,
    dirty_air_final_positions,
    marker="o"
)


plt.axvline(
    0.65,
    linestyle="--",
    label="Baseline Dirty-Air Loss"
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

plt.legend()

plt.tight_layout()

plt.show()