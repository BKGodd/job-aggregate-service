"""
Created by: Brandon Goddard
Description: This module contains functions that perform
             basic API testing for the running service.
"""
from urllib.parse import quote
import requests

# This needs to match the APP_PORT variable in the .env file
APP_PORT = 5000

def build_url(title='', location='', encode=False):
    """
    Create the URL request.

    Args:
        title (str): Title query text.
        location (str): Location query text.
        encode (bool): Whether the URL should be incoded or not.

    Returns:
        (str): Final URL that can be used as a request.
    """
    # Encode the URL if desired, FastAPI will automatically decode
    if encode:
        title = quote(title)
        location = quote(location)

    # Build the params for the URL
    if title and location:
        params = f"?title={title}&location={location}"
    elif title and not location:
        params = f"?title={title}"
    elif location and not title:
        params = f"?location={location}"
    else:
        params = ""

    return  f"http://localhost:{APP_PORT}/{params}"


def get_request(**kwargs):
    """
    Creates the URL request and sends the corresponding request.

    Args:
        title (str): Title query text.
        location (str): Location query text.
        encode (bool): Whether the URL should be incoded or not.
        timeout (int): How long for the request to wait before timing out.

    Returns:
        (Response): Object that stores response from the associated request.
    """
    title = kwargs.get('title', '')
    location = kwargs.get('location', '')
    encode = kwargs.get('encode', False)
    timeout = kwargs.get('timeout', 30)
    url = build_url(title=title, location=location, encode=encode)
    return requests.get(url, timeout=timeout)


def are_same(response1, response2):
    """
    Equate two given HTTP responses.

    Args:
        response1 (Response): Object that stores response.
        response2 (Response): Object that stores response.

    Returns:
        (bool): Whether both responses are equivalent.
    """
    json1 = response1.json()
    json2 = response2.json()

    # Elasticsearch usually approximates the percentiles,
    # therefore, check only the data points and mean salary
    points_match = json1['data_points'] == json2['data_points']
    avgs_match = json1['mean_salary'] == json2['mean_salary']

    if points_match and avgs_match:
        return True
    print('response1 =', json1)
    print('response2 =', json2)
    return False
