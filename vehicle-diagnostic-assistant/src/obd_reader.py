"""
OBD-II Data Reader Module
Connects to ELM327 adapter and reads vehicle diagnostic data
Supports mock data for testing without a real vehicle
"""

import obd
import random
from typing import Dict, List, Optional
import config


class OBDReader:
    """
    Handles connection to OBD-II adapter and data reading
    Supports both real vehicle connection and mock data for testing
    """
    
    def __init__(self, use_mock: bool = config.USE_MOCK_DATA):
        """
        Initialize OBD reader
        
        Args:
            use_mock: If True, use mock data instead of real connection
        """
        self.use_mock = use_mock
        self.connection = None
        
        if not use_mock:
            self.connect()
    
    def connect(self) -> bool:
        """
        Establish connection to OBD-II adapter
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            print("🔌 Connecting to OBD-II adapter...")
            
            # Attempt to connect to OBD adapter
            # If port is None, python-obd will auto-detect
            self.connection = obd.OBD(portstr=config.OBD_PORT, 
                                     baudrate=config.OBD_BAUDRATE)
            
            if self.connection.is_connected():
                print("✅ Successfully connected to vehicle!")
                print(f"📋 Protocol: {self.connection.protocol_name()}")
                return True
            else:
                print("❌ Failed to connect to vehicle")
                print("💡 Make sure:")
                print("   - ELM327 adapter is plugged in")
                print("   - Vehicle ignition is ON")
                print("   - Adapter drivers are installed")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def disconnect(self):
        """Close the OBD connection"""
        if self.connection:
            self.connection.close()
            print("🔌 Disconnected from vehicle")
    
    def read_vehicle_data(self) -> Dict:
        """
        Read current vehicle data from OBD-II
        
        Returns:
            Dict containing RPM, speed, coolant temp, and other data
        """
        if self.use_mock:
            return self._get_mock_data()
        
        data = {
            'rpm': None,
            'speed': None,
            'coolant_temp': None,
            'engine_load': None,
            'throttle_position': None,
            'status': 'connected'
        }
        
        try:
            # Read RPM (Revolutions Per Minute)
            rpm_response = self.connection.query(obd.commands.RPM)
            if not rpm_response.is_null():
                data['rpm'] = rpm_response.value.magnitude
            
            # Read Vehicle Speed
            speed_response = self.connection.query(obd.commands.SPEED)
            if not speed_response.is_null():
                data['speed'] = speed_response.value.magnitude
            
            # Read Coolant Temperature
            temp_response = self.connection.query(obd.commands.COOLANT_TEMP)
            if not temp_response.is_null():
                data['coolant_temp'] = temp_response.value.magnitude
            
            # Read Engine Load
            load_response = self.connection.query(obd.commands.ENGINE_LOAD)
            if not load_response.is_null():
                data['engine_load'] = load_response.value.magnitude
            
            # Read Throttle Position
            throttle_response = self.connection.query(obd.commands.THROTTLE_POS)
            if not throttle_response.is_null():
                data['throttle_position'] = throttle_response.value.magnitude
                
        except Exception as e:
            print(f"⚠️ Error reading data: {e}")
            data['status'] = 'error'
        
        return data
    
    def read_dtc_codes(self) -> List[tuple]:
        """
        Read Diagnostic Trouble Codes (DTCs) from the vehicle
        
        Returns:
            List of tuples: [(code, description), ...]
        """
        if self.use_mock:
            return self._get_mock_dtcs()
        
        try:
            # Query DTCs from vehicle
            dtc_response = self.connection.query(obd.commands.GET_DTC)
            
            if not dtc_response.is_null():
                return dtc_response.value
            else:
                return []
                
        except Exception as e:
            print(f"⚠️ Error reading DTCs: {e}")
            return []
    
    def _get_mock_data(self) -> Dict:
        """
        Generate realistic mock vehicle data for testing
        Simulates various driving scenarios
        """
        # Simulate different scenarios randomly
        scenarios = ['normal', 'high_temp', 'high_rpm', 'idle']
        scenario = random.choice(scenarios)
        
        if scenario == 'normal':
            data = {
                'rpm': random.randint(1500, 3000),
                'speed': random.randint(40, 80),
                'coolant_temp': random.randint(85, 95),
                'engine_load': random.randint(20, 50),
                'throttle_position': random.randint(15, 40),
                'status': 'mock'
            }
        elif scenario == 'high_temp':
            data = {
                'rpm': random.randint(2000, 3500),
                'speed': random.randint(60, 100),
                'coolant_temp': random.randint(105, 125),  # High!
                'engine_load': random.randint(50, 80),
                'throttle_position': random.randint(40, 70),
                'status': 'mock'
            }
        elif scenario == 'high_rpm':
            data = {
                'rpm': random.randint(4500, 6500),  # High RPM!
                'speed': random.randint(80, 120),
                'coolant_temp': random.randint(90, 100),
                'engine_load': random.randint(60, 90),
                'throttle_position': random.randint(60, 90),
                'status': 'mock'
            }
        else:  # idle
            data = {
                'rpm': random.randint(600, 900),
                'speed': 0,
                'coolant_temp': random.randint(80, 90),
                'engine_load': random.randint(10, 25),
                'throttle_position': random.randint(0, 10),
                'status': 'mock'
            }
        
        return data
    
    def _get_mock_dtcs(self) -> List[tuple]:
        """
        Generate mock DTCs for testing
        Randomly returns common diagnostic codes
        """
        # Common DTCs with descriptions
        all_dtcs = [
            ('P0301', 'Cylinder 1 Misfire Detected'),
            ('P0420', 'Catalyst System Efficiency Below Threshold'),
            ('P0171', 'System Too Lean (Bank 1)'),
            ('P0128', 'Coolant Thermostat Temperature Below Regulating Temperature'),
            ('P0442', 'Evaporative Emission System Leak Detected (Small Leak)'),
        ]
        
        # Randomly return 0-2 DTCs
        num_codes = random.choices([0, 1, 2], weights=[70, 20, 10])[0]
        
        if num_codes == 0:
            return []
        
        return random.sample(all_dtcs, num_codes)
    
    def print_data_formatted(self, data: Dict, dtcs: List[tuple]):
        """
        Print vehicle data in a clean, formatted way
        
        Args:
            data: Vehicle sensor data dictionary
            dtcs: List of diagnostic trouble codes
        """
        print("\n" + "="*50)
        print("🚗 VEHICLE DIAGNOSTIC DATA")
        print("="*50)
        
        # Status
        status_emoji = "🟢" if data['status'] == 'connected' else "🟡"
        print(f"\n{status_emoji} Status: {data['status'].upper()}")
        
        # Sensor Readings
        print("\n📊 SENSOR READINGS:")
        print(f"  🔄 RPM:                {data.get('rpm', 'N/A')} rpm")
        print(f"  🏎️  Speed:              {data.get('speed', 'N/A')} km/h")
        print(f"  🌡️  Coolant Temp:       {data.get('coolant_temp', 'N/A')} °C")
        print(f"  ⚙️  Engine Load:        {data.get('engine_load', 'N/A')} %")
        print(f"  🎚️  Throttle Position:  {data.get('throttle_position', 'N/A')} %")
        
        # Diagnostic Trouble Codes
        print("\n🔍 DIAGNOSTIC TROUBLE CODES:")
        if dtcs:
            for code, description in dtcs:
                print(f"  ⚠️  {code}: {description}")
        else:
            print("  ✅ No trouble codes detected")
        
        print("\n" + "="*50 + "\n")


def main():
    """
    Main function to demonstrate OBD-II reader functionality
    """
    print("🚀 Starting Vehicle Diagnostic System...")
    print(f"📍 Mode: {'MOCK DATA (Demo)' if config.USE_MOCK_DATA else 'REAL VEHICLE'}\n")
    
    # Initialize OBD reader
    reader = OBDReader(use_mock=config.USE_MOCK_DATA)
    
    try:
        # Read vehicle data
        print("📡 Reading vehicle data...")
        vehicle_data = reader.read_vehicle_data()
        
        # Read diagnostic codes
        print("🔍 Scanning for trouble codes...")
        dtc_codes = reader.read_dtc_codes()
        
        # Display results
        reader.print_data_formatted(vehicle_data, dtc_codes)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Always disconnect properly
        if not reader.use_mock:
            reader.disconnect()
    
    print("👋 Diagnostic system stopped")


if __name__ == "__main__":
    main()
