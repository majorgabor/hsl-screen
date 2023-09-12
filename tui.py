import math
import time
from rich import box
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.align import Align


class TUI:
    def __init__(self) -> None:
        # create a Layout
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="upper"),
            Layout(name="middle"),
            Layout(name="lower"),
            Layout(name="footer"),
        )
        self.layout["upper"].size = None
        self.layout["upper"].ratio = 1
        self.layout["upper"].split_row(
            Layout(name="left"),
            Layout(name="right"),
        )
        self.layout["middle"].size = None
        self.layout["middle"].ratio = 3
        self.layout["middle"].split_row(
            Layout(name="left"),
            Layout(name="right"),
        )
        self.layout["lower"].size = None
        self.layout["lower"].ratio = 3
        self.layout["lower"].split_row(
            Layout(name="left"),
            Layout(name="right"),
        )
        self.layout["footer"].size = None
        self.layout["footer"].ratio = 1
        self.layout["footer"].visible = False

        # create Live Display
        self.live_screen = Live(renderable=self.layout, screen=True, auto_refresh=False)
        self.live_screen.start()

    def __del__(self) -> None:
        self.live_screen.stop()

    def updateTimeTables(self, stops):
        """
        Puts the time table (schedules) on the screen
        """
        stop_groups = createStopGroups(stops)
        self.layout["middle"]["left"].update(
            generateTable(stop_groups["campus"], "campus")
        )
        self.layout["middle"]["right"].update(
            generateTable(stop_groups["city-center"], "Kamppi")
        )
        self.layout["lower"]["left"].update(
            generateTable(stop_groups["pasila-kallio"], "Pasila/Kallio")
        )
        self.layout["lower"]["right"].update(
            generateTable(stop_groups["north"], "north from here")
        )

    def updateTemperature(self, temperature_value):
        """
        Puts the temperature value on the screen
        """
        self.layout["upper"]["right"].update(
            Align.center(
                Panel(f"{temperature_value} \N{DEGREE SIGN}C", box=box.MINIMAL),
                vertical="middle",
            )
        )

    def putMessageOnFooter(self, message):
        self.layout["footer"].visible = True
        self.layout["footer"].update(
            Align.center(Panel(message, box=box.MINIMAL), vertical="middle")
        )

    def updateScreen(self, err_msgs):
        """
        Puts time and error messages if any then updates the live screen
        """
        # put time on screen
        self.layout["upper"]["left"].update(
            Align.center(
                Panel(time.strftime("%H:%M"), box=box.MINIMAL), vertical="middle"
            )
        )

        # pint error messages if needed
        if err_msgs:
            self.layout["footer"].visible = True
            text = "[red]Something unexpected occured!"
            for msg in err_msgs:
                text = text + "\n[red]" + msg
            self.layout["footer"].update(
                Align.center(Panel(text, box=box.MINIMAL), vertical="middle")
            )
        else:
            self.layout["footer"].visible = False

        self.live_screen.update(renderable=self.layout, refresh=True)
        time.sleep(15)


### Non class member helper functions ###


def createStopGroups(data: list) -> dict:
    """
    Groups stops based on direction the buses are leaving.
    """

    grouped_data = {}
    grouped_data["campus"] = []
    grouped_data["city-center"] = []
    grouped_data["north"] = []
    grouped_data["pasila-kallio"] = []

    for stop in data:
        if stop.id == "HSL:1301212":
            grouped_data["campus"].append(stop.schedules)

        elif stop.id == "HSL:1301451":
            grouped_data["city-center"].append(stop.schedules)

        elif (
            stop.id == "HSL:1301299"
            or stop.id == "HSL:1301123"
            or stop.id == "HSL:1301149"
        ):
            # 1301123 filter 52, 57
            if stop.id == "HSL:1301123":
                for idx, schedule in enumerate(stop.schedules):
                    if schedule.line_number == "52" or schedule.line_number == "57":
                        stop.schedules.pop(idx)
            grouped_data["north"].append(stop.schedules)

        elif stop.id == "HSL:1301122":
            for schedule in stop.schedules:
                if schedule.line_number == "500" or schedule.line_number == "510":
                    grouped_data["pasila-kallio"].append([schedule])
                else:
                    grouped_data["city-center"].append([schedule])

        elif stop.id == "HSL:1301124":
            for schedule in stop.schedules:
                if schedule.line_number == "502":
                    grouped_data["pasila-kallio"].append([schedule])
                else:
                    grouped_data["city-center"].append([schedule])

    # flaten, order and set readable times on lists
    grouped_data["campus"] = setDepartureTimeReadable(
        ordeByDepartureTime(flattenList(grouped_data["campus"]))
    )

    grouped_data["city-center"] = setDepartureTimeReadable(
        ordeByDepartureTime(flattenList(grouped_data["city-center"]))
    )

    grouped_data["north"] = setDepartureTimeReadable(
        ordeByDepartureTime(flattenList(grouped_data["north"]))
    )

    grouped_data["pasila-kallio"] = setDepartureTimeReadable(
        ordeByDepartureTime(flattenList(grouped_data["pasila-kallio"]))
    )

    return grouped_data


def flattenList(list_to_flatten: list):
    """
    From list of lists makes 'just' a list
    """
    return [item for sublist in list_to_flatten for item in sublist]


def ordeByDepartureTime(group: list):
    """
    Order a list of Schedules based on departure time
    """
    return sorted(group, key=lambda d: d.departure_time)


def setDepartureTimeReadable(schedules: list, time_frame_in_minutes: int = 10):
    """
    Converts unix time to human readable.
    If departure time and actual time is less than time_frame_in_minutes than it guves the minutes to departure.
    """
    for schedule in schedules:
        if schedule.departure_time - time.time() < time_frame_in_minutes * 60.0:
            schedule.departure_time = (
                str(math.ceil((schedule.departure_time - time.time()) / 60.0)) + " min"
            )
        else:
            schedule.departure_time = time.strftime(
                "%H:%M", time.localtime(schedule.departure_time)
            )
    return schedules


def generateTable(stop_data, direction) -> Table:
    """
    Make a table for the departures.
    """

    # create title for table
    table = Table(expand=True, box=box.SIMPLE)
    table.add_column("Line", no_wrap=True)
    table.add_column(f"Direction towards {direction}", no_wrap=False)
    table.add_column("Time", no_wrap=True)

    for schedule in stop_data:
        # add schedule
        table.add_row(
            schedule.line_number,
            schedule.direction,
            f"[green]{schedule.departure_time}"
            if schedule.is_real_time_tracked
            else f"{schedule.departure_time}",
        )
    return table
