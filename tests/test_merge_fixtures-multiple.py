import pytest

from lib.use_cases.use_merge import merge_pipeline

#jobs: #list
#  - name: gating-rc
#    plan: #list
#    - name: patate
#      in_parallel:
#      steps:
#        - get: webhook-trigger-rc
#          (-) trigger: true
#          (+) trigger: false
def test_list_override_multi_keys():
    b = {  
        "jobs":[  
            {  
                "name":"gating-rc",
                "plan":[  
                    {
                    "name": "patate",
                    "in_parallel":{
                        "steps":[  
                            {  
                                "get":"webhook-trigger-rc",
                                "trigger":True
                            }
                        ]
                    }
                    }
                ]
            }
        ]
    }

    n = {  
        "jobs":[  
            {  
                "name":"gating-rc",
                "plan":[  
                    {
                    "name": "patate",  
                    "in_parallel":{
                        "steps":[  
                            {  
                                "get":"webhook-trigger-rc",
                                "trigger":False
                            }
                        ]
                    }
                    }
                ]
            }
        ]
    }
      

    v = {"jobs":[{"name":"gating-rc","plan":[{"name":"patate","in_parallel":{"steps":[{"get":"webhook-trigger-rc","trigger":False}]}}]}]}

    merge_pipeline(b,n)
    
    assert b == v