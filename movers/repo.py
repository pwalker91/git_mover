#!/usr/bin/env python3

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# IMPORTS
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
import json
import tempfile
import os
import shutil
from urllib.parse import urlparse
from . import api as gitmover_api
from .exceptions import GitMoverApiCallError



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# FUNCTIONS
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# + + + + + + + + + + + + + + + + + + + + +
#   DOWNLOAD FUNCTIONS
# + + + + + + + + + + + + + + + + + + + + +
def download_repository(repo:str, host:str, creds:tuple) -> dict:
    """Gets all of the core information for the given repository.

    Arguments:
        repo (str): The Repo we are getting information about.
        host (str): The Github Host that we will be connecting to.
        creds (tuple): The credentials for authentication.

    Returns:
        dict: A JSON response from the Github server parsed into a dictionary.
    """
    res = gitmover_api.do_send('GET', host, "repos/{}".format(repo), creds)
    clean_res = json.loads(res.text)
    return clean_res
#END DEF

def download_branches(repo:str, host:str, creds:tuple) -> dict:
    """Gets the extra info about the Branches for the given repository.

    Arguments:
        repo (str): The Repo we are getting information about.
        host (str): The Github Host that we will be connecting to.
        creds (tuple): The credentials for authentication.

    Returns:
        dict: A JSON response from the Github server parsed into a dictionary.
    """
    res = gitmover_api.do_send('GET', host, "repos/{}/branches".format(repo), creds)
    clean_res = json.loads(res.text)
    for branch in clean_res:
        if branch['protected']:
            branch['details'] = {}

            br_p = gitmover_api.do_send('GET', host, "repos/{}/branches/{}/protection".format(repo, branch['name']), creds)
            branch['details']['protection'] = json.loads(br_p.text)

            br_p_rprr = gitmover_api.do_send('GET', host, "repos/{}/branches/{}/protection/required_pull_request_reviews".format(repo, branch['name']), creds)
            branch['details']['required_pull_request_reviews'] = json.loads(br_p_rprr.text)

            try:
                br_p_rst = gitmover_api.do_send('GET', host, "repos/{}/branches/{}/protection/required_status_checks".format(repo, branch['name']), creds)
                branch['details']['required_status_checks'] = json.loads(br_p_rst.text)
            except (GitMoverApiCallError) as e:
                api_res = e.get_api_response()
                if api_res.status_code == 404:
                    branch['details']['required_status_checks'] = None
                else:
                    raise RuntimeError("Unexpected response from Github API. {}".format(api_res.text)) from e
            #END TRY/EXCEPT

            try:
                br_p_r = gitmover_api.do_send('GET', host, "repos/{}/branches/{}/protection/restrictions".format(repo, branch['name']), creds)
                branch['details']['restrictions'] = json.loads(br_p_r.text)
            except (GitMoverApiCallError) as e:
                api_res = e.get_api_response()
                if api_res.status_code == 404:
                    branch['details']['restrictions'] = None
                else:
                    raise RuntimeError("Unexpected response from Github API. {}".format(api_res.text)) from e
            #END TRY/EXCEPT
    #END FOR
    return clean_res
#END DEF

def download_deploy_keys(repo:str, host:str, creds:tuple) -> dict:
    """Gets the Deploy Keys for the given repository.

    Arguments:
        repo (str): The Repo we are getting information about.
        host (str): The Github Host that we will be connecting to.
        creds (tuple): The credentials for authentication.

    Returns:
        dict: A JSON response from the Github server parsed into a dictionary.
    """
    res = gitmover_api.do_send('GET', host, "repos/{}/keys".format(repo), creds)
    clean_res = json.loads(res.text)
    return clean_res
#END DEF

def download_releases(repo:str, host:str, creds:tuple) -> dict:
    """Gets the Releases for the given repository.

    Arguments:
        repo (str): The Repo we are getting information about.
        host (str): The Github Host that we will be connecting to.
        creds (tuple): The credentials for authentication.

    Returns:
        dict: A JSON response from the Github server parsed into a dictionary.
    """
    res = gitmover_api.do_send('GET', host, "repos/{}/releases".format(repo), creds)
    clean_res = json.loads(res.text)
    return clean_res
