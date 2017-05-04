import contextlib
import git
import tempfile
import os
import pytest
import yaml


@pytest.fixture
def tmp_dir():
    return tempfile.mkdtemp()


@pytest.fixture
def git_repo(tmp_dir):
    print('Tmpdir: {}'.format(tmp_dir))
    repo = git.Repo.init(tmp_dir)
    readme = os.path.join(tmp_dir, 'README.md')
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
            'autopep8': {},
            'astyle': {}
        }
    }
    with open(os.path.join(root, 'zazu.yaml'), 'a') as file:
        file.write(yaml.dump(style_config))
    return git_repo


@pytest.fixture()
def repo_with_build_config(git_repo):
    root = git_repo.working_tree_dir
    style_config = {
        'components': [
            {
                'name': 'zazu',
                'goals': [
                    {
                        'name': 'echo_foobar',
                        'builds': [
                            {
                                'arch': 'python',
                                'script': ['echo "foobar"']
                            }
                        ]
                    },
                    {
                        'name': 'cmake_build',
                        'builds': [
                            {
                                'arch': 'host'
                            }
                        ]
                    }
                ]
            }
        ]
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
