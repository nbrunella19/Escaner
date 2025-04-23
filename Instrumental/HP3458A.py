import pyvisa
import time

class HP3458A:
    def __init__(self, gpib_address: str = "GPIB0::22::INSTR"):
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(gpib_address)
        self.instrument.timeout = 5000
        self.reset()

    def reset(self):
        """Resetea y limpia el instrumento."""
        self.instrument.write("*RST")
        self.instrument.write("*CLS")
        time.sleep(1)

    def identify(self) -> str:
        """Obtiene la identificación del dispositivo."""
        return self.instrument.query("*IDN?")

    def configure_measurement(self, mode="DCV", range_val=10, resolution=0.00001, nplc=10):
        """
        Configura el tipo de medición.
        mode: 'DCV' (voltaje DC), 'ACV' (voltaje AC), etc.
        """
        if mode.upper() == "DCV":
            self.instrument.write(f"DCV {range_val},{resolution}")
        elif mode.upper() == "ACV":
            self.instrument.write(f"ACV {range_val},{resolution}")
        else:
            raise ValueError(f"Modo de medición '{mode}' no soportado.")
        
        self.instrument.write(f"NPLC {nplc}")

    def trigger(self):
        """Dispara una medición y espera el resultado."""
        return float(self.instrument.query("TVAL?"))

    def read_buffer(self, count=10):
        """
        Realiza múltiples mediciones.
        """
        self.instrument.write(f"TRIG {count}")
        data = self.instrument.query("RMEM?")
        return [float(val) for val in data.strip().split(",")]

    def close(self):
        """Cierra la conexión."""
        self.instrument.close()
        self.rm.close()