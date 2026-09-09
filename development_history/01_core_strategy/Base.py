import matplotlib.pyplot as plt

race_laps = 50
pit_loss = 22.0

soft_base_time = 89.0
soft_degradation = 0.50

medium_base_time = 90.0
medium_degradation = 0.10

pit_laps = []
race_times = []

for pit_lap in range(2, race_laps):

    total_time = 0.0
    tyre_age = 0

    for lap in range(1, race_laps + 1):

        # Before the pit stop: Soft tyres
        if lap <= pit_lap:
            lap_time = soft_base_time + soft_degradation * tyre_age

        # After the pit stop: Medium tyres
        else:
            lap_time = medium_base_time + medium_degradation * tyre_age

        total_time = total_time + lap_time

        tyre_age = tyre_age + 1

        # Pit at the end of the chosen lap
        if lap == pit_lap:
            total_time = total_time + pit_loss
            tyre_age = 0

    pit_laps.append(pit_lap)
    race_times.append(total_time)


best_time = min(race_times)

best_index = race_times.index(best_time)

best_pit_lap = pit_laps[best_index]


print("Best pit lap:", best_pit_lap)

print("Best race time:", best_time, "seconds")


plt.plot(pit_laps, race_times)

plt.xlabel("Pit Lap")
plt.ylabel("Total Race Time (seconds)")
plt.title("Soft to Medium Strategy")

plt.show()

