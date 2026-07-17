# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
open_pdf_file
"""

import logging
import platform
import subprocess
import webbrowser
from pathlib import Path

logger = logging.getLogger(__name__)


def open_pdf_file(file_path: Path) -> bool:
    """
    Open a PDF file using the system's default PDF viewer.

    Args:
        file_path: Path to the PDF file

    Returns:
        True if successful, False otherwise
    """
    try:
        system = platform.system().lower()
        file_path_str = str(file_path.absolute())

        if system == "darwin":  # macOS
            subprocess.run(["open", file_path_str], check=True)
        elif system == "windows":  # Windows
            subprocess.run(["cmd", "/c", "start", "", file_path_str], check=True)
        elif system == "linux":  # Linux
            subprocess.run(["xdg-open", file_path_str], check=True)
        else:
            # Fallback: try using webbrowser module
            webbrowser.open(f"file://{file_path_str}")

        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"System command failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to open PDF: {e}")
        return False

