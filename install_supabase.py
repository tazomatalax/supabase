#!/usr/bin/env python3
"""
install_supabase.py

A dedicated script for installing and configuring Supabase locally.
This script handles cloning the Supabase repository, configuring environment
variables, and setting up the Docker containers.
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Union


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("supabase-installer")


def run_command(cmd: List[str], cwd: Optional[str] = None) -> subprocess.CompletedProcess:
    """
    Run a shell command and log it.
    
    Args:
        cmd (List[str]): Command to run as a list of strings.
        cwd (Optional[str]): Working directory to run the command in.
        
    Returns:
        subprocess.CompletedProcess: Result of the command execution.
        
    Raises:
        subprocess.CalledProcessError: If the command returns a non-zero exit code.
    """
    cmd_str = " ".join(cmd)
    logger.info(f"Running: {cmd_str}")
    
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        if result.stdout:
            logger.debug(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        if e.stdout:
            logger.error(f"Standard output: {e.stdout}")
        if e.stderr:
            logger.error(f"Standard error: {e.stderr}")
        raise


def clone_supabase_repo(repo_path: str = "supabase", branch: str = "master") -> None:
    """
    Clone the Supabase repository using sparse checkout if not already present.
    
    Args:
        repo_path (str): Path where the repo should be cloned.
        branch (str): Branch to checkout.
        
    Returns:
        None
    """
    repo_path_obj = Path(repo_path)
    
    if not repo_path_obj.exists():
        logger.info("Cloning the Supabase repository...")
        run_command([
            "git", "clone", "--filter=blob:none", "--no-checkout",
            "https://github.com/supabase/supabase.git", repo_path
        ])
        
        # Navigate to the repo directory
        os.chdir(repo_path)
        
        # Set up sparse checkout to only get the docker directory
        run_command(["git", "sparse-checkout", "init", "--cone"])
        run_command(["git", "sparse-checkout", "set", "docker"])
        run_command(["git", "checkout", branch])
        
        # Return to the original directory
        os.chdir("..")
        logger.info(f"Repository cloned successfully to {repo_path}")
    else:
        logger.info(f"Supabase repository already exists at {repo_path}, updating and ensuring sparse checkout...")
        # Store current working directory to return to it later
        original_cwd = Path.cwd()
        try:
            os.chdir(repo_path_obj) # Navigate to the repo directory
            
            run_command(["git", "fetch", "origin"])
            run_command(["git", "checkout", branch])
            run_command(["git", "pull", "origin", branch]) # Update the branch
            
            # Ensure sparse checkout is configured and applied
            run_command(["git", "sparse-checkout", "init", "--cone"]) # Idempotent
            run_command(["git", "sparse-checkout", "set", "docker"]) # This updates the working directory
            
        finally:
            os.chdir(original_cwd) # Return to the original directory
            
        logger.info(f"Repository {repo_path} updated and sparse checkout re-applied successfully")
    
    # Verify the docker directory structure
    find_docker_compose_file(repo_path)


def find_docker_compose_file(repo_path: str = "supabase") -> str:
    """
    Find the docker-compose.yml file in the Supabase repository.
    
    Args:
        repo_path (str): Path to the Supabase repository.
        
    Returns:
        str: Path to the docker-compose.yml file.
    """
    # Common locations for docker-compose.yml
    possible_paths = [
        Path(repo_path) / "docker" / "docker-compose.yml",
        Path(repo_path) / "docker" / "compose" / "docker-compose.yml",
        Path(repo_path) / "docker-compose.yml"
    ]
    
    # Debug the directory structure
    docker_dir = Path(repo_path) / "docker"
    if docker_dir.exists():
        logger.info(f"Docker directory exists at {docker_dir}")
        logger.info("Contents of docker directory:")
        for item in docker_dir.iterdir():
            logger.info(f"- {item}")
            # If it's a directory, list its contents too
            if item.is_dir():
                for subitem in item.iterdir():
                    logger.info(f"  - {subitem}")
    else:
        logger.error(f"Docker directory not found at {docker_dir}")
        
    # Check for docker-compose files
    for path in possible_paths:
        if path.exists():
            logger.info(f"Found docker-compose.yml at {path}")
            return str(path)
    
    # If none found, try to find any docker-compose file
    for root, _, files in os.walk(Path(repo_path)):
        for file in files:
            if file.endswith("docker-compose.yml"):
                compose_path = Path(root) / file
                logger.info(f"Found docker-compose.yml at {compose_path}")
                return str(compose_path)
    
    logger.error("No docker-compose.yml file found in the repository")
    return ""


def prepare_env_file(
    source_env_path: str = ".env", 
    target_env_path: str = "supabase/docker/.env",
    env_vars: Optional[Dict[str, str]] = None
) -> None:
    """
    Copy and configure the environment file for Supabase.
    
    Args:
        source_env_path (str): Source environment file path.
        target_env_path (str): Target environment file path.
        env_vars (Optional[Dict[str, str]]): Additional environment variables to set.
        
    Returns:
        None
    """
    target_path = Path(target_env_path)
    source_path = Path(source_env_path)
    example_env_path = Path('supabase/docker/.env.example')
    # Create parent directories if they don't exist
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if source_path.exists():
        logger.info(f"Copying {source_env_path} to {target_env_path}...")
        shutil.copyfile(source_path, target_path)
    elif example_env_path.exists():
        logger.info(f"Source .env file not found at {source_env_path}, copying .env.example to {target_env_path}...")
        shutil.copyfile(example_env_path, target_path)
    else:
        logger.warning(f"Source .env file not found at {source_env_path} and .env.example not found at {example_env_path}, creating default config...")
        # Create a basic .env file with default values
        default_env_content = """
