import pytest

from lib.use_cases.use_merge import merge_pipeline

def test_list_override():

    b = {
        "ressources": [
            {"name": "my-ressource", "type": "git", "source": {'branch': 'master', 'uri': 'https://github.com/pivotalservices/concourse-pipeline-samples.git'}}
        ]
    }

    n = {
        "ressources": [
            {"name": "my-ressource", "type": "git", "source": {'branch': 'dev'}}
        ]
    }

    v = {
        "ressources": [
            {"name": "my-ressource", "type": "git", "source": {'branch': 'dev', 'uri': 'https://github.com/pivotalservices/concourse-pipeline-samples.git'}}
        ]
    }

    merge_pipeline(b,n)
    
    assert b == v