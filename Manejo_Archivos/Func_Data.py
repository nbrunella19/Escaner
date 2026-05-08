################################################## LIBRERIAS #########################################################
import os
import re
import csv
import sys 
import json
import math
import time
import msvcrt
import datetime
from datetime import timedelta
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
from time import sleep
from pathlib import Path
from itertools import zip_longest
from scipy.stats import linregress
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
    # Hasta Acá todo ok
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


def Cargar_Base_De_Datos(RS_NOMBRE):
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

def Guarda_Medicion(
                    Rs_Data,
                    RS_NOMBRE, 
                    RX_NOMBRE, 
                    Ix,
                    Hora_Medicion,
                    Medicion_Relacion,
                    Hora_Medicion_DMM1,
                    Medicion_dmm1, 
                    Hora_Medicion_DMM2,
                    Medicion_dmm2, 
                    Hora_Medicion_DMM3,
                    Medicion_dmm3, 
                    Ruta_Salida,
                    Sensores_Seleccionados):

    # Sanitizar nombres
    rs = limpiar_nombre(RS_NOMBRE)
    rx = limpiar_nombre(RX_NOMBRE)

    ahora = datetime.datetime.now()
    fecha_str = ahora.strftime('%Y-%m-%d')

    nombre_archivo = f"{rs}_vs_{rx}_a_{Ix}mA-{fecha_str}.csv"
    Ruta_Salida_Full = Ruta_Salida / nombre_archivo

    archivo_existe = Ruta_Salida_Full.exists()

    with open(Ruta_Salida_Full, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)

        # =========================================
        # SI EL ARCHIVO ES NUEVO → escribir headers
        # =========================================
        if not archivo_existe:

            # Metadata opcional
            writer.writerow([f"# Rs: {RS_NOMBRE}"])
            writer.writerow([f"# Rx: {RX_NOMBRE}"])
            writer.writerow([f"# Ix: {Ix} mA"])
            writer.writerow([])

            # =========================================
            # BLOQUE SENSORES
            # =========================================
            writer.writerow(["# Sensores de temperatura utilizados"])
            writer.writerow(["Sensor", "Nombre", "R0 [ohm]", "alfa [1/C]", "beta [1/C^2]", "T0 [C]"])
            for sensor, params in Sensores_Seleccionados.items():
                writer.writerow([
                    sensor,
                    params.get("Nombre", ""),
                    params.get("R0", ""),
                    params.get("alfa", ""),
                    params.get("beta", ""),
                    params.get("T0", "")
                ])
            writer.writerow([])

            # =========================================
            # BLOQUE VALORES DEL PATRÓN
            # =========================================
            Rs_Data = Cargar_Base_De_Datos(RS_NOMBRE)
            if Rs_Data:
                writer.writerow(["# Valores del resistor de referencia Rs"])
                writer.writerow(["Parametro", "Valor", "Unidad"])
                writer.writerow(["Valor", Rs_Data.get("valor", ""), "ohm"])
                writer.writerow(["Alfa", Rs_Data.get("alfa", ""), "1/C"])
                writer.writerow(["Beta", Rs_Data.get("beta", ""), "1/C^2"])
                writer.writerow(["T0", Rs_Data.get("T0", ""), "C"])
                writer.writerow([])
            else:
                writer.writerow(["# Valores del resistor de referencia Rs - No encontrado"])
                writer.writerow([])

            writer.writerow([f"# Medicion - {(datetime.datetime.now()).strftime('%Y-%m-%d-%H-%M-%S')}"])
            writer.writerow([])

            # BLOQUE PUENTE
            #writer.writerow(["# Datos del puente"])
            #writer.writerow(["Horario de Medicion", "Relacion Rx/Rs"])
        else:
        # =========================================
        # SI YA EXISTE → separar nueva medición
        # =========================================
            writer.writerow([])
            writer.writerow([f"# Nueva medicion - {(datetime.datetime.now()).strftime('%Y-%m-%d-%H-%M-%S')}"])
            writer.writerow([])
            
        
        # =========================================
        # AGREGAR DATOS DEL PUENTE
        # =========================================
        writer.writerow(["# Datos del puente"])
        writer.writerow(["Horario de Medicion", "Relacion Rx/Rs"])
        
        for h, r in zip(Hora_Medicion, Medicion_Relacion):
            writer.writerow([h, r])

        writer.writerow([])

        # =========================================
        # BLOQUE DMM
        # =========================================
        writer.writerow(["# Datos de los DMMs"])
        writer.writerow([
            "Horario DMM1", "Medicion DMM1 [ohm]",
            "Horario DMM2", "Medicion DMM2 [ohm]",
            "Horario DMM3", "Medicion DMM3 [ohm]"
            ])

        for h1, d1, h2, d2, h3, d3 in zip_longest(
            Hora_Medicion_DMM1,
            Medicion_dmm1,
            Hora_Medicion_DMM2,
            Medicion_dmm2,
            Hora_Medicion_DMM3,
            Medicion_dmm3,
            fillvalue=""
        ):
            writer.writerow([h1, d1, h2, d2, h3, d3])

        writer.writerow([])

    print(f"Resultados guardados en: {Ruta_Salida_Full}\n")
    print("=" * 90)
    return Ruta_Salida_Full
    
