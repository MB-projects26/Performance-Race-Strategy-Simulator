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
# RIVAL CAR SETTINGS
# =============================================================
#
# This is a separate green-flag battle analysis.
#
# Our car begins 2 seconds behind the rival.
#
# Both cars use the same underlying tyre model.
#
# The rival has a fixed strategy:
#
# Medium -> Soft
# Pit lap 31
#
# =============================================================

rival_name = "Rival"

rival_tyre_sequence = [
    "Medium",
    "Soft"
]

rival_pit_laps = [
    31
]

# Our car begins this many seconds behind
# the rival.

initial_gap_to_rival = 2.0

# Positive number = rival is intrinsically slower.
# Negative number = rival is intrinsically faster.
#
# Keep at zero for now so the pit strategy itself
# determines the battle.

rival_pace_offset = 0.0

# Test pit stops this many laps before/after
# the rival's stop.

battle_window = 5


# =============================================================
# TYRE DATA
# =============================================================
#
# Each tyre contains:
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
# FUNCTION: CHECK SAFETY CAR LAP
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
# FUNCTION: PIT LOSS
# =============================================================

def calculate_pit_loss(
        lap,
        safety_car_start,
        safety_car_end):

    if is_safety_car_lap(
        lap,
        safety_car_start,
        safety_car_end
    ):

        return safety_car_pit_loss

    return normal_pit_loss


# =============================================================
# FUNCTION: FUEL MASS
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
# FUNCTION: FUEL LAP-TIME GAIN
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
# FUNCTION: FUEL EFFECT ON TYRE WEAR
# =============================================================

def calculate_fuel_wear_increment(
        lap,
        safety_car_start,
        safety_car_end):

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

    # Less wear behind Safety Car

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
# FUNCTION: TYRE CLIFF
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
# FUNCTION: TYRE DEGRADATION
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


    return total_loss


# =============================================================
# FUNCTION: TYRE WARM-UP
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
# FUNCTION: CALCULATE LAP TIME
# =============================================================

