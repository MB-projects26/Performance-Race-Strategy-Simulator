import matplotlib.pyplot as plt


# =============================================================
# RACE INPUTS
# =============================================================

race_laps = 50

normal_pit_loss = 22.0

minimum_stint = 5


# =============================================================
# SAFETY CAR MODEL
# =============================================================
#
# This is currently a known / predetermined Safety Car.
#
# The optimiser knows that the Safety Car occurs.
#
# Later we can make Safety Cars random and use
# Monte Carlo simulation.
#
# =============================================================

safety_car_enabled = True

safety_car_start_lap = 24

safety_car_duration = 3

safety_car_end_lap = (
    safety_car_start_lap
    + safety_car_duration
    - 1
)

# Simplified lap time while behind Safety Car

safety_car_lap_time = 120.0

# Pit-stop loss is smaller under Safety Car

safety_car_pit_loss = 10.0

# Tyres wear less while driving slowly

safety_car_tyre_wear_multiplier = 0.35


# =============================================================
# FUEL MODEL
# =============================================================

initial_fuel_mass = 100.0

fuel_burn_per_lap = 2.0

fuel_time_per_kg = 0.03

fuel_wear_sensitivity = 0.25


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
# 4 = warm-up recovery per lap
# 5 = tyre cliff threshold
# 6 = tyre cliff severity
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

def is_safety_car_lap(lap):

    if safety_car_enabled:

        if (
            lap >= safety_car_start_lap
            and lap <= safety_car_end_lap
        ):

            return True

    return False


# =============================================================
# FUNCTION: PIT-STOP LOSS
# =============================================================

def calculate_pit_loss(lap):

    if is_safety_car_lap(lap):

        return safety_car_pit_loss

    else:

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
# FUNCTION: FUEL LAP-TIME EFFECT
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

    # Less tyre wear during Safety Car laps

    if is_safety_car_lap(lap):

        wear_increment = (
            wear_increment
            * safety_car_tyre_wear_multiplier
        )

    return wear_increment


