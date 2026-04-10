import pyvisa


class HP34401A:
    def __init__(self, gpib_address: str = "GPIB0::14::INSTR"):
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(gpib_address)
        self.instrument.timeout = 5000
        self.reset()

    def reset(self):
        self.instrument.write("*RST")
        self.instrument.write("*CLS")

    def identify(self) -> str:
        return self.instrument.query("*IDN?")

    # -----------------------------
    # CONFIGURACIÓN 4-WIRE
    # -----------------------------
    def configure_resistance_4wire(self, range_val=100, resolution=0.001, nplc=10):
        """
        Configura medición de resistencia 4-wire (FRES)
        """

        self.instrument.write("CONF:FRES")

        self.instrument.write(f"FRES:RANG {range_val}")
        self.instrument.write(f"FRES:RES {resolution}")

        self.set_nplc(nplc)

    # -----------------------------
    # VELOCIDAD (NPLC)
    # -----------------------------
    def set_nplc(self, nplc: float = 10):
        """
        NPLC = Number of Power Line Cycles

        0.02 → muy rápido, más ruido
        1    → balanceado
        10   → alta precisión
        100  → ultra estable (lento)
        """
        self.instrument.write(f"SENS:FRES:NPLC {nplc}")

    # -----------------------------
    # RESOLUCIÓN (equivalente a dígitos)
    # -----------------------------
    def set_resolution(self, resolution: float):
        """
        Controla la resolución de la medición
        (equivalente a dígitos en este instrumento)
        """
        self.instrument.write(f"FRES:RES {resolution}")

    # -----------------------------
    # LECTURA
    # -----------------------------
    def read(self):
        return float(self.instrument.query("READ?"))

    # -----------------------------
    # ERRORES
    # -----------------------------
    def get_error(self):
        return self.instrument.query("SYST:ERR?")

    def clear_errors(self):
        self.instrument.write("*CLS")

    # -----------------------------
    # CIERRE
    # -----------------------------
    def close(self):
        if self.instrument:
            self.instrument.close()
            self.instrument = None
