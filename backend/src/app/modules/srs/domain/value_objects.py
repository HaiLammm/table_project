from enum import StrEnum


class QueueMode(StrEnum):
    FULL = "full"
    CATCHUP = "catchup"