# Default Supabase Environment Configuration
POSTGRES_PASSWORD=postgres
JWT_SECRET=super-secret-jwt-token-with-at-least-32-characters
ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiJ9.ZopqoUt20nEV9cklpv9e3yw3PVyZLmKs5qV0_JZTP3c
SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIn0.M2d3bEZPUFQ5cUZZQWQzMGxGdDROZ0ltN3pyUHQ5dFU
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=admin
"""
        with open(target_path, 'w') as f:
            f.write(default_env_content)

    # Add or update additional environment variables if provided
    if env_vars:
        logger.info("Adding custom environment variables...")
        with open(target_path, 'a') as f:
            for key, value in env_vars.items():
                f.write(f"\n{key}={value}")
        logger.info("Custom environment variables added successfully")


def verify_docker_installation() -> bool:
    """
    Verify that Docker is installed and running.
    
    Returns:
        bool: True if Docker is installed and running, False otherwise.
    """
    try:
        run_command(["docker", "--version"])
        run_command(["docker", "info"])
        logger.info("Docker is installed and running")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Docker is not installed or not running. Please install Docker and start it.")
        return False


def verify_docker_compose_installation() -> bool:
    """
    Verify that Docker Compose is installed.
    
    Returns:
        bool: True if Docker Compose is installed, False otherwise.
    """
    try:
        run_command(["docker", "compose", "version"])
        logger.info("Docker Compose is installed")
        return True
    except subprocess.CalledProcessError:
        logger.error("Docker Compose command failed. Please ensure Docker Compose is properly installed.")
        return False
    except FileNotFoundError:
        logger.error("Docker Compose not found. Please install Docker Compose.")
        return False


def stop_existing_containers(project_name: str = "supabase", repo_path: str = "supabase") -> None:
    """
    Stop and remove existing containers for the Supabase project.
    
    Args:
        project_name (str): Docker Compose project name.
        repo_path (str): Path to the Supabase repository.
        
    Returns:
        None
    """
    logger.info(f"Stopping and removing existing containers for the project '{project_name}'...")
    docker_compose_file = find_docker_compose_file(repo_path)
    if not docker_compose_file:
        logger.warning(f"Docker Compose file not found in {repo_path}, skipping stop.")
        return
        
    try:
        run_command([
            "docker", "compose", "-p", project_name, 
            "-f", docker_compose_file, "down"
        ])
        logger.info("Existing containers stopped and removed")
    except subprocess.CalledProcessError:
        logger.warning("No existing containers found or error stopping them")


def start_supabase(project_name: str = "supabase", detached: bool = True, repo_path: str = "supabase") -> None:
    """
    Start the Supabase services using Docker Compose.
    
    Args:
        project_name (str): Docker Compose project name.
        detached (bool): Run containers in detached mode.
        repo_path (str): Path to the Supabase repository.
        
    Returns:
        None
    """
    logger.info(f"Starting Supabase services with project name '{project_name}'...")
    docker_compose_file = find_docker_compose_file(repo_path)
    if not docker_compose_file:
        logger.error(f"Docker Compose file not found in {repo_path}. Cannot start Supabase.")
        raise FileNotFoundError(f"Docker Compose file not found in the Supabase repository")

    cmd = [
        "docker", "compose", "-p", project_name,
        "-f", docker_compose_file, "up"
    ]
    
    if detached:
        cmd.append("-d")
    
    run_command(cmd)
    logger.info("Supabase services started successfully")


def check_supabase_status(project_name: str = "supabase", repo_path: str = "supabase") -> bool:
    """
    Check if Supabase services are running properly.
    
    Args:
        project_name (str): Docker Compose project name.
        repo_path (str): Path to the Supabase repository.
        
    Returns:
        bool: True if Supabase services are running, False otherwise.
    """
    logger.info("Checking Supabase services status...")
    docker_compose_file = find_docker_compose_file(repo_path)
    if not docker_compose_file:
        logger.warning(f"Docker Compose file not found in {repo_path}, cannot check status.")
        return False
        
    try:
        result = run_command([
            "docker", "compose", "-p", project_name,
            "-f", docker_compose_file, "ps", "--format", "json"
        ])
        
        # If we get output without errors, services are running
        if result.stdout and "running" in result.stdout.lower():
            logger.info("Supabase services are running")
            return True
        else:
            logger.warning("Some Supabase services may not be running properly")
            return False
    except subprocess.CalledProcessError:
        logger.error("Failed to check Supabase services status")
        return False


def main() -> None:
    """
    Main function to install and start Supabase.
    """
    parser = argparse.ArgumentParser(
        description='Install and configure Supabase locally using Docker.'
    )
    parser.add_argument(
        '--env-file', type=str, default=".env",
        help='Path to environment file (default: .env)'
    )
    parser.add_argument(
        '--project-name', type=str, default="supabase",
        help='Docker Compose project name (default: supabase)'
    )
    parser.add_argument(
        '--repo-path', type=str, default="supabase",
        help='Path to clone the Supabase repository (default: supabase)'
    )
    parser.add_argument(
        '--no-detach', action='store_true',
        help='Run Docker Compose in foreground (not detached) mode'
    )
    parser.add_argument(
        '--branch', type=str, default="master",
        help='Branch to checkout (default: master)'
    )
    parser.add_argument(
        '--verbose', action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set log level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info("Starting Supabase installation...")
    
    # Check Docker and Docker Compose installations
    if not verify_docker_installation() or not verify_docker_compose_installation():
        logger.error("Docker or Docker Compose not available. Aborting installation.")
        sys.exit(1)
    
    # Clone Supabase repository
    try:
        clone_supabase_repo(args.repo_path, args.branch)
    except Exception as e:
        logger.error(f"Error cloning Supabase repository: {e}")
        sys.exit(1)
    
    # Prepare environment file
    try:
        prepare_env_file(args.env_file, f"{args.repo_path}/docker/.env")
    except Exception as e:
        logger.error(f"Error preparing environment file: {e}")
        sys.exit(1)
    
    # Stop any existing containers
    try:
        stop_existing_containers(args.project_name, args.repo_path)
    except Exception as e:
        logger.error(f"Error stopping existing containers: {e}")
        # We can continue even if this fails
    
    # Start Supabase
    try:
        start_supabase(args.project_name, not args.no_detach, args.repo_path)
    except Exception as e:
        logger.error(f"Error starting Supabase: {e}")
        sys.exit(1)
    
    # Check status
    logger.info("Waiting for Supabase services to initialize...")
    time.sleep(10)  # Give some time for services to start
    
    if check_supabase_status(args.project_name, args.repo_path):
        logger.info("""
Supabase has been successfully installed and started!

Access the services at:
- Studio (Dashboard): http://localhost:3000
- API: http://localhost:8000
- PostgreSQL: localhost:5432

Default credentials can be found in your .env file.
""")
    else:
        logger.warning("""
Supabase services have been started, but some may not be running correctly.
Check the Docker logs for more information:

docker compose -p %s -f %s/docker/docker-compose.yml logs
""", args.project_name, args.repo_path)


if __name__ == "__main__":
    main()