# =============================================================
# FUNCTION: TYRE CLIFF PENALTY
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
        linear_deg,
        quadratic_deg,
        tyre_wear,
        cliff_threshold,
        cliff_severity):

    normal_loss = (
        linear_deg * tyre_wear
        + quadratic_deg * (tyre_wear ** 2)
    )

    cliff_loss = calculate_cliff_penalty(
        tyre_wear,
        cliff_threshold,
        cliff_severity
    )

    total_tyre_loss = (
        normal_loss
        + cliff_loss
    )

    return total_tyre_loss


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

    # -----------------------------
    # Safety Car lap
    # -----------------------------

    if is_safety_car_lap(lap):

        return safety_car_lap_time


    # -----------------------------
    # Normal racing lap
    # -----------------------------

    base_time = tyre_data[0]

    linear_deg = tyre_data[1]

    quadratic_deg = tyre_data[2]

    initial_warmup = tyre_data[3]

    warmup_recovery = tyre_data[4]

    cliff_threshold = tyre_data[5]

    cliff_severity = tyre_data[6]


    tyre_loss = calculate_tyre_loss(
        linear_deg,
        quadratic_deg,
        tyre_wear,
        cliff_threshold,
        cliff_severity
    )


    warmup_penalty = calculate_warmup_penalty(
        initial_warmup,
        warmup_recovery,
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
# FUNCTION: CALCULATE ONE-STOP STRATEGY
# =============================================================

def calculate_one_stop_strategy(
        first_tyre_data,
        second_tyre_data):

    pit_laps = []

    race_times = []


    for pit_lap in range(
        minimum_stint,
        race_laps - minimum_stint + 1
    ):

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


            # Pit stop

            if lap == pit_lap:

                total_time = (
                    total_time
                    + calculate_pit_loss(lap)
                )

                tyre_age = 0

                tyre_wear = 0.0


        pit_laps.append(
            pit_lap
        )

        race_times.append(
            total_time
        )


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
# FUNCTION: CALCULATE TWO-STOP STRATEGY
# =============================================================

def calculate_two_stop_strategy(
        first_tyre_data,
        second_tyre_data,
        third_tyre_data):

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


                # First pit stop

                if lap == pit_lap_1:

                    total_time = (
                        total_time
                        + calculate_pit_loss(lap)
                    )

                    tyre_age = 0

                    tyre_wear = 0.0


                # Second pit stop

                if lap == pit_lap_2:

                    total_time = (
                        total_time
                        + calculate_pit_loss(lap)
                    )

                    tyre_age = 0

                    tyre_wear = 0.0


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
# FUNCTION: SIMULATE ONE-STOP LAP TRACE
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
# FUNCTION: SIMULATE TWO-STOP LAP TRACE
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
                + calculate_pit_loss(lap)
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
                + calculate_pit_loss(lap)
            )

            tyre_age = 0

            tyre_wear = 0.0


        if lap == pit_lap_2:

            total_time = (
                total_time
                + calculate_pit_loss(lap)
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
# LAP-TIME TRACES
# =============================================================

(
    best_one_stop_laps,
    best_one_stop_lap_times

) = simulate_one_stop(
    best_one_first_tyre,
    best_one_second_tyre,
    best_one_stop_pit
)


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
# CUMULATIVE TIMES
# =============================================================

(
    one_stop_cumulative_laps,
    one_stop_cumulative_times

) = cumulative_one_stop(
    best_one_first_tyre,
    best_one_second_tyre,
    best_one_stop_pit
)


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
# STRATEGY TIME GAP
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

print("SAFETY CAR MODEL")

print()

print(
    "Safety Car enabled:",
    safety_car_enabled
)

print(
    "Safety Car starts:",
    safety_car_start_lap
)

print(
    "Safety Car ends:",
    safety_car_end_lap
)

print(
    "Safety Car duration:",
    safety_car_duration,
    "laps"
)

print(
    "Safety Car lap time:",
    safety_car_lap_time,
    "seconds"
)

print(
    "Pit loss under Safety Car:",
    safety_car_pit_loss,
    "seconds"
)

print(
    "SC tyre-wear multiplier:",
    safety_car_tyre_wear_multiplier
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
    "Legal combinations tested:",
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

    if is_safety_car_lap(pit_lap):

        print(
            "Pit stop made under Safety Car"
        )

    else:

        print(
            "Pit stop made under green flag"
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
    "Pit loss:",
    calculate_pit_loss(
        best_one_stop_pit
    ),
    "seconds"
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
    "Legal combinations tested:",
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
    "Pit 1 loss:",
    calculate_pit_loss(
        best_two_stop_pit_1
    ),
    "seconds"
)

print(
    "Pit 2 loss:",
    calculate_pit_loss(
        best_two_stop_pit_2
    ),
    "seconds"
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


if best_two_stop_time < best_one_stop_time:

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
# TYRE DEGRADATION INCLUDING CLIFF
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

    wear = (
        wear
        + 0.5
    )


for tyre_name in tyres:

    tyre_data = tyres[
        tyre_name
    ]

    losses = []


    for tyre_wear in wear_values:

        loss = calculate_tyre_loss(
            tyre_data[1],
            tyre_data[2],
            tyre_wear,
            tyre_data[5],
            tyre_data[6]
        )

        losses.append(
            loss
        )


    plt.plot(
        wear_values,
        losses,
        label=tyre_name
    )


plt.xlabel(
    "Effective Tyre Wear (equivalent laps)"
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
# FUEL EFFECT ON TYRE WEAR
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


plt.axvspan(
    safety_car_start_lap,
    safety_car_end_lap,
    alpha=0.15,
    label="Safety Car"
)


plt.xlabel(
    "Race Lap"
)

plt.ylabel(
    "Equivalent Tyre Wear per Lap"
)

plt.title(
    "Fuel and Safety Car Effect on Tyre Wear"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 5
# PIT-STOP LOSS THROUGH RACE
# =============================================================

plt.figure(
    figsize=(10, 6)
)


pit_losses = []


for lap in race_lap_numbers:

    pit_losses.append(
        calculate_pit_loss(lap)
    )


plt.plot(
    race_lap_numbers,
    pit_losses
)


plt.axvspan(
    safety_car_start_lap,
    safety_car_end_lap,
    alpha=0.15,
    label="Safety Car"
)


plt.xlabel(
    "Race Lap"
)

plt.ylabel(
    "Pit-Stop Loss (seconds)"
)

plt.title(
    "Pit-Stop Cost Through the Race"
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 6
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


plt.axvspan(
    safety_car_start_lap,
    safety_car_end_lap,
    alpha=0.15,
    label="Safety Car"
)


plt.xlabel(
    "Pit Lap"
)

plt.ylabel(
    "Total Race Time (seconds)"
)

plt.title(
    "One-Stop Strategy Comparison with Safety Car"
)

plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 7
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


plt.axvspan(
    safety_car_start_lap,
    safety_car_end_lap,
    alpha=0.15,
    label="Safety Car"
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

plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 8
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


plt.axvspan(
    safety_car_start_lap,
    safety_car_end_lap,
    alpha=0.15,
    label="Safety Car"
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

plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 9
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


plt.axvspan(
    safety_car_start_lap,
    safety_car_end_lap,
    alpha=0.15,
    label="Safety Car"
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
# GRAPH 10
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


plt.axvspan(
    safety_car_start_lap,
    safety_car_end_lap,
    alpha=0.15,
    label="Safety Car"
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
# GRAPH 11
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


plt.axvspan(
    safety_car_start_lap,
    safety_car_end_lap,
    alpha=0.15,
    label="Safety Car"
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