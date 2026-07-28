import yaml

def test_workflow_is_valid_and_has_schedule():
    with open(".github/workflows/scheduled-run.yml") as f:
        wf = yaml.safe_load(f)
    # 'on' may parse as True in YAML; check both
    trigger = wf.get("on", wf.get(True))
    assert "schedule" in trigger
    assert "workflow_dispatch" in trigger
    steps = wf["jobs"]["run"]["steps"]
    runs = " ".join(s.get("run", "") for s in steps)
    assert "isa update" in runs and "isa run" in runs and "isa build" in runs
