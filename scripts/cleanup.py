#!/usr/bin/env python3
"""
Repository cleanup script for MVHS Load Test Framework
Removes unnecessary files and organizes the project structure.
"""

import os
import shutil
import glob
from pathlib import Path

def cleanup_repository():
    """Clean up the repository by removing temporary and unnecessary files."""
    
    print("🧹 Cleaning up MVHS Load Test Repository...")
    print("=" * 50)
    
    # Files and directories to remove
    cleanup_targets = [
        # Python cache files
        "__pycache__",
        "*.pyc",
        "*.pyo", 
        "*.pyd",
        ".Python",
        
        # IDE files
        ".idea",
        "*.swp",
        "*.swo",
        "*~",
        
        # OS files
        ".DS_Store",
        "Thumbs.db",
        "desktop.ini",
        
        # Temporary files
        "*.tmp",
        "*.temp",
        "*.log",
        
        # Old backup files
        "*.bak",
        "*.backup",
        "*.old",
        
        # Test artifacts (keep reports directory structure)
        "locust-*.log",
        "search_metrics_*.json",
        "request_metrics_*.json",
    ]
    
    removed_count = 0
    
    # Remove files matching patterns
    for pattern in cleanup_targets:
        if pattern.startswith("*"):
            # Handle glob patterns
            for file_path in glob.glob(pattern, recursive=True):
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"  ✅ Removed file: {file_path}")
                        removed_count += 1
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        print(f"  ✅ Removed directory: {file_path}")
                        removed_count += 1
                except Exception as e:
                    print(f"  ⚠️ Could not remove {file_path}: {e}")
        else:
            # Handle direct paths
            if os.path.exists(pattern):
                try:
                    if os.path.isfile(pattern):
                        os.remove(pattern)
                        print(f"  ✅ Removed file: {pattern}")
                        removed_count += 1
                    elif os.path.isdir(pattern):
                        shutil.rmtree(pattern)
                        print(f"  ✅ Removed directory: {pattern}")
                        removed_count += 1
                except Exception as e:
                    print(f"  ⚠️ Could not remove {pattern}: {e}")
    
    # Clean up __pycache__ directories recursively
    for root, dirs, files in os.walk("."):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                cache_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(cache_path)
                    print(f"  ✅ Removed cache: {cache_path}")
                    removed_count += 1
                except Exception as e:
                    print(f"  ⚠️ Could not remove {cache_path}: {e}")
    
    # Organize metrics files
    metrics_moved = organize_metrics_files()
    
    print(f"\n🎉 Cleanup Complete!")
    print(f"   📁 Removed {removed_count} files/directories")
    print(f"   📊 Organized {metrics_moved} metrics files")
    print(f"\n📁 Final Project Structure:")
    print_directory_tree()

def organize_metrics_files():
    """Move any stray metrics files to the proper location."""
    
    metrics_dir = Path("reports/metrics")
    metrics_dir.mkdir(parents=True, exist_ok=True)
    
    moved_count = 0
    
    # Patterns for metrics files
    metrics_patterns = [
        "search_metrics_*.json",
        "request_metrics_*.json", 
        "search_metrics_*.csv",
        "request_metrics_*.csv",
        "*_metrics_*.json",
        "*_metrics_*.csv"
    ]
    
    for pattern in metrics_patterns:
        for file_path in glob.glob(pattern):
            if not file_path.startswith("reports/"):
                try:
                    destination = metrics_dir / Path(file_path).name
                    shutil.move(file_path, destination)
                    print(f"  📊 Moved metrics: {file_path} → {destination}")
                    moved_count += 1
                except Exception as e:
                    print(f"  ⚠️ Could not move {file_path}: {e}")
    
    return moved_count

def print_directory_tree():
    """Print a clean directory tree of the project structure."""
    
    important_dirs = [
        "src/",
        "config/", 
        "reports/",
        "scripts/",
        "tests/",
        "docs/"
    ]
    
    important_files = [
        "run_stress_test.py",
        "start_web_ui.py", 
        "locustfile.py",
        "requirements.txt",
        "README.md"
    ]
    
    print("mvhs-load-test/")
    
    # Show directories
    for dir_path in important_dirs:
        if os.path.exists(dir_path):
            print(f"├── {dir_path}")
            
            # Show key files in src
            if dir_path == "src/":
                src_subdirs = ["config/", "core/", "users/", "tasks/", "reporting/", "runners/", "utils/"]
                for subdir in src_subdirs:
                    full_path = f"src/{subdir}"
                    if os.path.exists(full_path):
                        print(f"│   ├── {subdir}")
    
    # Show important files
    for file_path in important_files:
        if os.path.exists(file_path):
            print(f"├── {file_path}")
    
    print("└── ... (other files)")

if __name__ == "__main__":
    cleanup_repository()
