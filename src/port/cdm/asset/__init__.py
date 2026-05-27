# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
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
Asset CDM package — shared base for residential / commercial / industrial /
infrastructure assets.

Top-level modules hold the schema for every asset type. We deliberately keep
resilience / history / energy as single common files even when content
overlaps with asset-type specifics — duplication is tolerated until the
shape settles, then we refine.

    header.py      identifiers, valuation, location, common construction facts
    history.py     transaction history + hazard incident history
                   (flood, fire, wind, ground, environmental, HSE)
    energy.py      EPC, energy usage, building fabric (residential +
                   commercial; industrial process extensions included)
    loan.py        loan/mortgage CDM (LoanCDM class + MORTGAGE_SCHEMA dict)
    resilience.py  BRI resilience checklist, normalised hazard classes,
                   raw hazard exposure facts, industrial/safety/certifications,
                   insurance + governing-body ratings

Asset-type-specific extensions live in sub-packages and hold ONLY fields
that do not generalise. The sub-package boundary follows the MSCI sector
split, with industrial broken out from commercial because its risk profile
(COMAH, hazmat, process load, regulatory burden) diverges sharply:

    residential/    bedrooms, council tax band, gardens, residential
                    contents, etc.
    commercial/     office / retail / hotel / leisure / healthcare /
                    mixed-use — use class, NIA/NLA, lease economics,
                    accessibility/lift counts, plant room location,
                    service core, etc.
    industrial/     logistics / manufacturing / light industrial /
                    self-storage / data centre — eaves height,
                    floor loading, dock doors, craneage, process type,
                    shift pattern, etc.
    infrastructure/ (TBD)
"""
