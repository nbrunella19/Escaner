import numpy as np
import time

import os
import sys
# Hay que poner esto para que me tome el modulo MI6010D
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Instrumental.MI6010D import MI60100, MI60100Error


class Medida:
    def __init__(self, bridge_address="GPIB0::15::INSTR", verbose=True):
        self.bridge = MI60100(bridge_address)
        self.verbose = verbose

    def configurar_puente(self, Rs, Ix, t, n_medidas, n_stats):
        """Configura el puente con parámetros de medición"""
        self.bridge._write(f"A{Rs}")       # set resistencia
        self.bridge._write(f"I{Ix}")       # set corriente
        self.bridge._write(f"T{t}")        # tiempo
        self.bridge._write(f"M{n_medidas}")# número de medidas
        self.bridge._write(f"J{n_stats}")  # número de estadísticas
        self.bridge._write("R")            # remoto

    def medir(self, Rs, Ix, t, n_medidas, n_stats):
        """Ejecuta la secuencia de medición solo con el puente MI60100"""
        self.configurar_puente(Rs, Ix, t, n_medidas, n_stats)

        rel = np.zeros(n_medidas)

        for i in range(n_medidas):
            try:
                dato = self.bridge._read().strip()   # 👈 en vez de self.bridge.query()
            except MI60100Error as e:
                print(f"[ERROR] Puente devolvió error: {e}")
                break

            if dato.startswith("&"):
                rel[i] = float(dato[1:])
                if self.verbose:
                    print(f"[{i+1}/{n_medidas}] Rel = {rel[i]}")
            else:
                if self.verbose:
                    print(f"[{i+1}/{n_medidas}] Mensaje: {dato}")

            time.sleep(0.5)  # ajusta según velocidad real

        # Calcular promedio de las últimas n_stats muestras válidas
        medidas_validas = rel[rel != 0]
        rel_prom = np.mean(medidas_validas[-n_stats:]) if len(medidas_validas) >= n_stats else None

        return {
            "relaciones": medidas_validas,
            "rel_prom": rel_prom,
        }

    def close(self):
        try:
            self.bridge.standby()
            self.bridge.local_unlock()
        except Exception:
            pass
        self.bridge.rm.close()
        if self.verbose:
            print("[INFO] Conexión cerrada correctamente.")