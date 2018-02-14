# -*- coding: utf-8 -*-
import conftest
import jira
import jira.client
import pytest
import zazu.plugins.jira_issue_tracker

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


@pytest.fixture
def tracker_mock():
    return zazu.plugins.jira_issue_tracker.JiraIssueTracker('https://jira', 'ZZ', None)


@pytest.fixture
def mocked_jira_issue_tracker(mocker, tracker_mock):
    jira_mock = mocker.patch('jira.JIRA', autospec=True)
    tracker_mock._jira_handle = jira_mock
    return tracker_mock


mock_issue_dict = {
    'fields': {
        'summary': 'name',
        'status': {
            'name': 'Closed'
        },
        'resolution': {
            'name': 'Done'
        },
        'description': 'description',
        'issuetype': {
            'name': 'type'
        },
        'reporter': {
            'name': 'reporter'
        },
        'assignee': {
            'name': 'assignee'
        },
    },
    'key': 'ZZ-1'
}
mock_issue = conftest.dict_to_obj(mock_issue_dict)


def get_mock_issue_no_description(id):
    mock_issue_no_description = conftest.dict_to_obj(mock_issue_dict)
    mock_issue_no_description.fields.description = None
    return mock_issue_no_description


def test_jira_issue_tracker(mocker):
    mocker.patch('zazu.credential_helper.get_user_pass_credentials', return_value=('user', 'pass'))
    mocker.patch('jira.JIRA', autospec=True)
    uut = zazu.plugins.jira_issue_tracker.JiraIssueTracker('https://jira', 'ZZ', ['comp'])
    uut.connect()
    assert uut.default_project() == 'ZZ'
    assert uut.issue_components() == ['comp']
    assert uut.issue_types() == ['Task', 'Bug', 'Story']
    assert uut.issue('ZZ-1')


def test_jira_issue_tracker_no_description(mocker, mocked_jira_issue_tracker):
    mocked_jira_issue_tracker._jira_handle.issue = mocker.Mock(wraps=get_mock_issue_no_description)
    assert mocked_jira_issue_tracker.issue('ZZ-1').description == ''


def test_jira_issue_tracker_issue_error(mocker, mocked_jira_issue_tracker):
    mocked_jira_issue_tracker._jira_handle.issue = mocker.Mock(side_effect=jira.exceptions.JIRAError('foo'))
    with pytest.raises(zazu.issue_tracker.IssueTrackerError) as e:
        mocked_jira_issue_tracker.issue('ZZ-1')
    assert 'foo' in str(e.value)


def test_jira_issue_tracker_create_issue_error(mocker, mocked_jira_issue_tracker):
    mocked_jira_issue_tracker._jira_handle.create_issue = mocker.Mock(side_effect=jira.exceptions.JIRAError('foo'))
    with pytest.raises(zazu.issue_tracker.IssueTrackerError) as e:
        mocked_jira_issue_tracker.create_issue('', '', '', '', '')
    assert 'foo' in str(e.value)


def test_jira_issue_tracker_create_issue(mocker, mocked_jira_issue_tracker):
    mocked_jira_issue_tracker._jira_handle.create_issue = mocker.Mock(return_value=mock_issue)
    mocked_jira_issue_tracker.create_issue('project', 'issue_type', 'summary', 'description', 'component')
    jira_mock = mocked_jira_issue_tracker._jira_handle
    jira_mock.create_issue.call_count == 1
    jira_mock.assign_issue.call_count == 1
    jira_mock.assign_issue.assert_called_once_with(mock_issue, 'reporter')


def test_jira_issue_tracker_no_components(mocker):
    uut = zazu.plugins.jira_issue_tracker.JiraIssueTracker.from_config({'url': 'https://jira',
                                                                        'project': 'ZZ'})
    uut._jira_handle = mocker.Mock('jira.JIRA', autospec=True)
    assert uut.issue_components() == [None]


def test_from_config_no_project():
    with pytest.raises(zazu.ZazuException) as e:
        zazu.plugins.jira_issue_tracker.JiraIssueTracker.from_config({'url': 'https://jira'})
    assert str(e.value) == 'Jira config requires a "project" field'


def test_from_config_no_url():
    with pytest.raises(zazu.ZazuException) as e:
        zazu.plugins.jira_issue_tracker.JiraIssueTracker.from_config({'project': 'ZZ'})
    assert str(e.value) == 'Jira config requires a "url" field'


def test_jira_validate_id_format():
    uut = tracker_mock()
    uut.validate_id_format('LC-10')
    with pytest.raises(zazu.issue_tracker.IssueTrackerError) as e:
        uut.validate_id_format('lc-10')
    assert str(e.value) == 'issue id "lc-10" is not of the form PROJ-#'
    with pytest.raises(zazu.issue_tracker.IssueTrackerError):
        uut.validate_id_format('LC1-10')
    with pytest.raises(zazu.issue_tracker.IssueTrackerError):
        uut.validate_id_format('LC-10a')
    with pytest.raises(zazu.issue_tracker.IssueTrackerError):
        uut.validate_id_format('10')
    with pytest.raises(zazu.issue_tracker.IssueTrackerError):
        uut.validate_id_format('10a')


def test_jira_issue_adaptor(tracker_mock):
    uut = zazu.plugins.jira_issue_tracker.JiraIssueAdaptor(mock_issue, tracker_mock)
    assert uut.name == 'name'
    assert uut.status == 'Closed'
    assert uut.description == 'description'
    assert uut.assignee == 'assignee'
    assert uut.closed
    assert uut.type == 'type'
    assert uut.browse_url == 'https://jira/browse/ZZ-1'
    assert uut.id == 'ZZ-1'
    assert str(uut) == uut.id
