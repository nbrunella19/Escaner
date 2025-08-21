from Medida import Medida
import numpy as np
def main():
    Rs = 1.0
    Ix = 0.001
    t = 5
    n_medidas = 10
    n_stats = 5

    medida = Medida("GPIB0::15::INSTR", verbose=True)
    try:
        medida.medir(Rs, Ix, t, n_medidas, n_stats)
        
        # Realizar mediciones
        rel = []
        for i in range(n_medidas):
            try:
                dato = medida.bridge.single_measurement().strip()  # Aquí se inicia y obtiene la medida
                if dato.startswith("&"):
                    valor = float(dato[1:])
                    rel.append(valor)
                    if medida.verbose:
                        print(f"[{i+1}/{n_medidas}] Rel = {valor}")
                else:
                    if medida.verbose:
                        print(f"[{i+1}/{n_medidas}] Mensaje: {dato}")
            except Exception as e:
                print(f"[ERROR] Medición {i+1}: {e}")
        
        # Promedio últimas n_stats medidas válidas
        rel_validas = np.array(rel)
        rel_prom = np.mean(rel_validas[-n_stats:]) if len(rel_validas) >= n_stats else None

        print("\n=== Resultados ===")
        print("Todas las relaciones:", rel_validas)
        print(f"Promedio últimas {n_stats}: {rel_prom}")

    finally:
        medida.close()

if __name__ == "__main__":
    main()