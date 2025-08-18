"""
Enhanced System Initiative API Client with Component Creation
"""

import sys
import os
import argparse

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from src.si_session import SISession
from src.component_config_system import ComponentConfigManager
from src.changeset_extractor import extract_changeset_components
from src.component_generator import generate_component_config
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main application - List components in workspace"""
    
    print("System Initiative Component Manager (Enhanced Version)")
    print("=" * 55)
    
    try:
        # Check environment variables status
        print("\n1. Checking environment variables:")
        SISession.check_env_vars()
        
        # Create session from environment variables
        print("\n2. Creating SI session:")
        session = SISession.from_env()
        
        # Get available change sets
        print(f"\n3. Getting available change sets:")
        change_sets = session.get_change_sets()
        
        if not change_sets:
            print("❌ No change sets found!")
            print("\n🔍 Possible issues:")
            print("   - Authentication failed (check your API token)")
            print("   - No changesets exist in this workspace")
            print("   - Workspace ID is incorrect")
            return 1
        
        # Use the first available change set (or you could prompt user to choose)
        change_set = change_sets[0]
        change_set_id = change_set["id"]
        change_set_name = change_set["name"]
        
        print(f"✅ Using change set: '{change_set_name}' (ID: {change_set_id})")
        
        # List all components in the workspace
        print(f"\n4. Listing components in changeset:")
        print("-" * 50)
        
        components = session.get_components(change_set_id)
        if components:
            print(f"Found {len(components)} components:")
            for i, comp in enumerate(components, 1):
                print(f"  {i}. {comp['display_name']} ({comp['schema_name']})")
        else:
            print("🔭 No components found in this changeset.")
        
        # Component summary
        if components:
            print(f"\n📊 Component Summary:")
            print(f"   Total components: {len(components)}")
            
            # Group by schema type
            schema_counts = {}
            for component in components:
                schema = component.get('schema_name', 'Unknown')
                schema_counts[schema] = schema_counts.get(schema, 0) + 1
            
            print(f"   Schema distribution:")
            for schema, count in sorted(schema_counts.items()):
                print(f"     - {schema}: {count} component(s)")
        else:
            # Show available schemas if no components
            print(f"\n5. Available schemas for creating components:")
            print("-" * 50)
            schemas = session.get_schemas(change_set_id)
            
            if schemas:
                print(f"\n💡 You can create components using these {len(schemas)} available schemas.")
                for i, schema in enumerate(schemas[:10], 1):  # Show first 10
                    schema_name = schema.get('name', f'Schema {i}')
                    print(f"  {i}. {schema_name}")
                if len(schemas) > 10:
                    print(f"  ... and {len(schemas) - 10} more")
            else:
                print("❌ No schemas available. Check your workspace configuration.")
        
        print(f"\n✅ Application completed successfully!")
        return 0
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print(f"\n🔧 To fix this, set your environment variables:")
        print(f"   export SI_WORKSPACE_ID='your-workspace-id'")
        print(f"   export SI_API_TOKEN='your-api-token'")
        print(f"   export SI_HOST='https://your-host.com'    # optional")
        return 1
        
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def component_creation_mode_with_changeset(session: SISession, change_set_id: str):
    """Component creation mode using configuration files with a pre-selected changeset"""
    
    print(f"\n🔧 Component Creation Mode")
    print("=" * 30)
    
    try:
        from src.component_config_system import ComponentConfigManager
        config_manager = ComponentConfigManager()
        
        # Initialize sample configs if none exist
        if not config_manager.list_configs():
            print("No component configurations found. Creating sample configurations...")
            config_manager.create_sample_configs()
        
        while True:
            print(f"\n🔧 Component Creation Options:")
            print(f"  1. List available component configurations")
            print(f"  2. Create component from configuration")
            print(f"  3. Bulk create multiple components")
            print(f"  4. Create new configuration template")
            print(f"  5. Validate configurations")
            print(f"  6. Back to main menu")
            
            choice = input(f"\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                print(f"\n📋 Available Component Configurations:")
                print("-" * 40)
                configs = config_manager.list_configs()
                if configs:
                    for i, config in enumerate(configs, 1):
                        print(f"  {i}. {config.name}")
                        print(f"     Schema: {config.schema_name}")
                        if config.attributes:
                            attr_count = len(config.attributes)
                            print(f"     Attributes: {attr_count} configured")
                        print()
                else:
                    print("No configurations found.")
            
            elif choice == "2":
                config_name = input("Enter configuration name to create: ").strip()
                if config_name:
                    print(f"\n🚀 Creating component from config '{config_name}'...")
                    component_id = config_manager.create_component_from_config(
                        session, change_set_id, config_name
                    )
                    if component_id:
                        print(f"✅ Component created successfully with ID: {component_id}")
                    else:
                        print("❌ Failed to create component")
                else:
                    print("❌ Please enter a configuration name.")
            
            elif choice == "3":
                configs = config_manager.list_configs()
                if configs:
                    print(f"\nAvailable configurations:")
                    for i, config in enumerate(configs, 1):
                        print(f"  {i}. {config.name}")
                    
                    selections = input("\nEnter configuration numbers (comma-separated) or 'all': ").strip()
                    
                    if selections.lower() == 'all':
                        config_names = [config.name for config in configs]
                    else:
                        try:
                            indices = [int(x.strip()) - 1 for x in selections.split(',')]
                            config_names = [configs[i].name for i in indices if 0 <= i < len(configs)]
                        except (ValueError, IndexError):
                            print("❌ Invalid selection.")
                            continue
                    
                    if config_names:
                        print(f"\n🚀 Creating {len(config_names)} components...")
                        results = config_manager.bulk_create_components(session, change_set_id, config_names)
                        
                        success_count = sum(1 for result in results.values() if result is not None)
                        print(f"\n📊 Creation Summary:")
                        print(f"   Successfully created: {success_count}/{len(config_names)} components")
                else:
                    print("No configurations available.")
            
            elif choice == "4":
                schema_name = input("Enter schema name for template: ").strip()
                if schema_name:
                    output_file = f"component_configs/component_templates/{schema_name.lower().replace(' ', '_')}_template.json"
                    from src.component_config_system import create_config_template
                    create_config_template(schema_name, output_file)
                    print(f"✅ Template created: {output_file}")
                else:
                    print("❌ Please enter a schema name.")
            
            elif choice == "5":
                print(f"\n🔍 Validating all configurations:")
                print("-" * 35)
                configs = config_manager.list_configs()
                valid_count = 0
                for config in configs:
                    if config_manager.validate_config(config.name):
                        valid_count += 1
                print(f"\n📊 Validation Summary: {valid_count}/{len(configs)} configurations are valid")
            
            elif choice == "6":
                print("👋 Returning to main menu!")
                break
            
            else:
                print("❌ Invalid choice. Please enter 1-6.")
                
    except Exception as e:
        print(f"❌ Component creation mode error: {e}")
        import traceback
        traceback.print_exc()


def component_creation_mode():
    """Standalone component creation mode (requires changeset selection first)"""
    
    print(f"\n🔧 Component Creation Mode")
    print("=" * 30)
    
    try:
        from src.component_config_system import ComponentConfigManager
        session = SISession.from_env()
        
        # First, let user select or create a changeset
        change_set_id = select_or_create_changeset(session)
        if not change_set_id:
            print("❌ No changeset selected. Component creation requires a changeset.")
            return
        
        # Now use the changeset-aware creation mode
        component_creation_mode_with_changeset(session, change_set_id)
        
    except Exception as e:
        print(f"❌ Component creation mode error: {e}")
        import traceback
        traceback.print_exc()


def schema_fetcher_mode(session: SISession, change_set_id: str):
    """Schema template fetcher mode with clean output"""
    
    print(f"\n📋 Schema Template Fetcher")
    print("=" * 30)
    
    try:
        from src.schema_fetcher import fetch_schema_template
        
        while True:
            print(f"\n📋 Schema Template Options:")
            print(f"  1. Fetch schema template")
            print(f"  2. List available schemas")
            print(f"  3. Back to main menu")
            
            choice = input(f"\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                schema_name = input("Enter schema name (e.g., 'AWS::EC2::Instance'): ").strip()
                if schema_name:
                    print(f"\n🚀 Fetching schema template for '{schema_name}'...")
                    success = fetch_schema_template(schema_name, change_set_id)  # Uses default quiet=True
                    if not success:
                        print("❌ Failed to fetch schema template")
                else:
                    print("❌ Please enter a schema name.")
            
            elif choice == "2":
                print(f"\n📚 Available Schemas:")
                print("-" * 25)
                schemas = session.get_schemas(change_set_id)
                if schemas:
                    print(f"Found {len(schemas)} schemas:")
                    for i, schema in enumerate(schemas, 1):
                        schema_name = schema.get('name', f'Schema {i}')
                        print(f"  {i}. {schema_name}")
                else:
                    print("🔭 No schemas found.")
            
            elif choice == "3":
                print("👋 Returning to main menu!")
                break
            
            else:
                print("❌ Invalid choice. Please enter 1-3.")
                
    except Exception as e:
        print(f"❌ Schema fetcher mode error: {e}")
        import traceback
        traceback.print_exc()


def changeset_extractor_mode(session: SISession, change_set_id: str):
    """Changeset component extractor mode"""
    
    print(f"\n📦 Changeset Component Extractor")
    print("=" * 35)
    
    try:
        while True:
            print(f"\n📦 Component Extraction Options:")
            print(f"  1. Extract all components from current changeset")
            print(f"  2. Extract components to custom directory")
            print(f"  3. View extraction history")
            print(f"  4. Back to main menu")
            
            choice = input(f"\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                print(f"\n🚀 Extracting all components from changeset...")
                result = extract_changeset_components(change_set_id)
                
                if result["success"] and result["successful_extractions"] > 0:
                    print(f"✅ Successfully extracted {result['successful_extractions']} components")
                    print(f"📁 Files saved to: {result['output_directory']}")
                elif result["success"]:
                    print(f"⚠️  No components found to extract")
                else:
                    print(f"❌ Extraction failed: {result.get('error', 'Unknown error')}")
                    
            elif choice == "2":
                custom_dir = input("Enter custom output directory (or press Enter for default): ").strip()
                if not custom_dir:
                    custom_dir = "component_configs/current_components"
                
                print(f"\n🚀 Extracting components to: {custom_dir}")
                result = extract_changeset_components(change_set_id, custom_dir)
                
                if result["success"] and result["successful_extractions"] > 0:
                    print(f"✅ Successfully extracted {result['successful_extractions']} components")
                    print(f"📁 Files saved to: {result['output_directory']}")
                elif result["success"]:
                    print(f"⚠️  No components found to extract")
                else:
                    print(f"❌ Extraction failed: {result.get('error', 'Unknown error')}")
                    
            elif choice == "3":
                print(f"\n📋 Extraction History:")
                print("-" * 25)
                
                # Look for summary files
                import glob
                import json
                summary_files = glob.glob("component_configs/current_components/extraction_summary_*.json")
                
                if summary_files:
                    for summary_file in sorted(summary_files, reverse=True):
                        try:
                            with open(summary_file, 'r') as f:
                                summary = json.load(f)
                            
                            print(f"  📄 {os.path.basename(summary_file)}")
                            print(f"     Changeset: {summary.get('changeset_id', 'unknown')[:16]}...")
                            print(f"     Extracted: {summary.get('successful_extractions', 0)} components")
                            print(f"     Date: {summary.get('extracted_at', 'unknown')}")
                            print()
                            
                        except Exception as e:
                            print(f"  ❌ Error reading {os.path.basename(summary_file)}: {e}")
                else:
                    print("🔭 No extraction history found")
                    
            elif choice == "4":
                print("👋 Returning to main menu!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-4.")
                
    except Exception as e:
        print(f"❌ Changeset extractor mode error: {e}")
        import traceback
        traceback.print_exc()


def component_generator_mode(session: SISession, change_set_id: str):
    """Component generator mode"""
    
    print(f"\n🏗️  Component Generator")
    print("=" * 25)
    
    try:
        while True:
            print(f"\n🏗️  Component Generation Options:")
            print(f"  1. Generate component config with real references")
            print(f"  2. List available component references")
            print(f"  3. Batch generate multiple configs")
            print(f"  4. Back to main menu")
            
            choice = input(f"\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                schema_name = input("Enter schema name (e.g., 'AWS::EC2::Instance'): ").strip()
                if not schema_name:
                    print("❌ Please enter a schema name.")
                    continue
                
                component_name = input("Enter component name (e.g., 'my-ec2-instance'): ").strip()
                if not component_name:
                    print("❌ Please enter a component name.")
                    continue
                
                print(f"\n🚀 Generating component config...")
                result = generate_component_config(
                    schema_name=schema_name,
                    component_name=component_name,
                    change_set_id=change_set_id
                )
                
                if result["success"]:
                    print(f"✅ Successfully generated component config:")
                    print(f"   📁 File: {result['filename']}")
                    print(f"   🔗 Real references: {result['real_references_used']}")
                    print(f"   📊 Total attributes: {result['attributes_count']}")
                else:
                    print(f"❌ Generation failed: {result.get('error', 'Unknown error')}")
                    
            elif choice == "2":
                print(f"\n🔍 Available Component References:")
                print("-" * 35)
                
                from src.component_generator import ComponentGenerator
                generator = ComponentGenerator(session)
                component_refs = generator._load_current_component_references()
                
                print(f"  AWS Credentials: {len(component_refs['aws_credentials'])}")
                for cred in component_refs['aws_credentials']:
                    print(f"    • {cred['name']}")
                
                print(f"  Regions: {len(component_refs['regions'])}")
                for region in component_refs['regions']:
                    print(f"    • {region['name']}")
                
                print(f"  VPCs: {len(component_refs['vpcs'])}")
                for vpc in component_refs['vpcs']:
                    print(f"    • {vpc['name']}")
                
                print(f"  Subnets: {len(component_refs['subnets'])}")
                for subnet in component_refs['subnets']:
                    print(f"    • {subnet['name']}")
                
                print(f"  Security Groups: {len(component_refs['security_groups'])}")
                for sg in component_refs['security_groups']:
                    print(f"    • {sg['name']}")
                
                print(f"  Other Components: {len(component_refs['other'])}")
                for comp in component_refs['other']:
                    print(f"    • {comp['name']} ({comp['schema_name']})")
                    
            elif choice == "3":
                print(f"\n📋 Batch Component Generation")
                print("-" * 30)
                
                schemas_input = input("Enter schema names (comma-separated): ").strip()
                if not schemas_input:
                    print("❌ Please enter schema names.")
                    continue
                
                schemas = [s.strip() for s in schemas_input.split(',')]
                base_name = input("Enter base component name (will be suffixed): ").strip()
                if not base_name:
                    print("❌ Please enter a base component name.")
                    continue
                
                print(f"\n🚀 Generating {len(schemas)} component configs...")
                success_count = 0
                
                for i, schema in enumerate(schemas, 1):
                    component_name = f"{base_name}-{schema.split('::')[-1].lower()}"
                    print(f"  {i}/{len(schemas)} Generating: {component_name} ({schema})")
                    
                    result = generate_component_config(
                        schema_name=schema,
                        component_name=component_name,
                        change_set_id=change_set_id,
                        quiet=True
                    )
                    
                    if result["success"]:
                        success_count += 1
                        print(f"    ✅ {result['filename']}")
                    else:
                        print(f"    ❌ Failed: {result.get('error', 'Unknown error')}")
                
                print(f"\n📊 Batch Generation Summary:")
                print(f"   Successfully generated: {success_count}/{len(schemas)} configs")
                    
            elif choice == "4":
                print("👋 Returning to main menu!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-4.")
                
    except Exception as e:
        print(f"❌ Component generator mode error: {e}")
        import traceback
        traceback.print_exc()


def interactive_mode():
    """Enhanced interactive mode with component creation"""
    
    print(f"\n🎛️ Interactive System Initiative Explorer")
    print("=" * 45)
    
    try:
        session = SISession.from_env()
        
        # First, let user select or create a changeset
        change_set_id = select_or_create_changeset(session)
        if not change_set_id:
            print("❌ No changeset selected. Exiting interactive mode.")
            return
        
        while True:
            print(f"\n🎛️ Main Menu Options:")
            print(f"  1. List all components")
            print(f"  2. List components by schema filter")
            print(f"  3. Show available schemas")
            print(f"  4. Search component by name")
            print(f"  5. 🔧 Create components from configurations")
            print(f"  6. 📋 Generate schema templates")
            print(f"  7. 📦 Extract changeset components to JSON files")
            print(f"  8. 🏗️  Generate component config with real references")
            print(f"  9. Switch changeset")
            print(f"  10. Exit")
            
            choice = input(f"\nEnter your choice (1-10): ").strip()
            
            if choice == "1":
                print(f"\n📋 All Components:")
                print("-" * 30)
                components = session.get_components(change_set_id)
                if components:
                    print(f"Found {len(components)} components:")
                    for i, comp in enumerate(components, 1):
                        print(f"  {i}. {comp['display_name']} ({comp['schema_name']})")
                        print(f"     ID: {comp['id']}")
                else:
                    print("🔭 No components found in this changeset.")
                
            elif choice == "2":
                schema_filter = input("Enter schema name (or part of it): ").strip()
                if schema_filter:
                    print(f"\n🔍 Components matching '{schema_filter}':")
                    print("-" * 50)
                    components = session.get_components(change_set_id)
                    if components:
                        filtered = [c for c in components if schema_filter.lower() in c.get('schema_name', '').lower()]
                        if filtered:
                            print(f"Found {len(filtered)} matching components:")
                            for i, comp in enumerate(filtered, 1):
                                print(f"  {i}. {comp['display_name']} ({comp['schema_name']})")
                                print(f"     ID: {comp['id']}")
                        else:
                            print(f"No components match '{schema_filter}'")
                    else:
                        print("🔭 No components found in this changeset.")
                else:
                    print("❌ Please enter a schema filter.")
                
            elif choice == "3":
                print(f"\n📚 Available Schemas:")
                print("-" * 25)
                schemas = session.get_schemas(change_set_id)
                if schemas:
                    print(f"Found {len(schemas)} schemas:")
                    for i, schema in enumerate(schemas, 1):
                        schema_name = schema.get('name', f'Schema {i}')
                        print(f"  {i}. {schema_name}")
                else:
                    print("🔭 No schemas found.")
                
            elif choice == "4":
                component_name = input("Enter component name: ").strip()
                if component_name:
                    print(f"\n🔍 Searching for '{component_name}':")
                    print("-" * 40)
                    components = session.get_components(change_set_id)
                    if components:
                        matches = [c for c in components if component_name.lower() in c.get('display_name', '').lower()]
                        if matches:
                            print(f"Found {len(matches)} matching components:")
                            for i, comp in enumerate(matches, 1):
                                print(f"  {i}. {comp['display_name']} ({comp['schema_name']})")
                                print(f"     ID: {comp['id']}")
                        else:
                            print(f"No components match '{component_name}'")
                    else:
                        print("🔭 No components found in this changeset.")
                else:
                    print("❌ Please enter a component name.")
                
            elif choice == "5":
                component_creation_mode_with_changeset(session, change_set_id)
                
            elif choice == "6":
                schema_fetcher_mode(session, change_set_id)
                
            elif choice == "7":
                changeset_extractor_mode(session, change_set_id)
                
            elif choice == "8":
                component_generator_mode(session, change_set_id)
                
            elif choice == "9":
                change_set_id = select_or_create_changeset(session)
                if not change_set_id:
                    print("❌ No changeset selected.")
                
            elif choice == "10":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-10.")
                
    except Exception as e:
        print(f"❌ Interactive mode error: {e}")
        import traceback
        traceback.print_exc()


def select_or_create_changeset(session: SISession) -> Optional[str]:
    """
    Let user select an existing changeset or create a new one.
    
    Args:
        session: SISession instance
        
    Returns:
        str: Selected changeset ID, or None if cancelled
    """
    print(f"\n📂 Changeset Selection")
    print("=" * 25)
    
    # Get existing changesets
    change_sets = session.get_change_sets()
    
    if change_sets:
        print(f"\n📋 Available Changesets:")
        for i, cs in enumerate(change_sets, 1):
            status_indicator = "🟢" if cs['status'].lower() == 'open' else "🔵"
            head_indicator = " 📌" if cs.get('is_head') else ""
            print(f"  {i}. {status_indicator} {cs['name']} ({cs['status']}){head_indicator}")
        
        print(f"  {len(change_sets) + 1}. ➕ Create new changeset")
        print(f"  0. ❌ Cancel")
        
        while True:
            try:
                choice = input(f"\nSelect changeset (0-{len(change_sets) + 1}): ").strip()
                
                if choice == "0":
                    return None
                    
                elif choice == str(len(change_sets) + 1):
                    # Create new changeset
                    return create_new_changeset(session)
                    
                else:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(change_sets):
                        selected_cs = change_sets[choice_num - 1]
                        print(f"✅ Selected: {selected_cs['name']}")
                        return selected_cs['id']
                    else:
                        print(f"❌ Please enter a number between 0 and {len(change_sets) + 1}")
                        
            except ValueError:
                print("❌ Please enter a valid number.")
                
    else:
        print("🔭 No existing changesets found.")
        create_choice = input("Would you like to create a new changeset? (y/N): ").strip().lower()
        
        if create_choice in ['y', 'yes']:
            return create_new_changeset(session)
        else:
            return None


def create_new_changeset(session: SISession) -> Optional[str]:
    """
    Create a new changeset with user input.
    
    Args:
        session: SISession instance
        
    Returns:
        str: New changeset ID, or None if failed/cancelled
    """
    print(f"\n➕ Create New Changeset")
    print("-" * 25)
    
    while True:
        name = input("Enter changeset name (or 'cancel' to abort): ").strip()
        
        if name.lower() == 'cancel':
            return None
            
        if not name:
            print("❌ Changeset name cannot be empty.")
            continue
            
        print(f"Creating changeset '{name}'...")
        changeset_id = session.create_change_set(name)
        
        if changeset_id:
            print(f"✅ Successfully created changeset: {name}")
            return changeset_id
        else:
            retry = input("❌ Failed to create changeset. Try again? (y/N): ").strip().lower()
            if retry not in ['y', 'yes']:
                return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="System Initiative Component Manager (Enhanced)")
    parser.add_argument(
        "--interactive", "-i", 
        action="store_true", 
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--create-components", "-c",
        action="store_true",
        help="Run in component creation mode"
    )
    
    args = parser.parse_args()
    
    if args.create_components:
        component_creation_mode()
    elif args.interactive:
        interactive_mode()
    else:
        result = main()
        exit(result)