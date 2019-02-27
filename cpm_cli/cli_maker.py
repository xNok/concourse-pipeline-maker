
# coding: utf-8
"""
CONCOURSE PIPELINE MAKER

Usage:
  cpm [--ifile <inputfile>] [--ofile <outputfile>] 
    [-p <text_to_search:replacement_text>...] [options]
  cpm <pipeline_name>... [--ifile <inputfile>] [--ofile <outputfile>] 
    [-p <text_to_search:replacement_text>...] [options]
  cpm -h | --help
  cpm --it

Options:                         
  -i <inputfile>, --ifile <inputfile>       Path to the pipeline manifest. [default: pipelinemanifest.json]
  -o <outputfile>, --ofile <outputfile>     Path to the output folder. [default: ./pipelines_files]
  -p <text_to_search:replacement_text>      Search and replace operation applied before procssing the pipeline manifest.
                                            Very usefull when working locally.
  -s <sfolder>, --static <sfolder>          When publishing pipelines in a repo make sur it si compatible with concourse/concourse-pipeline-resource [default: git-infra-res/]
Options-Flags:
  --cli                                     Generate the Fly command line for each pipeline
  --copy                                    Systematically copy the pipeline in the output directory.
  --prod                                    Process the prod section of the pipeline manifest instead of the nonprod
  --debug                                   Set the log level to debug
  --it                                      Interactive mode

  -h, --help                                Show the help screen.
"""

# Utilitaire pour gérer les commande lines
from docopt import docopt
from shutil import copyfile

from .h_colors import *
from .h_utils  import *

import logging

# Generer le fichier de configuration des pipelines
from pipeline_maker.pipeline_config import PipelineConfig

import yaml, json
import copy
import sys, os
import os.path
import errno

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

    run(cli_args)

