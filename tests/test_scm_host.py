# -*- coding: utf-8 -*-
import pytest
import zazu.scm_host

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


def test_scm_host_repo():
    uut = zazu.scm_host.ScmHostRepo()
    with pytest.raises(NotImplementedError):
        uut.name
    with pytest.raises(NotImplementedError):
        uut.id
    with pytest.raises(NotImplementedError):
        uut.description
    with pytest.raises(NotImplementedError):
        uut.browse_url
    with pytest.raises(NotImplementedError):
        uut.ssh_url
