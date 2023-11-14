"""
Further information can be found at:
https://newcastle.urbanobservatory.ac.uk/api_docs/doc/sensors-json/
"""

from api_requests.api_utils import handle_api_response, make_api_request


def request(params):
    """
    Sends a request to the urban observatory sensors API. This returns a json dictionary.
    """
    url = "https://newcastle.urbanobservatory.ac.uk/api/v1.1/sensors/json/"
    try:
        response = make_api_request(url, params)
        return handle_api_response(response)
    except ValueError as ve:
        print(f"Error in API request: {ve}")
        # Handle the error as needed, e.g., log it, return a default value, etc.
        return None
