"""
Utility functions related to API requests (e.g. handling errors, common functionality)
"""

import requests


def handle_api_response(response):
    """
    Handles the API response and returns the JSON data if successful, otherwise raises
    a more specific exception.
    """
    try:
        if isinstance(response, requests.Response):
            response.raise_for_status()
            return response.json()
        else:
            raise ValueError("Invalid response type. Expected requests.Response.")
    except requests.exceptions.HTTPError as errh:
        raise ValueError(f"HTTP Error: {errh}") from errh
    except requests.exceptions.ConnectionError as errc:
        raise ValueError(f"Error Connecting: {errc}") from errc
    except requests.exceptions.Timeout as errt:
        raise ValueError(f"Timeout Error: {errt}") from errt
    except requests.exceptions.RequestException as err:
        raise ValueError(f"Request Error: {err}") from err


def make_api_request(url, params=None, timeout=1000):
    """
    Makes a generic API request with error handling.
    """
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as errh:
        raise ValueError(f"HTTP Error: {errh}") from errh
    except requests.exceptions.Timeout as errt:
        raise ValueError(f"Timeout Error: {errt}") from errt
    except requests.exceptions.RequestException as err:
        raise ValueError(f"API request failed: {err}") from err
