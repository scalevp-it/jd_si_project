#!/usr/bin/env python3
"""
Setup script for System Initiative Component Configuration System
"""

import os
import json
from pathlib import Path

def create_directory_structure():
    """Create the necessary directory structure"""
    directories = [
        "component_configs",
        "src"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_sample_configs():
    """Create sample configuration files"""
    
    # AWS configurations
    aws_configs = [
        {
            "name": "production-web-server",
            "schema_name": "AWS EC2 Instance",
            "attributes": {
                "InstanceType": "t3.medium",
                "ImageId": "ami-0c02fb55956c7d316",
                "KeyName": "production-keypair",
                "SecurityGroups": ["web-server-sg"],
                "UserData": "#!/bin/bash\nyum update -y\nyum install -y httpd\nsystemctl start httpd\nsystemctl enable httpd"
            },
            "domain": {
                "Name": "ProductionWebServer",
                "Environment": "production",
                "Owner": "devops-team",
                "CostCenter": "engineering",
                "Project": "main-website"
            }
        },
        {
            "name": "development-database",
            "schema_name": "AWS RDS Instance", 
            "attributes": {
                "DBInstanceClass": "db.t3.micro",
                "Engine": "mysql",
                "EngineVersion": "8.0.35",
                "AllocatedStorage": 20,
                "DBName": "devdb",
                "MasterUsername": "admin",
                "BackupRetentionPeriod": 7,
                "MultiAZ": False
            },
            "domain": {
                "Name": "DevelopmentDatabase",
                "Environment": "development",
                "Owner": "dev-team"
            },
            "secrets": {
                "MasterUserPassword": "{{SECRET:db-password}}"
            }
        },
        {
            "name": "main-vpc",
            "schema_name": "AWS VPC",
            "attributes": {
                "CidrBlock": "10.0.0.0/16",
                "EnableDnsHostnames": True,
                "EnableDnsSupport": True,
                "InstanceTenancy": "default"
            },
            "domain": {
                "Name": "MainVPC",
                "Environment": "production",
                "Owner": "network-team"
            }
        }
    ]
    
    # Docker configurations
    docker_configs = [
        {
            "name": "nginx-web-server",
            "schema_name": "Docker Container",
            "attributes": {
                "Image": "nginx:1.21-alpine",
                "Ports": ["80:80", "443:443"],
                "Environment": {
                    "NGINX_HOST": "localhost",
                    "NGINX_PORT": "80"
                },
                "Volumes": [
                    "/var/log/nginx:/var/log/nginx",
                    "/etc/nginx/conf.d:/etc/nginx/conf.d:ro"
                ],
                "RestartPolicy": "always"
            },
            "domain": {
                "Name": "NginxWebServer",
                "Version": "1.21",
                "Environment": "production",
                "Owner": "web-team"
            }
        },
        {
            "name": "postgres-database",
            "schema_name": "Docker Container",
            "attributes": {
                "Image": "postgres:15",
                "Ports": ["5432:5432"],
                "Environment": {
                    "POSTGRES_DB": "appdb",
                    "POSTGRES_USER": "appuser",
                    "POSTGRES_PASSWORD": "{{SECRET:postgres-password}}"
                },
                "Volumes": [
                    "postgres-data:/var/lib/postgresql/data",
                    "./init.sql:/docker-entrypoint-initdb.d/init.sql:ro"
                ],
                "RestartPolicy": "always"
            },
            "domain": {
                "Name": "PostgresDatabase",
                "Version": "15",
                "Environment": "production",
                "Owner": "backend-team"
            }
        }
    ]
    
    # Kubernetes configurations
    k8s_configs = [
        {
            "name": "api-deployment",
            "schema_name": "Kubernetes Deployment",
            "attributes": {
                "replicas": 3,
                "selector": {
                    "matchLabels": {
                        "app": "api-service"
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "api-service",
                            "version": "v1.2.0"
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": "api",
                                "image": "mycompany/api-service:v1.2.0",
                                "ports": [
                                    {
                                        "containerPort": 8080,
                                        "name": "http"
                                    }
                                ],
                                "env": [
                                    {
                                        "name": "DATABASE_URL",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "name": "api-secrets",
                                                "key": "database-url"
                                            }
                                        }
                                    }
                                ],
                                "resources": {
                                    "requests": {
                                        "memory": "256Mi",
                                        "cpu": "250m"
                                    },
                                    "limits": {
                                        "memory": "512Mi",
                                        "cpu": "500m"
                                    }
                                }
                            }
                        ]
                    }
                }
            },
            "domain": {
                "namespace": "production",
                "app": "api-service",
                "team": "backend",
                "version": "v1.2.0"
            }
        }
    ]
    
    # Write configuration files
    config_files = {
        "component_configs/aws_examples.json.example": aws_configs,
        "component_configs/docker_examples.json.example": docker_configs,
        "component_configs/kubernetes_examples.json.example": k8s_configs
    }
    
    for filename, configs in config_files.items():
        with open(filename, 'w') as f:
            json.dump(configs, f, indent=2)
        print(f"✅ Created configuration file: {filename}")

