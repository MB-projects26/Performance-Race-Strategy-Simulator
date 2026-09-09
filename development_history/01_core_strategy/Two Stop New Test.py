import matplotlib.pyplot as plt


# =============================================================
# RACE INPUTS
# =============================================================

race_laps = 50
pit_loss = 22.0
fuel_effect = 0.06


# =============================================================
# TYRE DATA
# =============================================================

soft_base_time = 89.0
soft_degradation = 0.20

medium_base_time = 90.0
medium_degradation = 0.10

hard_base_time = 92.0
hard_degradation = 0.05


# =============================================================
# FUNCTION: ONE-STOP STRATEGY
# =============================================================

def calculate_strategy(first_base, first_deg,
                       second_base, second_deg):

    pit_laps = []
    race_times = []

    # Test every possible pit lap
    for pit_lap in range(2, race_laps):

        total_time = 0.0
        tyre_age = 0

        # Simulate race lap by lap
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

            # Pit stop
            if lap == pit_lap:

                total_time = total_time + pit_loss

                tyre_age = 0

        # Save result
        pit_laps.append(pit_lap)

        race_times.append(total_time)

    # Find fastest pit lap
    best_time = min(race_times)

    best_index = race_times.index(best_time)

    best_pit_lap = pit_laps[best_index]

    return best_pit_lap, best_time, pit_laps, race_times


# =============================================================
# FUNCTION: TWO-STOP STRATEGY
# =============================================================

def calculate_two_stop_strategy(first_base, first_deg,
                                second_base, second_deg,
                                third_base, third_deg):

    best_time = None

    best_pit_1 = None

    best_pit_2 = None

    # Test every possible first pit stop
    for pit_lap_1 in range(2, race_laps - 1):

        # Second stop must happen after first stop
        for pit_lap_2 in range(pit_lap_1 + 1, race_laps):

            total_time = 0.0

            tyre_age = 0

            # Simulate race lap by lap
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

    return best_pit_1, best_pit_2, best_time


# =============================================================
# FUNCTION: ONE-STOP LAP-TIME TRACE
# =============================================================

def simulate_best_one_stop(first_base, first_deg,
                           second_base, second_deg,
                           pit_lap):

    lap_numbers = []

    lap_times = []

    tyre_age = 0

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

        lap_numbers.append(lap)

        lap_times.append(lap_time)

        tyre_age = tyre_age + 1

        # Reset tyre age after pit stop
        if lap == pit_lap:

            tyre_age = 0

    return lap_numbers, lap_times


# =============================================================
# FUNCTION: TWO-STOP LAP-TIME TRACE
# =============================================================

def simulate_best_two_stop(first_base, first_deg,
                           second_base, second_deg,
                           third_base, third_deg,
                           pit_lap_1, pit_lap_2):

    lap_numbers = []

    lap_times = []

    tyre_age = 0

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

        lap_numbers.append(lap)

        lap_times.append(lap_time)

        tyre_age = tyre_age + 1

        # Reset tyre age after first pit
        if lap == pit_lap_1:

            tyre_age = 0

        # Reset tyre age after second pit
        if lap == pit_lap_2:

            tyre_age = 0

    return lap_numbers, lap_times


# =============================================================
# FUNCTION: ONE-STOP CUMULATIVE TIME
# =============================================================

def cumulative_one_stop(first_base, first_deg,
                        second_base, second_deg,
                        pit_lap):

    lap_numbers = []

    cumulative_times = []

    total_time = 0.0

    tyre_age = 0

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

        # Pit stop
        if lap == pit_lap:

            total_time = total_time + pit_loss

            tyre_age = 0

        lap_numbers.append(lap)

        cumulative_times.append(total_time)

    return lap_numbers, cumulative_times


# =============================================================
# FUNCTION: TWO-STOP CUMULATIVE TIME
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

        lap_numbers.append(lap)

        cumulative_times.append(total_time)

    return lap_numbers, cumulative_times


# =============================================================
# ONE-STOP STRATEGIES
# =============================================================


# -----------------------------
# Soft -> Medium
# -----------------------------

soft_medium = calculate_strategy(
    soft_base_time,
    soft_degradation,
    medium_base_time,
    medium_degradation
)

soft_medium_pit = soft_medium[0]

soft_medium_time = soft_medium[1]

soft_medium_pit_laps = soft_medium[2]

soft_medium_race_times = soft_medium[3]


# -----------------------------
# Soft -> Hard
# -----------------------------

soft_hard = calculate_strategy(
    soft_base_time,
    soft_degradation,
    hard_base_time,
    hard_degradation
)

soft_hard_pit = soft_hard[0]

soft_hard_time = soft_hard[1]

soft_hard_pit_laps = soft_hard[2]

soft_hard_race_times = soft_hard[3]


# -----------------------------
# Medium -> Hard
# -----------------------------

