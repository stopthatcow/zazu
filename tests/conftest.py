import contextlib
import git
import tempfile
import os
import pytest
import ruamel.yaml as yaml


@pytest.fixture
def tmp_dir():
    return tempfile.mkdtemp()


@pytest.fixture
def empty_repo(tmp_dir):
    return git.Repo.init(tmp_dir)


@pytest.fixture
def git_repo(empty_repo):
    dir = empty_repo.working_tree_dir
    readme = os.path.join(dir, 'README.md')
    with open(readme, 'w'):
        pass
    empty_repo.index.add([readme])
    empty_repo.index.commit('initial readme')
    return empty_repo


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
        'style': [
            {'exclude': ['dependency'],
             'stylers':[
                {'type': 'autopep8'},
                {'type': 'clang-format'}
            ]
            }
        ]
    }
    with open(os.path.join(root, 'zazu.yaml'), 'a') as file:
        yaml.dump(style_config, file)
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
        yaml.dump(config, file)
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


@pytest.fixture()
def git_repo_with_out_of_date_local_origin(git_repo):
    """Create a local remote with 2 clients.

    Use 1 client to update develop so that the other client is out of date.
    Return the out of date client.

    """
    temp_dir = tempfile.mkdtemp()
    git.Repo.init(temp_dir, bare=True)
    git_repo.create_remote('origin', temp_dir)
    git_repo.git.checkout('-b', 'develop')
    git_repo.git.push('-u', 'origin', 'develop')
    other_client = git.Repo.init(tempfile.mkdtemp())
    other_client.create_remote('origin', temp_dir)
    other_client.git.checkout('-b', 'develop')
    other_client.git.pull('origin', 'develop')
    readme = os.path.join(other_client.working_tree_dir, 'README.md')
    with open(readme, 'w') as f:
        f.write('foo')
    other_client.index.add([readme])
    other_client.index.commit('updated readme')
    other_client.git.push('-u', 'origin', 'develop')

    return git_repo


@contextlib.contextmanager
def working_directory(path):
    """Changes the working directory to the given path back to its previous value on exit."""
    prev_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def dict_to_obj(dictionary):
    """Creates a object from a dictionary."""
    class Struct(object):

        def __init__(self, d):
            for a, b in d.items():
                if isinstance(b, (list, tuple)):
                    setattr(self, a, [Struct(x) if isinstance(x, dict) else x for x in b])
                else:
                    setattr(self, a, Struct(b) if isinstance(b, dict) else b)
    return Struct(dictionary)
