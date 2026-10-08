import datetime as dt
import math
import xml.etree.ElementTree as ET

import requests


class FmiHandler:
    FMI_API_URL = "https://opendata.fmi.fi/wfs"
    STATION_ID = "100971"
    FORECAST_LOCATION = "60.195738,24.884575"
    FORECAST_PARAMETERS = (
        "temperature,precipitation1h,windspeedms,totalcloudcover,humidity,weathersymbol3"
    )
    NS = {
        "wfs": "http://www.opengis.net/wfs/2.0",
        "fmi": "http://xml.fmi.fi/schema/wfs/2.0",
    }

    @staticmethod
    def getWeatherFromFmi():
        now = dt.datetime.now().astimezone().replace(second=0, microsecond=0)
        targets = FmiHandler._forecastTargets(now)

        observed = FmiHandler._load(
            {
                "storedquery_id": "fmi::observations::weather::simple",
                "parameters": "temperature",
                "fmisid": FmiHandler.STATION_ID,
                "starttime": FmiHandler._timestamp(
                    (now - dt.timedelta(hours=1)).astimezone(dt.timezone.utc)
                ),
                "endtime": FmiHandler._timestamp(now.astimezone(dt.timezone.utc)),
                "timestep": "10",
            }
        )
        forecast_values = FmiHandler._load(
            {
                "storedquery_id": "fmi::forecast::harmonie::surface::point::simple",
                "parameters": FmiHandler.FORECAST_PARAMETERS,
                "latlon": FmiHandler.FORECAST_LOCATION,
                "starttime": FmiHandler._timestamp(targets[0].astimezone(dt.timezone.utc)),
                "endtime": FmiHandler._timestamp(targets[-1].astimezone(dt.timezone.utc)),
                "timestep": "60",
            }
        )

        temperatures = [
            (timestamp, values["temperature"])
            for timestamp, values in observed.items()
            if FmiHandler._number(values.get("temperature")) is not None
        ]
        if not temperatures:
            raise RuntimeError("FMI returned no measured temperature")

        result = {"observed_temperature": max(temperatures)[1], "forecasts": []}
        for target in targets:
            timestamp = FmiHandler._timestamp(target.astimezone(dt.timezone.utc))
            if timestamp not in forecast_values:
                raise RuntimeError(f"FMI returned no forecast for {target:%H:%M}")
            result["forecasts"].append(
                {
                    "time": target.strftime("%H:%M")
                    if target.date() == now.date()
                    else target.strftime("%a %H:%M"),
                    **forecast_values[timestamp],
                }
            )
        return result

    @staticmethod
    def _forecastTargets(now):
        first_hour = (now + dt.timedelta(hours=1)).replace(
            minute=0, second=0, microsecond=0
        )
        targets = [first_hour + dt.timedelta(hours=hours) for hours in range(3)]
        day = now.date()
        while len(targets) < 6:
            for hour in (9, 12, 15, 18, 21):
                target = dt.datetime.combine(day, dt.time(hour)).replace(tzinfo=now.tzinfo)
                if target > now and target not in targets:
                    targets.append(target)
                    if len(targets) == 6:
                        break
            day += dt.timedelta(days=1)
        return targets

    @staticmethod
    def _load(params):
        request_params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "getFeature",
            **params,
        }
        try:
            response = requests.get(FmiHandler.FMI_API_URL, params=request_params, timeout=3)
            response.raise_for_status()
            root = ET.fromstring(response.content)
        except (requests.exceptions.RequestException, ET.ParseError) as exc:
            raise RuntimeError("Failed to load data from FMI's API") from exc

        values = {}
        for member in root.findall("wfs:member", FmiHandler.NS):
            element = member.find("fmi:BsWfsElement", FmiHandler.NS)
            if element is None:
                continue
            timestamp = element.findtext("fmi:Time", namespaces=FmiHandler.NS)
            parameter = element.findtext("fmi:ParameterName", namespaces=FmiHandler.NS)
            value = element.findtext("fmi:ParameterValue", namespaces=FmiHandler.NS)
            if timestamp and parameter and value is not None:
                values.setdefault(timestamp, {})[parameter] = value
        return values

    @staticmethod
    def _number(value):
        try:
            value = float(value)
            return value if math.isfinite(value) else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _timestamp(value):
        return value.isoformat(timespec="seconds").replace("+00:00", "Z")

    @staticmethod
    def roundDownDateTime(value):
        return value - dt.timedelta(minutes=value.minute % 5)
