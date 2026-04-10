################################################## LIBRERIAS #########################################################
import csv
import os
import sys 
import json
from time import sleep
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
from scipy.stats import linregress
from pathlib import Path
from datetime import datetime


#####################################################################################################################
def Welcome_Menu():
    limpiar_pantalla()
    limpiar_teclado()
    print("=" * 60)
    print("#   Sistema de medición y calibración de resistores de precisión ScannerINTI-MI6010D v1.0 ")    
    print("#   Autor: NSB")   
    print("#   Año  : 2026")      
    print("=" * 60)
    while True:
        opcion = input("\nPresionar 1 para iniciar medición o 2 para cerrar: ")
        limpiar_pantalla() 
        if opcion == "1":
            Estado = "Lectura_Parametros"
            break
        if opcion == "2":
            sys.exit()  
        else:
            limpiar_pantalla()
            print("Elección incorrecta.") 
    return Estado
##################################################################################################################### 

def Final_Menu():
    limpiar_teclado()
    while True:
        opcion = input("\nPresionar 1 para volver al menú principal o 2 para cerrar: ")  
        limpiar_pantalla() 
        if opcion == "1":
            Estado = "Inicio"
            break
        if opcion == "2":
            sys.exit()  
        else:
            limpiar_pantalla()
            print("Elección incorrecta.") 
    return Estado
#####################################################################################################################     

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')


def limpiar_teclado():
    try:
        import termios
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
    except:
        pass  # en Windows no existe termios
#####################################################################################################################

def Menu_Inicial():
    
    print("--- Modo de aplicación ---\n") 
    print("1. Medir y calibrar")
    print("2. Calcular desde una medición ya existente")
    while True:
            
            opcion = input("Introducir modo (1 o 2):")
            if opcion ==   '1' :
                break
                 
            elif opcion == '2':
                break
            
            else:
                limpiar_pantalla()
                print("--- Modo de aplicación ---\n") 
                print("1. Medir y calibrar")
                print("2. Calcular desde una medición ya existente")
                      
    return opcion   
#####################################################################################################################

def Ruta_de_analisis_existente():
    # --- pedir y validar ruta del generador ---
    limpiar_pantalla()
    while True:
        ruta_generador_str = input("Introducir la ruta de archivo de medición de generador:\n")
        ruta_generador = Path(ruta_generador_str)
        if ruta_generador.exists():
            ruta_generador = ruta_generador.resolve()  # normalizar ruta absoluta
            break
        else:
            print("⚠️ La ruta no existe o está mal escrita. Intente de nuevo.\n")

    # --- pedir y validar ruta de la curva de carga ---
    while True:
        ruta_curva_carga_str = input("Introducir la ruta de archivo de medición de curva de carga:\n")
        ruta_curva_carga = Path(ruta_curva_carga_str)
        if ruta_curva_carga.exists():
            ruta_curva_carga = ruta_curva_carga.resolve()
            break
        else:
            print("⚠️ La ruta no existe o está mal escrita. Intente de nuevo.\n")

    while True:
        ruta_curva_config_str = input("Introducir la ruta del archivo de configuración:\n")
        ruta_curva_config = Path(ruta_curva_config_str)
        if ruta_curva_config.exists():
            ruta_curva_config= ruta_curva_config.resolve()
            break
        else:
            print("⚠️ La ruta no existe o está mal escrita. Intente de nuevo.\n")

    # --- obtener nombres de archivo ---
    nombre_archivo_generador = ruta_generador.name  # solo el nombre con extensión
    nombre_archivo_curva = ruta_curva_carga.name
    nombre_archivo_config = ruta_curva_config.name

    return (str(ruta_generador), str(ruta_curva_carga),str(ruta_curva_config),
            nombre_archivo_generador, nombre_archivo_curva, nombre_archivo_config)

