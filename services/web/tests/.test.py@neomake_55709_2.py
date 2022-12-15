"""
Created by: Brandon Goddard
Description: This module contains functions that perform
             basic API testing for the running service.
"""
from urllib.parse import quote
import requests
from requests.exceptions import ConnectionError as ConnError

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


def test_connection():
    """Test that the service is running and a connection can be made."""
    try:
        get_request(timeout=10)
    except ConnError:
        assert False


def test_encode():
    """Test URL encoding functionality."""

    regular_url = build_url('director', 'dallas')
    encoded_url = build_url('director', 'dallas', encode=True)
    response1 = requests.get(regular_url, timeout=30)
    response2 = requests.get(encoded_url, timeout=30)
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json() == response2.json()



def test_void():
    """Test inclusion / exclusion of different query inputs."""

    # All empty parameters are considered insufficient inputs
    response = get_request()
    assert response.status_code == 404

    # Verify strings are stripped, same as not providing any inputs
    response = get_request(title='  ', location='  ')
    assert response.status_code == 404

    # Verify providing title but not location
    response = get_request(title='director')
    assert response.status_code == 200
    assert response.json()['data_points'] > 0

    # Verify providing location but not title
    response = get_request(location='new york')
    assert response.status_code == 200
    assert response.json()['data_points'] > 0


def test_filters():
    """Test input query text filters."""

    # Verify that letter case and punctuation is filtered out for location
    response1 = get_request(location='NEW YORK CITY')
    response2 = get_request(location='new. york, city?')
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json() == response2.json()

    # Verify that letter case and punctuation is filtered out for title
    response1 = get_request(title='.JAVA$?')
    response2 = get_request(title='java')
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json() == response2.json()


def test_order():
    """Test query text word ordering."""

    # Verify location is not getting matched with title, and vice versa
    response1 = get_request(title='new york city')
    response2 = get_request(location='new york city')
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json() != response2.json()

    # Verify that query word ordering does not matter
    response1 = get_request(title='assurance senior audit')
    response2 = get_request(title='audit assurance senior')
    response3 = get_request(title='senior audit assurance')
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response3.status_code == 200
    assert response1.json() == response2.json() == response3.json()
