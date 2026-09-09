import matplotlib.pyplot as plt


# =============================================================
# RACE INPUTS
# =============================================================

race_laps = 50
pit_loss = 22.0
fuel_effect = 0.06

# Minimum number of laps allowed in any stint
minimum_stint = 5


# =============================================================
# TYRE DATA
# =============================================================

soft_base_time = 89.0
soft_degradation = 0.20

medium_base_time = 90.0
medium_degradation = 0.10

hard_base_time = 92.0
hard_degradation = 0.05


# Store tyre data in a dictionary

tyres = {
    "Soft": (soft_base_time, soft_degradation),
    "Medium": (medium_base_time, medium_degradation),
    "Hard": (hard_base_time, hard_degradation)
}


# =============================================================
# FUNCTION: CALCULATE ONE-STOP STRATEGY
# =============================================================

def calculate_one_stop_strategy(first_base, first_deg,
                                second_base, second_deg):

    pit_laps = []
    race_times = []

    # Pit lap must leave at least the minimum stint length
    # on both sides of the pit stop
    for pit_lap in range(
        minimum_stint,
        race_laps - minimum_stint + 1
    ):

        total_time = 0.0
        tyre_age = 0

        # Simulate entire race
        for lap in range(1, race_laps + 1):

            # First tyre
            if lap <= pit_lap:

                lap_time = (
                    first_base
                    + first_deg * tyre_age
                    - fuel_effect * (lap - 1)
                )

            # Second tyre
            else:

                lap_time = (
                    second_base
                    + second_deg * tyre_age
                    - fuel_effect * (lap - 1)
                )

            total_time = total_time + lap_time

            tyre_age = tyre_age + 1

            # Pit stop at end of chosen lap
            if lap == pit_lap:

                total_time = total_time + pit_loss

                tyre_age = 0

        pit_laps.append(pit_lap)

        race_times.append(total_time)

    # Find fastest pit lap
    best_time = min(race_times)

    best_index = race_times.index(best_time)

    best_pit_lap = pit_laps[best_index]

    best_time = round(best_time, 6)

    return best_pit_lap, best_time, pit_laps, race_times


# =============================================================
# FUNCTION: CALCULATE TWO-STOP STRATEGY
# =============================================================

def calculate_two_stop_strategy(first_base, first_deg,
                                second_base, second_deg,
                                third_base, third_deg):

    best_time = None

    best_pit_1 = None
    best_pit_2 = None

    # First stop must leave enough laps for
    # stint 2 and stint 3
    for pit_lap_1 in range(
        minimum_stint,
        race_laps - (2 * minimum_stint) + 1
    ):

        # Second stop must be at least minimum_stint
        # laps after the first stop and leave enough
        # laps for the final stint
        for pit_lap_2 in range(
            pit_lap_1 + minimum_stint,
            race_laps - minimum_stint + 1
        ):

            total_time = 0.0
            tyre_age = 0

            # Simulate entire race
            for lap in range(1, race_laps + 1):

                # First tyre
                if lap <= pit_lap_1:

                    lap_time = (
                        first_base
                        + first_deg * tyre_age
                        - fuel_effect * (lap - 1)
                    )

                # Second tyre
                elif lap <= pit_lap_2:

                    lap_time = (
                        second_base
                        + second_deg * tyre_age
                        - fuel_effect * (lap - 1)
                    )

                # Third tyre
                else:

                    lap_time = (
                        third_base
                        + third_deg * tyre_age
                        - fuel_effect * (lap - 1)
                    )

                total_time = total_time + lap_time

                tyre_age = tyre_age + 1

                # First pit stop
                if lap == pit_lap_1:

                    total_time = total_time + pit_loss

                    tyre_age = 0

                # Second pit stop
                if lap == pit_lap_2:

                    total_time = total_time + pit_loss

                    tyre_age = 0

            # Check if this is fastest result so far
            if best_time is None or total_time < best_time:

                best_time = total_time

                best_pit_1 = pit_lap_1

                best_pit_2 = pit_lap_2

    best_time = round(best_time, 6)

    return best_pit_1, best_pit_2, best_time


# =============================================================
# FUNCTION: AUTOMATIC ONE-STOP SEARCH
# =============================================================

