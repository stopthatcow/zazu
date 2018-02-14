# -*- coding: utf-8 -*-
import pytest
import zazu.issue_tracker

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


def test_issue():
    uut = zazu.issue_tracker.Issue()
    with pytest.raises(NotImplementedError):
        uut.name
    with pytest.raises(NotImplementedError):
        uut.status
    with pytest.raises(NotImplementedError):
        uut.description
    with pytest.raises(NotImplementedError):
        uut.type
    with pytest.raises(NotImplementedError):
        uut.assignee
    with pytest.raises(NotImplementedError):
        uut.browse_url
    with pytest.raises(NotImplementedError):
        uut.id
    with pytest.raises(NotImplementedError):
        uut.closed
