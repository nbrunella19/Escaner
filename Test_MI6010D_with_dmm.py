"""
Test script corregido para MI6010D
Lectura correcta usando Serial Poll (SRQ handling)
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from Instrumental.MI6010D import MI6010D
from Instrumental.HP34420 import HP34420A
from Instrumental.HP34401 import HP34401A

def test_mi6010d_with_dmm():

    bridge = MI6010D()
    
    # CONFIGURACIÓN
    GPIB_ADDRESS = 15
    RS = 1.0
    RX = 1.0
    TIME_REVERSAL = 8
    IX = 1
    NUM_MEASUREMENTS = 5
    NUM_STATISTICS = 5
    
    
    dmm1   = HP34401A("GPIB0::14::INSTR")
    dmm2   = HP34420A("GPIB0::13::INSTR")

    # configuración DMM
    print("Identificando instrumentos...")
    print("HP34401A:", dmm1.identify())
    print("HP34420A:", dmm2.identify())

    dmm1.configure_resistance_4wire(range_val=1000)
    dmm2.configure_resistance_4wire_2(range_val=1000)

    # buffers de medición
    r1_values = []
    r2_values = []

    # intervalo de lectura de DMM
    DMM_INTERVAL = 1.0
    next_dmm_time = time.time()
    
    bridge.is_present = True
    bridge.gpib_address = 15
    bridge.connect()

    try:

        bridge.reset()
        bridge.send_remote()
        bridge.send_stop()

        bridge.send_rs(RS)
        bridge.send_rx(RX)
        bridge.send_ix(IX)
        bridge.send_reversal_rate(TIME_REVERSAL)
        bridge.send_measurements(NUM_MEASUREMENTS)
        bridge.send_statistics(NUM_STATISTICS)

        measurements = []

        timeout_limit = time.time() + 600

        while len(measurements) < 5:

            if time.time() > timeout_limit:
                print("⛔ Timeout global alcanzado")
                break

            # -----------------------------
            # POLLING DEL PUENTE
            # -----------------------------
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
            # LECTURA DMM (no bloqueante)
            # -----------------------------
            if time.time() >= next_dmm_time:

                try:
                    r1 = dmm1.read()
                    r2 = dmm2.read()

                    r1_values.append(r1)
                    r2_values.append(r2)

                    print(f"DMM1: {r1:.6f} Ω | DMM2: {r2:.6f} Ω")

                except Exception as e:
                    print("Error leyendo DMM:", e)

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

        bridge.send_stop()
        bridge.disconnect()

        dmm1.close()
        dmm2.close()

if __name__ == "__main__":
    test_mi6010d_with_dmm()
