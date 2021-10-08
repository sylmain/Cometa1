import requests
from requests.exceptions import HTTPError
from requests.exceptions import Timeout


class GetRequest:
    def getRequest(url):
        # return requests.get(url).json()
        try:
            response = requests.get(url, timeout=45)
            # если ответ успешен, исключения задействованы не будут
            response.raise_for_status()
        except Timeout:
            response = "Error. The request timed out"
        except HTTPError as http_err:
            response = f"Error. HTTP error occurred: {http_err}"
        except Exception as err:
            response = f"Error. Other error occurred: {err}"
        else:
            response = response.text

        return response
