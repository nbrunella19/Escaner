#################################################################################################################
#   Archivo: Main.py    
#   Descripción: Script principal que orquesta la ejecución del programa, gestionando el flujo de estados y tareas
#   Autor: NSB
#################################################################################################################

import sys
import time
from time import sleep, time
from turtle import delay
from Instrumental import Scanner
import Manejo_Archivos.Func_Data
import Measurement_MI6010D
from Measurement_MI6010D import Measure_with_Temp
from Menu_Temp import Menu_Temp
import Driver_EscanerINTI   
from Instrumental.Scanner import ScannerInti
from pathlib import Path
import pandas as pd
import msvcrt

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
    
    Medicion_Ratio =[]
    Medicion_dmm1  =[]
    Medicion_dmm2  =[]
    Medicion_dmm3  =[]
    Des_Ratio =[]
    Des_dmm1  =[]
    Des_dmm2  =[]
    Des_dmm3  =[]
    
    
    while True:
        
        # Estado dedicado a mostrar el menú de bienvenida
        if State_of_Program == "Inicio":
            
            State_of_Program = Manejo_Archivos.Func_Data.Welcome_Menu()

        if State_of_Program == "Lectura_Parametros":
            
            State_of_Program, Listado_de_Mediciones, Cantidad_Mediciones, Ruta_Salida = Manejo_Archivos.Func_Data.Lectura_Parametros()
                                                           
        if State_of_Program == "Seleccion_Instrumentos":
            
            State_of_Program, GPIB_DMM1, GPIB_DMM2, GPIB_DMM3, Cant_Sensores = Menu_Temp(GPIB_ADDRESS_DMM1, GPIB_ADDRESS_DMM2, GPIB_ADDRESS_DMM3)   
        
        if State_of_Program == "Medición":
            
            for index, row in Listado_de_Mediciones.iterrows():
                
                if State_of_sub_Program == "Inicio":
                    
                    # Estado inicial utilizado como punto de reinicio.
                    Dummy_1 = input("\nPresionar Enter para continuar...")
                    State_of_sub_Program = "Adquirir_Datos"
                
                if State_of_sub_Program == "Adquirir_Datos":
                    
                    # Toma los parámetros para la medición actual desde el DataFrame
                    Tomar_Parametros = row.to_dict()
                    
                    RS_NOMBRE           = Tomar_Parametros['Rs_Nombre']
                    RX_NOMBRE           = Tomar_Parametros['Rx_Nombre']
                    ENTRADA_S           = int(Tomar_Parametros['CH_Rs'])
                    ENTRADA_X           = int(Tomar_Parametros['CH_Rx'])
                    RS                  = float(Tomar_Parametros['Rs_Nominal'])
                    RX                  = float(Tomar_Parametros['Rx_Nominal'])
                    IX                  = float(Tomar_Parametros['Ix'])
                    TIME_REVERSAL       = float(Tomar_Parametros['t_inv'])
                    NUM_MEASUREMENTS    = int(Tomar_Parametros['Cant_Med'])
                    NUM_STATISTICS      = int(Tomar_Parametros['Cant_Med_Est']) 
                    TIEMPO_DELAY        = int(Tomar_Parametros['Delay'])
                    
                    
                    State_of_sub_Program = "Análisis_Datos"

                if State_of_sub_Program == "Análisis_Datos":

                    # Cargar datos del resistor calibrado desde la base de datos JSON
                    RS_Calibrado = Manejo_Archivos.Func_Data.Cargar_Resistor_Calibrado(RS_NOMBRE)
                    
                    if RS_Calibrado:
                        
                        # Asignar los valores del resistor calibrado a variables
                        RS_valor  = float(RS_Calibrado.get("valor"))
                        RS_serial = RS_Calibrado.get("serial")
                        RS_Psmax  = float(RS_Calibrado.get("Potencia_maxima_de_disipacion"))
            
                        print("=" * 90)
                        print(f"  Datos cargados:")
                        print(f"  Resistor patrón: {RS_NOMBRE}")
                        print(f"  Valor Nominal  : {RS_valor} Ω")
                        print(f"  Número de Serie: {RS_serial}")
                        print("=" * 90)
                      
                    else:
                        print(f"\nNo se pudieron cargar los datos de '{RS_NOMBRE}'")
                        State_of_sub_Program = "Abrir_Canales"
                        continue
                    
                    State_of_sub_Program = "Conf_Escaner"
                    
                if State_of_sub_Program == "Conf_Escaner":    
                    
                    print("=" * 90) 
                    print(f"\nIniciando medición {index + 1} de {Cantidad_Mediciones}...")  
                    print("=" * 90)
                    print(f"\nENTRADA_S asignada a canal: {ENTRADA_S}")
                    print(f"ENTRADA_X asignada a canal: {ENTRADA_X}")
                    # Inicializa el Scanner y configura canales de forma segura
                    Scanner = ScannerInti(f"GPIB0::{GPIB_ADDRESS_ESCA}::INSTR")
                                    
                    # Asegurar estado inicial con todos los canales abiertos
                    Driver_EscanerINTI.Abrir_Canales(Scanner) 
                    sleep(3)
                    State_of_sub_Program = Driver_EscanerINTI.Conectar_Entradas_Salidas(Scanner, ENTRADA_S,ENTRADA_X)
                    # Cambiar al estado de Análisis después de conectar
                                                    
                if State_of_sub_Program == "Medición_N":
                    
                    if Measurement_MI6010D.Check_de_Seguridad(RS, RX, IX, RS_Psmax):
                        
                        ratio_aux, des_ratio_aux,dmm1_aux,des_dmm1_aux, dmm2_aux, des_dmm2_aux, dmm3_aux, des_dmm3_aux = Measurement_MI6010D.Measure_with_Temp(GPIB_ADDRESS_BRID, 
                                                                                                                            RS, 
                                                                                                                            TIME_REVERSAL, 
                                                                                                                            IX, NUM_MEASUREMENTS, 
                                                                                                                            NUM_STATISTICS, 
                                                                                                                            DMM_NAME_1, 
                                                                                                                            GPIB_DMM1, DMM_NAME_2, 
                                                                                                                            GPIB_DMM2, 
                                                                                                                            DMM_NAME_3, 
                                                                                                                            GPIB_DMM3, 
                                                                                                                            Cant_Sensores)

                    
                        State_of_sub_Program = "Abrir_Canales"
                        
                    else:
                        
                        print("Condición de seguridad no cumplida. Saltando medición.")
                        
                        State_of_sub_Program = "Abrir_Canales"

                             
                if State_of_sub_Program == "Abrir_Canales":
                    
                    Driver_EscanerINTI.Cerrar_Escaner(Scanner)
                    
                    State_of_sub_Program = "Guardar_Datos"
                
                if State_of_sub_Program == "Guardar_Datos":
                    
                    Manejo_Archivos.Func_Data.Guarda_Medicion(  RS_NOMBRE,
                                                                RX_NOMBRE,
                                                                IX,
                                                                [ratio_aux],
                                                                [des_ratio_aux],
                                                                [dmm1_aux],
                                                                [des_dmm1_aux],
                                                                [dmm2_aux],
                                                                [des_dmm2_aux],
                                                                [dmm3_aux],
                                                                [des_dmm3_aux],
                                                                Ruta_Salida)
                    State_of_sub_Program = "Delay_Mediciones"
                
                if State_of_sub_Program == "Delay_Mediciones":
                    
                    TIEMPO_DELAY = int(float(Tomar_Parametros['Delay']))

                    print("Presione '1' para omitir la espera...\n")

                    for i in range(TIEMPO_DELAY, 0, -1):
                        print(f"Esperando... {i} s", end="\r", flush=True)

                        # Espera en pequeños pasos para poder detectar tecla
                        for _ in range(10):  # 10 x 0.1s = 1 segundo
                            sleep(0.1)

                            if msvcrt.kbhit():  # tecla presionada
                                tecla = msvcrt.getch().decode("utf-8")

                                if tecla == "1":
                                    print("\n⏩ Delay omitido por el usuario")
                                    
                                    # limpiar buffer hasta Enter
                                    while msvcrt.kbhit():
                                        msvcrt.getch()
                                    
                                    State_of_sub_Program = "Adquirir_Datos"
                                    break
                        else:
                            continue  # sigue el for externo
                        
                        break  # rompe si se presionó tecla

                    else:
                        # terminó normalmente la cuenta regresiva
                        State_of_sub_Program = "Adquirir_Datos"

                    print(" " * 40, end="\r")
                    
                    State_of_sub_Program = "Adquirir_Datos"
                    
                else:
                    print("Estado no reconocido, reiniciando programa...")
                    # Cerrar sesión de todos los instrumentos para evitar recursos abiertos
                    if 'Scanner' in locals() and Scanner is not None:
                        Scanner.close()
                        del Scanner
                    State_of_Program = "Final"
                    State_of_sub_Program = "Inicio"
                    break
             
            # Al finalizar todas las mediciones, reinicio variable.      
            State_of_sub_Program = "Inicio"
        
        
        State_of_Program = "Calibrar"

        if State_of_Program == "Calibrar":                     
            s=input("\nIniciando proceso de calibración...")
            State_of_Program = "Final"
                                  
        if State_of_Program == "Final":
                    
             State_of_Program = Manejo_Archivos.Func_Data.Final_Menu()
                                                    

if __name__ == "__main__":

    main()