def Leer_Medicion_Completa(ruta_archivo, NUM_STATISTICS=None):
    ruta = Path(ruta_archivo)

    with open(ruta, "r") as f:
        lineas = [l.strip() for l in f.readlines()]

    mediciones = []
    i = 0
    metadata = {
        "Rs": "N/A",
        "Rx": "N/A",
        "Ix": "N/A",
        "Rs_patron": {
            "Valor": None,
            "Alfa": None,
            "Beta": None,
            "T0": None
        }
    }
    en_rs_patron = False

    # =========================
    # Leer metadata inicial
    # =========================
    while i < len(lineas):
        linea = lineas[i]

        if linea.startswith("# Rs:"):
            metadata["Rs"] = linea.split(":", 1)[1].strip()
            en_rs_patron = False
        elif linea.startswith("# Rx:"):
            metadata["Rx"] = linea.split(":", 1)[1].strip()
            en_rs_patron = False
        elif linea.startswith("# Ix:"):
            metadata["Ix"] = linea.split(":", 1)[1].strip()
            en_rs_patron = False
        elif linea.startswith("# Valores del resistor de referencia Rs"):
            en_rs_patron = True
        elif linea.startswith("# Medicion") or linea.startswith("# Nueva medicion"):
            break
        elif en_rs_patron and linea and not linea.startswith("#"):
            partes = [p.strip() for p in linea.split(",")]
            if len(partes) >= 2 and partes[0] in ("Valor", "Alfa", "Beta", "T0"):
                try:
                    metadata["Rs_patron"][partes[0]] = float(partes[1])
                except ValueError:
                    metadata["Rs_patron"][partes[0]] = partes[1]

        i += 1

    # =========================
    # Loop de mediciones
    # =========================
    while i < len(lineas):

        if not (lineas[i].startswith("# Medicion") or lineas[i].startswith("# Nueva medicion")):
            i += 1
            continue

        medicion_info = {
            "metadata": metadata.copy(),
            "timestamp": lineas[i],
            "puente": None,
            "dmm": None
        }

        i += 1

        # -------------------------
        # BLOQUE PUENTE
        # -------------------------
        while i < len(lineas) and "# Datos del puente" not in lineas[i]:
            i += 1

        i += 1  # título
        headers = lineas[i].split(",")
        i += 1

        datos = []
        while i < len(lineas) and lineas[i] and not lineas[i].startswith("#"):
            datos.append(lineas[i].split(","))
            i += 1

        df_puente = pd.DataFrame(datos, columns=headers)

        # 👉 Convertir a numérico
        df_puente["Relacion Rx/Rs"] = pd.to_numeric(
            df_puente["Relacion Rx/Rs"], errors="coerce"
        )

        # 👉 Eliminar NaN
        df_puente = df_puente.dropna(subset=["Relacion Rx/Rs"])

        # 👉 QUEDARSE SOLO CON LOS ÚLTIMOS N
        if NUM_STATISTICS is not None:
            df_puente = df_puente.tail(NUM_STATISTICS)

        medicion_info["puente"] = df_puente

        # -------------------------
        # BLOQUE DMM
        # -------------------------
        while i < len(lineas) and "# Datos de los DMMs" not in lineas[i]:
            i += 1

        i += 1
        headers = lineas[i].split(",")
        i += 1

        datos = []
        while i < len(lineas) and lineas[i] and not lineas[i].startswith("#"):
            datos.append(lineas[i].split(","))
            i += 1

        df_dmm = pd.DataFrame(datos, columns=headers)

        medicion_info["dmm"] = df_dmm

        mediciones.append(medicion_info)

    return mediciones


