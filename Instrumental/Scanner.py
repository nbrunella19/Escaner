#################################################################################################################
#   Archivo: Scanner.py 
#   Descripción: Clase para controlar el conmutador de entradas/salidas del escáner, utilizando PyVISA para la comunicación GPIB
#   Autor: NSB
#################################################################################################################
import time
import pyvisa

class ScannerInti:
    # Constantes del instrumento
    #ADDRESS_GPIB = "GPIB0::18::INSTR"  # Formato VISA
    SALIDA_1 = 'S'
    SALIDA_2 = 'X'
    ENTRADA_1 = 1
    ENTRADA_2 = 2
    ENTRADA_3 = 3
    ENTRADA_4 = 4
    ENTRADA_5 = 5
    ENTRADA_6 = 6
    ENTRADA_7 = 7
    ENTRADA_8 = 8
    ENTRADA_9 = 9
    ENTRADA_10 = 10
    NADA = 63
    RESET_TODO = 112

    def __init__(self, gpib_address: str = "GPIB0::18::INSTR"):
        # Inicializa conexión con PyVISA
        self.rm = pyvisa.ResourceManager()
        try:
            self.direccion = self.rm.open_resource(gpib_address)
            self.direccion.timeout = 1000  # Timeout en ms
            print(f"\nEscaner conectado a {gpib_address}")
            self.Configuracion(self.direccion)
        except Exception as e:
            raise RuntimeError(f"No se pudo conectar al instrumento: {e}")

    def close(self):
        """Cierra explícitamente la conexión del Scanner."""
        if hasattr(self, 'direccion') and self.direccion is not None:
            self.direccion.close()
            self.direccion = None
            print("Conexión Scanner cerrada")

    def __del__(self):
        self.close()

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
    
    # Nuevo método para hacer un query al instrumento
    def query(self, command):
        """
        Envía un comando al instrumento y devuelve la respuesta.
        """
        self._iprintf(self.direccion, command)
        print(self._iscanf(self.direccion))