#END DEF

# + + + + + + + + + + + + + + + + + + + + +
#   CREATE REPO FUNCTIONS
# + + + + + + + + + + + + + + + + + + + + +
def create_repository(source_repo_info:dict, destination_repo:str, destination_host:str, creds:tuple) -> dict:
    """Creates a blank new repository in the destination using info from the source.

    Arguments:
        source_repo_info (dict): Basic information about the source repository.
        destination_repo (str): The name of the new repository we are creating.
        destination_host (str): The Github Host that we will be connecting to.
        creds (tuple): The credentials for authentication.

    Returns:
        dict: A JSON response from the Github server parsed into a dictionary.
    """
    dest_org, dest_repo_name = destination_repo.split('/')
    new_repo = {
        "name": dest_repo_name,
        "description": source_repo_info['description'],
        "homepage": source_repo_info['homepage'],
        "private": source_repo_info['private'],
        "auto_init": False,
    }
    res = gitmover_api.do_send('POST', destination_host, "orgs/{}/repos".format(dest_org), data=new_repo, creds=creds)
    clean_res = json.loads(res.text)
    return clean_res
#END DEF

def clone_repository(source_clone_url:str, destination_clone_url:str, all_creds:dict) -> bool:
    """Creates a blank new repository in the destination using info from the source.

    Arguments:
        source_clone_url (str): The full URL to use when cloning the source repository.
        destination_clone_url (str): The full URL to push the cloned repository to.
        all_creds (dict): A dictionary containing the credentials for both the source and destination API.

    Returns:
        bool: True if the cloned repo code/commits/etc. were successfully pushed to the destination. False if not.
    """
    source_url_parts = urlparse(source_clone_url)
    destination_url_parts = urlparse(destination_clone_url)

    full_source_clone_url = (
        source_url_parts.scheme + '://' +
        all_creds['src'][0] + ':' + all_creds['src'][1] + '@' +
        source_url_parts.netloc +
        source_url_parts.path
    )
    full_destination_clone_url = (
        destination_url_parts.scheme + '://' +
        all_creds['dst'][0] + ':' + all_creds['dst'][1] + '@' +
        destination_url_parts.netloc +
        destination_url_parts.path
    )

    current_directory = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)

    cmd_clone = os.system("git clone --bare {} .".format(full_source_clone_url))
    if cmd_clone != 0:
        raise RuntimeError("Failed to clone source repository.")
    cmd_push = os.system("git push --mirror {}".format(full_destination_clone_url))
    os.chdir(current_directory)
    shutil.rmtree(temp_dir)

    return cmd_push == 0
#END DEF

# + + + + + + + + + + + + + + + + + + + + +
#   CREATE GITHUB DATA FUNCTIONS
# + + + + + + + + + + + + + + + + + + + + +
def create_branches(branches:list, repo:str, host:str, creds:tuple, **kwargs) -> bool:
    """Creates Github data for Branches for the specified repository.

    Arguments:
        branches (list): A list of dictionaries of special data for Branches on the specified repository.
            The dictionaries should contain details about the repository's branches, branch protections, etc.
        repo (str): The full URL to use when cloning the source repository.
        host (str): The full URL to push the cloned repository to.
        creds (tuple): The credentials for authentication.

    Returns:
        bool: The Branch(es) Github data was successfully created

    Raises:
        RuntimeError: The call to create the specified data on the Github repository failed in an unexpected way
    """
    for br in branches:
        if not br['protected']:
            continue
        uri ="repos/{}/branches/{}/protection".format(repo, br['name'])
        try:
            res = gitmover_api.do_send(
                'PUT', host, uri, creds,
                data={
                    #objects
                    'required_status_checks': br['details']['required_status_checks'],
                    'required_pull_request_reviews': br['details']['required_pull_request_reviews'],
                    'restrictions': br['details']['restrictions'],
                    #booleans
                    'allow_force_pushes': br['details']['protection']['allow_force_pushes']['enabled'],
                    'allow_deletions': br['details']['protection']['allow_deletions']['enabled'],
                    'enforce_admins': br['details']['protection']['enforce_admins']['enabled'],
                    'required_linear_history': br['details']['protection']['required_linear_history']['enabled'],
                    'required_conversation_resolution': False,
                },
            )
        except (GitMoverApiCallError) as e:
            api_res = e.get_api_response()
            if api_res.status_code == 422:
                vprint(
                    "--- API Response from `POST` to `{}` gave HTTP response code 422. ".format(uri) +
                    "The data for branch '{}' was invalid.".format(br['name'])
                )
                return False
            else:
                raise RuntimeError("Unknown error while creating Branch(es) Github data.") from e
    #END FOR
    return True