def Procesar_Medicion(Mediciones, verbose=True):

    resultados = []

    for i, m in enumerate(Mediciones):
        
        # =========================
        # Obtener metadatos de la Medición
        # =========================
        m["metadata"]["Rs"]
        m["metadata"]["Rx"]
        m["metadata"]["Ix"]
        metadata = m.get("metadata", {})

        rs = metadata.get("Rs", "N/A")
        rx = metadata.get("Rx", "N/A")
        ix = metadata.get("Ix", "N/A")
        # =========================
        # PUENTE (convertir a DataFrame si querés)
        # =========================

        df = pd.DataFrame(m["puente"])

        df["Ratio"] = pd.to_numeric(df["Ratio"], errors="coerce")
        df = df.dropna(subset=["Ratio"])

        if df.empty:
            promedio = None
            desvio = None
            hora_inicio = None
            hora_fin = None
            N = 0
        else:
            promedio = df["Ratio"].mean()
            desvio = df["Ratio"].std()
            hora_inicio = df["Horario"].iloc[0]
            hora_fin = df["Horario"].iloc[-1]
            N = len(df)

        # =========================
        # DMMs (SIN pandas)
        # =========================
        dmm1_vals = m["dmm"]["DMM1"]["Valor"]
        dmm2_vals = m["dmm"]["DMM2"]["Valor"]
        dmm3_vals = m["dmm"]["DMM3"]["Valor"]

        dmm1_mean = np.mean(dmm1_vals) if dmm1_vals else None
        dmm2_mean = np.mean(dmm2_vals) if dmm2_vals else None
        dmm3_mean = np.mean(dmm3_vals) if dmm3_vals else None
        
        dmm1_std = np.std(dmm1_vals) if dmm1_vals else None
        dmm2_std = np.std(dmm2_vals) if dmm2_vals else None
        dmm3_std = np.std(dmm3_vals) if dmm3_vals else None

        # =========================
        # TEMPERATURA
        # =========================
        sensores_metadata = metadata.get("sensores", {}) or {}

        sensor_dmm1 = sensores_metadata.get("DMM1")
        t1 = resistencia_a_temperatura(
            dmm1_mean,
            sensor_dmm1["R0"],
            sensor_dmm1["alfa"],
            sensor_dmm1["beta"],
            sensor_dmm1["T0"]
        ) if (dmm1_mean is not None and sensor_dmm1) else None

        sensor_dmm2 = sensores_metadata.get("DMM2")
        t2 = resistencia_a_temperatura(
            dmm2_mean,
            sensor_dmm2["R0"],
            sensor_dmm2["alfa"],
            sensor_dmm2["beta"],
            sensor_dmm2["T0"]
        ) if (dmm2_mean is not None and sensor_dmm2) else None

        sensor_dmm3 = sensores_metadata.get("DMM3")
        t3 = resistencia_a_temperatura(
            dmm3_mean,
            sensor_dmm3["R0"],
            sensor_dmm3["alfa"],
            sensor_dmm3["beta"],
            sensor_dmm3["T0"]
        ) if (dmm3_mean is not None and sensor_dmm3) else None

        rs_patron = metadata.get("Rs_patron", {}) or {}
        rs_valor_patron = _to_float(rs_patron.get("Valor"))
        rs_alfa_patron = _to_float(rs_patron.get("Alfa"))
        rs_beta_patron = _to_float(rs_patron.get("Beta"))
        rs_t0_patron = _to_float(rs_patron.get("T0"))
        
        # =========================
        # RESULTADO
        # =========================
        resultado = {
            "Rs_patron": rs_patron,
            "Rs_Valor_Patron": rs_valor_patron,
            "Rs_alfa_Patron": rs_alfa_patron,
            "Rs_beta_Patron": rs_beta_patron,
            "Rs_T0_Patron": rs_t0_patron,
            "medicion": i + 1,
            "Rs_nombre": rs,
            "Rx_nombre": rx,
            "Ix": ix,
            "hora_inicio": hora_inicio,
            "hora_fin": hora_fin,
            "promedio_puente": promedio,
            "desvio_puente": desvio,
            "N_puente": N,
            "dmm1_mean": dmm1_mean,
            "dmm2_mean": dmm2_mean,
            "dmm3_mean": dmm3_mean,
            "dmm1_std": dmm1_std,
            "dmm2_std": dmm2_std,
            "dmm3_std": dmm3_std,
            "dmm1_temp": t1,
            "dmm2_temp": t2,
            "dmm3_temp": t3,
            "sensores": sensores_metadata
        }

        resultados.append(resultado)

        if verbose:
            print(f"\nMedición {i+1}")
            print(f"  Rs: {rs}")
            print(f"  Rx: {rx}")
            print(f"  Ix: {ix}")
            print(f"  Puente → Promedio: {promedio} | Desvío: {desvio}")
            print(f"  DMM1: {dmm1_mean} | Temp: {t1}")
            print(f"  DMM2: {dmm2_mean} | Temp: {t2}")
            print(f"  DMM3: {dmm3_mean} | Temp: {t3}")

    return resultados

def Agrupar_Mediciones(Resultados):
    """
    Agrupa las mediciones por Rs_nombre, Rx_nombre e Ix sin promediar.
    Cada grupo conserva la lista de mediciones originales y añade los
    parámetros de Rs y el valor de Rs_corregido por medición.
    """

    grupos = {}
    cache_rs = {}

    for entrada in Resultados:
        rs_nombre = str(entrada.get("Rs_nombre", "N/A"))
        rx_nombre = str(entrada.get("Rx_nombre", "N/A"))
        ix = str(entrada.get("Ix", "N/A"))
        llave = (rs_nombre, rx_nombre, ix)

        if llave not in grupos:
            grupos[llave] = {
                "Rs_nombre": rs_nombre,
                "Rx_nombre": rx_nombre,
                "Ix": ix,
                "Rs_Valor": None,
                "Rs_R0": None,
                "Rs_alfa": None,
                "Rs_beta": None,
                "Rs_T0": None,
                "mediciones": []
            }

        if rs_nombre not in cache_rs:
            cache_rs[rs_nombre] = Cargar_Base_De_Datos(rs_nombre) if rs_nombre != "N/A" else None

        rs_data = cache_rs.get(rs_nombre)
        medicion = entrada.copy()

        rs_patron = entrada.get("Rs_patron", {}) or {}
        rs_patron_valor = _to_float(rs_patron.get("Valor"))
        rs_patron_alfa = _to_float(rs_patron.get("Alfa"))
        rs_patron_beta = _to_float(rs_patron.get("Beta"))
        rs_patron_t0 = _to_float(rs_patron.get("T0"))

        if rs_data:
            valor_rs = _to_float(rs_data.get("valor")) if rs_data.get("valor") is not None else rs_patron_valor
            alfa = _to_float(rs_data.get("alfa")) if rs_data.get("alfa") is not None else rs_patron_alfa
            beta = _to_float(rs_data.get("beta")) if rs_data.get("beta") is not None else rs_patron_beta
            t0_value = _to_float(rs_data.get("temperatura_de_calibración", rs_data.get("T0")))
            if t0_value is None:
                t0_value = rs_patron_t0

            medicion["Rs_Valor"] = valor_rs
            medicion["Rs_R0"] = valor_rs
            medicion["Rs_alfa"] = alfa
            medicion["Rs_beta"] = beta
            medicion["Rs_T0"] = t0_value

            if grupos[llave]["Rs_Valor"] is None:
                grupos[llave].update({
                    "Rs_Valor": valor_rs,
                    "Rs_R0": valor_rs,
                    "Rs_alfa": alfa,
                    "Rs_beta": beta,
                    "Rs_T0": t0_value
                })
        else:
            valor_rs = rs_patron_valor
            alfa = rs_patron_alfa
            beta = rs_patron_beta
            t0_value = rs_patron_t0

            medicion["Rs_Valor"] = valor_rs
            medicion["Rs_R0"] = valor_rs
            medicion["Rs_alfa"] = alfa
            medicion["Rs_beta"] = beta
            medicion["Rs_T0"] = t0_value

        temperatura = medicion.get("dmm1_temp")
        if temperatura is None:
            temperatura = medicion.get("dmm1_temp_mean")

        medicion["Rs_Corregida"] = _calcular_rs_corregida(
            medicion.get("Rs_Valor"),
            medicion.get("Rs_alfa"),
            medicion.get("Rs_beta"),
            medicion.get("Rs_T0"),
            temperatura
        )

        # =========================
        # Rx calibrado y incertidumbre tipo B
        # =========================
        try:
            ratio = float(medicion.get("promedio_puente"))
            rs_corr = float(medicion.get("Rs_Corregida")) if medicion.get("Rs_Corregida") is not None else None
            if rs_corr is not None:
                rx_calibrado = ratio * rs_corr
                medicion["Rx_Calibrado"] = rx_calibrado
                medicion["uB"] = Detector_Incertidumbre_B(ratio, rs_corr, rx_calibrado)
            else:
                medicion["Rx_Calibrado"] = None
                medicion["uB"] = None
        except (TypeError, ValueError):
            medicion["Rx_Calibrado"] = None
            medicion["uB"] = None

        grupos[llave]["mediciones"].append(medicion)

    resultados_analizados = {
        "grupos": grupos,
        "n_grupos": len(grupos)
    }

    if resultados_analizados["n_grupos"] == 1:
        return next(iter(resultados_analizados["grupos"].values()))

    return resultados_analizados

