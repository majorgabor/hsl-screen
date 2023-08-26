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
        # update from API
        try:
            data = HslHandler.GetDeparturesForStops()
        except RuntimeError as exc:
            # stop UI
            del terminal_ui
            # print error
            print(exc)
            # exit with code 1
            exit(1)

        # extract useful information
        stops = parseHSLData(data)

        # update temperature every ~5 minutes
        if counter % 20 == 0:
            temperature = FmiHandler.getTemperatureFromFmi()

        # update screen
        terminal_ui.updateScreen(stops, temperature)

        counter = counter + 1
