import pyvisa

class HP34401A:
    def __init__(self, gpib_address: str = "GPIB0::5::INSTR"):
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(gpib_address)
        self.instrument.timeout = 5000
        self.reset()

    def reset(self):
        self.instrument.write("*RST")
        self.instrument.write("*CLS")

    def identify(self) -> str:
        return self.instrument.query("*IDN?")

    def configure_voltage_dc(self, range_val=10, resolution=0.00001):
        self.instrument.write("CONF:VOLT:DC")
        self.instrument.write(f"VOLT:DC:RANG {range_val}")
        self.instrument.write(f"VOLT:DC:RES {resolution}")

    def read(self):
        return abs(float(self.instrument.query("READ?")))

    def close(self):
        """Close the instrument connection (keep ResourceManager open)."""
        if self.instrument:
            self.instrument.close()
            self.instrument = None
        # Keep rm open to avoid invalidating other GPIB instruments
        
    def configure_resistance_4wire(self, range_val=1000, resolution=0.001):
        """
        Configura medición de resistencia 4 terminales
        """
        self.instrument.write("CONF:FRES")
        self.instrument.write(f"FRES:RANG {range_val}")
        self.instrument.write(f"FRES:RES {resolution}")
        
        # tiempo de integración (mejor precisión)
        self.instrument.write("SENS:FRES:NPLC 10")