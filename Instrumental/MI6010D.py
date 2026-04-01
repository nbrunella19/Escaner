"""
MI6010D - Control class for MI 6010D Bridge through GPIB/VISA

This module provides a Python class for controlling the MI 6010D bridge
measurement instrument via GPIB communication using PyVISA.

Original VB Author: Andrew Giffin (2001-02-12)
Python Translation Date: 2026-02-24
"""

import pyvisa
import time
from typing import Optional


class MI6010D:
    """
    Class for controlling the MI 6010D DC Bridge via GPIB.
    
    This class handles communication with the 6010D bridge instrument,
    including connection management, command sending, and data retrieval.
    """
    
    def __init__(self):
        """Initialize the MI6010D control object."""
        self._is_present = False
        self._gpib_address = 15  # Default Address
        self._gpib_error = 0  # 0: no error, 1: write error, 2: read error
        self._serial_number = ""
        self._uncertainty_ppm = 0.0
        self._unc_degrees_of_freedom = 0  # 0 is for infinite
        self._calibration_values = [""] * 24  # Array for calibration values
        self._instrument = None  # PyVISA resource object
        self._resource_manager = None
        self.read_termination  = "\n"
        self.write_termination = "\n"
        
    # Properties
    @property
    def is_present(self) -> bool:
        """Get whether the device is present."""
        return self._is_present
    
    @is_present.setter
    def is_present(self, value: bool):
        """Set whether the device is present."""
        self._is_present = value
    
    @property
    def gpib_address(self) -> int:
        """Get the GPIB address of the device."""
        return self._gpib_address
    
    @gpib_address.setter
    def gpib_address(self, value: int):
        """Set the GPIB address (must be 0-30)."""
        if 0 <= value < 31:
            self._gpib_address = value
    
    @property
    def serial_number(self) -> str:
        """Get the serial number of the device."""
        return self._serial_number
    
    @serial_number.setter
    def serial_number(self, value: str):
        """Set the serial number of the device."""
        self._serial_number = value
    
    @property
    def uncertainty_ppm(self) -> float:
        """Get the uncertainty in PPM."""
        return self._uncertainty_ppm
    
    @uncertainty_ppm.setter
    def uncertainty_ppm(self, value: float):
        """Set the uncertainty in PPM (must be 0-10)."""
        if 0.0 <= value <= 10.0:
            self._uncertainty_ppm = value
    
    @property
    def unc_degrees_of_freedom(self) -> int:
        """Get the degrees of freedom for uncertainty."""
        return self._unc_degrees_of_freedom
    
    @unc_degrees_of_freedom.setter
    def unc_degrees_of_freedom(self, value: int):
        """Set the degrees of freedom for uncertainty."""
        if value >= 0:
            self._unc_degrees_of_freedom = value
    
    @property
    def gpib_error(self) -> int:
        """Get the GPIB error code."""
        return self._gpib_error
    
    # Calibration methods
    def set_calibration_value(self, index: int, value: str):
        """
        Store a calibration value.
        
        Args:
            index: Index in calibration array (0-23)
            value: Calibration value string
        """
        if 0 <= index < 24:
            self._calibration_values[index] = value
    
    def get_calibration_value(self, index: int) -> str:
        """
        Retrieve a calibration value.
        
        Args:
            index: Index in calibration array (0-23)
            
        Returns:
            The calibration value string
        """
        if 0 <= index < 24:
            return self._calibration_values[index]
        return ""
    
    def clear_gpib_error(self):
        """Clear the GPIB error flag."""
        self._gpib_error = 0
    
    # Connection methods
    def connect(self):
        """Establish GBIB connection to the instrument."""
        if not self._is_present:
            return
        
        try:
            self._resource_manager = pyvisa.ResourceManager()
            # Create GPIB address string: GPIB0::address::INSTR
            gpib_address_str = f"GPIB0::{self._gpib_address}::INSTR"
            self._instrument = self._resource_manager.open_resource(gpib_address_str)
            # Configure terminators for proper communication
            # A lot of MI6010D firmware revisions only send a carriage return (\r) at the
            # end of each response.  Older code used '\n' because that used to work, but
            # a recent device update switched to CR‑only which triggers a PyVISA
            # ``UserWarning`` ("read string doesn't end with termination ") and then
            # subsequent calls block until the timeout.  To avoid the warning and
            # prevent the read from hanging we allow the terminator to be configurable
            # and we suppress the warning when doing the actual read.  The default
            # here is ``'\r'`` which has been verified on the current hardware – run
            # ``Pruebas/Test_MI6010D_diagnostic.py`` if you need to check a different
            # terminator (``'\n'``, ``'\r\n'`` or ``None`` are tested there).
            # apply whatever terminators the caller has configured; these can
            # be tweaked before calling ``connect`` if circumstances change.
            self._instrument.read_termination = self.read_termination
            self._instrument.write_termination = self.write_termination
            self._instrument.send_end = True
            # Set timeout
            self._instrument.timeout = 20000  # 20 seconds (sufficient for measurements)
        except Exception as e:
            print(f"Error connecting to GPIB device at address {self._gpib_address}: {e}")
            self._gpib_error = 1
    
    def disconnect(self):
        """Close GPIB connection to the instrument (keep ResourceManager open)."""
        if not self._is_present:
            return
        
        try:
            if self._instrument:
                self._instrument.close()
                self._instrument = None
            # Keep _resource_manager open to avoid invalidating other GPIB instruments
        except Exception as e:
            print(f"Error disconnecting from GPIB device: {e}")
            self._gpib_error = 1
    
    # Helper method for sending commands
    def _send_command(self, command: str):
        """
        Send a command to the device.
        
        Args:
            command: The command string to send
        """
        if not self._is_present or not self._instrument:
            return
        
        try:
            self._instrument.write(command)
        except Exception as e:
            print(f"Error sending command '{command}': {e}")
            self._gpib_error = 1
    
    # Helper method for receiving data
    def _receive_data(self) -> str:
        """
        Receive data from the device.
        
        Returns:
            The received data string
        """
        if not self._is_present or not self._instrument:
            return ""
        
        try:
            # ``pyvisa`` will emit a ``UserWarning`` if the buffer is returned
            # before the expected read terminator is seen; the instrument stopped
            # appending a newline a while ago and the most recent firmware only
            # sends a ``\r``.  Suppress the warning and fall back to a raw read if
            # the normal ``read`` call fails.
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                data = self._instrument.read()
        except Exception as e:
            # if ``read`` itself raised we try a raw read so we can still recover
            try:
                raw = self._instrument.read_raw()
                data = raw.decode('ascii', errors='replace')
            except Exception:
                data = ''
            error_str = str(e)
            if "TMO" not in error_str and "Timeout" not in error_str and "VI_ERROR" not in error_str:
                print(f"Error receiving data: {e}")
            self._gpib_error = 2
        # Strip any terminating CR/LF and whitespace
        if isinstance(data, bytes):
            try:
                data = data.decode('ascii', errors='replace')
            except Exception:
                data = str(data)
        return data.strip('\n \t') if isinstance(data, str) else str(data).strip()

    
    # Control commands
    def send_keyboard_lockout(self, lock: bool):
        """
        Set the local lock out condition.
        
        Args:
            lock: True to lock keyboard, False to unlock
        """
        if not self._is_present:
            return
        
        command = "K" if lock else "U"
        self._send_command(command)

    def send_stdby(self):
        """Set device to standby mode."""
        if not self._is_present:
            return
        self._send_command("S")
    
    def send_remote(self):
        """Set device to remote mode."""
        if not self._is_present:
            return
        self._send_command("R")
    
    def send_calibrate(self):
        """Send the calibrate command."""
        if not self._is_present:
            return
        self._send_command("C")
    
    def send_filter(self, filter_time: str):
        """
        Set the bridge filter.
        
        Args:
            filter_time: Filter time as string ("0.3s", "1s", "3s")
        """
        if not self._is_present:
            return
        
        # Normalize comma to dot for international versions
        filter_time = filter_time.replace(",", ".")
        
        commands = {
            "0.3s": "G1",
            "1s": "G2",
            "3s": "G3"
        }
        
        command = commands.get(filter_time)
        if command:
            self._send_command(command)
    
    def send_extender_mode(self, extender: int):
        """
        Set which extender mode is being used.
        
        Args:
            extender: Extender mode (1, 2, or other)
        """
        if not self._is_present:
            return
        
        command = "E" if extender in [1, 2] else "H"
        self._send_command(command)
    
    def send_ix(self, ix: float):
        """
        Set the current (Ix).
        
        Args:
            ix: Current value in Amperes (will be converted to mA)
        """
        if not self._is_present:
            return
        
        # Convert to mA
        send_string = str(ix)
        # Ensure dot notation for firmware
        send_string = send_string.replace(",", ".")
        self._send_command(f"I{send_string}")
    
    def send_ext_ix(self, ix: float):
        """
        Set the extended current (EXTIx).
        
        Args:
            ix: Current value in Amperes (will be converted to mA)
        """
        if not self._is_present:
            return
        
        # Convert to mA
        send_string = str(ix * 1000.0)
        # Ensure dot notation for firmware
        send_string = send_string.replace(",", ".")
        self._send_command(f"j{send_string}")
    
    def send_reversal_rate(self, reversal_rate: int):
        """
        Set the reversal rate.
        
        Args:
            reversal_rate: The reversal rate value
        """
        if not self._is_present:
            return
        self._send_command(f"T{reversal_rate}")
    
    def send_measurements(self, number: int):
        """
        Set the number of measurements.
        
        Args:
            number: Number of measurements
        """
        if not self._is_present:
            return
        self._send_command(f"M{number}")
    
    def send_statistics(self, number: int):
        """
        Set the number of statistics.
        
        Args:
            number: Number of statistics (limited to 50 if > 50)
        """
        if not self._is_present:
            return
        
        # Ensure proper values for statistics
        if number > 50 and number <= 250:
            number = 50
        self._send_command(f"J{number}")
    
    def send_rs(self, value: float):
        """
        Set the Rs (series resistance) value.
        
        Args:
            value: Rs value
        """
        if not self._is_present:
            return
        
        send_string = str(value)
        # Ensure dot notation for firmware
        send_string = send_string.replace(",", ".")
        self._send_command(f"A{send_string}")
    
    def send_rx(self, value: float):
        """
        Set the Rx (unknown resistance) value.
        
        Args:
            value: Rx value
        """
        if not self._is_present:
            return
        
        send_string = str(value)
        # Ensure dot notation for firmware
        send_string = send_string.replace(",", ".")
        self._send_command(f"r{send_string}")
    
    def send_standard_resistors_status(self, rx_as_standard: bool):
        """
        Set standard resistors status.
        
        Args:
            rx_as_standard: True if Rx is standard, False otherwise
        """
        if not self._is_present:
            return
        
        command = "x" if rx_as_standard else "s"
        self._send_command(command)
    
    def send_temp_string(self, value: str, command: str):
        """
        Send temperature parameter as string.
        
        Args:
            value: Temperature value string
            command: Command prefix
        """
        if not self._is_present:
            return
        
        send_string = value.replace(",", ".")
        self._send_command(f"{command}{send_string}")
    
    def send_temp_double(self, value: float, command: str):
        """
        Send temperature parameter as double.
        
        Args:
            value: Temperature value
            command: Command prefix
        """
        if not self._is_present:
            return
        
        send_string = str(value).replace(",", ".")
        self._send_command(f"{command}{send_string}")
    
    def send_current_factor(self, factor: float):
        """
        Set the current factor (divide rough current by 10 or not).
        
        Args:
            factor: 0.1 or 1.0
        """
        if not self._is_present:
            return
        
        if factor == 0.1:
            self._send_command("V")
        elif factor == 1.0:
            self._send_command("W")
    
    def send_continue(self):
        """Tell the 6010C to continue with the measurement."""
        if not self._is_present:
            return
        self._send_command("W")
    
    def send_query(self):
        """Query the bridge's state."""
        if not self._is_present:
            return
        self._send_command("Q")
    
    def send_ix_multiply_one_over_root_two(self):
        """Multiply the current by 0.707 (1/√2)."""
        if not self._is_present:
            return
        self._send_command("X")
    
    def send_ix_multiply_root_two(self):
        """Multiply the current by 1.414 (√2)."""
        if not self._is_present:
            return
        self._send_command("Z")
    
    def send_stop(self):
        """Stop the unit / set to standby."""
        if not self._is_present:
            return
        self._send_command("S")
    
    def send_range_ext_error(self, range_value: int):
        """
        Set the error of turns used in range extension.
        
        Args:
            range_value: The range value
        """
        if not self._is_present:
            return
        
        # This is a complex method with references to UI elements
        # Implementing a basic version without UI dependencies
        if range_value == 0:
            send_string = str(0.0)
        elif range_value in [1, 3]:
            send_string = str(0.0)
        elif range_value in [10, 30]:
            send_string = str(0.0)
        elif range_value in [100, 300]:
            send_string = str(0.0)
        else:
            send_string = str(0.0)
        
        # Ensure dot notation
        if send_string == "0.0":
            send_string = str(0.00000000012)  # FW freezes when getting 0.0
        
        send_string = send_string.replace(",", ".")
        self._send_command(f"Y{send_string}")
    
    # Data retrieval methods
    def get_serial_poll(self) -> int:
        """
        Wait for and return a non-zero serial poll.
        
        Returns:
            The serial poll value
        """
        if not self._is_present or not self._instrument:
            return 0
        
        try:
            # Poll the device until we get a non-zero response
            sp_finished = False
            sp_new = 0
            
            while True:
                time.sleep(0.2)
                sp_received = int(self._instrument.read_stb())
                
                if sp_received != 0:
                    if sp_received != sp_new:
                        sp_new = sp_received
                        sp_finished = True
                else:
                    if sp_finished:
                        break
            
            return sp_new
        except Exception as e:
            print(f"Error on serial poll: {e}")
            self._gpib_error = 2
            return 0
    
    def get_data(self) -> str:
        """
        Get data received from the 6010D.
        
        Returns:
            The received data string
        """
        if not self._is_present:
            return ""
        return self._receive_data()
    
    def get_value(self) -> float:
        """
        Get a floating point number received from the 6010D.
        
        Returns:
            The numeric value, or 0.0 if parsing fails
        """
        if not self._is_present:
            return 0.0      
        data = self._receive_data()
        
        try:
            # Skip first character if present
            numeric_part = data[1:] if len(data) > 1 else data
            # Try parsing with dot notation
            value = float(numeric_part)
            return value
        except ValueError:
            # Try with comma notation
            try:
                numeric_part = data[1:] if len(data) > 1 else data
                numeric_part = numeric_part.replace(".", ",")
                value = float(numeric_part.replace(",", "."))
                return value
            except ValueError:
                return 0.0
    
    def clear_bridge(self):
        """Send clear command to the bridge."""
        if not self._is_present or not self._instrument:
            return
        
        try:
            self._instrument.clear()
        except Exception as e:
            print(f"Error clearing bridge: {e}")
            self._gpib_error = 1

    def reset(self, flush_timeout: int = 500):
        """
        Perform a safe logical reset of the instrument after cancelling a measurement.

        Steps:
        - send Standby ('S') to stop measurement
        - short delay
        - clear the device
        - flush any remaining data from the instrument buffer

        Args:
            flush_timeout: timeout in milliseconds used when flushing the buffer
        """
        if not self._is_present or not self._instrument:
            return

        try:
            # Send Standby (stop)
            try:
                self._instrument.write('S')
            except Exception:
                # fallback to _send_command to handle errors
                self._send_command('S')

            time.sleep(0.5)

            # Clear device
            try:
                self._instrument.clear()
            except Exception:
                pass

            # Flush buffer: read until timeout
            orig_timeout = getattr(self._instrument, 'timeout', None)
            try:
                # set short timeout for flushing
                self._instrument.timeout = flush_timeout
                while True:
                    try:
                        msg = self._instrument.read_raw()
                        #msg = self._instrument.read()
                        # discard
                    except Exception:
                        break
            finally:
                # restore timeout
                if orig_timeout is not None:
                    self._instrument.timeout = orig_timeout

        except Exception as e:
            print(f"Error during reset: {e}")
            self._gpib_error = 1
    
    def send_gpib_test_command(self, test_command: str):
        """
        Send a test command for GPIB debugging.
        
        Args:
            test_command: The test command string
        """
        try:
            if self._instrument:
                self._instrument.write(test_command)
        except Exception as e:
            print(f"Error on GPIB test command: {e}")
            self._gpib_error = 1
    
    def get_gpib_test_response(self) -> str:
        """
        Get the response to a GPIB test command.
        
        Returns:
            The response string
        """
        try:
            if self._instrument:
                return self._instrument.read()
        except Exception as e:
            print(f"Error reading GPIB test response: {e}")
            self._gpib_error = 2
        return ""
