import sys
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as readme:
    long_description = readme.read()

if sys.version_info < (3, 6):
    print('ERROR: sphinx-reloader requires at least Python 3.6 to run.')
    sys.exit(1)

install_requires = [
    
]

setup(
    name = "sphinx-reloader",
    version= "0.0.1",
    author="Ruckshan Hendry Ratnam",
    author_email="hendryratnam@gmail.com",
    description="A reloader and HTTP server for Sphinx",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            "sphinx-reloader = src.sphinx_reloader:main",
        ],
    },
)