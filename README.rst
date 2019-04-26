Getting Started
===============
|buildBadge| |coverageBadge|
|ReleaseBadge|  |FormatBadge|
|LicenseBadge| |PythonVersionBadge|

.. |coverageBadge| image:: https://coveralls.io/repos/github/stopthatcow/zazu/badge.svg?branch=develop
    :target: https://coveralls.io/github/stopthatcow/zazu?branch=develop

.. |buildBadge| image:: https://travis-ci.org/stopthatcow/zazu.svg?branch=develop
    :target: https://travis-ci.org/stopthatcow/zazu

.. |ReleaseBadge| image:: https://img.shields.io/pypi/v/zazu.svg
    :target: https://coveralls.io/github/stopthatcow/zazu

.. |LicenseBadge| image:: https://img.shields.io/pypi/l/zazu.svg
    :target: https://coveralls.io/github/stopthatcow/zazu

.. |PythonVersionBadge| image:: https://img.shields.io/pypi/pyversions/zazu.svg
    :target: https://coveralls.io/github/stopthatcow/zazu

.. |FormatBadge| image:: https://img.shields.io/pypi/format/zazu.svg
    :target: https://coveralls.io/github/stopthatcow/zazu

Complete documentation is available at `zazu.readthedocs.io <http://zazu.readthedocs.io>`__.

Zazu is a CLI development workflow management tool that combines
elements of git flow with issue tracking and code review.

.. image:: https://g.gravizo.com/svg?digraph%20G%20{
    "Zazu" -> "Issue Tracker"
    "Issue Tracker" -> "JIRA"
    "Issue Tracker" -> "GitHub"
    "Zazu" -> "Code Review"
    "Code Review" -> "GitHub"
    "Zazu" -> "Code Style"
    "Code Style" -> "Artistic Style"
    "Code Style" -> "ClangFormat"
    "Code Style" -> "autopep8"
    "Code Style" -> "goimports"
    "Code Style" -> "esformatter"
    "Code Style" -> "..."}
    :align: center

Zazu is implemented in Python and is a
`Click <http://click.pocoo.org/5/>`__ based CLI. If you're wondering why
Click, this is a `well answered <http://click.pocoo.org/5/why/>`__
question.

Install
-------

Pre-requsites (linux)
~~~~~~~~~~~~~~~~~~~~~

::

    apt-get install python-dev python-pip libssl-dev libffi-dev

From PyPi
~~~~~~~~~

::

    pip install zazu

If you get an error about a package called "six" use the following
command instead: ``pip install --upgrade --ignore-installed zazu``

From Source
~~~~~~~~~~~
Zazu is fastest when installed in wheel form.

::

    git clone git@github.com:stopthatcow/zazu.git
    cd zazu
    pip install --upgrade pip setuptools wheel
    python setup.py bdist_wheel
    pip install dist/*.whl

Configuration
-------------
Setup your user config file (located in ~/zazuconfig.yaml).

GitHub setup
~~~~~~~~~~~~
::

    zazu config --add scmHost.default.type github
    zazu config --add scmHost.default.user <github username>

Command overview
----------------
The following diagram shows the available subcommands of zazu.

.. image:: https://g.gravizo.com/svg?digraph%20G%20{
      "zazu" -> "config"
      "zazu" -> "style"
      "zazu" -> "repo"
      "repo" -> "init"
      "repo" -> "cleanup"
      "repo" -> "clone"
      "zazu" -> "dev"
      "dev" -> "start"
      "dev" -> "status"
      "dev" -> "ticket"
      "dev" -> "review"}

Repo management
---------------

-  ``zazu repo clone <name>`` clones repo and installs GIT
   hooks
-  ``zazu repo init`` installs default GIT hooks to an existing repo

Development workflow management
-------------------------------

-  ``zazu dev start`` interactivly creates new ticket
-  ``zazu dev start <name>`` e.g.
   ``zazu dev start LC-440_a_cool_feature``
-  ``zazu dev status`` displays ticket and pull request status
-  ``zazu dev ticket`` launches web browser to the ticket page
-  ``zazu dev review`` launches web browser to create/view a pull
   request

Code Style Enforcement
----------------------

-  ``zazu style`` fixes code style using astyle and autopep8


~/.zazuconfig.yaml file (user level configuration)
--------------------------------------------------

The .zazuconfig.yaml is a file that lives in your home directory and sets high
level configuration options for zazu. Most people will likely have a single
default scmHost entry, though zazu supports multiple named entries.

::

  # User configuration file for zazu.

  # SCM hosts are cloud hosting services for repos. Currently GitHub is supported.
  scmHost:
    default:              # This is the default SCM host.
      type: github        # Type of this SCM host.
      user: stopthatcow   # GitHub username
    pat:                  # Optionally: another SCM host named "pat".
      type: github        # Type of this SCM host.
      user: moorepatrick  # GitHub username

With the above configuration in place the following are allowed:

- ``zazu repo clone stopthatcow/zazu`` Using the default host so we don't need the fully-qualified name.
- ``zazu repo clone pat/moorepatrick/zazu`` This uses a non-default host so we need the name.

zazu.yaml file (repo level configuration)
-----------------------------------------

The zazu.yaml file lives at the base of the repo and describes the integrations to use with this repo.

::

    issue_tracker:
        type: github
        owner: stopthatcow
        repo: zazu

    code_reviewer:
        type: github
        owner: stopthatcow
        repo: zazu

    style:
      - exclude:
          - dependencies/ # list path prefixes here to exclude from style
          - build/
        stylers:
          - type: astyle
            options:
              - "--options=astyle.conf" # options passed to astyle
            include:
              - src/**.cpp # list of globs of files to style
              - include/**.h
              - test/**.cpp
          - type: autopep8
            options:
              - "--max-line-length=150" # options passed to autopep8
          # Generic styler that uses sed to fix common misspellings.
          - type: generic
            command: sed
            options:
              - "s/responce/response/g"
            include:
              - src/**
              - include/**
              - test/**

    # An optional section where names for special branches can be remapped.
    branches:
      develop: master  # Features will be started from the "master" branch.

    zazu: 0.11.0 # optional required zazu version


Command autocompletion
----------------------

Note that autocompletion currently only works for commands and
subcommands (not arguments).

BASH users
~~~~~~~~~~

Add the following to your
``~/.bashrc`` file:

::

    eval "$(_ZAZU_COMPLETE=source zazu)"

ZSH users
~~~~~~~~~

Add the following to your ``~/.zshrc`` file

::

    eval "$(_ZAZU_COMPLETE=source_zsh zazu)"

Handy aliases
-------------

::

    alias zz="zazu"
    alias zd="zazu dev"
    alias zds="zazu dev start"
    alias zdr="zazu dev review"
    alias zdt="zazu dev ticket"
    alias zs="zazu style"
