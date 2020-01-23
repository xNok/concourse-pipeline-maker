import os, shutil, tempfile, fileinput
import re
from datetime import datetime

def use_partials(pipeline, out_directory="./"):

    for p in reversed(pipeline.p_tools["partials"][1:]):
        if isinstance(p, dict):
            # partials:
            # - { config_file: "config_file", with: {}}
            config_to_merge = pipeline.p_config["config_file"] + p["config_file"] + ".yml"
            config_to_merge = replace_config_with(config_to_merge, p["with"])
        else:
            # partials:
            # - "config_file"
            config_to_merge = pipeline.p_config["config_file"] + p + ".yml"
        pipeline.p_tools["merge"].insert(0, config_to_merge)

    #  Manage the with case
    if isinstance(pipeline.p_tools["partials"][0], dict):
        pipeline.p_config["config_file"] = pipeline.p_config["config_file"] + pipeline.p_tools["partials"][0]["config_file"] + ".yml"
        pipeline.p_config["config_file"] = replace_config_with(pipeline.p_config["config_file"], pipeline.p_tools["partials"][0]["with"])
    else:
        pipeline.p_config["config_file"] = pipeline.p_config["config_file"] + pipeline.p_tools["partials"][0] + ".yml"

    return pipeline.p_config["config_file"], pipeline.p_tools["merge"]


# merge operation ca require temporary copy not to change the original file
def create_temporary_copy(path):
    """Create a temporary copy of a file"""
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, str(datetime.timestamp(datetime.now())) + "-" + os.path.basename(path))
    shutil.copy2(path, temp_path)

    return temp_path

# do inplace replace in a configfile
def replace_config_with(config_file, to_replace={}):
    """ Replace ((var)) by the valye provided in the dic to_replace"""
    config_file = create_temporary_copy(config_file)

    with fileinput.FileInput(config_file, inplace=True) as file:
        to_replace = dict((re.escape("((" + k + "))"), v) for k, v in to_replace.items())
        pattern = re.compile("|".join(to_replace.keys()))
        for line in file:
            print(pattern.sub(lambda m: to_replace[re.escape(m.group(0))], line))

    return config_file
