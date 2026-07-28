import glob, importlib.util, os

REQUIRED_META = {"id", "name", "kind", "params"}
VALID_KINDS = {"signal", "portfolio", "screen", "benchmark", "cashflow"}

def load_strategy(path):
    spec = importlib.util.spec_from_file_location(
        f"isa_strategy_{os.path.splitext(os.path.basename(path))[0]}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    meta = getattr(mod, "META", None)
    if not isinstance(meta, dict) or not REQUIRED_META <= set(meta):
        raise ValueError(f"{path}: META must be a dict with keys {sorted(REQUIRED_META)}")
    if meta["kind"] not in VALID_KINDS:
        raise ValueError(f"{path}: invalid kind {meta['kind']!r}")
    if not callable(getattr(mod, "generate", None)):
        raise ValueError(f"{path}: missing callable generate()")
    return mod

def discover_strategies(folder="strategies"):
    mods = []
    for p in sorted(glob.glob(os.path.join(folder, "*.py"))):
        if os.path.basename(p).startswith("__"):
            continue
        mods.append(load_strategy(p))
    return sorted(mods, key=lambda m: m.META["id"])
