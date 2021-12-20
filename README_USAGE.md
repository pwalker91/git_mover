# Git Mover Usage

Using your preferred command line tool, navigate to your clone of this repository and run the following command:
```bash
$ python3 git-mover.py [OPTIONS] source_repo destination_repo
```

This script has a number of options for modifying what information is moved/cloned from one repository to another. Please review the details below on how to use these options.

For authentication, Git Mover requires the use of a **Personal Access Token**, which can be generated in your GitHub Profile settings. Follow [this walkthrough](https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token) to create a Personal Access Token in _both the source and destination Github server_.



## Positional Arguments

- `source_repo`: the repo to migrate from.

- `destination_repo`: the repo to migrate to.

#### Repo Arg Format

- The specified source and destination repository need to be in the format `<team_name>/<repo>`.
> Eg. `informationtechnology/migrate-AD-users`

- When the value of `destination_repo` is `dot` (`.`), the same value of `source_repo` will be assigned as `destination_repo`.


#### Migrate multiple repositories

The name of repositories provided to `source_repo` and `destination_repo` can be comma separated. _If you need to specify your list of repositories with spaces between names, enclose the argument in quotation marks_.
> Eg. `<repo_name1>,<repo_name2>` or `'<repo_name1>, <repo_name2>  ,<repo_name3>'`

_If the number of items for `source_repo` does not match the number of items for `destination_repo`, an error will be thrown._

If multiple repositories are specified for `source_repo`, the same number of repositories need to be specified for `destination_repo`.
> Eg. `<dest_repo_name1>,<dest_repo_name2>`

If specifying multiple source repositories that will be going to the same team/repo on the destination server, you can specify dots (`.`) for the destination repo names.
> Eg. `.,.`



## Key/Keyword Arguments

#### Credential/Github-Host options

- `-sh, --sourceHost [SOURCE_HOST_URL]`: The HTTPS URL to the source repository's GitHub server, eg. `https://my-source-github.com`.

- `-su, --sourceUserName [USERNAME]`; Username for source GitHub.

- `-st, --sourceToken [TOKEN]`: Your Personal Access Token for the source GitHub account.

- `-dh, --destinationHost [DESTINATION_HOST_URL]`: The HTTPS URL to the destination repository's GitHub server, eg. `https://my-dest-github.com`.

- `-du, --destinationUserName [USERNAME]`: Username for destination GitHub.

- `-dt, --destinationToken [TOKEN]`: Your Personal Access Token for the destination GitHub account.

#### GitHub Action options

- `-R, --fullRepo`: Clones source repository git commits/branches/tags and Github data (Milestones/Labels/Issues) to the destination. This is essentially a shorthand for using both the `--clone` and `--githubData` options.

- `-GD, --githubData`: Migrates GitHub data (Milestones/Labels/Issues). User must specify either nothing (which will result in _all_ Github Data being migrated), or a comma-separated list of types of Github Data to migrate.

- `-C, --clone`: Clones source repository commits/branchs/tags to the destination.

#### Others

- `-h, --help`: show help message and exit.



## Example Usages

Move GHE repository `dev/gcp`, and `dev/network-service` to `github.com` with milestones, labels, and issues

```bash
$ python git-mover.py --clone --githubData --sourceHost https://onprem-git.local  --destinationHost https://github.com --sourceUserName <USERNAME_A> --sourceToken <TOKEN_A> --destinationUserName <USERNAME_B> --destinationToken <TOKEN_B>  dev/gcp,dev/networkservice company-it/gcp,company-it/networkservice
```

Or use dot (.) as destination repository.

```bash
$ python git-mover.py --clone --githubData --sourceHost https://onprem-git.local  --destinationHost https://github.com --sourceUserName <USERNAME_A> --sourceToken <TOKEN_A> --destinationUserName <USERNAME_B> --destinationToken <TOKEN_B>  dev/gcp,dev/networkservice .
```
