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
        now = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0)
        forecasts_start = FmiHandler.roundDownDateTime(now + dt.timedelta(hours=1))
        forecasts_end = forecasts_start + dt.timedelta(hours=5)

        observed = FmiHandler._load(
            {
                "storedquery_id": "fmi::observations::weather::simple",
                "parameters": "temperature",
                "fmisid": FmiHandler.STATION_ID,
                "starttime": FmiHandler._timestamp(now - dt.timedelta(hours=1)),
                "endtime": FmiHandler._timestamp(now),
                "timestep": "10",
            }
        )
        forecasts = FmiHandler._load(
            {
                "storedquery_id": "fmi::forecast::harmonie::surface::point::simple",
                "parameters": FmiHandler.FORECAST_PARAMETERS,
                "latlon": FmiHandler.FORECAST_LOCATION,
                "starttime": FmiHandler._timestamp(forecasts_start),
                "endtime": FmiHandler._timestamp(forecasts_end),
                "timestep": "5",
            }
        )

        temperatures = [
            (timestamp, values["temperature"])
            for timestamp, values in observed.items()
            if FmiHandler._number(values.get("temperature")) is not None
        ]
        if not temperatures:
            raise RuntimeError("FMI returned no measured temperature")

        result = {"observed_temperature": max(temperatures)[1], "forecasts": {}}
        for hours in (1, 2, 3, 6):
            target = FmiHandler._timestamp(
                FmiHandler.roundDownDateTime(now + dt.timedelta(hours=hours))
            )
            if target not in forecasts:
                raise RuntimeError(f"FMI returned no forecast for +{hours}h")
            result["forecasts"][hours] = forecasts[target]
        return result

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
