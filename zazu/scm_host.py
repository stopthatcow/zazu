# -*- coding: utf-8 -*-
"""Source code management (SCM) host related classes."""
__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2018'


class ScmHost(object):
    """Parent of all ScmHost objects."""


class ScmHostError(Exception):
    """Parent of all ScmHost errors."""


class ScmHostRepo(object):
    """Parent of all SCM repos."""

    @property
    def name(self):
        """Get the name of the repo."""
        raise NotImplementedError('Must implement name')

    @property
    def id(self):
        """Get the id of the repo."""
        raise NotImplementedError('Must implement id')

    @property
    def description(self):
        """Get the description of the repo."""
        raise NotImplementedError('Must implement description')

    @property
    def browse_url(self):
        """Get the url to open to display the repo."""
        raise NotImplementedError('Must implement browse_url')

    @property
    def ssh_url(self):
        """Get the ssh url to clone the repo."""
        raise NotImplementedError('Must implement ssh_url')

    def __str__(self):
        """Return the id as the string representation."""
        return self.id

    def __repr__(self):
        """Return the id as the string representation."""
        return self.id