#####################################################################################################################
def extraccion_datos(ruta_json):
    """
    Lee un archivo JSON y devuelve los valores:
    Vn_Cx, Vn_Rp, Vn_Tau, Frec, Sweep_time
    """
    ruta = Path(ruta_json)
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_json}")
    
    with open(ruta, "r") as file:
        datos = json.load(file)
    
    try:
        Modo   = datos["Modo"]
        Vn_Cx  = datos["Vn_Cx"]
        Vn_Rp  = datos["Vn_Rp"]
        Vn_Tau = datos["Vn_Tau"]
        Frec   = datos["Frec"]
        Sweep_time = datos["Sweep_time"]
    except KeyError as e:
        raise KeyError(f"Falta el campo {e} en el archivo JSON: {ruta_json}")
    
    return Modo,Vn_Cx, Vn_Rp, Vn_Tau, Frec, Sweep_time

#####################################################################################################################

def Creacion_Directorio_Salida(RS, RX, IX, TIME_REVERSAL, NUM_MEASUREMENTS, NUM_STATISTICS):
    # Base de ejecución
    base_path = Path(__file__).parent

    # Timestamp para nombre del archivo
    fecha_actual = datetime.datetime.now()
    nombre_archivo = fecha_actual.strftime("Medicion_%Y-%m-%d_%H-%M-%S.txt")
    nombre_archivo_config = fecha_actual.strftime("Medicion_%Y-%m-%d_%H-%M-%S.json")
 
    # Carpetas
    Mediciones = base_path / "Mediciones" 
    
    # Subcarpetas
    Mediciones_Resistencia  = Mediciones / f"Rs_{RS}ohm"
    Mediciones_Temperatura  = Mediciones / "Temperatura"
    
     # Crear carpetas necesarias
    Mediciones.mkdir(parents=True, exist_ok=True)
    Mediciones_Resistencia.mkdir(parents=True, exist_ok=True)
    Mediciones_Temperatura.mkdir(parents=True, exist_ok=True)
    
    # Ruta final del archivo de Medición
    Ruta_medicion_resistencia = Mediciones_Resistencia / nombre_archivo
    Ruta_medicion_temperatura = Mediciones_Temperatura / nombre_archivo
    
    print(f"Archivo de medición guardado en: {Ruta_medicion_resistencia}")
    print(f"Archivo de configuración guardado en: {Ruta_medicion_temperatura}")

#####################################################################################################################
def Menu_Config():   
    
    print("\n---- Menú de Configuración ----\n")  
      
    while True:
        Vn_capacitor   = input("Valor nominal del capacitor de transferencia (Cx) en microfarad: ")
        if Vn_capacitor.isdigit():
            Vn_capacitor_int = int(Vn_capacitor) 
            break
        else:
            print("Eso no es un número válido.")   
     
    while True:
        Vn_resistencia = input("Valor nominal del resistor patrón (Rp) en ohm: ")
        if Vn_resistencia .isdigit():
            Vn_resistencia_int = int(Vn_resistencia) 
            break
        else:
            print("Eso no es un número válido.")   
    
    tau_x_ciclo = 5

    return Vn_capacitor_int, Vn_resistencia_int, tau_x_ciclo


def Mostrar_Configuracion(Rx, Rs, Ix, Is, T_inv, Cant_Med, Cant_Stat):
    
    Is= Ix * Rs / Rx  # Corriente en Rs usando divisor de corriente
    print("\n--- Resumen de configuración ---\n") 
    print(f"Se medirá un RX de valor nominal: {Rx} ohm")
    print(f"Se utilizará un Rs de valor nominal: {Rs} ohm")
    print(f"La corriente aplicada en Rx será: {Ix} ohm")
    print(f"La corriente aplicada en Rs será: {Is} ohm")
    print(f"El tiempo de inversión será: {T_inv} segundos")
    print(f"Se realizarán {Cant_Med} mediciones, con {Cant_Stat} estadísticas cada una")
   
    return 

###################################################################################################################