def find_best_one_stop():

    best_time = None

    best_strategy = None

    best_pit = None

    tyre_names = list(tyres.keys())

    all_results = {}

    legal_combinations = 0

    # First tyre
    for first_tyre in tyre_names:

        # Second tyre
        for second_tyre in tyre_names:

            # Must use at least two different compounds
            if first_tyre == second_tyre:
                continue

            legal_combinations = legal_combinations + 1

            first_base = tyres[first_tyre][0]
            first_deg = tyres[first_tyre][1]

            second_base = tyres[second_tyre][0]
            second_deg = tyres[second_tyre][1]

            result = calculate_one_stop_strategy(
                first_base,
                first_deg,
                second_base,
                second_deg
            )

            pit_lap = result[0]
            race_time = result[1]

            strategy_name = (
                first_tyre
                + " -> "
                + second_tyre
            )

            # Save for graphing
            all_results[strategy_name] = result

            # Check if fastest so far
            if best_time is None or race_time < best_time:

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

    tyre_names = list(tyres.keys())

    legal_combinations = 0

    # First tyre
    for first_tyre in tyre_names:

        # Second tyre
        for second_tyre in tyre_names:

            # Third tyre
            for third_tyre in tyre_names:

                # Reject strategies using only one compound
                #
                # Rejected examples:
                #
                # Soft -> Soft -> Soft
                # Medium -> Medium -> Medium
                # Hard -> Hard -> Hard

                if first_tyre == second_tyre == third_tyre:
                    continue

                legal_combinations = legal_combinations + 1

                first_base = tyres[first_tyre][0]
                first_deg = tyres[first_tyre][1]

                second_base = tyres[second_tyre][0]
                second_deg = tyres[second_tyre][1]

                third_base = tyres[third_tyre][0]
                third_deg = tyres[third_tyre][1]

                result = calculate_two_stop_strategy(
                    first_base,
                    first_deg,
                    second_base,
                    second_deg,
                    third_base,
                    third_deg
                )

                pit_1 = result[0]
                pit_2 = result[1]
                race_time = result[2]

                # Check if fastest so far
                if best_time is None or race_time < best_time:

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
# FUNCTION: ONE-STOP LAP-TIME TRACE
# =============================================================

def simulate_one_stop(first_base, first_deg,
                      second_base, second_deg,
                      pit_lap):

    lap_numbers = []

    lap_times = []

    tyre_age = 0

    for lap in range(1, race_laps + 1):

        if lap <= pit_lap:

            lap_time = (
                first_base
                + first_deg * tyre_age
                - fuel_effect * (lap - 1)
            )

        else:

            lap_time = (
                second_base
                + second_deg * tyre_age
                - fuel_effect * (lap - 1)
            )

        lap_numbers.append(lap)

        lap_times.append(lap_time)

        tyre_age = tyre_age + 1

        if lap == pit_lap:

            tyre_age = 0

    return lap_numbers, lap_times


# =============================================================
# FUNCTION: TWO-STOP LAP-TIME TRACE
# =============================================================

def simulate_two_stop(first_base, first_deg,
                      second_base, second_deg,
                      third_base, third_deg,
                      pit_lap_1, pit_lap_2):

    lap_numbers = []

    lap_times = []

    tyre_age = 0

    for lap in range(1, race_laps + 1):

        if lap <= pit_lap_1:

            lap_time = (
                first_base
                + first_deg * tyre_age
                - fuel_effect * (lap - 1)
            )

        elif lap <= pit_lap_2:

            lap_time = (
                second_base
                + second_deg * tyre_age
                - fuel_effect * (lap - 1)
            )

        else:

            lap_time = (
                third_base
                + third_deg * tyre_age
                - fuel_effect * (lap - 1)
            )

        lap_numbers.append(lap)

        lap_times.append(lap_time)

        tyre_age = tyre_age + 1

        if lap == pit_lap_1:

            tyre_age = 0

        if lap == pit_lap_2:

            tyre_age = 0

    return lap_numbers, lap_times


# =============================================================
# FUNCTION: ONE-STOP CUMULATIVE RACE TIME
# =============================================================

def cumulative_one_stop(first_base, first_deg,
                        second_base, second_deg,
                        pit_lap):

    lap_numbers = []

    cumulative_times = []

    total_time = 0.0

    tyre_age = 0

    for lap in range(1, race_laps + 1):

        if lap <= pit_lap:

            lap_time = (
                first_base
                + first_deg * tyre_age
                - fuel_effect * (lap - 1)
            )

        else:

            lap_time = (
                second_base
                + second_deg * tyre_age
                - fuel_effect * (lap - 1)
            )

        total_time = total_time + lap_time

        tyre_age = tyre_age + 1

        if lap == pit_lap:

            total_time = total_time + pit_loss

            tyre_age = 0

        lap_numbers.append(lap)

        cumulative_times.append(total_time)

    return lap_numbers, cumulative_times


# =============================================================
# FUNCTION: TWO-STOP CUMULATIVE RACE TIME
# =============================================================