def Preguntar_Si_No(mensaje):
    while True:
        respuesta = input(f"{mensaje} (s/n): ").strip().lower()
        if respuesta == 's' or respuesta == 'n':
            if respuesta == 's':
                return "Calibracion"
            else:
                return "Final"
        else:
            print("Respuesta no válida. Por favor, ingrese 's' para sí o 'n' para no.")

def Correccion_Temperatura(Resultados_Ordenados):
    """Corrige Rs por temperatura usando Rs_nombre y la temperatura medida en DMM1.

    El resultado conserva la misma estructura de Resultados_Ordenados,
    añadiendo Rs_Corregida en cada medición/grupo y en metadata si existe.
    """

    def corregir_entrada(entrada):
        if not isinstance(entrada, dict):
            return entrada

        if "mediciones" in entrada and isinstance(entrada["mediciones"], list):
            entrada["mediciones"] = [corregir_entrada(m) for m in entrada["mediciones"]]
            return entrada

        rs_nombre = entrada.get("Rs_nombre")
        if not rs_nombre:
            return entrada

        rs_data = Cargar_Base_De_Datos(rs_nombre)
        if not rs_data:
            entrada["Rs_Corregida"] = None
            if "metadata" in entrada and isinstance(entrada["metadata"], dict):
                entrada["metadata"]["Rs_Corregida"] = None
            return entrada

        temperatura = entrada.get("dmm1_temp_mean")
        if temperatura is None:
            temperatura = entrada.get("dmm1_temp")

        try:
            T0 = float(rs_data.get("temperatura_de_calibracion", rs_data.get("T0", 0.0)))
            alfa = float(rs_data.get("alfa", 0.0))
            beta = float(rs_data.get("beta", 0.0))
            valor_rs = float(rs_data.get("valor", 0.0))
        except (TypeError, ValueError):
            entrada["Rs_Corregida"] = None
            if "metadata" in entrada and isinstance(entrada["metadata"], dict):
                entrada["metadata"]["Rs_Corregida"] = None
            return entrada

        if temperatura is None:
            entrada["Rs_Corregida"] = None
            if "metadata" in entrada and isinstance(entrada["metadata"], dict):
                entrada["metadata"]["Rs_Corregida"] = None
            return entrada

        try:
            temperatura = float(temperatura)
            Rs_corregida = valor_rs * (
                1 + alfa * (temperatura - T0) + beta * (temperatura - T0) ** 2
            )
        except (TypeError, ValueError):
            Rs_corregida = None

        entrada["Rs_Corregida"] = Rs_corregida
        if "metadata" in entrada and isinstance(entrada["metadata"], dict):
            entrada["metadata"]["Rs_Corregida"] = Rs_corregida
        return entrada

    if isinstance(Resultados_Ordenados, dict):
        if "grupos" in Resultados_Ordenados and isinstance(Resultados_Ordenados["grupos"], dict):
            for clave, valor in Resultados_Ordenados["grupos"].items():
                Resultados_Ordenados["grupos"][clave] = corregir_entrada(valor)
            return Resultados_Ordenados
        return corregir_entrada(Resultados_Ordenados)

    if isinstance(Resultados_Ordenados, list):
        return [corregir_entrada(x) for x in Resultados_Ordenados]

    return Resultados_Ordenados


