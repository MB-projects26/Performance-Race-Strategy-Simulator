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
        - fuel_burn_per_lap * (lap - 1)
    )

    if fuel_mass < 0:

        fuel_mass = 0.0

    return fuel_mass


# =============================================================
# FUNCTION: FUEL LAP-TIME GAIN
# =============================================================

def calculate_fuel_time_gain(lap):

    current_fuel = calculate_fuel_mass(lap)

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

    current_fuel = calculate_fuel_mass(lap)

    fuel_fraction = (
        current_fuel
        / initial_fuel_mass
    )

    wear_increment = (
        1.0
        + fuel_wear_sensitivity * fuel_fraction
    )


    # Less tyre wear during Safety Car

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
        + quadratic_deg * (tyre_wear ** 2)
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
        - recovery_rate * tyre_age
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
        safety_car_end):


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
    # Normal racing lap
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
    )


    return lap_time


# =============================================================
# FUNCTION: CHECK PIT PLAN IS LEGAL
# =============================================================

def pit_plan_is_legal(
        pit_laps):


    # Pit laps must be in increasing order

    for i in range(
        len(pit_laps) - 1
    ):

        if pit_laps[i] >= pit_laps[i + 1]:

            return False


    # -----------------------------
    # Calculate stint lengths
    # -----------------------------

    if len(pit_laps) == 0:

        stint_lengths = [
            race_laps
        ]


    else:

        stint_lengths = [
            pit_laps[0]
        ]


        for i in range(
            1,
            len(pit_laps)
        ):

            stint_length = (
                pit_laps[i]
                - pit_laps[i - 1]
            )

            stint_lengths.append(
                stint_length
            )


        final_stint = (
            race_laps
            - pit_laps[-1]
        )


        stint_lengths.append(
            final_stint
        )


    # -----------------------------
    # Check minimum stint
    # -----------------------------

    for stint_length in stint_lengths:

        if stint_length < minimum_stint:

            return False


    return True


# =============================================================
# FUNCTION: SIMULATE FIXED STRATEGY
# =============================================================
#
# This function follows the supplied pit plan exactly.
#
# It is used for:
#
# - baseline optimisation
# - fixed Monte Carlo strategy
# - Safety Car look-ahead calculations
#
# =============================================================

def simulate_fixed_strategy(
        tyre_sequence,
        pit_laps,
        safety_car_start=None,
        safety_car_end=None,
        return_trace=False):


    # Strategy must have one fewer pit stop
    # than tyre stints

    if len(pit_laps) != len(tyre_sequence) - 1:

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


    # -----------------------------
    # Race simulation
    # -----------------------------

    for lap in range(
        1,
        race_laps + 1
    ):


        current_tyre_name = (
            tyre_sequence[stint_number]
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
            safety_car_end
        )


        total_time = (
            total_time
            + lap_time
        )


        tyre_age = (
            tyre_age
            + 1
        )


        tyre_wear = (
            tyre_wear
            + calculate_fuel_wear_increment(
                lap,
                safety_car_start,
                safety_car_end
            )
        )


        # -----------------------------
        # Planned pit stop
        # -----------------------------

        if (
            pit_number < len(pit_laps)
            and lap == pit_laps[pit_number]
        ):


            total_time = (
                total_time
                + calculate_pit_loss(
                    lap,
                    safety_car_start,
                    safety_car_end
                )
            )


            tyre_age = 0

            tyre_wear = 0.0


            stint_number = (
                stint_number
                + 1
            )


            pit_number = (
                pit_number
                + 1
            )


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
# FUNCTION: LOOK-AHEAD SAFETY CAR STRATEGY
# =============================================================
#
# When a Safety Car occurs before a planned stop:
#
# OPTION A:
# stay out and follow the original plan
#
# OPTION B:
# pit now and bring that stop forward
#
# The simulator calculates the predicted total
# race time for both options.
#
# It chooses whichever option is faster.
#
# =============================================================