def calculate_lap_time(
        tyre_data,
        tyre_age,
        tyre_wear,
        lap,
        safety_car_start,
        safety_car_end,
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


    warmup_penalty = calculate_warmup_penalty(
        tyre_data,
        tyre_age
    )


    fuel_time_gain = calculate_fuel_time_gain(
        lap
    )


    lap_time = (
        base_time
        + tyre_loss
        + warmup_penalty
        - fuel_time_gain
        + pace_offset
    )


    return lap_time


# =============================================================
# FUNCTION: CHECK PIT PLAN
# =============================================================

def pit_plan_is_legal(
        pit_laps):


    # Pit laps must be increasing

    for i in range(
        len(pit_laps) - 1
    ):

        if (
            pit_laps[i]
            >= pit_laps[i + 1]
        ):

            return False


    if len(pit_laps) == 0:

        return (
            race_laps
            >= minimum_stint
        )


    # -----------------------------
    # Calculate stint lengths
    # -----------------------------

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
# FUNCTION: FIXED STRATEGY SIMULATION
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


        current_tyre_name = (
            tyre_sequence[
                stint_number
            ]
        )


        current_tyre = tyres[
            current_tyre_name
        ]


        lap_time = calculate_lap_time(
            current_tyre,
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


        # -----------------------------
        # Pit stop
        # -----------------------------

        if (
            pit_number
            < len(pit_laps)
            and lap
            == pit_laps[pit_number]
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


        # -----------------------------
        # Save trace
        # -----------------------------

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
# FUNCTION: POSSIBLE SAFETY CAR END LAPS
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


        # If the SC is still active now,
        # it cannot already have ended.

        if possible_end >= current_lap:

            possible_end_laps.append(
                possible_end
            )


    return possible_end_laps


# =============================================================
# FUNCTION: EXPECTED PIT-PLAN TIME
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
# FUNCTION: UNCERTAINTY-AWARE STRATEGY
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


        current_tyre_name = (
            tyre_sequence[
                stint_number
            ]
        )


        current_tyre = tyres[
            current_tyre_name
        ]


        lap_time = calculate_lap_time(
            current_tyre,
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


        # -----------------------------
        # Pit decision
        # -----------------------------

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


            # Planned stop

            if lap == planned_pit:

                should_pit = True


            # Safety Car opportunity

            elif (
                is_safety_car_lap(
                    lap,
                    actual_safety_car_start,
                    actual_safety_car_end
                )
                and lap < planned_pit
            ):


                # -----------------------------
                # Stay out
                # -----------------------------

                stay_out_plan = (
                    actual_pit_laps
                    + planned_pit_laps[
                        pit_number:
                    ]
                )


                # -----------------------------
                # Pit now
                # -----------------------------

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
                        possible_end_laps

                    ) = calculate_expected_plan_time(

                        tyre_sequence,

                        stay_out_plan,

                        actual_safety_car_start,

                        lap
                    )


                    (
                        expected_pit_time,
                        ignored_end_laps

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
                            possible_end_laps,
                            expected_stay_time,
                            expected_pit_time,
                            decision
                        )
                    )


        # -----------------------------
        # Execute pit stop
        # -----------------------------

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
# FUNCTION: ONE-STOP OPTIMISATION
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
# FUNCTION: TWO-STOP OPTIMISATION
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
# FUNCTION: FIND BEST ONE-STOP
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


            # Different compounds required

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
# FUNCTION: FIND BEST TWO-STOP
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


                # At least two compounds required

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
# FUNCTION: RANDOM SAFETY CAR SCENARIOS
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
# FUNCTION: CALCULATE TRACK GAP
# =============================================================
#
# Positive gap:
# our car is behind rival
#
# Negative gap:
# our car is ahead of rival
#
# =============================================================

def calculate_track_gap(
        our_cumulative_times,
        rival_cumulative_times,
        starting_gap):


    track_gaps = []


    for i in range(
        race_laps
    ):


        gap = (
            starting_gap
            + our_cumulative_times[i]
            - rival_cumulative_times[i]
        )


        track_gaps.append(
            gap
        )


    return track_gaps


# =============================================================
# FUNCTION: ANALYSE PIT BATTLE
# =============================================================

def analyse_pit_battle(
        our_pit_lap,
        rival_cumulative_times):


    our_total, our_lap_times, our_cumulative = (
        simulate_fixed_strategy(
            rival_tyre_sequence,
            [our_pit_lap],
            return_trace=True
        )
    )


    track_gaps = calculate_track_gap(
        our_cumulative,
        rival_cumulative_times,
        initial_gap_to_rival
    )


    rival_pit_lap = (
        rival_pit_laps[0]
    )


    earlier_pit = min(
        our_pit_lap,
        rival_pit_lap
    )


    later_pit = max(
        our_pit_lap,
        rival_pit_lap
    )


    # Gap on lap before the first car pits

    before_cycle_lap = (
        earlier_pit - 1
    )


    if before_cycle_lap < 1:

        gap_before_cycle = (
            initial_gap_to_rival
        )

    else:

        gap_before_cycle = (
            track_gaps[
                before_cycle_lap - 1
            ]
        )


    # Gap immediately after our own stop

    rejoin_gap = (
        track_gaps[
            our_pit_lap - 1
        ]
    )


    # Gap once both cars have completed
    # their pit stops

    gap_after_cycle = (
        track_gaps[
            later_pit - 1
        ]
    )


    final_gap = (
        track_gaps[-1]
    )


    pit_cycle_gain = (
        gap_before_cycle
        - gap_after_cycle
    )


    # -----------------------------
    # Classify tactic
    # -----------------------------

    if (
        our_pit_lap
        < rival_pit_lap
    ):

        tactic = "Undercut"


        if (
            gap_before_cycle > 0
            and gap_after_cycle < 0
        ):

            outcome = (
                "Successful undercut"
            )

        else:

            outcome = (
                "Undercut did not gain position"
            )


    elif (
        our_pit_lap
        > rival_pit_lap
    ):

        tactic = "Overcut"


        if (
            gap_before_cycle > 0
            and gap_after_cycle < 0
        ):

            outcome = (
                "Successful overcut"
            )

        else:

            outcome = (
                "Overcut did not gain position"
            )


    else:

        tactic = "Same-lap stop"

        outcome = (
            "No undercut or overcut"
        )


    return {

        "pit_lap":
            our_pit_lap,

        "tactic":
            tactic,

        "outcome":
            outcome,

        "gap_before_cycle":
            gap_before_cycle,

        "rejoin_gap":
            rejoin_gap,

        "gap_after_cycle":
            gap_after_cycle,

        "pit_cycle_gain":
            pit_cycle_gain,

        "final_gap":
            final_gap,

        "race_time":
            our_total,

        "lap_times":
            our_lap_times,

        "cumulative_times":
            our_cumulative,

        "track_gaps":
            track_gaps
    }


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
# BASELINE LAP TRACES
# =============================================================

(
    baseline_one_total,
    baseline_one_lap_times,
    baseline_one_cumulative

) = simulate_fixed_strategy(

    list(best_one_stop_strategy),

    best_one_stop_pits,

    return_trace=True
)


(
    baseline_two_total,
    baseline_two_lap_times,
    baseline_two_cumulative

) = simulate_fixed_strategy(

    list(best_two_stop_strategy),

    best_two_stop_pits,

    return_trace=True
)


race_lap_numbers = list(
    range(
        1,
        race_laps + 1
    )
)


baseline_gap = []


for i in range(
    race_laps
):


    gap = (
        baseline_two_cumulative[i]
        - baseline_one_cumulative[i]
    )


    baseline_gap.append(
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


uncertain_one_pit_plans = []

uncertain_two_pit_plans = []


for scenario in scenarios:


    safety_car_start = scenario[0]

    safety_car_end = scenario[1]


    # -----------------------------
    # Fixed one-stop
    # -----------------------------

    fixed_one_time = (
        simulate_fixed_strategy(
            list(best_one_stop_strategy),
            best_one_stop_pits,
            safety_car_start,
            safety_car_end
        )
    )


    fixed_one_times.append(
        fixed_one_time
    )


    # -----------------------------
    # Uncertainty-aware one-stop
    # -----------------------------

    (
        uncertain_one_time,
        actual_one_pits,
        one_decisions

    ) = simulate_uncertainty_strategy(

        list(best_one_stop_strategy),

        best_one_stop_pits,

        safety_car_start,

        safety_car_end
    )


    uncertain_one_times.append(
        uncertain_one_time
    )


    uncertain_one_pit_plans.append(
        actual_one_pits
    )


    # -----------------------------
    # Fixed two-stop
    # -----------------------------

    fixed_two_time = (
        simulate_fixed_strategy(
            list(best_two_stop_strategy),
            best_two_stop_pits,
            safety_car_start,
            safety_car_end
        )
    )


    fixed_two_times.append(
        fixed_two_time
    )


    # -----------------------------
    # Uncertainty-aware two-stop
    # -----------------------------

    (
        uncertain_two_time,
        actual_two_pits,
        two_decisions

    ) = simulate_uncertainty_strategy(

        list(best_two_stop_strategy),

        best_two_stop_pits,

        safety_car_start,

        safety_car_end
    )


    uncertain_two_times.append(
        uncertain_two_time
    )


    uncertain_two_pit_plans.append(
        actual_two_pits
    )


# =============================================================
# MONTE CARLO STATISTICS
# =============================================================

fixed_one_mean = statistics.mean(
    fixed_one_times
)


uncertain_one_mean = statistics.mean(
    uncertain_one_times
)


fixed_two_mean = statistics.mean(
    fixed_two_times
)


uncertain_two_mean = statistics.mean(
    uncertain_two_times
)


one_stop_benefits = []

two_stop_benefits = []


strategy_gaps = []


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


    strategy_gaps.append(
        strategy_gap
    )


    if strategy_gap < 0:

        two_stop_wins += 1


    elif strategy_gap > 0:

        one_stop_wins += 1


    else:

        ties += 1


average_one_benefit = statistics.mean(
    one_stop_benefits
)


average_two_benefit = statistics.mean(
    two_stop_benefits
)


average_strategy_gap = statistics.mean(
    strategy_gaps
)


# =============================================================
# EXPLICIT RIVAL SIMULATION
# =============================================================

(
    rival_total_time,
    rival_lap_times,
    rival_cumulative_times

) = simulate_fixed_strategy(

    rival_tyre_sequence,

    rival_pit_laps,

    pace_offset=rival_pace_offset,

    return_trace=True
)


# =============================================================
# TEST UNDERCUT / OVERCUT PIT LAPS
# =============================================================

rival_pit_lap = (
    rival_pit_laps[0]
)


battle_start_lap = max(
    minimum_stint,
    rival_pit_lap - battle_window
)


battle_end_lap = min(
    race_laps - minimum_stint,
    rival_pit_lap + battle_window
)


battle_results = []


for candidate_pit in range(
    battle_start_lap,
    battle_end_lap + 1
):


    result = analyse_pit_battle(
        candidate_pit,
        rival_cumulative_times
    )


    battle_results.append(
        result
    )


# =============================================================
# FIND BEST TACTICAL PIT
# =============================================================

best_battle_result = min(
    battle_results,
    key=lambda result:
        result["final_gap"]
)


best_battle_pit = (
    best_battle_result[
        "pit_lap"
    ]
)


best_battle_track_gaps = (
    best_battle_result[
        "track_gaps"
    ]
)


best_battle_lap_times = (
    best_battle_result[
        "lap_times"
    ]
)


# =============================================================
# PRINT SETTINGS
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

print(
    "Tyre model:"
)

print(
    "Non-linear degradation + "
    "warm-up + cliff"
)

print()

print(
    "Fuel-dependent tyre wear: enabled"
)

print(
    "Random Safety Cars: enabled"
)

print(
    "Safety Car decision uncertainty: enabled"
)

print(
    "Explicit rival model: enabled"
)

print()

print("----------------------------------")


# =============================================================
# PRINT BASELINE ONE-STOP SEARCH
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


    result = one_stop_results[
        strategy_name
    ]


    pit_lap = result[0]

    race_time = result[1]


    print(strategy_name)

    print(
        "Best pit lap:",
        pit_lap
    )

    print(
        "Stint lengths:",
        pit_lap,
        "+",
        race_laps - pit_lap
    )

    print(
        f"Race time: "
        f"{race_time:.1f} seconds"
    )

    print()


# =============================================================
# PRINT BASELINE WINNERS
# =============================================================

print("----------------------------------")

print()

print("BEST BASELINE ONE-STOP")

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
    race_laps - best_one_stop_pit
)

print(
    f"Race time: "
    f"{best_one_stop_time:.1f} seconds"
)

print()


print("BEST BASELINE TWO-STOP")

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
# PRINT MONTE CARLO
# =============================================================

print()

print("----------------------------------")

print()

print("MONTE CARLO SAFETY CAR ANALYSIS")

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
# PRINT RIVAL SETTINGS
# =============================================================

print()

print("----------------------------------")

print()

print("EXPLICIT RIVAL BATTLE")

print()

print(
    "Our starting gap:",
    initial_gap_to_rival,
    "seconds behind"
)

print()

print(
    "Rival strategy:",
    rival_tyre_sequence[0],
    "->",
    rival_tyre_sequence[1]
)

print(
    "Rival pit lap:",
    rival_pit_lap
)

print(
    f"Rival race time: "
    f"{rival_total_time:.3f} seconds"
)

print()

print(
    "Candidate pit laps:",
    battle_start_lap,
    "to",
    battle_end_lap
)

print()


# =============================================================
# PRINT UNDERCUT / OVERCUT RESULTS
# =============================================================

for result in battle_results:


    print(
        "Our pit lap:",
        result["pit_lap"]
    )

    print(
        "Tactic:",
        result["tactic"]
    )

    print(
        "Outcome:",
        result["outcome"]
    )

    print(
        f"Gap before pit cycle: "
        f"{result['gap_before_cycle']:.3f} seconds"
    )

    print(
        f"Gap immediately after our stop: "
        f"{result['rejoin_gap']:.3f} seconds"
    )

    print(
        f"Gap after both cars stop: "
        f"{result['gap_after_cycle']:.3f} seconds"
    )

    print(
        f"Pit-cycle gain: "
        f"{result['pit_cycle_gain']:.3f} seconds"
    )

    print(
        f"Final gap: "
        f"{result['final_gap']:.3f} seconds"
    )

    print()


# =============================================================
# PRINT BEST RIVAL BATTLE STRATEGY
# =============================================================

print("----------------------------------")

print()

print("BEST PIT TIMING AGAINST RIVAL")

print()

print(
    "Pit lap:",
    best_battle_result[
        "pit_lap"
    ]
)

print(
    "Tactic:",
    best_battle_result[
        "tactic"
    ]
)

print(
    "Outcome:",
    best_battle_result[
        "outcome"
    ]
)

print()

print(
    f"Gap before pit cycle: "
    f"{best_battle_result['gap_before_cycle']:.3f} seconds"
)

print(
    f"Rejoin gap after our pit: "
    f"{best_battle_result['rejoin_gap']:.3f} seconds"
)

print(
    f"Gap after rival pit: "
    f"{best_battle_result['gap_after_cycle']:.3f} seconds"
)

print(
    f"Pit-cycle gain: "
    f"{best_battle_result['pit_cycle_gain']:.3f} seconds"
)

print(
    f"Final gap: "
    f"{best_battle_result['final_gap']:.3f} seconds"
)

print()


if (
    best_battle_result[
        "final_gap"
    ] < 0
):

    print(
        "Final position: "
        "Our car finishes ahead by",
        f"{abs(best_battle_result['final_gap']):.3f}",
        "seconds"
    )

else:

    print(
        "Final position: "
        "Our car finishes behind by",
        f"{best_battle_result['final_gap']:.3f}",
        "seconds"
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
                tyres[tyre_name],
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
    range(0, 10)
)


for tyre_name in tyres:


    penalties = []


    for tyre_age in warmup_ages:


        penalties.append(
            calculate_warmup_penalty(
                tyres[tyre_name],
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


    result = one_stop_results[
        strategy_name
    ]


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
# BASELINE ONE-STOP VS TWO-STOP
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
    baseline_gap
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
# MONTE CARLO SAFETY CAR BENEFIT
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
    strategy_gaps,
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
# OUR CAR VS RIVAL LAP TIMES
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    race_lap_numbers,
    best_battle_lap_times,
    label=(
        "Our Car - Pit "
        + str(best_battle_pit)
    )
)


plt.plot(
    race_lap_numbers,
    rival_lap_times,
    label=(
        rival_name
        + " - Pit "
        + str(rival_pit_lap)
    )
)


plt.axvline(
    best_battle_pit,
    linestyle="--",
    label="Our Pit"
)


plt.axvline(
    rival_pit_lap,
    linestyle="--",
    label="Rival Pit"
)


plt.xlabel(
    "Race Lap"
)

plt.ylabel(
    "Lap Time (seconds)"
)

plt.title(
    "Our Car vs Rival Lap Times"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 10
# TRACK GAP TO RIVAL
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    race_lap_numbers,
    best_battle_track_gaps,
    label="Gap to Rival"
)


plt.axhline(
    0,
    linestyle="--",
    label="Same Track Position"
)


plt.axvline(
    best_battle_pit,
    linestyle="--",
    label="Our Pit"
)


plt.axvline(
    rival_pit_lap,
    linestyle="--",
    label="Rival Pit"
)


plt.xlabel(
    "Race Lap"
)

plt.ylabel(
    "Gap to Rival (seconds)"
)

plt.title(
    "Explicit Rival Battle"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 11
# PIT-CYCLE GAP VS PIT LAP
# =============================================================

battle_pit_laps = []

battle_post_cycle_gaps = []


for result in battle_results:


    battle_pit_laps.append(
        result[
            "pit_lap"
        ]
    )


    battle_post_cycle_gaps.append(
        result[
            "gap_after_cycle"
        ]
    )


plt.figure(
    figsize=(10, 6)
)


plt.plot(
    battle_pit_laps,
    battle_post_cycle_gaps,
    marker="o"
)


plt.axhline(
    0,
    linestyle="--",
    label="Same Track Position"
)


plt.axvline(
    rival_pit_lap,
    linestyle="--",
    label="Rival Pit Lap"
)


plt.xlabel(
    "Our Pit Lap"
)

plt.ylabel(
    "Gap After Both Pit Stops (seconds)"
)

plt.title(
    "Undercut / Overcut Pit-Cycle Result"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 12
# FINAL RACE GAP VS PIT LAP
# =============================================================

battle_final_gaps = []


for result in battle_results:


    battle_final_gaps.append(
        result[
            "final_gap"
        ]
    )


plt.figure(
    figsize=(10, 6)
)


plt.plot(
    battle_pit_laps,
    battle_final_gaps,
    marker="o"
)


plt.axhline(
    0,
    linestyle="--",
    label="Equal Finish Time"
)


plt.axvline(
    rival_pit_lap,
    linestyle="--",
    label="Rival Pit Lap"
)


plt.axvline(
    best_battle_pit,
    linestyle="--",
    label="Best Tactical Pit"
)


plt.xlabel(
    "Our Pit Lap"
)

plt.ylabel(
    "Final Gap to Rival (seconds)"
)

plt.title(
    "Final Rival Gap vs Pit Timing"
)

plt.legend()

plt.tight_layout()

plt.show()