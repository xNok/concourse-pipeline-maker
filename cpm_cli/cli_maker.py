# coding: utf-8
"""
CONCOURSE PIPELINE MAKER

Usage:
  cpm [--ifile <inputfile>] [--ofile <outputfile>]
    [-p <text_to_search:replacement_text>...] [options]
  cpm <pipeline_name>... [--ifile <inputfile>] [--ofile <outputfile>]
    [-p <text_to_search:replacement_text>...] [options]
  cpm -h | --help

Options:
  -i <inputfile>, --ifile <inputfile>       Path to the pipeline manifest. [default: pipelinemanifest.json]
  -o <outputfile>, --ofile <outputfile>     Path to the output folder. [default: ./pipelines_files]
  -p <text_to_search:replacement_text>      Search and replace operation applied before procssing the pipeline manifest.
                                            Very usefull when working locally.
  -c <sfolder>, --ci <sfolder>              When publishing pipelines in a repo make sure it is compatible with concourse/concourse-pipeline-resource
Options-Flags:
  --cli                                     Generate the Fly command line for each pipeline
  --copy                                    Systematically copy the pipeline in the output directory.
  --debug                                   Set the log level to debug
  --fly3                                    Retro-compatibility with concourse and fly 3
  -h, --help                                Show the help screen.
"""

# Utilitaire pour gérer les commande lines
from docopt import docopt
from shutil import copyfile
from deepmerge import always_merger

from .h_colors import *

import logging

# Generer le fichier de configuration des pipelines
from pipeline_maker.pipeline_config import PipelineConfig

import yaml, json
import copy
import sys, os
import os.path
from pathlib import Path
import errno
import shutil
import fileinput

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

    rc_file = ".cpmrc"
    cli_args_rc = {}
    if os.path.exists(rc_file):
        print(tag.info, "Loading runtime config from .cpmrc file", ft.reset)
        with open(rc_file) as f:
            cli_args_rc = json.load(f)
    else:
        print(tag.info, "Locally you can use " + fg.green + "a .cpmrc file" + ft.reset + "to avoide typing cpm flag every time")

    cli_args = always_merger.merge(cli_args, cli_args_rc)

    run(cli_args)

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

    print("")
    print("This is what we gonna do:")
    print(json.dumps(cli_args, sort_keys=True, indent=4))
    print("")

    print(ft.underline + bg.green + fg.white, "Processing pipeline manifest ...  ",ft.reset)
    print("")

    pipelines_file = { "pipelines": [] }

    # II.1. Read the configuration for the space
    space_config = PipelineConfig()
    if "configs" in pipelinemanifest:
        logging.debug("Space config found")
        print(tag.info, "Space config found", ft.reset)
        space_config.read_pipeline_config(pipelinemanifest["configs"])
    else:
        print(tag.info, "Use a section " + fg.green + "configs" + ft.reset + " in pipelinemanifest.json to aplly configuration to all pipelines")


    template_configs = {}
    if "templates" in pipelinemanifest:
        print(tag.info, "%s Templates found" % len(pipelinemanifest["templates"]))
        print(", ".join(pipelinemanifest["templates"].keys()))
        for tpl in pipelinemanifest["templates"]:
            logging.debug("Template config found")
            template_configs[tpl] = PipelineConfig(space_config, pipelinemanifest["templates"][tpl])
    else:
        print(tag.info, "Use a section " + fg.green + "templates" + ft.reset + " in pipelinemanifest.json to create resuable configuration")

    # II.2. Read the configuration for each pipeline
    print(tag.info, "%s Pipelines found" % len(pipelinemanifest["pipelines"]))
    for p in pipelinemanifest["pipelines"]:

        # II.2.1 Create pipeline config
        if "template" in p or "-tpl" in p:
            # II.2.2a Templates -> start by applying the right template
            template = p["-tpl"] if "-tpl" in p else p["template"]
            logging.debug("template:" + template)
            pipeline_config = PipelineConfig(template_configs[template], p)
        else:
            # II.2.2b Space config -> start by applying the space config
            pipeline_config = PipelineConfig(space_config, p)

        logging.debug(pipeline_config.get("name"))
        logging.debug(pipeline_config.p_config)
        if cli_args["<pipeline_name>"] and pipeline_config.get("name") not in cli_args["<pipeline_name>"]:
            continue

        ## III.2.3 Partials -> merge all the partials into one file
        if pipeline_config.get("partials"):
            logging.debug("partials:" + str(pipeline_config.get("partials")))
            pipeline_config.process_partials()

        ## II.2.4 Merging -> modify the pipeline config
        if pipeline_config.get("merge"):
            logging.debug("merge:" + str(pipeline_config.get("merge")))
            try:
                pipeline_config.process_to_be_merged(out_directory=cli_args["--ofile"])
            except IOError as e:
                print(fg.red, "Error: File does not appear to exist.", ft.reset)
                print(e)
                print(tag.info, "Locally use " + fg.green + "cpm -p <text_to_search:replacement_text>" + ft.reset + " to correct the paths in the pipelinemanifest.json")
                continue

        ## II.2.5 Copy (optional) -> copy les fichiers dans le dossier output
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

        ## II.2.6 Cli (optionnal) -> generate the cli
        if cli_args["--cli"]:
            logging.debug("** gen cli")
            pipeline_config.process_cli()

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

    print("")
    print(ft.underline + bg.green + fg.white + "  Le Ficher pipelinemanifest.yml est prêt  " + ft.reset)
    print(fg.green + "Go check it out: " + fg.yellow + cli_args["--ofile"] + '/pipelinemanifest.yml' + ft.reset)
    print("")

    if not cli_args["--cli"]:
        print(tag.info, "Use the flag " + fg.green + "--cli" + ft.reset + " to generate executable file to generate pipeline")
    else:
        print(tag.info, "Executable file have been generated, see in folder: " + fg.green + "fly_cli/" + ft.reset)

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
