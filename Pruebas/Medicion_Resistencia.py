import sys
import os
import re
import csv
import time
from datetime import datetime
from datetime import date

# Asumiendo que Instrumental.MI6010D ya está en el sys.path o que la clase MI60100 está directamente accesible.
# Si la clase MI60100 está en el mismo directorio o un subdirectorio accesible,
# la siguiente línea podría necesitar ajustarse según la estructura de tu proyecto.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Instrumental.MI6010D import MI60100 # Esta línea importa la clase MI60100 [9].

# Carpeta donde está el script actual
base_dir = os.path.dirname(os.path.abspath(__file__))

# Nombre dinámico con la fecha de hoy
nombre_csv = f"Medicion_{date.today().isoformat()}.csv"

# Ruta completa (al lado del script)
ruta_csv = os.path.join(base_dir, nombre_csv)

def parse_report(report: str) -> dict:
    """
    Parser específico para reportes del MI60100.
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

def medir_resistencia_unica(mi: MI60100, Rx: float, Rs: float, Ix: float, csv_file: str = "medicion_unica.csv"):
    """
    Configura el puente y toma una única medición.
    """
    # 1. Standby
    mi.standby()
    time.sleep(0.1)

    # 2. Rs como estándar
    mi.send_rx_value(Rs)
    time.sleep(0.1)
    mi.set_rs_as_standard()
    time.sleep(0.1)

    # 3. Rx nominal
    mi.send_rx_value(Rx)
    time.sleep(0.1)

    # 4. Corriente (esto ya enciende Ix)
    mi.set_primary_current(Ix)
    time.sleep(0.2)

    # 5. Medir
    rep = mi.single_measurement()  # pequeña pausa extra
    parsed = parse_report(rep)

    # 6. Guardar en CSV
    fieldnames = ["timestamp", "ratio", "Rs", "Rx", "media", "std_ppm", "incertidumbre_ppm", "raw"]
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(parsed)

    return parsed

# Instanciación y uso del puente
# GPIB #15
bridge = MI60100(15) 
# Deshabilita el local lockout para control remoto.
bridge.local_unlock() 
# Realiza un query del estado del instrumento.
print("Estado:", bridge.query()) 

# Realiza un query del estado del instrumento .
Resultados = medir_resistencia_unica(
    bridge,
    Rx=1,
    Rs=1,
    Ix=0.001,
    csv_file=ruta_csv
)

print("Resultados de la medición:", Resultados)

bridge.close() # Cierra la conexión GPIB [18, 22].