def Detector_Incertidumbre_B(ratio, Rs, Rx_calibrado, tol_ratio=0.2):
    """
    ratio: valor float (ej: 0.98, 1.02, 10, 0.1)
    Rs: valor en ohm
    Rx_calibrado: valor de la resistencia bajo calibración (ohm)
    tol_ratio: tolerancia para identificar tipo de ratio

    devuelve incertidumbre absoluta (ohm)
    """

    Rs = float(Rs)
    ratio = float(ratio)
    Rx_calibrado = float(Rx_calibrado)

    # =========================
    # DETECTAR TIPO DE RATIO
    # =========================
    if abs(ratio - 1) <= tol_ratio:
        tipo = "1:1"
    elif abs(ratio - 10) <= tol_ratio or abs(ratio - 0.1) <= tol_ratio:
        tipo = "10:1"
    else:
        raise ValueError(f"Ratio {ratio} no reconocido")

    # =========================
    # INCERTIDUMBRE RELATIVA
    # =========================
    if tipo == "1:1":
        if Rs <= 0.1:
            u_rel = 0.1e-6
        elif Rs <= 1e3:
            u_rel = 0.04e-6
        else:
            u_rel = 0.1e-6

    elif tipo == "10:1":
        if Rs <= 10e3:
            u_rel = 0.04e-6
        else:
            u_rel = 0.1e-6

    # =========================
    # PASAR A ABSOLUTO
    # =========================
    u_abs = u_rel * Rx_calibrado

    return u_abs

def resistencia_a_temperatura(R, R0, alfa, beta, T0):


    if R is None:
        return None

    try:
        a = beta
        b = alfa
        c = 1 - (R / R0)

        discriminante = b**2 - 4*a*c

        if discriminante < 0:
            return None

        x1 = (-b + math.sqrt(discriminante)) / (2*a)
        x2 = (-b - math.sqrt(discriminante)) / (2*a)

        # elegimos la solución físicamente razonable
        x = x1 if abs(x1) < abs(x2) else x2

        return T0 + x

    except:
        return None
    
def Cargar_Sensores(lista_sensores, Cant_Sensores):

    Parametros_sensores = {}
    Lectura_ok = True  # ✔ asumimos que todo está bien

    for i in range(Cant_Sensores):

        nombre_sensor = lista_sensores[i]
        sensor_data = Cargar_Base_De_Datos(nombre_sensor)

        if sensor_data:
            try:
                Parametros_sensores[f"DMM{i+1}"] = {
                    "Nombre": nombre_sensor,
                    "R0": float(sensor_data.get("valor")),
                    "alfa": float(sensor_data.get("alfa")),
                    "beta": float(sensor_data.get("beta")),
                    "T0": float(sensor_data.get("T0"))
                }
            except Exception as e:
                print(f"\nError al procesar datos de '{nombre_sensor}': {e}")
                Lectura_ok = False   # ❌ algo falló
        else:
            print(f"\nNo se pudieron cargar los datos de '{nombre_sensor}'")
            Lectura_ok = False       # ❌ algo falló

    return Lectura_ok, Parametros_sensores

def Cargar_Resistor_Calibrado(RS_NOMBRE, verbose=True):

    datos_rs = {}
    ok = False

    RS_Calibrado = Cargar_Base_De_Datos(RS_NOMBRE)

    if RS_Calibrado:
        try:
            datos_rs = {
                "nombre": RS_NOMBRE,
                "valor": float(RS_Calibrado.get("valor")),
                "serial": RS_Calibrado.get("serial"),
                "Pmax": float(RS_Calibrado.get("Potencia_maxima_de_disipacion")),
                "alfa": float(RS_Calibrado.get("alfa")),
                "beta": float(RS_Calibrado.get("beta")),
                "T0": float(RS_Calibrado.get("T0"))
            }

            ok = True

            if verbose:
                print("=" * 90)
                print("Datos cargados:")
                print(f"Resistor patrón: {datos_rs['nombre']}")
                print(f"Valor Nominal  : {datos_rs['valor']} Ω")
                print(f"Número de Serie: {datos_rs['serial']}")
                print("=" * 90)

        except Exception as e:
            print(f"\nError al procesar datos de '{RS_NOMBRE}': {e}")
            ok = False

    else:
        print(f"\nNo se pudieron cargar los datos de '{RS_NOMBRE}'")
        ok = False

    return ok, datos_rs

def Delay_Interactivo(TIEMPO_DELAY):

    print("Presione '1' para omitir la espera...\n")

    for i in range(int(TIEMPO_DELAY), 0, -1):
        print(f"Esperando... {i} s", end="\r", flush=True)

        for _ in range(10):  # 10 x 0.1s = 1 segundo
            time.sleep(0.1)

            if msvcrt.kbhit():
                tecla = msvcrt.getch().decode("utf-8", errors="ignore")

                if tecla == "1":
                    print("\n⏩ Delay omitido por el usuario")

                    # limpiar buffer
                    while msvcrt.kbhit():
                        msvcrt.getch()

                    print(" " * 40, end="\r")
                    
