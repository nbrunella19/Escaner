import pyvisa

class HP34420A:
    def __init__(self, gpib_address: str = "GPIB0::10::INSTR"):
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(gpib_address)
        self.instrument.timeout = 5000
        self.reset()

    def reset(self):
        self.instrument.write("*RST")
        self.instrument.write("*CLS")

    def identify(self) -> str:
        return self.instrument.query("*IDN?")

    def configure_voltage_dc(self, range_val=0.01, resolution=1e-7):
        self.instrument.write("CONF:VOLT:DC")
        self.instrument.write(f"VOLT:DC:RANG {range_val}")
        self.instrument.write(f"VOLT:DC:RES {resolution}")
        self.set_input_impedance(1e10)
        self.set_digits(7)
        self.set_integration_speed(10)

    def set_input_impedance(self, impedance_ohm: float = 1e10):
        self.instrument.write(f"SENS:VOLT:DC:IMP {impedance_ohm:.0E}")

    def set_digits(self, digits: int = 7):
        self.instrument.write(f"SENS:FRES:DIG {digits}")

    def set_integration_speed(self, nplc: float = 20.0):
        self.instrument.write(f"SENS:FRES:NPLC {nplc}")

    def read(self):
        if hasattr(self, "_measure_cmd"):
            return float(self.instrument.query(self._measure_cmd))
        else:
            return float(self.instrument.query("READ?"))

    def close(self):
        """Close the instrument connection (keep ResourceManager open)."""
        if self.instrument:
            self.instrument.close()
            self.instrument = None
        # Keep rm open to avoid invalidating other GPIB instruments
    
    def configure_resistance_4wire(self, range_val=100, resolution=0.001,nplc=10):
        # seleccionar terminal correcto
        self.instrument.write("ROUT:TERM FRONt1")
        # modo 4-wire
        self.instrument.write("CONF:FRES")
        # rango
        self.instrument.write(f"FRES:RANG {range_val}")
        # resolución
        self.instrument.write(f"FRES:RES {resolution}")
        # tiempo de integración
        self.instrument.write(f"SENS:FRES:NPLC {nplc}")
       