def cumulative_two_stop(first_base, first_deg,
                        second_base, second_deg,
                        third_base, third_deg,
                        pit_lap_1, pit_lap_2):

    lap_numbers = []

    cumulative_times = []

    total_time = 0.0

    tyre_age = 0

    for lap in range(1, race_laps + 1):

        if lap <= pit_lap_1:

            lap_time = (
                first_base
                + first_deg * tyre_age
                - fuel_effect * (lap - 1)
            )

        elif lap <= pit_lap_2:

            lap_time = (
                second_base
                + second_deg * tyre_age
                - fuel_effect * (lap - 1)
            )

        else:

            lap_time = (
                third_base
                + third_deg * tyre_age
                - fuel_effect * (lap - 1)
            )

        total_time = total_time + lap_time

        tyre_age = tyre_age + 1

        if lap == pit_lap_1:

            total_time = total_time + pit_loss

            tyre_age = 0

        if lap == pit_lap_2:

            total_time = total_time + pit_loss

            tyre_age = 0

        lap_numbers.append(lap)

        cumulative_times.append(total_time)

    return lap_numbers, cumulative_times


# =============================================================
# AUTOMATIC ONE-STOP SEARCH
# =============================================================

one_stop_search = find_best_one_stop()

best_one_stop_strategy = one_stop_search[0]

best_one_stop_pit = one_stop_search[1]

best_one_stop_time = one_stop_search[2]

one_stop_results = one_stop_search[3]

one_stop_combination_count = one_stop_search[4]


best_one_stop_name = (
    best_one_stop_strategy[0]
    + " -> "
    + best_one_stop_strategy[1]
)


# =============================================================
# GET BEST ONE-STOP TYRE DATA
# =============================================================

best_one_first_base = tyres[
    best_one_stop_strategy[0]
][0]

best_one_first_deg = tyres[
    best_one_stop_strategy[0]
][1]


best_one_second_base = tyres[
    best_one_stop_strategy[1]
][0]

best_one_second_deg = tyres[
    best_one_stop_strategy[1]
][1]


# =============================================================
# AUTOMATIC TWO-STOP SEARCH
# =============================================================

two_stop_search = find_best_two_stop()

best_two_stop_strategy = two_stop_search[0]

best_two_stop_pit_1 = two_stop_search[1]

best_two_stop_pit_2 = two_stop_search[2]

best_two_stop_time = two_stop_search[3]

two_stop_combination_count = two_stop_search[4]


best_two_stop_name = (
    best_two_stop_strategy[0]
    + " -> "
    + best_two_stop_strategy[1]
    + " -> "
    + best_two_stop_strategy[2]
)


# =============================================================
# GET BEST TWO-STOP TYRE DATA
# =============================================================

best_two_first_base = tyres[
    best_two_stop_strategy[0]
][0]

best_two_first_deg = tyres[
    best_two_stop_strategy[0]
][1]


best_two_second_base = tyres[
    best_two_stop_strategy[1]
][0]

best_two_second_deg = tyres[
    best_two_stop_strategy[1]
][1]


best_two_third_base = tyres[
    best_two_stop_strategy[2]
][0]

best_two_third_deg = tyres[
    best_two_stop_strategy[2]
][1]


# =============================================================
# LAP-TIME TRACE FOR BEST ONE-STOP
# =============================================================

best_one_stop_laps, best_one_stop_lap_times = simulate_one_stop(
    best_one_first_base,
    best_one_first_deg,
    best_one_second_base,
    best_one_second_deg,
    best_one_stop_pit
)


# =============================================================
# LAP-TIME TRACE FOR BEST TWO-STOP
# =============================================================

best_two_stop_laps, best_two_stop_lap_times = simulate_two_stop(
    best_two_first_base,
    best_two_first_deg,
    best_two_second_base,
    best_two_second_deg,
    best_two_third_base,
    best_two_third_deg,
    best_two_stop_pit_1,
    best_two_stop_pit_2
)


# =============================================================
# CUMULATIVE TIME FOR BEST ONE-STOP
# =============================================================

one_stop_cumulative_laps, one_stop_cumulative_times = cumulative_one_stop(
    best_one_first_base,
    best_one_first_deg,
    best_one_second_base,
    best_one_second_deg,
    best_one_stop_pit
)


# =============================================================
# CUMULATIVE TIME FOR BEST TWO-STOP
# =============================================================

two_stop_cumulative_laps, two_stop_cumulative_times = cumulative_two_stop(
    best_two_first_base,
    best_two_first_deg,
    best_two_second_base,
    best_two_second_deg,
    best_two_third_base,
    best_two_third_deg,
    best_two_stop_pit_1,
    best_two_stop_pit_2
)


# =============================================================
# CALCULATE TIME GAP
# =============================================================

time_gap = []

for i in range(race_laps):

    gap = (
        two_stop_cumulative_times[i]
        - one_stop_cumulative_times[i]
    )

    time_gap.append(gap)


