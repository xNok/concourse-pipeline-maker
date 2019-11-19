def use_partials(pipeline, out_directory="./"):

    for p in reversed(pipeline.p_tools["partials"][1:]):
        if isinstance(p, dict):
            # partials:
            # - { config_file: "config_file", with: {}}
            config_to_merge = pipeline.p_config["config_file"] + p["config_file"] + ".yml"
            config_to_merge = pipeline.replace_config_with(config_to_merge, p["with"])
        else:
            # partials:
            # - "config_file"
            config_to_merge = pipeline.p_config["config_file"] + p + ".yml"
        pipeline.p_tools["merge"].insert(0, config_to_merge)

    #  Manage the with case
    if isinstance(pipeline.p_tools["partials"][0], dict):
        pipeline.p_config["config_file"] = pipeline.p_config["config_file"] + pipeline.p_tools["partials"][0]["config_file"] + ".yml"
        pipeline.p_config["config_file"] = pipeline.replace_config_with(pipeline.p_config["config_file"], pipeline.p_tools["partials"][0]["with"])
    else:
        pipeline.p_config["config_file"] = pipeline.p_config["config_file"] + pipeline.p_tools["partials"][0] + ".yml"

    return pipeline.p_config["config_file"], pipeline.p_tools["merge"]
