# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
            subprocess.run(["start", "", file_path_str], shell=True, check=True)
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

