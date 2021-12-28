# -*- coding: utf-8 -*-
"""Setup for the package."""

# Standard Library
import os
import re

# 3rd-party
from setuptools import find_packages
from setuptools import setup


def get_version(package):
    """Return package version as listed in `__version__` in `init.py`."""
    init_py = open(os.path.join(package, "__init__.py")).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


def read(fname):
    """Read text file content and return it."""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


# TODO - This is super over egging it. Slim down.
def requirements_as_list():
    with open("requirements.txt") as f:
        required = f.read().splitlines()
        print(required)
    return required


version = get_version("motor_controller")

setup(
    name="motor-controller",
    version=version,
    description="A utility for controlling stepper motors with Django and RaspberryPi.",
    long_description="read('README.md')",
    classifiers=[
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    author="Jake Saunders",
    author_email="jakelsaunders94@gmail.com",
    url="https://github.com/JakeLSaunders94/django-migration-dbindex-check",
    license="MIT",
    packages=find_packages(exclude=["tests"]),
    install_requires=requirements_as_list(),
    setup_requires=[],
    tests_require=["pytest"],
)
