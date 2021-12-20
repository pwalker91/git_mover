#!/usr/bin/env python3

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# IMPORTS
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
import argparse
import re



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# CONSTS
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
GHE_API_PATH = '/api/v3'
GITHUB_URL = 'https://github.com'
GITHUB_API_URL = 'https://api.github.com'
GITHUB_DATA_TYPES = [
    'branches',
    'deploy_keys',
    'releases',
    ##To be implemented later, if necessary
    # 'collaborators',
    # 'issues',
    # 'milestones',
    # 'labels',
]



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# FUNCTIONS
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def get_arg_parser() -> argparse.ArgumentParser:
    """Gets the Argument Parser for the `git_mover` script.

    Arguments:
        None

    Returns:
        argparse.ArugmentParser: The argument parser for this project.
    """
    parser = argparse.ArgumentParser(
        usage='%(prog)s [OPTIONS] source_repo destination_repo',
        description='Migrate a repository between two Github server, complete with Milestones, Labels, and Issues.',
        formatter_class=argparse.RawTextHelpFormatter,
    )
    #Positional Args
    parser.add_argument(
        'source_repo',
        type=str,
        help="The owner and repo to migrate from: `<owner>/<repo_name>`. Multiple repos separated by a comma (,).",
    )
    parser.add_argument(
        'destination_repo',
        type=str,
        help="The owner and repo to migrate to: `<owner>/<repo_name>`. Multiple repos separated by a comma (,).",
    )
    #Credentials/Host Args
    parser.add_argument(
        '-v', '--verbose', dest='verbose',
        action="store_true", default=False,
        help="Script should verbosly print out what is happening."
    )
    parser.add_argument(
        '-sh', '--sourceHost', dest='sourceHost',
        nargs='?', required=True,
        type=str, action='store',
        help="The GitHub host to migrate from.",
    )
    parser.add_argument(
        '-su', '--sourceUserName', dest='sourceUserName',
        nargs='?', required=True,
        type=str, action='store',
        help="Your Username for source GitHub.",
    )
    parser.add_argument(
        '-st', '--sourceToken', dest='sourceToken',
        nargs='?', required=True,
        type=str, action='store',
        help="Your Personal Access Token for the source GitHub account.",
    )
    parser.add_argument(
        '-dh', '--destinationHost', dest='destinationHost',
        nargs='?',  required=True,
        type=str, action='store',
        help="The GitHub domain to migrate to.",
    )
    parser.add_argument(
        '-du', '--destinationUserName', dest='destinationUserName',
        nargs='?', required=True,
        type=str, action='store',
        help="Your Username for destination GitHub.",
    )
    parser.add_argument(
        '-dt', '--destinationToken', dest='destinationToken',
        nargs='?', required=True,
        type=str, action='store',
        help="Your Personal Access Token for the destination GitHub account.",
    )
    #Optional Args
    parser.add_argument(
        '-GD', '--githubData', dest='githubData',
        nargs='?',
        type=str, action="store", default=argparse.SUPPRESS,
        help="Migrates source git repository's GitHub data (eg. Milestones, Labels, Issues) to the destination.\n"+
            "Specify what you would like migrated as a comma-separated list of the following values:\n"+
            "  {}\n".format(', '.join(GITHUB_DATA_TYPES))+
            "If no value is specified, script will assume all Github data is requested.",
    )
    parser.add_argument(
        '-C', '--clone',
        action="store_true", default=False,
        help="Clones source git repository's commits/branchs/tags to the destination.",
    )

    return parser
#END DEF

