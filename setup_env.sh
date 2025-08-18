#!/bin/bash

# System Initiative Environment Setup Script
# This script helps you set up environment variables for the SI Python SDK

echo "System Initiative Environment Setup"
echo "=================================="
echo ""

# Function to read input with default value
read_with_default() {
    local prompt="$1"
    local default="$2"
    local result
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " result
        result="${result:-$default}"
    else
        read -p "$prompt: " result
    fi
    
    echo "$result"
}

# Check if .env file exists
ENV_FILE=".env"
if [ -f "$ENV_FILE" ]; then
    echo "Found existing .env file. Loading current values..."
    source "$ENV_FILE"
    echo ""
fi

# Get current values or defaults
current_host="${SI_HOST:-https://api.systeminit.com}"
current_workspace="${SI_WORKSPACE_ID:-}"
current_token="${SI_API_TOKEN:-}"

echo "Please provide your System Initiative configuration:"
echo ""

# Read configuration values
new_host=$(read_with_default "SI Host URL" "$current_host")
new_workspace=$(read_with_default "Workspace ID" "$current_workspace")
new_token=$(read_with_default "API Token (optional)" "$current_token")

# Validate required fields
if [ -z "$new_workspace" ]; then
    echo ""
    echo "❌ Error: Workspace ID is required!"
    echo "You can find your workspace ID in the System Initiative web interface."
    exit 1
fi

# Create/update .env file
echo "# System Initiative Configuration" > "$ENV_FILE"
echo "# Generated on $(date)" >> "$ENV_FILE"
echo "" >> "$ENV_FILE"
echo "export SI_HOST=\"$new_host\"" >> "$ENV_FILE"
echo "export SI_WORKSPACE_ID=\"$new_workspace\"" >> "$ENV_FILE"

if [ -n "$new_token" ]; then
    echo "export SI_API_TOKEN=\"$new_token\"" >> "$ENV_FILE"
else
    echo "# export SI_API_TOKEN=\"your-token-here\"" >> "$ENV_FILE"
fi

echo ""
echo "✅ Configuration saved to $ENV_FILE"
echo ""
echo "To use these environment variables, run:"
echo "  source $ENV_FILE"
echo ""
echo "Or to export them for your current shell session:"
echo "  export SI_HOST=\"$new_host\""
echo "  export SI_WORKSPACE_ID=\"$new_workspace\""
if [ -n "$new_token" ]; then
    echo "  export SI_API_TOKEN=\"$new_token\""
fi
echo ""
echo "You can then test your configuration by running:"
echo "  python example_with_env.py"