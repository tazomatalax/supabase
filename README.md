# Supabase Installation Script

This project provides a Python script to easily install and configure Supabase locally using Docker. The script handles all necessary steps including repository cloning, environment setup, and Docker container management.

## Features

- Automated Supabase repository cloning with sparse checkout (only the Docker directory)
- Environment file configuration with sensible defaults
- Docker and Docker Compose verification
- Container lifecycle management (stop, start, status checking)
- Cross-platform support (Linux, macOS, Windows)
- Detailed logging and error handling

## Prerequisites

- Python 3.6+
- Docker and Docker Compose
- Git

## Installation

Clone this repository to your local machine:

```bash
git clone https://github.com/yourusername/supabase-installer.git
cd supabase-installer
```

## Usage

### Basic Usage

To install and start Supabase with default settings:

```bash
python install_supabase.py
```

This will:
1. Clone the Supabase repository (if not already present)
2. Set up the environment configuration
3. Stop any existing Supabase containers
4. Start the Supabase services

### Advanced Options

The script supports several command-line options for customization:

```bash
# Use a custom environment file
python install_supabase.py --env-file my-custom.env

# Specify a different project name for Docker Compose
python install_supabase.py --project-name my-supabase

# Clone the repository to a specific location
python install_supabase.py --repo-path /path/to/supabase

# Run in foreground mode (not detached)
python install_supabase.py --no-detach

# Use a specific branch
python install_supabase.py --branch develop

# Enable verbose logging
python install_supabase.py --verbose
```

## Accessing Supabase Services

Once installation is complete, you can access Supabase services at:

- **Studio (Dashboard)**: [http://localhost:3000](http://localhost:3000)
- **API**: [http://localhost:8000](http://localhost:8000)
- **PostgreSQL**: localhost:5432

The default credentials can be found in your `.env` file.

## Environment Configuration

The script will use an existing `.env` file if available, or create one with default values. The following environment variables are set by default:

- `POSTGRES_PASSWORD`: postgres
- `JWT_SECRET`: super-secret-jwt-token-with-at-least-32-characters
- `ANON_KEY`: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiJ9.ZopqoUt20nEV9cklpv9e3yw3PVyZLmKs5qV0_JZTP3c
- `SERVICE_ROLE_KEY`: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIn0.M2d3bEZPUFQ5cUZZQWQzMGxGdDROZ0ltN3pyUHQ5dFU
- `DASHBOARD_USERNAME`: admin
- `DASHBOARD_PASSWORD`: admin

**Important**: For production use, you should modify these default values in your `.env` file.

## Troubleshooting

### Docker Issues

If you encounter Docker-related issues:

1. Ensure Docker is running:
   ```bash
   docker info
   ```

2. Check Supabase container logs:
   ```bash
   docker compose -p supabase -f supabase/docker/docker-compose.yml logs
   ```

### Permission Issues

If you encounter permission issues on Linux:

```bash
# Make the script executable
chmod +x install_supabase.py
```

## Development

### Running Tests

The project includes a comprehensive test suite:

```bash
# Run all tests
python -m unittest test_install_supabase.py

# Run specific test
python -m unittest test_install_supabase.TestInstallSupabase.test_run_command_success
```

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.