def Leer_Mediciones_Estructuradas(ruta_archivo, NUM_STATISTICS=None):

    mediciones = []

    metadata = {
        "Rs": "N/A",
        "Rx": "N/A",
        "Ix": "N/A",
        "sensores": {},
        "Rs_patron": {
            "Valor": None,
            "Alfa": None,
            "Beta": None,
            "T0": None
        }
    }

    medicion_actual = {
        "metadata": metadata.copy(),
        "puente": {"Horario": [], "Ratio": []},
        "dmm": {
            "DMM1": {"Horario": [], "Valor": []},
            "DMM2": {"Horario": [], "Valor": []},
            "DMM3": {"Horario": [], "Valor": []}
        }
    }

    en_puente = False
    en_dmm = False
    en_sensores = False
    en_rs_patron = False
    fecha_inicio = None
    sensores_headers = None
    
    with open(ruta_archivo, "r") as f:
        reader = csv.reader(f)

        for row in reader:

            if not row:
                continue

            texto = row[0].strip()

            # =========================
            # EXTRAER METADATOS INICIALES
            # =========================
            if texto.startswith("# Rs:"):
                metadata["Rs"] = texto.split(":", 1)[1].strip()
                medicion_actual["metadata"]["Rs"] = metadata["Rs"]
            elif texto.startswith("# Rx:"):
                metadata["Rx"] = texto.split(":", 1)[1].strip()
                medicion_actual["metadata"]["Rx"] = metadata["Rx"]
            elif texto.startswith("# Ix:"):
                metadata["Ix"] = texto.split(":", 1)[1].strip()
                medicion_actual["metadata"]["Ix"] = metadata["Ix"]
            # =========================
            # BLOQUE SENSORES
            # =========================
            elif texto.startswith("# Sensores"):
                en_sensores = True
                en_puente = False
                en_dmm = False
                en_rs_patron = False
                sensores_headers = None
                continue
            # =========================
            # BLOQUE VALORES DEL PATRÓN
            # =========================
            elif texto.startswith("# Valores del patrón") or texto.startswith("# Valores del resistor de referencia Rs"):
                en_rs_patron = True
                en_sensores = False
                en_puente = False
                en_dmm = False
                continue
            # =========================
            # EXTRAER FECHA INICIAL
            # =========================
            elif texto.startswith("# Medicion -") and fecha_inicio is None:
                match = re.search(r"\d{4}-\d{2}-\d{2}", texto)
                if match:
                    fecha_inicio = match.group()
                en_sensores = False
                en_rs_patron = False
            elif texto.startswith("# Nueva medicion"):
                if medicion_actual["puente"]["Horario"]:
                    mediciones.append(aplicar_filtro(medicion_actual, NUM_STATISTICS, fecha_inicio))

                medicion_actual = {
                    "metadata": metadata.copy(),
                    "puente": {"Horario": [], "Ratio": []},
                    "dmm": {
                        "DMM1": {"Horario": [], "Valor": []},
                        "DMM2": {"Horario": [], "Valor": []},
                        "DMM3": {"Horario": [], "Valor": []}
                    }
                }

                en_puente = False
                en_dmm = False
                en_rs_patron = False
                continue

            # =========================
            # BLOQUE PUENTE
            # =========================
            elif texto.startswith("# Datos del puente"):
                en_puente = True
                en_dmm = False
                en_rs_patron = False
                next(reader, None)
                continue

            # =========================
            # BLOQUE DMM
            # =========================
            elif texto.startswith("# Datos de los DMMs"):
                en_dmm = True
                en_puente = False
                en_rs_patron = False
                next(reader, None)
                continue

            # =========================
            # OTROS BLOQUES
            # =========================
            elif texto.startswith("#"):
                en_puente = False
                en_dmm = False
                en_sensores = False
                en_rs_patron = False
                continue

            # =========================
            # DATOS SENSORES
            # =========================
            if en_sensores and len(row) >= 1:
                if sensores_headers is None:
                    # Primera línea: encabezados
                    sensores_headers = row
                else:
                    # Datos de sensores
                    try:
                        sensor_nombre = row[0].strip() if len(row) > 0 else ""
                        if sensor_nombre:
                            sensor_data = {
                                "nombre": row[1].strip() if len(row) > 1 else "",
                                "R0": float(row[2]) if len(row) > 2 else 0.0,
                                "alfa": float(row[3]) if len(row) > 3 else 0.0,
                                "beta": float(row[4]) if len(row) > 4 else 0.0,
                                "T0": float(row[5]) if len(row) > 5 else 0.0
                            }
                            metadata["sensores"][sensor_nombre] = sensor_data
                            medicion_actual["metadata"]["sensores"] = metadata["sensores"].copy()
                    except (ValueError, IndexError):
                        pass

            # =========================
            # DATOS Rs PATRÓN
            # =========================
            if en_rs_patron and len(row) >= 2:
                llave = row[0].strip()
                valor = row[1].strip()
                if llave in ("Valor", "Alfa", "Beta", "T0"):
                    try:
                        metadata["Rs_patron"][llave] = float(valor)
                    except ValueError:
                        metadata["Rs_patron"][llave] = valor
                    medicion_actual["metadata"]["Rs_patron"] = metadata["Rs_patron"].copy()

            # =========================
            # DATOS PUENTE
            # =========================
            if en_puente and len(row) >= 2:
                try:
                    h = row[0].strip()
                    r = float(row[1])

                    medicion_actual["puente"]["Horario"].append(h)
                    medicion_actual["puente"]["Ratio"].append(r)
                except:
                    pass

            # =========================
            # DATOS DMM
            # =========================
            if en_dmm and len(row) >= 6:

                # DMM1
                if row[0] and row[1]:
                    try:
                        medicion_actual["dmm"]["DMM1"]["Horario"].append(row[0])
                        medicion_actual["dmm"]["DMM1"]["Valor"].append(float(row[1]))
                    except:
                        pass

                # DMM2
                if row[2] and row[3]:
                    try:
                        medicion_actual["dmm"]["DMM2"]["Horario"].append(row[2])
                        medicion_actual["dmm"]["DMM2"]["Valor"].append(float(row[3]))
                    except:
                        pass

                # DMM3
                if row[4] and row[5]:
                    try:
                        medicion_actual["dmm"]["DMM3"]["Horario"].append(row[4])
                        medicion_actual["dmm"]["DMM3"]["Valor"].append(float(row[5]))
                    except:
                        pass

    # última medición
    if medicion_actual["puente"]["Horario"]:
        mediciones.append(aplicar_filtro(medicion_actual, NUM_STATISTICS, fecha_inicio))

    return mediciones


