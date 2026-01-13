"""Setup shim that mirrors metadata from pyproject.toml (uv style)."""
from __future__ import annotations

from pathlib import Path

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback when packaging w/ older Python
    import tomli as tomllib  # type: ignore

from setuptools import find_packages, setup

HERE = Path(__file__).parent
PYPROJECT = tomllib.loads((HERE / "pyproject.toml").read_text())
PROJECT = PYPROJECT.get("project", {})
DEPENDENCIES = PROJECT.get("dependencies", [])
PYTHON_REQUIRES = PROJECT.get("requires-python", ">=3.11")
README_PATH = HERE / PROJECT.get("readme", "README.md")

setup(
    name=PROJECT.get("name", "poly-web3"),
    version=PROJECT.get("version", "0.0.2"),
    description=PROJECT.get("description", ""),
    long_description=README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else "",
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=("tests", "tests.*", "__pycache__", "*.pyc", "*.pyo")),
    include_package_data=True,
    python_requires=PYTHON_REQUIRES,
    install_requires=DEPENDENCIES,
    license=PROJECT.get("license", "MIT"),
    author=PROJECT.get("authors", [{}])[0].get("name", "PinBar") if PROJECT.get("authors") else "PinBar",
    keywords=PROJECT.get("keywords", []),
    classifiers=PROJECT.get("classifiers", [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
    ]),
    url=PROJECT.get("urls", {}).get("Homepage", "https://github.com/tosmart01/poly-web3"),
    project_urls=PROJECT.get("urls", {}),
)
