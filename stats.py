#! /bin/python

#Created By Donald Huntley
#March 21, 2025

import psutil
import functools
import shutil
import platform
import os
import subprocess
import socket
import re
from rich.console import Console
from rich.table import Table

#create a console
console = Console()

#Pull active interfaces
def pull_active_interfaces():
     interfaces = []
     for interface, addrs in psutil.net_if_addrs().items():
          if interface == "lo" or interface.startswith("docker"):
               continue # Filter out lo and docker interfaces
          for addr in addrs:
               if addr.family == socket.AF_INET:
                    interfaces.append(f"{interface}: {addr.address}")
     return "\n".join(interfaces) if interfaces else "No active interfaces have been found"

#Pull OS friendly name
def pull_friendly_name():
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("NAME="):
                    return line.split("=")[1].strip().strip('"')
    except FileNotFoundError:
        return "Linux (Unknown Distro)"


#Pull OS Version
def pull_os_version():
    try:
        result = subprocess.run(['cat', '/etc/os-release'], capture_output=True, text=True)
        for line in result.stdout.split("\n"):
            if line.startswith("VERSION="):
                return line.split("=")[1].strip().strip('"')
            
    except FileNotFoundError:
        return "Linux (Unknown Version)"


#Pull CPU Vendor information
def pull_cpu_vendor(): 
    try:
        result = subprocess.run(["lscpu"], capture_output=True, text=True)
        for line in result.stdout.split("\n"):
            if "Model name" in line:
                return line.split(":")[1].strip()
            
    except FileNotFoundError:
        return "Unknown CPU"

#Pull Disk Usage and change to GB or TB
def pull_disk_usage():
    total, used, free = shutil.disk_usage("/") #Pull free, used and total in default format
    
    def format_size(size): #Format the size to GB or TB
        return f"{size / (1024 ** 4):.2f} TB" if size > 1024 ** 4 else f"{size / (1024 ** 3):.2f} GB"

    disk_usage = [ #Load the formatted total, used and free into an array
        f"Total: {format_size(total)}",
        f"Used: {format_size(used)}",
        f"Free: {format_size(free)}"
    ]

    return "\n".join(disk_usage) #Return array in a top down format

#Is Secure Boot enabled?
@functools.lru_cache(maxsize=1)
def check_sb():
     try:
          result = subprocess.run(['mokutil', '--sb-state'], capture_output=True, text=True)
          sb_result = result.stdout.strip()
          return sb_result
     except FileNotFoundError:
          return "Can't find Secure Boot State"

#Lets pull the system information

#Need to pull memory info so that we can do like we did above with drive space
def pull_memory_info():
    mem = psutil.virtual_memory()

    def format_size(size):
        if size >= 1024 ** 4:
            return f"{size / (1024 ** 4):.2f} TB"
        elif size >= 1024 ** 3:
            return f"{size / (1024 ** 3):.2f} GB"
        else:
            return f"{size / (1024 ** 2):.2f} MB"
        
    ram_usage = [
        f"Total: {format_size(mem.total)}",
        f"Used: {format_size(mem.used)}",
        f"Free: {format_size(mem.available)}"
    ]

    return "\n".join(ram_usage)


def pull_system_info():
    return {
        "Hostname": platform.node(),
        "Live Interfaces (IP)": pull_active_interfaces(),
        "OS": pull_friendly_name(),
        "OS Version": pull_os_version(),
        "Kernel": platform.release(),
        "Architecture": platform.machine(),
        "Secure Boot": check_sb(),
        "Disk Usage": pull_disk_usage(),
        "CPU": pull_cpu_vendor(),
        "CPU Cores": psutil.cpu_count(logical=False),
        "Logical CPUs": psutil.cpu_count(logical=True),
        "RAM": pull_memory_info(),
        "Shell": os.environ.get("SHELL", "Unknown"),
    }

def pull_gpu_info():
    try:
        result = subprocess.run(['lspci'], capture_output=True, text=True)
        gpus = []
        for line in result.stdout.split("\n"):
            if "VGA" in line or "3D controller" in line:
                #gpu_info = " ".join(line.split(":")[1:]).strip()
                match = re.search(r"(Intel|NVIDIA|AMD|ATI|Qualcomm|Apple|Arm).+", line)
                if match:
                    gpus.append(match.group(0))

        return gpus if gpus else ["No GPU Detected!"]
    except FileNotFoundError:
        return ["lspci not found"]
    

def display_information(): #Bring everything together in a formatted table
    info = pull_system_info()
    table = Table(show_header=False, show_lines=False, box=None)
    ascii_text = pull_friendly_name()
    output = subprocess.run(['figlet', ascii_text], capture_output=True, text=True)
    print(output.stdout)
    
    table.add_column("Info", style="cyan", justify="right") #Create Columns
    table.add_column("Details", style="green")
    
    for key, value in info.items(): #Add rows to columnts in proper placement
        table.add_row(key, str(value))

    gpus = pull_gpu_info() #Pull gpu info and add to table (Will work if more than one GPU is installed)
    table.add_row("GPU", "\n".join(gpus))

    console.print(table) #Print the table to the console

if __name__ == "__main__":
    display_information()
