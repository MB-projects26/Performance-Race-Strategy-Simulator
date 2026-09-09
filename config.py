"""Configuration and modelling assumptions for the race strategy simulator.

The values in this file are intentionally easy to inspect and edit. Unless a
value is explicitly reported as calibrated from real data, treat it as a model
assumption rather than a measured Formula 1 parameter.
"""

RACE_LAPS = 50
NORMAL_PIT_LOSS = 22.0
MINIMUM_STINT = 5

INITIAL_FUEL_MASS = 100.0
FUEL_BURN_PER_LAP = 2.0
FUEL_TIME_PER_KG = 0.03
FUEL_WEAR_SENSITIVITY = 0.25
TYRE_DEGRADATION_SCALE = 1.0

SAFETY_CAR_PROBABILITY = 0.40
SAFETY_CAR_MIN_START = 5
SAFETY_CAR_MAX_START = 45
SAFETY_CAR_MIN_DURATION = 2
SAFETY_CAR_MAX_DURATION = 5
SAFETY_CAR_LAP_TIME = 120.0
SAFETY_CAR_PIT_LOSS = 10.0
SAFETY_CAR_TYRE_WEAR_MULTIPLIER = 0.35
MONTE_CARLO_RUNS = 1000
RANDOM_SEED = 42

DIRTY_AIR_ENABLED = True
DIRTY_AIR_RANGE = 1.5
DIRTY_AIR_MAX_PENALTY = 0.65
OVERTAKE_MARGIN = 0.25
MINIMUM_FOLLOWING_GAP = 0.15

# Generic overtaking-aid model. This is not intended to reproduce the exact
# regulations of a particular championship season.
DRS_ENABLED = True
DRS_ACTIVATION_LAP = 3
DRS_DETECTION_RANGE = 1.0
DRS_TIME_GAIN = 0.45
DRS_OVERTAKE_MARGIN_REDUCTION = 0.15

# Tuple layout:
# base lap time, linear deg, quadratic deg, warm-up penalty, warm-up recovery,
# cliff threshold, cliff severity
TYRES = {
    "Soft": (89.0, 0.10, 0.006, 0.30, 0.15, 18.0, 0.04),
    "Medium": (90.0, 0.06, 0.0025, 0.50, 0.15, 28.0, 0.02),
    "Hard": (92.0, 0.03, 0.001, 0.70, 0.15, 38.0, 0.01),
}

FIELD_CONFIGURATION = [
    {"name": "Leader", "start_gap": 0.0,
     "tyre_sequence": ["Medium", "Soft"], "pit_laps": [31],
     "pace_offset": -0.05},
    {"name": "Car B", "start_gap": 0.8,
     "tyre_sequence": ["Medium", "Soft"], "pit_laps": [30],
     "pace_offset": 0.03},
    {"name": "Our Car", "start_gap": 1.4,
     "tyre_sequence": ["Medium", "Soft"], "pit_laps": [29],
     "pace_offset": 0.0},
    {"name": "Car D", "start_gap": 2.0,
     "tyre_sequence": ["Medium", "Soft"], "pit_laps": [28],
     "pace_offset": 0.08},
    {"name": "Car E", "start_gap": 2.7,
     "tyre_sequence": ["Hard", "Soft"], "pit_laps": [34],
     "pace_offset": 0.06},
    {"name": "Car F", "start_gap": 3.4,
     "tyre_sequence": ["Medium", "Hard"], "pit_laps": [26],
     "pace_offset": 0.15},
]
FIELD_PIT_SEARCH_START = 24
FIELD_PIT_SEARCH_END = 34

# Real-world validation settings
REAL_VALIDATION_YEAR = 2024
REAL_VALIDATION_EVENT = "Austria"
REAL_VALIDATION_SESSION = "R"
REAL_VALIDATION_COMPOUND = "AUTO"
REAL_REQUIRE_FRESH_TYRE = True
REAL_MINIMUM_CLEAN_LAPS = 7
REAL_MINIMUM_TYRE_AGE = 2
REAL_MAXIMUM_VALIDATION_STINTS = 10
REAL_OUTLIER_THRESHOLD = 1.50
REAL_OUTLIER_WINDOW = 2

REAL_LINEAR_MIN = 0.000
REAL_LINEAR_MAX = 0.150
REAL_LINEAR_STEP = 0.005
REAL_QUADRATIC_MIN = 0.000
REAL_QUADRATIC_MAX = 0.008
REAL_QUADRATIC_STEP = 0.00025

# Keep False for the portfolio baseline. The calibrated Austria coefficients
# are event-specific and validate relative stint evolution, not universal pace.
APPLY_REAL_CALIBRATION_TO_STRATEGY_MODEL = False
