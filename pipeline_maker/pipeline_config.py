import os, shutil, errno, copy
import yaml
import logging
import tempfile
import fileinput
from datetime import datetime
import re

## Dependences
from .pipeline_merger import merge_pipeline

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
            logging.debug("partials:" + str(self.get("partials")))
            self.process_partials()

        ## Merging -> modify the pipeline config
        if self.get("merge"):
            logging.debug("merge:" + str(self.get("merge")))
            self.process_to_be_merged(out_directory=out_directory)

        ## Resources -> Merge the new ressources if needed
        if self.get("resources_file"):
            logging.debug("resources:" + str(self.get("resources_file")))
            self.process_resources(out_directory=out_directory)

    def read_pipeline_config(self, data):
        """
        Create the PipelineCongig Object for the space.
        Valid entries: -t,-p,-c,-l,-v
        Valid function: -tpl, -m, -s
        """

        logging.info("Reading the config")
        logging.debug(data)
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
    
    ## Utils processing / transformations
    def process_to_be_merged(self, out_directory="./"):
        """Loop over the merge array and merge together file in order"""
        logging.info("Merging option")

        # base pipeline configuration
        with open(self.p_config["config_file"]) as fp:
            m_source = yaml.safe_load(fp)

        # loop for the merge
        for  m in self.p_tools["merge"]:
            logging.info("merging: " + str(m))
            with open(m) as fp:
                m_destination = yaml.safe_load(fp)
 
            m_source = merge_pipeline(m_source, m_destination)

        self.print_config_file(m_source, out_directory=out_directory)

        return self.p_config["config_file"]

        # define output path
    def print_config_file(self, source, out_directory="./"):
        out_path = out_directory +'/config_files/' + self.p_config["name"] + ".yml"

        if not os.path.exists(out_directory + "/config_files/"):
            os.mkdir(out_directory + "/config_files/")
        
        with open(out_path, 'w+') as fp:
            yaml.dump(source, fp, default_flow_style=False)

        self.p_config["config_file"] = out_path

        return out_path

    def process_partials(self, out_directory="./"):

        for p in reversed(self.p_tools["partials"][1:]):
            if isinstance(p, dict):
                # partials:
                # - { config_file: "config_file", with: {}}
                config_to_merge = self.p_config["config_file"] + p["config_file"] + ".yml"
                config_to_merge = self.replace_config_with(config_to_merge, p["with"])
            else:
                # partials:
                # - "config_file"
                config_to_merge = self.p_config["config_file"] + p + ".yml"
            self.p_tools["merge"].insert(0, config_to_merge)

        if isinstance(self.p_tools["partials"][0], dict):
            self.p_config["config_file"] = self.p_config["config_file"] + self.p_tools["partials"][0]["config_file"] + ".yml"
            self.p_config["config_file"] = self.replace_config_with(self.p_config["config_file"], self.p_tools["partials"][0]["with"])
        else:
            self.p_config["config_file"] = self.p_config["config_file"] + self.p_tools["partials"][0] + ".yml"

        return self.p_config["config_file"], self.p_tools["merge"]

    def process_resources(self, out_directory="./"):

        for files in self.get("resources_file"):

            with open(files) as f:
                resources_file = yaml.safe_load(f)
                resources = set([r["name"] for r in resources_file["resources"]])

            # Which resources do we need ?
            with open(self.get("config_file")) as f:
                result = [self.find_resource(resources, line.lower()) for line in f.readlines() if self.find_resource(resources, line.lower())]

            # keep only what we need
            resources_file["resources"]      = [r for r in resources_file["resources"] if r["name"] in result]
            resources_type = set([r["type"] for r in resources_file["resources"]])
            resources_file["resource_types"] = [r for r in resources_file["resource_types"] if r["name"] in resources_type ]

            logging.debug("resources:" + str(resources_file["resources"]))
            logging.debug("resource_types:" + str(resources_file["resource_types"]))

            with open(self.p_config["config_file"]) as fp:
                m_source = yaml.safe_load(fp)

            m_source = merge_pipeline(m_source,resources_file)

            self.print_config_file(m_source, out_directory=out_directory)

            return self.p_config["config_file"]

    def process_cli(self, out_directory="./", ext="cmd"):
        """provide the fly cli for a given pipeline"""

        # Create fly command line
        fly = "fly -t " + self.p_config["team"] + " set-pipeline" \
                                + " -p " + self.p_config["name"] \
                                + " -c "  + self.p_config["config_file"] \
                                + " ".join([" -l "  + l for l in self.p_config["vars_files"]]) \
                                + " ".join([" --var " + k + "=" + str(v) for k,v in self.flatten(self.p_config["vars"]).items()])

        self.p_tools["cli"] = fly

        # Create output dir
        out_directory = out_directory + '/fly_cli/'
        if not os.path.exists(out_directory):
            os.mkdir(out_directory)

        if ext in ["sh", ".sh"]:
            # Write output
            with open(out_directory + self.p_config["name"] + ".sh", 'w+') as outfile:
                outfile.write("cd `dirname $0`")
                outfile.write('\n')
                outfile.write('cd ..')
                outfile.write('\n')
                outfile.write(fly)
                outfile.write('\n')
                outfile.write("read -p 'Press [Enter] key to continue...'")
        else:
            # Write output
            with open(out_directory + self.p_config["name"] + ".cmd", 'w+') as outfile:
                outfile.write("cd /d %~dp0")
                outfile.write('\n')
                outfile.write('cd ..')
                outfile.write('\n')
                outfile.write(fly)
                outfile.write('\n')
                outfile.write("pause")

        return fly

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
        elif  name in data:
            r = data[name]
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
        else:
            _r = None

        if _r is not None:
            if isinstance(r, dict):
                r = {**r, **_r}
            else:
                r = r + _r
            
        return r

    def find_resource(self, resource_list, line):
        """ Are any of these resources in the line?"""
        for word in resource_list:
            if "get: " + word in line or "put: " + word in line:
                return word

    # flatten is used for vars. We need to flatten then to create a valide cli
    def flatten(self, d, parent_key='', sep='.'):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            try:
                items.extend(self.flatten(v, new_key, sep=sep).items())
            except:
                items.append((new_key, v))
        return dict(items)

    # merge operation ca require temporary copy not to change the original file
    def create_temporary_copy(self, path):
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, str(datetime.timestamp(datetime.now())) + "-" + os.path.basename(path))
        shutil.copy2(path, temp_path)
        return temp_path

    # do inplace replace in a configfile
    def replace_config_with(self, config_file, to_replace={}):

        config_file = self.create_temporary_copy(config_file)
        with fileinput.FileInput(config_file, inplace=True) as file:
            to_replace = dict((re.escape("((" + k + "))"), v) for k, v in to_replace.items())
            pattern = re.compile("|".join(to_replace.keys()))
            for line in file:
                print(pattern.sub(lambda m: to_replace[re.escape(m.group(0))], line))

        return config_file