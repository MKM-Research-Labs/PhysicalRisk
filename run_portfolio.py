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

#!/usr/bin/env python3
"""
Simplified Portfolio Generator - Integration Test Version

This module provides a streamlined orchestration for generating portfolio files
in the correct sequence with integration testing.
"""

import sys
import json
import traceback
from pathlib import Path
from typing import Dict, Optional, Union
from datetime import datetime

# Setup project root and paths
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add portfolio generators to path
sys.path.insert(0, str(project_root / 'src' / 'portfolio'))

class SimplifiedPortfolioGenerator:
    """
    Simplified Portfolio Generator with integration testing.
    """
    
    def __init__(self, output_dir: Optional[Union[str, Path]] = None, timestamped: bool = True):
        """
        Initialize the Portfolio Generator.
        
        Args:
            output_dir: Base directory to save generated files (default: project_root/input)
            timestamped: Create timestamped subdirectory for each run (default: True)
        """
        # Set up base output directory
        if output_dir:
            base_dir = Path(output_dir)
        else:
            base_dir = project_root / 'input'
            
        # Create timestamped subdirectory if requested
        if timestamped:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir = base_dir / f"portfolio_run_{timestamp}"
        else:
            self.output_dir = base_dir
            
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Output directory: {self.output_dir}")
        
        # Initialize generators (will be set in run_integration_test)
        self.generators_available = {}

    def run_integration_test(self) -> Dict[str, bool]:
        """
        Test that all required modules can be imported and initialized.
        
        Returns:
            Dict mapping module names to import success status
        """
        print("🔍 RUNNING INTEGRATION TEST")
        print("=" * 50)
        
        test_results = {}
        
        # Test 1: Property Portfolio Generator
        try:
            from property_portfolio import PropertyPortfolioGenerator
            self.property_generator = PropertyPortfolioGenerator(self.output_dir)
            test_results['PropertyPortfolioGenerator'] = True
            print("✅ PropertyPortfolioGenerator - Import & Init Success")
        except Exception as e:
            test_results['PropertyPortfolioGenerator'] = False
            print(f"❌ PropertyPortfolioGenerator - Failed: {e}")
        
        # Test 2: Flood Gauge Portfolio Generator
        try:
            from flood_gauge_portfolio import FloodGaugePortfolioGenerator
            self.flood_gauge_generator = FloodGaugePortfolioGenerator(self.output_dir)
            test_results['FloodGaugePortfolioGenerator'] = True
            print("✅ FloodGaugePortfolioGenerator - Import & Init Success")
        except Exception as e:
            test_results['FloodGaugePortfolioGenerator'] = False
            print(f"❌ FloodGaugePortfolioGenerator - Failed: {e}")
        
        # Test 3: Mortgage Portfolio Generator
        try:
            from mortgage_portfolio import MortgagePortfolioGenerator
            self.mortgage_generator = MortgagePortfolioGenerator(self.output_dir)
            test_results['MortgagePortfolioGenerator'] = True
            print("✅ MortgagePortfolioGenerator - Import & Init Success")
        except Exception as e:
            test_results['MortgagePortfolioGenerator'] = False
            print(f"❌ MortgagePortfolioGenerator - Failed: {e}")
        
        # Test 4: TC Event TS Portfolio Generator
        try:
            from tc_event_ts_portfolio import TCEventTSPortfolioGenerator
            self.tc_event_generator = TCEventTSPortfolioGenerator(self.output_dir)
            test_results['TCEventTSPortfolioGenerator'] = True
            print("✅ TCEventTSPortfolioGenerator - Import & Init Success")
        except Exception as e:
            test_results['TCEventTSPortfolioGenerator'] = False
            print(f"❌ TCEventTSPortfolioGenerator - Failed: {e}")
        
        # Test 5: Flood Gauge Time Series Function
        try:
            from flood_gauge_ts import generate_gauge_floodts_json
            self.generate_gauge_floodts_json = generate_gauge_floodts_json
            test_results['generate_gauge_floodts_json'] = True
            print("✅ generate_gauge_floodts_json - Import Success")
        except Exception as e:
            test_results['generate_gauge_floodts_json'] = False
            print(f"❌ generate_gauge_floodts_json - Failed: {e}")
        
        # Summary
        total_tests = len(test_results)
        passed_tests = sum(test_results.values())
        
        print(f"\n📊 INTEGRATION TEST RESULTS")
        print("-" * 30)
        print(f"Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 All integration tests passed!")
            return test_results
        else:
            print("⚠️  Some integration tests failed. Check module paths and dependencies.")
            return test_results

    def generate_portfolio(self, 
                          count_properties: int = 200, 
                          count_gauges: int = 40, 
                          count_mortgages: int = 200,
                          count_tc_events: int = 2) -> Dict[str, Path]:
        """
        Generate portfolio files in the correct sequence.
        
        Args:
            count_properties: Number of properties to generate
            count_gauges: Number of flood gauges to generate  
            count_mortgages: Number of mortgages to generate
            count_tc_events: Number of TC events to generate
            
        Returns:
            Dictionary of generated file paths
        """
        print("\n🚀 STARTING PORTFOLIO GENERATION")
        print("=" * 50)
        print(f"Generating: {count_properties} properties, {count_gauges} gauges, " +
              f"{count_mortgages} mortgages, {count_tc_events} TC events")
        
        output_paths = {}
        
        try:
            # Step 1: Generate Properties (base dependency)
            print("\n1️⃣ Generating Properties...")
            if hasattr(self, 'property_generator'):
                properties = self.property_generator.generate(count_properties)
                output_paths['properties'] = properties['file_path']
                print(f"✅ Generated {count_properties} properties")
            else:
                print("❌ Property generator not available")
                return output_paths
            
            # Step 2: Generate Flood Gauges (independent)
            print("\n2️⃣ Generating Flood Gauges...")
            if hasattr(self, 'flood_gauge_generator'):
                flood_gauges = self.flood_gauge_generator.generate(count_gauges)
                output_paths['flood_gauges'] = flood_gauges['file_path']
                print(f"✅ Generated {count_gauges} flood gauges")
            else:
                print("❌ Flood gauge generator not available")
            
            # Step 3: Generate Mortgages (depends on properties)
            print("\n3️⃣ Generating Mortgages...")
            if hasattr(self, 'mortgage_generator'):
                mortgages = self.mortgage_generator.generate_from_properties()
                output_paths['mortgages'] = mortgages['file_path']
                print(f"✅ Generated mortgages from properties")
            else:
                print("❌ Mortgage generator not available")
            
            # Step 4: Generate TC Events (independent)
            print("\n4️⃣ Generating TC Events...")
            if hasattr(self, 'tc_event_generator'):
                tc_events = self.tc_event_generator.generate(count_tc_events)
                output_paths['tc_events'] = tc_events['file_path']
                print(f"✅ Generated {count_tc_events} TC events")
            else:
                print("❌ TC event generator not available")
            
            # Step 5: Generate Flood Gauge Time Series (depends on flood gauges)
            print("\n5️⃣ Generating Flood Gauge Time Series...")
            if hasattr(self, 'generate_gauge_floodts_json') and 'flood_gauges' in output_paths:
                gauge_ts_file = self.output_dir / "gauge_floodts.json"
                
                # Call the time series generation function
                self.generate_gauge_floodts_json(
                    output_file=str(gauge_ts_file),
                    input_portfolio_file=str(output_paths['flood_gauges']),
                    cdm_validation=True,
                    simulation_params={
                        "simulation_hours": 24,
                        "time_step": 2,
                        "flood_wave_speed": 1.5
                    }
                )
                output_paths['gauge_time_series'] = gauge_ts_file
                print(f"✅ Generated flood gauge time series")
            else:
                print("❌ Flood gauge time series generation not available")
            
            # Generate summary report
            self._generate_summary_report(output_paths)
            
            # Copy files to root/input directory
            self._copy_to_root_input(output_paths)
            
            print(f"\n🎉 PORTFOLIO GENERATION COMPLETE!")
            print(f"📁 Files saved to: {self.output_dir}")
            print(f"📁 Files copied to: {project_root / 'input'}")
            
            return output_paths
            
        except Exception as e:
            print(f"\n❌ ERROR DURING PORTFOLIO GENERATION")
            print(f"Error: {str(e)}")
            traceback.print_exc()
            raise

    def _generate_summary_report(self, output_paths: Dict[str, Path]):
        """Generate a summary report of the portfolio generation."""
        summary = {
            "generation_timestamp": datetime.now().isoformat(),
            "output_directory": str(self.output_dir),
            "generated_files": {k: str(v) for k, v in output_paths.items()},
            "file_sizes": {},
            "record_counts": {}
        }
        
        # Get file sizes and record counts
        for name, path in output_paths.items():
            if path.exists():
                summary["file_sizes"][name] = path.stat().st_size
                
                # Try to get record counts from JSON files
                if path.suffix == '.json':
                    try:
                        with open(path, 'r') as f:
                            data = json.load(f)
                            if isinstance(data, dict):
                                # Look for common array keys
                                for key in ['properties', 'mortgages', 'flood_gauges', 'tc_events', 'time_series']:
                                    if key in data and isinstance(data[key], list):
                                        summary["record_counts"][f"{name}_{key}"] = len(data[key])
                    except Exception:
                        pass  # Skip if can't read JSON
        
        # Save summary report
        summary_file = self.output_dir / "portfolio_generation_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"📊 Summary report saved: {summary_file}")

    def _copy_to_root_input(self, output_paths: Dict[str, Path]):
        """
        Copy generated portfolio files to root/input directory.
        This allows other modules to find the files in the expected location.
        """
        import shutil
        
        root_input_dir = project_root / 'input'
        root_input_dir.mkdir(exist_ok=True)
        
        print(f"\n📋 Copying files to root/input directory...")
        
        # Files to copy
        files_to_copy = [
            'property_portfolio.json',
            'mortgage_portfolio.json', 
            'flood_gauge_portfolio.json',
            'tc_events.json',
            'single_tceventts.json',
            'gauge_floodts.json',
            'portfolio_generation_summary.json'
        ]
        
        copied_count = 0
        
        for filename in files_to_copy:
            source_file = self.output_dir / filename
            dest_file = root_input_dir / filename
            
            if source_file.exists():
                try:
                    shutil.copy2(source_file, dest_file)
                    print(f"  ✅ Copied {filename}")
                    copied_count += 1
                except Exception as e:
                    print(f"  ❌ Failed to copy {filename}: {e}")
            else:
                print(f"  ⚠️  {filename} not found in output directory")
        
        print(f"📁 Copied {copied_count} files to: {root_input_dir}")
        print(f"📁 Timestamped backup preserved at: {self.output_dir}")
        
        # Also copy any additional files from output_paths
        for name, path in output_paths.items():
            if path.exists() and path.parent == self.output_dir:
                dest_file = root_input_dir / path.name
                if not dest_file.exists():  # Don't overwrite if already copied
                    try:
                        shutil.copy2(path, dest_file)
                        print(f"  ✅ Copied {path.name} (from output_paths)")
                    except Exception as e:
                        print(f"  ❌ Failed to copy {path.name}: {e}")


