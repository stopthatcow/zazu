# -*- coding: utf-8 -*-
import click
import click.testing
import tests.conftest as conftest
import pytest
import webbrowser
import zazu.cli
import zazu.dev.commands


__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


def test_issue_descriptor():
    uut = zazu.dev.commands.IssueDescriptor('feature/', '3')
    assert uut.get_branch_name() == 'feature/3'
    uut = zazu.dev.commands.IssueDescriptor('feature/', '3', 'a description')
    assert uut.get_branch_name() == 'feature/3_a_description'
    assert uut.readable_description() == 'A description'


def test_verify_ticket_exists(mocker):
    issue_tracker_mock = mocker.Mock()
    issue_tracker_mock.issue = mocker.Mock(side_effect=zazu.issue_tracker.IssueTrackerError("No ticket found"))
    with pytest.raises(click.ClickException) as e:
        zazu.dev.commands.verify_ticket_exists(issue_tracker_mock, '1')
    assert str(e.value) == 'no ticket for id "1"'
    issue_tracker_mock.issue = mocker.Mock()
    zazu.dev.commands.verify_ticket_exists(issue_tracker_mock, '1')


def test_offer_to_stash_changes(mocker):
    mock_repo = mocker.Mock()
    mock_repo.index = mocker.Mock()
    mock_repo.index.diff = mocker.Mock(return_value=' ')
    mock_repo.git = mocker.Mock()
    mock_repo.git.status = mocker.Mock(return_value=' ')
    mock_repo.git.stash = mocker.Mock()
    mocker.patch('click.confirm', return_value=True)
    zazu.dev.commands.offer_to_stash_changes(mock_repo)
    assert click.confirm.call_count == 1
    click.confirm.assert_called_once_with('Local changes detected, stash first?', default=True)


def test_make_issue_descriptor_bad_type():
    with pytest.raises(click.ClickException) as e:
        zazu.dev.commands.make_issue_descriptor('bad/1', require_type=True)
    assert str(e.value).startswith('Branch prefix must be one of ')


def test_make_issue_descriptor_github_style():
    with pytest.raises(click.ClickException) as e:
        zazu.dev.commands.make_issue_descriptor('bad/1', require_type=True)
    assert str(e.value).startswith('Branch prefix must be one of ')
    branch_name = 'feature/1_description'
    uut = zazu.dev.commands.make_issue_descriptor(branch_name)
    assert uut.get_branch_name() == branch_name
    assert uut.type == 'feature/'
    assert uut.id == '1'
    assert uut.description == 'description'


def test_make_issue_descriptor_jira_style():
    branch_name = 'feature/ZZ-1_description'
    uut = zazu.dev.commands.make_issue_descriptor(branch_name)
    assert uut.get_branch_name() == branch_name
    assert uut.type == 'feature/'
    assert uut.id == 'ZZ-1'
    assert uut.description == 'description'


def test_make_ticket(mocker):
    mock_issue_tracker = mocker.Mock('zazu.issue_tracker.IssueTracker', autospec=True)
    mocker.patch('zazu.util.prompt', side_effect=['title', 'description'])
    mock_issue_tracker.connect = mocker.Mock()
    mock_issue_tracker.create_issue = mocker.Mock()
    mock_issue_tracker.default_project = mocker.Mock(return_value='project')
    mock_issue_tracker.issue_types = mocker.Mock(return_value=['type'])
    mock_issue_tracker.issue_components = mocker.Mock(return_value=['component'])
    zazu.dev.commands.make_ticket(mock_issue_tracker)
    mock_issue_tracker.create_issue.assert_called_once_with(project='project',
                                                            issue_type='type',
                                                            summary='title',
                                                            description='description',
                                                            component='component')


def test_rename(git_repo):
    with zazu.util.cd(git_repo.working_tree_dir):
        assert 'foo' not in git_repo.heads
        git_repo.git.checkout('HEAD', b="foo")
        assert 'bar' not in git_repo.heads
        assert 'foo' in git_repo.heads
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['dev', 'rename', 'bar'])
        assert result.output == ''
        assert not result.exception
        assert result.exit_code == 0
        assert 'bar' in git_repo.heads
        assert 'foo' not in git_repo.heads


