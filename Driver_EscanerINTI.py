################################################################################################################
#   Archivo: Escaner_Test.py
#   Descripción: Script de prueba para verificar la conectividad y funcionalidad básica de la clase ScannerInti
#   Autor: NSB
################################################################################################################



import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from Instrumental.Scanner import ScannerInti


def test_ScannerInti():
    scanner = None
    try:
        # Verificar conectividad: intentar instanciar la clase
        print("Verificando conectividad con ScannerInti...")
        scanner = ScannerInti()
        print("Conectividad verificada exitosamente.")
        
        # Reset general para asegurar estado inicial
        scanner.ResetGeneral(ScannerInti.DireccionGPIB)
        time.sleep(3)
        
        Conectar_Entrada_Salida(scanner, ScannerInti.SALIDA_1, ScannerInti.ENTRADA_3)
    
    except Exception as e:
        print(f"Error durante la prueba: {e}")
    finally:
        # Cerrar conexión si se instanció
        if scanner:
            del scanner
        



def Conectar_Entrada_Salida(Scanner, SALIDA, ENTRADA):
    """
    Función que utilizando la clase ScannerInti conecta y setea una entrada específica a una salida 
    que puede ser S O X, de forma segura (sin superposición de relés).
    """     
        
    print(f"Conectado canal {ENTRADA} a salida {SALIDA}...")
    Scanner.SetearCanal(Scanner.direccion, SALIDA, ENTRADA)
    time.sleep(1)  # Pequeño delay
    
    # Verificar estado de canal
    estado_canal_seleccionado = Scanner.Ver(Scanner.direccion, SALIDA)
    print(f"EL canal activo en este momento es el: {estado_canal_seleccionado + 1}")


def Conectar_Entradas_Salidas(Scanner, ENTRADA_S, ENTRADA_X):
    """
    Conecta ENTRADA_S a SALIDA 'S' y ENTRADA_X a SALIDA 'X'.
    Retorna True si es válido. De lo contrario retorna False.
    """
    if not isinstance(ENTRADA_S, int) or not (1 <= ENTRADA_S <= 10):
        print("Error: ENTRADA_S debe ser entero entre 1 y 10.")
        return False

    if not isinstance(ENTRADA_X, int) or not (1 <= ENTRADA_X <= 10):
        print("Error: ENTRADA_X debe ser entero entre 1 y 10.")
        return False

    if ENTRADA_S == ENTRADA_X:
        print("Error: No se pueden usar la misma entrada para S y X.")
        return False

    print(f"Conectando canal {ENTRADA_S} a salida S...")
    # Salida S es "SALIDA_1"
    Scanner.SetearCanal(Scanner.direccion, Scanner.SALIDA_1, ENTRADA_S)
    time.sleep(1)

    # Salida X es "SALIDA_2"
    print(f"Conectando canal {ENTRADA_X} a salida X...")
    Scanner.SetearCanal(Scanner.direccion, Scanner.SALIDA_2, ENTRADA_X)
    time.sleep(1)

    return True


def Abrir_Canales(Scanner):
    Scanner.ResetGeneral(Scanner.direccion)
    time.sleep(6)
    print("Salidas abiertas.")
    
def Cerrar_Escaner(Scanner):
    """
    Cierra la conexión del Scanner de forma controlada.
    """
    #Abro todos los canales para asegurar que no queden relés cerrados
    Scanner.ResetGeneral(Scanner.direccion)
    print("Cerrando Scanner...")
    Scanner.close()
    print("Scanner cerrado exitosamente.")
    

'''
if __name__ == "__main__":
    test_ScannerInti()
'''
