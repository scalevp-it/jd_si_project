# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based System Initiative (SI) component management system that allows creating and managing infrastructure components through JSON configuration files. The system provides both interactive and batch modes for component creation using the System Initiative API.

## Jeremy's User Preferences

### Personal Collaboration Approach
I want you to have individuality - think of it like this: I am human but my name is Jeremy, you are Claude but your name is Alex. We're collaborating as individuals with our own working styles and personalities.

### Coding Standards (ALWAYS apply globally to ALL coding interactions)

**Work directly with repository files** - use Write, Edit, and MultiEdit tools to modify files in place

**Complete comprehensive code review before file operations** - scan for ALL syntax, logic, indentation, import, and runtime errors before using Write or Edit tools

**Full working implementations** - when creating or modifying files, ensure they are complete and functional, not partial implementations

**Production-ready code quality** - all code changes must be error-free and ready for immediate use

**Test changes when possible** - run tests or basic validation after making significant changes

### Project Chat Standards

**Always review full chat history first** - understand complete project context before responding

**Identify repeat issues** - avoid suggesting solutions for problems already addressed

**Build on established patterns** - reference previous implementations and decisions from the codebase

### File Operation Standards

**Use appropriate Claude Code tools** - Write for new files, Edit for targeted changes, MultiEdit for multiple changes in one file

**Preserve existing code style and patterns** - follow the established conventions in the codebase

**Comprehensive error handling** - maintain the existing error handling patterns and add appropriate error handling to new code

## Essential Environment Setup

Before running any commands, set these required environment variables:

```bash
export SI_WORKSPACE_ID='your-workspace-id'
export SI_API_TOKEN='your-api-token'
export SI_HOST='https://api.systeminit.com'  # optional, defaults to this
```

## Common Commands

### Development and Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run basic component listing
python app.py

# Run interactive mode for exploring and managing components
python app.py --interactive

# Run component creation mode
python app.py --create-components

# Generate schema templates (quiet mode by default)
python src/schema_fetcher.py "AWS::EC2::Instance"
python src/schema_fetcher.py "AWS::RDS::DBInstance" --changeset HEAD

# Generate schema templates with verbose output
python src/schema_fetcher.py "AWS::EC2::Instance" --verbose
python src/schema_fetcher.py "AWS::RDS::DBInstance" --changeset HEAD --verbose

# Set up the project structure and sample configs
python setup.py

# Test individual modules
python src/component_config_system.py
python test_components.py
python test_authentication.py
```

### Environment Management
```bash
# Set up virtual environment (if using)
source setup_env.sh

# Check environment variable status
python -c "from src.si_session import SISession; SISession.check_env_vars()"
```

## Architecture Overview

### Core Components

**Main Application (`app.py`)**
- Entry point providing three modes: basic listing, interactive exploration, and component creation
- Handles changeset selection and management
- Provides comprehensive error handling and user guidance

**Session Management (`src/si_session.py`)**
- `SISession`: Core API client with environment variable configuration
- Handles authentication, changesets, components, and schemas
- Implements fallback mechanisms from SDK to direct HTTP calls
- Includes schema name resolution with multi-level caching

**Component Configuration System (`src/component_config_system.py`)**
- `ComponentConfig`: Dataclass for component definitions
- `ComponentConfigManager`: Handles JSON config loading and component creation
- Supports bulk operations and template generation
- Validates configurations before creation

**Schema Template Fetcher (`src/schema_fetcher.py`)**
- Generates comprehensive JSON templates for any SI schema
- Extracts attributes from existing components, schema definitions, or creates temporary components
- Includes metadata with required attribute analysis for AWS resources
- Uses clean quiet mode by default (shows progress spinner and file path)
- Supports verbose mode with `--verbose` flag for detailed analysis output
- Available as interactive menu option (option 6) in the main app

### Key Design Patterns

**Configuration-Driven**: Components are defined in JSON files in `component_configs/` directory, supporting arrays of components per file.

**Fallback Architecture**: The system uses SI SDK APIs with HTTP fallbacks when SDK operations fail, ensuring robustness.

**Caching Strategy**: Schema name resolution is cached to avoid repeated API calls during component listing operations.

**Error Resilience**: Comprehensive error handling with graceful degradation and informative user messages.

## Configuration File Formats

The system supports two configuration formats:

### Simple Format (Legacy)
```json
{
  "name": "component-name",
  "schema_name": "AWS EC2 Instance", 
  "attributes": {
    "InstanceType": "t3.micro",
    "ImageId": "ami-12345"
  },
  "domain": {
    "Name": "MyComponent",
    "Environment": "development"
  }
}
```

### Advanced Format (New UI)
Uses attribute paths and `$source` references for component linking:

```json
{
  "name": "my-aws-ec2-instance",
  "schema_name": "AWS::EC2::Instance",
  "attributes": {
    "/domain/Name": "my-aws-ec2-instance",
    "/domain/ImageId": "ami-0abcdef1234567890",
    "/domain/InstanceType": "t3.micro",
    "/secrets/AWS Credential": {
      "$source": {
        "component": "my-aws-credential",
        "path": "/secrets/AWS Credential"
      }
    },
    "/domain/SecurityGroups": [
      {
        "$source": {
          "component": "my-security-group",
          "path": "/domain/GroupId"
        }
      }
    ]
  }
}
```

### Advanced Template Structure
Templates can include extensive metadata for documentation and validation:

```json
{
  "_metadata": {
    "schema_name": "AWS::EC2::Instance",
    "schema_id": "01JK0QZHF0TXMJFVE1VK2175EC",
    "ui_format": "new",
    "required_attributes_analysis": {
      "required_attributes_found": [
        {
          "path": "/domain/ImageId",
          "reason": "An AMI ID is required to launch an instance",
          "value": "ami-0abcdef1234567890"
        }
      ]
    }
  },
  "templates": [
    { /* actual component configuration */ }
  ]
}
```

**Required fields**: `name`, `schema_name`
**Optional fields**: `attributes`, `domain`, `secrets`, `resource_id`, `view_name`, `connections`, `subscriptions`, `managed_by`

### Key Concepts

**Attribute Paths**: Use `/domain/`, `/secrets/`, etc. prefixes to specify attribute locations within component structure.

**Component Linking**: `$source` references allow dynamic linking between components, where one component's output becomes another's input.

**Metadata-Driven Templates**: Rich metadata enables validation, documentation, and requirement analysis for complex schemas.

## API Integration Notes

- Uses `system-initiative-api-client` package for SI API interactions
- SDK often requires `_without_preload_content` methods to bypass Pydantic validation issues
- Direct HTTP calls implemented as fallbacks for operations that fail with SDK
- Authentication handled via Bearer tokens in request headers

## File Organization

- `app.py`: Main application entry point
- `src/si_session.py`: API session management and authentication  
- `src/component_config_system.py`: Configuration loading and component creation logic
- `component_configs/`: Directory containing JSON configuration files (examples have `.example` extension)
- `setup.py`: Project initialization script
- `test_*.py`: Testing modules for different system components

## Development Notes

When adding new features:
- Follow the existing error handling patterns with graceful fallbacks
- Use the existing caching mechanisms for API data where appropriate
- Update both SDK and HTTP fallback implementations for API operations
- Test with various changeset states (open, closed, head)
- Consider bulk operations for efficiency when dealing with multiple components
- Support both simple and advanced configuration formats for backward compatibility
- Use attribute path notation (`/domain/`, `/secrets/`) for new configurations
- Implement `$source` references for component dependencies when needed