def test_rename_with_origin(git_repo_with_local_origin):
    repo = git_repo_with_local_origin
    with zazu.util.cd(repo.working_tree_dir):
        assert 'foo' not in repo.heads
        repo.git.checkout('HEAD', b="foo")
        repo.git.push('-u', 'origin', 'foo')
        assert 'bar' not in repo.heads
        assert 'foo' in repo.heads
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['dev', 'rename', 'bar'])
        assert result.exit_code == 0
        assert not result.exception
        assert 'bar' in repo.heads
        assert 'foo' not in repo.heads


def test_rename_detached_head(git_repo):
    with zazu.util.cd(git_repo.working_tree_dir):
        git_repo.git.checkout('--detach')
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['dev', 'rename', 'bar'])
        assert 'the current HEAD is detached' in result.output
        assert result.exception
        assert result.exit_code != 0

def test_rename_develop(git_repo):
    with zazu.util.cd(git_repo.working_tree_dir):
        assert 'foo' not in git_repo.heads
        git_repo.git.checkout('HEAD', b="develop")
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['dev', 'rename', 'bar'])
        assert 'branch "develop" is protected' in result.output
        assert result.exception
        assert result.exit_code != 0
        assert 'develop' in git_repo.heads

def test_branch_is_current(git_repo_with_out_of_date_local_origin):
    assert not zazu.dev.commands.branch_is_current(git_repo_with_out_of_date_local_origin, 'develop')
    git_repo_with_out_of_date_local_origin.git.pull('origin', 'develop')
    assert zazu.dev.commands.branch_is_current(git_repo_with_out_of_date_local_origin, 'develop')
    git_repo_with_out_of_date_local_origin.git.branch('--unset-upstream')
    assert zazu.dev.commands.branch_is_current(git_repo_with_out_of_date_local_origin, 'develop')


def test_start(git_repo_with_out_of_date_local_origin, mocker):
    git_repo = git_repo_with_out_of_date_local_origin
    mocker.patch('zazu.util.prompt', return_value='description')
    with zazu.util.cd(git_repo.working_tree_dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['dev', 'start', 'bar-1', '--no-verify'])
        assert not result.exception
        assert result.exit_code == 0
        assert 'feature/bar-1_description' in git_repo.heads
        # Test the exists case:
        result = runner.invoke(zazu.cli.cli, ['dev', 'start', 'bar-1', '--no-verify'])
        assert result.exception
        assert result.exit_code != 0
        assert 'branch with same id exists: feature/bar-1_description' in result.output
        assert 'feature/foo-1_description' not in git_repo.heads
        # Test the rename case:
        result = runner.invoke(zazu.cli.cli, ['dev', 'start', 'foo-1', '--no-verify', '--rename'])
        assert not result.exception
        assert result.exit_code == 0
        assert 'feature/foo-1_description' in git_repo.heads
        # Test the rename case with same id:
        result = runner.invoke(zazu.cli.cli, ['dev', 'start', 'foo-1_description2', '--no-verify', '--rename'])
        assert not result.exception
        assert result.exit_code == 0
        assert 'feature/foo-1_description' not in git_repo.heads
        assert 'feature/foo-1_description2' in git_repo.heads
        # Test with exactly same name.
        result = runner.invoke(zazu.cli.cli, ['dev', 'start', 'foo-1_description2', '--no-verify', '--rename'])
        assert not result.exception
        assert result.exit_code == 0
        # Test with no origin.
        git_repo_with_out_of_date_local_origin.git.remote('remove', 'origin')
        result = runner.invoke(zazu.cli.cli, ['dev', 'start', 'bar-2', '--no-verify'])
        assert not result.exception
        assert result.exit_code == 0


def test_start_make_ticket(git_repo_with_local_origin, mocker):
    mocker.patch('zazu.dev.commands.make_ticket', return_value='foo-1_description')
    mocker.patch('zazu.config.Config.issue_tracker')
    mocker.patch('zazu.dev.commands.verify_ticket_exists')
    git_repo = git_repo_with_local_origin
    with zazu.util.cd(git_repo.working_tree_dir):
        git_repo.git.checkout('HEAD', b='develop')
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['dev', 'start'])
        assert not result.exception
        assert result.exit_code == 0
        assert not zazu.dev.commands.verify_ticket_exists.called
        assert 'feature/foo-1_description' in git_repo.heads
        mocker.patch('zazu.config.Config.issue_tracker', side_effect=zazu.issue_tracker.IssueTrackerError('Invalid ID'))
        result = runner.invoke(zazu.cli.cli, ['dev', 'start'])
        assert result.exit_code != 0
        assert 'Invalid ID' in result.output


