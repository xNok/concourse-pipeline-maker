import pytest
from shutil import copyfile
from shutil import copytree
import filecmp
import difflib
import os

from lib.use_cases.find_params import find_params

###
#The basic fictures are:
# * Generate the fly cli command line
# * Generate the pipelines_file for concourse-pipeline-resource
###


@pytest.fixture
def golden_file(tmpdir, request):

    if request.param:
        test_name = request.param
    else:
        test_name = request.node.name


    filepath = request.module.__file__
    test_dir, f = os.path.split(filepath)

    # Resolve paths
    resources = os.path.join(test_dir, "resources")
    resources_assets = os.path.join(resources, "pipelines_assets")

    # Prepare env
    copytree(resources_assets, os.path.join(tmpdir, "pipelines_assets"))

    # We work in temps dir
    os.chdir(tmpdir)

    golden_file = {}

    return golden_file
 
class Test:


    @pytest.mark.parametrize("golden_file", [("test_base")], indirect=True)
    def test_find_params(self, tmpdir, golden_file):
        """
        GIVEN: pipeline file
        return all params
        """

        result = find_params("./pipelines_assets/pipeline-with-params.yml")

        assert result == set(['branch','linux', 'ubuntu', 'resource-name'])
