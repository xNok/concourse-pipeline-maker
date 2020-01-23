import os

# flatten is used for vars. We need to flatten then to create a valide cli
def flatten(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        try:
            items.extend(flatten(v, new_key, sep=sep).items())
        except:
            items.append((new_key, v))
    return dict(items)

def generate_cli(pipeline, out_directory="./", ext="cmd"):
    """provide the fly cli for a given pipeline"""

    # Create fly command line
    fly = "fly -t " + pipeline.p_config["team"] + " set-pipeline" \
                            + " -p " + pipeline.p_config["name"] \
                            + " -c "  + pipeline.p_config["config_file"] \
                            + " ".join([" -l "  + l for l in pipeline.p_config["vars_files"]]) \
                            + " ".join([" --var " + k + "=" + str(v) for k,v in flatten(pipeline.p_config["vars"]).items()])

    pipeline.p_tools["cli"] = fly

    # Create output dir
    out_directory = './set-pipelines/'
    if not os.path.exists(out_directory):
        os.mkdir(out_directory)

    if ext in ["sh", ".sh"]:
        # Write output
        with open(out_directory + pipeline.p_config["name"] + ".sh", 'w+') as outfile:
            outfile.write(fly)
            outfile.write('\n')
            outfile.write("read -p 'Press [Enter] key to continue...'")
    else:
        # Write output
        with open(out_directory + pipeline.p_config["name"] + ".cmd", 'w+') as outfile:
            outfile.write(fly)
            outfile.write('\n')
            outfile.write("pause")

    return fly