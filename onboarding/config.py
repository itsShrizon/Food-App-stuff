"""Configuration constants for the onboarding module."""

# Core required fields for onboarding (matching DB structure)
ONBOARDING_FIELDS = (
    'gender', 'date_of_birth',
    'current_height', 'current_height_unit',
    'current_weight', 'current_weight_unit',
    'target_weight', 'target_weight_unit',
    'goal', 'target_speed', 'activity_level',
)

# Dietary preference flags (nested object in DB)
DIETARY_PREFERENCE_FLAGS = (
    'vegan', 'dairy_free', 'gluten_free', 'nut_free', 'pescatarian'
)

# Activity level multipliers for TDEE calculation
ACTIVITY_MULTIPLIERS = {
    'sedentary': 1.2,
    'light': 1.375,
    'moderate': 1.55,
    'active': 1.725,
}

# Target speed rates (kg per week)
TARGET_SPEED_RATES = {
    'slow': 0.25,
    'normal': 0.5,
    'fast': 0.75,
}

# Valid values for validation
VALID_GENDERS = ('male', 'female', 'others')
VALID_GOALS = ('lose_weight', 'maintain', 'gain_weight')
VALID_HEIGHT_UNITS = ('cm', 'in')
VALID_WEIGHT_UNITS = ('kg', 'lb')
