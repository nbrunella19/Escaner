"""
Test script corregido para MI6010D
Lectura correcta usando Serial Poll (SRQ handling)
"""

import sys
import time
#import Manejo_Archivos.Func_Data
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from Instrumental.HP3458A import HP3458A
from Instrumental.MI6010D import MI6010D
from Instrumental.HP34420 import HP34420A
from Instrumental.HP34401 import HP34401A
from Manejo_Archivos.Func_Data import Guarda_Medicion
import numpy as np


def Measure_with_Temp(GPIB_ADDRESS_BRID, RS, TIME_REVERSAL, IX, NUM_MEASUREMENTS, NUM_STATISTICS, DMM_NAME_1, GPIB_ADDRESS_DMM1, DMM_NAME_2, GPIB_ADDRESS_DMM2, DMM_NAME_3, GPIB_ADDRESS_DMM3, Cant_Sensores):

    bridge = MI6010D()

    # Timestamp para el archivo
    timestamp = time.strftime("%Y-%m-%d-%H-%M")
  
    dmm1 = None
    dmm2 = None
    dmm3 = None
    dmm1_connected = False
    dmm2_connected = False
    dmm3_connected = False
    bridge_connected = False

    DMM_1 = f"{DMM_NAME_1}-{GPIB_ADDRESS_DMM1}"
    DMM_2 = f"{DMM_NAME_2}-{GPIB_ADDRESS_DMM2}"
    DMM_3 = f"{DMM_NAME_3}-{GPIB_ADDRESS_DMM3}"

    # Intentar conectar puente
    try:
        bridge.is_present = True
        bridge.gpib_address = GPIB_ADDRESS_BRID
        bridge.connect()
        bridge_connected = True
        print("Iniciando mediciones con el puente MI6010D y DMMs...")
    except Exception as e:
        print(f"No se pudo conectar al puente MI6010D: {e}")

    # Intentar conectar DMM según cantidad de sensores
    if Cant_Sensores >= 1:
        # Intentar conectar DMM1
        try:
            if DMM_NAME_1 == "HP34401A":
                dmm1 = HP34401A(f"GPIB0::{GPIB_ADDRESS_DMM1}::INSTR")
            elif DMM_NAME_1 == "HP34420A":
                dmm1 = HP34420A(f"GPIB0::{GPIB_ADDRESS_DMM1}::INSTR")
            elif DMM_NAME_1 == "HP3458A":
                dmm1 = HP3458A(f"GPIB0::{GPIB_ADDRESS_DMM1}::INSTR")
            print(f"DMM1 ({DMM_NAME_1}) conectado en GPIB {GPIB_ADDRESS_DMM1}")
            dmm1_connected = True
        except Exception as e:
            print(f"No se pudo conectar al DMM1 {DMM_NAME_1}: {e}")

    if Cant_Sensores >= 2:
        # Intentar conectar DMM2
        try:
            if DMM_NAME_2 == "HP34401A":
                dmm2 = HP34401A(f"GPIB0::{GPIB_ADDRESS_DMM2}::INSTR")
            elif DMM_NAME_2 == "HP34420A":
                dmm2 = HP34420A(f"GPIB0::{GPIB_ADDRESS_DMM2}::INSTR")
            elif DMM_NAME_2 == "HP3458A":
                dmm2 = HP3458A(f"GPIB0::{GPIB_ADDRESS_DMM2}::INSTR")
            print(f"DMM2 ({DMM_NAME_2}) conectado en GPIB {GPIB_ADDRESS_DMM2}")
            dmm2_connected = True
        except Exception as e:
            print(f"No se pudo conectar al DMM2 {DMM_NAME_2}: {e}")

    if Cant_Sensores >= 3:
        # Intentar conectar DMM3
        try:
            if DMM_NAME_3 == "HP34401A":
                dmm3 = HP34401A(f"GPIB0::{GPIB_ADDRESS_DMM3}::INSTR")
            elif DMM_NAME_3 == "HP34420A":
                dmm3 = HP34420A(f"GPIB0::{GPIB_ADDRESS_DMM3}::INSTR")
            elif DMM_NAME_3 == "HP3458A":
                dmm3 = HP3458A(f"GPIB0::{GPIB_ADDRESS_DMM3}::INSTR")
            print(f"DMM3 ({DMM_NAME_3}) conectado en GPIB {GPIB_ADDRESS_DMM3}")
            dmm3_connected = True
        except Exception as e:
            print(f"No se pudo conectar al DMM3 {DMM_NAME_3}: {e}")

    # configuración DMM si conectados
    if dmm1_connected:
        dmm1.configure_resistance_4wire(range_val=1000)  # HP34401A tiene rango máximo de 100Ω en 4-wire
    if dmm2_connected:
        dmm2.configure_resistance_4wire(range_val=100)   # HP34420A tiene rango máximo de 100Ω en 4-wire
    if dmm3_connected:
        dmm3.configure_resistance_4wire(range_val=100)   # HP3458A tiene rango máximo de 100Ω en 4-wire

    # buffers de medición
    r1_values = []
    r2_values = []
    r3_values = []

    # intervalo de lectura de DMM
    DMM_INTERVAL = 5.0
    next_dmm_time = time.time()
    
    measurements = []

    try:
        if bridge_connected:
            bridge.reset()
            bridge.send_remote()
            bridge.send_stop()
            bridge.send_rs(RS)
            #bridge.send_rx(RX)
            bridge.send_ix(IX)
            bridge.send_reversal_rate(TIME_REVERSAL)
            bridge.send_measurements(NUM_MEASUREMENTS)
            bridge.send_statistics(NUM_STATISTICS)

        timeout_limit = time.time() + 600

        while time.time() < timeout_limit:

            if bridge_connected and len(measurements) >= NUM_MEASUREMENTS:
                break

            # -----------------------------
            # POLLING DEL PUENTE si conectado
            # -----------------------------
            if bridge_connected:
                try:
                    sp = bridge._instrument.read_stb()
                except Exception as e:
                    print("Error leyendo STB:", e)
                    break

                if sp != 0:

                    data = bridge.get_data().strip()

                    if not data:
                        continue

                    print(f"[STB={sp}] {data}")

                    if data.startswith("&"):
                        try:
                            value = float(data[1:])
                            measurements.append(value)
                            print(f"→ Rx/Rs puente: {value}")
                        except ValueError:
                            print("Error parseando valor")

                    elif data.startswith("N"):
                        bridge._instrument.write("O")

            # -----------------------------
            # LECTURA DMM (no bloqueante) si conectados
            # -----------------------------
            if time.time() >= next_dmm_time:

                r1 = None
                r2 = None
                r3 = None

                if dmm1_connected:
                    try:
                        r1 = dmm1.read()
                        r1_values.append(r1)
                        print(f"{DMM_1}: {r1:.5f} Ω")
                    except Exception as e:
                        print("Error leyendo DMM1:", e)

                if dmm2_connected:
                    try:
                        r2 = dmm2.read()
                        r2_values.append(r2)
                        print(f"{DMM_2}: {r2:.5f} Ω")
                    except Exception as e:
                        print("Error leyendo DMM2:", e)
                        
                if dmm3_connected:
                    try:
                        r3 = dmm3.read()
                        r3_values.append(r3)
                        print(f"{DMM_3}: {r3:.5f} Ω")
                    except Exception as e:
                        print("Error leyendo DMM3:", e)

                next_dmm_time = time.time() + DMM_INTERVAL

            time.sleep(0.05)

        # -----------------------------
        # RESULTADOS
        # -----------------------------
        ratio_promedio = sum(measurements)/len(measurements) if measurements else None
        ratio_desvio = np.std(measurements) if measurements else None
        
        r1_promedio = sum(r1_values)/len(r1_values) if r1_values else None
        r1_desvio = np.std(r1_values) if r1_values else None
        
        r2_promedio = sum(r2_values)/len(r2_values) if r2_values else None
        r2_desvio = np.std(r2_values) if r2_values else None
        
        r3_promedio = sum(r3_values)/len(r3_values) if r3_values else None
        r3_desvio = np.std(r3_values) if r3_values else None

        if measurements:
            print(f"\nRx/Rs promedio: {ratio_promedio}, desvío: {ratio_desvio}")
        if r1_values:
            print(f"DMM1 promedio: {r1_promedio}, desvío: {r1_desvio}")
        if r2_values:
            print(f"DMM2 promedio: {r2_promedio}, desvío: {r2_desvio}")
        if r3_values:
            print(f"DMM3 promedio: {r3_promedio}, desvío: {r3_desvio}")

    finally:

        if bridge_connected:
            bridge.send_stop()
            bridge.disconnect()

        if dmm1_connected:
            dmm1.close()
        if dmm2_connected:
            dmm2.close()
        if dmm3_connected:
            dmm3.close()

    return ratio_promedio, ratio_desvio, r1_promedio, r1_desvio, r2_promedio, r2_desvio, r3_promedio, r3_desvio


def Check_de_Seguridad(Rs, Rx, Ix,Psmax):
    """
    Función que verifica que las condiciones de seguridad  
    para la medición se cumplan antes de iniciar el proceso.
     - Rs: Resistencia del resistor patrón (Ohmios)
     - Rx: Resistencia del resistor a medir (Ohmios)
     - Ix: Corriente aplicada al resistor (mA)
     - Psmax: Potencia máxima de disipación del resistor patrón (W)
    """   
    Is= Rx*Ix*1e-3/Rs
    Ps= Rs*Is**2
    
    print(f"  Corriente Is: {Is:.6f} mA")
    print(f"  Potencia  Rs: {Ps:.6f} mW")
    if Rs <= 0 or Rx <= 0:
        print("Error: Rs y Rx deben ser mayores que 0.")
        return False
    if Ps > Psmax:
        print("Error: La potencia de salida excede el límite permitido.")
        return False
    if Ix <= 0:
        print("Error: Ix debe ser mayor que 0.")
        return False
    return True

'''
if __name__ == "__main__":
    Measure_with_Temp()
'''