medium_hard = calculate_strategy(
    medium_base_time,
    medium_degradation,
    hard_base_time,
    hard_degradation
)

medium_hard_pit = medium_hard[0]

medium_hard_time = medium_hard[1]

medium_hard_pit_laps = medium_hard[2]

medium_hard_race_times = medium_hard[3]


# =============================================================
# FIND BEST ONE-STOP STRATEGY
# =============================================================

best_one_stop_time = min(
    soft_medium_time,
    soft_hard_time,
    medium_hard_time
)


if best_one_stop_time == soft_medium_time:

    best_one_stop_name = "Soft -> Medium"

    best_one_stop_pit = soft_medium_pit

    best_one_first_base = soft_base_time
    best_one_first_deg = soft_degradation

    best_one_second_base = medium_base_time
    best_one_second_deg = medium_degradation


elif best_one_stop_time == soft_hard_time:

    best_one_stop_name = "Soft -> Hard"

    best_one_stop_pit = soft_hard_pit

    best_one_first_base = soft_base_time
    best_one_first_deg = soft_degradation

    best_one_second_base = hard_base_time
    best_one_second_deg = hard_degradation


else:

    best_one_stop_name = "Medium -> Hard"

    best_one_stop_pit = medium_hard_pit

    best_one_first_base = medium_base_time
    best_one_first_deg = medium_degradation

    best_one_second_base = hard_base_time
    best_one_second_deg = hard_degradation


# =============================================================
# TWO-STOP STRATEGIES
# =============================================================


# -----------------------------
# Soft -> Medium -> Hard
# -----------------------------

soft_medium_hard = calculate_two_stop_strategy(
    soft_base_time,
    soft_degradation,
    medium_base_time,
    medium_degradation,
    hard_base_time,
    hard_degradation
)

smh_pit_1 = soft_medium_hard[0]

smh_pit_2 = soft_medium_hard[1]

smh_time = soft_medium_hard[2]


# -----------------------------
# Soft -> Medium -> Medium
# -----------------------------

soft_medium_medium = calculate_two_stop_strategy(
    soft_base_time,
    soft_degradation,
    medium_base_time,
    medium_degradation,
    medium_base_time,
    medium_degradation
)

smm_pit_1 = soft_medium_medium[0]

smm_pit_2 = soft_medium_medium[1]

smm_time = soft_medium_medium[2]


# -----------------------------
# Soft -> Soft -> Medium
# -----------------------------

soft_soft_medium = calculate_two_stop_strategy(
    soft_base_time,
    soft_degradation,
    soft_base_time,
    soft_degradation,
    medium_base_time,
    medium_degradation
)

ssm_pit_1 = soft_soft_medium[0]

ssm_pit_2 = soft_soft_medium[1]

ssm_time = soft_soft_medium[2]


# -----------------------------
# Medium -> Medium -> Hard
# -----------------------------

medium_medium_hard = calculate_two_stop_strategy(
    medium_base_time,
    medium_degradation,
    medium_base_time,
    medium_degradation,
    hard_base_time,
    hard_degradation
)

mmh_pit_1 = medium_medium_hard[0]

mmh_pit_2 = medium_medium_hard[1]

mmh_time = medium_medium_hard[2]


# =============================================================
# FIND BEST TWO-STOP STRATEGY
# =============================================================

best_two_stop_time = min(
    smh_time,
    smm_time,
    ssm_time,
    mmh_time
)


if best_two_stop_time == smh_time:

    best_two_stop_name = "Soft -> Medium -> Hard"

    best_two_stop_pit_1 = smh_pit_1
    best_two_stop_pit_2 = smh_pit_2

    best_two_first_base = soft_base_time
    best_two_first_deg = soft_degradation

    best_two_second_base = medium_base_time
    best_two_second_deg = medium_degradation

    best_two_third_base = hard_base_time
    best_two_third_deg = hard_degradation


elif best_two_stop_time == smm_time:

    best_two_stop_name = "Soft -> Medium -> Medium"

    best_two_stop_pit_1 = smm_pit_1
    best_two_stop_pit_2 = smm_pit_2

    best_two_first_base = soft_base_time
    best_two_first_deg = soft_degradation

    best_two_second_base = medium_base_time
    best_two_second_deg = medium_degradation

    best_two_third_base = medium_base_time
    best_two_third_deg = medium_degradation


elif best_two_stop_time == ssm_time:

    best_two_stop_name = "Soft -> Soft -> Medium"

    best_two_stop_pit_1 = ssm_pit_1
    best_two_stop_pit_2 = ssm_pit_2

    best_two_first_base = soft_base_time
    best_two_first_deg = soft_degradation

    best_two_second_base = soft_base_time
    best_two_second_deg = soft_degradation

    best_two_third_base = medium_base_time
    best_two_third_deg = medium_degradation


