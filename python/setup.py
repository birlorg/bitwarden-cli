
"""
horrible. seriously.
"""
import os

from setuptools import setup

VERSION = "0.3.0"


def readme():
    """ Load the contents of the README file """
    readme_path = os.path.join(os.path.dirname(__file__), '..', "README.txt")
    with open(readme_path, "r") as f:
        return f.read()


def read_requirements(filename):
    reqs = []
    with open(filename, 'r') as f:
        for line in f:
            reqs.append(line.strip())
    return reqs


setup(
    name="bitwarden",
    version=VERSION,
    author="Birl.org developers",
    author_email="bitwarden@birl.org",
    description="Cross Platform Bitwarden library and CLI with sudolikeaboss.",
    long_description=readme(),
    license="MIT",
    url="https://fossil.birl.ca/bitwarden-cli/doc/trunk/README.txt",
    classifiers=[],
    install_requires=[
        "click==6.7",
        "cryptography==2.2.2",
        "objectpath==0.5",
        "psutil==5.4.3",
        "pystandardpaths==0.3.2",
        "records==0.5.2",
        "requests==2.18.4",
        "tablib==0.12.1",
    ],
    # install_requires=read_requirements('requirements.txt'),
    tests_require=read_requirements('requirements-tests-py3.txt'),
    packages=[
        'bitwarden'
    ],
    entry_points={
        'console_scripts': ['bitwarden=bitwarden.main:cli', 'bitwarden-agent=bitwarden.agent:main'],

    },

)