# =============================================================
# PRINT MODEL SETTINGS
# =============================================================

print("MODEL SETTINGS")

print()

print("Race laps:", race_laps)

print("Pit loss:", pit_loss, "seconds")

print("Fuel effect:", fuel_effect, "seconds per lap")

print("Minimum stint length:", minimum_stint, "laps")

print()

print("----------------------------------")

print()


# =============================================================
# PRINT ALL ONE-STOP RESULTS
# =============================================================

print("ONE-STOP AUTOMATIC SEARCH")

print()

print(
    "Legal tyre combinations tested:",
    one_stop_combination_count
)

print()


for strategy_name in one_stop_results:

    result = one_stop_results[strategy_name]

    pit_lap = result[0]

    race_time = result[1]

    first_stint = pit_lap

    second_stint = race_laps - pit_lap

    print(strategy_name)

    print("Best pit lap:", pit_lap)

    print(
        "Stint lengths:",
        first_stint,
        "+",
        second_stint
    )

    print(f"Race time: {race_time:.1f} seconds")

    print()


# =============================================================
# PRINT BEST ONE-STOP
# =============================================================

print("----------------------------------")

print()

print("BEST ONE-STOP STRATEGY")

print()

print("Strategy:", best_one_stop_name)

print("Pit lap:", best_one_stop_pit)

print(
    "Stint lengths:",
    best_one_stop_pit,
    "+",
    race_laps - best_one_stop_pit
)

print(f"Race time: {best_one_stop_time:.1f} seconds")


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

print("Strategy:", best_two_stop_name)

print("Pit 1:", best_two_stop_pit_1)

print("Pit 2:", best_two_stop_pit_2)

print(
    "Stint lengths:",
    best_two_stop_pit_1,
    "+",
    best_two_stop_pit_2 - best_two_stop_pit_1,
    "+",
    race_laps - best_two_stop_pit_2
)

print(f"Race time: {best_two_stop_time:.1f} seconds")


# =============================================================
# FINAL STRATEGY COMPARISON
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

    print("Strategy type: Two-stop")

    print(
        f"Time saved compared with best one-stop: "
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

    print("Strategy type: One-stop")

    print(
        f"Time saved compared with best two-stop: "
        f"{time_saved:.1f} seconds"
    )


# =============================================================
# GRAPH 1
# ALL LEGAL ONE-STOP STRATEGIES
# =============================================================

plt.figure(figsize=(10, 6))


for strategy_name in one_stop_results:

    result = one_stop_results[strategy_name]

    pit_laps = result[2]

    race_times = result[3]

    plt.plot(
        pit_laps,
        race_times,
        label=strategy_name
    )


plt.xlabel("Pit Lap")

plt.ylabel("Total Race Time (seconds)")

plt.title("All Legal One-Stop Strategy Comparison")

plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 2
# BEST ONE-STOP LAP-TIME TRACE
# =============================================================

plt.figure(figsize=(10, 6))

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

plt.xlabel("Race Lap")

plt.ylabel("Lap Time (seconds)")

plt.title("Best One-Stop Lap-Time Trace")

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 3
# BEST TWO-STOP LAP-TIME TRACE
# =============================================================

plt.figure(figsize=(10, 6))

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

plt.xlabel("Race Lap")

plt.ylabel("Lap Time (seconds)")

plt.title("Best Two-Stop Lap-Time Trace")

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================
# GRAPH 4
# BEST ONE-STOP VS BEST TWO-STOP LAP TIMES
# =============================================================

plt.figure(figsize=(10, 6))

plt.plot(
    best_one_stop_laps,
    best_one_stop_lap_times,
    label="One Stop: " + best_one_stop_name
)

plt.plot(
    best_two_stop_laps,
    best_two_stop_lap_times,
    label="Two Stop: " + best_two_stop_name
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

plt.xlabel("Race Lap")

plt.ylabel("Lap Time (seconds)")

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
# GRAPH 5
# CUMULATIVE RACE-TIME COMPARISON
# =============================================================

plt.figure(figsize=(10, 6))

plt.plot(
    one_stop_cumulative_laps,
    one_stop_cumulative_times,
    label="One Stop: " + best_one_stop_name
)

plt.plot(
    two_stop_cumulative_laps,
    two_stop_cumulative_times,
    label="Two Stop: " + best_two_stop_name
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

plt.xlabel("Race Lap")

plt.ylabel("Cumulative Race Time (seconds)")

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
# GRAPH 6
# STRATEGY TIME GAP
# =============================================================

plt.figure(figsize=(10, 6))

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

plt.xlabel("Race Lap")

plt.ylabel("Time Gap (seconds)")

plt.title(
    "Best Two-Stop vs Best One-Stop Time Gap"
)

plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

plt.show()