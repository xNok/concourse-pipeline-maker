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
    resources_pipelines_validation = os.path.join(resources, "pipelines_validation")
    resources_validation = os.path.join(resources, "validation" , test_name + "_pipelinemanifest.yml")

    # Prepare env
    copytree(resources_assets, os.path.join(tmpdir, "pipelines_assets"))
    copytree(resources_pipelines_validation, os.path.join(tmpdir, "pipelines_validation"))
    copyfile(resources_manifest, os.path.join(tmpdir, "pipelinemanifest.json"))
    copyfile(resources_validation, os.path.join(tmpdir, "validation_pipelinemanifest.yml"))

    # We work in temps dir
    os.chdir(tmpdir)

    manifest = tmpdir.join('./pipelines_files/pipelinemanifest.yml')
    manifest_validation = tmpdir.join('./validation_pipelinemanifest.yml')

    return {"generated": manifest, "expected": manifest_validation, "tmpdir": tmpdir}
 
class Test:

    cli_args= {
        "--ci": None,
        "--cli": False,
        "--copy": False,
        "--debug": False,
        "--help": False,
        "--ifile": "pipelinemanifest.json",
        "--ofile": "./pipelines_files",
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

    @pytest.mark.parametrize("manifest", [("test_adv_merge")], indirect=True)
    def test_merge(self, tmpdir, manifest):
        """
        Given fly cli arguments, generate: 
        1. pipelinemanifest.yml
        """

        cpm(self.cli_args)

        assert os.path.isfile(manifest["generated"])
        #assert filecmp.cmp(manifest, manifest_validation)
        assert manifest["generated"].read() == manifest["expected"].read()

    @pytest.mark.parametrize("manifest", [("test_adv_config_replace")], indirect=True)
    def test_adv_config_replace(self, tmpdir, manifest):
        """
        argument --cli
        generate set_{pipeline}.cmd
        """

        cli_args = self.cli_args.copy()

        cli_args["-p"] = ["concourse:pipelines_assets"]

        cpm(cli_args)

        assert os.path.isfile(manifest["generated"])
        assert manifest["generated"].read() == manifest["expected"].read()

    @pytest.mark.parametrize("manifest", [("test_adv_config_ci")], indirect=True)
    def test_adv_config_ci(self, tmpdir, manifest):
        """
        argument --cli
        generate set_{pipeline}.cmd
        """

        cli_args = self.cli_args.copy()

        cli_args["--ci"] = "git-infra-res"

        cpm(cli_args)

        assert os.path.isfile(manifest["generated"])
        assert manifest["generated"].read() == manifest["expected"].read()

    @pytest.mark.parametrize("manifest", [("test_adv_partials")], indirect=True)
    def test_adv_partials(self, tmpdir, manifest):
        """
        Given fly cli arguments, generate: 
        1. pipelinemanifest.yml
        """

        cpm(self.cli_args)

        assert os.path.isfile(manifest["generated"])
        #assert filecmp.cmp(manifest, manifest_validation)
        assert manifest["generated"].read() == manifest["expected"].read()

    @pytest.mark.parametrize("manifest", [("test_adv_partials_resources")], indirect=True)
    def test_adv_resources(self, tmpdir, manifest):
        """
        Given fly cli arguments, generate: 
        1. pipelinemanifest.yml
        """

        cpm(self.cli_args)

        assert os.path.isfile(manifest["generated"])
        #assert filecmp.cmp(manifest, manifest_validation)
        assert manifest["generated"].read() == manifest["expected"].read()
        
        pipeline_to_validate = manifest["tmpdir"].join('./pipelines_files/config_files/Test 3.yml')
        pipeline_to_expect   = manifest["tmpdir"].join('./pipelines_validation/pipelines_files/config_files/Test 3.yml')
        assert os.path.isfile(pipeline_to_validate)
        assert pipeline_to_validate.read() == pipeline_to_expect.read()

        pipeline_to_validate = manifest["tmpdir"].join('./pipelines_files/config_files/Test 4.yml')
        pipeline_to_expect   = manifest["tmpdir"].join('./pipelines_validation/pipelines_files/config_files/Test 4.yml')
        assert os.path.isfile(pipeline_to_validate)
        assert pipeline_to_validate.read() == pipeline_to_expect.read()