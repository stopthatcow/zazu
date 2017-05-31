# -*- coding: utf-8 -*-
__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


class IssueTracker(object):
    """Parent of all IssueTracker objects"""
    pass


class IssueTrackerError(Exception):
    """Parent of all IssueTracker errors"""


class Issue(object):

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
    def type(self):
        raise NotImplementedError('Must implement type')

    @property
    def assignee(self):
        raise NotImplementedError('Must implement assignee')

    @property
    def browse_url(self):
        raise NotImplementedError('Must implement browse_url')

    @property
    def id(self):
        raise NotImplementedError('Must implement id')
