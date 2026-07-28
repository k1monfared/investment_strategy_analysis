import isa

def test_package_has_version():
    assert isinstance(isa.__version__, str)
    assert isa.__version__
