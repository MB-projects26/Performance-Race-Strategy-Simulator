import matplotlib.pyplot as plt


# =============================================================
# RACE INPUTS
# =============================================================

race_laps = 50
pit_loss = 22.0
minimum_stint = 5


# =============================================================
# FUEL MODEL
# =============================================================
#
# The car starts with 100 kg of fuel.
#
# 2 kg is burned per lap.
#
# As fuel burns:
# - the car becomes faster
# - the tyres experience less wear
#
# fuel_wear_sensitivity = 0.25 means:
#
# At full fuel:
# tyre wear per lap = 1.25 equivalent laps
#
# At very low fuel:
# tyre wear per lap approaches 1.00 equivalent lap
#
# These are modelling assumptions.
# =============================================================

initial_fuel_mass = 100.0

fuel_burn_per_lap = 2.0

fuel_time_per_kg = 0.03

fuel_wear_sensitivity = 0.25


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
# 4 = warm-up recovery per lap
#
# =============================================================

tyres = {

    "Soft": (
        89.0,
        0.10,
        0.006,
        0.30,
        0.15
    ),

    "Medium": (
        90.0,
        0.06,
        0.0025,
        0.50,
        0.15
    ),

    "Hard": (
        92.0,
        0.03,
        0.001,
        0.70,
        0.15
    )
}


# =============================================================
# FUNCTION: CALCULATE FUEL MASS
# =============================================================

def calculate_fuel_mass(lap):

    fuel_mass = (
        initial_fuel_mass
        - fuel_burn_per_lap * (lap - 1)
    )

    # Fuel mass cannot become negative
    if fuel_mass < 0:

        fuel_mass = 0.0

    return fuel_mass


# =============================================================
# FUNCTION: CALCULATE FUEL TIME GAIN
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
# FUNCTION: CALCULATE FUEL-RELATED TYRE WEAR
# =============================================================

def calculate_fuel_wear_increment(lap):

    current_fuel = calculate_fuel_mass(lap)

    fuel_fraction = (
        current_fuel
        / initial_fuel_mass
    )

    wear_increment = (
        1.0
        + fuel_wear_sensitivity * fuel_fraction
    )

    return wear_increment


# =============================================================
# FUNCTION: TYRE DEGRADATION
# =============================================================

def calculate_tyre_loss(
        linear_deg,
        quadratic_deg,
        tyre_wear):

    tyre_loss = (
        linear_deg * tyre_wear
        + quadratic_deg * (tyre_wear ** 2)
    )

    return tyre_loss


# =============================================================
# FUNCTION: TYRE WARM-UP
# =============================================================

def calculate_warmup_penalty(
        initial_penalty,
        recovery_rate,
        tyre_age):

    warmup_penalty = (
        initial_penalty
        - recovery_rate * tyre_age
    )

    # Warm-up penalty cannot become negative
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
        lap):

    base_time = tyre_data[0]

    linear_deg = tyre_data[1]

    quadratic_deg = tyre_data[2]

    initial_warmup = tyre_data[3]

    warmup_recovery = tyre_data[4]


    # -----------------------------
    # Tyre degradation
    # -----------------------------

    tyre_loss = calculate_tyre_loss(
        linear_deg,
        quadratic_deg,
        tyre_wear
    )


    # -----------------------------
    # Warm-up penalty
    # -----------------------------

    warmup_penalty = calculate_warmup_penalty(
        initial_warmup,
        warmup_recovery,
        tyre_age
    )


    # -----------------------------
    # Fuel effect
    # -----------------------------

    fuel_time_gain = calculate_fuel_time_gain(
        lap
    )


    # -----------------------------
    # Final lap time
    # -----------------------------

    lap_time = (
        base_time
        + tyre_loss
        + warmup_penalty
        - fuel_time_gain
    )

    return lap_time


# =============================================================
# FUNCTION: ONE-STOP STRATEGY
# =============================================================

