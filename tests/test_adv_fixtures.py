import pytest
from shutil import copyfile
from shutil import copytree
import filecmp
import difflib
import os

from cpm_cli.cli_maker import run as cpm

###
#The basic fictures are:
# * Generate the fly cli command line
# * Generate the pipelines_file for concourse-pipeline-resource
###


@pytest.fixture
def manifest(tmpdir, request):

    if request.param:
        test_name = request.param
    else:
        test_name = request.node.name


    filepath = request.module.__file__
    test_dir, f = os.path.split(filepath)

    # Resolve paths
    resources = os.path.join(test_dir, "resources")
    resources_assets = os.path.join(resources, "pipelines_assets")
    resources_manifest = os.path.join(resources, test_name + "_manifest.json")
    resources_validation = os.path.join(resources, "validation" , test_name + "_pipelinemanifest.yml")

    # Prepare env
    copytree(resources_assets, os.path.join(tmpdir, "pipelines_assets"))
    copyfile(resources_manifest, os.path.join(tmpdir, "pipelinemanifest.json"))
    copyfile(resources_validation, os.path.join(tmpdir, "validation_pipelinemanifest.yml"))

    # We work in temps dir
    os.chdir(tmpdir)

    manifest = tmpdir.join('./pipelines_files/pipelinemanifest.yml')
    manifest_validation = tmpdir.join('./validation_pipelinemanifest.yml')

    return {"generated": manifest, "expected": manifest_validation}
 
class Test:

    cli_args= {
        "--cli": False,
        "--copy": False,
        "--debug": False,
        "--help": False,
        "--ifile": "pipelinemanifest.json",
        "--it": False,
        "--ofile": "./pipelines_files",
        "--prod": False,
        "--static": "",
        "-p": [],
        "<pipeline_name>": []
    }

    @pytest.mark.parametrize("manifest", [("test_adv_template")], indirect=True)
    def test_template(self, tmpdir, manifest):
        """
        Given fly cli arguments, generate: 
        1. pipelinemanifest.yml
        """

        cpm(self.cli_args)

        assert os.path.isfile(manifest["generated"])
        #assert filecmp.cmp(manifest, manifest_validation)
        assert manifest["generated"].read() == manifest["expected"].read()

    # @pytest.mark.parametrize("manifest", [("test_merge")], indirect=True)
    # def test_merge(self, tmpdir, manifest):
    #     """
    #     Given fly cli arguments, generate: 
    #     1. pipelinemanifest.yml
    #     """

    #     cpm(self.cli_args)

    #     assert os.path.isfile(manifest["generated"])
    #     #assert filecmp.cmp(manifest, manifest_validation)
    #     assert manifest["generated"].read() == manifest["expected"].read()