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
    repo = git.Repo.init(tmp_dir)
    readme = os.path.join(tmp_dir, 'README.md')
    with open(readme, 'w'):
        pass
    repo.index.add([readme])
    repo.index.commit('initial readme')
    return repo


@pytest.fixture
def git_repo_with_bad_config(git_repo):
    zazu_file = os.path.join(git_repo.working_tree_dir, 'zazu.yaml')
    with open(zazu_file, 'w') as f:
        f.write('{')
    return git_repo


@pytest.fixture()
def repo_with_style(git_repo):
    root = git_repo.working_tree_dir
    style_config = {
        'style': {
            'exclude': ['dependency'],
            'autopep8': {},
            'clang-format': {}
        }
    }
    with open(os.path.join(root, 'zazu.yaml'), 'a') as file:
        file.write(yaml.dump(style_config))
    return git_repo


@pytest.fixture()
def repo_with_build_config(git_repo):
    root = git_repo.working_tree_dir
    config = {
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
        file.write(yaml.dump(config))
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


@pytest.fixture()
def repo_with_github_as_origin(git_repo):
    git_repo.create_remote('origin', 'http://github.com/stopthatcow/zazu')
    return git_repo


@pytest.fixture()
def git_repo_with_local_origin(git_repo):
    temp_dir = tempfile.mkdtemp()
    git.Repo.init(temp_dir, bare=True)
    git_repo.create_remote('origin', temp_dir)
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


def dict_to_obj(dictionary):
    """Creates a object from a dictionary"""
    class Struct(object):

        def __init__(self, d):
            for a, b in d.items():
                if isinstance(b, (list, tuple)):
                    setattr(self, a, [Struct(x) if isinstance(x, dict) else x for x in b])
                else:
                    setattr(self, a, Struct(b) if isinstance(b, dict) else b)
    return Struct(dictionary)