def calculate_one_stop_strategy(
        first_tyre_data,
        second_tyre_data):

    pit_laps = []

    race_times = []


    # Test every legal pit lap
    for pit_lap in range(
        minimum_stint,
        race_laps - minimum_stint + 1
    ):

        total_time = 0.0

        tyre_age = 0

        tyre_wear = 0.0


        # Simulate race
        for lap in range(
            1,
            race_laps + 1
        ):


            # First stint
            if lap <= pit_lap:

                current_tyre = first_tyre_data


            # Second stint
            else:

                current_tyre = second_tyre_data


            # Calculate lap time
            lap_time = calculate_lap_time(
                current_tyre,
                tyre_age,
                tyre_wear,
                lap
            )


            total_time = (
                total_time
                + lap_time
            )


            # -----------------------------
            # Increase tyre age
            # -----------------------------

            tyre_age = (
                tyre_age
                + 1
            )


            # -----------------------------
            # Increase tyre wear
            #
            # Heavy fuel increases wear
            # -----------------------------

            tyre_wear = (
                tyre_wear
                + calculate_fuel_wear_increment(lap)
            )


            # -----------------------------
            # Pit stop
            # -----------------------------

            if lap == pit_lap:

                total_time = (
                    total_time
                    + pit_loss
                )

                tyre_age = 0

                tyre_wear = 0.0


        pit_laps.append(
            pit_lap
        )

        race_times.append(
            total_time
        )


    # Find fastest pit lap
    best_time = min(
        race_times
    )

    best_index = race_times.index(
        best_time
    )

    best_pit_lap = pit_laps[
        best_index
    ]


    best_time = round(
        best_time,
        6
    )


    return (
        best_pit_lap,
        best_time,
        pit_laps,
        race_times
    )


# =============================================================
# FUNCTION: TWO-STOP STRATEGY
# =============================================================

def calculate_two_stop_strategy(
        first_tyre_data,
        second_tyre_data,
        third_tyre_data):

    best_time = None

    best_pit_1 = None

    best_pit_2 = None


    # Test first pit stop
    for pit_lap_1 in range(
        minimum_stint,
        race_laps - (2 * minimum_stint) + 1
    ):


        # Test second pit stop
        for pit_lap_2 in range(
            pit_lap_1 + minimum_stint,
            race_laps - minimum_stint + 1
        ):

            total_time = 0.0

            tyre_age = 0

            tyre_wear = 0.0


            # Simulate race
            for lap in range(
                1,
                race_laps + 1
            ):


                # First stint
                if lap <= pit_lap_1:

                    current_tyre = first_tyre_data


                # Second stint
                elif lap <= pit_lap_2:

                    current_tyre = second_tyre_data


                # Third stint
                else:

                    current_tyre = third_tyre_data


                # Calculate lap time
                lap_time = calculate_lap_time(
                    current_tyre,
                    tyre_age,
                    tyre_wear,
                    lap
                )


                total_time = (
                    total_time
                    + lap_time
                )


                # Increase tyre age
                tyre_age = (
                    tyre_age
                    + 1
                )


                # Increase tyre wear
                tyre_wear = (
                    tyre_wear
                    + calculate_fuel_wear_increment(lap)
                )


                # First pit stop
                if lap == pit_lap_1:

                    total_time = (
                        total_time
                        + pit_loss
                    )

                    tyre_age = 0

                    tyre_wear = 0.0


                # Second pit stop
                if lap == pit_lap_2:

                    total_time = (
                        total_time
                        + pit_loss
                    )

                    tyre_age = 0

                    tyre_wear = 0.0


            # Check fastest result
            if (
                best_time is None
                or total_time < best_time
            ):

                best_time = total_time

                best_pit_1 = pit_lap_1

                best_pit_2 = pit_lap_2


    best_time = round(
        best_time,
        6
    )


    return (
        best_pit_1,
        best_pit_2,
        best_time
    )


