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


@pytest.fixture()
def before(tmpdir, request):

    filepath = request.module.__file__
    test_dir, f = os.path.split(filepath)
    test_file, ext = os.path.splitext(f)
    test_name = request.node.name

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

    print('\nbefore each test')
 
@pytest.mark.usefixtures("before")
class Test:

    def test_base(self, tmpdir):
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

        cpm(cli_args)

        manifest =  tmpdir.join('./pipelines_files/pipelinemanifest.yml')
        manifest_validation = tmpdir.join('./validation_pipelinemanifest.yml')

        assert os.path.isfile(manifest)
        #assert filecmp.cmp(manifest, manifest_validation)
        assert manifest.read() == manifest_validation.read()