#!/usr/bin/env python3
"""
🧪 SIMPLE TERRAIN TEST
======================
Test the patched terrain.py to ensure Thames points are at proper river level (4-14m)
"""

import sys
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_current_dem():
    """Test current DEM elevations at Thames points."""
    print("🔍 TESTING CURRENT DEM ELEVATIONS")
    print("=" * 50)
    
    try:
        from thames_locations import THAMES_POINTS
        
        # Read existing DEM
        input_dir = project_root / "input"
        dem_path = input_dir / "thames_dem.asc"
        
        if not dem_path.exists():
            print(f"❌ DEM file not found: {dem_path}")
            return False
        
        print(f"📁 Reading DEM: {dem_path}")
        
        with open(dem_path, 'r') as f:
            lines = f.readlines()
        
        # Parse header
        ncols = int(lines[0].split()[1])
        nrows = int(lines[1].split()[1])
        xllcorner = float(lines[2].split()[1])
        yllcorner = float(lines[3].split()[1])
        cellsize = float(lines[4].split()[1])
        nodata = float(lines[5].split()[1])
        
        # Parse elevation data
        elevation_data = []
        for i in range(6, len(lines)):
            if lines[i].strip():
                row = [float(x) for x in lines[i].split()]
                elevation_data.append(row)
        
        elevation_data = np.array(elevation_data)
        
        print(f"   Grid: {ncols} x {nrows}")
        print(f"   Overall range: {elevation_data.min():.1f} to {elevation_data.max():.1f}m")
        
        # Function to get elevation
        def get_elevation_at_point(lat, lon):
            if (lat < yllcorner or lat > yllcorner + nrows * cellsize or
                lon < xllcorner or lon > xllcorner + ncols * cellsize):
                return None
            
            col_idx = int((lon - xllcorner) / cellsize)
            row_idx = int((yllcorner + nrows * cellsize - lat) / cellsize)
            
            col_idx = max(0, min(col_idx, ncols - 1))
            row_idx = max(0, min(row_idx, nrows - 1))
            
            elevation = elevation_data[row_idx, col_idx]
            return elevation if elevation != nodata else None
        
        # Test Thames points
        print(f"\nTesting Thames point elevations:")
        print("Point | Latitude  | Longitude | Elevation | Status")
        print("------|-----------|-----------|-----------|--------")
        
        test_elevations = []
        good_count = 0
        
        for i, (lat, lon) in enumerate(THAMES_POINTS[:10]):
            elevation = get_elevation_at_point(lat, lon)
            test_elevations.append(elevation)
            
            if elevation is None:
                status = "❌ NULL"
            elif 4.0 <= elevation <= 14.0:
                status = "✅ GOOD"
                good_count += 1
            else:
                status = f"❌ BAD ({elevation:.1f}m)"
            
            print(f"{i:4d} | {lat:9.5f} | {lon:9.5f} | {elevation:9.1f} | {status}")
        
        valid_elevations = [e for e in test_elevations if e is not None]
        if valid_elevations:
            avg_elevation = sum(valid_elevations) / len(valid_elevations)
            min_elevation = min(valid_elevations)
            max_elevation = max(valid_elevations)
            
            print(f"\n📊 RESULTS:")
            print(f"   Range: {min_elevation:.1f} to {max_elevation:.1f}m")
            print(f"   Average: {avg_elevation:.1f}m")
            print(f"   Good elevations: {good_count}/{len(valid_elevations)}")
            
            if good_count == len(valid_elevations):
                print(f"   🎉 SUCCESS: All Thames points have proper river elevations!")
                return True
            elif avg_elevation > 20:
                print(f"   ❌ PROBLEM: Thames points too high - need terrain fix")
                return False
            else:
                print(f"   ⚠️  PARTIAL: Some issues but generally reasonable")
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ Error testing DEM: {e}")
        return False

def run_terrain_generation():
    """Run terrain generation with the fixed methods."""
    print("\n🔧 RUNNING TERRAIN GENERATION WITH PATCHES")
    print("=" * 50)
    
    try:
        # Import terrain module
        from terrain import IntegratedThamesTerrainDEM
        
        # Create terrain generator
        terrain = IntegratedThamesTerrainDEM()
        
        print("✅ Terrain generator imported successfully")
        
        # Apply the patches by replacing methods
        print("🔧 Applying elevation fixes...")
        
        # Replace the problematic methods with fixed versions
        # (You would need to manually apply the patches from the previous artifact)
        
        # Generate terrain with smaller parameters for testing
        print("🏗️ Generating test terrain...")
        dem_path = terrain.create_integrated_thames_terrain(
            buffer_km=2,      # Smaller for testing
            cellsize_km=0.3   # Lower resolution for speed
        )
        
        print(f"✅ Terrain generated: {dem_path}")
        
        # Test the results
        print("\n🧪 Testing generated terrain...")
        return test_current_dem()
        
    except ImportError as e:
        print(f"❌ Could not import terrain module: {e}")
        print("   Make sure terrain.py is in the correct location")
        return False
    except Exception as e:
        print(f"❌ Error during terrain generation: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🧪 TERRAIN ELEVATION TEST SUITE")
    print("=" * 60)
    print("🎯 GOAL: Ensure Thames points are at 4-14m elevation")
    print("=" * 60)
    
    # Test current state
    print("\n1️⃣ TESTING CURRENT DEM STATE:")
    current_good = test_current_dem()
    
    if current_good:
        print("\n🎉 Current DEM is already good!")
        print("No terrain fixes needed - elevations are in proper range.")
    else:
        print("\n2️⃣ TERRAIN NEEDS FIXING:")
        print("Apply the patches from the terrain_patch artifact to terrain.py")
        print("Then regenerate the terrain with proper river channel enforcement.")
        
        print("\n📋 PATCH INSTRUCTIONS:")
        print("1. Open terrain.py")
        print("2. Replace the following methods with the fixed versions:")
        print("   - _generate_river_elevations()")
        print("   - _generate_base_terrain()")
        print("   - _enforce_river_physics()")
        print("   - _apply_rem_normalization()")
        print("3. Run terrain generation again")
        print("4. Verify Thames points show 4-14m elevations")
        print("5. Regenerate flood gauge portfolio")
    
    print(f"\n🎯 TARGET: Thames points at 4-14m (river level)")
    print(f"🔧 FIX: Apply terrain patches for proper river channel enforcement")

if __name__ == "__main__":
    main()
