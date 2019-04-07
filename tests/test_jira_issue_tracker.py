# -*- coding: utf-8 -*-
import conftest
import copy
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


JIRA_ADDRESS = 'https://jira'


def test_jira_issue_tracker(mocker):
    mocker.patch('zazu.credential_helper.get_user_pass_credentials', return_value=('user', 'pass'))
    mocker.patch('jira.JIRA', autospec=True)
    uut = zazu.plugins.jira_issue_tracker.JiraIssueTracker(JIRA_ADDRESS, 'ZZ', ['comp'])
    uut.connect()
    assert uut.default_project() == 'ZZ'
    assert uut.issue_components() == ['comp']
    assert uut.issue_types() == ['Task', 'Bug', 'Story']
    assert uut.issue('ZZ-1')


def test_jira_issue_tracker_bad_credentials(mocker):
    mocker.patch('zazu.credential_helper.get_user_pass_credentials', side_effect=[('user', 'pass'), ('user', 'pass2')])
    mocker.patch('jira.JIRA', autospec=True, side_effect=[jira.JIRAError(status_code=401), object()])
    uut = zazu.plugins.jira_issue_tracker.JiraIssueTracker(JIRA_ADDRESS, 'ZZ', ['comp'])
    uut.connect()
    calls = zazu.credential_helper.get_user_pass_credentials.call_args_list
    assert calls[0] == mocker.call(JIRA_ADDRESS, use_saved=True)
    assert calls[1] == mocker.call(JIRA_ADDRESS, use_saved=False)


def test_jira_issue_tracker_exception(mocker):
    mocker.patch('zazu.credential_helper.get_user_pass_credentials', return_value=('user', 'pass'))
    mocker.patch('jira.JIRA', autospec=True, side_effect=jira.JIRAError(status_code=400))
    uut = zazu.plugins.jira_issue_tracker.JiraIssueTracker(JIRA_ADDRESS, 'ZZ', ['comp'])
    with pytest.raises(zazu.issue_tracker.IssueTrackerError) as e:
        uut.connect()
        assert '400' in str(e.value)


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


def test_jira_assign_issue(mocker, mocked_jira_issue_tracker):
    mocked_jira_issue_tracker._jira_handle.current_user = mocker.Mock(return_value='me')
    mocked_jira_issue_tracker._jira_handle.assign_issue = mocker.Mock()
    issue = zazu.plugins.jira_issue_tracker.JiraIssueAdaptor(mock_issue, mocked_jira_issue_tracker)
    mocked_jira_issue_tracker.assign_issue(issue, mocked_jira_issue_tracker.user())
    mocked_jira_issue_tracker._jira_handle.assign_issue.assert_called_once_with(mock_issue, 'me')


def test_jira_list_issues(mocker, mocked_jira_issue_tracker):
    mocked_jira_issue_tracker._jira_handle.current_user = mocker.Mock(return_value='me')
    mocked_jira_issue_tracker._jira_handle.search_issues = mocker.Mock(return_value=[])
    mocked_jira_issue_tracker.issues()
    mocked_jira_issue_tracker._jira_handle.search_issues.assert_called_once_with(
        'assignee=me AND resolution="Unresolved"', fields='key, summary, description')


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


def test_jira_validate_id_format(tracker_mock):
    uut = tracker_mock
    assert uut.validate_id_format('ZZ-10') == 'ZZ-10'
    assert uut.validate_id_format('Zz-10') == 'ZZ-10'
    assert uut.validate_id_format('zz-10') == 'ZZ-10'
    assert uut.validate_id_format('10') == 'ZZ-10'
    with pytest.raises(zazu.issue_tracker.IssueTrackerError) as e:
        uut.validate_id_format('3-10')
    assert str(e.value) == 'project "3" is not "ZZ"'
    with pytest.raises(zazu.issue_tracker.IssueTrackerError):
        uut.validate_id_format('ZZ1-10')
    with pytest.raises(zazu.issue_tracker.IssueTrackerError):
        uut.validate_id_format('ZZ-10a')
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
    assert uut.parse_key() == ('ZZ', 1)
    assert str(uut) == uut.id
    assert repr(uut) == uut.id
    mock_issue2 = copy.copy(mock_issue)
    mock_issue2.key = 'ZZ-2'
    uut2 = zazu.plugins.jira_issue_tracker.JiraIssueAdaptor(mock_issue2, tracker_mock)
    assert uut < uut2
    assert uut < 'ZZ-2'
