from data_structures.stop import Stop
from data_structures.schedule import Schedule


def parseHSLData(hsl_data):
    """
    Parsing the data provided by HSL's API to my data types
    """
    stops = []

    for stop_data in hsl_data["data"]["stops"]:
        # create a Stop instance
        stop : Stop = Stop(
            stop_data["gtfsId"],
            stop_data["name"],
            routes=[d["shortName"] for d in stop_data["routes"]]
        )

        for schedule_data in stop_data["stoptimesWithoutPatterns"]:
            if not schedule_data["headsign"]:
                # This is a termination, skip
                continue

            if schedule_data["realtime"]:
                departure_time = (
                    schedule_data["serviceDay"] + schedule_data["realtimeDeparture"]
                )
            else:
                departure_time = (
                    schedule_data["serviceDay"] + schedule_data["scheduledDeparture"]
                )

            # create schedule instance
            schedule = Schedule(
                schedule_data["trip"]["route"]["shortName"],
                schedule_data["headsign"],
                departure_time,
                schedule_data["realtime"],
            )

            stop.addSchedule(schedule)
        # end for
        stops.append(stop)
    # end for
    return stops
