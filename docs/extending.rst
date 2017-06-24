Extending
=========

Zazu has 4 classes of plugins:

- BuildServer (aka CI or Continuous Integration)
- IssueTracker
- CodeReviewer
- Styler

Creating a new plugin
---------------------
Zazu uses the `straight.plugin <http://straightplugin.readthedocs.io/en/latest/index.html>`__ framework. Creating a
new Zazu plugin is as easy as subclassing one of the base plugin types and installing the module containing the subclass
to the ``zazu.plugin`` namespace.

Build Servers
-------------

The build server interface exists so zazu can setup a continuous integration server to automatically build your repo when you make changes.
Zazu ships with support built in for JetBrains TeamCity.


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
Zazu ships with support built in for astyle, clang-format and autopep8.
