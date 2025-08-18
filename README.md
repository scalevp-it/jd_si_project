# System Initiative Component Management System

A comprehensive Python application for managing System Initiative (SI) components, schemas, and configurations. This system provides tools for creating components, extracting existing configurations, generating schema templates, and managing complex SI deployments.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ with virtual environment
- System Initiative workspace access
- API token with appropriate permissions

### Installation & Setup

1. **Clone and setup environment:**
```bash
cd /path/to/si_project
python -m venv .
source bin/activate  # On macOS/Linux
# or
Scripts\activate     # On Windows
pip install -r requirements.txt  # if requirements.txt exists
```

2. **Set environment variables:**
```bash
export SI_WORKSPACE_ID='your-workspace-id'
export SI_API_TOKEN='your-api-token'
export SI_HOST='https://api.systeminit.com'  # optional
```

Or create a `.env` file:
```bash
# .env file
SI_WORKSPACE_ID=your-workspace-id
SI_API_TOKEN=your-api-token
SI_HOST=https://api.systeminit.com
```

3. **Run the application:**
```bash
python app.py --interactive
```

## 📁 Project Structure

```
si_project/
├── README.md                       # This comprehensive guide
├── .env                           # Environment variables (create this)
├── app.py                         # Main application entry point
├── src/                           # Core application modules
│   ├── __init__.py
│   ├── si_session.py              # SI API session management
│   ├── component_config_system.py # Component configuration management
│   ├── schema_fetcher.py          # Schema template generator
│   ├── changeset_extractor.py     # Live component extraction
│   ├── component_helpers.py       # Helper utilities
│   └── [other modules]            # Additional functionality
├── component_configs/             # Component configurations directory
│   ├── README.md                  # Component configs documentation
│   ├── examples/                  # Schema templates (.example files only)
│   │   └── *.json.example         # Schema templates from fetcher
│   ├── component_templates/       # Component creation configurations
│   │   └── *.json                 # Component creation templates
│   └── current_components/        # Extracted live component data
│       ├── *.json                 # Individual extracted components
│       └── extraction_summary_*.json # Extraction metadata
├── lib/                          # Python packages (virtual environment)
└── [test files]                 # Testing utilities
```

## 🎛️ Application Modes

### Interactive Mode (Recommended)
Full-featured menu-driven interface:
```bash
python app.py --interactive
```

### Basic Mode
Simple component listing:
```bash
python app.py
```

### Component Creation Mode
Direct access to component creation:
```bash
python app.py --create-components
```

## 🌟 Core Features

### 1. 📋 Component Management
- **List Components**: View all components in changesets
- **Filter by Schema**: Find components by schema type
- **Search by Name**: Locate specific components
- **Component Details**: View comprehensive component information

### 2. 🔧 Component Creation System
- **Template-Based Creation**: Create components from JSON templates
- **Bulk Operations**: Create multiple components simultaneously
- **Configuration Validation**: Ensure templates are valid before creation
- **Dynamic Templates**: Generate new templates for any schema

**Template Format:**
```json
{
  "name": "my-component",
  "schema_name": "AWS::EC2::Instance",
  "attributes": {
    "/domain/Name": "my-ec2-instance",
    "/domain/InstanceType": "t3.micro",
    "/domain/ImageId": "ami-0abcdef1234567890",
    "/secrets/AWS Credential": {
      "$source": {
        "component": "my-aws-credential",
        "path": "/secrets/AWS Credential"
      }
    }
  }
}
```

### 3. 📦 Changeset Component Extractor
Extract live components from changesets and transform them into reusable templates:

**Features:**
- **Live Extraction**: Extract components from any changeset
- **Template Transformation**: Convert to standard template format
- **Dynamic References**: Auto-generate `$source` reference examples
- **Schema-Specific Patterns**: Tailored reference patterns for each schema type

**Generated Reference Examples:**
```json
"_reference_examples": {
  "description": "Examples of how to reference this AWS::EC2::VPC component in other templates",
  "component_name": "new-ui-vpc",
  "schema_name": "AWS::EC2::VPC",
  "available_outputs": [
    {
      "socket_name": "Vpc Id",
      "path": "/domain/Vpc Id",
      "description": "Reference to Vpc Id from new-ui-vpc"
    }
  ],
  "usage_examples": {
    "reference_vpc_id": {
      "/domain/Vpc Id": {
        "$source": {
          "component": "new-ui-vpc",
          "path": "/domain/Vpc Id"
        }
      }
    }
  },
  "common_references": {
    "vpc_id_reference": {
      "description": "Reference VPC ID for subnet creation",
      "example": {
        "/domain/VpcId": {
          "$source": {
            "component": "new-ui-vpc",
            "path": "/resource_value/VpcId"
          }
        }
      }
    }
  }
}
```

### 4. 📚 Schema Template Generator
Generate comprehensive templates for any SI schema:

**Features:**
- **Complete Examples**: Full attribute coverage with sample values
- **Minimal Examples**: "Needed to deploy" with only required fields
- **Dynamic Requirements**: Auto-detect required vs optional attributes
- **AWS CloudFormation Integration**: Fetch requirements from live AWS docs
- **SI UI Format**: Proper nested paths matching SI interface

**Generated Template Structure:**
```json
{
  "_metadata": { /* Schema and generation info */ },
  "_needed_to_deploy": {
    "description": "Minimal example with only required fields needed for deployment",
    "attribute_count": 4,
    "create_component_request": {
      "schemaName": "AWS::EC2::Instance",
      "name": "minimal-component",
      "attributes": { /* Only essential attributes */ }
    }
  },
  "_complete_usage_example": {
    "description": "Complete ready-to-use example with all available attributes",
    "create_component_request": { /* Full attribute coverage */ }
  }
}
```

