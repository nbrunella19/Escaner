"""
Test script corregido para MI6010D
Lectura correcta usando Serial Poll (SRQ handling)
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Instrumental.HP34420 import HP34420A
from Instrumental.HP34401 import HP34401A

def measure_two_resistances(samples=2, delay=0.5):

    dmm1 = HP34401A("GPIB0::14::INSTR")
    dmm2 = HP34420A("GPIB0::13::INSTR")

    try:

        print("Identificando instrumentos...")
        print("HP34401A:", dmm1.identify())
        print("HP34420A:", dmm2.identify())

        # Configuración 4-wire
        dmm1.configure_resistance_4wire(range_val=1000)
        dmm2.configure_resistance_4wire_2(range_val=1000)

        time.sleep(1)

        r1_values = []
        r2_values = []

        print("\nIniciando mediciones\n")

        for i in range(samples):

            r1 = dmm1.read()
            r2 = dmm2.read()

            r1_values.append(r1)
            r2_values.append(r2)

            print(
                f"[{i+1}/{samples}] "
                f"R1 = {r1:.6f} Ω   "
                f"R2 = {r2:.6f} Ω"
            )

            time.sleep(delay)

        r1_avg = sum(r1_values)/len(r1_values)
        r2_avg = sum(r2_values)/len(r2_values)

        print("\n==============================")
        print(f"R1 promedio: {r1_avg:.6f} Ω")
        print(f"R2 promedio: {r2_avg:.6f} Ω")
        print("==============================")

        return r1_avg, r2_avg

    finally:
        dmm1.close()
        dmm2.close()
        
if __name__ == "__main__":
        r1, r2 = measure_two_resistances(
        samples=5,
        delay=0.3
        )