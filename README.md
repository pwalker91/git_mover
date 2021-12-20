# Git Mover

A Python script to clone a repository (all commits/code/tags/branches/etc.) and migrate the repository to a new location.

### Python Version

This script was written for **Python 3.9**.

### Dependencies

This project contains a Python script that can be run from the command line. Before running the script, be sure to install any required libraries by running the following command:
```bash
$ pip3 install -r requirements.txt
```
> NOTE!<br>
> You might consider using `virtualenv` and `virtualenvwrapper` to keep this project's Python version isolated from your system's Python. [Consider following this guide](https://virtualenvwrapper.readthedocs.io/en/latest/).

You will also need to install `git` Command Line Tool so that the Python script can use it to clone the specified repositories.<br>Refer to the [git-scm.com downloads page](https://git-scm.com/downloads) for information on how to install `git` on your machine.

## Usage

Using your preferred command line tool, navigate to your clone of this repository and run the following command:
```bash
$ python3 git-mover.py [OPTIONS] source_repo destination_repo
```
For more details on this script's options and how to use them, please review [the Usage Readme](README_USAGE.md).

### Warning! SSL Cert Verification

When the script sends an HTTP Request to any host _other than `https://api.github.com`_, the server's SSL Certification **will not be verified**.

## Remaining ToDo
- [ ] Logic for migration of labels
- [ ] Logic for migration of milestones
- [ ] Logic for migration of issues
- [ ] Logic for migration of PRs


----

_This project was based on the [original implementation](https://github.com/ahadik/git_mover) by `ahadik`. It also draws from [improvements](https://github.com/freshbooks/git_mover) made by `freshbooks`._
