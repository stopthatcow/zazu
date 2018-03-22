# -*- coding: utf-8 -*-
"""Code reviewer related classes."""
__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2017'


class CodeReviewer(object):
    """Parent of all CodeReviewer objects."""

    def connect(self):
        """Get handle to ensure that credentials are in place."""
        raise NotImplementedError('Must implement connect')

    def review(self, status, head, base):
        """Get list of reviews matching the supplied filters."""
        raise NotImplementedError('Must implement review')

    def create_review(self, title, base, head, body):
        """Create a new review."""
        raise NotImplementedError('Must implement create_review')


class CodeReviewerError(Exception):
    """Parent of all CodeReview errors."""


class CodeReview(object):
    """Provides an interface for code reviews."""

    @property
    def name(self):
        """Return the string name of the code review."""
        raise NotImplementedError('Must implement name')

    @property
    def status(self):
        """Return the string status of the code review."""
        raise NotImplementedError('Must implement status')

    @property
    def description(self):
        """Return the string status of the code review."""
        raise NotImplementedError('Must implement description')

    @property
    def assignee(self):
        """Return the assignee of the code review."""
        raise NotImplementedError('Must implement assignee')

    @property
    def head(self):
        """Return the branch name that is being merged from."""
        raise NotImplementedError('Must implement head')

    @property
    def base(self):
        """Return the branch name that is being merged to."""
        raise NotImplementedError('Must implement base')

    @property
    def browse_url(self):
        """Get the url to open to display the code review."""
        raise NotImplementedError('Must implement browse_url')

    @property
    def merged(self):
        """Return True if the code review is closed."""
        raise NotImplementedError('Must implement merged')

    @property
    def id(self):
        """Return the unique id of the code review."""
        raise NotImplementedError('Must implement id')
