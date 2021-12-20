#!/usr/bin/env python3

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# IMPORTS
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
import requests



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# CUSTOM EXCEPTION CLASSES
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class GitMoverApiCallError(Exception):
    """A custom Error class that lets use attach other args to the object.
    """

    def __init__(self, message:str, api_response:requests.Response) -> None:
        self.message = message
        self.api_response = api_response
    #END DEF

    def get_api_response(self) -> requests.Response:
        return self.api_response
    #END DEF

    def __str__(self) -> str:
        return "GitMoverApiCallError: {}".format(self.message)
    #END DEF
#END CLASS