else:

    best_two_stop_name = "Medium -> Medium -> Hard"

    best_two_stop_pit_1 = mmh_pit_1
    best_two_stop_pit_2 = mmh_pit_2

    best_two_first_base = medium_base_time
    best_two_first_deg = medium_degradation

    best_two_second_base = medium_base_time
    best_two_second_deg = medium_degradation

    best_two_third_base = hard_base_time
    best_two_third_deg = hard_degradation


# =============================================================
# LAP-TIME TRACES FOR BEST STRATEGIES
# =============================================================

best_one_stop_laps, best_one_stop_lap_times = simulate_best_one_stop(
    best_one_first_base,
    best_one_first_deg,
    best_one_second_base,
    best_one_second_deg,
    best_one_stop_pit
)


best_two_stop_laps, best_two_stop_lap_times = simulate_best_two_stop(
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
# CUMULATIVE TIMES FOR BEST STRATEGIES
# =============================================================

one_stop_cumulative_laps, one_stop_cumulative_times = cumulative_one_stop(
    best_one_first_base,
    best_one_first_deg,
    best_one_second_base,
    best_one_second_deg,
    best_one_stop_pit
)


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
# PRINT RESULTS
# =============================================================

print("ONE-STOP STRATEGIES")

print()

print("Soft -> Medium")
print("Best pit lap:", soft_medium_pit)
print(f"Best race time: {soft_medium_time:.1f} seconds")

print()

print("Soft -> Hard")
print("Best pit lap:", soft_hard_pit)
print(f"Best race time: {soft_hard_time:.1f} seconds")

print()

print("Medium -> Hard")
print("Best pit lap:", medium_hard_pit)
print(f"Best race time: {medium_hard_time:.1f} seconds")


print()
print("----------------------------------")
print()


print("TWO-STOP STRATEGIES")

print()

print("Soft -> Medium -> Hard")
print("Pit 1:", smh_pit_1)
print("Pit 2:", smh_pit_2)
print(f"Race time: {smh_time:.1f} seconds")

print()

print("Soft -> Medium -> Medium")
print("Pit 1:", smm_pit_1)
print("Pit 2:", smm_pit_2)
print(f"Race time: {smm_time:.1f} seconds")

print()

print("Soft -> Soft -> Medium")
print("Pit 1:", ssm_pit_1)
print("Pit 2:", ssm_pit_2)
print(f"Race time: {ssm_time:.1f} seconds")

print()

print("Medium -> Medium -> Hard")
print("Pit 1:", mmh_pit_1)
print("Pit 2:", mmh_pit_2)
print(f"Race time: {mmh_time:.1f} seconds")


print()
print("----------------------------------")
print()


print("BEST ONE-STOP STRATEGY")

print("Strategy:", best_one_stop_name)
print("Pit lap:", best_one_stop_pit)
print(f"Race time: {best_one_stop_time:.1f} seconds")


print()

print("BEST TWO-STOP STRATEGY")

print("Strategy:", best_two_stop_name)
print("Pit 1:", best_two_stop_pit_1)
print("Pit 2:", best_two_stop_pit_2)
print(f"Race time: {best_two_stop_time:.1f} seconds")


print()
print("----------------------------------")
print()


# =============================================================
# FINAL STRATEGY COMPARISON
# =============================================================

if best_two_stop_time < best_one_stop_time:

    time_saved = best_one_stop_time - best_two_stop_time

    print("Best overall strategy:", best_two_stop_name)

    print("Strategy type: Two-stop")

    print(f"Time saved: {time_saved:.1f} seconds")


else:

    time_saved = best_two_stop_time - best_one_stop_time

    print("Best overall strategy:", best_one_stop_name)

    print("Strategy type: One-stop")

    print(f"Time saved: {time_saved:.1f} seconds")


# =============================================================
# GRAPH 1
# ONE-STOP STRATEGY OPTIMISATION
# =============================================================

plt.figure(figsize=(10, 6))

plt.plot(
    soft_medium_pit_laps,
    soft_medium_race_times,
    label="Soft -> Medium"
)

plt.plot(
    soft_hard_pit_laps,
    soft_hard_race_times,
    label="Soft -> Hard"
)

plt.plot(
    medium_hard_pit_laps,
    medium_hard_race_times,
    label="Medium -> Hard"
)

plt.xlabel("Pit Lap")

plt.ylabel("Total Race Time (seconds)")

plt.title("One-Stop Strategy Comparison")

plt.legend()

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
# ONE-STOP VS TWO-STOP LAP-TIME COMPARISON
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

plt.title("Best One-Stop vs Two-Stop Lap-Time Comparison")

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

plt.title("One-Stop vs Two-Stop Cumulative Race Time")

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

plt.title("Best Two-Stop vs Best One-Stop Time Gap")

plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

plt.show()