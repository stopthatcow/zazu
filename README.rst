Zazu (at your service)
======================
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

Zazu is a CLI development workflow management tool that combines
elements of git flow with CI and issue tracking.

.. image:: https://g.gravizo.com/svg?digraph%20G%20{
    "Zazu" -> "Continuous Integration"
    "Continuous Integration" -> "TeamCity"
    "Zazu" -> "Issue Tracker"
    "Issue Tracker" -> "JIRA"
    "Issue Tracker" -> "GitHub"
    "Zazu" -> "Code Review"
    "Code Review" -> "GitHub"
    "Zazu" -> "Code Style"
    "Code Style" -> "AStyle"
    "Code Style" -> "Clang Format"
    "Code Style" -> "Autopep8"}
    :align: center

Zazu is implemented in Python and is a
`Click <http://click.pocoo.org/5/>`__ based CLI. If you're wondering why
Click, this is a well `answered <http://click.pocoo.org/5/why/>`__
question.

Install
-------

Pre-requsites (linux)
~~~~~~~~~~~~~~~~~~~~~

::

    sudo apt-get install python-dev libssl-dev libffi-dev

All platforms
~~~~~~~~~~~~~

::

    sudo pip install --upgrade pip
    sudo pip install zazu

If you get an error about a package called "six" use the following
command instead: ``sudo pip install --upgrade --ignore-installed zazu``

Command overview
----------------
The following diagram shows the available subcommands of zazu.

.. image:: https://g.gravizo.com/svg?digraph%20G%20{
      "zazu" -> "build"
      "zazu" -> "tool"
      "tool" -> "install"
      "tool" -> "uninstall"
      "zazu" -> "style"
      "zazu" -> "repo"
      "repo" -> "setup"
      "setup" -> "hooks"
      "setup" -> "ci"
      "repo" -> "cleanup"
      "repo" -> "repo_init"
      repo_init [label=init, style=dashed]
      "repo" -> "clone"
      "zazu" -> "dev"
      "dev" -> "start"
      "dev" -> "status"
      dev_builds [label=builds, style=dashed]
      "dev" -> "dev_builds"
      "dev" -> "review"
      "dev" -> "ticket"}

Note: dashed lines are not yet implemented

Repo management
---------------

-  ``zazu repo clone <name>`` clones repo and installs GIT
   hooks
-  ``zazu repo init <name>`` initializes repo to default project
   structure (Unimplemented)
-  ``zazu repo setup hooks`` installs default GIT hooks to the repo
-  ``zazu repo setup ci`` sets up CI builds based on the zazu.yaml file
   in the repo

CI build configuration management
---------------------------------

Zazu can setup CI server builds (currently only TeamCity is supported)
to build targets specified by a recipe file (the zazu.yaml file in the
root of a repo).

-  ``zazu repo setup ci``

Development workflow management
-------------------------------

-  ``zazu dev start`` interactivly creates new ticket
-  ``zazu dev start <name>`` e.g.
   ``zazu dev start LC-440_a_cool_feature``
-  ``zazu dev status`` displays ticket and pull request status
-  ``zazu dev ticket`` launches web browser to the ticket page
-  ``zazu dev builds`` launches web browser to the CI project page
-  ``zazu dev review`` launches web browser to create/view a pull
   request

Code Style Enforcement
----------------------

-  ``zazu style`` fixes code style using astyle and autopep8

Building
--------

Zazu uses the zazu.yaml file to build goals defined there

-  ``zazu build <goal>``
-  The target architecture is assumed to be 'local' but may be
   overridden using the --arch flag. e.g
   ``zazu build --arch=arm32-linux-gnueabihf package`` would build
   targeting 32 bit arm linux.

Passing variables to the build
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You may pass extra variables to the build using key=value pairs.
``zazu build --arch=arm32-linux-gnueabihf package FOO=bar`` This sets
the environement variable *FOO* to the value *bar* during the build.

Build tool installation
-----------------------

Zazu will automatically try to obtain required build tools needed for
each target as specified in the zazu.yaml file. These may be
installed/uninstalled manually as well:

-  ``zazu tool install <tool==version>``
-  ``zazu tool uninstall <tool==version>``

These tools will be installed to the ``~/.zazu/tools/`` folder.

zazu.yaml file
--------------

The zazu.yaml file lives at the base of the repo and describes the CI
goals and architectures to be run. In addition it describes the
requirements for each goal.

::

    components:
      - name: networkInterface
        goals:
          - name: coverage
            description: "Runs the \"check\" target and reports coverage via gcovr"
            buildType: coverage
            buildVars:
                  LOCAL_SERVER: ON
            builds:
              - arch: x86_64-linux-gcc
          - name: package
            buildType: minSizeRel
            builds:
              - arch: arm32-linux-gnueabihf
                requires:
                  zazu:
                    - gcc-linaro-arm-linux-gnueabihf==4.9
              - arch: x86_64-linux-gcc

    issueTracker:
        type: github
        owner: stopthatcow
        repo: zazu

    codeReviewer:
        type: github
        owner: stopthatcow
        repo: zazu

    style:
      exclude:
        - dependencies/ #list path prefixes here to exclude from style
        - build/
      astyle:
        options:
          - "--options=astyle.conf" # options passed to astyle
        include:
          - src/*.cpp # list of globs of files to style
          - include/*.h
          - test/*.cpp
      autopep8:
        options:
          - "--max-line-length=150" # options passed to autopep8

      zazu: 0.2.0 # optional required zazu version

Compiler tuples
~~~~~~~~~~~~~~~

Architectures are defined as tuple in the folowing form:
``<ISA>-<OS>-<ABI>``

============
Examples
============

- x86\_64-linux-gcc
- x86\_32-linux-gcc
- x86\_64-win-msvc\_2013
- x86\_64-win-msvc\_2015
- x86\_32-win-msvc\_2013
- x86\_32-win-msvc\_2015
- arm32-linux-gnueabihf
- arm32-none-eabi

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

    autoload bashcompinit
    bashcompinit
    eval "$(_ZAZU_COMPLETE=source zazu)"

Handy aliases
-------------

::

    alias zz="zazu"
    alias zd="zazu dev"
    alias zds="zazu dev start"
    alias zdr="zazu dev review"
    alias zdt="zazu dev ticket"
    alias zdb="zazu dev builds"
    alias zs="zazu style"
    alias zb="zazu build"