def run(cli_args):

    # Set the log level
    log = logging.getLogger(__name__)
    log.handlers = []
    ch = logging.StreamHandler()
    log.addHandler(ch)
    if cli_args["--debug"]:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    # 0. do we have a pipeline manifest?
    if not os.path.isfile(cli_args["--ifile"]):
        print(tag.warn, "Pipeline Manifest not found. %s" % cli_args["--ifile"])
        # 0N. Are we in interactive mode?
        if not cli_args["--it"]: exit(1)

        # interactive command function
        print(tag.question, """Do ou wanna create Pipeline Manifest?
        Yes) I would love you do that for me
        No) But i can tell you where to find it
        """)

    # 1. Apply scripts according to arguments
    ## --ofile argument
    if not os.path.exists(cli_args["--ofile"]):
        print("Creating output directory %s" % str(cli_args["--ofile"]))
        print("")
        os.makedirs(cli_args["--ofile"])

    ## -p arguments
    if cli_args["-p"]:
        print(fg.orange, "Processing <text_to_search:replacement_text>", ft.reset)
        preprocessing(cli_args["--ifile"],cli_args["-p"])
        print(fg.blue,"Your original pipeline manifest has been saved as: " + cli_args["--ifile"] + ".bak",ft.reset)
    else:
        print(tag.info, "Locally use " + fg.green + "cpm -p <text_to_search:replacement_text>" + ft.reset + " to correct the paths in the pipelinemanifest.json")

    ################################################################################################
    #### II. Script Start
    ################################################################################################

    # I Parsing the pipeline manifest
    print("Processing %s" % str(cli_args["--ifile"]))

    env = "prod" if cli_args["--prod"] else "nonprod"
    with open(cli_args["--ifile"]) as f:
        pipelinemanifest = json.load(f)[env]
        
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
        print(tag.info, "Space config found", ft.reset)
        space_config.read_pipeline_config(pipelinemanifest["configs"])
        log.debug(space_config.p_config)

    template_configs = {}
    if "templates" in pipelinemanifest:
        print(tag.info, "%s Templates found" % len(pipelinemanifest["templates"]))
        print(", ".join(pipelinemanifest["templates"].keys()))
        for tpl in pipelinemanifest["templates"]:
            template_configs[tpl] = PipelineConfig(space_config, pipelinemanifest["templates"][tpl])

    # II.2. Read the configuration for each pipeline
    print(tag.info, "%s Pipelines found" % len(pipelinemanifest["pipelines"]))
    for p in pipelinemanifest["pipelines"]:
        
        # II.2.1 Create pipeline config
        if "template" in p or "-tpl" in p:
            # II.2.2a Templates -> start by applying the right template
            log.debug("template:" + pipeline_config.get("template"))
            pipeline_config = PipelineConfig(template_configs[pipeline_config.get("template")], p)
        else:
            # II.2.2b Space config -> start by applying the space config
            pipeline_config = PipelineConfig(space_config, p)

        log.debug(pipeline_config.get("name"))
        log.debug(pipeline_config.p_config)
        if cli_args["<pipeline_name>"] and pipeline_config.get("name") not in cli_args["<pipeline_name>"]:
            continue

        ## III.2.3 Partials -> merge all the partials into one file
        if pipeline_config.get("partials"):
            log.debug("partials:" + pipeline_config.get("partials"))
            pipeline_config.process_partials()

        ## II.2.4 Merging -> modify the pipeline config
        if pipeline_config.get("merge"):
            log.debug("merge:" + pipeline_config.get("merge"))
            try:
                pipeline_config.process_to_be_merged(out_directory=cli_args["--ofile"])
            except IOError as e:
                print(fg.red, "Error: File does not appear to exist.", ft.reset)
                print(e)
                print(tag.info, "Locally use " + fg.green + "cpm -p <text_to_search:replacement_text>" + ft.reset + " to correct the paths in the pipelinemanifest.json")
                continue

        ## II.2.5 Copy (optional) -> copy les fichiers dans le dossier output
        if cli_args["--copy"]:
            log.debug("** copy files")
            outputfile = cli_args["--ofile"] + "/config_files/" + pipeline_config.get("name") + ".yml"

            # config_file
            if not os.path.exists(cli_args["--ofile"] + "/config_files/"):
                os.mkdir(cli_args["--ofile"] + "/config_files/")
                
            copyfile(pipeline_config.get("config_file"), outputfile)
            pipeline_config.set("config_file", outputfile)
            # vars_files
            vars_files = []
            for f in pipeline_config.get("vars_files"):
                outputfile =  cli_args["--ofile"] + "/vars_files/" + os.path.basename(f)

                if not os.path.exists(cli_args["--ofile"] + "/vars_files/"):
                    os.mkdir(cli_args["--ofile"] + "/vars_files/")
                
                copyfile(f, outputfile)
                vars_files.append(outputfile)
            pipeline_config.set("vars_files", vars_files)
   
        ## II.2.6 Cli (optionnal) -> generate the cli
        if cli_args["--cli"]:
            log.debug("** gen cli")
            pipeline_config.process_cli()

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

    #4. Generate the pipelines_file
    # Ecrire le ficher des pipelines
    with open(cli_args["--ofile"]+'/pipelinemanifest.yml', 'w') as outfile:
        yaml.safe_dump(pipelines_file, outfile, default_flow_style=False)

    ################################################################################################
    #### Post-processing
    ################################################################################################

    # Revert the preprocessing
    if cli_args["-p"]:
        preprocessing(cli_args["--ifile"],cli_args["-p"], reverte=True)
        print(fg.blue + "Your original pipeline manifest has been restored: " + cli_args["--ifile"] + ft.reset)
        print("The original output has been saved: " + cli_args["--ifile"] + ".back")

        print(fg.orange + "Post-Processing <text_to_search:replacement_text>" + ft.reset)
        preprocessing(cli_args["--ofile"]+'/pipelinemanifest.yml',cli_args["-p"], reverte=True)
        print(fg.blue + "Your output has been post-processed: " + cli_args["--ofile"] +'/pipelinemanifest.yml' + ft.reset)
        print("The original output has been saved: " + cli_args["--ofile"] +'/pipelinemanifest.yml' + ".back")

    # Post processing pour les pipelines
    if cli_args["--static"]:
        s_outputfile = cli_args["--ofile"] + '/pipelinemanifest-infra-static.yml'
        p = ["./:" + cli_args["--static"]]
        copyfile(cli_args["--ofile"] + '/pipelinemanifest.yml', s_outputfile)
        preprocessing(s_outputfile, p, backup=False)