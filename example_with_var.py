#!/usr/bin/env python3
"""
Example of using SISession with environment variables
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from src.si_session import SISession


def main():
    print("System Initiative Session - Environment Variables Example")
    print("=" * 60)
    
    # Check what environment variables are currently set
    print("\n1. Checking environment variables:")
    SISession.check_env_vars()
    
    # Example 1: Create session using environment variables
    print("\n2. Creating session from environment variables:")
    try:
        session = SISession.from_env()
        print(f"✓ Session created successfully!")
        
    except ValueError as e:
        print(f"✗ Failed to create session: {e}")
        print("\nTo fix this, set your environment variables:")
        print("  export SI_WORKSPACE_ID='your-workspace-id'")
        print("  export SI_API_TOKEN='your-api-token'      # optional")
        print("  export SI_HOST='https://your-host.com'    # optional")
        return 1
    
    # Example 2: Override specific values while using env vars for others
    print("\n3. Creating session with mixed configuration:")
    try:
        mixed_session = SISession(
            si_host="https://dev.systeminit.com",  # Override host
            # workspace_id will come from env var
            # api_token will come from env var
        )
        print(f"✓ Mixed session created: {mixed_session}")
        
    except ValueError as e:
        print(f"✗ Failed to create mixed session: {e}")
    
    # Example 3: Create session with explicit values (no env vars)
    print("\n4. Creating session with explicit values:")
    explicit_session = SISession(
        si_host="https://localhost:3000",
        workspace_id="explicit-workspace-id",
        api_token="explicit-token",
        verify_ssl=False
    )
    print(f"✓ Explicit session created: {explicit_session}")
    
    return 0


def setup_example_env():
    """
    Example of how to set up environment variables programmatically
    (for testing purposes - normally you'd set these in your shell)
    """
    print("\n" + "="*50)
    print("EXAMPLE: Setting up environment variables")
    print("="*50)
    
    # Set example environment variables
    os.environ['SI_WORKSPACE_ID'] = 'example-workspace-123'
    os.environ['SI_API_TOKEN'] = 'example-token-abcdef123456'
    os.environ['SI_HOST'] = 'https://demo.systeminit.com'
    
    print("Set example environment variables:")
    SISession.check_env_vars()
    
    # Now create a session using these env vars
    print("\nCreating session with example env vars:")
    session = SISession.from_env()
    
    return session


if __name__ == "__main__":
    # Run the main example
    result = main()
    
    # If the main example failed (probably due to missing env vars),
    # show the programmatic setup example
    if result != 0:
        print("\n" + "🔧 Running setup example with mock environment variables:")
        try:
            example_session = setup_example_env()
            print(f"\n✓ Example session working: {example_session}")
            result = 0
        except Exception as e:
            print(f"✗ Example setup failed: {e}")
    
    exit(result)