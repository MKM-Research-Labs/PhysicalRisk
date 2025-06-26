# Copyright (c) 2025 MKM Research Labs. All rights reserved.
# 
# This software is provided under license by MKM Research Labs. 
# Use, reproduction, distribution, or modification of this code is subject to the 
# terms and conditions of the license agreement provided with this software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Project paths utility module.

This module provides a utility class for managing project file paths,
handling path resolution, directory creation, and file operations
in a consistent way across different modules.
"""

import sys
from pathlib import Path

class ProjectPaths:
    """Simple project paths based on fixed hierarchy."""
    
    def __init__(self, src_file: str):
        """
        Initialize project paths.
        
        Logic: Any file in src/ structure -> project root is parent of 'src'
        """
        # Get absolute path of the calling file
        file_path = Path(src_file).resolve()
        
        # Walk up until we find 'src' directory
        current = file_path.parent
        found_src = False
        
        # Limit the search to prevent infinite loops
        max_levels = 10
        levels_up = 0
        
        while current.parent != current and levels_up < max_levels:
            if current.name == 'src':
                found_src = True
                break
            current = current.parent
            levels_up += 1
        
        # Project root is parent of 'src'
        if found_src:
            self.project_root = current.parent
        else:
            # Fallback: look for common project indicators
            current = file_path.parent
            while current.parent != current and levels_up < max_levels:
                # Look for project root indicators
                if any((current / indicator).exists() for indicator in 
                       ['setup.py', 'pyproject.toml', '.git', 'requirements.txt']):
                    self.project_root = current
                    break
                current = current.parent
                levels_up += 1
            else:
                # Last resort: assume standard depth
                self.project_root = file_path.parent.parent.parent
        
        print(f"DEBUG: ProjectPaths detected root as: {self.project_root}")
    
        # Fixed directory structure
        self.input_dir = self.project_root / 'input'
        self.results_dir = self.project_root / 'results'
        self.docs_dir = self.project_root / 'docs'
        self.src_dir = self.project_root / 'src'
        
        # Create directories
        self.input_dir.mkdir(exist_ok=True, parents=True)
        self.results_dir.mkdir(exist_ok=True, parents=True)
        self.docs_dir.mkdir(exist_ok=True, parents=True)
        
        # Auto-setup import paths when initialized
        self.setup_import_paths()
    
    def get_input_path(self, filename: str) -> Path:
        """Get path to file in input directory."""
        return self.input_dir / filename
    
    def get_results_path(self, filename: str) -> Path:
        """Get path to file in results directory."""
        return self.results_dir / filename
    
    def get_docs_path(self, filename: str) -> Path:
        """Get path to file in docs directory."""
        return self.docs_dir / filename
    
    def get_project_root(self) -> Path:
        """Get the project root directory."""
        return self.project_root
    
    def setup_import_paths(self):
        """Add necessary paths to sys.path for imports to work."""
        paths_to_add = [
            self.project_root,                           # Root for absolute imports
            self.src_dir,                               # src directory
            self.src_dir / "portfolio",                 # portfolio module
            self.src_dir / "cdm",                       # cdm module
            self.src_dir / "utilities",                 # utilities module
        ]
        
        # Add any additional subdirectories in src
        if self.src_dir.exists():
            for subdir in self.src_dir.iterdir():
                if subdir.is_dir() and not subdir.name.startswith('.'):
                    paths_to_add.append(subdir)
        
        for path in paths_to_add:
            if path.exists():
                path_str = str(path)
                if path_str not in sys.path:
                    sys.path.insert(0, path_str)
                    print(f"DEBUG: Added to sys.path: {path_str}")
    
    def __str__(self) -> str:
        return f"ProjectPaths(root={self.project_root})"

# Convenience function for quick setup
def setup_project_imports(calling_file: str = None):
    """
    Quick setup function to add project paths to sys.path.
    
    Args:
        calling_file: Usually __file__ from the calling module
    """
    if calling_file is None:
        # Try to get the caller's file
        import inspect
        frame = inspect.currentframe().f_back
        calling_file = frame.f_globals.get('__file__', '')
    
    paths = ProjectPaths(calling_file)
    return paths