# =============================================================
# FUNCTION: AUTOMATIC ONE-STOP SEARCH
# =============================================================

def find_best_one_stop():

    best_time = None

    best_strategy = None

    best_pit = None

    all_results = {}

    legal_combinations = 0


    tyre_names = list(
        tyres.keys()
    )


    for first_tyre in tyre_names:

        for second_tyre in tyre_names:


            # Must use different compounds
            if first_tyre == second_tyre:

                continue


            legal_combinations = (
                legal_combinations
                + 1
            )


            result = calculate_one_stop_strategy(

                tyres[first_tyre],

                tyres[second_tyre]
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


            # Check fastest
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
# FUNCTION: AUTOMATIC TWO-STOP SEARCH
# =============================================================

def find_best_two_stop():

    best_time = None

    best_strategy = None

    best_pit_1 = None

    best_pit_2 = None

    legal_combinations = 0


    tyre_names = list(
        tyres.keys()
    )


    for first_tyre in tyre_names:

        for second_tyre in tyre_names:

            for third_tyre in tyre_names:


                # Must use at least
                # two compounds
                if (
                    first_tyre
                    == second_tyre
                    == third_tyre
                ):

                    continue


                legal_combinations = (
                    legal_combinations
                    + 1
                )


                result = calculate_two_stop_strategy(

                    tyres[first_tyre],

                    tyres[second_tyre],

                    tyres[third_tyre]
                )


                pit_1 = result[0]

                pit_2 = result[1]

                race_time = result[2]


                # Check fastest
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
# FUNCTION: SIMULATE ONE-STOP LAP TIMES
# =============================================================

def simulate_one_stop(
        first_tyre_data,
        second_tyre_data,
        pit_lap):

    lap_numbers = []

    lap_times = []

    tyre_age = 0

    tyre_wear = 0.0


    for lap in range(
        1,
        race_laps + 1
    ):


        if lap <= pit_lap:

            current_tyre = first_tyre_data


        else:

            current_tyre = second_tyre_data


        lap_time = calculate_lap_time(
            current_tyre,
            tyre_age,
            tyre_wear,
            lap
        )


        lap_numbers.append(
            lap
        )

        lap_times.append(
            lap_time
        )


        tyre_age = (
            tyre_age
            + 1
        )


        tyre_wear = (
            tyre_wear
            + calculate_fuel_wear_increment(lap)
        )


        if lap == pit_lap:

            tyre_age = 0

            tyre_wear = 0.0


    return (
        lap_numbers,
        lap_times
    )


# =============================================================
# FUNCTION: SIMULATE TWO-STOP LAP TIMES
# =============================================================

def simulate_two_stop(
        first_tyre_data,
        second_tyre_data,
        third_tyre_data,
        pit_lap_1,
        pit_lap_2):

    lap_numbers = []

    lap_times = []

    tyre_age = 0

    tyre_wear = 0.0


    for lap in range(
        1,
        race_laps + 1
    ):


        if lap <= pit_lap_1:

            current_tyre = first_tyre_data


        elif lap <= pit_lap_2:

            current_tyre = second_tyre_data


        else:

            current_tyre = third_tyre_data


        lap_time = calculate_lap_time(
            current_tyre,
            tyre_age,
            tyre_wear,
            lap
        )


        lap_numbers.append(
            lap
        )

        lap_times.append(
            lap_time
        )


        tyre_age = (
            tyre_age
            + 1
        )


        tyre_wear = (
            tyre_wear
            + calculate_fuel_wear_increment(lap)
        )


        if lap == pit_lap_1:

            tyre_age = 0

            tyre_wear = 0.0


        if lap == pit_lap_2:

            tyre_age = 0

            tyre_wear = 0.0


    return (
        lap_numbers,
        lap_times
    )


# =============================================================
# FUNCTION: ONE-STOP CUMULATIVE TIME
# =============================================================

def cumulative_one_stop(
        first_tyre_data,
        second_tyre_data,
        pit_lap):

    lap_numbers = []

    cumulative_times = []

    total_time = 0.0

    tyre_age = 0

    tyre_wear = 0.0


    for lap in range(
        1,
        race_laps + 1
    ):


        if lap <= pit_lap:

            current_tyre = first_tyre_data


        else:

            current_tyre = second_tyre_data


        lap_time = calculate_lap_time(
            current_tyre,
            tyre_age,
            tyre_wear,
            lap
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
            + calculate_fuel_wear_increment(lap)
        )


        if lap == pit_lap:

            total_time = (
                total_time
                + pit_loss
            )

            tyre_age = 0

            tyre_wear = 0.0


        lap_numbers.append(
            lap
        )

        cumulative_times.append(
            total_time
        )


    return (
        lap_numbers,
        cumulative_times
    )


# =============================================================
# FUNCTION: TWO-STOP CUMULATIVE TIME
# =============================================================

def cumulative_two_stop(
        first_tyre_data,
        second_tyre_data,
        third_tyre_data,
        pit_lap_1,
        pit_lap_2):

    lap_numbers = []

    cumulative_times = []

    total_time = 0.0

    tyre_age = 0

    tyre_wear = 0.0


    for lap in range(
        1,
        race_laps + 1
    ):


        if lap <= pit_lap_1:

            current_tyre = first_tyre_data


        elif lap <= pit_lap_2:

            current_tyre = second_tyre_data


        else:

            current_tyre = third_tyre_data


        lap_time = calculate_lap_time(
            current_tyre,
            tyre_age,
            tyre_wear,
            lap
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
            + calculate_fuel_wear_increment(lap)
        )


        if lap == pit_lap_1:

            total_time = (
                total_time
                + pit_loss
            )

            tyre_age = 0

            tyre_wear = 0.0


        if lap == pit_lap_2:

            total_time = (
                total_time
                + pit_loss
            )

            tyre_age = 0

            tyre_wear = 0.0


        lap_numbers.append(
            lap
        )

        cumulative_times.append(
            total_time
        )


    return (
        lap_numbers,
        cumulative_times
    )


# =============================================================
# RUN ONE-STOP SEARCH
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


best_one_first_tyre = tyres[
    best_one_stop_strategy[0]
]

best_one_second_tyre = tyres[
    best_one_stop_strategy[1]
]


# =============================================================
# RUN TWO-STOP SEARCH
# =============================================================

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


best_two_first_tyre = tyres[
    best_two_stop_strategy[0]
]

best_two_second_tyre = tyres[
    best_two_stop_strategy[1]
]

best_two_third_tyre = tyres[
    best_two_stop_strategy[2]
]


# =============================================================
# BEST ONE-STOP LAP TRACE
# =============================================================

(
    best_one_stop_laps,
    best_one_stop_lap_times

) = simulate_one_stop(

    best_one_first_tyre,

    best_one_second_tyre,

    best_one_stop_pit
)


# =============================================================
# BEST TWO-STOP LAP TRACE
# =============================================================

(
    best_two_stop_laps,
    best_two_stop_lap_times

) = simulate_two_stop(

    best_two_first_tyre,

    best_two_second_tyre,

    best_two_third_tyre,

    best_two_stop_pit_1,

    best_two_stop_pit_2
)


# =============================================================
# CUMULATIVE ONE-STOP
# =============================================================

(
    one_stop_cumulative_laps,
    one_stop_cumulative_times

) = cumulative_one_stop(

    best_one_first_tyre,

    best_one_second_tyre,

    best_one_stop_pit
)


# =============================================================
# CUMULATIVE TWO-STOP
# =============================================================

(
    two_stop_cumulative_laps,
    two_stop_cumulative_times

) = cumulative_two_stop(

    best_two_first_tyre,

    best_two_second_tyre,

    best_two_third_tyre,

    best_two_stop_pit_1,

    best_two_stop_pit_2
)


# =============================================================
# CALCULATE TIME GAP
# =============================================================

time_gap = []


for i in range(
    race_laps
):

    gap = (

        two_stop_cumulative_times[i]

        - one_stop_cumulative_times[i]
    )


    time_gap.append(
        gap
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
    "Pit loss:",
    pit_loss,
    "seconds"
)

print(
    "Minimum stint:",
    minimum_stint,
    "laps"
)

print()

print("FUEL MODEL")

print()

print(
    "Initial fuel mass:",
    initial_fuel_mass,
    "kg"
)

print(
    "Fuel burn:",
    fuel_burn_per_lap,
    "kg per lap"
)

print(
    "Lap-time effect:",
    fuel_time_per_kg,
    "seconds per kg"
)

print(
    "Fuel tyre-wear sensitivity:",
    fuel_wear_sensitivity
)

print()

print(
    "Full-fuel tyre wear multiplier:",
    f"{calculate_fuel_wear_increment(1):.3f}"
)

print(
    "Final-lap tyre wear multiplier:",
    f"{calculate_fuel_wear_increment(race_laps):.3f}"
)

print()

print("----------------------------------")

print()


# =============================================================
# PRINT ONE-STOP RESULTS
# =============================================================

print("ONE-STOP AUTOMATIC SEARCH")

print()

print(
    "Legal tyre combinations tested:",
    one_stop_combination_count
)

print()


for strategy_name in one_stop_results:

    result = one_stop_results[
        strategy_name
    ]

    pit_lap = result[0]

    race_time = result[1]


    print(
        strategy_name
    )

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
# PRINT BEST ONE-STOP
# =============================================================

print("----------------------------------")

print()

print("BEST ONE-STOP STRATEGY")

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
    "Stint lengths:",
    best_one_stop_pit,
    "+",
    race_laps - best_one_stop_pit
)

