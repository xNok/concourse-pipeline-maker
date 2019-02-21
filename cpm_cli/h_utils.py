# coding: utf-8
import fileinput
import sys, os
import fnmatch
import re

def preprocessing(file, args, reverte=False, backup=True):
    """
    Search and replace text in a file to preprocess the pipeline.json or other files
    """
    if backup:
        f = fileinput.FileInput(file, inplace=True, backup=".bak")
    else:
        f = fileinput.FileInput(file, inplace=True)
    
    for line in f:
        for arg in args:
            procs = arg.split(":")
            if reverte:
                text_to_search, replacement_text = procs[1], procs[0]
            else:
                text_to_search, replacement_text = procs[0], procs[1]
            
            line = line.replace(text_to_search, replacement_text)

        sys.stdout.write(line)

    f.close()