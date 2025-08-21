from Medida import Medida

def main():
    Rs = 1.0
    Ix = 0.001
    t = 5
    n_medidas = 10
    n_stats = 5

    medida = Medida("GPIB0::15::INSTR", verbose=True)

    try:
        resultados = medida.medir(Rs, Ix, t, n_medidas, n_stats)

        print("\n=== Resultados ===")
        print("Todas las relaciones:", resultados["relaciones"])
        print(f"Promedio últimas {n_stats}: {resultados['rel_prom']}")

    finally:
        medida.close()

if __name__ == "__main__":
    main()
