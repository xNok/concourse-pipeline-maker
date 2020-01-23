# -*- coding: utf-8 -*-
import os, copy
import yaml

## Dependences
from ..use_cases.use_merge                import use_merge
from ..use_cases.use_resources_file       import use_resources_file
from ..use_cases.use_partials             import use_partials

import logging

class PipelineConfig(object):
    """Manage the configuration of a pipeline, deal with the read/write operation"""

    def __init__(self, data=None, templates={}, default=None):
        """ Create the data structure from congiguration
            default -> let you give a default config
            templates -> let you initialise form template
            data -> read the configuration
        """
        # Create default config
        if default:
            self.p_config = copy.deepcopy(default.p_config)
            self.p_tools = copy.deepcopy(default.p_tools)
        else:
            self.p_config = {
                # Basic configuration
                "team": "",
                "name": "",
                "config_file": "",
                "vars_files": [],
                "vars": {},
            }

            self.p_tools = {
                # Advanced Configuration
                "template": "",
                "merge": [],
                "partials": [],
                "resources_file": [],
                "cli": ""
            }
        
        # Create pipeline from data
        if data:
            # do we have template?
            if "template" in data or "-tpl" in data:
                # Templates -> start by applying the right template
                template_name = data["-tpl"] if "-tpl" in data else data["template"]
                logging.debug("template:" + template_name)
                # do we need to apply template
                if template_name in templates:
                    self.p_config = copy.deepcopy(templates[template_name].p_config)
                    self.p_tools = copy.deepcopy(templates[template_name].p_tools)
            # read all the data
            self.p_config = self.read_pipeline_config(data)

    ## Main processing function
    def make_pipeline(self, out_directory="./"):
        """Execute all the script to create the final pipeline"""

        ## Partials -> merge all the partials into one file
        if self.get("partials"):
            logging.debug("partials: " + str(self.get("partials")))
            use_partials(self)

        ## Merging -> modify the pipeline config
        if self.get("merge"):
            logging.debug("merge: " + str(self.get("merge")))
            use_merge(self, out_directory=out_directory)

        ## Resources -> Merge the new ressources if needed
        if self.get("resources_file"):
            logging.debug("resources: " + str(self.get("resources_file")))
            use_resources_file(self, out_directory=out_directory)

    def read_pipeline_config(self, data):
        """
        Create the PipelineCongig Object for the space.
        Valid entries: -t,-p,-c,-l,-v
        Valid function: -tpl, -m, -s
        """

        logging.info("Reading the config")
        ## Fly cli args
        # Single arguements allowed
        self.p_config["team"]         = self.get_parameter(data, "-t", "team")
        self.p_config["name"]         = self.get_parameter(data, "-p", "pipeline", "name")
        self.p_config["config_file"]  = self.get_parameter(data, "-c", "config", "config_file")
        # Multiple arguments allowed
        self.p_config["vars_files"]   = self.get_list_of_paramters(data, "-l", "load-vars-from", "vars_files")

        # Get user vars
        self.p_config["vars"]         = self.get_list_of_paramters(data, "-v", "var", "vars")

        ##  Advanced args
        self.p_tools["template"]      = self.get_parameter(data, "-tpl", "template")
        self.p_tools["merge"]         = self.get_list_of_paramters(data, "-m", "merge")
        self.p_tools["partials"]      = self.get_list_of_paramters(data, "-s", "partials")
        self.p_tools["resources_file"] = self.get_list_of_paramters(data, "-r", "resources_file")

        return self.p_config
    
    
    def print_config_file(self, source, out_directory="./"):
        out_path = out_directory +'/config_files/' + self.p_config["name"] + ".yml"

        if not os.path.exists(out_directory + "/config_files/"):
            os.mkdir(out_directory + "/config_files/")
        
        with open(out_path, 'w+') as fp:
            yaml.dump(source, fp, default_flow_style=False)

        self.p_config["config_file"] = out_path

        return out_path

    # change the config object
    def set(self, key, value):
        self.p_config[key] = value

    ## Utils extract params
    def get(self, key):
        z = {**self.p_config, **self.p_tools}
        return z[key]

    def get_parameter(self, data, flag, name, alias=None):
        """
        Extract a string by flag or name or return default
        """

        if alias is None: alias = name

        if flag in data:
            r = data[flag]
        elif name in data:
            r = data[name]
        elif alias in data:
            r = data[alias]
        else:
            r = self.get(alias)
        
        return r

    def get_list_of_paramters(self, data, flag, name, alias=None):
        """
        Extract a list by flag or name, concat with defaul value
        """
        if alias is None: alias = name
        r = self.get(alias)

        if flag in data:
            _r = data[flag] if not isinstance(data[flag], str) else [data[flag]]
        elif name in data:
            _r = data[name] if not isinstance(data[name], str) else [data[name]]
        elif alias in data:
            _r = data[alias] if not isinstance(data[alias], str) else [data[alias]]
        else:
            _r = None

        if _r is not None:
            if isinstance(r, dict):
                r = {**r, **_r}
            else:
                r = r + _r
            
        return r