def test_start_bad_ticket(git_repo_with_local_origin, mocker):
    mocker.patch('zazu.config.Config.issue_tracker')
    mocker.patch('zazu.dev.commands.verify_ticket_exists', returns=True)
    git_repo = git_repo_with_local_origin
    with zazu.util.cd(git_repo.working_tree_dir):
        git_repo.git.checkout('HEAD', b='develop')
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['dev', 'start', 'foo-1_description'])
        assert not result.exception
        assert result.exit_code == 0
        zazu.dev.commands.verify_ticket_exists.assert_called_once()
        assert 'feature/foo-1_description' in git_repo.heads


def test_ticket(mocker):
    mocker.patch('webbrowser.open_new')
    mock_ticket = conftest.dict_to_obj({'browse_url': 'url'})
    mocker.patch('zazu.dev.commands.verify_ticket_exists', return_value=mock_ticket)
    mocked_tracker = mocker.Mock()
    mocker.patch('zazu.config.Config.issue_tracker', return_value=mocked_tracker)
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['dev', 'ticket', 'foo-1'])
    assert not result.exception
    assert result.exit_code == 0
    zazu.dev.commands.verify_ticket_exists.assert_called_once_with(mocked_tracker, 'foo-1')
    webbrowser.open_new.assert_called_once_with('url')


def test_ticket_from_active_branch(mocker, git_repo):
    mocker.patch('webbrowser.open_new')
    mock_ticket = conftest.dict_to_obj({'browse_url': 'url'})
    mocker.patch('zazu.dev.commands.verify_ticket_exists', return_value=mock_ticket)
    mocked_tracker = mocker.Mock()
    mocker.patch('zazu.config.Config.issue_tracker', return_value=mocked_tracker)
    with zazu.util.cd(git_repo.working_tree_dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['dev', 'ticket'])
        assert not result.exception
        assert result.exit_code == 0
        zazu.dev.commands.verify_ticket_exists.assert_called_once_with(mocked_tracker, 'master')
        webbrowser.open_new.assert_called_once_with('url')


def test_review(mocker, git_repo_with_local_origin):
    mocker.patch('webbrowser.open_new')
    mocked_tracker = mocker.Mock()
    mocked_tracker.issue = mocker.Mock(side_effect=zazu.issue_tracker.IssueTrackerError)
    mocked_reviewer = mocker.Mock()
    mocked_reviewer.review = mocker.Mock(return_value=[])
    mocked_reviewer.create_review = mocker.Mock()
    mocker.patch('zazu.config.Config.issue_tracker', return_value=mocked_tracker)
    mocker.patch('zazu.config.Config.code_reviewer', return_value=mocked_reviewer)
    mocker.patch('zazu.util.prompt', side_effect=['title', 'summary'])
    with zazu.util.cd(git_repo_with_local_origin.working_tree_dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['dev', 'review'])
        assert not result.exception
        assert result.exit_code == 0


def test_review_push_fails(mocker, git_repo):
    mocked_reviewer = mocker.Mock()
    mocked_reviewer.review = mocker.Mock(return_value=[])
    mocked_reviewer.create_review = mocker.Mock()
    mocker.patch('zazu.config.Config.code_reviewer', return_value=mocked_reviewer)
    with zazu.util.cd(git_repo.working_tree_dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['dev', 'review'])
        mocked_reviewer.create_review.assert_not_called()
        assert result.exception
        assert result.exit_code == 1


def test_review_dirty_working_tree(mocker, git_repo_with_local_origin, tmp_dir):
    mocked_reviewer = mocker.Mock()
    mocked_reviewer.review = mocker.Mock(return_value=[])
    mocked_reviewer.create_review = mocker.Mock()
    mocker.patch('zazu.config.Config.code_reviewer', return_value=mocked_reviewer)
    with zazu.util.cd(tmp_dir):
        with open('un-tracked_file.txt', 'w'):
            pass
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['dev', 'review'])
        mocked_reviewer.create_review.assert_not_called()
        assert result.exception
        assert result.exit_code == 1


