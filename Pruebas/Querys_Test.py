import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Instrumental.MI6010D import MI60100 # Esta línea importa la clase MI60100 [9].
from Instrumental.Scanner import ScannerInti
from Instrumental.HP3458A import HP3458A
from Instrumental.HP34401 import HP34401A
from Instrumental.HP34420 import HP34420A


# Ejemplo de uso Query MI60100
bridge = MI60100(15)  # GPIB #15
bridge.local_unlock()
bridge.standby()
print("Estado:", bridge.query())
bridge.local_lockout()
bridge.close()



"""
Mul_HP3458A = HP3458A("GPIB0::26::INSTR")
valor=Mul_HP3458A.identify()
print("Identificación del HP3458A:", valor) 
Mul_HP3458A.close()
"""
"""
# Pruebas del multímetro HP34401A
Mul_HP34401A = HP34401A("GPIB0::14::INSTR")
valor=Mul_HP34401A.identify()
print("Identificación del HP34401:", valor) 
Mul_HP34401A.close()
"""
"""
# Pruebas del multímetro HP34401A
Mul_HP34420A = HP34420A("GPIB0::14::INSTR")
valor=Mul_HP34420A.identify()
print("Identificación del HP34420:", valor) 
Mul_HP34420A.close()
"""
"""
# Pruebas en el scanner
scanner = ScannerInti()  # Esto abre la conexión GPIB
#scanner.SetearCanal(scanner.DireccionGPIB, ScannerInti.SALIDA_1, 5)
#scanner.ResetGeneral(scanner.DireccionGPIB)
#print("Valor leído:",scanner.Ver(scanner.DireccionGPIB, ScannerInti.SALIDA_1))
"""


