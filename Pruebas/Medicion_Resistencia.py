from Instrumental.MI6010D import MI60100
from Instrumental.Scanner import ScannerInti
from Instrumental.HP3458A import HP3458A
from Instrumental.HP34401 import HP34401A
from Instrumental.HP34420 import HP34420A
import re
import csv
import os
from datetime import datetime
from datetime import date

# Carpeta donde está el script actual
base_dir = os.path.dirname(os.path.abspath(__file__))

# Nombre dinámico con la fecha de hoy
nombre_csv = f"Medicion_{date.today().isoformat()}.csv"

# Ruta completa (al lado del script)
ruta_csv = os.path.join(base_dir, nombre_csv)

def parse_report(report: str) -> dict:
    """
    Parser específico para reportes A3 del MI60100.
    """
    data = {'raw': report, 'timestamp': datetime.now().isoformat()}

    patterns = {
        'ratio': r'R[=:]\s*([+-]?\d+\.\d+E[+-]?\d+)',
        'Rs': r'RS[=:]\s*([+-]?\d+\.\d+E[+-]?\d+)',
        'Rx': r'RX[=:]\s*([+-]?\d+\.\d+E[+-]?\d+)',
        'media': r'MEAN[=:]\s*([+-]?\d+\.\d+E[+-]?\d+)',
        'std_ppm': r'STD[=:]\s*([+-]?\d+\.\d+E[+-]?\d+)',
        'incertidumbre_ppm': r'UNC[=:]\s*([+-]?\d+\.\d+E[+-]?\d+)',
    }

    for key, pat in patterns.items():
        m = re.search(pat, report)
        if m:
            data[key] = float(m.group(1))

    return data


def medir_resistencia(mi: MI60100, Rx: float, Rs: float, Ix: float, tiempo_inversion: int, num_muestras: int,
                      num_stats: int, csv_file: str = "mediciones.csv"):
    """
    Ejecuta una medición de resistencia Rx con el puente MI60100,
    parsea los resultados y los guarda en un CSV.

    Retorna:
        Lista de diccionarios con resultados.
    """
    # 1. Standby antes de configurar
    mi.standby()

    # 2. Configurar estándar Rs
    mi.send_rx_value(Rs)
    mi.set_rs_as_standard()

    # 3. Configurar Rx (valor nominal)
    mi.send_rx_value(Rx)

    # 4. Configurar corriente
    mi.set_primary_current(Ix)

    # 5. Configurar parámetros de medición
    mi.set_delay_seconds(tiempo_inversion)
    mi.set_num_measurements(num_muestras)
    mi.set_num_statistics(num_stats)

    # 6. Iniciar medición
    mi.start_measurements()

    # 7. Leer reportes y parsearlos
    results = []
    for _ in range(num_muestras):
        try:
            rep = mi.read_report()
            parsed = parse_report(rep)
            results.append(parsed)
        except Exception as e:
            print(f"Error leyendo reporte: {e}")
            break

    # 8. Guardar en CSV
    fieldnames = ["timestamp", "ratio", "Rs", "Rx", "media", "std_ppm", "incertidumbre_ppm", "raw"]
    file_exists = False
    try:
        with open(csv_file, "r"):
            file_exists = True
    except FileNotFoundError:
        pass

    with open(csv_file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for row in results:
            writer.writerow(row)

    return results


bridge = MI60100(15)  # GPIB #15
bridge.local_unlock()
print("Estado:", bridge.query())
Resultados = medir_resistencia(
    bridge,
    Rx=1000.0,
    Rs=1000.0,
    Ix=0.001,
    tiempo_inversion=8,
    num_muestras=35,
    num_stats=25,
    csv_file=ruta_csv
)
bridge.close()

