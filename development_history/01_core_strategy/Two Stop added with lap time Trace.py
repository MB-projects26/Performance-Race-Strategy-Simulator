import matplotlib.pyplot as plt

# -----------------------------
# Race inputs
# -----------------------------

race_laps = 50
pit_loss = 22.0
fuel_effect = 0.06

# Tyre data
soft_base_time = 89.0
soft_degradation = 0.20

medium_base_time = 90.0
medium_degradation = 0.10

hard_base_time = 92.0
hard_degradation = 0.05


# -----------------------------
# Function to test one-stop strategy
# -----------------------------

def calculate_strategy(first_base, first_deg,
                       second_base, second_deg):

    pit_laps = []
    race_times = []

    # Test every possible pit lap
    for pit_lap in range(2, race_laps):

        total_time = 0.0
        tyre_age = 0

        # Simulate the race lap by lap
        for lap in range(1, race_laps + 1):

            # First tyre before pit stop
            if lap <= pit_lap:
                lap_time = (
                    first_base
                    + first_deg * tyre_age
                    - fuel_effect * (lap - 1)
                )

            # Second tyre after pit stop
            else:
                lap_time = (
                    second_base
                    + second_deg * tyre_age
                    - fuel_effect * (lap - 1)
                )

            total_time = total_time + lap_time
            tyre_age = tyre_age + 1

            # Pit stop at the end of the chosen lap
            if lap == pit_lap:
                total_time = total_time + pit_loss
                tyre_age = 0

        # Save this strategy result
        pit_laps.append(pit_lap)
        race_times.append(total_time)

    # Find fastest pit lap
    best_time = min(race_times)

    best_index = race_times.index(best_time)

    best_pit_lap = pit_laps[best_index]

    return best_pit_lap, best_time, pit_laps, race_times


# -----------------------------
# Function to test two-stop strategy
# -----------------------------

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

            # Check if this is the fastest strategy so far
            if best_time is None or total_time < best_time:
                best_time = total_time
                best_pit_1 = pit_lap_1
                best_pit_2 = pit_lap_2

    return best_pit_1, best_pit_2, best_time

# -----------------------------
# Function to simulate lap times
# for the best one-stop strategy
# -----------------------------

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

# -----------------------------
# Function to simulate lap times
# for a two-stop strategy
# -----------------------------

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

        # Reset tyre age after each pit stop
        if lap == pit_lap_1:
            tyre_age = 0

        if lap == pit_lap_2:
            tyre_age = 0

    return lap_numbers, lap_times


# -----------------------------
# One-stop: Soft -> Medium
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

# Simulate the lap times for the best Soft -> Medium strategy

best_one_stop_laps, best_one_stop_lap_times = simulate_best_one_stop(
    soft_base_time,
    soft_degradation,
    medium_base_time,
    medium_degradation,
    soft_medium_pit
)


# -----------------------------
# One-stop: Soft -> Hard
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
# One-stop: Medium -> Hard
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


# -----------------------------
# Two-stop: Soft -> Medium -> Hard
# -----------------------------

soft_medium_hard = calculate_two_stop_strategy(
    soft_base_time,
    soft_degradation,
    medium_base_time,
    medium_degradation,
    hard_base_time,
    hard_degradation
)

two_stop_pit_1 = soft_medium_hard[0]
two_stop_pit_2 = soft_medium_hard[1]
two_stop_time = soft_medium_hard[2]

best_two_stop_laps, best_two_stop_lap_times = simulate_best_two_stop(
    soft_base_time,
    soft_degradation,
    medium_base_time,
    medium_degradation,
    hard_base_time,
    hard_degradation,
    two_stop_pit_1,
    two_stop_pit_2
)


# -----------------------------
# Print one-stop results
# -----------------------------

print("Soft -> Medium")
print("Best pit lap:", soft_medium_pit)
print("Best race time:", soft_medium_time, "seconds")

print()

print("Soft -> Hard")
print("Best pit lap:", soft_hard_pit)
print("Best race time:", soft_hard_time, "seconds")

print()

print("Medium -> Hard")
print("Best pit lap:", medium_hard_pit)
print("Best race time:", medium_hard_time, "seconds")


# -----------------------------
# Print two-stop result
# -----------------------------

print()

print("Soft -> Medium -> Hard")
print("Best first pit lap:", two_stop_pit_1)
print("Best second pit lap:", two_stop_pit_2)
print("Best race time:", two_stop_time, "seconds")


# -----------------------------
# Find best one-stop strategy
# -----------------------------

best_one_stop_time = min(
    soft_medium_time,
    soft_hard_time,
    medium_hard_time
)

if best_one_stop_time == soft_medium_time:
    print()
    print("Best one-stop strategy: Soft -> Medium")

elif best_one_stop_time == soft_hard_time:
    print()
    print("Best one-stop strategy: Soft -> Hard")

else:
    print()
    print("Best one-stop strategy: Medium -> Hard")

print("Best one-stop race time:", best_one_stop_time, "seconds")


# -----------------------------
# Compare one-stop and two-stop
# -----------------------------

print()

if two_stop_time < best_one_stop_time:
    print("Two-stop strategy is faster")
    print(
        "Time saved:",
        best_one_stop_time - two_stop_time,
        "seconds"
    )

else:
    print("One-stop strategy is faster")
    print(
        "Time saved:",
        two_stop_time - best_one_stop_time,
        "seconds"
    )


# -----------------------------
# Plot one-stop strategies
# -----------------------------

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
plt.title("One-Stop Strategy Comparison with Fuel Effect")

plt.legend()

plt.show()
# -----------------------------
# Plot lap-time trace
# -----------------------------

plt.plot(
    best_one_stop_laps,
    best_one_stop_lap_times,
    label="Lap Time"
)

plt.axvline(
    soft_medium_pit,
    linestyle="--",
    label="Pit Stop"
)

plt.xlabel("Race Lap")
plt.ylabel("Lap Time (seconds)")
plt.title("Best Soft -> Medium Lap Time Trace")

plt.legend()

plt.show()

# -----------------------------
# Plot two-stop lap-time trace
# -----------------------------

plt.plot(
    best_two_stop_laps,
    best_two_stop_lap_times,
    label="Lap Time"
)

plt.axvline(
    two_stop_pit_1,
    linestyle="--",
    label="Pit Stop 1"
)

plt.axvline(
    two_stop_pit_2,
    linestyle="--",
    label="Pit Stop 2"
)

plt.xlabel("Race Lap")
plt.ylabel("Lap Time (seconds)")
plt.title("Best Soft -> Medium -> Hard Lap Time Trace")

plt.legend()

plt.show()

plt.figure(figsize=(10, 6))

plt.plot(
    best_one_stop_laps,
    best_one_stop_lap_times,
    label="One Stop: Soft -> Medium"
)

plt.plot(
    best_two_stop_laps,
    best_two_stop_lap_times,
    label="Two Stop: Soft -> Medium -> Hard"
)

# One-stop pit
plt.axvline(
    soft_medium_pit,
    linestyle="--",
    label="One-Stop Pit"
)

# Two-stop pits
plt.axvline(
    two_stop_pit_1,
    linestyle="--",
    label="Two-Stop Pit 1"
)

plt.axvline(
    two_stop_pit_2,
    linestyle="--",
    label="Two-Stop Pit 2"
)

plt.xlabel("Race Lap")
plt.ylabel("Lap Time (seconds)")
plt.title("Best One-Stop vs Two-Stop Lap Time Comparison")

plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()

plt.show()