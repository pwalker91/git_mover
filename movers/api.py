#!/usr/bin/env python3

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# IMPORTS
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
import requests
import urllib3
import copy
import time
from . import args as gitmover_args
from .exceptions import GitMoverApiCallError



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# CONSTS
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
BASE_HEADERS = {
    'Content-type': 'application/json',
    'Accept': 'application/vnd.github.v3+json'
}



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# FUNCTIONS
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def _response_is_valid(res:requests.Response, expected_code_min:int=200, expected_code_max:int=299) -> bool:
    """Validates that the response from the Github Server is "okay".

    Arguments:
        res (requests.Response): The Response object from the HTTP call to a Github Server's API.
        expected_code_min (int): The minimum expected HTTP Response Code. Default=200
        expected_code_max (int): The maximum expected HTTP Response Code. Default=299

    Returns:
        bool: The Response was valid or not

    Raises:
        TypeError: The given min/max expected HTTP codes are not integers.
    """
    if not all([isinstance(v,int) for v in [expected_code_min,expected_code_max]]):
        raise TypeError("Min and Max Expected HTTP Response Codes need to be integers.")
    if not(expected_code_max >= res.status_code >= expected_code_min):
        return False
    return True
#END DEF

def do_send(
        method:str, host:str, uri:str,
        creds:tuple=None, data=None,
        accept_header:str=None,
        expected_code_min:int=200, expected_code_max:int=299,
        do_wait:bool=False
) -> requests.Response:
    """Sends a GET request to the specified Github API URL.

    Arguments:
        method (str): The HTTP Method.
        host (str): The host path to a Github server.
        uri (str): The URI of the Github server we are accessing.
        creds (tuple): The credentials for authentication in the following order; (username, pa-token). Default=None
        data (object): The data to pass to the `requests.request` function. Default=None
        accept_header (str): An override of the default value sent in the 'Accept' header.
        expected_code_min (int): The minimum expected HTTP Response Code. Default=200
        expected_code_max (int): The maximum expected HTTP Response Code. Default=299
        do_wait (bool): Whether to wait a second before sending the request. Used to avoid rate limiting.

    Returns:
        str: The response from the Github server, as a string (should be JSON).

    Raises:
        GitMoverApiCallError: HTTP Request received an invalid response.
    """
    if do_wait:
        time.sleep(1)
    urllib3.disable_warnings()

    this_headers = copy.deepcopy(BASE_HEADERS)
    if accept_header is not None:
        this_headers['Accept'] = accept_header

    requestArgs = {
        'method': method,
        'url': (host+uri),
        'headers': this_headers,
        'auth': creds,
        'verify': True if (host == gitmover_args.GITHUB_API_URL) else False,
    }
    if data is not None:
        requestArgs['json'] = data
    res = requests.request(**requestArgs)

    if not _response_is_valid(res, expected_code_min, expected_code_max):
        raise GitMoverApiCallError(
            "Given HTTP response was invalid: {} {}".format(res.status_code, res.text),
            api_response = res,
        )
    return res
#END DEF