def validate_repo_args(args:argparse.Namespace) -> None:
    """Parses the expected "repository" arguments and validates them.

    Arguments:
        args (argparse.Namespace): The result of `parser.parse_args` from the main script.

    Returns:
        None

    Raises:
        RuntimeError: The parsed repo arguments have an invalid string.

    The input param `args` is modified in place in the following manner:
        - `args.source_repo` copied to `args.source_repo_original`
        - `args.source_repo` split into list on comma (`,`)
        - All items in `args.source_repo` checked with regular expression to be a valid repository name
        - `args.destination_repo` copied to `args.destination_repo_original`
        - `args.destination_repo` split into list on comma (`,`)
        - All items in `args.destination_repo` checked with regular expression to be a valid repository name
    """
    git_repo_regex = r"^([\w\-]+)\/([\w\-]+)$"
    args.source_repo_original = args.source_repo
    args.destination_repo_original = args.destination_repo

    #Extracting the list of source repositories
    if ',' in args.source_repo:
        args.source_repo = [v.strip() for v in args.source_repo.split(',')]
    else:
        args.source_repo = [args.source_repo.strip()]
    #Validating that all of the repos specified as sources are in a valid format
    for srepo in args.source_repo:
        srematch = re.match(git_repo_regex, srepo)
        if srematch is None:
            raise RuntimeError("Source Repository '{}' is not a valid repository name.".format(srepo))
    #END FOR

    #Extracting the list of destination repositories.
    if ',' in args.destination_repo:
        args.destination_repo = [v.strip() for v in args.destination_repo.split(',')]
    else:
        args.destination_repo = [args.destination_repo.strip()]
    #END IF/ELIF/ELSE

    #Validating that all of the repos specified as destination either match or are a dot ('.')
    if len(args.destination_repo) != len(args.source_repo):
        raise RuntimeError(
            (   "Number of source repositories specified ({}) "+
                "does not equal the number of destination repositories ({})."
            ).format(len(args.source_repo), len(args.destination_repo))
        )
    for i in range(len(args.destination_repo)):
        drepo = args.destination_repo[i]
        if drepo == '.':
            args.destination_repo[i] = args.source_repo[i]
        else:
            drematch = re.match(git_repo_regex, drepo)
            if drematch is None:
                raise RuntimeError("Destination Repository '{}' is not a valid repository name.".format(drepo))
    #END FOR

    return
#END DEF

def validate_hosts(args:argparse.Namespace) -> None:
    """Parses the expected "repository" arguments and validates them.

    Arguments:
        args (argparse.Namespace): The result of `parser.parse_args` from the main script.

    Returns:
        None

    Raises:
        RuntimeError: The parsed host arguments are invalid.

    The input param `args` is modified in place in the following manner:
        - `args.sourceHost` copied to `args.sourceHost_original`
        - If currently GITHUB_URL or GITHUB_API_URL, `args.sourceHost` converted to GITHUB_API_URL.
          Else, GHE_API_PATH added to end of given value.
        - `args.destinationHost` copied to `args.destinationHost_original`
        - If currently GITHUB_URL or GITHUB_API_URL, `args.destinationHost` converted to GITHUB_API_URL.
          Else, GHE_API_PATH added to end of given value.
    """
    if any([ ('https://' != v[:8]) for v in [args.sourceHost, args.destinationHost]]):
        raise RuntimeError("This script only supports Source and Destination Github Hosts specified using an HTTPS URL.")

    args.sourceHost_original = args.sourceHost
    args.destinationHost_original = args.destinationHost
    if args.sourceHost.endswith('/'):
        args.sourceHost = args.sourceHost[:-1]
    if args.destinationHost.endswith('/'):
        args.destinationHost = args.destinationHost[:-1]

    if args.sourceHost in [GITHUB_URL, GITHUB_API_URL]:
        args.sourceHost = GITHUB_API_URL
    else:
        if args.sourceHost[(-1*len(GHE_API_PATH)):] != GHE_API_PATH:
            args.sourceHost += GHE_API_PATH
    #END IF/ELSE

    if args.destinationHost in [GITHUB_URL, GITHUB_API_URL]:
        args.destinationHost = GITHUB_API_URL
    else:
        if args.destinationHost[(-1*len(GHE_API_PATH)):] != GHE_API_PATH:
            args.destinationHost += GHE_API_PATH
    #END IF/ELSE

    args.sourceHost += '/'
    args.destinationHost += '/'

    return
#END DEF