def aplicar_filtro(medicion, N, fecha_inicio):

    if N is None:
        return medicion

    # =========================
    # PUENTE → últimos N
    # =========================
    horarios = medicion["puente"]["Horario"]
    ratios = medicion["puente"]["Ratio"]

    horarios_filtrados = horarios[-N:]
    ratios_filtrados = ratios[-N:]

    medicion["puente"]["Horario"] = horarios_filtrados
    medicion["puente"]["Ratio"] = ratios_filtrados

    tiempos_puente = construir_tiempos(horarios_filtrados,fecha_inicio)
    tiempos_puente = [t for t in tiempos_puente if t is not None]

    if not tiempos_puente:
        return medicion

    t_inicio = min(tiempos_puente)
    t_fin = max(tiempos_puente)

    # =========================
    # FILTRAR DMMs
    # =========================
    for dmm in medicion["dmm"]:

        horarios_dmm = medicion["dmm"][dmm]["Horario"]
        valores_dmm = medicion["dmm"][dmm]["Valor"]

        tiempos_dmm = construir_tiempos(horarios_dmm,fecha_inicio)

        nuevos_h = []
        nuevos_v = []

        for h, v, t in zip(horarios_dmm, valores_dmm, tiempos_dmm):
            if t and t_inicio <= t <= t_fin:
                nuevos_h.append(h)
                nuevos_v.append(v)

        medicion["dmm"][dmm]["Horario"] = nuevos_h
        medicion["dmm"][dmm]["Valor"] = nuevos_v

    return medicion

# =========================
# FUNCION PARA ARMAR DATETIME COMPLETO
# =========================
def construir_tiempos(lista_horarios, fecha_inicio):
    tiempos = []

    fecha_base = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    dia_actual = fecha_base

    t_anterior = None

    for h in lista_horarios:
        try:
            t = datetime.datetime.strptime(h, "%H:%M:%S")
        except:
            tiempos.append(None)
            continue

        t_full = dia_actual.replace(hour=t.hour, minute=t.minute, second=t.second)

        # detectar cruce de medianoche
        if t_anterior and t < t_anterior:
            dia_actual += timedelta(days=1)
            t_full = dia_actual.replace(hour=t.hour, minute=t.minute, second=t.second)

        tiempos.append(t_full)
        t_anterior = t

    return tiempos

def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def _calcular_rs_corregida(valor_rs, alfa, beta, t0, temperatura):
    if valor_rs is None or alfa is None or beta is None or t0 is None or temperatura is None:
        return None
    try:
        temperatura = float(temperatura)
        return valor_rs * (1 + alfa * (temperatura - t0) + beta * (temperatura - t0) ** 2)
    except (TypeError, ValueError):
        return None
    