def create_readme():
    """Create a README file with usage instructions"""
    readme_content = """# System Initiative Component Configuration System

This system allows you to create and manage System Initiative components using JSON configuration files.

## Directory Structure

```
├── component_configs/          # Component configuration files
│   ├── aws_examples.json      # AWS component examples
│   ├── docker_examples.json   # Docker component examples
│   └── kubernetes_examples.json # Kubernetes component examples
├── src/
│   ├── si_session.py          # SI session management
│   └── component_config_system.py # Main configuration system
├── app.py                     # Enhanced application
└── README.md                  # This file
```

## Usage

### 1. Set up environment variables

```bash
export SI_WORKSPACE_ID='your-workspace-id'
export SI_API_TOKEN='your-api-token'
export SI_HOST='https://api.systeminit.com'  # optional
```

### 2. Run the application

**Basic mode** (list components):
```bash
python app.py
```

**Interactive mode** (explore and manage):
```bash
python app.py --interactive
```

**Component creation mode**:
```bash
python app.py --create-components
```

### 3. Configuration File Format

Each configuration file contains an array of component configurations:

```json
[
  {
    "name": "my-component",
    "schema_name": "AWS EC2 Instance",
    "attributes": {
      "InstanceType": "t3.micro",
      "ImageId": "ami-12345"
    },
    "domain": {
      "Name": "MyComponent",
      "Environment": "development"
    },
    "secrets": {
      "Password": "{{SECRET:my-password}}"
    }
  }
]
```

### 4. Creating Components

1. **From Interactive Mode**: Choose option 5 for component creation mode
2. **Direct Mode**: Run `python app.py --create-components`
3. **Bulk Creation**: Select multiple configurations to create at once

### 5. Adding New Configurations

1. Create a new JSON file in `component_configs/`
2. Follow the schema format shown above
3. Run the application - it will automatically load your new configurations

### 6. Configuration Fields

- **name**: Component name (required)
- **schema_name**: SI schema name (required)
- **attributes**: Schema-specific attributes (optional)
- **domain**: Domain properties (optional)
- **secrets**: Secret references (optional)
- **resource_id**: External resource ID (optional)
- **view_name**: View name (optional)
- **connections**: Component connections (optional)
- **subscriptions**: Component subscriptions (optional)
- **managed_by**: Management relationship (optional)

## Examples

The system comes with example configurations for:
- AWS components (EC2, RDS, VPC)
- Docker containers
- Kubernetes deployments and services

## Features

- ✅ Load configurations from JSON files
- ✅ Validate configurations
- ✅ Create single or multiple components
- ✅ Interactive component management
- ✅ Template generation for new schemas
- ✅ Comprehensive error handling and logging

## Troubleshooting

1. **Authentication errors**: Check your SI_WORKSPACE_ID and SI_API_TOKEN
2. **Schema not found**: Verify the schema name exists in your workspace
3. **Configuration errors**: Run validation mode to check your JSON files
"""
    
    with open("README.md", "w") as f:
        f.write(readme_content)
    print("✅ Created README.md")

def create_gitignore():
    """Create a .gitignore file"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log

# SI specific
si_session_cache.json
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    print("✅ Created .gitignore")

def main():
    """Main setup function"""
    print("🚀 Setting up System Initiative Component Configuration System")
    print("=" * 65)
    
    print("\n1. Creating directory structure...")
    create_directory_structure()
    
    print("\n2. Creating sample configuration files...")
    create_sample_configs()
    
    print("\n3. Creating documentation...")
    create_readme()
    
    print("\n4. Creating .gitignore...")
    create_gitignore()
    
    print(f"\n✅ Setup completed successfully!")
    print(f"\n🔧 Next steps:")
    print(f"   1. Set your environment variables:")
    print(f"      export SI_WORKSPACE_ID='your-workspace-id'")
    print(f"      export SI_API_TOKEN='your-api-token'")
    print(f"   2. Run the application:")
    print(f"      python app.py --interactive")
    print(f"   3. Try component creation mode:")
    print(f"      python app.py --create-components")

if __name__ == "__main__":
    main()