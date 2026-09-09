"""Simplified multi-car traffic, dirty-air and overtaking model."""

import copy

import config
from model import calculate_lap_time, calculate_fuel_wear_increment


def calculate_dirty_air_penalty(gap_to_car_ahead):
    if not config.DIRTY_AIR_ENABLED:
        return 0.0
    if gap_to_car_ahead <= 0 or gap_to_car_ahead > config.DIRTY_AIR_RANGE:
        return 0.0
    gap_fraction = gap_to_car_ahead / config.DIRTY_AIR_RANGE
    return config.DIRTY_AIR_MAX_PENALTY * (1.0 - gap_fraction)


def calculate_drs_gain(lap, gap_to_car_ahead):
    if not config.DRS_ENABLED:
        return 0.0
    if lap < config.DRS_ACTIVATION_LAP:
        return 0.0
    if gap_to_car_ahead <= 0 or gap_to_car_ahead > config.DRS_DETECTION_RANGE:
        return 0.0
    return config.DRS_TIME_GAIN


def calculate_required_overtake_margin(current_drs_gain):
    margin = config.OVERTAKE_MARGIN
    if current_drs_gain > 0:
        margin -= config.DRS_OVERTAKE_MARGIN_REDUCTION
    return max(0.0, margin)


def copy_field_configuration(our_pit_lap):
    field = copy.deepcopy(config.FIELD_CONFIGURATION)
    for car in field:
        if car["name"] == "Our Car":
            car["pit_laps"] = [our_pit_lap]
    return field


def simulate_small_field(our_pit_lap):
    field = copy_field_configuration(our_pit_lap)
    states = {
        car["name"]: {
            "total_time": car["start_gap"],
            "tyre_age": 0,
            "tyre_wear": 0.0,
            "stint": 0,
        }
        for car in field
    }

    position_history = []
    dirty_air_history = []
    drs_history = []
    overtaking_events = []
    pit_rejoin_positions = {}

    for lap in range(1, config.RACE_LAPS + 1):
        running_order = sorted(
            field,
            key=lambda car: states[car["name"]]["total_time"],
        )

        effective_lap_times = {}
        dirty_air_penalties = {}
        drs_gains = {}
        cars_pitting = {}

        for index, car in enumerate(running_order):
            name = car["name"]
            state = states[name]
            tyre_name = car["tyre_sequence"][state["stint"]]

            lap_time = calculate_lap_time(
                config.TYRES[tyre_name],
                state["tyre_age"],
                state["tyre_wear"],
                lap,
                pace_offset=car["pace_offset"],
            )

            dirty_air_penalty = 0.0
            current_drs_gain = 0.0

            if index > 0:
                ahead_name = running_order[index - 1]["name"]
                gap = state["total_time"] - states[ahead_name]["total_time"]
                dirty_air_penalty = calculate_dirty_air_penalty(gap)
                current_drs_gain = calculate_drs_gain(lap, gap)
                lap_time += dirty_air_penalty
                lap_time -= current_drs_gain

            is_pitting = lap in car["pit_laps"]
            effective_time = lap_time + (config.NORMAL_PIT_LOSS if is_pitting else 0.0)

            effective_lap_times[name] = effective_time
            dirty_air_penalties[name] = dirty_air_penalty
            drs_gains[name] = current_drs_gain
            cars_pitting[name] = is_pitting

        predicted_times = {
            car["name"]: states[car["name"]]["total_time"]
            + effective_lap_times[car["name"]]
            for car in field
        }
        adjusted_times = predicted_times.copy()

        # Pairwise pass restriction using the start-of-lap order.
        for index in range(1, len(running_order)):
            following_name = running_order[index]["name"]
            ahead_name = running_order[index - 1]["name"]

            if cars_pitting[following_name] or cars_pitting[ahead_name]:
                continue

            if adjusted_times[following_name] < adjusted_times[ahead_name]:
                pace_advantage = (
                    effective_lap_times[ahead_name]
                    - effective_lap_times[following_name]
                )
                required_margin = calculate_required_overtake_margin(
                    drs_gains[following_name]
                )

                if pace_advantage < required_margin:
                    adjusted_times[following_name] = (
                        adjusted_times[ahead_name]
                        + config.MINIMUM_FOLLOWING_GAP
                    )
                else:
                    overtaking_events.append((lap, following_name, ahead_name))

        for car in field:
            name = car["name"]
            states[name]["total_time"] = adjusted_times[name]

        wear_increment = calculate_fuel_wear_increment(lap)
        for car in field:
            name = car["name"]
            states[name]["tyre_age"] += 1
            states[name]["tyre_wear"] += wear_increment

            if cars_pitting[name]:
                states[name]["tyre_age"] = 0
                states[name]["tyre_wear"] = 0.0
                states[name]["stint"] += 1

        new_order = sorted(
            field,
            key=lambda car: states[car["name"]]["total_time"],
        )
        order_names = [car["name"] for car in new_order]
        our_position = order_names.index("Our Car") + 1
        position_history.append(our_position)
        dirty_air_history.append(dirty_air_penalties["Our Car"])
        drs_history.append(drs_gains["Our Car"])

        if cars_pitting["Our Car"]:
            pit_rejoin_positions[lap] = our_position

    final_order_raw = sorted(
        field,
        key=lambda car: states[car["name"]]["total_time"],
    )
    final_order = [
        (car["name"], states[car["name"]]["total_time"])
        for car in final_order_raw
    ]
    final_names = [name for name, _ in final_order]

    return {
        "final_position": final_names.index("Our Car") + 1,
        "our_final_time": states["Our Car"]["total_time"],
        "final_order": final_order,
        "position_history": position_history,
        "dirty_air_history": dirty_air_history,
        "drs_history": drs_history,
        "pit_rejoin_positions": pit_rejoin_positions,
        "overtaking_events": overtaking_events,
    }


def find_best_field_pit():
    results = []
    for candidate_pit in range(
        config.FIELD_PIT_SEARCH_START,
        config.FIELD_PIT_SEARCH_END + 1,
    ):
        result = simulate_small_field(candidate_pit)
        results.append((candidate_pit, result))

    best = min(
        results,
        key=lambda item: (
            item[1]["final_position"],
            item[1]["our_final_time"],
        ),
    )
    return best[0], best[1], results
