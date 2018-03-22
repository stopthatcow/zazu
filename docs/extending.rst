Extending
=========

Zazu has 4 classes of plugins:

- IssueTracker
- CodeReviewer
- ScmHost
- Styler

Creating a new plugin
---------------------
Zazu uses the `straight.plugin <http://straightplugin.readthedocs.io/en/latest/index.html>`__ framework. Creating a
new Zazu plugin is as easy as subclassing one of the base plugin types and installing the module containing the subclass
to the ``zazu.plugin`` namespace.

SCM Host
--------
A SCM host is a service that hosts source code such as github. Zazu uses the ScmHost interface to allow shortcuts when cloning new repos.
Zazu ships with support for GitHub hosting.


Issue Trackers
--------------

Zazu uses the IssueTracer interface to create new issues and ensure that new branches are associated with an issue.
Zazu ships with support built in for Atlassian JIRA and GitHub issues.


Code Reviewers
--------------
Zazu uses the CodeReviewer interface to create new code reviews and ensure that code reviews are linked to IssueTracker issues.
Zazu ships with support built in for GitHub code reviews.


Code Stylers
------------

Zazu uses the Styler interface to check code style, prevent commits when there are style violations and fix these violations.
Zazu ships with support built in for astyle, clang-format, autopep8, docformatter, goimports, esformatter and a generic styler.
The generic styler can be used for any program that can take unstyled input from stdin and output styled test on stdout.