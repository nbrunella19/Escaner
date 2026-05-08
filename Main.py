#################################################################################################################
#   Archivo: Main.py    
#   Descripción: Script principal que orquesta la ejecución del programa, gestionando el flujo de estados y tareas
#   Autor: NSB
#################################################################################################################

import sys
import time
from time import sleep, time
from turtle import delay
import datetime
from Instrumental import Scanner
import Manejo_Archivos.Func_Data
import Measurement_MI6010D
from Measurement_MI6010D import Measure_with_Temp
from Menu_Temp import Menu_Temp
import Driver_EscanerINTI   
from Instrumental.Scanner import ScannerInti
from pathlib import Path
import pandas as pd

 # Importamos el script de prueba para verificar la conectividad antes de iniciar el programa principal

sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
   
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
      
    Estado_Programa = "Inicio"  
    #Estado_Programa = "Procesamiento_Datos"
    
    while True:
        
        # Estado dedicado a mostrar el menú de bienvenida
        if Estado_Programa == "Inicio":
            
            Estado_Programa = Manejo_Archivos.Func_Data.Welcome_Menu()

        if Estado_Programa == "Lectura_Parametros":
            
            Estado_Programa, Listado_de_Mediciones, Cantidad_Mediciones, Ruta_Salida = Manejo_Archivos.Func_Data.Lectura_Parametros()
                                                                 
        
        if Estado_Programa == "Seleccion_Instrumentos":
            
            Estado_Programa, GPIB_DMM1, GPIB_DMM2, GPIB_DMM3, Cant_Sensores, Configuracion = Menu_Temp(GPIB_ADDRESS_DMM1, GPIB_ADDRESS_DMM2, GPIB_ADDRESS_DMM3)   
                  
        if Estado_Programa == "Medición":

            for Fila_leida, row in Listado_de_Mediciones.iterrows():

                Estado_Sub_Programa = "Inicio"

                while Estado_Sub_Programa != "Fin":

                    # =========================
                    # INICIO
                    # =========================
                    if Estado_Sub_Programa == "Inicio":
                        Estado_Sub_Programa = "Adquirir_Datos"

                    # =========================
                    # ADQUIRIR DATOS (CSV)
                    # =========================
                    elif Estado_Sub_Programa == "Adquirir_Datos":

                        Tomar_Parametros = row.to_dict()

                        RS_NOMBRE        = Tomar_Parametros['Rs_Nombre']
                        RX_NOMBRE        = Tomar_Parametros['Rx_Nombre']
                        ENTRADA_S        = int(Tomar_Parametros['CH_Rs'])
                        ENTRADA_X        = int(Tomar_Parametros['CH_Rx'])
                        RS               = float(Tomar_Parametros['Rs_Nominal'])
                        RX               = float(Tomar_Parametros['Rx_Nominal'])
                        IX               = float(Tomar_Parametros['Ix'])
                        TIME_REVERSAL    = float(Tomar_Parametros['t_inv'])
                        NUM_MEASUREMENTS = int(Tomar_Parametros['Cant_Med'])
                        NUM_STATISTICS   = int(Tomar_Parametros['Cant_Med_Est'])
                        Tiempo_Espera    = int(Tomar_Parametros['Delay'])

                        Sensor_1 = str(Configuracion["sensores"][0] if len(Configuracion["sensores"]) > 0 else None)
                        Sensor_2 = str(Configuracion["sensores"][1] if len(Configuracion["sensores"]) > 1 else None)
                        Sensor_3 = str(Configuracion["sensores"][2] if len(Configuracion["sensores"]) > 2 else None)

                        lista_sensores = [Sensor_1, Sensor_2, Sensor_3]

                        Estado_Sub_Programa = "Analisis_Datos"

                    # =========================
                    # ANALISIS DATOS
                    # =========================
                    elif Estado_Sub_Programa == "Analisis_Datos":

                        Lectura_Rs_Ok, Rs_data = Manejo_Archivos.Func_Data.Cargar_Resistor_Calibrado(RS_NOMBRE)

                        Lectura_Sensores_Ok, Sensores_Seleccionados = Manejo_Archivos.Func_Data.Cargar_Sensores(
                            lista_sensores,
                            Cant_Sensores
                        )

                        if Lectura_Sensores_Ok and Lectura_Rs_Ok:
                            Estado_Sub_Programa = "Setear_Escaner"
                        else:
                            Estado_Sub_Programa = "Error"

                    # =========================
                    # SETEAR ESCANER
                    # =========================
                    elif Estado_Sub_Programa == "Setear_Escaner":

                        Scanner = ScannerInti(f"GPIB0::{GPIB_ADDRESS_ESCA}::INSTR")

                        Driver_EscanerINTI.Abrir_Canales(Scanner)

                        Check_Entrada_Salida = Driver_EscanerINTI.Conectar_Entradas_Salidas(
                            Scanner, ENTRADA_S, ENTRADA_X
                        )

                        Check_Seguridad_Elec = Measurement_MI6010D.Check_de_Seguridad(
                            RS, RX, IX, Rs_data["Pmax"]
                        )

                        if Check_Entrada_Salida and Check_Seguridad_Elec:
                            Estado_Sub_Programa = "Medicion_N"
                        else:
                            Estado_Sub_Programa = "Error"

                    # =========================
                    # MEDICIÓN
                    # =========================
                    elif Estado_Sub_Programa == "Medicion_N":

                        (
                            Hora_Medicion, Rx_Rs,
                            Hora_Medicion_DMM1, dmm1_aux,
                            Hora_Medicion_DMM2, dmm2_aux,
                            Hora_Medicion_DMM3, dmm3_aux
                        ) = Measurement_MI6010D.Measure_with_Temp(
                            GPIB_ADDRESS_BRID,
                            RS,
                            TIME_REVERSAL,
                            IX,
                            NUM_MEASUREMENTS,
                            NUM_STATISTICS,
                            DMM_NAME_1,
                            GPIB_DMM1,
                            DMM_NAME_2,
                            GPIB_DMM2,
                            DMM_NAME_3,
                            GPIB_DMM3,
                            Cant_Sensores
                        )

                        Driver_EscanerINTI.Cerrar_Escaner(Scanner)

                        Estado_Sub_Programa = "Guardar_Datos"

                    # =========================
                    # GUARDAR DATOS
                    # =========================
                    elif Estado_Sub_Programa == "Guardar_Datos":

                        Ruta_Salida_Full = Manejo_Archivos.Func_Data.Guarda_Medicion(
                            Rs_data,
                            RS_NOMBRE,
                            RX_NOMBRE,
                            IX,
                            Hora_Medicion,
                            Rx_Rs,
                            Hora_Medicion_DMM1,
                            dmm1_aux,
                            Hora_Medicion_DMM2,
                            dmm2_aux,
                            Hora_Medicion_DMM3,
                            dmm3_aux,
                            Ruta_Salida,
                            Sensores_Seleccionados
                        )

                        Manejo_Archivos.Func_Data.Delay_Interactivo(Tiempo_Espera)

                        Estado_Sub_Programa = "Fin"

                    # =========================
                    # ERROR
                    # =========================
                    elif Estado_Sub_Programa == "Error":

                        print("❌ Error en la medición. Saltando a la siguiente fila.")

                        try:
                            Driver_EscanerINTI.Cerrar_Escaner(Scanner)
                            if Scanner:
                                Scanner.close()
                        except:
                            pass

                        Estado_Sub_Programa = "Fin"

                    # =========================
                    # ESTADO DESCONOCIDO
                    # =========================
                    else:
                        print("⚠️ Estado no reconocido.")
                        print(Estado_Sub_Programa)
                        a=input("Presione Enter para continuar...")
                        Estado_Sub_Programa = "Error"
            
            Estado_Programa = "Procesamiento_Datos"
            
        if Estado_Programa == "Procesamiento_Datos":  
            
            
            
            ruta = Path(Ruta_Salida)
            Resultados_Generales = []

            for archivo in ruta.glob("*.csv"):

                print(f"\nProcesando: {archivo.name}")

                Mediciones = Manejo_Archivos.Func_Data.Leer_Mediciones_Estructuradas(
                    archivo, NUM_STATISTICS
                )

                Resultados = Manejo_Archivos.Func_Data.Procesar_Medicion(
                    Mediciones
                )

                Resultados_Generales.extend(Resultados)                  

            Estado_Programa = Manejo_Archivos.Func_Data.Preguntar_Si_No("Se han procesado los datos. ¿Desea generar el resumen global?")  
        
        if Estado_Programa == "Calibracion":
            
            Resultados_Analizados  = Manejo_Archivos.Func_Data.Agrupar_Mediciones(Resultados_Generales)  
            
            Manejo_Archivos.Func_Data.Imprimir_Resultados_Analizados(Resultados_Analizados)
            
            Manejo_Archivos.Func_Data.crear_dataframe_resultados(Resultados_Analizados, Ruta_Salida)
            
            Estado_Programa = "Final"
            
        if Estado_Programa == "Final":
                    
             Estado_Programa = Manejo_Archivos.Func_Data.Final_Menu()
                                                    

if __name__ == "__main__":

    main()