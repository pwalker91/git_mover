#!/usr/bin/env python3

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# IMPORTS
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
import sys
import os
import movers.args
import movers.repo
from movers.exceptions import GitMoverApiCallError



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# FUNCTIONS
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

vprint = None
def _define_verbose_print(is_verbose_exec:bool=False):
    """Given the boolean input, either does or does not define a "verbose print" function.

    Arguments:
        is_verbose_exec (bool): Whether the script is being executed with the "verbose" flag. Default=False

    Returns:
        None

    This function will either define a "non-op" function for the variable `vprint`, or will define a simple
    pass-through print function (where all of the args to `vprint` are simply passed on to an execution of `print`).
    """
    if is_verbose_exec:
        def _v_print(*sargs, **kwargs):
            print(*sargs, **kwargs)
    else:
        _v_print = lambda *a: None  # do-nothing function
    global vprint
    vprint = _v_print
#END DEF

def main() -> int:
    """Processes user request to move a git repo. Returns a Bash Shell exit code.

    Returns:
        int: The command line response code for this script's execution.
            0 = Script successfully terminated
            1 = Invalid arguments
            2 = `git` not installed
            3 = Issue with creating and cloning codebase to destination repository
            4 = Issue with copying Github Data to destination repository
    """
    parser = movers.args.get_arg_parser()
    args = parser.parse_args()
    _define_verbose_print(args.verbose)
    vprint("--- All arguments parsed.")
    vprint("--- ARG NAMESPACE | {!r}".format(args))
    # A Python Argument Parser has the `-h, --help` options built in.
    # For details on what arguments are expected, review the functions in `movers.args`.

    try:
        vprint("--- Validating Repository arguments")
        movers.args.validate_repo_args(args)
        vprint("--- Validating Hosts arguments")
        movers.args.validate_hosts(args)
        vprint("--- Cleaning value of `githubData` argument")
        if 'githubData' in args:
            args.githubData = (args.githubData or '').replace(' ','')
    except (RuntimeError) as e:
        print("+++ Failed to validate the given arguments. REASON: {}".format(e))
        return 1
    #END TRY/EXCEPT

    if not args.clone and 'githubData' not in args:
        print('+++ Action not specified. Use of `--clone` and/or `--githubData` option is required.')
        return 1
    #END IF
    if args.clone:
        cmd_git_exists = os.system("command -v git > /dev/null")
        if cmd_git_exists != 0:
            print("+++ This script needs to be able to use the 'git' command line tool. Please install 'git'.")
            return 2
    #END IF
    vprint("--- All arguments validated")
    vprint("--- CLEANED ARG NAMESPACE | {!r}".format(args))

    vprint("--- Defining HTTPS Credential pairs for source and destination.")
    all_credentials = {
        'src': (args.sourceUserName, args.sourceToken),
        'dst': (args.destinationUserName, args.destinationToken),
    }

    print("+++ Processing list of {} repositories".format(len(args.source_repo)))
    for idx in range(len(args.source_repo)):
        srepo = args.source_repo[idx]
        drepo = args.destination_repo[idx]
        print("+++ Processing '{}' --> '{}'".format(srepo, drepo))
        vprint("--- '{}' on {} being moved to '{}' on {}".format(srepo, args.sourceHost, drepo, args.destinationHost))

        #Testing to see if the Destination Repository already exists
        vprint("--- Testing if '{}' on {} already exists.".format(drepo, args.destinationHost))
        try:
            drepo_info = movers.repo.download_repository(drepo, args.destinationHost, all_credentials['dst'])
        except (GitMoverApiCallError) as e:
            api_res = e.get_api_response()
            if api_res.status_code == 404:
                vprint(
                    "--- API Response from function `movers.repo.download_repository` gave HTTP response code 404. "+
                    "Destination Repository does not exist. Safe to continue."
                )
                drepo_info = None
            else:
                print("+++ Unable to determine if destination repo does or does not already exist.")
                vprint("--- GitMoverApiCallError | {} ; {} ; {}".format(e, api_res.status_code, api_res.text))
                return 3
        #END TRY/EXCEPT

        if args.clone:
            if drepo_info is not None:
                print("+++ The destination repository already exists. Please delete it or only use the `--githubData` option.")
                return 3
            vprint("--- Cloning source repo to destination")
            vprint("----- Downloading info on source repo")
            srepo_info = movers.repo.download_repository(srepo, args.sourceHost, all_credentials['src'])
            if srepo_info['archived'] or srepo_info['disabled']:
                print("+++ The source repository has been archived or disabled. Skipping...")
                continue
            try:
                vprint("----- Creating new blank destination repo")
                drepo_info = movers.repo.create_repository(srepo_info, drepo, args.destinationHost, all_credentials['dst'])
                vprint("----- Cloning source repo commits/code/tags/etc. to destination")
                movers.repo.clone_repository(srepo_info['clone_url'], drepo_info['clone_url'], all_credentials)
            except (Exception) as e:
                print("+++ Failed to clone source repository's codebase to destination repository.")
                vprint("--- Exception | {}".format(e))
                return 3
            #END TRY/EXCEPT
        #END IF

        if 'githubData' in args:
            if drepo_info is None:
                print("+++ The destination repository does not exist. Please create it manually or use the `--clone` option.")
                return 4
            for gdt in movers.args.GITHUB_DATA_TYPES:
                if args.githubData == '' or gdt in args.githubData:
                    vprint("--- Copying source repository's {} data to destination".format(gdt))
                    github_download_function = getattr(movers.repo, 'download_{}'.format(gdt))
                    github_create_function = getattr(movers.repo, 'create_{}'.format(gdt))

                    try:
                        vprint("----- Downloading source repository's {} data".format(gdt))
                        downloaded_data = github_download_function(srepo, args.sourceHost, all_credentials['src'])
                        vprint("----- Uploading {} data to destination repository".format(gdt))
                        creation_successful = github_create_function(downloaded_data, drepo, args.destinationHost, all_credentials['dst'])
                        if not creation_successful:
                            print("+++ Failed to successfully create {} data. Deleting partial repository from destination.".format(gdt))
                            movers.repo._delete_repo(drepo, args.destinationHost, all_credentials['dst'])
                            return 4
                    except (Exception) as e:
                        print("+++ Error while creating {} data. Deleting partial repository from destination.".format(gdt))
                        vprint("----- Error encountered | {}".format(e))
                        movers.repo._delete_repo(drepo, args.destinationHost, all_credentials['dst'])
                        return 4
                    #END TRY/EXCEPT
                #END IF
            #END FOR
        #END IF
        print("+++ Successfully created data in new destination repository")

        # #####
        # #
        # # temp code while implementing
        # do_delete = input(">>> delete? (Y/n): ")
        # if do_delete == '' or do_delete.lower() == 'y':
        #     movers.repo._delete_repo(drepo, args.destinationHost, all_credentials['dst'])
        # #
        # #####
    #END FOR

    print("Done!")
    return 0
#END MAIN

if __name__ == "__main__":
    sys.exit(main())
