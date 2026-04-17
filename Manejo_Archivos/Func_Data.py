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
import datetime


#####################################################################################################################
def Welcome_Menu():
    limpiar_pantalla()
    limpiar_teclado()
    print("=" * 90)
    print("#   Sistema de medición y calibración de resistores de precisión ScannerINTI-MI6010D v1.0 ")  
    print("#   Departamento de Metrología Cuántica - INTI")     
    print("#   Autor: Sr. Nicolás S. Brunella")   
    print("#   Última corrección : Abril 2026")      
    print("=" * 90)
    while True:
        opcion = input("\nPresionar 1 para iniciar medición o 2 para cerrar: ")
        print("=" * 90)
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
    
    print("=" * 90)
    print("\n       Lectura de parámetros       \n")  
    print("=" * 90)

    # -------------------------------
    # RUTA DE ENTRADA (CSV)
    # -------------------------------
    while True:
        print("Ingrese la ruta del archivo CSV con los parámetros de medición:\n")
        Ruta_entrada = input().strip()
        ruta_csv = Path(Ruta_entrada)

        if not ruta_csv.exists():
            print("❌ El archivo no existe. Intente nuevamente.\n")
            continue

        if not ruta_csv.is_file():
            print("❌ La ruta no corresponde a un archivo.\n")
            continue

        break

    # Leer CSV
    df = pd.read_csv(ruta_csv)
    Cantidad_filas = len(df)

    # -------------------------------
    # RUTA DE SALIDA (DIRECTORIO)
    # -------------------------------
    while True:
        print("\nIngrese la carpeta donde quiere guardar la medición:\n")
        Ruta_salida = input().strip()
        ruta_salida = Path(Ruta_salida)

        if ruta_salida.exists():
            if ruta_salida.is_dir():
                break
            else:
                print("❌ La ruta existe pero no es una carpeta.\n")
                continue
        else:
            try:
                ruta_salida.mkdir(parents=True, exist_ok=True)
                print("📁 Carpeta creada correctamente.\n")
                break
            except Exception as e:
                print(f"❌ No se pudo crear la carpeta: {e}\n")
                continue

    return "Seleccion_Instrumentos", df, Cantidad_filas, ruta_salida


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
                print(f"\nResistor '{RS_NOMBRE}' encontrado en base de datos")
                return resistor
        
        print(f"\n✗ Resistor '{RS_NOMBRE}' NO encontrado en base de datos")
        return None
        
    except json.JSONDecodeError as e:
        print(f"Error al leer el archivo JSON: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def limpiar_nombre(nombre):
    return nombre.replace(" ", "_").replace("/", "-")


def Guarda_Medicion(RS_NOMBRE, RX_NOMBRE, Ix,
                   Medicion_Ratio, Desvio_Ratio,
                   Medicion_dmm1, Desvio_dmm1,
                   Medicion_dmm2, Desvio_dmm2,
                   Medicion_dmm3, Desvio_dmm3,
                   Ruta_Salida):

    # Sanitizar nombres
    rs = limpiar_nombre(RS_NOMBRE)
    rx = limpiar_nombre(RX_NOMBRE)

    ahora = datetime.datetime.now()
    fecha_str = ahora.strftime('%Y-%m-%d')

    # Nombre de archivo con formato pedido
    nombre_archivo = f"{rs}_vs_{rx}_a_{Ix}mA-{fecha_str}.csv"
    #ruta_salida = Path(__file__).parent / nombre_archivo

    ruta_salida = Ruta_Salida / nombre_archivo
    
    # Verificar si ya existe
    archivo_existe = ruta_salida.exists()

    with open(ruta_salida, "a", newline="") as csvfile:
        fieldnames = [
            "timestamp",
            "Medicion_Ratio", "Desvio_Ratio",
            "Medicion_dmm1", "Desvio_dmm1",
            "Medicion_dmm2", "Desvio_dmm2",
            "Medicion_dmm3", "Desvio_dmm3"
        ]

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Escribir encabezado solo si es nuevo
        if not archivo_existe:
            writer.writeheader()

        # Timestamp con hora:minuto:segundo
        timestamp = ahora.strftime("%H:%M:%S")

        for ratio, desvio_ratio, dmm1, desvio_dmm1, dmm2, desvio_dmm2, dmm3, desvio_dmm3 in zip(
            Medicion_Ratio, Desvio_Ratio,
            Medicion_dmm1, Desvio_dmm1,
            Medicion_dmm2, Desvio_dmm2,
            Medicion_dmm3, Desvio_dmm3
        ):
            writer.writerow({
                "timestamp": timestamp,
                "Medicion_Ratio": ratio,
                "Desvio_Ratio": desvio_ratio,
                "Medicion_dmm1": dmm1,
                "Desvio_dmm1": desvio_dmm1,
                "Medicion_dmm2": dmm2,
                "Desvio_dmm2": desvio_dmm2,
                "Medicion_dmm3": dmm3,
                "Desvio_dmm3": desvio_dmm3
            })

    print(f"Resultados guardados en: {ruta_salida}\n")
    print("=" * 90) 