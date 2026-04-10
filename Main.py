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
import Driver_EscanerINTI   
from Instrumental.Scanner import ScannerInti
from pathlib import Path
import pandas as pd

 # Importamos el script de prueba para verificar la conectividad antes de iniciar el programa principal

sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    State_of_Program = "Inicio"  
    State_of_sub_Program = "Inicio"
    GPIB_ADDRESS_BRID = 15      # MI6010D
    GPIB_ADDRESS_DMM1 = 14      # HP34401A
    GPIB_ADDRESS_DMM2 = 13      # HP34420A
    GPIB_ADDRESS_DMM3 = 26      # HP3458A
    GPIB_ADDRESS_ESCA = 18      # Escaner
    DMM_NAME_1 = "HP34401A"
    DMM_NAME_2 = "HP34420A"
    DMM_NAME_3 = "HP3458A"

    RX = 1.0
    ISMAX = 1e-3 
    PSAMX = 25.0e-3
    
    # Variables para parámetros de medición (inicializadas)
    ENTRADA_S = None
    ENTRADA_X = None
    RS_NOMBRE = None
    RX_NOMBRE = None
    RS = None
    IX = None
    TIME_REVERSAL    = None
    NUM_MEASUREMENTS = None
    NUM_STATISTICS   = None

    while True:
        
        # Estado dedicado a mostrar el menú de bienvenida
        if State_of_Program == "Inicio":
            
            State_of_Program = Manejo_Archivos.Func_Data.Welcome_Menu()

        if State_of_Program == "Lectura_Parametros":
            
            State_of_Program, Listado_de_Mediciones, Cantidad_Mediciones = Manejo_Archivos.Func_Data.Lectura_Parametros()
                                                           
        if State_of_Program == "Medición":
            
            for index, row in Listado_de_Mediciones.iterrows():  
                           
                if State_of_sub_Program == "Inicio":
                    # Estado inicial utilizado como punto de reinicio.
                    Dummy_1 = input("Lista de tareas procesada. Presionar Enter para continuar...")
                    State_of_sub_Program = "Adquirir_Datos"
                
                if State_of_sub_Program == "Adquirir_Datos":
                    
                    # Toma los parámetros para la medición actual desde el DataFrame
                    Tomar_Parametros = row.to_dict()
                    
                    RS_NOMBRE           = Tomar_Parametros['ID_Rs']
                    RX_NOMBRE           = Tomar_Parametros['ID_Rx']
                    ENTRADA_S           = int(Tomar_Parametros['Ch_Rs'])
                    print(f"ENTRADA_S asignada a canal: {ENTRADA_S}")
                    ENTRADA_X           = int(Tomar_Parametros['Ch_Rx'])
                    print(f"ENTRADA_X asignada a canal: {ENTRADA_X}")
                    RS                  = float(Tomar_Parametros['VN_Rs [ohm]'])
                    IX                  = float(Tomar_Parametros['Ix [mA]'])
                    TIME_REVERSAL       = float(Tomar_Parametros['Tiempo_Inversion [s]'])
                    NUM_MEASUREMENTS    = int(Tomar_Parametros['Cant_Mediciones'])
                    NUM_STATISTICS      = int(Tomar_Parametros['Cant_Estadistica']) 
                    
                    State_of_sub_Program = "Conf_Escaner"
                    
                if State_of_sub_Program == "Conf_Escaner":    
                    
                    print(f"\nIniciando medición {index + 1} de {Cantidad_Mediciones}...")  
                    
                    # Inicializa el Scanner y configura canales de forma segura
                    Scanner = ScannerInti(f"GPIB0::{GPIB_ADDRESS_ESCA}::INSTR")
                                 
                    # Asegurar estado inicial con todos los canales abiertos
                    Driver_EscanerINTI.Abrir_Canales(Scanner) 
                    sleep(3)
                    State_of_sub_Program = Driver_EscanerINTI.Conectar_Entradas_Salidas(Scanner, ENTRADA_S,ENTRADA_X)
                    # Cambiar al estado de Análisis después de conectar
                
                    
                if State_of_sub_Program == "Análisis_Datos":
                    # Cargar datos del resistor calibrado desde la base de datos JSON
                    RS_Calibrado = Manejo_Archivos.Func_Data.Cargar_Resistor_Calibrado(RS_NOMBRE)
                    
                    if RS_Calibrado:
                        # Asignar los valores del resistor calibrado a variables
                        RS_serial = RS_Calibrado.get("serial")
                        RS_valor = float(RS_Calibrado.get("valor"))
                        RS_incertidumbre = float(RS_Calibrado.get("incertidumbre"))
                        RS_drift_anual = float(RS_Calibrado.get("drift anual"))
                        RS_alfa = float(RS_Calibrado.get("alfa"))
                        RS_beta = float(RS_Calibrado.get("beta"))
                        RS_temp_calibracion = float(RS_Calibrado.get("temperatura de calibracion"))
                        RS_fecha_calibracion = RS_Calibrado.get("fecha de calibracion")
                        
                        print(f"Datos cargados:")
                        print(f"  Serial: {RS_serial}")
                        print(f"  Valor: {RS_valor}")
                        print(f"  Incertidumbre: {RS_incertidumbre} ppm")
                    else:
                        print(f"No se pudieron cargar los datos de '{RS_NOMBRE}'")
                        State_of_sub_Program = "Abrir_Canales"
                        continue
                    
                    State_of_sub_Program = "Medición_N"
                    
                if State_of_sub_Program == "Medición_N":
                    
                    if Measurement_MI6010D.Check_de_Seguridad(RS, RX, ISMAX, IX, PSAMX):
                        Measurement_MI6010D.Measure_with_Temp(GPIB_ADDRESS_BRID, RS, RX, TIME_REVERSAL, IX, NUM_MEASUREMENTS, NUM_STATISTICS, DMM_NAME_1, GPIB_ADDRESS_DMM1, DMM_NAME_2, GPIB_ADDRESS_DMM2)
                    else:
                        print("Condición de seguridad no cumplida. Saltando medición.")
                    
                    State_of_sub_Program = "Abrir_Canales"
                
                if State_of_sub_Program == "Abrir_Canales":
                    
                    Driver_EscanerINTI.Cerrar_Escaner(Scanner)
                    State_of_sub_Program = "Conf_Escaner"
                    
                else:
                    print("Estado no reconocido, reiniciando programa...")
                    # Cerrar sesión de todos los instrumentos para evitar recursos abiertos
                    if 'Scanner' in locals() and Scanner is not None:
                        Scanner.close()
                        del Scanner
                    State_of_Program = "Final"
                    State_of_sub_Program = "Inicio"
                    break
            
            State_of_Program = "Final"
            State_of_sub_Program = "Inicio"
                                  
            if State_of_Program == "Final":
                    
                 State_of_Program = Manejo_Archivos.Func_Data.Final_Menu()
                                                    



if __name__ == "__main__":

    main()