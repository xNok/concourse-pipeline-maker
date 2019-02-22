import os, shutil, errno, copy
import yaml
import warnings
from collections import defaultdict

## Dependences
from .pipeline_merger import merge_pipeline

import logging

class PipelineConfig(object):
    """Manage the configuration of a pipeline, deal with the read/write operation"""

    p_config = {
        # Basic configuration
        "team": "",
        "name": "",
        "config_file": "",
        "vars_files": [],
        "vars": [],
    }

    p_tools = {
        # Advanced Configuration
        "template": "",
        "merge": [],
        "partials": [],
        "cli": ""
    }

    def __init__(self, default_config=None, data=None):
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.StreamHandler())

        if default_config:
            self.p_config = copy.deepcopy(default_config)
        
        if data:
            self.p_config = self.read_pipeline_config(data)

    ## Main processing function
    def read_pipeline_config(self, data):
        """
        Create the PipelineCongig Object for the space.
        Valid entries: -t,-p,-c,-l,-v
        Valid function: -tpl, -m, -s
        """

        self.logger.info("Reading the config")
        self.logger.debug(data)
        ## Fly cli args
        # Single arguements allowed
        self.p_config["team"]         = self.get_parameter(data, "-t", "team")
        self.p_config["name"]         = self.get_parameter(data, "-p", "pipeline")
        self.p_config["config_file"]  = self.get_parameter(data, "-c", "config")
        # Multiple arguments allowed
        self.p_config["vars_files"]   += self.get_list_of_paramters(data, "-l", "load-vars-from")
        self.p_config["vars"]         += self.get_list_of_paramters(data, "-v", "var")

        ##  Advanced args
        self.p_tools["template"] = self.get_parameter(data, "-tpl", "template")
        self.p_tools["merge"]    += self.get_list_of_paramters(data, "-m", "merge")
        self.p_tools["partials"] += self.get_list_of_paramters(data, "-s", "partials")

        return self.p_config
    
    ## Utils processing / transformations
    def process_to_be_merged(self, out_directory="./"):
        """Loop over the merge array and merge together file in order"""
        self.logger.info("Merging option")
        basepipeline = os.path.basename(self.p_config["config_file"])

        # loop for the merge
        for idx, m in enumerate(self.p_tools["merge"]):
            out_config_file = out_directory + '/debug_merged/' + self.p_config["name"] + '-' +  str(idx)  + '-' + basepipeline 
            merge_pipeline(m, self.p_config["config_file"], output=out_config_file)
            self.p_config["config_file"]=out_config_file

        out_merged = out_directory +'/config_files/' + self.p_config["name"] + ".yml"

        if not os.path.exists(out_directory + "/config_files/"):
            os.mkdir(out_directory + "/config_files/")
        shutil.move(out_config_file, out_merged)

        self.p_config["config_file"] = out_merged

        return out_merged

    def process_vars(self, out_directory="./"):

        self.logger.info("Var option unabled - Creating a var file")

        vars_ = dict([v.split('=') for v in self.p_config["vars"]])
        vars_path  = out_directory + '/vars_files/' + self.p_config["name"] +'.yml'

        self.logger.debug(yaml.safe_dump(vars_, default_flow_style=False))

        if not os.path.exists(os.path.dirname(vars_path)):
            try:
                os.makedirs(os.path.dirname(vars_path))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        
        with open(vars_path, 'w') as outfile:
            yaml.safe_dump(vars_, outfile, default_flow_style=False)
        
        self.p_config["vars_files"] += [vars_path]

    def process_partials(self):

        for p in self.p_tools["partials"][1:]:
            self.p_tools["merge"].append(self.p_config["config_file"] + p + ".yml")

        self.p_config["config_file"] = self.p_config["config_file"] + self.p_tools["partials"][0] + ".yml"

    def process_cli(self):
        """provide the fly cli for a given pipeline"""
        fly = "fly -t " + self.p_config["team"] + " set-pipeline" \
                                + " -p " + self.p_config["name"] \
                                + " -c "  + self.p_config["config_file"] \
                                + " ".join([" -l "  + l for l in self.p_config["vars_files"]]) \
                                + " ".join([" --var " + var for var in self.p_config["vars"]])

        self.p_config["cli"] = fly

        return fly

    ## Utils extract params
    def get(self, key):
        z = {**self.p_config, **self.p_tools}
        return z[key]

    def set(self, key, value):
        self.p_config[key] = value

    def get_parameter(self, data, flag, name):
        """
        Extract a string by flag or name or return default
        """
        if flag in data:
            r = data[flag]
        elif  name in data:
            r = data[name]
        else:
            r = self.get(name)
        
        return r

    def get_list_of_paramters(self, data, flag, name):
        """
        Extract a list by flag or name, concat with defaul value
        """
        if flag in data:
            r = data[flag] if isinstance(data[flag], list) else [data[flag]]
        elif name in data:
            r = data[name] if isinstance(data[name], list) else [data[name]]
        else:
            r = self.get(name)
            
        return r