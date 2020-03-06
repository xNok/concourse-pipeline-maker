import yaml

def get_templates_from_file(template_file):

    with open(template_file) as f:
        templates = yaml.safe_load(f)

    return templates