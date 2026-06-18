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

"""Construction section of the asset header schema."""

CONSTRUCTION = {
        "ConstructionType": {
            "type": "menu",
            "options": ["Brick and block", "Timber frame", "Stone", "Modern methods", "Mixed construction"],
            "description": "Primary construction material/method"
        },
        "FoundationType": {
            "type": "menu",
            "options": ["Strip foundations", "Raft foundations", "Pile foundations", "Deep foundations", "Unknown"],
            "description": "Type of foundation system"
        },
        "FloorLevelMeters": {
            "type": "decimal",
            "description": "Height of ground floor above ground level in metres"
        },
        "BRIAdjustedFloorLevelMeters": {
            "type": "decimal",
            "description": (
                "Effective flood-threshold floor level (m) = FloorLevelMeters "
                "plus a Building Resilience Index credit derived from the BRI "
                "flood sub-score. A highly resilient (AA) building floods only "
                "once water rises well above its nominal floor. Used by the PRS "
                "flood event filter; falls back to FloorLevelMeters + a credit "
                "computed from BRIFloodScore when absent."
            )
        },
        "BasementPresent": {
            "type": "boolean",
            "description": "Indicates presence of basement"
        },
        "FloorType": {
            "type": "menu",
            "options": [
                "Suspended timber", "Solid concrete", "Suspended concrete",
                "Beam and block", "Mixed",
            ],
            "description": "Ground floor construction type"
        },
        "StiltsHeight": {
            "type": "decimal",
            "description": "Height of any stilts/pillars supporting property"
        },
        "PropertyHeight": {
            "type": "decimal",
            "description": "Total height of property in metres"
        },
        "RoofDetails": {
            "RoofCover": {
                "type": "menu",
                "options": ["Slate", "Clay tile", "Concrete tile", "Metal", "Felt", "Thatch", "Green roof", "Other"],
                "description": "Primary roof covering material"
            },
            "RoofGeometry": {
                "type": "menu",
                "options": ["Flat", "Gabled", "Hip", "Mansard", "Complex", "Barrel vault"],
                "description": "Roof shape / geometry"
            },
            "RoofPitch": {
                "type": "menu",
                "options": ["Flat (<5°)", "Low (5-20°)", "Medium (20-35°)", "Steep (>35°)"],
                "description": "Roof pitch category"
            },
            "RoofFrame": {
                "type": "menu",
                "options": ["Timber truss", "Timber rafter", "Steel", "Concrete", "Unknown"],
                "description": "Roof structural frame type"
            },
            "RoofDeck": {
                "type": "menu",
                "options": ["Plywood", "OSB", "Metal deck", "Concrete", "Sarking board", "Unknown"],
                "description": "Roof deck/substrate material"
            },
            "RoofYearReplaced": {
                "type": "integer",
                "description": "Year roof was last replaced (may differ from build year)"
            },
        },
        "SoftStory": {
            "type": "boolean",
            "description": "Ground floor structurally weaker than storeys above (OED SoftStory)"
        },
        "ShapeIrregularity": {
            "type": "menu",
            "options": ["None", "Plan", "Vertical", "Both"],
            "description": "Structural shape irregularity type (OED ShapeIrregularity)"
        },
        "BrickVeneer": {
            "type": "boolean",
            "description": "Non-structural masonry cladding over frame"
        },
        "GlassType": {
            "type": "menu",
            "options": ["Standard", "Laminated", "Tempered", "Impact resistant", "Unknown"],
            "description": "Structural glazing type (wind/impact resistance)"
        },
        "RetrofitYear": {
            "type": "integer",
            "description": "Year of last structural retrofit or seismic strengthening"
        },
        "HasCrippleWall": {
            "type": "boolean",
            "description": "Short wood-framed wall between foundation and first floor"
        },
}
