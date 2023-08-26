import time
import math


class Schedule:
    """
    A single schedule.
    """

    def __init__(
        self,
        line_number: str,
        direction: str,
        departure_time: int,
        is_real_time_tracked: bool,
    ) -> None:
        # number of the line
        self.line_number = line_number
        # head sign on the bus, showing direction
        self.direction = direction
        # departure time
        self.departure_time = departure_time
        # real time updates avaiable
        self.is_real_time_tracked = is_real_time_tracked

    def __repr__(self)  -> str:
        return f'line: {self.line_number}, direction: {self.direction}, departing at: {self.departure_time}, real time: {self.is_real_time_tracked}\n'

    def formatDepartureTimeToReadable(self, time_frame_in_minutes=10) -> None:
        if self.departure_time - time.time() < time_frame_in_minutes * 60.0:
            self.departure_time = (
                str(math.ceil((self.departure_time - time.time()) / 60.0)) + " min"
            )
        else:
            self.departure_time = time.strftime(
                "%H:%M", time.localtime(self.departure_time)
            )