def Menu_Final():
    """ Menú final después de la calibración """
    limpiar_pantalla()
    print("La calibración ha finalizado.")
    while True: 
            select_final = input("\nPresionar 1 para volver al menú principal o 2 para cerrar: ")  
            limpiar_pantalla() 
            if select_final == "1":
                return "INICIO"
            elif select_final == "2":
                sys.exit()   
            else:
                limpiar_pantalla()
                print("Elección incorrecta.")



def Save_Data(Name_M,Path_Output, Rs, Rx, Ix, T_Invertion, Num_Med, Num_Stat,
              Mea_Res=None, Mea_Temp1=None, Mea_Temp2=None):
    """
    Guardar los datos de la medición en un archivo CSV
    """

    if None not in (Path_Output, Rs, Rx, Ix, T_Invertion, Num_Med):

        parametros = {
            "Resistor Patrón ('Rs')" : Rs,
            "Resistor Medido ('Rx')" : Rx,
            "Corriente aplicada a Rx": Ix,
            "Tiempo de inversión"    : T_Invertion,
            "Número de mediciones"   : Num_Med,
            "Número de estadísticas" : Num_Stat
        }

        ruta_csv = Path(Path_Output).with_suffix(".csv")

        with open(ruta_csv, "w", newline="") as csv_file:

            # ---- Guardar parámetros ----
            writer = csv.DictWriter(csv_file, fieldnames=parametros.keys())
            writer.writeheader()
            writer.writerow(parametros)

            # Línea vacía para separar
            csv_file.write("\n")

            # ---- Preparar columnas de medición ----
            columnas = {}
            if Mea_Res not in (None, 0, []):
                columnas["Resistencia"] = Mea_Res

            if Mea_Temp1 not in (None, 0, []):
                columnas["Temp1"] = Mea_Temp1

            if Mea_Temp2 not in (None, 0, []):
                columnas["Temp2"] = Mea_Temp2

            # Si hay datos de medición
            if columnas:
                fieldnames = list(columnas.keys())
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()

                # número máximo de filas
                n = max(len(v) for v in columnas.values())

                for i in range(n):
                    fila = {}
                    for k, v in columnas.items():
                        fila[k] = v[i] if i < len(v) else ""
                    writer.writerow(fila)

###################################################################################################################
def Set_Directories(cliente, nombre_resistor):
    try:
        # Base de ejecución
        base_path = Path(__file__).parent

        # Fecha actual
        now = datetime.now()
        mes_anio = now.strftime("%m-%Y")

        # Construcción de rutas
        mediciones = base_path / "Mediciones"
        cliente_path = mediciones / cliente
        resistor_path = cliente_path / nombre_resistor
        fecha_path = resistor_path / mes_anio
        config_path = fecha_path / "CONFIG"
        datos_path = fecha_path / "DATOS"

        rutas = [
            mediciones,
            cliente_path,
            resistor_path,
            fecha_path,
            config_path,
            datos_path
        ]

        mensajes = []

        # Crear carpetas si no existen
        for ruta in rutas:
            if ruta.exists():
                mensajes.append(f"Ya existía: {ruta}")
            else:
                ruta.mkdir(parents=True, exist_ok=True)
                mensajes.append(f"Creada: {ruta}")

        print("\n----- Resultado -----")
        for m in mensajes:
            print(m)

        return {
            "mediciones": str(mediciones),
            "cliente": str(cliente_path),
            "resistor": str(resistor_path),
            "fecha": str(fecha_path),
            "config": str(config_path),
            "datos": str(datos_path)
        }

    except Exception as e:
        print("Error al crear las carpetas:", e)
        return None