#END DEF

def create_deploy_keys(deploy_keys:list, repo:str, host:str, creds:tuple, **kwargs) -> bool:
    """Creates Deploy Keys for the specified repository.

    Arguments:
        deploy_keys (list): A list of Deploy Keys to create on the specified repository.
            The list should contain dictionaries with the details to send to the `/keys` API endpoint.
        repo (str): The full URL to use when cloning the source repository.
        host (str): The full URL to push the cloned repository to.
        creds (tuple): The credentials for authentication.

    Returns:
        bool: The Deploy Keys were successfully created

    Raises:
        RuntimeError: The call to create the specified data on the Github repository failed in an unexpected way
    """
    for dk in deploy_keys:
        uri = "repos/{}/keys".format(repo)
        try:
            res = gitmover_api.do_send(
                'POST', host, uri, creds, do_wait=True,
                data={
                    'title': dk['title'],
                    'key': dk['key'],
                    'read_only': dk['read_only'],
                },
            )
        except (GitMoverApiCallError) as e:
            api_res = e.get_api_response()
            if api_res.status_code == 422:
                vprint(
                    "--- API Response from `POST` to `{}` gave HTTP response code 422. ".format(uri) +
                    "The deploy key '{}' was invalid.".format(dk['title'])
                )
                return False
            else:
                raise RuntimeError("Unknown error while creating Deploy Key.") from e
        #END TRY/EXCEPT
    #END FOR
    return True
#END DEF

def create_releases(releases:list, repo:str, host:str, creds:tuple, **kwargs) -> bool:
    """Creates Releases for the specified repository.

    Arguments:
        releases (list): A list of Releases to create on the specified repository.
            The list should contain dictionaries with the details to send to the `/releases` API endpoint.
        repo (str): The full URL to use when cloning the source repository.
        host (str): The full URL to push the cloned repository to.
        creds (tuple): The credentials for authentication.

    Returns:
        bool: The Releases were successfully created

    Raises:
        RuntimeError: The call to create the specified data on the Github repository failed in an unexpected way
    """
    for rl in releases:
        uri = "repos/{}/releases".format(repo)
        try:
            res = gitmover_api.do_send(
                'POST', host, uri, creds, do_wait=True,
                data={
                    'tag_name': rl['tag_name'],
                    'target_commitish': rl['target_commitish'],
                    'name': rl['name'],
                    'body': rl['body'],
                    'draft': rl['draft'],
                    'prerelease': rl['prerelease'],
                },
            )
        except (GitMoverApiCallError) as e:
            api_res = e.get_api_response()
            if api_res.status_code == 422:
                vprint(
                    "--- API Response from `POST` to `{}` gave HTTP response code 422. ".format(uri) +
                    "The release '{} ({})' was invalid.".format(rl['name'], rl['tag_name'])
                )
                return False
            else:
                raise RuntimeError("Unknown error while creating Release.") from e
        #END TRY/EXCEPT
    #END FOR
    return True
#END DEF



# + + + + + + + + + + + + + + + + + + + + +
#   FUNCTIONS WHILE DEBUGGING
# + + + + + + + + + + + + + + + + + + + + +
def _delete_repo(repo:str, host:str, creds:tuple) -> None:
    """Deletes the specified repository.

    Arguments:
        repo (str): The full URL to use when cloning the source repository.
        host (str): The full URL to push the cloned repository to.
        creds (tuple): The credentials for authentication.

    Returns:
        None

    """
    res = gitmover_api.do_send('DELETE', host, "repos/{}".format(repo), creds=creds)
    print("deleted repo --> {}".format(res))
#END DEF
