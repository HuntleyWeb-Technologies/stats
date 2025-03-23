#! /bin/python3

import pkg_resources
import subprocess
import sys

def check_for_packages(package_name):
    try:
        pkg_resources.get_distribution(package_name)
        return True
    except pkg_resources.DistributionNotFound:
        return False
    

if __name__ == "__main__":
    required_packages = ["psutil", "rich"]
    for package in required_packages:
        if check_for_packages(package):
            print(f"{package} is installed ✅")
        else:
            print(f"{package} not found installing...")
            subprocess.run(["pip3", "install", package], capture_output=False, text=False)