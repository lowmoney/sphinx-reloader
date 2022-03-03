# Sphinx Reloader
When building documentation for [Sphinx](https://www.sphinx-doc.org/en/master/), I got sick of running the build command, needing to delete the build folder when changes would not show, etc. So, I made this tool to do it for me.


## Features
Sphinx Reloader creates a realoder that watches the source directory where your Sphinx documentation lives, and when changes occure, will create a new build of the updated files. Sphinx Reloader will also create a simple HTTP server to serve the documentation.

Sphinx Reloader also has a live reload feature built into the web server where it will reload the webpage when a change has been detected.

## Install
clone the repo and run `pip install .`

Make sure you have [Sphinx](https://www.sphinx-doc.org/en/master/) and [Watchdog](https://pypi.org/project/watchdog/) installed