print(
    f"Race time: "
    f"{best_one_stop_time:.1f} seconds"
)


# =============================================================
# PRINT BEST TWO-STOP
# =============================================================

print()

print("----------------------------------")

print()

print("TWO-STOP AUTOMATIC SEARCH")

print()

print(
    "Legal tyre combinations tested:",
    two_stop_combination_count
)

print()

print("BEST TWO-STOP STRATEGY")

print()

print(
    "Strategy:",
    best_two_stop_name
)

print(
    "Pit 1:",
    best_two_stop_pit_1
)

print(
    "Pit 2:",
    best_two_stop_pit_2
)

print(
    "Stint lengths:",
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
# FINAL COMPARISON
# =============================================================

print()

print("----------------------------------")

print()

print("FINAL STRATEGY COMPARISON")

print()


if (
    best_two_stop_time
    < best_one_stop_time
):

    time_saved = (

        best_one_stop_time

        - best_two_stop_time
    )


    print(
        "Best overall strategy:",
        best_two_stop_name
    )

    print(
        "Strategy type: Two-stop"
    )

    print(
        f"Time saved compared with "
        f"best one-stop: "
        f"{time_saved:.1f} seconds"
    )


else:

    time_saved = (

        best_two_stop_time

        - best_one_stop_time
    )


    print(
        "Best overall strategy:",
        best_one_stop_name
    )

    print(
        "Strategy type: One-stop"
    )

    print(
        f"Time saved compared with "
        f"best two-stop: "
        f"{time_saved:.1f} seconds"
    )


# =============================================================
# GRAPH 1
# NON-LINEAR TYRE DEGRADATION
# =============================================================

plt.figure(
    figsize=(10, 6)
)


wear_values = list(
    range(0, 31)
)


for tyre_name in tyres:

    tyre_data = tyres[
        tyre_name
    ]

    degradation_losses = []


    for tyre_wear in wear_values:

        tyre_loss = calculate_tyre_loss(

            tyre_data[1],

            tyre_data[2],

            tyre_wear
        )

        degradation_losses.append(
            tyre_loss
        )


    plt.plot(
        wear_values,
        degradation_losses,
        label=tyre_name
    )


plt.xlabel(
    "Effective Tyre Wear (equivalent laps)"
)

plt.ylabel(
    "Lap-Time Loss (seconds)"
)

plt.title(
    "Non-Linear Tyre Degradation Model"
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

        penalty = calculate_warmup_penalty(

            tyre_data[3],

            tyre_data[4],

            tyre_age
        )

        penalties.append(
            penalty
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


race_lap_numbers = list(
    range(1, race_laps + 1)
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
# FUEL-RELATED TYRE WEAR
# =============================================================

plt.figure(
    figsize=(10, 6)
)


wear_multipliers = []


for lap in race_lap_numbers:

    wear_multipliers.append(
        calculate_fuel_wear_increment(lap)
    )


plt.plot(
    race_lap_numbers,
    wear_multipliers
)


plt.xlabel(
    "Race Lap"
)

plt.ylabel(
    "Tyre Wear Multiplier"
)

plt.title(
    "Fuel Load Effect on Tyre Wear"
)

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 5
# ALL LEGAL ONE-STOP STRATEGIES
# =============================================================

plt.figure(
    figsize=(10, 6)
)


for strategy_name in one_stop_results:

    result = one_stop_results[
        strategy_name
    ]

    pit_laps = result[2]

    race_times = result[3]


    plt.plot(
        pit_laps,
        race_times,
        label=strategy_name
    )


plt.xlabel(
    "Pit Lap"
)

plt.ylabel(
    "Total Race Time (seconds)"
)

plt.title(
    "All Legal One-Stop Strategy Comparison"
)

plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 6
# BEST ONE-STOP LAP TRACE
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    best_one_stop_laps,
    best_one_stop_lap_times,
    label=best_one_stop_name
)


plt.axvline(
    best_one_stop_pit,
    linestyle="--",
    label="Pit Stop"
)


plt.xlabel(
    "Race Lap"
)

plt.ylabel(
    "Lap Time (seconds)"
)

plt.title(
    "Best One-Stop Lap-Time Trace"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 7
# BEST TWO-STOP LAP TRACE
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    best_two_stop_laps,
    best_two_stop_lap_times,
    label=best_two_stop_name
)


plt.axvline(
    best_two_stop_pit_1,
    linestyle="--",
    label="Pit Stop 1"
)


plt.axvline(
    best_two_stop_pit_2,
    linestyle="--",
    label="Pit Stop 2"
)


plt.xlabel(
    "Race Lap"
)

plt.ylabel(
    "Lap Time (seconds)"
)

plt.title(
    "Best Two-Stop Lap-Time Trace"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 8
# ONE-STOP VS TWO-STOP LAP TIMES
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    best_one_stop_laps,
    best_one_stop_lap_times,
    label=(
        "One Stop: "
        + best_one_stop_name
    )
)


plt.plot(
    best_two_stop_laps,
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
    "Best One-Stop vs Best Two-Stop "
    "Lap-Time Comparison"
)


plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 9
# CUMULATIVE RACE TIME
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    one_stop_cumulative_laps,
    one_stop_cumulative_times,
    label=(
        "One Stop: "
        + best_one_stop_name
    )
)


plt.plot(
    two_stop_cumulative_laps,
    two_stop_cumulative_times,
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
    "Cumulative Race Time (seconds)"
)

plt.title(
    "Best One-Stop vs Best Two-Stop "
    "Cumulative Race Time"
)


plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 10
# STRATEGY TIME GAP
# =============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    one_stop_cumulative_laps,
    time_gap,
    label="Two-Stop minus One-Stop"
)


plt.axhline(
    0,
    linestyle="--",
    label="Equal Race Time"
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
    "Time Gap (seconds)"
)

plt.title(
    "Best Two-Stop vs Best One-Stop Time Gap"
)


plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

plt.show()