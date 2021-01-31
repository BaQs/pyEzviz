"""Defense mode types relationship."""
from enum import Enum, unique


@unique
class DefenseModeType(Enum):
    """Defense mode name and number."""

    HOME_MODE = 1
    AWAY_MODE = 2
