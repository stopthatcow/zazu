# -*- coding: utf-8 -*-
"""Issue tracker related classes."""
__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2016'


class IssueTracker(object):
    """Parent of all IssueTracker objects."""


class IssueTrackerError(Exception):
    """Parent of all IssueTracker errors."""


class Issue(object):
    """Parent of all Issues."""

    @property
    def name(self):
        """Get the name of the issue."""
        raise NotImplementedError('Must implement name')

    @property
    def status(self):
        """Get the status string of the issue."""
        raise NotImplementedError('Must implement status')

    @property
    def closed(self):
        """Return True if the issue is closed."""
        raise NotImplementedError('Must implement closed')

    @property
    def description(self):
        """Get the description of the issue."""
        raise NotImplementedError('Must implement description')

    @property
    def type(self):
        """Get the string type of the issue."""
        raise NotImplementedError('Must implement type')

    @property
    def assignee(self):
        """Get the string assignee of the issue."""
        raise NotImplementedError('Must implement assignee')

    @property
    def browse_url(self):
        """Get the url to open to display the issue."""
        raise NotImplementedError('Must implement browse_url')

    @property
    def id(self):
        """Get the string id of the issue."""
        raise NotImplementedError('Must implement id')

    def __str__(self):
        """Return the id as the string representation."""
        return self.id

    def __repr__(self):
        """Return the id as the string representation."""
        return self.id
