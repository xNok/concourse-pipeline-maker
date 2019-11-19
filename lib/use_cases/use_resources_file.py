import yaml
import logging

from .merge_pipelines_together import merge_pipeline

def use_resources_file(pipeline, out_directory="./"):

    def find_resource(resource_list, line):
        """ Are any of these resources in the line?"""
        for word in resource_list:
            if "get: " + word in line or "put: " + word in line:
                return word

        return False

    # Merge all resource files together
    files = pipeline.get("resources_file")

    with open(files[0]) as f:
        resources_file = yaml.safe_load(f)
    
    for f in files[1:]:
        with open(f) as fp:
            m_addon = yaml.safe_load(fp)

        resources_file = merge_pipeline(resources_file,m_addon)
    
    # Analyse resource we have in resource file
    resources = sorted(
        set([r["name"] for r in resources_file["resources"]]),
        key=len,
        reverse=True
    )

    # Which resources do we need ?
    with open(pipeline.get("config_file")) as f:


        result = [i for i in
            (
                find_resource(resources, line.lower()) for line in f.readlines()
            )
             if i]

    # keep only what we need
    resources_file["resources"]      = [r for r in resources_file["resources"] if r["name"] in result]
    resources_type                   = set([r["type"] for r in resources_file["resources"]])
    if "resource_types" in resources_file:
        resources_file["resource_types"] = [r for r in resources_file["resource_types"] if r["name"] in resources_type ]

    logging.debug("resources: " + str(resources))
    logging.debug("resource_types: " + str(resources_type))

    with open(pipeline.p_config["config_file"]) as fp:
        config_file = yaml.safe_load(fp)

    config_file = merge_pipeline(config_file, resources_file)

    pipeline.print_config_file(config_file, out_directory=out_directory)

    return pipeline.p_config["config_file"]
