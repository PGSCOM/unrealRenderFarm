"""
Client request utility functions
"""


import logging
import requests
import json
import os

from . import renderRequestworker


LOGGER = logging.getLogger(__name__)

with open(os.path.join(os.path.dirname(__file__), '..', 'config.json'), 'r') as f:
    config = json.load(f)

SERVER_URL = config.get('serverUrl', 'http://localhost:5000')
SERVER_API_URL = SERVER_URL + '/api'

# Coger la contraseña de cloudflarepassword.json desde el valor "password", si no exsiste dejar la variable vacía
try:
    with open(os.path.join(os.path.dirname(__file__), '..', 'cloudflarepassword.json'), 'r') as f:
        password = json.load(f)['password']
except FileNotFoundError:
    password = ''


def get_all_requests():
    """
    Call a 'GET' method for all render requests from the server

    :return: [renderRequest.RenderRequest]. request objects
    """
    try:
        response = requests.get(SERVER_API_URL+'/get', params={'password': password})
        LOGGER.debug('GET all requests response: %s', response.text)
    except requests.exceptions.ConnectionError:
        LOGGER.error('failed to connect to server %s', SERVER_API_URL)
        return

    if response.status_code != 200:
        LOGGER.error('Failed to get requests, status code: %d', response.status_code)
        return

    results = response.json().get('results', [])
    LOGGER.debug('Number of requests received: %d', len(results))
    return [renderRequestworker.RenderRequest.from_dict(result) for result in results]


def get_request(uid):
    """
    Call a 'GET' method for a specific render request from the server
    
    :param uid: str. request uid
    :return: renderRequest.RenderRequest. request object
    """
    try:
        response = requests.get(SERVER_API_URL+'/get/{}'.format(uid), params={'password': password})
    except requests.exceptions.ConnectionError:
        LOGGER.error('failed to connect to server %s', SERVER_API_URL)
        return

    return renderRequestworker.RenderRequest.from_dict(response.json())


def add_request(d):
    """
    Call a 'POST' method to add a render request to the server
    
    :param d: dict. render request represented as dictionary
    :return: renderRequest.RenderRequest. request object created
    """
    try:
        response = requests.post(SERVER_API_URL+'/post', json=d, params={'password': password})
        LOGGER.debug('POST add request response: %s', response.text)
    except requests.exceptions.ConnectionError:
        LOGGER.error('failed to connect to server %s', SERVER_API_URL)
        return
    
    if response.status_code != 200:
        LOGGER.error('Failed to add request, status code: %d', response.status_code)
        return
    
    return renderRequestworker.RenderRequest.from_dict(response.json())


def remove_request(uid):
    """
    Call a 'DELETE' method to remove a render request to the server

    :param uid: str. render request uid
    :return: renderRequest.RenderRequest. request object created
    """
    try:
        response = requests.delete(SERVER_API_URL+'/delete/{}'.format(uid), params={'password': password})
    except requests.exceptions.ConnectionError:
        LOGGER.error('failed to connect to server %s', SERVER_API_URL)
        return
    
    return renderRequestworker.RenderRequest.from_dict(response.json())


def update_request(uid, progress=0, status='', time_estimate=''):
    """
    Call a 'PUT' method to update a render request on the server

    :param uid: str. render request uid to update
    :param progress: int. updated progress
    :param status: renderRequest.RenderStatus. updated status
    :param time_estimate: str. updated estimate remaining time
    :return: renderRequest.RenderRequest. updated render request object
    """
    try:
        response = requests.put(
            SERVER_API_URL+'/put/{}'.format(uid),
            data='{};{};{}'.format(progress, time_estimate, status),
            headers={'Content-Type': 'text/plain'}, params={'password': password}
        )
        LOGGER.debug('PUT update request response: %s', response.text)
    except requests.exceptions.ConnectionError:
        LOGGER.error('failed to connect to server %s', SERVER_API_URL)
        return

    if response.status_code != 200:
        LOGGER.error('Failed to update request, status code: %d', response.status_code)
        return

    return renderRequestworker.RenderRequest.from_dict(response.json())