def test_review_existing(mocker, git_repo):
    mocker.patch('webbrowser.open_new')
    mocked_tracker = mocker.Mock()
    mocked_tracker.issue = mocker.Mock(return_value=None)
    mocked_reviewer = mocker.Mock()
    mocked_review = mocker.Mock()
    mocked_review.browse_url = 'url'
    mocked_reviewer.review = mocker.Mock(return_value=[mocked_review])
    mocked_reviewer.create_review = mocker.Mock()
    mocker.patch('zazu.config.Config.issue_tracker', return_value=mocked_tracker)
    mocker.patch('zazu.config.Config.code_reviewer', return_value=mocked_reviewer)
    mocker.patch('zazu.util.prompt', side_effect=['title', 'summary'])
    with zazu.util.cd(git_repo.working_tree_dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['dev', 'review'])
        assert not result.exception
        assert result.exit_code == 0


def test_status(mocker, git_repo):
    mocked_tracker = mocker.Mock()
    mocked_issue = mocker.Mock()
    mocked_issue.name = ''
    mocked_issue.description = ''
    mocked_issue.status = ''
    mocked_tracker.issue = mocker.Mock(return_value=mocked_issue)
    mocked_reviewer = mocker.Mock()
    mocked_review = mocker.Mock()
    mocked_review.name = ''
    mocked_review.description = ''
    mocked_review.merged = False
    mocked_review.head = ''
    mocked_review.base = ''
    mocked_review.status = ''
    mocked_reviewer.review = mocker.Mock(return_value=[mocked_review])
    mocked_reviewer.create_review = mocker.Mock()
    mocker.patch('zazu.config.Config.issue_tracker', return_value=mocked_tracker)
    mocker.patch('zazu.config.Config.code_reviewer', return_value=mocked_reviewer)
    with zazu.util.cd(git_repo.working_tree_dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['dev', 'status'])
        assert not result.exception
        assert result.exit_code == 0


def test_status_no_matching_issue(mocker, git_repo):
    mocked_tracker = mocker.Mock()
    mocked_tracker.issue = mocker.Mock(side_effect=zazu.issue_tracker.IssueTrackerError)
    mocked_reviewer = mocker.Mock()
    mocked_reviewer.review = mocker.Mock(return_value=[])
    mocked_reviewer.create_review = mocker.Mock()
    mocker.patch('zazu.config.Config.issue_tracker', return_value=mocked_tracker)
    mocker.patch('zazu.config.Config.code_reviewer', return_value=mocked_reviewer)
    with zazu.util.cd(git_repo.working_tree_dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['dev', 'status'])
        assert not result.exception
        assert result.exit_code == 0
        assert "No ticket found" in result.output


def test_builds():
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['dev', 'builds'])
    assert result.exception
    assert result.exit_code != 0


def test_complete_git_branch(git_repo):
    with zazu.util.cd(git_repo.working_tree_dir):
        assert zazu.dev.commands.complete_git_branch(None, [], 'mas') == ['master']


def test_complete_issue_and_complete_feature(mocker):
    mocked_config = mocker.Mock()
    mocked_tracker = mocker.Mock()
    mocked_issue = mocker.Mock()
    mocked_issue.__str__ = mocker.Mock(return_value='ZZ-1')
    mocked_issue.name = 'name'
    mocked_tracker.issues = mocker.Mock(return_value=[mocked_issue])
    mocked_config.issue_tracker = mocker.Mock(return_value=mocked_tracker)
    mocker.patch('zazu.config.Config', return_value=mocked_config)
    assert zazu.dev.commands.complete_issue(None, [], 'Z') == [(str(mocked_issue), 'name')]
    assert zazu.dev.commands.complete_issue(None, [], 'Na') == [(str(mocked_issue), 'name')]
    assert zazu.dev.commands.complete_issue(None, [], '') == [(str(mocked_issue), 'name')]
    assert zazu.dev.commands.complete_issue(None, [], 'foo') == []
    assert zazu.dev.commands.complete_feature(None, [], 'Z') == [('feature/ZZ-1', 'name')]
