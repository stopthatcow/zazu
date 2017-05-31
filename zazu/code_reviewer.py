# -*- coding: utf-8 -*-
__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


class CodeReviewer(object):
    """Parent of all CodeReviewer objects"""

    def connect(self):
        """Get handle to ensure that credentials are in place"""
        raise NotImplementedError('Must implement connect')

    def review(self, status, head, base):
        """Get list of reviews matching the supplied filters"""
        raise NotImplementedError('Must implement review')

    def create_review(self, title, base, head, body):
        """Create a new review"""
        raise NotImplementedError('Must implement create_review')


class CodeReviewerError(Exception):
    """Parent of all CodeReview errors"""


class CodeReview(object):
    """Provides an interface for code reviews"""
    @property
    def name(self):
        raise NotImplementedError('Must implement name')

    @property
    def status(self):
        raise NotImplementedError('Must implement status')

    @property
    def description(self):
        raise NotImplementedError('Must implement description')

    @property
    def assignee(self):
        raise NotImplementedError('Must implement assignee')

    @property
    def head(self):
        raise NotImplementedError('Must implement head')

    @property
    def base(self):
        raise NotImplementedError('Must implement base')

    @property
    def id(self):
        raise NotImplementedError('Must implement id')
