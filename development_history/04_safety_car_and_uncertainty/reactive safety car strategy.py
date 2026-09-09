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
# REACTIVE STRATEGY SETTINGS
# =============================================================
#
# If a Safety Car appears this many laps or fewer
# before the next planned stop, the driver may pit early.
#
# Example:
#
# Planned stop = lap 29
# reaction_window = 6
#
# Safety Car lap 24:
# 29 - 24 = 5
#
# Therefore the strategy may react and pit on lap 24.
#
# =============================================================

reaction_window = 6


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

    # Reduced tyre wear behind Safety Car

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


    tyre_loss = (
        normal_loss
        + cliff_loss
    )


    return tyre_loss


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


    # Safety Car lap

    if is_safety_car_lap(
        lap,
        safety_car_start,
        safety_car_end
    ):

        return safety_car_lap_time


    # Normal racing lap

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
# FUNCTION: SIMULATE STRATEGY
# =============================================================
#
# reactive=False
#
# Driver follows planned pit laps exactly.
#
#
# reactive=True
#
# Driver may bring the next pit stop forward
# if a Safety Car appears close to the planned stop.
#
# =============================================================

def simulate_strategy(
        tyre_sequence,
        planned_pit_laps,
        safety_car_start=None,
        safety_car_end=None,
        reactive=False,
        return_trace=False):


    total_time = 0.0

    tyre_age = 0

    tyre_wear = 0.0


    stint_number = 0

    pit_number = 0

    last_pit_lap = 0


    actual_pit_laps = []


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
        # Lap time
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


        # -----------------------------
        # Tyre age
        # -----------------------------

        tyre_age = (
            tyre_age
            + 1
        )


        # -----------------------------
        # Tyre wear
        # -----------------------------

        tyre_wear = (
            tyre_wear
            + calculate_fuel_wear_increment(
                lap,
                safety_car_start,
                safety_car_end
            )
        )


        # -----------------------------
        # Decide whether to pit
        # -----------------------------

        should_pit = False


        if pit_number < len(
            planned_pit_laps
        ):


            planned_pit = (
                planned_pit_laps[pit_number]
            )


            # Normal planned stop

            if lap == planned_pit:

                should_pit = True


            # -----------------------------
            # Reactive Safety Car stop
            # -----------------------------

            elif reactive:

                if is_safety_car_lap(
                    lap,
                    safety_car_start,
                    safety_car_end
                ):


                    # Only react BEFORE
                    # the planned stop

                    if lap < planned_pit:


                        laps_early = (
                            planned_pit
                            - lap
                        )


                        # Current stint length

                        current_stint_length = (
                            lap
                            - last_pit_lap
                        )


                        # Number of stints that
                        # still need to happen
                        # after this pit

                        remaining_stints = (
                            len(planned_pit_laps)
                            - pit_number
                        )


                        remaining_race_laps = (
                            race_laps
                            - lap
                        )


                        # Safety Car is close enough

                        if (
                            laps_early
                            <= reaction_window
                        ):


                            # Current stint must be legal

                            if (
                                current_stint_length
                                >= minimum_stint
                            ):


                                # Enough laps must remain
                                # for all future stints

                                if (
                                    remaining_race_laps
                                    >= (
                                        remaining_stints
                                        * minimum_stint
                                    )
                                ):

                                    should_pit = True


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


            last_pit_lap = lap


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
            lap_times,
            cumulative_times
        )


    return (
        total_time,
        actual_pit_laps
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


        race_time, actual_pits = (
            simulate_strategy(
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


            race_time, actual_pits = (
                simulate_strategy(
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


            # Must use two different compounds

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


                # Must use at least
                # two different compounds

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
# FUNCTION: GENERATE RANDOM SAFETY CARS
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
# FUNCTION: RUN MONTE CARLO
# =============================================================

def run_monte_carlo(
        tyre_sequence,
        planned_pit_laps,
        scenarios,
        reactive):


    race_times = []

    actual_pit_results = []

    strategy_changes = 0


    for scenario in scenarios:


        safety_car_start = scenario[0]

        safety_car_end = scenario[1]


        race_time, actual_pits = (
            simulate_strategy(
                tyre_sequence,
                planned_pit_laps,
                safety_car_start,
                safety_car_end,
                reactive=reactive
            )
        )


        race_times.append(
            race_time
        )


        actual_pit_results.append(
            actual_pits
        )


        if actual_pits != planned_pit_laps:

            strategy_changes += 1


    return (
        race_times,
        actual_pit_results,
        strategy_changes
    )


# =============================================================
# BASELINE OPTIMISATION
# =============================================================
#
# This is the pre-race strategy.
#
# No Safety Car is assumed when determining the
# original planned pit laps.
#
# =============================================================

one_stop_search = find_best_one_stop()


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


two_stop_search = find_best_two_stop()


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


best_one_stop_pits = [
    best_one_stop_pit
]


best_two_stop_pits = [
    best_two_stop_pit_1,
    best_two_stop_pit_2
]


# =============================================================
# BASELINE TRACES
# =============================================================

(
    baseline_one_total,
    baseline_one_pits,
    best_one_stop_lap_times,
    one_stop_cumulative_times

) = simulate_strategy(
    list(best_one_stop_strategy),
    best_one_stop_pits,
    return_trace=True
)


(
    baseline_two_total,
    baseline_two_pits,
    best_two_stop_lap_times,
    two_stop_cumulative_times

) = simulate_strategy(
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


baseline_time_gap = []


for i in range(
    race_laps
):


    gap = (
        two_stop_cumulative_times[i]
        - one_stop_cumulative_times[i]
    )


    baseline_time_gap.append(
        gap
    )


# =============================================================
# GENERATE MONTE CARLO SCENARIOS
# =============================================================

safety_car_scenarios = (
    generate_safety_car_scenarios(
        monte_carlo_runs
    )
)


safety_car_count = 0


for scenario in safety_car_scenarios:

    if scenario[0] is not None:

        safety_car_count += 1


# =============================================================
# FIXED ONE-STOP MONTE CARLO
# =============================================================

(
    fixed_one_times,
    fixed_one_pits,
    fixed_one_changes

) = run_monte_carlo(
    list(best_one_stop_strategy),
    best_one_stop_pits,
    safety_car_scenarios,
    reactive=False
)


# =============================================================
# REACTIVE ONE-STOP MONTE CARLO
# =============================================================

(
    reactive_one_times,
    reactive_one_pits,
    reactive_one_changes

) = run_monte_carlo(
    list(best_one_stop_strategy),
    best_one_stop_pits,
    safety_car_scenarios,
    reactive=True
)


# =============================================================
# FIXED TWO-STOP MONTE CARLO
# =============================================================

(
    fixed_two_times,
    fixed_two_pits,
    fixed_two_changes

) = run_monte_carlo(
    list(best_two_stop_strategy),
    best_two_stop_pits,
    safety_car_scenarios,
    reactive=False
)


# =============================================================
# REACTIVE TWO-STOP MONTE CARLO
# =============================================================

(
    reactive_two_times,
    reactive_two_pits,
    reactive_two_changes

) = run_monte_carlo(
    list(best_two_stop_strategy),
    best_two_stop_pits,
    safety_car_scenarios,
    reactive=True
)


# =============================================================
# CALCULATE MONTE CARLO STATISTICS
# =============================================================

fixed_one_mean = statistics.mean(
    fixed_one_times
)

reactive_one_mean = statistics.mean(
    reactive_one_times
)

fixed_two_mean = statistics.mean(
    fixed_two_times
)

reactive_two_mean = statistics.mean(
    reactive_two_times
)


fixed_one_std = statistics.stdev(
    fixed_one_times
)

reactive_one_std = statistics.stdev(
    reactive_one_times
)

fixed_two_std = statistics.stdev(
    fixed_two_times
)

reactive_two_std = statistics.stdev(
    reactive_two_times
)


# =============================================================
# REACTIVE BENEFIT
# =============================================================
#
# Positive:
# reactive strategy was faster
#
# Negative:
# reacting made the strategy worse
#
# =============================================================

one_stop_reaction_benefit = []

two_stop_reaction_benefit = []


for i in range(
    monte_carlo_runs
):


    one_stop_benefit = (
        fixed_one_times[i]
        - reactive_one_times[i]
    )


    two_stop_benefit = (
        fixed_two_times[i]
        - reactive_two_times[i]
    )


    one_stop_reaction_benefit.append(
        one_stop_benefit
    )


    two_stop_reaction_benefit.append(
        two_stop_benefit
    )


average_one_reaction_benefit = (
    statistics.mean(
        one_stop_reaction_benefit
    )
)


average_two_reaction_benefit = (
    statistics.mean(
        two_stop_reaction_benefit
    )
)


# =============================================================
# FIXED STRATEGY COMPARISON
# =============================================================

fixed_strategy_gaps = []

fixed_one_wins = 0

fixed_two_wins = 0


for i in range(
    monte_carlo_runs
):


    gap = (
        fixed_two_times[i]
        - fixed_one_times[i]
    )


    fixed_strategy_gaps.append(
        gap
    )


    if gap < 0:

        fixed_two_wins += 1

    elif gap > 0:

        fixed_one_wins += 1


average_fixed_gap = statistics.mean(
    fixed_strategy_gaps
)


# =============================================================
# REACTIVE STRATEGY COMPARISON
# =============================================================

reactive_strategy_gaps = []

reactive_one_wins = 0

reactive_two_wins = 0


for i in range(
    monte_carlo_runs
):


    gap = (
        reactive_two_times[i]
        - reactive_one_times[i]
    )


    reactive_strategy_gaps.append(
        gap
    )


    if gap < 0:

        reactive_two_wins += 1

    elif gap > 0:

        reactive_one_wins += 1


average_reactive_gap = statistics.mean(
    reactive_strategy_gaps
)


# =============================================================
# PRINT MODEL SETTINGS
# =============================================================

print("MODEL SETTINGS")

print()

print("Race laps:", race_laps)

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

print("SAFETY CAR SETTINGS")

print()

print(
    "Safety Car probability:",
    safety_car_probability
)

print(
    "Start range:",
    safety_car_min_start,
    "to",
    safety_car_max_start
)

print(
    "Duration:",
    safety_car_min_duration,
    "to",
    safety_car_max_duration,
    "laps"
)

print(
    "Safety Car pit loss:",
    safety_car_pit_loss,
    "seconds"
)

print(
    "Reactive pit window:",
    reaction_window,
    "laps"
)

print()

print("----------------------------------")


# =============================================================
# PRINT BASELINE STRATEGIES
# =============================================================

print()

print("BASELINE STRATEGIES")

print()

print("Best one-stop:")

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

print("Best two-stop:")

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

print("----------------------------------")


# =============================================================
# PRINT MONTE CARLO SETTINGS
# =============================================================

print()

print("MONTE CARLO")

print()

print(
    "Simulations:",
    monte_carlo_runs
)

print(
    "Random seed:",
    random_seed
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

print("----------------------------------")


# =============================================================
# PRINT ONE-STOP REACTION RESULTS
# =============================================================

print()

print("ONE-STOP SAFETY CAR RESPONSE")

print()

print(
    "Planned pit:",
    best_one_stop_pit
)

print(
    "Races where pit plan changed:",
    reactive_one_changes
)

print()

print(
    f"Fixed mean race time: "
    f"{fixed_one_mean:.1f} seconds"
)

print(
    f"Reactive mean race time: "
    f"{reactive_one_mean:.1f} seconds"
)

print(
    f"Fixed standard deviation: "
    f"{fixed_one_std:.1f} seconds"
)

print(
    f"Reactive standard deviation: "
    f"{reactive_one_std:.1f} seconds"
)

print(
    f"Average benefit from reacting: "
    f"{average_one_reaction_benefit:.2f} seconds"
)

print()

print("----------------------------------")


# =============================================================
# PRINT TWO-STOP REACTION RESULTS
# =============================================================

print()

print("TWO-STOP SAFETY CAR RESPONSE")

print()

print(
    "Planned pits:",
    best_two_stop_pit_1,
    "and",
    best_two_stop_pit_2
)

print(
    "Races where pit plan changed:",
    reactive_two_changes
)

print()

print(
    f"Fixed mean race time: "
    f"{fixed_two_mean:.1f} seconds"
)

print(
    f"Reactive mean race time: "
    f"{reactive_two_mean:.1f} seconds"
)

print(
    f"Fixed standard deviation: "
    f"{fixed_two_std:.1f} seconds"
)

print(
    f"Reactive standard deviation: "
    f"{reactive_two_std:.1f} seconds"
)

print(
    f"Average benefit from reacting: "
    f"{average_two_reaction_benefit:.2f} seconds"
)

print()

print("----------------------------------")


# =============================================================
# PRINT FIXED STRATEGY COMPARISON
# =============================================================

print()

print("FIXED STRATEGY COMPARISON")

print()

print(
    "One-stop wins:",
    fixed_one_wins
)

print(
    "Two-stop wins:",
    fixed_two_wins
)

print(
    f"Average gap "
    f"(two-stop minus one-stop): "
    f"{average_fixed_gap:.1f} seconds"
)

print()

print("----------------------------------")


# =============================================================
# PRINT REACTIVE STRATEGY COMPARISON
# =============================================================

print()

print("REACTIVE STRATEGY COMPARISON")

print()

print(
    "One-stop wins:",
    reactive_one_wins
)

print(
    "Two-stop wins:",
    reactive_two_wins
)

print(
    f"Average gap "
    f"(two-stop minus one-stop): "
    f"{average_reactive_gap:.1f} seconds"
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


    tyre_data = tyres[
        tyre_name
    ]


    losses = []


    for tyre_wear in wear_values:


        losses.append(
            calculate_tyre_loss(
                tyre_data,
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


    tyre_data = tyres[
        tyre_name
    ]


    penalties = []


    for tyre_age in warmup_ages:


        penalties.append(
            calculate_warmup_penalty(
                tyre_data,
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
# FUEL LOAD
# =============================================================

plt.figure(
    figsize=(10, 6)
)


fuel_masses = []


for lap in race_lap_numbers:


    fuel_masses.append(
        calculate_fuel_mass(lap)
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
    "Fuel Load Through the Race"
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


green_flag_wear = []


for lap in race_lap_numbers:


    green_flag_wear.append(
        calculate_fuel_wear_increment(
            lap,
            None,
            None
        )
    )


plt.plot(
    race_lap_numbers,
    green_flag_wear
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
    "Total Race Time (seconds)"
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
# GRAPH 6
# BASELINE LAP-TIME COMPARISON
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    race_lap_numbers,
    best_one_stop_lap_times,
    label=(
        "One Stop: "
        + best_one_stop_name
    )
)


plt.plot(
    race_lap_numbers,
    best_two_stop_lap_times,
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
    "Baseline Best Strategy Lap Times"
)

plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 7
# BASELINE STRATEGY GAP
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    race_lap_numbers,
    baseline_time_gap,
    label="Two-Stop minus One-Stop"
)


plt.axhline(
    0,
    linestyle="--",
    label="Equal Race Time"
)


plt.xlabel(
    "Race Lap"
)

plt.ylabel(
    "Time Gap (seconds)"
)

plt.title(
    "Baseline Strategy Time Gap"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 8
# FIXED MONTE CARLO DISTRIBUTION
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
    fixed_two_times,
    bins=25,
    alpha=0.6,
    label="Fixed Two-Stop"
)


plt.xlabel(
    "Race Time (seconds)"
)

plt.ylabel(
    "Simulated Races"
)

plt.title(
    "Fixed Strategy Monte Carlo Distribution"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 9
# REACTIVE MONTE CARLO DISTRIBUTION
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.hist(
    reactive_one_times,
    bins=25,
    alpha=0.6,
    label="Reactive One-Stop"
)


plt.hist(
    reactive_two_times,
    bins=25,
    alpha=0.6,
    label="Reactive Two-Stop"
)


plt.xlabel(
    "Race Time (seconds)"
)

plt.ylabel(
    "Simulated Races"
)

plt.title(
    "Reactive Strategy Monte Carlo Distribution"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 10
# BENEFIT OF REACTING
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.hist(
    one_stop_reaction_benefit,
    bins=25,
    alpha=0.6,
    label="One-Stop Reaction Benefit"
)


plt.hist(
    two_stop_reaction_benefit,
    bins=25,
    alpha=0.6,
    label="Two-Stop Reaction Benefit"
)


plt.axvline(
    0,
    linestyle="--",
    label="No Benefit"
)


plt.xlabel(
    "Fixed Time minus Reactive Time (seconds)"
)

plt.ylabel(
    "Simulated Races"
)

plt.title(
    "Benefit of Reacting to Safety Car"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 11
# FIXED VS REACTIVE STRATEGY GAP
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.hist(
    fixed_strategy_gaps,
    bins=25,
    alpha=0.6,
    label="Fixed Strategies"
)


plt.hist(
    reactive_strategy_gaps,
    bins=25,
    alpha=0.6,
    label="Reactive Strategies"
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
    "Fixed vs Reactive Strategy Gap"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 12
# SAFETY CAR START-LAP DISTRIBUTION
# =============================================================

safety_car_start_laps = []


for scenario in safety_car_scenarios:


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