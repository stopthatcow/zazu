# -*- coding: utf-8 -*-
import pytest
import zazu.code_reviewer

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


def test_code_reviewer():
    uut = zazu.code_reviewer.CodeReviewer()
    with pytest.raises(NotImplementedError):
        uut.connect()
    with pytest.raises(NotImplementedError):
        uut.review('', '', '')
    with pytest.raises(NotImplementedError):
        uut.create_review('', '', '', '')


def test_code_review():
    uut = zazu.code_reviewer.CodeReview()
    with pytest.raises(NotImplementedError):
        uut.name
    with pytest.raises(NotImplementedError):
        uut.status
    with pytest.raises(NotImplementedError):
        uut.description
    with pytest.raises(NotImplementedError):
        uut.assignee
    with pytest.raises(NotImplementedError):
        uut.head
    with pytest.raises(NotImplementedError):
        uut.base
    with pytest.raises(NotImplementedError):
        uut.id
