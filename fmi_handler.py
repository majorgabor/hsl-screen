import requests
import datetime as dt
import xml.etree.ElementTree as ET


class FmiHandler:
    FMI_API_URL = "https://opendata.fmi.fi/wfs"
    PARAMS = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "getFeature",
        "storedquery_id": "fmi::forecast::harmonie::surface::point::simple",
        "timestep": "5",
        "parameters": "temperature",
        "latlon": "60.195738,24.884575",
    }

    @staticmethod
    def getTemperatureFromFmi():
        params = FmiHandler.PARAMS
        params["starttime"] = (
            FmiHandler.roundDownDateTime(dt.datetime.utcnow()).isoformat(
                timespec="seconds"
            )
            + "Z"
        )
        params["endtime"] = params["starttime"]

        try:
            # make a request to the API
            response = requests.get(FmiHandler.FMI_API_URL, params=params)
        except requests.exceptions.RequestException as exc:
            raise RuntimeError("Failed to load data from FMI's API") from exc

        # parse XML
        root = ET.fromstring(response.content)
        member = root.find("{http://www.opengis.net/wfs/2.0}member")
        element = member.find("{http://xml.fmi.fi/schema/wfs/2.0}BsWfsElement")
        parameter = element.find("{http://xml.fmi.fi/schema/wfs/2.0}ParameterValue")
        
        return parameter.text

    @staticmethod
    def roundDownDateTime(dt_obj):
        delta_min = dt_obj.minute % 5
        return dt.datetime(
            dt_obj.year,
            dt_obj.month,
            dt_obj.day,
            dt_obj.hour,
            dt_obj.minute - delta_min,
        )
