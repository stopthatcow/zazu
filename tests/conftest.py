import git
import tempfile
import os
import pytest


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