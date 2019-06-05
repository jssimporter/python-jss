import pytest
from jss import Policy, JSS, Package, PostError
from xml.etree import ElementTree


@pytest.fixture
def policy(j):  # type: (JSS) -> Policy
    p = Policy(j, "Fixture Policy")
    try:
        p.save()
    except PostError:  # Already existed from previous test run
        p = j.Policy("Fixture Policy")

    yield p

    p.delete()


@pytest.fixture
def package(j):  # type: (JSS) -> Package
    pkg = Package(j, "Fixture Package")
    try:
        pkg.save()
    except PostError:  # Already existed from previous test run
        pkg = j.Package("Fixture Package")

    yield pkg

    pkg.delete()

