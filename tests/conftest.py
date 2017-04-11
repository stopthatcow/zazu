import contextlib
import git
import tempfile
import os
import pytest
import yaml

@pytest.fixture
def git_repo():
    dir = tempfile.mkdtemp()
    print('Tmpdir: {}'.format(dir))
    repo = git.Repo.init(dir)
    readme = os.path.join(dir, 'README.md')
    with open(readme, 'w'):
        pass
    repo.index.add([readme])
    repo.index.commit('initial readme')
    return repo

@pytest.fixture()
def repo_with_style(git_repo):
    root = git_repo.working_tree_dir
    style_config = {
        'style': {
            'exclude': ['dependency'],
            'autopep8': {
                'options': ''
            },
            'astyle': {
                'options': ''
            }
        }
    }
    with open(os.path.join(root, 'zazu.yaml'), 'a') as file:
        file.write(yaml.dump(style_config))
    return git_repo

@pytest.fixture()
def repo_with_empty_zazu_file(git_repo):
    root = git_repo.working_tree_dir
    with open(os.path.join(root, 'zazu.yaml'), 'a'):
        pass
    return git_repo


@pytest.fixture()
def repo_with_missing_style(git_repo):
    root = git_repo.working_tree_dir
    config = {
        'components': [{'name': 'zazu'}]
    }
    with open(os.path.join(root, 'zazu.yaml'), 'a') as file:
        file.write(yaml.dump(config))
    return git_repo


@contextlib.contextmanager
def working_directory(path):
    """Changes the working directory to the given path back to its previous value on exit"""
    prev_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)
