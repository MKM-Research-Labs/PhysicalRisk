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

"""
Industrial asset extensions to the asset CDM.

Holds ONLY industrial-specific schema. Resilience, history and energy are
shared with residential / commercial / infrastructure and live at the
asset/ level — they are NOT duplicated here. Industrial-specific resilience
/ history / energy fields (COMAH status, HSE incidents, industrial process
load, hazardous zones, etc.) are absorbed into the shared asset/* modules.

Reference taxonomy (MSCI Industrial subsector + UK Use Class B2/B8):

    IndustrialType (menu):
        Logistics / Distribution warehouse  (Use Class B8)
        Manufacturing / Heavy industrial    (Use Class B2)
        Light industrial                    (Use Class E sub-class —
                                             office/research/light assembly)
        Self-storage
        Data centre                         (sui generis)

Candidate modules to create here from Commercial_Property_CDM_v1.xlsx
(the industrial fields that were over-bundled under 'commercial' in v1):

    header.py    Industrial-specific physical attributes:
                 IndustrialType (see menu above),
                 EavesHeightMeters, ClearInternalHeightMeters,
                 FloorLoadingKNm2, YardDepthMeters, DockDoorCount,
                 LevelAccessDoorCount, CraneageInstalled, CraneCapacityT,
                 PowerCapacityKVA, SprinklerHazardClass,
                 LoadingBays (from v1), TotalUnits (from v1),
                 PlantRoomLocation, ServiceCore

    operations.py  Operational profile (lives here because it drives
                   process / regulatory risk, not financial reporting):
                   ProcessType, ShiftPattern (1/2/3-shift / continuous),
                   ProductsHandled, FeedstockHazardClass,
                   ProductHazardClass

    cdm.py       IndustrialAssetCDM — composes asset.* + industrial.*
                 schemas, exposes the same validate / create_mapping /
                 get_required_fields surface as ResidentialAssetCDM today.

Industrial-specific fields that ALREADY live in shared asset/* modules
(do not duplicate them here):

    asset/resilience.py
        RiskAssessment      IndustrialProcessRisk, ChemicalStorage,
                            OperatingHours, FireLoadRating
        IndustrialFeatures  HazardousZones, StorageTankCount,
                            StorageCapacity, WasteTreatment,
                            EffluentTreatment, HeavyMachineryZones
        SafetyCompliance    COMAHStatus, SafetyDistance,
                            EmergencyResponseTime, AssemblyPoints,
                            EvacuationTime
        Certifications      HSECertification, EnvironmentalPermit,
                            AirQualityPermit, WastePermit
        ResilienceMeasures  FireSuppressionType (industrial typically
                            foam / gas / sprinkler at a higher hazard
                            class than retail/office)

    asset/energy.py
        IndustrialFabric    IndustrialProcessLoad, ProcessCooling,
                            CompressedAir

    asset/history.py
        HazardHistory       HSEIncidents (count), LastHSEIncidentDate
"""
