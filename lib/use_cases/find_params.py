import re


def find_params(file):

    pattern = re.compile("\(\((.*?)\)\)")

    params = set()
            
    with open(file) as file_in:
        for line in file_in:
            params.update(re.findall(pattern,line))

    return params
