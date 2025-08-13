from Instrumental.MI6010D import MI60100
from Instrumental.Scanner import ScannerInti


"""
# Ejemplo de uso Query MI60100
bridge = MI60100(15)  # GPIB #15
bridge.local_unlock()
print("Estado:", bridge.query())
bridge.close()
"""

scanner = ScannerInti()  # Esto abre la conexión GPIB
#scanner.SetearCanal(scanner.DireccionGPIB, ScannerInti.SALIDA_1, 5)
#scanner.ResetGeneral(scanner.DireccionGPIB)
print("Valor leído:",scanner.Ver(scanner.DireccionGPIB, ScannerInti.SALIDA_1))
#print("Valor leído:", valor)