def Imprimir_Resultados_Analizados(resultados_analizados):

    # =========================
    # Normalizar estructura
    # =========================
    if "grupos" not in resultados_analizados:
        grupos = {
            (
                resultados_analizados.get("Rs_nombre"),
                resultados_analizados.get("Rx_nombre"),
                resultados_analizados.get("Ix")
            ): resultados_analizados
        }
    else:
        grupos = resultados_analizados["grupos"]

    print("=" * 100)
    print("RESULTADOS ANALIZADOS")
    print("=" * 100)

    # =========================
    # Recorrer grupos
    # =========================
    for idx, (llave, grupo) in enumerate(grupos.items(), start=1):

        print("\n" + "-" * 100)
        print(f"GRUPO {idx}")
        print("-" * 100)

        print(f"Rs : {grupo.get('Rs_nombre')}")
        print(f"Rx : {grupo.get('Rx_nombre')}")
        print(f"Ix : {grupo.get('Ix')}")

        print("\nParámetros Rs:")
        print(f"  Valor nominal : {grupo.get('Rs_Valor')}")
        print(f"  R0            : {grupo.get('Rs_R0')}")
        print(f"  alfa          : {grupo.get('Rs_alfa')}")
        print(f"  beta          : {grupo.get('Rs_beta')}")
        print(f"  T0            : {grupo.get('Rs_T0')}")

        print("\nMediciones:")
        print("-" * 100)

        mediciones = grupo.get("mediciones", [])

        for i, medicion in enumerate(mediciones, start=1):

            print(f"\n  Medición #{i}")

            print(f"    Hora inicio      : {medicion.get('hora_inicio')}")
            print(f"    Hora fin         : {medicion.get('hora_fin')}")

            promedio = medicion.get("promedio_puente")
            desvio = medicion.get("desvio_puente")

            print(f"    Ratio promedio   : {promedio:.12f}" if promedio is not None else
                  "    Ratio promedio   : None")

            print(f"    Ratio desvío     : {desvio:.12f}" if desvio is not None else
                  "    Ratio desvío     : None")

            print(f"    N puente         : {medicion.get('N_puente')}")

            rx_cal = medicion.get("Rx_Calibrado")
            print(f"    Rx calibrado     : {rx_cal:.12f} ohm" if rx_cal is not None else
                  "    Rx calibrado     : None")

            print("\n    Temperaturas:")

            t1 = medicion.get("dmm1_temp")
            t2 = medicion.get("dmm2_temp")
            t3 = medicion.get("dmm3_temp")

            print(f"      DMM1 : {t1:.6f} °C" if t1 is not None else
                  "      DMM1 : None")

            print(f"      DMM2 : {t2:.6f} °C" if t2 is not None else
                  "      DMM2 : None")

            print(f"      DMM3 : {t3:.6f} °C" if t3 is not None else
                  "      DMM3 : None")

            print("\n    Desvíos DMM:")

            dmm1_std = medicion.get("dmm1_std")
            dmm2_std = medicion.get("dmm2_std")
            dmm3_std = medicion.get("dmm3_std")

            print(f"      DMM1 : {dmm1_std:.12e}" if dmm1_std is not None else
                  "      DMM1 : None")

            print(f"      DMM2 : {dmm2_std:.12e}" if dmm2_std is not None else
                  "      DMM2 : None")

            print(f"      DMM3 : {dmm3_std:.12e}" if dmm3_std is not None else
                  "      DMM3 : None")

            rs_corr = medicion.get("Rs_Corregida")

            print(
                f"\n    Rs corregida     : {rs_corr:.12f} ohm"
                if rs_corr is not None else
                "\n    Rs corregida     : None"
            )

    print("\n" + "=" * 100)
    print("FIN DEL REPORTE")
    print("=" * 100)

#####################################################################################################################

def crear_dataframe_resultados(resultados_analizados, ruta_salida):
    """
    Crea un DataFrame a partir de Resultados_Analizados donde cada fila es una medición
    con las columnas especificadas, lo muestra en consola y lo guarda en un archivo CSV.
    
    Args:
        resultados_analizados: Diccionario con los resultados analizados
        ruta_salida: Ruta donde guardar el archivo CSV
    """
    # =========================
    # Normalizar estructura
    # =========================
    if "grupos" not in resultados_analizados:
        grupos = {
            (
                resultados_analizados.get("Rs_nombre"),
                resultados_analizados.get("Rx_nombre"),
                resultados_analizados.get("Ix")
            ): resultados_analizados
        }
    else:
        grupos = resultados_analizados["grupos"]

    # =========================
    # Recopilar datos para el DataFrame
    # =========================
    data = []
    for llave, grupo in grupos.items():
        rx_nombre = grupo.get('Rx_nombre')
        rs_nombre = grupo.get('Rs_nombre')
        mediciones = grupo.get("mediciones", [])
        for medicion in mediciones:
            row = {
                'Rx_nombre': rx_nombre,
                'Rx_Calibrado': medicion.get('Rx_Calibrado'),
                'Separador': '',
                'Rs_nombre': rs_nombre,
                'Rs_Corregido': medicion.get('Rs_Corregida'),
                'Ix': medicion.get('Ix'),
                'ratio_promedio': medicion.get('promedio_puente'),
                'desvio_ratio': medicion.get('desvio_puente'),
                'uB': medicion.get('uB'),
                'Temp_dmm1': medicion.get('dmm1_temp'),
                'desvio_dmm1': medicion.get('dmm1_std'),
                'Temp_dmm2': medicion.get('dmm2_temp'),
                'desvio_dmm2': medicion.get('dmm2_std'),
                'Temp_dmm3': medicion.get('dmm3_temp'),
                'desvio_dmm3': medicion.get('dmm3_std'),
            }
            data.append(row)

    # =========================
    # Crear DataFrame y mostrar
    # =========================
    df = pd.DataFrame(data)
    # Reordenar columnas en el orden especificado
    columnas_ordenadas = [
        'Rx_nombre', 'Rx_Calibrado', 'Separador', 'Rs_nombre', 'Rs_Corregido', 'Ix',
        'ratio_promedio', 'desvio_ratio', 'uB', 'Temp_dmm1', 'desvio_dmm1',
        'Temp_dmm2', 'desvio_dmm2', 'Temp_dmm3', 'desvio_dmm3'
    ]
    df = df[columnas_ordenadas]
    print("\n" + "=" * 100)
    print("DATAFRAME DE RESULTADOS ANALIZADOS")
    print("=" * 100)
    print(df.to_string(index=False))
    print("=" * 100)

    # =========================
    # Guardar en archivo CSV
    # =========================
    # Crear nombre de archivo con fecha y hora
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    nombre_archivo = f"Resumen-{timestamp}.csv"
    ruta_completa = os.path.join(ruta_salida, nombre_archivo)
    
    # Crear directorio si no existe
    Path(ruta_salida).mkdir(parents=True, exist_ok=True)
    
    # Guardar DataFrame en CSV
    df.to_csv(ruta_completa, index=False, encoding='utf-8', sep=';')
    print(f"\n✅ Archivo guardado: {ruta_completa}\n")

    return df

#####################################################################################################################