#!/usr/bin/env python3
"""
Build script for the Rust extension module.

This can be run manually to build the Rust extension:
    python rust_ext/build.py

Or run from the rust_ext directory:
    cd rust_ext
    python build.py
"""

import subprocess
import sys
from pathlib import Path

def build_rust_extension():
    """Build the Rust extension using cargo."""
    # Handle both being run from project root or from rust_ext directory
    script_path = Path(__file__).resolve()
    rust_dir = script_path.parent
    
    print("Building Rust extension for tristrip...")
    print(f"Working directory: {rust_dir}")
    
    try:
        # Build in release mode for performance
        result = subprocess.run(
            ["cargo", "build", "--release"],
            cwd=rust_dir,
            check=True,
            capture_output=True,
            text=True
        )
        
        print("✓ Rust extension built successfully!")
        print(f"  Library location: {rust_dir / 'target' / 'release'}")
        
        # Rename .dll to .pyd on Windows for Python compatibility
        release_dir = rust_dir / "target" / "release"
        dll_file = release_dir / "tristrip_rust.dll"
        pyd_file = release_dir / "tristrip_rust.pyd"
        
        if dll_file.exists() and not pyd_file.exists():
            import shutil
            shutil.copy2(dll_file, pyd_file)
            print(f"  → Created {pyd_file.name} from {dll_file.name}")
        
        # Show where the compiled library is
        found_libs = []
        for ext in ['.pyd', '.so', '.dll', '.dylib']:
            for lib in release_dir.glob(f"*tristrip_rust*{ext}"):
                found_libs.append(lib)
                print(f"  → {lib.name}")
        
        if not found_libs:
            print("  Warning: No compiled library found. Check cargo output.")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print("✗ Failed to build Rust extension", file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        if e.stdout:
            print(e.stdout, file=sys.stderr)
        return False
    except FileNotFoundError:
        print("✗ Cargo not found. Please install Rust from https://rustup.rs/", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = build_rust_extension()
    sys.exit(0 if success else 1)
