#!/usr/bin/env python3
import os
import subprocess
import platform
import sys

def run_command(command, shell=False):
    """Run a command and return its output"""
    print(f"Running: {command}")
    if shell:
        process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        process = subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process

def check_docker():
    """Check if Docker is installed and running"""
    print("Checking Docker installation...")
    docker_check = run_command("docker info")
    if docker_check.returncode != 0:
        print("Docker is not running or not installed. Please install and start Docker first.")
        sys.exit(1)
    print("Docker is running.")

def check_gvisor():
    """Check if gVisor is installed"""
    print("Checking gVisor installation...")
    docker_info = run_command("docker info")
    if b"runsc" in docker_info.stdout:
        print("gVisor runtime (runsc) is already installed.")
        return True
    return False

def install_gvisor_ubuntu():
    """Install gVisor on Ubuntu"""
    print("Installing gVisor on Ubuntu...")
    
    # Add the Google Cloud public key
    key_cmd = run_command("curl -fsSL https://gvisor.dev/archive.key | sudo apt-key add -", shell=True)
    if key_cmd.returncode != 0:
        print("Failed to add Google Cloud public key.")
        return False
    
    # Add the gVisor repository
    repo_cmd = run_command('echo "deb https://storage.googleapis.com/gvisor/releases release main" | sudo tee /etc/apt/sources.list.d/gvisor.list', shell=True)
    if repo_cmd.returncode != 0:
        print("Failed to add gVisor repository.")
        return False
    
    # Update apt and install runsc
    update_cmd = run_command("sudo apt-get update", shell=True)
    if update_cmd.returncode != 0:
        print("Failed to update apt.")
        return False
    
    install_cmd = run_command("sudo apt-get install -y runsc", shell=True)
    if install_cmd.returncode != 0:
        print("Failed to install runsc.")
        return False
    
    # Configure Docker to use gVisor
    config_cmd = run_command('sudo runsc install', shell=True)
    if config_cmd.returncode != 0:
        print("Failed to configure Docker to use gVisor.")
        return False
    
    # Restart Docker
    restart_cmd = run_command("sudo systemctl restart docker", shell=True)
    if restart_cmd.returncode != 0:
        print("Failed to restart Docker.")
        return False
    
    print("gVisor installed successfully.")
    return True

def main():
    """Main function to set up gVisor"""
    print("gVisor Setup Script")
    print("-------------------")
    
    # Check if running as root/sudo
    if os.geteuid() != 0:
        print("This script requires sudo privileges. Please run with sudo.")
        sys.exit(1)
    
    # Check Docker
    check_docker()
    
    # Check if gVisor is already installed
    if check_gvisor():
        print("gVisor is already set up correctly.")
        sys.exit(0)
    
    # Install gVisor based on OS
    distro = platform.linux_distribution()[0].lower() if hasattr(platform, 'linux_distribution') else ""
    
    if "ubuntu" in distro or "debian" in distro:
        success = install_gvisor_ubuntu()
    else:
        print("Automatic installation is only supported on Ubuntu/Debian.")
        print("Please follow manual installation instructions for your OS:")
        print("https://gvisor.dev/docs/user_guide/install/")
        sys.exit(1)
    
    if success:
        print("gVisor installation completed successfully.")
        print("You can now use the 'runsc' runtime with Docker.")
    else:
        print("gVisor installation failed. Please try manual installation.")
        sys.exit(1)

if __name__ == "__main__":
    main()
