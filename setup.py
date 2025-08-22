import os
import zipfile
import requests
import subprocess

# List of modules to install
modules = ["zmq", "ecdsa", "urllib3", "requests", "pycryptodome"]

# Install each module using pip
for module in modules:
    subprocess.run(["pip", "install", module])
