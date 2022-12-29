"""Import top APIs and version."""
from importlib.metadata import PackageNotFoundError, version

# https://github.com/pypa/setuptools_scm/#retrieving-package-version-at-runtime
try:
    __version__ = version("spinspg")
except PackageNotFoundError:
    # package is not installed
    pass
