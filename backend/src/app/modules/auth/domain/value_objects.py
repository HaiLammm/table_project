from enum import StrEnum
from typing import Final


class UserTier(StrEnum):
    FREE = "free"
    STUDENT = "student"
    PROFESSIONAL = "professional"


class LearningGoal(StrEnum):
    JLPT_PREP = "jlpt_prep"
    TOEIC_PREP = "toeic_prep"
    WORKPLACE = "workplace"
    GENERAL = "general"


class EnglishLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class JapaneseLevel(StrEnum):
    NONE = "none"
    N5 = "n5"
    N4 = "n4"
    N3 = "n3"
    N2 = "n2"
    N1 = "n1"


class ITDomain(StrEnum):
    WEB_DEV = "web_dev"
    BACKEND = "backend"
    NETWORKING = "networking"
    DATA = "data"
    GENERAL_IT = "general_it"


DEFAULT_LEARNING_GOAL: Final = LearningGoal.GENERAL
DEFAULT_ENGLISH_LEVEL: Final = EnglishLevel.BEGINNER
DEFAULT_JAPANESE_LEVEL: Final = JapaneseLevel.NONE
DEFAULT_DAILY_STUDY_MINUTES: Final = 15
DEFAULT_IT_DOMAIN: Final = ITDomain.GENERAL_IT
DEFAULT_NOTIFICATION_EMAIL: Final = True
DEFAULT_NOTIFICATION_REVIEW_REMINDER: Final = True
ALLOWED_DAILY_STUDY_MINUTES: Final[frozenset[int]] = frozenset({5, 15, 30, 60})
