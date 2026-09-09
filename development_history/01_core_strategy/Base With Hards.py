import matplotlib.pyplot as plt

# -----------------------------
# Race inputs
# -----------------------------

race_laps = 50
pit_loss = 22.0

# Tyre data
soft_base_time = 89.0
soft_degradation = 0.20

medium_base_time = 90.0
medium_degradation = 0.10

hard_base_time = 92.0
hard_degradation = 0.05


# -----------------------------
# Function to test one strategy
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
                lap_time = first_base + first_deg * tyre_age

            # Second tyre after pit stop
            else:
                lap_time = second_base + second_deg * tyre_age

            total_time = total_time + lap_time

            tyre_age = tyre_age + 1

            # Pit stop
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


# -----------------------------
# Print results
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
# Find best overall strategy
# -----------------------------

best_overall_time = min(
    soft_medium_time,
    soft_hard_time,
    medium_hard_time
)

if best_overall_time == soft_medium_time:
    print()
    print("Best overall strategy: Soft -> Medium")

elif best_overall_time == soft_hard_time:
    print()
    print("Best overall strategy: Soft -> Hard")

else:
    print()
    print("Best overall strategy: Medium -> Hard")


# -----------------------------
# Plot all strategies
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
plt.title("One-Stop Strategy Comparison")

plt.legend()

plt.show()