def main():
    """Main execution function."""
    print("🌊 SIMPLIFIED PORTFOLIO GENERATOR WITH INTEGRATION TESTING")
    print(f"Timestamp: {datetime.now()}")
    print("=" * 80)
    
    # Initialize generator
    generator = SimplifiedPortfolioGenerator(timestamped=True)
    
    # Run integration test first
    test_results = generator.run_integration_test()
    
    # Only proceed if most tests pass
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    if passed_tests >= total_tests * 0.8:  # At least 80% pass rate
        print(f"\n✅ Integration tests sufficient ({passed_tests}/{total_tests}). Proceeding with generation...")
        
        # Generate portfolio with small test counts
        try:
            result = generator.generate_portfolio(
                count_properties=200,
                count_gauges=40, 
                count_mortgages=200,
                count_tc_events=2
            )
            
            print(f"\n🎉 SUCCESS! Portfolio generated successfully.")
            print(f"📁 Timestamped location: {generator.output_dir}")
            print(f"📁 Main location: {Path(__file__).resolve().parent / 'input'}")
            print(f"📄 Generated files:")
            for name, path in result.items():
                print(f"   • {name}: {path.name}")
                
        except Exception as e:
            print(f"\n❌ Portfolio generation failed: {e}")
            return 1
            
    else:
        print(f"\n❌ Too many integration test failures ({passed_tests}/{total_tests}). Please fix module imports first.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)