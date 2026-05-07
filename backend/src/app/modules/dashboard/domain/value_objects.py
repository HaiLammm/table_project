from enum import StrEnum


class PatternType(StrEnum):
    TIME_OF_DAY_PATTERN = "time_of_day_pattern"
    CATEGORY_SPECIFIC_WEAKNESS = "category_specific_weakness"
    CROSS_LANGUAGE_INTERFERENCE = "cross_language_interference"
    RESPONSE_TIME_ANOMALY = "response_time_anomaly"
    SESSION_LENGTH_EFFECT = "session_length_effect"
    DAY_OF_WEEK_PATTERN = "day_of_week_pattern"
