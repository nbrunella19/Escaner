"""
Test script for MI6010D bridge measurement
Measures a 1 Ohm resistor with basic configuration
"""

import sys
import time
from pathlib import Path

# Add Instrumental to path BEFORE importing
sys.path.insert(0, str(Path(__file__).parent.parent))

from Instrumental.MI6010D import MI6010D

def Flush_buffer(puente):
    print("Vaciando buffer...")
    puente.timeout = 500
    while True:
        try:
            msg = puente.read()
            print("  >>", msg)
        except:
            break
    puente.timeout = 20000  



def test_mi6010d():
    """
    Basic test for MI6010D bridge measurement
    
    Configuration:
    - Rs (Series Resistance): 1 Ohm
    - Rx (Unknown Resistance): 1 Ohm
    - Reversal delay time: 8 seconds
    - Current (Ix): 0.1 A (10 mA)
    - Number of measurements: 10
    - Number of statistics: 5
    """
    
    # Create instance of MI6010D
    bridge = MI6010D()
   
    # Configuration parameters
    GPIB_ADDRESS = 15  # Adjust this to your device address
    RS = 1.0           # 1 ohm
    RX = 1.0           # 1 ohm
    TIME = 8           # 8 seconds
    IX = 1             # mA
    NUM_MEASUREMENTS = 10
    NUM_STATISTICS = 5
    
    print("=" * 60)
    print("MI6010D Bridge Measurement Test")
    print("=" * 60)
    
    # Configure the bridge
    print("\n[1] Configuring device...")
    bridge.is_present = True
    bridge.gpib_address = GPIB_ADDRESS
    bridge.serial_number = "TEST-001"
    
    print(f"    GPIB Address : {bridge.gpib_address}")
    print(f"    Serial Number: {bridge.serial_number}")
    
    # Connect to devices
    print("\n[2] Connecting to device...")
    try:

        bridge.connect()
        print("    ✓ Connected successfully")
    except Exception as e:
        print(f"    ✗ Connection failed: {e}")
        return False
    
    try:
        bridge.send_stdby()
        # Clear any previous state
        print("\n[3] Clearing device state...")
        bridge.reset()
        time.sleep(0.2)
        print("    ✓ Device cleared")
        
        bridge.send_remote()
        time.sleep(0.5)
        bridge.send_stdby()        # manda ‘S’ otra vez para salir de standby
        time.sleep(0.5)
        
        # Set series resistance (Rs) - BEFORE Query
        print(f"\n[4] Setting series resistance (Rs) = {RS} Ω...")
        bridge.send_rs(RS)
        time.sleep(0.5)
        print("    ✓ Rs set")
        
        # Set unknown resistance (Rx) - BEFORE Query
        print(f"\n[5] Setting unknown resistance (Rx) = {RX} Ω...")
        bridge.send_rx(RX)
        time.sleep(0.5)
        print("    ✓ Rx set")
        
        # Set current (Ix) - BEFORE Query
        print(f"\n[6] Setting current (Ix) = {IX} A ({IX} mA)...")
        bridge.send_ix(IX)
        time.sleep(0.5)
        print("    ✓ Current set")
        
        # Set reversal rate (time for measurement cycle) - BEFORE Query
        print(f"\n[7] Setting reversal rate (time = {TIME}s)...")
        bridge.send_reversal_rate(TIME)
        time.sleep(0.5)
        print("    ✓ Reversal rate set")
        
        # Set number of measurements - BEFORE Query
        print(f"\n[8] Setting number of measurements = {NUM_MEASUREMENTS}...")
        bridge.send_measurements(NUM_MEASUREMENTS)
        time.sleep(0.5)
        print("    ✓ Measurements count set")
              
        # Set number of statistics - BEFORE Query
        print(f"\n[9] Setting number of statistics = {NUM_STATISTICS}...")
        bridge.send_statistics(NUM_STATISTICS)
        time.sleep(0.5)
        print("    ✓ Statistics count set")
        
                
        print("\n[10] Configuration complete. Device is measuring.")
        print("=" * 60)
        print(f"Waiting for {NUM_MEASUREMENTS} measurements...")
        print("(D=description, #=number, &=value, E=error)")
        print("=" * 60 + "\n")
        
        # Read data as it arrives from the device
        measurements = []
        
        start_read_time = time.time()
        data_count = 0
        pass_count = 0
        
        while data_count < NUM_MEASUREMENTS:
            try:
                # Read data from device (blocking, will wait for data)
                raw_data = bridge.get_data()              
                print(f"    → Pasada: {pass_count}\n")             
                if raw_data:
                    raw_data = raw_data.strip()  # Clean whitespace
                    print(f"[{data_count}] Received: {raw_data} (measurements: {len(measurements)+1}/{NUM_MEASUREMENTS})")
                    
                    # Parse data based on first character
                    if raw_data.startswith("&"):
                        # Ratio/Resistance value
                        try:
                            value = float(raw_data[1:])
                            measurements.append(value)
                            print(f"    → Rx value: {value:.10f}\n")
                        except ValueError:
                            print(f"    ✗ Could not parse value\n")
                    elif raw_data.startswith("D"):
                        # Measurement description
                        print(f"    → Description: {raw_data[1:]}\n")
                    elif raw_data.startswith("#"):
                        # Measurement number
                        print(f"    → Measurement #: {raw_data[1:]}\n")
                        data_count += 1
                    elif raw_data.startswith("E"):
                        # Error message (11-25)
                        print(f"    ✗ Device error: {raw_data}\n")
                        break
                    else:
                        # Unknown format
                        print(f"    → Other: {raw_data}\n")
                
            except Exception as e:
                # Timeout is expected when measurement ends - just break silently
                error_str = str(e)
                if "TMO" in error_str or "Timeout" in error_str or "VI_ERROR" in error_str:
                    # Normal end of data transmission
                    break
                else:
                    # Other unexpected error
                    print(f"Unexpected error: {error_str}")
                # Continue waiting - don't break on timeout
                time.sleep(0.1)
            pass_count += 1
        
        elapsed_read = time.time() - start_read_time
        print("=" * 60)
        
        # Calculate statistics
        if measurements:
            rx_avg = sum(measurements) / len(measurements)
            print(f"\n✓ Measurement completed in {elapsed_read:.1f} seconds")
            print(f"✓ Measurements received: {len(measurements)}/{NUM_MEASUREMENTS}")
            print(f"✓ Rx average value: {rx_avg:.10f} Ω")
            
            # Show all measurements
            print("\nAll measurements:")
            for i, val in enumerate(measurements, 1):
                print(f"  [{i:2d}] {val:.10f} Ω")
        else:
            rx_avg = 0.0
            print(f"\n✗ No measurements received")
        
        # Print measurement summary
        print("\n" + "=" * 60)
        print("Measurement Summary:")
        print("=" * 60)
        print(f"Series Resistance (Rs):        {RS} Ω")
        print(f"Unknown Resistance (Rx):       {rx_avg:.10f} Ω (avg)")
        print(f"Current (Ix):                  {IX} mA ({IX} mA)")
        print(f"Reversal rate (per cycle):     {TIME} s")
        print(f"Number of measurements:        {len(measurements)}/{NUM_MEASUREMENTS}")
        print(f"Number of statistics:          {NUM_STATISTICS}")
        print(f"Total time elapsed:            {elapsed_read:.1f} s")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error during measurement: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Disconnect
        print("\nDisconnecting...")
        try:
            bridge.send_stop()
            time.sleep(0.5)
            bridge.disconnect()
            print("✓ Disconnected")
        except Exception as e:
            print(f"✗ Error disconnecting: {e}")


if __name__ == "__main__":
    success = test_mi6010d()
    if success:
        print("\n✓ Test completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Test failed!")
        sys.exit(1)
