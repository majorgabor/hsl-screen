import json
import requests
import urllib3

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)  # disable some warning print


class HslHandler:
    # static class variables
    HSL_API_URL = "https://omatnaytot.hsl.fi/api/graphql"
    REQUEST_HEADERS = {"Content-Type": "application/json"}
    try:
        with open("request_payload.json") as json_file:
            GET_DEPARTURES_FOR_STOPS_PAYLOAD = json.loads(json_file.read())
        with open("get_departures_for_stops.gql") as gql_file:
            GET_DEPARTURES_FOR_STOPS_PAYLOAD["query"] = gql_file.read()
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Failed to load payload data from json or grqphql file"
        ) from exc

    @staticmethod
    def GetDeparturesForStops() -> dict:
        try:
            # make a request to the API
            response = requests.post(
                HslHandler.HSL_API_URL,
                json=HslHandler.GET_DEPARTURES_FOR_STOPS_PAYLOAD,
                headers=HslHandler.REQUEST_HEADERS,
                verify=False,
                timeout=3,
            )
        except requests.exceptions.RequestException as exc:
            raise RuntimeError("Failed to load data from HSL's API") from exc

        # check if there is error response code
        if not response.ok:
            raise RuntimeError(
                "Failed to load data from HSL's API.\nResponse code: ",
                response.status_code,
            )

        # return response as dict/json
        return response.json()
