#!/usr/bin/env python3
"""
Migration script to help transition from v1.0 to v2.0 structure.

This script helps migrate existing configurations and provides
guidance for updating to the new architecture.
"""

import os
import shutil
import json
from pathlib import Path


def check_old_files():
    """Check for old configuration files that need migration."""
    old_files = {
        'website_profiles.json': 'config/website_profiles.json',
        'stress_test_config.json': 'config/stress_test_config.json'
    }
    
    found_files = []
    
    for old_file, new_location in old_files.items():
        if Path(old_file).exists() and not Path(new_location).exists():
            found_files.append((old_file, new_location))
    
    return found_files


def migrate_config_files():
    """Migrate configuration files to the new structure."""
    print("🔄 Checking for configuration files to migrate...")
    
    files_to_migrate = check_old_files()
    
    if not files_to_migrate:
        print("✅ No configuration files need migration")
        return True
    
    # Ensure config directory exists
    Path("config").mkdir(exist_ok=True)
    
    success = True
    for old_file, new_location in files_to_migrate:
        try:
            print(f"📁 Moving {old_file} → {new_location}")
            shutil.move(old_file, new_location)
        except Exception as e:
            print(f"❌ Error moving {old_file}: {e}")
            success = False
    
    return success


def validate_config_files():
    """Validate that configuration files are properly formatted."""
    print("\n🔍 Validating configuration files...")
    
    config_files = {
        'config/website_profiles.json': 'Website Profiles',
        'config/stress_test_config.json': 'Stress Test Configuration'
    }
    
    all_valid = True
    
    for config_file, description in config_files.items():
        if not Path(config_file).exists():
            print(f"⚠️ {description} file not found: {config_file}")
            continue
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if config_file.endswith('website_profiles.json'):
                if 'profiles' not in config:
                    print(f"❌ {description}: Missing 'profiles' key")
                    all_valid = False
                else:
                    print(f"✅ {description}: {len(config['profiles'])} profiles found")
            
            elif config_file.endswith('stress_test_config.json'):
                if 'test_configurations' not in config:
                    print(f"❌ {description}: Missing 'test_configurations' key")
                    all_valid = False
                else:
                    test_count = len(config['test_configurations'])
                    behavior_count = len(config.get('user_behavior', {}))
                    print(f"✅ {description}: {test_count} tests, {behavior_count} behaviors")
        
        except json.JSONDecodeError as e:
            print(f"❌ {description}: Invalid JSON - {e}")
            all_valid = False
        except Exception as e:
            print(f"❌ {description}: Error reading file - {e}")
            all_valid = False
    
    return all_valid


def test_new_entry_points():
    """Test that new entry points work correctly."""
    print("\n🧪 Testing new entry points...")
    
    entry_points = [
        ('locustfile_new.py', 'New Locust file'),
        ('stress_test_runner_new.py', 'New stress test runner'),
        ('generate_report_new.py', 'New report generator'),
        ('configure_user_behavior_new.py', 'New behavior configurator')
    ]
    
    all_working = True
    
    for entry_point, description in entry_points:
        if Path(entry_point).exists():
            try:
                # Basic import test
                import importlib.util
                spec = importlib.util.spec_from_file_location("test", entry_point)
                if spec and spec.loader:
                    print(f"✅ {description}: Import test passed")
                else:
                    print(f"❌ {description}: Import test failed")
                    all_working = False
            except Exception as e:
                print(f"❌ {description}: Error - {e}")
                all_working = False
        else:
            print(f"⚠️ {description}: File not found")
            all_working = False
    
    return all_working


def create_backup():
    """Create a backup of the current state."""
    print("\n💾 Creating backup...")
    
    timestamp = Path().resolve().name + "_backup"
    backup_dir = Path("../") / timestamp
    
    try:
        if backup_dir.exists():
            print(f"⚠️ Backup directory already exists: {backup_dir}")
            return False
        
        # Copy important files
        files_to_backup = [
            'locustfile.py',
            'stress_test_runner.py', 
            'generate_report.py',
            'configure_user_behavior.py'
        ]
        
        backup_dir.mkdir()
        
        for file_name in files_to_backup:
            if Path(file_name).exists():
                shutil.copy2(file_name, backup_dir / file_name)
        
        print(f"✅ Backup created: {backup_dir}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return False


def show_migration_summary():
    """Show a summary of the migration process and next steps."""
    print("\n" + "="*60)
    print("📋 MIGRATION SUMMARY")
    print("="*60)
    
    print("\n✅ Migration completed! Here's what to do next:")
    
    print("\n1. 🧪 Test the new entry points:")
    print("   python stress_test_runner_new.py")
    print("   python generate_report_new.py")
    print("   python configure_user_behavior_new.py")
    
    print("\n2. 🚀 Run a test with the new system:")
    print("   python stress_test_runner_new.py light_stress")
    
    print("\n3. 📊 Generate a report:")
    print("   python generate_report_new.py")
    
    print("\n4. 🎭 Configure user behavior:")
    print("   python configure_user_behavior_new.py show")
    
    print("\n5. 🌐 Try the web UI:")
    print("   python stress_test_runner_new.py web")
    
    print("\n📁 New project structure:")
    print("   src/           - Main source code")
    print("   config/        - Configuration files")
    print("   reports/       - Test reports")
    print("   scripts/       - Utility scripts")
    
    print("\n💡 Tips:")
    print("   - Old entry points still work for compatibility")
    print("   - Use *_new.py files for new features")
    print("   - Configuration files are now in config/ directory")
    print("   - Check README.md for detailed documentation")
    
    print("\n🎉 Welcome to MVHS Load Testing Framework v2.0!")


def main():
    """Main migration function."""
    print("🚀 MVHS Load Testing Framework v1.0 → v2.0 Migration")
    print("="*60)
    
    # Step 1: Create backup
    if not create_backup():
        print("⚠️ Warning: Could not create backup. Continuing anyway...")
    
    # Step 2: Migrate configuration files
    if not migrate_config_files():
        print("❌ Configuration migration failed!")
        return False
    
    # Step 3: Validate configurations
    if not validate_config_files():
        print("❌ Configuration validation failed!")
        return False
    
    # Step 4: Test new entry points
    if not test_new_entry_points():
        print("⚠️ Warning: Some entry points may have issues")
    
    # Step 5: Show summary
    show_migration_summary()
    
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Migration completed with errors. Please check the issues above.")
        exit(1)
    else:
        print("\n✅ Migration completed successfully!")
        exit(0)
