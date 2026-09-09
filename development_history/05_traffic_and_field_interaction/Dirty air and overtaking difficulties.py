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
# DIRTY AIR / OVERTAKING MODEL
# =============================================================
#
# Dirty air affects the car immediately behind.
#
# If the gap is greater than dirty_air_range,
# there is no dirty-air penalty.
#
# A following car also needs enough pace
# advantage to complete an on-track overtake.
#
# Position changes caused by pit stops are
# allowed freely.
#
# These are modelling assumptions.
#
# =============================================================

dirty_air_enabled = True

dirty_air_range = 1.5

dirty_air_max_penalty = 0.65

overtake_margin = 0.25

minimum_following_gap = 0.15


# =============================================================
# TYRE DATA
# =============================================================
#
# Each tyre stores:
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
# SMALL FIELD CONFIGURATION
# =============================================================
#
# start_gap:
# race-time gap from the leader at the start.
#
# pace_offset:
#
# Negative = intrinsically faster car
# Positive = intrinsically slower car
#
# Rival strategies remain fixed.
#
# Our pit lap will be changed automatically
# during the field strategy search.
#
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
# FIELD PIT SEARCH
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


    current_fuel = (
        calculate_fuel_mass(
            lap
        )
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
# CALCULATE LAP TIME
# =============================================================

def calculate_lap_time(
        tyre_data,
        tyre_age,
        tyre_wear,
        lap,
        safety_car_start=None,
        safety_car_end=None,
        pace_offset=0.0):


    # -----------------------------
    # Safety Car lap
    # -----------------------------

    if is_safety_car_lap(
        lap,
        safety_car_start,
        safety_car_end
    ):

        return safety_car_lap_time


    # -----------------------------
    # Green-flag lap
    # -----------------------------

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


    fuel_gain = (
        calculate_fuel_time_gain(
            lap
        )
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


        # -----------------------------
        # Pit stop
        # -----------------------------

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


    expected_time = (
        statistics.mean(
            predicted_times
        )
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


        lap_time = (
            calculate_lap_time(
                tyre_data,
                tyre_age,
                tyre_wear,
                lap,
                actual_safety_car_start,
                actual_safety_car_end
            )
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


            # -----------------------------
            # Normal planned stop
            # -----------------------------

            if lap == planned_pit:

                should_pit = True


            # -----------------------------
            # Safety Car decision
            # -----------------------------

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


        # -----------------------------
        # Execute pit stop
        # -----------------------------

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


    best_index = (
        race_times.index(
            best_time
        )
    )


    best_pit_lap = (
        pit_laps_tested[
            best_index
        ]
    )


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
# GENERATE RANDOM SAFETY CARS
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


        safety_car_occurs = (
            random.random()
            < safety_car_probability
        )


        if safety_car_occurs:


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
                    car["tyre_sequence"]
                ),

            "pit_laps":
                list(
                    car["pit_laps"]
                ),

            "pace_offset":
                car["pace_offset"]
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
#
# This simulates the cars together.
#
# Every lap:
#
# 1. Sort cars by current race time.
#
# 2. Calculate each car's theoretical pace.
#
# 3. Apply dirty air to followers.
#
# 4. Add pit-stop losses.
#
# 5. Check attempted on-track overtakes.
#
# 6. Update the running order.
#
# =============================================================

def simulate_small_field(
        our_pit_lap):


    field = (
        copy_field_configuration(
            our_pit_lap
        )
    )


    # =========================================================
    # INITIAL CAR STATES
    # =========================================================

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


    # =========================================================
    # STORAGE
    # =========================================================

    our_position_history = []

    gap_to_ahead_history = []

    gap_to_behind_history = []

    our_dirty_air_history = []


    field_order_history = []


    overtaking_events = []


    pit_rejoin_positions = {}


    # =========================================================
    # RACE LOOP
    # =========================================================

    for lap in range(
        1,
        race_laps + 1
    ):


        # -----------------------------------------------------
        # Running order at beginning of lap
        # -----------------------------------------------------

        running_order = sorted(

            field,

            key=lambda car:
                states[
                    car["name"]
                ]["total_time"]
        )


        # -----------------------------------------------------
        # Calculate lap times
        # -----------------------------------------------------

        effective_lap_times = {}

        dirty_air_penalties = {}

        cars_pitting = {}


        for index in range(
            len(running_order)
        ):


            car = (
                running_order[
                    index
                ]
            )


            car_name = (
                car["name"]
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
                    car_state["stint"]
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


            # -------------------------------------------------
            # Dirty air from directly ahead
            # -------------------------------------------------

            dirty_air_penalty = 0.0


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


            cars_pitting[
                car_name
            ] = (
                is_pitting
            )


        # =====================================================
        # PREDICT NEW TOTAL TIMES
        # =====================================================

        predicted_total_times = {}


        for car in field:


            car_name = (
                car["name"]
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


        # =====================================================
        # OVERTAKING DIFFICULTY
        # =====================================================
        #
        # We compare each following car with the car
        # directly ahead at the start of the lap.
        #
        # If the follower would cross ahead but did not
        # have enough lap-time advantage, hold the car
        # just behind.
        #
        # If either car pits, allow the position change.
        #
        # =====================================================

        adjusted_total_times = (
            predicted_total_times.copy()
        )


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


            # -------------------------------------------------
            # On-track pass attempt
            # -------------------------------------------------

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


                    if (
                        lap_time_advantage
                        < overtake_margin
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


                        overtaking_events.append(
                            (
                                lap,
                                following_name,
                                ahead_name
                            )
                        )


        # =====================================================
        # UPDATE CAR TIMES
        # =====================================================

        for car in field:


            car_name = (
                car["name"]
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


        # =====================================================
        # UPDATE TYRE STATES
        # =====================================================

        wear_increment = (
            calculate_fuel_wear_increment(
                lap
            )
        )


        for car in field:


            car_name = (
                car["name"]
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


            # -------------------------------------------------
            # Pit reset
            # -------------------------------------------------

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
        # NEW RUNNING ORDER
        # =====================================================

        new_running_order = sorted(

            field,

            key=lambda car:
                states[
                    car["name"]
                ]["total_time"]
        )


        order_names = []


        for car in new_running_order:


            order_names.append(
                car["name"]
            )


        field_order_history.append(
            order_names
        )


        # =====================================================
        # OUR POSITION
        # =====================================================

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
        # Gap to car ahead
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
        # Gap to car behind
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


        # -----------------------------------------------------
        # Record pit rejoin position
        # -----------------------------------------------------

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
            ]["total_time"]
    )


    final_order = []


    for car in final_running_order:


        car_name = (
            car["name"]
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


    # ---------------------------------------------------------
    # Final gap to car ahead
    # ---------------------------------------------------------

    if final_position == 1:


        final_gap_to_ahead = None


    else:


        ahead_name = (
            final_names[
                final_position - 2
            ]
        )


        final_gap_to_ahead = (

            our_final_time

            - states[
                ahead_name
            ][
                "total_time"
            ]
        )


    # ---------------------------------------------------------
    # Final gap to car behind
    # ---------------------------------------------------------

    if (
        final_position
        == len(final_names)
    ):


        final_gap_to_behind = None


    else:


        behind_name = (
            final_names[
                final_position
            ]
        )


        final_gap_to_behind = (

            states[
                behind_name
            ][
                "total_time"
            ]

            - our_final_time
        )


    return {

        "final_position":
            final_position,

        "our_final_time":
            our_final_time,

        "final_order":
            final_order,

        "final_gap_to_ahead":
            final_gap_to_ahead,

        "final_gap_to_behind":
            final_gap_to_behind,

        "position_history":
            our_position_history,

        "gap_to_ahead_history":
            gap_to_ahead_history,

        "gap_to_behind_history":
            gap_to_behind_history,

        "dirty_air_history":
            our_dirty_air_history,

        "field_order_history":
            field_order_history,

        "overtaking_events":
            overtaking_events,

        "pit_rejoin_positions":
            pit_rejoin_positions
    }


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

one_stop_combination_count = (
    one_stop_search[4]
)


best_one_stop_name = (
    best_one_stop_strategy[0]
    + " -> "
    + best_one_stop_strategy[1]
)


best_one_stop_pits = [
    best_one_stop_pit
]


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

two_stop_combination_count = (
    two_stop_search[4]
)


best_two_stop_name = (
    best_two_stop_strategy[0]
    + " -> "
    + best_two_stop_strategy[1]
    + " -> "
    + best_two_stop_strategy[2]
)


best_two_stop_pits = [
    best_two_stop_pit_1,
    best_two_stop_pit_2
]


# =============================================================
# BASELINE TRACES
# =============================================================

(
    baseline_one_total,
    baseline_one_lap_times,
    baseline_one_cumulative

) = simulate_fixed_strategy(

    list(
        best_one_stop_strategy
    ),

    best_one_stop_pits,

    return_trace=True
)


(
    baseline_two_total,
    baseline_two_lap_times,
    baseline_two_cumulative

) = simulate_fixed_strategy(

    list(
        best_two_stop_strategy
    ),

    best_two_stop_pits,

    return_trace=True
)


race_lap_numbers = list(
    range(
        1,
        race_laps + 1
    )
)


baseline_strategy_gap = []


for i in range(
    race_laps
):


    gap = (
        baseline_two_cumulative[i]
        - baseline_one_cumulative[i]
    )


    baseline_strategy_gap.append(
        gap
    )


# =============================================================
# SAFETY CAR MONTE CARLO
# =============================================================

scenarios = (
    generate_safety_car_scenarios(
        monte_carlo_runs
    )
)


safety_car_count = 0


for scenario in scenarios:


    if scenario[0] is not None:

        safety_car_count += 1


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


    # ---------------------------------------------------------
    # Fixed one-stop
    # ---------------------------------------------------------

    fixed_one_time = (
        simulate_fixed_strategy(

            list(
                best_one_stop_strategy
            ),

            best_one_stop_pits,

            safety_car_start,

            safety_car_end
        )
    )


    fixed_one_times.append(
        fixed_one_time
    )


    # ---------------------------------------------------------
    # Uncertainty-aware one-stop
    # ---------------------------------------------------------

    (
        uncertain_one_time,
        actual_one_pits,
        one_decisions

    ) = simulate_uncertainty_strategy(

        list(
            best_one_stop_strategy
        ),

        best_one_stop_pits,

        safety_car_start,

        safety_car_end
    )


    uncertain_one_times.append(
        uncertain_one_time
    )


    # ---------------------------------------------------------
    # Fixed two-stop
    # ---------------------------------------------------------

    fixed_two_time = (
        simulate_fixed_strategy(

            list(
                best_two_stop_strategy
            ),

            best_two_stop_pits,

            safety_car_start,

            safety_car_end
        )
    )


    fixed_two_times.append(
        fixed_two_time
    )


    # ---------------------------------------------------------
    # Uncertainty-aware two-stop
    # ---------------------------------------------------------

    (
        uncertain_two_time,
        actual_two_pits,
        two_decisions

    ) = simulate_uncertainty_strategy(

        list(
            best_two_stop_strategy
        ),

        best_two_stop_pits,

        safety_car_start,

        safety_car_end
    )


    uncertain_two_times.append(
        uncertain_two_time
    )


# =============================================================
# MONTE CARLO STATISTICS
# =============================================================

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


one_stop_benefits = []

two_stop_benefits = []

monte_carlo_strategy_gaps = []


one_stop_wins = 0

two_stop_wins = 0

ties = 0


for i in range(
    monte_carlo_runs
):


    one_benefit = (
        fixed_one_times[i]
        - uncertain_one_times[i]
    )


    two_benefit = (
        fixed_two_times[i]
        - uncertain_two_times[i]
    )


    one_stop_benefits.append(
        one_benefit
    )


    two_stop_benefits.append(
        two_benefit
    )


    strategy_gap = (
        uncertain_two_times[i]
        - uncertain_one_times[i]
    )


    monte_carlo_strategy_gaps.append(
        strategy_gap
    )


    if strategy_gap < 0:

        two_stop_wins += 1


    elif strategy_gap > 0:

        one_stop_wins += 1


    else:

        ties += 1


average_one_benefit = (
    statistics.mean(
        one_stop_benefits
    )
)


average_two_benefit = (
    statistics.mean(
        two_stop_benefits
    )
)


average_strategy_gap = (
    statistics.mean(
        monte_carlo_strategy_gaps
    )
)


# =============================================================
# SMALL FIELD PIT SEARCH
# =============================================================

field_search_results = []


for candidate_pit in range(
    field_pit_search_start,
    field_pit_search_end + 1
):


    field_result = (
        simulate_small_field(
            candidate_pit
        )
    )


    field_search_results.append(
        {
            "pit_lap":
                candidate_pit,

            "result":
                field_result
        }
    )


# =============================================================
# FIND BEST FIELD STRATEGY
# =============================================================
#
# Primary objective:
# best finishing position
#
# Secondary objective:
# lowest race time
#
# =============================================================

best_field_entry = min(

    field_search_results,

    key=lambda entry:
        (
            entry[
                "result"
            ][
                "final_position"
            ],

            entry[
                "result"
            ][
                "our_final_time"
            ]
        )
)


best_field_pit = (
    best_field_entry[
        "pit_lap"
    ]
)


best_field_result = (
    best_field_entry[
        "result"
    ]
)


best_rejoin_position = (
    best_field_result[
        "pit_rejoin_positions"
    ][
        best_field_pit
    ]
)


# =============================================================
# PRINT MODEL SETTINGS
# =============================================================

print("MODEL SETTINGS")

print()

print(
    "Race laps:",
    race_laps
)

print(
    "Normal pit loss:",
    normal_pit_loss,
    "seconds"
)

print(
    "Minimum stint:",
    minimum_stint,
    "laps"
)

print()

print("TYRE MODEL")

print()

print(
    "Non-linear degradation: enabled"
)

print(
    "Warm-up model: enabled"
)

print(
    "Tyre cliff: enabled"
)

print(
    "Fuel-dependent tyre wear: enabled"
)

print()

print("SAFETY CAR MODEL")

print()

print(
    "Random Safety Cars: enabled"
)

print(
    "Decision under duration uncertainty: enabled"
)

print()

print("FIELD MODEL")

print()

print(
    "Cars in field:",
    len(
        field_configuration
    )
)

print(
    "Dirty-air range:",
    dirty_air_range,
    "seconds"
)

print(
    "Maximum dirty-air loss:",
    dirty_air_max_penalty,
    "seconds/lap"
)

print(
    "Overtake margin:",
    overtake_margin,
    "seconds"
)

print()

print("----------------------------------")


# =============================================================
# PRINT ONE-STOP RESULTS
# =============================================================

print()

print("ONE-STOP AUTOMATIC SEARCH")

print()

print(
    "Legal combinations:",
    one_stop_combination_count
)

print()


for strategy_name in one_stop_results:


    result = (
        one_stop_results[
            strategy_name
        ]
    )


    print(
        strategy_name
    )


    print(
        "Best pit lap:",
        result[0]
    )


    print(
        "Stint lengths:",
        result[0],
        "+",
        race_laps
        - result[0]
    )


    print(
        f"Race time: "
        f"{result[1]:.1f} seconds"
    )


    print()


# =============================================================
# PRINT BASELINE WINNERS
# =============================================================

print("----------------------------------")

print()

print(
    "BEST BASELINE ONE-STOP"
)

print()

print(
    "Strategy:",
    best_one_stop_name
)

print(
    "Pit:",
    best_one_stop_pit
)

print(
    "Stints:",
    best_one_stop_pit,
    "+",
    race_laps
    - best_one_stop_pit
)

print(
    f"Race time: "
    f"{best_one_stop_time:.1f} seconds"
)

print()


print(
    "BEST BASELINE TWO-STOP"
)

print()

print(
    "Strategy:",
    best_two_stop_name
)

print(
    "Pits:",
    best_two_stop_pit_1,
    "and",
    best_two_stop_pit_2
)

print(
    "Stints:",
    best_two_stop_pit_1,
    "+",
    best_two_stop_pit_2
    - best_two_stop_pit_1,
    "+",
    race_laps
    - best_two_stop_pit_2
)

print(
    f"Race time: "
    f"{best_two_stop_time:.1f} seconds"
)


# =============================================================
# PRINT MONTE CARLO RESULTS
# =============================================================

print()

print("----------------------------------")

print()

print(
    "MONTE CARLO SAFETY CAR ANALYSIS"
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

print(
    "No Safety Car races:",
    monte_carlo_runs
    - safety_car_count
)

print()


print("ONE-STOP")

print()

print(
    f"Fixed mean: "
    f"{fixed_one_mean:.3f} seconds"
)

print(
    f"Uncertainty-aware mean: "
    f"{uncertain_one_mean:.3f} seconds"
)

print(
    f"Average decision benefit: "
    f"{average_one_benefit:.3f} seconds"
)

print()


print("TWO-STOP")

print()

print(
    f"Fixed mean: "
    f"{fixed_two_mean:.3f} seconds"
)

print(
    f"Uncertainty-aware mean: "
    f"{uncertain_two_mean:.3f} seconds"
)

print(
    f"Average decision benefit: "
    f"{average_two_benefit:.3f} seconds"
)

print()

print(
    "One-stop wins:",
    one_stop_wins
)

print(
    "Two-stop wins:",
    two_stop_wins
)

print(
    "Ties:",
    ties
)

print(
    f"Average two-stop minus one-stop gap: "
    f"{average_strategy_gap:.3f} seconds"
)


# =============================================================
# PRINT FIELD CONFIGURATION
# =============================================================

print()

print("----------------------------------")

print()

print(
    "SMALL FIELD SIMULATION"
)

print()


for car in field_configuration:


    print(
        car["name"]
    )


    print(
        "Starting gap:",
        car["start_gap"],
        "seconds"
    )


    print(
        "Strategy:",
        " -> ".join(
            car[
                "tyre_sequence"
            ]
        )
    )


    print(
        "Pit plan:",
        car[
            "pit_laps"
        ]
    )


    print(
        "Pace offset:",
        car[
            "pace_offset"
        ]
    )


    print()


# =============================================================
# PRINT FIELD PIT SEARCH
# =============================================================

print("----------------------------------")

print()

print(
    "FIELD PIT-LAP SEARCH"
)

print()


for entry in field_search_results:


    pit_lap = (
        entry[
            "pit_lap"
        ]
    )


    result = (
        entry[
            "result"
        ]
    )


    rejoin_position = (
        result[
            "pit_rejoin_positions"
        ][
            pit_lap
        ]
    )


    print(
        "Pit lap:",
        pit_lap
    )


    print(
        "Pit rejoin position: P"
        + str(
            rejoin_position
        )
    )


    print(
        "Final position: P"
        + str(
            result[
                "final_position"
            ]
        )
    )


    print(
        f"Final race time: "
        f"{result['our_final_time']:.3f} seconds"
    )


    if (
        result[
            "final_gap_to_ahead"
        ]
        is not None
    ):


        print(
            f"Gap to car ahead: "
            f"{result['final_gap_to_ahead']:.3f} seconds"
        )


    else:


        print(
            "Gap to car ahead: LEADER"
        )


    if (
        result[
            "final_gap_to_behind"
        ]
        is not None
    ):


        print(
            f"Gap to car behind: "
            f"{result['final_gap_to_behind']:.3f} seconds"
        )


    print()


# =============================================================
# PRINT BEST FIELD STRATEGY
# =============================================================

print("----------------------------------")

print()

print(
    "BEST FIELD STRATEGY"
)

print()

print(
    "Pit lap:",
    best_field_pit
)

print(
    "Pit rejoin position: P"
    + str(
        best_rejoin_position
    )
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

print()


if (
    best_field_result[
        "final_position"
    ] == 1
):


    print(
        "Result: Our car wins the simulated field."
    )


else:


    print(
        "Result: Our car finishes P"
        + str(
            best_field_result[
                "final_position"
            ]
        )
    )


print()

print("FINAL RUNNING ORDER")

print()


for position in range(
    len(
        best_field_result[
            "final_order"
        ]
    )
):


    car_name = (
        best_field_result[
            "final_order"
        ][
            position
        ][0]
    )


    car_time = (
        best_field_result[
            "final_order"
        ][
            position
        ][1]
    )


    print(
        "P"
        + str(
            position + 1
        ),
        "-",
        car_name,
        "-",
        f"{car_time:.3f} s"
    )


# =============================================================
# PRINT OVERTAKE EVENTS
# =============================================================

print()

print(
    "ON-TRACK OVERTAKE EVENTS"
)

print()


if len(
    best_field_result[
        "overtaking_events"
    ]
) == 0:


    print(
        "No successful on-track overtakes."
    )


else:


    for event in (
        best_field_result[
            "overtaking_events"
        ]
    ):


        print(
            "Lap",
            event[0],
            "-",
            event[1],
            "passed",
            event[2]
        )


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
    "Tyre Degradation with Cliff Behaviour"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 2
# TYRE WARM-UP
# =============================================================

plt.figure(
    figsize=(10, 6)
)


warmup_ages = list(
    range(
        0,
        10
    )
)


for tyre_name in tyres:


    penalties = []


    for tyre_age in warmup_ages:


        penalties.append(
            calculate_warmup_penalty(
                tyres[
                    tyre_name
                ],
                tyre_age
            )
        )


    plt.plot(
        warmup_ages,
        penalties,
        label=tyre_name
    )


plt.xlabel(
    "Tyre Age (laps)"
)

plt.ylabel(
    "Warm-Up Penalty (seconds)"
)

plt.title(
    "Fresh-Tyre Warm-Up Model"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 3
# FUEL MASS
# =============================================================

plt.figure(
    figsize=(10, 6)
)


fuel_masses = []


for lap in race_lap_numbers:


    fuel_masses.append(
        calculate_fuel_mass(
            lap
        )
    )


plt.plot(
    race_lap_numbers,
    fuel_masses
)


plt.xlabel(
    "Race Lap"
)

plt.ylabel(
    "Fuel Mass (kg)"
)

plt.title(
    "Fuel Load Through Race"
)

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 4
# BASELINE ONE-STOP OPTIMISATION
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
    "Baseline One-Stop Strategy Optimisation"
)

plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 5
# BASELINE LAP-TIME COMPARISON
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    race_lap_numbers,
    baseline_one_lap_times,
    label=(
        "One Stop: "
        + best_one_stop_name
    )
)


plt.plot(
    race_lap_numbers,
    baseline_two_lap_times,
    label=(
        "Two Stop: "
        + best_two_stop_name
    )
)


plt.axvline(
    best_one_stop_pit,
    linestyle="--",
    label="One-Stop Pit"
)


plt.axvline(
    best_two_stop_pit_1,
    linestyle="--",
    label="Two-Stop Pit 1"
)


plt.axvline(
    best_two_stop_pit_2,
    linestyle="--",
    label="Two-Stop Pit 2"
)


plt.xlabel(
    "Race Lap"
)

plt.ylabel(
    "Lap Time (seconds)"
)

plt.title(
    "Best Baseline Strategy Lap Times"
)

plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 6
# BASELINE STRATEGY GAP
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    race_lap_numbers,
    baseline_strategy_gap
)


plt.axhline(
    0,
    linestyle="--"
)


plt.xlabel(
    "Race Lap"
)

plt.ylabel(
    "Two-Stop minus One-Stop (seconds)"
)

plt.title(
    "Baseline Strategy Time Gap"
)

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 7
# SAFETY CAR DECISION BENEFIT
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.hist(
    one_stop_benefits,
    bins=25,
    alpha=0.6,
    label="One-Stop"
)


plt.hist(
    two_stop_benefits,
    bins=25,
    alpha=0.6,
    label="Two-Stop"
)


plt.axvline(
    0,
    linestyle="--",
    label="No Benefit"
)


plt.xlabel(
    "Fixed Time minus Optimised Time (seconds)"
)

plt.ylabel(
    "Simulated Races"
)

plt.title(
    "Safety Car Decision Benefit"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 8
# MONTE CARLO STRATEGY GAP
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.hist(
    monte_carlo_strategy_gaps,
    bins=25
)


plt.axvline(
    0,
    linestyle="--",
    label="Equal Race Time"
)


plt.xlabel(
    "Two-Stop minus One-Stop (seconds)"
)

plt.ylabel(
    "Simulated Races"
)

plt.title(
    "Monte Carlo Strategy Comparison"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 9
# OUR POSITION THROUGH FIELD RACE
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    race_lap_numbers,
    best_field_result[
        "position_history"
    ]
)


plt.axvline(
    best_field_pit,
    linestyle="--",
    label="Our Pit Stop"
)


plt.gca().invert_yaxis()


plt.xlabel(
    "Race Lap"
)

plt.ylabel(
    "Track Position"
)

plt.title(
    "Our Position Through the Small-Field Race"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 10
# GAP TO CAR AHEAD
# =============================================================

gap_ahead_plot = []


for gap in (
    best_field_result[
        "gap_to_ahead_history"
    ]
):


    if gap is None:

        gap_ahead_plot.append(
            0.0
        )


    else:

        gap_ahead_plot.append(
            gap
        )


plt.figure(
    figsize=(10, 6)
)


plt.plot(
    race_lap_numbers,
    gap_ahead_plot
)


plt.axhline(
    dirty_air_range,
    linestyle="--",
    label="Dirty-Air Range"
)


plt.axvline(
    best_field_pit,
    linestyle="--",
    label="Our Pit Stop"
)


plt.xlabel(
    "Race Lap"
)

plt.ylabel(
    "Gap to Car Ahead (seconds)"
)

plt.title(
    "Gap to Car Ahead"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 11
# OUR DIRTY-AIR PENALTY
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    race_lap_numbers,
    best_field_result[
        "dirty_air_history"
    ]
)


plt.axvline(
    best_field_pit,
    linestyle="--",
    label="Our Pit Stop"
)


plt.xlabel(
    "Race Lap"
)

plt.ylabel(
    "Dirty-Air Penalty (seconds/lap)"
)

plt.title(
    "Our Dirty-Air Loss Through the Race"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 12
# FINAL POSITION VS PIT LAP
# =============================================================

field_candidate_pits = []

field_final_positions = []


for entry in field_search_results:


    field_candidate_pits.append(
        entry[
            "pit_lap"
        ]
    )


    field_final_positions.append(
        entry[
            "result"
        ][
            "final_position"
        ]
    )


plt.figure(
    figsize=(10, 6)
)


plt.plot(
    field_candidate_pits,
    field_final_positions,
    marker="o"
)


plt.axvline(
    best_field_pit,
    linestyle="--",
    label="Best Pit Lap"
)


plt.gca().invert_yaxis()


plt.xlabel(
    "Our Pit Lap"
)

plt.ylabel(
    "Final Position"
)

plt.title(
    "Final Position vs Pit Timing"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 13
# FINAL RACE TIME VS PIT LAP
# =============================================================

field_final_times = []


for entry in field_search_results:


    field_final_times.append(
        entry[
            "result"
        ][
            "our_final_time"
        ]
    )


plt.figure(
    figsize=(10, 6)
)


plt.plot(
    field_candidate_pits,
    field_final_times,
    marker="o"
)


plt.axvline(
    best_field_pit,
    linestyle="--",
    label="Best Field Pit"
)


plt.xlabel(
    "Our Pit Lap"
)

plt.ylabel(
    "Our Final Race Time (seconds)"
)

plt.title(
    "Race Time vs Pit Timing in Traffic"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 14
# PIT REJOIN POSITION VS PIT LAP
# =============================================================

field_rejoin_positions = []


for entry in field_search_results:


    pit_lap = (
        entry[
            "pit_lap"
        ]
    )


    rejoin_position = (
        entry[
            "result"
        ][
            "pit_rejoin_positions"
        ][
            pit_lap
        ]
    )


    field_rejoin_positions.append(
        rejoin_position
    )


plt.figure(
    figsize=(10, 6)
)


plt.plot(
    field_candidate_pits,
    field_rejoin_positions,
    marker="o"
)


plt.axvline(
    best_field_pit,
    linestyle="--",
    label="Best Field Pit"
)


plt.gca().invert_yaxis()


plt.xlabel(
    "Our Pit Lap"
)

plt.ylabel(
    "Position Immediately After Pit"
)

plt.title(
    "Pit Rejoin Position vs Pit Timing"
)

plt.legend()

plt.tight_layout()

plt.show()