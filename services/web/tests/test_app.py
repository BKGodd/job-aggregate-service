"""
Created by: Brandon Goddard
Description: This module contains functions that perform
             basic API testing for the running service.
"""
from helper import get_request, are_same
from requests.exceptions import ConnectionError as ConnError


def test_connection():
    """Test that the service is running and a connection can be made."""
    try:
        get_request(timeout=10)
    except ConnError:
        assert False


def test_encode():
    """Test URL encoding functionality."""

    response1 = get_request(title='director', location='dallas')
    response2 = get_request(title='director', location='dallas', encode=True)
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert are_same(response1, response2)


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
    assert are_same(response1, response2)

    # Verify that letter case and punctuation is filtered out for title
    response1 = get_request(title='.JAVA$?')
    response2 = get_request(title='java')
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert are_same(response1, response2)


def test_order():
    """Test query text word ordering."""

    # Verify location is not getting matched with title, and vice versa
    response1 = get_request(title='new york city')
    response2 = get_request(location='new york city')
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert not are_same(response1, response2)

    # Verify that query word ordering does not matter
    response1 = get_request(title='assurance senior audit')
    response2 = get_request(title='audit assurance senior')
    response3 = get_request(title='senior audit assurance')
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response3.status_code == 200
    assert are_same(response1, response2)
    assert are_same(response2, response3)
