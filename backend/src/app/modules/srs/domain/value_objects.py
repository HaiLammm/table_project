import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import cast

from fsrs import Card
from fsrs import Rating as FsrsRating


class QueueMode(StrEnum):
    FULL = "full"
    CATCHUP = "catchup"


class Rating(StrEnum):
    AGAIN = "again"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"

    @classmethod
    def from_score(cls, score: int) -> "Rating":
        score_map = {
            1: cls.AGAIN,
            2: cls.HARD,
            3: cls.GOOD,
            4: cls.EASY,
        }
        return score_map[score]

    def to_score(self) -> int:
        score_map = {
            Rating.AGAIN: 1,
            Rating.HARD: 2,
            Rating.GOOD: 3,
            Rating.EASY: 4,
        }
        return score_map[self]

    def to_fsrs(self) -> FsrsRating:
        return FsrsRating(self.to_score())


class FSRSState:
    @staticmethod
    def from_card(card: Card) -> dict[str, object]:
        return cast(dict[str, object], json.loads(card.to_json()))

    @staticmethod
    def to_card(
        state: dict[str, object],
        *,
        fallback_due_at: datetime | None = None,
    ) -> Card:
        if not state or any(key not in state for key in ("card_id", "state", "due")):
            return Card(due=fallback_due_at or datetime.now(UTC))

        return Card.from_json(json.dumps(state))
