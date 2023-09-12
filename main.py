from hsl_handler import HslHandler
from fmi_handler import FmiHandler
from data_parser import parseHSLData
from tui import TUI

# main
if __name__ == "__main__":
    terminal_ui = TUI()

    counter = 0
    temperature = 0

    while True:
        err_msgs = []

        try:
            # update from API
            hsl_data = HslHandler.GetDeparturesForStops()
            # extract useful information
            schedules = parseHSLData(hsl_data)
            # update screen with time tables
            terminal_ui.updateTimeTables(schedules)
        except RuntimeError as exc:
            err_msgs.append("Could not update schedules!")

        # update temperature every ~5 minutes
        if counter % 20 == 0:
            try:
                # update from FMI
                temperature = FmiHandler.getTemperatureFromFmi()
                # update screen with temperatue
                terminal_ui.updateTemperature(temperature)
            except RuntimeError as exc:
                err_msgs.append("Could not update temperature!")
                # reset counter
                counter = -1 # -1 coz the end increment


        # update screen
        terminal_ui.updateScreen(err_msgs)
        # increment counter
        counter = counter + 1
