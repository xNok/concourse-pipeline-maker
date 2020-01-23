#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CONCOURSE PIPELINE MAKER

Usage:
  cpm find -i <inputfile> [-rv]
  cpm [options]
  cpm <pipeline_name>... [options]
  cpm -h | --help

Find Options:
  -r, --resources                           Extract all resource, when using cpm find
  -v, --vars                                Extract all variables, when using cpm find

Options:
  -i <inputfile>, --ifile <inputfile>       Path to the pipeline manifest. [default: pipelinemanifest.json]
  -o <outputfile>, --ofile <outputfile>     Path to the output folder. [default: ./pipelines_files]
  -p <text_to_search:replacement_text>      Search and replace operation applied before procssing the pipeline manifest.
                                            Very usefull when working locally.
  -c <sfolder>, --ci <sfolder>              When publishing pipelines in a repo make sure it is compatible with concourse/concourse-pipeline-resource
  -x <cli_ext>, --cli <cli_ext>             Generate the Fly command line for each pipeline [default: cmd]
  Options-Flags:
  --copy                                    Systematically copy the pipeline in the output directory.
  --debug                                   Set the log level to debug
  -h, --help                                Show the help screen.
"""

# Utilitaire pour gérer les commande lines
from docopt import docopt

from deepmerge import always_merger
from cli_cpm.h_colors import *

import logging

# Generer le fichier de configuration des pipelines
from lib.entities.pipeline_config import PipelineConfig
from lib.use_cases.create_fly_cmd import generate_cli
from lib.use_cases.find_params    import find_params

from pathlib import Path
import yaml, json
import copy, sys, os, os.path
import errno
import shutil
from shutil import copyfile
import fileinput

import asyncio

def main():
    ################################################################################################
    #### Pre-processing
    ################################################################################################
    cli_args = docopt(__doc__, argv=None, help=True, version=None, options_first=False)

    print("""
    ####################################
    #                                  #
    #     CONCOURSE PIPELINE MAKER     #
    #                                  #
    ####################################
    """)

    print("""
    {tag} Use {color} cpm -h {reset} to lear how to use the command line"
    {tag} Use {color} cpm --it {reset} to activate the interactive guide"
    """.format(tag=tag.info,color=fg.green,reset=ft.reset,))

    if cli_args["find"]:
        find(cli_args)
    else:

        rc_file = ".cpmrc"
        cli_args_rc = {}
        if os.path.exists(rc_file):
            print(tag.info, "Loading runtime config from .cpmrc file", ft.reset)
            with open(rc_file) as f:
                cli_args_rc = json.load(f)
        else:
            print(tag.info, "Locally you can use " + fg.green + "a .cpmrc file" + ft.reset + "to avoide typing cpm flag every time")

        cli_args = always_merger.merge(cli_args, cli_args_rc)

        if cli_args["--debug"]:
            print("")
            print("This is what we gonna do:")
            print(json.dumps(cli_args, sort_keys=True, indent=4))
            print("")

        run(cli_args)

def find(cli_args):

    ifile = cli_args["--ifile"]

    if cli_args["--resources"]:
        print(f"{tag.info} Searching params in {fg.green} {ifile} {ft.reset}.")
        print(find_params(cli_args["--ifile"]))

def run(cli_args):

    # Set the log level
    if cli_args["--debug"]:
        logging.basicConfig(level=logging.DEBUG)

    # 0. do we have a pipeline manifest?
    if not os.path.isfile(cli_args["--ifile"]):
        print(tag.warn, "Pipeline Manifest not found. %s" % cli_args["--ifile"])

    # 1. Apply scripts according to arguments
    ## --ofile argument
    if not os.path.exists(cli_args["--ofile"]):
        print("Creating output directory %s" % str(cli_args["--ofile"]))
        print("")
        os.makedirs(cli_args["--ofile"])

    ## -p arguments, replace to resolve local path
    if cli_args["-p"]:
        print(fg.orange, "Activate replacement <text_to_search:replacement_text> ", ft.reset)
        print(json.dumps(cli_args["-p"], sort_keys=True, indent=4))
    else:
        print(tag.info, "Locally use " + fg.green + "cpm -p <text_to_search:replacement_text>" + ft.reset + " to correct the paths in the pipelinemanifest.json")

    ################################################################################################
    #### II. Script Start
    ################################################################################################

    # I Parsing the pipeline manifest
    print("Processing %s" % str(cli_args["--ifile"]))

    if cli_args["-p"]:
        with fileinput.FileInput(cli_args["--ifile"], inplace=True) as file:
            for line in file:
                for p in cli_args["-p"]:
                    print(line.replace(p.split(":")[0], p.split(":")[1]), end='')

    with open(cli_args["--ifile"]) as f:
        filename, file_extension = os.path.splitext(cli_args["--ifile"])
        if file_extension == ".json":
            pipelinemanifest = json.load(f)
        elif file_extension == ".yml":
            pipelinemanifest = yaml.safe_load(f)

    print(ft.underline + bg.green + fg.white, "Processing pipeline manifest ...  ",ft.reset)
    print("")

    # II.2. Read the configuration for the space and templates
    space_config, template_configs = make_configs(pipelinemanifest)

    # II.3. Read the configuration for each pipeline
    print(tag.info, "%s Pipelines found" % len(pipelinemanifest["pipelines"]))

    loop = asyncio.new_event_loop()
    pipelines_file = loop.run_until_complete(
        make_pipelines_loop(loop, cli_args, pipelinemanifest, template_configs, space_config)
    )
    loop.close()
  
    print("")
    print(ft.underline + bg.green + fg.white + "  Le Ficher pipelinemanifest.yml est prêt  " + ft.reset)
    print(fg.green + "Go check it out: " + fg.yellow + cli_args["--ofile"] + '/pipelinemanifest.yml' + ft.reset)
    print("")

    if not cli_args["--cli"]:
        print(tag.info, "Use the flag " + fg.green + "--cli" + ft.reset + " to generate executable file to generate pipeline")
    else:
        print(tag.info, "Executable file have been generated, see in folder: " + fg.green + "set-pipelines/" + ft.reset)

    if not cli_args["--copy"]:
        print(tag.info, "Use the flag " + fg.green + "--copy" + ft.reset + " to copy all necessary files in " + cli_args["--ofile"])
    else:
        print(tag.info, "All files have been copied, see in folder:" + fg.green + cli_args["--ofile"] + ft.reset)

    #4. Generate the pipelines_file
    # Ecrire le ficher des pipelines
    with open(cli_args["--ofile"] + '/pipelinemanifest.yml', 'w') as outfile:
        yaml.safe_dump(pipelines_file, outfile, default_flow_style=False)

    if cli_args["-p"]:
        with fileinput.FileInput([cli_args["--ifile"],cli_args["--ofile"]+'/pipelinemanifest.yml'] , inplace=True) as file:
            for line in file:
                for p in cli_args["-p"]:
                    print(line.replace(p.split(":")[1], p.split(":")[0]), end='')


def make_configs(pipelinemanifest):

    # II.1. Read the configuration for the space
    space_config = PipelineConfig()
    if "configs" in pipelinemanifest:
        logging.debug("Space config found")
        print(tag.info, "Space config found", ft.reset)
        space_config.read_pipeline_config(pipelinemanifest["configs"])
    else:
        print(tag.info, "Use a section " + fg.green + "configs" + ft.reset + " in pipelinemanifest.json to aplly configuration to all pipelines")

    # II.2. Read the configuration for the templates
    template_configs = {}
    if "templates" in pipelinemanifest:
        print(tag.info, "%s Templates found" % len(pipelinemanifest["templates"]))
        print(", ".join(pipelinemanifest["templates"].keys()))
        for tpl in pipelinemanifest["templates"]:
            logging.debug("Template config found")
            template_configs[tpl] = PipelineConfig(data=pipelinemanifest["templates"][tpl], default=space_config)
    else:
        print(tag.info, "Use a section " + fg.green + "templates" + ft.reset + " in pipelinemanifest.json to create resuable configuration")

    return space_config, template_configs

async def make_pipelines_loop(loop, cli_args, pipelinemanifest, template_configs, space_config):
    added_tasks = []
    pipelines_file = { "pipelines": [] }

    print('Async Pipeline creation: adding tasks')

    for p in pipelinemanifest["pipelines"]:
        pipeline_config = PipelineConfig(data=p, templates=template_configs, default=space_config)

        # Skip this pipeline if it is not one of the specified pipelines
        if cli_args["<pipeline_name>"] and pipeline_config.get("name") not in cli_args["<pipeline_name>"]:
            continue

        task = asyncio.create_task(
            make_pipeline(pipeline_config, cli_args, pipelines_file)
        )
        added_tasks.append(task)

    print('Async Pipeline creation: done adding tasks')

    running_tasks = added_tasks[::]

    # wait until we see that all tasks have completed
    while running_tasks:
        running_tasks = [x for x in running_tasks if not x.done()]
        await asyncio.sleep(0)

    print('Async Pipeline creation: done running tasks')

    return pipelines_file

async def make_pipeline(pipeline_config, cli_args, pipelines_file):

    pipeline_config.make_pipeline(out_directory=cli_args["--ofile"])

    ## II.2.6 Copy (optional) -> copy les fichiers dans le dossier output
    if cli_args["--copy"]:
        logging.debug("** copy files")

        outputfile = cli_args["--ofile"] + "/config_files/" + pipeline_config.get("name") + ".yml"

        # config_file
        if not os.path.exists(cli_args["--ofile"]+ "/config_files/"):
            os.mkdir(cli_args["--ofile"] + "/config_files/")

        try:
            copyfile(pipeline_config.get("config_file"), outputfile)
        except shutil.SameFileError as e:
            pass

        _p = Path(cli_args["--ofile"])
        _p = _p / "config_files" / (pipeline_config.get("name") + ".yml")

        pipeline_config.set("config_file", str(_p.as_posix()))
        # vars_files
        vars_files = []
        for f in pipeline_config.get("vars_files"):
            outputfile =  cli_args["--ofile"] + "/vars_files/" + os.path.basename(f)

            if not os.path.exists(cli_args["--ofile"] + "/vars_files/"):
                os.mkdir(cli_args["--ofile"] + "/vars_files/")

            try:
                copyfile(f, outputfile)
            except shutil.SameFileError as e:
                pass

            _p = Path(cli_args["--ofile"])
            _p = _p / "vars_files" / os.path.basename(f)

            vars_files.append(str(_p.as_posix()))

        pipeline_config.set("vars_files", vars_files)

    ## II.2.7 Cli (optionnal) -> generate the cli
    if cli_args["--cli"]:
        logging.debug("** gen cli")
        generate_cli(pipeline_config, ext=cli_args["--cli"], out_directory=cli_args["--ofile"])

    ## II.2.8 Cli (optionnal) -> change the path tu be used in concourse
    if cli_args["--ci"]:
        # edit config file
        _p = Path(cli_args["--ci"])
        _p = _p / pipeline_config.get("config_file")
        pipeline_config.set("config_file", str(_p.as_posix()))
        # edit var files
        vars_files = []
        for f in pipeline_config.get("vars_files"):

            _p = Path(cli_args["--ci"] )
            _p = _p / f

            vars_files.append(str(_p.as_posix()))

        pipeline_config.set("vars_files", vars_files)

    # 3.3 Save the pipeline
    print(fg.green, "Ajout de " + pipeline_config.get("name") + " au pipelinemanifest.yml", ft.reset)
    pipelines_file["pipelines"].append(pipeline_config.p_config)

    if pipeline_config.get("name") in cli_args["<pipeline_name>"]:
        print("\n\n" + fg.blue + "***** Setup your new pipeline *****" + ft.reset)
        print(pipeline_config.get("cli"))
