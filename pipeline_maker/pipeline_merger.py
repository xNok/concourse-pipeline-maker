import yaml
import os, shutil, errno

import logging
import deepmerge

## Merging mechanism
### TODO http://y.tsutsumi.io/deepmerge-deep-merge-dictionaries-lists-and-more-in-python.html
### use deepmerge as inspiration for better maintainability
def merge_yaml(source, destination, seq_key= ["name", "get", "put", "task", "aggregate", "do"]):
    """ Return the Union of Two dict
        * If key doesn not exist -> deep copy
        * If the key exist
        *** dict: recursive call
        *** seq: search for a matching object by seq_key else append
    """
    def find_node(item, nodes, seq_key):
        """Return first item in sequence where f(item) == True."""
        for s in nodes: # Foreach element of the destination
            for sq in seq_key: # Foreach possible key
                if (sq in s) and (sq in item):
                    if s[sq] == item[sq]:
                        return s
                    
    for key, value in source.items():
        # Update of existing values
        if key in destination:
            if isinstance(value, dict):
                # logging.debug("!!map " + str(key))
                # get node or create one
                node = destination.setdefault(key, {})
                ## Validate the node
                if not isinstance(node, str):
                    merge_yaml(value, node)
                else:
                    destination[key] = value
            elif isinstance(value, list):
                # logging.debug("!!seq " + str(key))
                # get node or create one
                nodes = destination.setdefault(key, [])
                for item in value:
                    # look for a node in the destination with the same name base on seq_key
                    # ie. search for the values of the keys in seq_key
                    node = find_node(item, nodes, seq_key)
                    if node: # We found a node, then we merge ii
                        merge_yaml(item, node)
                    else:    # We did not found a node
                        destination[key].append(item)
            else:
                # logging.debug("!!str " + str(key) + ": " + str(value))
                destination[key] = value
        # Create New nodes
        else:
            logging.debug("Create new node: " + key)
            destination[key] = value
            
    return destination

def merge_list(merger, path, base, nxt):
    return base


def merge_pipeline(source, dest, output="output.yml"):
    """
    Merge Two pipeline files base on the above merge function
    """

    logging.debug("Merging: " + source + " into " + dest)

    # Open file
    with open(source) as fp:
        d_source = yaml.load(fp)
    with open(dest) as fp:
        d_destination = yaml.load(fp)

    # Merge
    merged = merge_yaml(d_source, d_destination)

    if not os.path.exists(os.path.dirname(output)):
        try:
            os.makedirs(os.path.dirname(output))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    # Write output
    with open(output, 'w+') as outfile:
        yaml.dump(merged, outfile, default_flow_style=False)
