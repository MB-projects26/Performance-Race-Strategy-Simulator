"""Core lap-time, tyre and fuel model."""

import config


def is_safety_car_lap(lap, safety_car_start=None, safety_car_end=None):
    if safety_car_start is None or safety_car_end is None:
        return False
    return safety_car_start <= lap <= safety_car_end


def calculate_pit_loss(lap, safety_car_start=None, safety_car_end=None,
                       normal_pit_loss=None):
    if is_safety_car_lap(lap, safety_car_start, safety_car_end):
        return config.SAFETY_CAR_PIT_LOSS
    if normal_pit_loss is None:
        normal_pit_loss = config.NORMAL_PIT_LOSS
    return normal_pit_loss


def calculate_fuel_mass(lap):
    fuel_mass = (
        config.INITIAL_FUEL_MASS
        - config.FUEL_BURN_PER_LAP * (lap - 1)
    )
    return max(0.0, fuel_mass)


def calculate_fuel_time_gain(lap):
    fuel_burned = config.INITIAL_FUEL_MASS - calculate_fuel_mass(lap)
    return fuel_burned * config.FUEL_TIME_PER_KG


def calculate_fuel_wear_increment(lap, safety_car_start=None,
                                   safety_car_end=None):
    fuel_fraction = calculate_fuel_mass(lap) / config.INITIAL_FUEL_MASS
    increment = 1.0 + config.FUEL_WEAR_SENSITIVITY * fuel_fraction
    if is_safety_car_lap(lap, safety_car_start, safety_car_end):
        increment *= config.SAFETY_CAR_TYRE_WEAR_MULTIPLIER
    return increment


def calculate_cliff_penalty(tyre_wear, cliff_threshold, cliff_severity):
    if tyre_wear <= cliff_threshold:
        return 0.0
    excess = tyre_wear - cliff_threshold
    return cliff_severity * excess ** 2


def calculate_tyre_loss(tyre_data, tyre_wear, degradation_scale=None):
    linear = tyre_data[1]
    quadratic = tyre_data[2]
    cliff = calculate_cliff_penalty(tyre_wear, tyre_data[5], tyre_data[6])
    normal_loss = linear * tyre_wear + quadratic * tyre_wear ** 2
    if degradation_scale is None:
        degradation_scale = config.TYRE_DEGRADATION_SCALE
    return (normal_loss + cliff) * degradation_scale


def calculate_warmup_penalty(tyre_data, tyre_age):
    penalty = tyre_data[3] - tyre_data[4] * tyre_age
    return max(0.0, penalty)


def calculate_lap_time(tyre_data, tyre_age, tyre_wear, lap,
                       safety_car_start=None, safety_car_end=None,
                       pace_offset=0.0, degradation_scale=None):
    if is_safety_car_lap(lap, safety_car_start, safety_car_end):
        return config.SAFETY_CAR_LAP_TIME

    return (
        tyre_data[0]
        + calculate_tyre_loss(tyre_data, tyre_wear, degradation_scale)
        + calculate_warmup_penalty(tyre_data, tyre_age)
        - calculate_fuel_time_gain(lap)
        + pace_offset
    )