def Config_Rx():
    while True:

        Client_input = input("Ingrese el nombre de cliente: ")
        if Client_input.isdigit():
            Client_Rx = int(Client_input)
            print(f"El cliente es: {Client_Rx}")           
        else:
            print("Valor no válido. Por favor, ingrese un número entero.")

        Rx_nom_input = input("Ingrese el valor nominal de Rx en ohm: ")
        if Rx_nom_input.isdigit():
            Rx_nom = int(Rx_nom_input)
            print(f"El valor nominal de Rx es: {Rx_nom}")           
        else:
            print("Valor no válido. Por favor, ingrese un número entero.")

        Name_input = input("Ingrese el valor nominal de Rx en ohm: ")
        if Name_input.isdigit():
            Name_Rx = int(Name_input)
            print(f"La fecha es: {Name_Rx}")           
        else:
            print("Valor no válido. Por favor, ingrese un número entero.")

        Name_input = input("Ingrese el nombre del resistor: ")
        if Name_input.isdigit():
            Name_Rx = int(Name_input)
            print(f"El nombre del resistor es: {Name_Rx}")           
        else:
            print("Valor no válido. Por favor, ingrese un número entero.")

        Rx_input = input("Ingrese el valor nominal de Rx en ohm: ")
        if Rx_input.isdigit():
            Rx = int(Rx_input)
            print(f"Rx configurado a {Rx} ohm")           
        else:
            print("Valor no válido. Por favor, ingrese un número entero.")

        Ix_input = input("Ingrese el valor nominal de Ix en A: ")
        if Ix_input.isdigit():
            Ix = int(Ix_input)
            print(f"Ix configurado a {Ix} A")           
        else:
            print("Valor no válido. Por favor, ingrese un número entero.")
            
        return Rx

def Lectura_Parametros():    
    
    print("\n---- Lectura de parámetros ----\n")  
    while True:
                
            Ruta_entrada = input("Ingrese la ruta completa del archivo de parámetros (CSV): ")
            Ruta = Path(Ruta_entrada)
    
            if not Ruta.exists():
        
                opcion = input("Ruta mal escrita o archivo no encontrado.\nPresionar 2 para salir o cualquier otra tecla para intentar de nuevo: ")
                if opcion == "2":
                    sys.exit()  
            else:
                break
    
    with open(Ruta, "r") as file:    
        # Leer el archivo CSV y almacenar los datos en una lista de listas
        datos = csv.reader(file)
        
        listado_listas = []
        # Convertir cada fila del CSV en una lista y agregarla a la lista principal
        for fila in datos:
            listado_listas.append(fila)
        
        # Crear DataFrame
        columnas = ['ID_Rs', 'ID_Rx', 'Ix [mA]', 'Tiempo_Inversion [s]', 'VN_Rs [ohm]', 'Cant_Mediciones', 'Cant_Estadistica', 'Ch_Rs', 'Ch_Rx', 'Bit_Control']        
        # Ordenamiento de información en DataFrame para facilitar su procesamiento.
        df = pd.DataFrame(listado_listas, columns=columnas)
        
        # Variable global para cantidad de Mediciones
        Cantidad_filas = len(df)


    return "Medición",df,Cantidad_filas


def Cargar_Resistor_Calibrado(RS_NOMBRE):
    """
    Busca un resistor en el archivo Base 16-03-26.json por nombre
    Si lo encuentra, devuelve un diccionario con sus propiedades
    Si no lo encuentra, devuelve None
    """
    ruta_base = Path(__file__).parent.parent
    ruta_json = ruta_base / "Base 16-03-26.json"
    
    if not ruta_json.exists():
        print(f"Archivo no encontrado: {ruta_json}")
        return None
    
    try:
        with open(ruta_json, "r") as file:
            datos = json.load(file)
        
        # Buscar el resistor por nombre
        for resistor in datos:
            if resistor.get("Nombre") == RS_NOMBRE:
                print(f"\n✓ Resistor '{RS_NOMBRE}' encontrado en base de datos")
                return resistor
        
        print(f"\n✗ Resistor '{RS_NOMBRE}' NO encontrado en base de datos")
        return None
        
    except json.JSONDecodeError as e:
        print(f"Error al leer el archivo JSON: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