def simulate_lookahead_strategy(
        tyre_sequence,
        planned_pit_laps,
        safety_car_start=None,
        safety_car_end=None,
        return_trace=False):


    total_time = 0.0

    tyre_age = 0

    tyre_wear = 0.0


    stint_number = 0

    pit_number = 0


    actual_pit_laps = []


    decision_log = []


    lap_times = []

    cumulative_times = []


    for lap in range(
        1,
        race_laps + 1
    ):


        # -----------------------------
        # Current tyre
        # -----------------------------

        current_tyre_name = (
            tyre_sequence[stint_number]
        )


        current_tyre = tyres[
            current_tyre_name
        ]


        # -----------------------------
        # Calculate current lap
        # -----------------------------

        lap_time = calculate_lap_time(
            current_tyre,
            tyre_age,
            tyre_wear,
            lap,
            safety_car_start,
            safety_car_end
        )


        total_time = (
            total_time
            + lap_time
        )


        tyre_age = (
            tyre_age
            + 1
        )


        tyre_wear = (
            tyre_wear
            + calculate_fuel_wear_increment(
                lap,
                safety_car_start,
                safety_car_end
            )
        )


        # -----------------------------
        # Pit decision
        # -----------------------------

        should_pit = False


        if pit_number < len(
            planned_pit_laps
        ):


            planned_pit = (
                planned_pit_laps[
                    pit_number
                ]
            )


            # -----------------------------
            # Planned stop reached
            # -----------------------------

            if lap == planned_pit:

                should_pit = True


            # -----------------------------
            # Safety Car opportunity
            # -----------------------------

            elif (
                is_safety_car_lap(
                    lap,
                    safety_car_start,
                    safety_car_end
                )
                and lap < planned_pit
            ):


                # ---------------------------------
                # Option A: Stay out
                # ---------------------------------

                stay_out_plan = (
                    actual_pit_laps
                    + planned_pit_laps[
                        pit_number:
                    ]
                )


                # ---------------------------------
                # Option B: Pit now
                # ---------------------------------

                pit_now_plan = (
                    actual_pit_laps
                    + [lap]
                    + planned_pit_laps[
                        pit_number + 1:
                    ]
                )


                # Only test legal pit plans

                if pit_plan_is_legal(
                    pit_now_plan
                ):


                    stay_out_time = (
                        simulate_fixed_strategy(
                            tyre_sequence,
                            stay_out_plan,
                            safety_car_start,
                            safety_car_end
                        )
                    )


                    pit_now_time = (
                        simulate_fixed_strategy(
                            tyre_sequence,
                            pit_now_plan,
                            safety_car_start,
                            safety_car_end
                        )
                    )


                    # ---------------------------------
                    # Choose faster option
                    # ---------------------------------

                    if (
                        pit_now_time
                        < stay_out_time
                    ):


                        should_pit = True


                        decision = (
                            lap,
                            planned_pit,
                            stay_out_time,
                            pit_now_time,
                            "PIT"
                        )


                    else:


                        decision = (
                            lap,
                            planned_pit,
                            stay_out_time,
                            pit_now_time,
                            "STAY OUT"
                        )


                    decision_log.append(
                        decision
                    )


        # -----------------------------
        # Make pit stop
        # -----------------------------

        if should_pit:


            total_time = (
                total_time
                + calculate_pit_loss(
                    lap,
                    safety_car_start,
                    safety_car_end
                )
            )


            actual_pit_laps.append(
                lap
            )


            tyre_age = 0

            tyre_wear = 0.0


            stint_number = (
                stint_number
                + 1
            )


            pit_number = (
                pit_number
                + 1
            )


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
            actual_pit_laps,
            decision_log,
            lap_times,
            cumulative_times
        )


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
        race_laps - minimum_stint + 1
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
        race_laps - (2 * minimum_stint) + 1
    ):


        for pit_lap_2 in range(
            pit_lap_1 + minimum_stint,
            race_laps - minimum_stint + 1
        ):


            race_time = simulate_fixed_strategy(
                tyre_sequence,
                [
                    pit_lap_1,
                    pit_lap_2
                ]
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


            if first_tyre == second_tyre:

                continue


            legal_combinations += 1


            result = calculate_one_stop_strategy(
                first_tyre,
                second_tyre
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


                if (
                    first_tyre
                    == second_tyre
                    == third_tyre
                ):

                    continue


                legal_combinations += 1


                result = calculate_two_stop_strategy(
                    first_tyre,
                    second_tyre,
                    third_tyre
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
# FUNCTION: GENERATE SAFETY CAR SCENARIOS
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
# BASELINE TRACES
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
# MONTE CARLO SCENARIOS
# =============================================================

scenarios = generate_safety_car_scenarios(
    monte_carlo_runs
)


safety_car_count = 0


for scenario in scenarios:

    if scenario[0] is not None:

        safety_car_count += 1


# =============================================================
# MONTE CARLO RESULTS
# =============================================================

fixed_one_times = []

lookahead_one_times = []


fixed_two_times = []

lookahead_two_times = []


lookahead_one_actual_pits = []

lookahead_two_actual_pits = []


one_stop_decision_logs = []

two_stop_decision_logs = []


# =============================================================
# RUN MONTE CARLO
# =============================================================

for scenario in scenarios:


    safety_car_start = scenario[0]

    safety_car_end = scenario[1]


    # -----------------------------
    # Fixed one-stop
    # -----------------------------

    fixed_one_time = simulate_fixed_strategy(
        list(best_one_stop_strategy),
        best_one_stop_pits,
        safety_car_start,
        safety_car_end
    )


    fixed_one_times.append(
        fixed_one_time
    )


    # -----------------------------
    # Look-ahead one-stop
    # -----------------------------

    (
        lookahead_one_time,
        actual_one_pits,
        one_decisions

    ) = simulate_lookahead_strategy(

        list(best_one_stop_strategy),
        best_one_stop_pits,
        safety_car_start,
        safety_car_end
    )


    lookahead_one_times.append(
        lookahead_one_time
    )


    lookahead_one_actual_pits.append(
        actual_one_pits
    )


    one_stop_decision_logs.append(
        one_decisions
    )


    # -----------------------------
    # Fixed two-stop
    # -----------------------------

    fixed_two_time = simulate_fixed_strategy(
        list(best_two_stop_strategy),
        best_two_stop_pits,
        safety_car_start,
        safety_car_end
    )


    fixed_two_times.append(
        fixed_two_time
    )


    # -----------------------------
    # Look-ahead two-stop
    # -----------------------------

    (
        lookahead_two_time,
        actual_two_pits,
        two_decisions

    ) = simulate_lookahead_strategy(

        list(best_two_stop_strategy),
        best_two_stop_pits,
        safety_car_start,
        safety_car_end
    )


    lookahead_two_times.append(
        lookahead_two_time
    )


    lookahead_two_actual_pits.append(
        actual_two_pits
    )


    two_stop_decision_logs.append(
        two_decisions
    )


# =============================================================
# MEAN AND STANDARD DEVIATION
# =============================================================

fixed_one_mean = statistics.mean(
    fixed_one_times
)


lookahead_one_mean = statistics.mean(
    lookahead_one_times
)


fixed_two_mean = statistics.mean(
    fixed_two_times
)


lookahead_two_mean = statistics.mean(
    lookahead_two_times
)


fixed_one_std = statistics.stdev(
    fixed_one_times
)


lookahead_one_std = statistics.stdev(
    lookahead_one_times
)


fixed_two_std = statistics.stdev(
    fixed_two_times
)


lookahead_two_std = statistics.stdev(
    lookahead_two_times
)


# =============================================================
# CALCULATE BENEFIT OF LOOK-AHEAD
# =============================================================

one_stop_benefits = []

two_stop_benefits = []


for i in range(
    monte_carlo_runs
):


    one_benefit = (
        fixed_one_times[i]
        - lookahead_one_times[i]
    )


    two_benefit = (
        fixed_two_times[i]
        - lookahead_two_times[i]
    )


    one_stop_benefits.append(
        one_benefit
    )


    two_stop_benefits.append(
        two_benefit
    )


average_one_benefit = statistics.mean(
    one_stop_benefits
)


average_two_benefit = statistics.mean(
    two_stop_benefits
)


# =============================================================
# COUNT CHANGED PIT PLANS
# =============================================================

one_stop_plan_changes = 0

two_stop_plan_changes = 0


for pit_plan in lookahead_one_actual_pits:

    if pit_plan != best_one_stop_pits:

        one_stop_plan_changes += 1


for pit_plan in lookahead_two_actual_pits:

    if pit_plan != best_two_stop_pits:

        two_stop_plan_changes += 1


# =============================================================
# LOOK-AHEAD ONE VS TWO STOP
# =============================================================

lookahead_strategy_gaps = []


one_stop_wins = 0

two_stop_wins = 0

ties = 0


for i in range(
    monte_carlo_runs
):


    gap = (
        lookahead_two_times[i]
        - lookahead_one_times[i]
    )


    lookahead_strategy_gaps.append(
        gap
    )


    if gap < 0:

        two_stop_wins += 1


    elif gap > 0:

        one_stop_wins += 1


    else:

        ties += 1


average_strategy_gap = statistics.mean(
    lookahead_strategy_gaps
)


# =============================================================
# FIND ONE EXAMPLE OF A SAFETY CAR DECISION
# =============================================================

example_decision = None


for i in range(
    monte_carlo_runs
):


    if len(
        one_stop_decision_logs[i]
    ) > 0:


        example_decision = (
            i,
            scenarios[i],
            one_stop_decision_logs[i],
            lookahead_one_actual_pits[i]
        )


        break


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

print("SAFETY CAR")

print()

print(
    "Probability:",
    safety_car_probability
)

print(
    "Safety Car pit loss:",
    safety_car_pit_loss,
    "seconds"
)

print(
    "Safety Car lap time:",
    safety_car_lap_time,
    "seconds"
)

print()

print(
    "Safety Car decision method:"
)

print(
    "Look-ahead optimisation"
)

print()

print("----------------------------------")


# =============================================================
# PRINT BASELINE RESULTS
# =============================================================

print()

print("BASELINE STRATEGIES")

print()

print("ONE-STOP")

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


print("TWO-STOP")

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

print()

print("----------------------------------")


# =============================================================
# PRINT MONTE CARLO RESULTS
# =============================================================

print()

print("MONTE CARLO RESULTS")

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
    f"{fixed_one_mean:.1f} seconds"
)

print(
    f"Look-ahead mean: "
    f"{lookahead_one_mean:.1f} seconds"
)

print(
    f"Fixed standard deviation: "
    f"{fixed_one_std:.1f} seconds"
)

print(
    f"Look-ahead standard deviation: "
    f"{lookahead_one_std:.1f} seconds"
)

print(
    f"Average benefit of look-ahead: "
    f"{average_one_benefit:.3f} seconds"
)

print(
    "Changed pit plans:",
    one_stop_plan_changes
)

print()

print("TWO-STOP")

print()

print(
    f"Fixed mean: "
    f"{fixed_two_mean:.1f} seconds"
)

print(
    f"Look-ahead mean: "
    f"{lookahead_two_mean:.1f} seconds"
)

print(
    f"Fixed standard deviation: "
    f"{fixed_two_std:.1f} seconds"
)

print(
    f"Look-ahead standard deviation: "
    f"{lookahead_two_std:.1f} seconds"
)

print(
    f"Average benefit of look-ahead: "
    f"{average_two_benefit:.3f} seconds"
)

print(
    "Changed pit plans:",
    two_stop_plan_changes
)

print()

print("----------------------------------")


# =============================================================
# PRINT FINAL STRATEGY COMPARISON
# =============================================================

print()

print(
    "LOOK-AHEAD STRATEGY COMPARISON"
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

print()

print(
    f"Average two-stop minus one-stop gap: "
    f"{average_strategy_gap:.1f} seconds"
)

print()


if average_strategy_gap < 0:

    print(
        "Two-stop is faster on average by:",
        f"{abs(average_strategy_gap):.1f} seconds"
    )

else:

    print(
        "One-stop is faster on average by:",
        f"{average_strategy_gap:.1f} seconds"
    )


# =============================================================
# PRINT EXAMPLE DECISION
# =============================================================

if example_decision is not None:


    simulation_number = (
        example_decision[0]
    )


    scenario = (
        example_decision[1]
    )


    decisions = (
        example_decision[2]
    )


    actual_pits = (
        example_decision[3]
    )


    print()

    print("----------------------------------")

    print()

    print(
        "EXAMPLE SAFETY CAR DECISION"
    )

    print()

    print(
        "Simulation:",
        simulation_number + 1
    )

    print(
        "Safety Car:",
        scenario[0],
        "to",
        scenario[1]
    )

    print(
        "Original one-stop pit:",
        best_one_stop_pit
    )

    print(
        "Actual pit plan:",
        actual_pits
    )

    print()


    for decision in decisions:


        print(
            "Decision lap:",
            decision[0]
        )

        print(
            "Original planned pit:",
            decision[1]
        )

        print(
            f"Stay-out predicted time: "
            f"{decision[2]:.1f}"
        )

        print(
            f"Pit-now predicted time: "
            f"{decision[3]:.1f}"
        )

        print(
            "Decision:",
            decision[4]
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


    tyre_data = tyres[
        tyre_name
    ]


    tyre_losses = []


    for tyre_wear in wear_values:


        tyre_losses.append(
            calculate_tyre_loss(
                tyre_data,
                tyre_wear
            )
        )


    plt.plot(
        wear_values,
        tyre_losses,
        label=tyre_name
    )


plt.xlabel(
    "Effective Tyre Wear"
)

plt.ylabel(
    "Lap-Time Loss (seconds)"
)

plt.title(
    "Tyre Degradation with Cliff"
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
# FUEL EFFECT ON TYRE WEAR
# =============================================================

plt.figure(
    figsize=(10, 6)
)


wear_increments = []


for lap in race_lap_numbers:


    wear_increments.append(
        calculate_fuel_wear_increment(
            lap,
            None,
            None
        )
    )


plt.plot(
    race_lap_numbers,
    wear_increments
)


plt.xlabel(
    "Race Lap"
)

plt.ylabel(
    "Equivalent Tyre Wear per Lap"
)

plt.title(
    "Fuel Load Effect on Tyre Wear"
)

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 5
# ONE-STOP OPTIMISATION
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
    "Baseline One-Stop Optimisation"
)

plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 6
# BASELINE LAP TIMES
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
    "Baseline Strategy Lap Times"
)

plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 7
# BASELINE TIME GAP
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
# GRAPH 8
# FIXED VS LOOK-AHEAD ONE-STOP
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.hist(
    fixed_one_times,
    bins=25,
    alpha=0.6,
    label="Fixed One-Stop"
)


plt.hist(
    lookahead_one_times,
    bins=25,
    alpha=0.6,
    label="Look-Ahead One-Stop"
)


plt.xlabel(
    "Race Time (seconds)"
)

plt.ylabel(
    "Simulated Races"
)

plt.title(
    "One-Stop Safety Car Strategy"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 9
# FIXED VS LOOK-AHEAD TWO-STOP
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.hist(
    fixed_two_times,
    bins=25,
    alpha=0.6,
    label="Fixed Two-Stop"
)


plt.hist(
    lookahead_two_times,
    bins=25,
    alpha=0.6,
    label="Look-Ahead Two-Stop"
)


plt.xlabel(
    "Race Time (seconds)"
)

plt.ylabel(
    "Simulated Races"
)

plt.title(
    "Two-Stop Safety Car Strategy"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 10
# BENEFIT OF LOOK-AHEAD
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
    "Fixed Time minus Look-Ahead Time (seconds)"
)

plt.ylabel(
    "Simulated Races"
)

plt.title(
    "Benefit of Safety Car Look-Ahead"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 11
# ONE-STOP VS TWO-STOP UNDER LOOK-AHEAD
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.hist(
    lookahead_strategy_gaps,
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
    "Look-Ahead Strategy Comparison"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 12
# SAFETY CAR START DISTRIBUTION
# =============================================================

safety_car_start_laps = []


for scenario in scenarios:


    if scenario[0] is not None:


        safety_car_start_laps.append(
            scenario[0]
        )


plt.figure(
    figsize=(10, 6)
)


plt.hist(
    safety_car_start_laps,
    bins=20
)


plt.xlabel(
    "Safety Car Start Lap"
)

plt.ylabel(
    "Number of Safety Cars"
)

plt.title(
    "Random Safety Car Start Distribution"
)

plt.tight_layout()

plt.show()