import pytest

from pipeline_maker.pipeline_merger import merge_pipeline

def test_list_override_multi_keys():
    b = {"jobs":[{"name":"gating-rc","plan":[{"in_parallel":{"name":"patate","steps":[{"get":"webhook-trigger-rc","trigger":True}]}}]}]}
    n = {"jobs":[{"name":"gating-rc","plan":[{"in_parallel":{"name":"patate","steps":[{"get":"webhook-trigger-rc","trigger":False}]}}]}]}

    v = {"jobs":[{"name":"gating-rc","plan":[{"in_parallel":{"name":"patate","steps":[{"get":"webhook-trigger-rc","trigger":False}]}}]}]}

    merge_pipeline(b,n)
    
    assert b == v