import time
import pyvisa

class ScannerInti:
    # Constantes del instrumento
    ADDRESS_GPIB = "GPIB0::18::INSTR"  # Formato VISA
    SALIDA_1 = 'S'
    SALIDA_2 = 'X'
    NADA = 63
    RESET_TODO = 112

    DireccionGPIB = None  # Será el recurso VISA

    def __init__(self):
        # Inicializa conexión con PyVISA
        self.rm = pyvisa.ResourceManager()
        try:
            ScannerInti.DireccionGPIB = self.rm.open_resource(self.ADDRESS_GPIB)
            ScannerInti.DireccionGPIB.timeout = 1000  # Timeout en ms
            print(f"Conectado a {self.ADDRESS_GPIB}")
            self.Configuracion(ScannerInti.DireccionGPIB)
        except Exception as e:
            raise RuntimeError(f"No se pudo conectar al instrumento: {e}")

    def __del__(self):
        if ScannerInti.DireccionGPIB is not None:
            ScannerInti.DireccionGPIB.close()
            print("Conexión cerrada")

    # ---------------------------------------------------
    # Métodos privados para comunicación GPIB
    # ---------------------------------------------------
    def _iprintf(self, handle, command, *args):
        cmd = command % args if args else command
        handle.write(cmd)

    def _iscanf(self, handle, fmt=None):
        # fmt no se usa porque VISA maneja strings directamente
        return handle.read().strip()

    # ---------------------------------------------------
    # Métodos equivalentes al C++
    # ---------------------------------------------------
    def ConfiguracionPuerto(self, direccion):
        self._iprintf(direccion, "C2X\n")
        return 0

    def ConfiguracionFormato(self, direccion):
        self._iprintf(direccion, "F3X\n")
        return 0

    def Configuracion(self, direccion):
        self.ConfiguracionPuerto(direccion)
        self.ConfiguracionFormato(direccion)
        return 0

    def EnviarDato(self, direccion, dato):
        self._iprintf(direccion, "P1X\n")
        self._iprintf(direccion, f"D{dato}ZX\n")
        return 0

    def ResetPlacaGpib(self, direccion):
        # No hay equivalente directo a iclear en PyVISA, pero se puede resetear
        direccion.clear()
        return 0

    def ResetGeneral(self, direccion):
        self.EnviarDato(direccion, self.RESET_TODO)
        return 0

    def CambiarEstado(self, direccion):
        self._iprintf(direccion, "A9X\n")
        time.sleep(0.01)
        self._iprintf(direccion, "B9X\n")
        return 0

    def Decodificacion(self, puerto, entrada):
        entrada -= 1
        if puerto == self.SALIDA_1:
            entrada += 16
        elif puerto == self.SALIDA_2:
            entrada += 32
        else:
            entrada = 0
        return entrada

    def Codificacion(self, puerto, entrada):
        if puerto == self.SALIDA_1:
            entrada = entrada + 1 if entrada != self.NADA else 0
        elif puerto == self.SALIDA_2:
            entrada = entrada + 1 - 24 if entrada != self.NADA else 0
        return entrada

    def Ver(self, direccion, salida):
        if salida == self.SALIDA_1:
            self._iprintf(direccion, "P3X\n")
            dato = self._iscanf(direccion)
        elif salida == self.SALIDA_2:
            self._iprintf(direccion, "P4X\n")
            dato = self._iscanf(direccion)
        else:
            dato = "0"
        return int(dato)

    def InvertirCanal(self, direccion):
        temporal1 = self.Ver(direccion, self.SALIDA_1)
        temporal2 = self.Ver(direccion, self.SALIDA_2)
        if temporal1 != self.NADA and temporal2 != self.NADA:
            temporal2 -= 24
            self.ResetCanal(direccion, self.SALIDA_1, temporal1 + 1)
            time.sleep(0.02)
            self.SetearCanal(direccion, self.SALIDA_2, temporal1 + 1)
            time.sleep(0.04)
            self.SetearCanal(direccion, self.SALIDA_1, temporal2 + 1)

    def SetearCanal(self, direccion, puerto, entrada):
        datoaescribir = self.Decodificacion(puerto, entrada)
        if datoaescribir != 0:
            self.EnviarDato(direccion, datoaescribir)
        return 0

    def ResetCanal(self, direccion, puerto, entrada):
        datoaescribir = self.Decodificacion(puerto, entrada)
        if datoaescribir != 0:
            datoaescribir += 64
            self.EnviarDato(direccion, datoaescribir)
        return 0