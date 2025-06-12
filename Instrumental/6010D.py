import pyvisa

class MI6010D:
    def __init__(self, gpib_address="GPIB0::5::INSTR"):
        self.rm = pyvisa.ResourceManager()
        self.inst = self.rm.open_resource(gpib_address)
        self.inst.timeout = 10000  # 10 segundos

    def identify(self):
        """Intenta identificar el instrumento."""
        try:
            return self.inst.query("*IDN?")
        except Exception:
            return "MI 6010D - No responde a *IDN?"

    def reset(self):
        """Reset básico del instrumento."""
        self.inst.write("Z")

    def set_temperature(self, temp_celsius):
        """Setea la temperatura esperada en grados Celsius."""
        self.inst.write(f"T{temp_celsius}")

    def set_frequency(self, freq_hz):
        """Setea la frecuencia de operación (por ejemplo, 1000 para 1kHz)."""
        self.inst.write(f"F{int(freq_hz)}")

    def set_current(self, current_mA):
        """Setea la corriente de prueba en mA."""
        self.inst.write(f"C{int(current_mA)}")

    def start_measurement(self):
        """Inicia una medición."""
        self.inst.write("M1")

    def fetch_result(self):
        """Recupera el resultado de la última medición."""
        return self.inst.query("R?")

    def close(self):
        """Cierra la conexión GPIB."""
        self.inst.close()
        self.rm.close()
        
bridge = MI6010D("GPIB0::5::INSTR")
print(bridge.identify())
bridge.reset()
bridge.set_temperature(23.0)
bridge.set_frequency(1000)
bridge.set_current(5)
bridge.start_measurement()
result = bridge.fetch_result()
print(f"Resultado: {result}")
bridge.close()