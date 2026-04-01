#################################################################################################################
#   Archivo: Main.py    
#   Descripción: Script principal que orquesta la ejecución del programa, gestionando el flujo de estados y tareas
#   Autor: NSB
#################################################################################################################

import sys
from time import sleep, time
from turtle import delay
from Instrumental import Scanner
import Manejo_Archivos.Func_Data
import Measurement_MI6010D
from Measurement_MI6010D import Measure_with_Temp
import Escaner_Test   
from Instrumental.Scanner import ScannerInti
from pathlib import Path

 # Importamos el script de prueba para verificar la conectividad antes de iniciar el programa principal

sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    State_of_Program = "Inicio"  
    ENTRADA_S = 2
    ENTRADA_X = 3
    GPIB_ADDRESS = 15
    RS = 1.0
    RX = 1.0
    TIME_REVERSAL = 8
    IX = 1  #mA
    NUM_MEASUREMENTS = 2
    NUM_STATISTICS = 2
    ISMAX = 0.9e-3 
    PSAMX = 25.0e-3

    while True:
        
        # Estado dedicado a mostrar el menú de bienvenida
        if State_of_Program == "Inicio":
            
            State_of_Program = Manejo_Archivos.Func_Data.Welcome_Menu()
                              
        if State_of_Program == "Config_Escaner":
            
            # Verificar conectividad: intentar instanciar la clase ScannerInti
            # Inicializa el Scanner y configura canales de forma segura
            Scanner = ScannerInti()
          
            # Asegurar estado inicial con todos los canales abiertos
            Escaner_Test.Abrir_Canales(Scanner) 
            sleep(3)
            State_of_Program = Escaner_Test.Conectar_Entradas_Salidas(Scanner, ENTRADA_S,ENTRADA_X)
                   
        if State_of_Program == "Medición":
            
            if Measurement_MI6010D.Check_de_Seguridad(RS, RX, ISMAX, IX, PSAMX):
                Measurement_MI6010D.Measure_with_Temp(GPIB_ADDRESS, RS, RX, TIME_REVERSAL, IX, NUM_MEASUREMENTS, NUM_STATISTICS, ISMAX, PSAMX)
            else:
                print("Condición de seguridad no cumplida. Saltando medición.")
            
            State_of_Program = "Abrir_Canales"
        
        if State_of_Program == "Abrir_Canales":
            
            Escaner_Test.Cerrar_Escaner(Scanner)
            # del Scanner
            State_of_Program = "Final"
        
        
        if State_of_Program == "Final":
            
            State_of_Program = Manejo_Archivos.Func_Data.Final_Menu()
                                             
        else:
            print("Estado no reconocido, reiniciando programa...")
            # Cerrar sesión de todos los instrumentos para evitar recursos abiertos
            if 'Scanner' in locals() and Scanner is not None:
                Scanner.close()
                del Scanner
            State_of_Program = "Inicio"


if __name__ == "__main__":

    main()