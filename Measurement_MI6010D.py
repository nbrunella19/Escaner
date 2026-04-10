"""
Test script corregido para MI6010D
Lectura correcta usando Serial Poll (SRQ handling)
"""

import sys
import time
#import Manejo_Archivos.Func_Data
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from Instrumental.MI6010D import MI6010D
from Instrumental.HP34420 import HP34420A
from Instrumental.HP34401 import HP34401A



def Measure_with_Temp(GPIB_ADDRESS_BRID, RS, RX, TIME_REVERSAL, IX, NUM_MEASUREMENTS, NUM_STATISTICS, DMM_NAME_1, GPIB_ADDRESS_DMM1, DMM_NAME_2, GPIB_ADDRESS_DMM2):

    bridge = MI6010D()

  
    dmm1 = None
    dmm2 = None
    bridge_connected = False
    dmm1_connected = False
    dmm2_connected = False

    DMM_1 = f"{DMM_NAME_1}-{GPIB_ADDRESS_DMM1}"
    DMM_2 = f"{DMM_NAME_2}-{GPIB_ADDRESS_DMM2}"

    # Intentar conectar puente
    try:
        bridge.is_present = True
        bridge.gpib_address = GPIB_ADDRESS_BRID
        bridge.connect()
        bridge_connected = True
        print("Ejecutando test de MI6010D con DMMs...")
    except Exception as e:
        print(f"No se pudo conectar al puente MI6010D: {e}")

    # Intentar conectar DMM1
    try:
        if DMM_NAME_1 == "HP34401A":
            dmm1 = HP34401A(f"GPIB0::{GPIB_ADDRESS_DMM1}::INSTR")
        elif DMM_NAME_1 == "HP34420A":
            dmm1 = HP34420A(f"GPIB0::{GPIB_ADDRESS_DMM1}::INSTR")
        print(f"DMM1 ({DMM_NAME_1}) conectado en GPIB {GPIB_ADDRESS_DMM1}")
        dmm1_connected = True
    except Exception as e:
        print(f"No se pudo conectar al DMM1 {DMM_NAME_1}: {e}")

    # Intentar conectar DMM2
    try:
        if DMM_NAME_2 == "HP34401A":
            dmm2 = HP34401A(f"GPIB0::{GPIB_ADDRESS_DMM2}::INSTR")
        elif DMM_NAME_2 == "HP34420A":
            dmm2 = HP34420A(f"GPIB0::{GPIB_ADDRESS_DMM2}::INSTR")
        print(f"DMM2 ({DMM_NAME_2}) conectado en GPIB {GPIB_ADDRESS_DMM2}")
        dmm2_connected = True
    except Exception as e:
        print(f"No se pudo conectar al DMM2 {DMM_NAME_2}: {e}")

    # configuración DMM si conectados
    if dmm1_connected:
        dmm1.configure_resistance_4wire(range_val=1000)  # HP34401A tiene rango máximo de 100Ω en 4-wire
    if dmm2_connected:
        dmm2.configure_resistance_4wire(range_val=100)   # HP34420A tiene rango máximo de 100Ω en 4-wire


    # buffers de medición
    r1_values = []
    r2_values = []

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
                            print(f"→ Rx puente: {value}")
                        except ValueError:
                            print("Error parseando valor")

                    elif data.startswith("N"):
                        bridge._instrument.write("O")

            # -----------------------------
            # LECTURA DMM (no bloqueante) si conectados
            # -----------------------------
            if time.time() >= next_dmm_time:

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

                next_dmm_time = time.time() + DMM_INTERVAL

            time.sleep(0.05)

        # -----------------------------
        # RESULTADOS
        # -----------------------------
        if measurements:
            print("\nPuente promedio:", sum(measurements)/len(measurements))

        if r1_values:
            print("DMM1 promedio:", sum(r1_values)/len(r1_values))

        if r2_values:
            print("DMM2 promedio:", sum(r2_values)/len(r2_values))

    finally:

        if bridge_connected:
            bridge.send_stop()
            bridge.disconnect()

        if dmm1_connected:
            dmm1.close()
        if dmm2_connected:
            dmm2.close()


def Check_de_Seguridad(Rs, Rx, Ismax, Ix,Psmax):
    Is= Rx*Ix*1e-3/Rs
    Ps= Rs*Is**2
    print(f"Corriente de salida calculada: {Is:.6f} mA")
    print(f"Potencia de salida calculada: {Ps:.6f} mW")
    if Rs <= 0 or Rx <= 0:
        print("Error: Rs y Rx deben ser mayores que 0.")
        return False
    if Is > Ismax:
        print("Error: La corriente de salida excede el límite permitido.")
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