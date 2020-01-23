# -*- coding: utf-8 -*-
import yaml
import os, shutil, errno

import logging
from deepmerge import Merger


## Utils processing / transformations
def use_merge(pipeline, out_directory="./"):
    """
        GIVEN a pipeline_config
        Loop over the merge array and merge together file in order
        Return the new config_file path
    """

    logging.info("process_to_be_merged")

    # base pipeline configuration
    with open(pipeline.p_config["config_file"]) as fp:
        m_base = yaml.safe_load(fp)

    # loop for the merge
    for  m in pipeline.p_tools["merge"]:
        logging.info("merging: " + str(m))
        with open(m) as fp:
            m_addon = yaml.safe_load(fp)

        m_base = merge_pipeline(m_base, m_addon)

    pipeline.print_config_file(m_base, out_directory=out_directory)

    return pipeline.p_config["config_file"]

## Merging mechanism
def merge_pipeline(b, n):
    """
    Merge Two pipeline files base on the above merge function
    """

    # Merge
    my_merger = Merger(
    # pass in a list of tuples,with the
    # strategies you are looking to apply
    # to each type.
    [
        (list, [merge_list]),
        (dict, ["merge"])
    ],
    # next, choose the fallback strategies,
    # applied to all other types:
    ["override"],
    # finally, choose the strategies in
    # the case where the types conflict:
    ["override"]
    )

    my_merger.merge(b,n)

    return b

# We find a note to keep merging base ont sone known keys
def find_node(item, nodes, seq_key= ["name", "get", "put", "task"], deeper_key=["aggregate","in_parallel"]):
    """ Return first item in sequence where f(item) == True. """
    for s in nodes: # Foreach element of the destination
        for sq in seq_key: # Foreach possible key
            if (sq in s) and (sq in item):
                if s[sq] == item[sq]:
                    return s

def merge_list(merger, path, base, nxt):
    """ Handler for mergeing list together in concourse context"""
    # can we merge further in the base?
    logging.debug(path)
    for item in nxt:
        
        node = find_node(item, base)

        if node:
            node = merger.merge(node,item)
        else:
            base += [item]

    return base
