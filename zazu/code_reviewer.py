# -*- coding: utf-8 -*-
__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


class CodeReviewer(object):
    """Parent of all CodeReview objects"""
    pass


class CodeReviewError(Exception):
    """Parent of all CodeReview errors"""


class CodeReview:

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
        return self._pr.base  # -*- coding: utf-8 -*-
__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


class CodeReviewer(object):
    """Parent of all CodeReview objects"""
    pass


class CodeReviewError(Exception):
    """Parent of all CodeReview errors"""


class CodeReview:

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
