from enum import Enum


class TripState(str, Enum):
    ONGOING: str = "Ongoing"
    FINISHED: str = "Finished"
