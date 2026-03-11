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

def test_mi6010d():

    bridge = MI6010D()

    # CONFIGURACIÓN
    GPIB_ADDRESS = 15
    RS = 1.0
    RX = 1.0
    TIME_REVERSAL = 8
    IX = 1
    NUM_MEASUREMENTS = 5
    NUM_STATISTICS = 5

    print("=" * 60)
    print("MI6010D - TEST CORREGIDO")
    print("=" * 60)

    bridge.is_present = True
    bridge.gpib_address = GPIB_ADDRESS
    bridge.serial_number = "TEST-001"

    # CONEXIÓN
    print("\n[1] Conectando...")
    bridge.connect()
    print("✓ Conectado")

    try:

        # Reset seguro
        print("\n[2] Reset instrumento...")
        bridge.reset()
        time.sleep(0.5)

        bridge.send_remote()
        time.sleep(0.5)

        bridge.send_stop()
        time.sleep(0.5)

        # CONFIGURACIÓN
        print("\n[3] Configuración medición...")
        bridge.send_rs(RS)
        time.sleep(0.3)

        bridge.send_rx(RX)
        time.sleep(0.3)

        bridge.send_ix(IX)
        time.sleep(0.3)

        bridge.send_reversal_rate(TIME_REVERSAL)
        time.sleep(0.3)

        bridge.send_measurements(NUM_MEASUREMENTS)
        time.sleep(0.3)

        bridge.send_statistics(NUM_STATISTICS)
        time.sleep(0.3)

        print("✓ Configuración enviada")

        print("\n[4] Esperando mediciones...")
        print("=" * 60)

        measurements = []
        timeout_limit = time.time() + 600  # 10 minutos máximo

        while len(measurements) < NUM_MEASUREMENTS:

            if time.time() > timeout_limit:
                print("⛔ Timeout global alcanzado")
                break

            # --- Serial Poll ---
            try:
                sp = bridge._instrument.read_stb()
            except Exception as e:
                print("Error leyendo STB:", e)
                break

            if sp == 0:
                time.sleep(0.1)
                continue

            # --- Leer mensaje ---
            data = bridge.get_data().strip()

            if not data:
                continue

            print(f"[STB={sp}] {data}")

            # --- Procesar mensaje ---
            if data.startswith("&"):
                try:
                    value = float(data[1:])
                    measurements.append(value)
                    print(f"  → Medición {len(measurements)}/{NUM_MEASUREMENTS}: {value}")
                except ValueError:
                    print("  ✗ Error parseando valor")

            elif data.startswith("E"):
                print("  ⛔ Error del equipo:", data)
                break

            elif data.startswith("D"):
                print("  → Descripción:", data[1:])

            elif data.startswith("#"):
                print("  → Número medición:", data[1:])

            elif data.startswith("N"):
                print("  → Instrucción recibida → enviando OK")
                bridge._instrument.write("O")

            else:
                print("  → Mensaje no clasificado")

        print("=" * 60)

        if measurements:
            avg = sum(measurements) / len(measurements)
            print("=" * 60)
            print("\nMedición completada ✓")
            print(f"Mediciones recibidas: {len(measurements)} / {NUM_MEASUREMENTS}")
            print(f"Resistencia patrón (Rs):        {RS} Ω")
            print(f"Resistencia mesurando (Rx): {avg:.10f} Ω")
            print(f"Current (Ix):                  {IX} mA ({IX} mA)")
            print(f"Tiempo de inversión:     {TIME_REVERSAL} s")
            print(f"Número de mediciones:        {len(measurements)}/{NUM_MEASUREMENTS}")
            print(f"Mediciones para estadística:          {NUM_STATISTICS}")
            print("=" * 60)
            print("\nListado completo:")
            for i, val in enumerate(measurements, 1):
                print(f"  [{i:2d}] {val:.10f} Ω")
                   # Print measurement summary

        else:
            print("\n⛔ No se recibieron mediciones")

    finally:
        print("\n[5] Cerrando conexión...")
        try:
            bridge.send_stop()
            time.sleep(0.5)
            bridge.disconnect()
        except:
            pass
        print("✓ Desconectado")


if __name__ == "__main__":
    test_mi6010d()
