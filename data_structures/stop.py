from data_structures.schedule import Schedule


class Stop:
    """
    A single public transport stop.
    """

    def __init__(self, id: str, name: str, routes: list = []) -> None:
        # id
        self.id = id
        # name of the stop
        self.name = name
        # routes departing from the stop
        self.routes = routes
        # schedules
        self.schedules = []

    def __repr__(self) -> str:
        return f"Stop: {self.id}, {self.name}, routes: {self.routes}, schedules:\n{[s for s in self.schedules]}\n"

    def addSchedule(self, schedule: Schedule) -> None:
        self.schedules.append(schedule)

    def formatDepartureTimeToReadable(self, time_frame_in_minutes=10) -> None:
        for schedule in self.schedules:
            schedule.formatDepartureTimeToReadable(time_frame_in_minutes)
