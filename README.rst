Zazu (at your service)
======================

|zazuLogo| |buildBadge| |coverageBadge|

.. |coverageBadge| image:: https://coveralls.io/repos/github/stopthatcow/zazu/badge.svg
    :target: https://coveralls.io/github/stopthatcow/zazu

.. |buildBadge| image:: https://travis-ci.org/stopthatcow/zazu.svg?branch=develop
    :target: https://travis-ci.org/stopthatcow/zazu

.. |zazuLogo| image:: http://vignette1.wikia.nocookie.net/disney/images/c/ca/Zazu01cf.png
   :target: https://www.github.com/stopthatcow/zazu
   :height: 50 px
   :width: 50 px
   :align: center

Zazu is a CLI development workflow management tool that combines
elements of git flow with CI and issue tracking.

.. image:: https://g.gravizo.com/svg?digraph%20G%20{
    "Zazu" -> "Continuous Integration"
    "Zazu" -> "Source Control"
    "Zazu" -> "Issue Tracker"}
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

    sudo apt-get install libncurses-dev python-dev libssl-dev libffi-dev
    sudo pip install keyrings.alt

All platforms
~~~~~~~~~~~~~

::

    git clone git@github.com:stopthatcow/zazu.git
    cd zazu
    sudo pip install --upgrade pip
    sudo pip install --upgrade .

If you get an error about a package called "six" use the following
command instead: ``sudo pip install --upgrade --ignore-installed six .``

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

-  ``zazu dev start`` interactivly creates new JIRA ticket
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

    _zazu_completion() {
        COMPREPLY=( $( env COMP_WORDS="${COMP_WORDS[*]}" \
                       COMP_CWORD=$COMP_CWORD \
                       _ZAZU_COMPLETE=complete $1 ) )
        return 0
    }

    complete -F _zazu_completion -o default zazu;

ZSH users
~~~~~~~~~

Add the following to your ``~/.zshrc`` file

::

    autoload bashcompinit
    bashcompinit
    _zazu_completion() {
        COMPREPLY=( $( env COMP_WORDS="${COMP_WORDS[*]}" \
                       COMP_CWORD=$COMP_CWORD \
                       _ZAZU_COMPLETE=complete $1 ) )
        return 0
    }

    complete -F _zazu_completion -o default zazu;

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