### 5. 🔄 Changeset Management
- **Changeset Selection**: Choose or create changesets for operations
- **Multi-Changeset Support**: Work with different changesets seamlessly
- **Status Tracking**: View changeset status and metadata

### 6. 📊 Schema Discovery
- **Schema Listing**: View all available schemas in workspace
- **Schema Details**: Comprehensive schema information
- **Installation Status**: Check which schemas are installed

## 🎯 Common Workflows

### Workflow 1: Extract and Reuse Existing Components
1. **Extract Live Components**: Menu option 7 → Extract changeset components
2. **Review Templates**: Check `component_configs/current_components/`
3. **Copy Reference Examples**: Use the `_reference_examples` for connections
4. **Create New Components**: Use extracted templates as basis for new infrastructure

### Workflow 2: Create Infrastructure from Templates
1. **Generate Schema Template**: Menu option 6 → Generate schema templates
2. **Customize Template**: Edit the generated `.example` file
3. **Save as Component Config**: Move to `component_templates/` directory
4. **Create Components**: Menu option 5 → Create from configurations

### Workflow 3: Build Connected Infrastructure
1. **Extract Base Components**: Extract foundational components (VPC, credentials)
2. **Use Reference Examples**: Copy `$source` patterns from extracted files
3. **Create Dependent Components**: Build subnets, security groups, EC2 instances
4. **Deploy Incrementally**: Create components in dependency order

## 🛠️ Advanced Configuration

### Component Template Format
Templates use SI's standard attribute path format:

```json
{
  "name": "component-name",
  "schema_name": "Schema::Name",
  "attributes": {
    "/domain/AttributeName": "value",
    "/secrets/SecretName": {
      "$source": {
        "component": "source-component-name",
        "path": "/secrets/SecretName"
      }
    },
    "/domain/nested/Path": "nested-value"
  }
}
```

### Supported Reference Types
- **Direct Values**: Simple strings, numbers, booleans
- **Component References**: `$source` objects for inter-component connections
- **Arrays and Objects**: Complex nested structures
- **Secret References**: Secure credential passing between components

### Schema-Specific Reference Patterns

**AWS::EC2::VPC:**
```json
"/domain/VpcId": {
  "$source": {
    "component": "vpc-component-name",
    "path": "/resource_value/VpcId"
  }
}
```

**AWS Credential:**
```json
"/secrets/AWS Credential": {
  "$source": {
    "component": "credential-component-name", 
    "path": "/secrets/AWS Credential"
  }
}
```

**Region:**
```json
"/domain/extra/Region": {
  "$source": {
    "component": "region-component-name",
    "path": "/domain/region"
  }
}
```

## 🔧 Troubleshooting

### Common Issues

**Authentication Errors:**
```bash
# Check environment variables
echo $SI_WORKSPACE_ID
echo $SI_API_TOKEN

# Test authentication
python -c "from src.si_session import SISession; SISession.check_env_vars()"
```

**Schema Not Found:**
- Verify schema name matches exactly (case-sensitive)
- Check if schema is installed in your workspace
- Use schema listing feature to see available schemas

**Component Creation Failures:**
- Validate JSON template format
- Check required attributes are present
- Ensure referenced components exist
- Verify changeset is in "Open" status

**Extraction Issues:**
- Ensure changeset has components
- Check component permissions
- Verify API token has appropriate access

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Examples

### Example 1: AWS Infrastructure Stack
```json
// 1. Extract existing AWS credential
// 2. Create VPC template
{
  "name": "production-vpc",
  "schema_name": "AWS::EC2::VPC",
  "attributes": {
    "/domain/Name": "production-vpc",
    "/domain/CidrBlock": "10.0.0.0/16",
    "/domain/EnableDnsHostnames": true,
    "/domain/EnableDnsSupport": true,
    "/secrets/AWS Credential": {
      "$source": {
        "component": "aws-credentials",
        "path": "/secrets/AWS Credential"
      }
    }
  }
}
```

### Example 2: Connected Subnet
```json
{
  "name": "production-subnet-public", 
  "schema_name": "AWS::EC2::Subnet",
  "attributes": {
    "/domain/Name": "production-subnet-public",
    "/domain/CidrBlock": "10.0.1.0/24",
    "/domain/VpcId": {
      "$source": {
        "component": "production-vpc",
        "path": "/resource_value/VpcId"
      }
    },
    "/domain/AvailabilityZone": "us-west-2a",
    "/secrets/AWS Credential": {
      "$source": {
        "component": "aws-credentials", 
        "path": "/secrets/AWS Credential"
      }
    }
  }
}
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Submit pull request with detailed description

### Code Style
- Follow existing patterns in the codebase
- Use descriptive variable names
- Include comprehensive error handling
- Add docstrings for public functions
- Test with various SI environments

## 📄 License

This project is part of System Initiative tooling. Please refer to SI's licensing terms.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review SI documentation at [docs.systeminit.com](https://docs.systeminit.com)
3. Create issues in the project repository
4. Contact SI support for workspace-related issues

## 🚀 What's Next

Planned enhancements:
- [ ] Automated dependency resolution
- [ ] Component validation and testing
- [ ] CI/CD integration
- [ ] Configuration versioning
- [ ] Multi-workspace support
- [ ] Advanced search and filtering
- [ ] Component relationship visualization

---

**Happy System Initiative building!** 🎉