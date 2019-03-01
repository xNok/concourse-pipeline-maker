import yaml
import os, shutil, errno

import logging
from deepmerge import Merger

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
def find_node(item, nodes, seq_key= ["name", "get", "put", "task", "aggregate", "do"]):
    """Return first item in sequence where f(item) == True."""
    for s in nodes: # Foreach element of the destination
        for sq in seq_key: # Foreach possible key
            if (sq in s) and (sq in item):
                if s[sq] == item[sq]:
                    return s

def merge_list(merger, path, base, nxt):
    # can we merge further in the base?
    logging.debug(path)
    for item in nxt:
        
        node = find_node(item, base)

        if node:
            node = merger.merge(node,item)
        else:
            base += [item]

    return base
