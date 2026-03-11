import pyvisa
import time

def Reset(puente):
    """
    Secuencia segura de reinicio lógico del MI60100
    """
    try:
        print("Deteniendo medición...")
        puente.write('S')  # Stop - Standby
        time.sleep(1)

        print("Limpiando estado...")
        puente.clear()  # Limpia el bus GPIB
        Flush_buffer(puente)
        print("Puente reiniciado.")

    except Exception as e:
        print("Error durante el reset:", e)  
        
def Flush_buffer(puente):
    print("Vaciando buffer...")
    puente.timeout = 500
    while True:
        try:
            msg = puente.read()
            print("  >>", msg)
        except:
            break
    puente.timeout = 20000  

def configurar_y_medir():

    # Parámetros
    Rs = 1
    Rx = 1
    t = 8
    n_medidas = 10
    n_stats = 5
    corriente = 0.1  # 100 mA

    rm = pyvisa.ResourceManager()
    recurso = "GPIB0::15::INSTR"

    inst = rm.open_resource(recurso)

    inst.write_termination = '\n'
    #inst.read_termination = None
    inst.read_termination = '\n'
    inst.timeout = 15000

    print("Conectado al 6010D")

    Reset(inst)
    
    # 1️⃣ Remote
    inst.write("R")
    time.sleep(0.5)

    # 2️⃣ Standby OFF
    inst.write("S")
    time.sleep(0.5)

    # 3️⃣ Definir estándar (ejemplo: Rs como estándar)
    inst.write("s")
    time.sleep(0.5)

    # 4️⃣ Enviar valores
    inst.write(f"A{Rs}")  # Rs
    time.sleep(0.2)

    inst.write(f"r{Rx}")  # Rx
    time.sleep(0.2)

    # 5️⃣ Corriente
    inst.write(f"I{corriente}")
    time.sleep(0.5)

    # 6️⃣ Delay
    inst.write(f"T{t}")
    time.sleep(0.5)

    # 8️⃣ Medición
    inst.write(f"M{n_medidas}")
    time.sleep(0.5)
    
    # 7️⃣ Estadísticas
    inst.write(f"J{n_stats}")
    time.sleep(0.5)

    print("\nParámetros configurados correctamente.")

    ratios = []

    while len(ratios) < n_medidas:
        try:
            respuesta = inst.read().strip()
            print("Recibido:", respuesta)

            if respuesta.startswith("&"):
                ratios.append(float(respuesta[1:]))

            elif respuesta.startswith("E"):
                print("Error:", respuesta)
                break

        except pyvisa.errors.VisaIOError:
            continue

    print("\nRatios obtenidos:")
    for i, r in enumerate(ratios, 1):
        print(f"{i}: {r}")

    inst.close()
    print("\nConexión cerrada.")

if __name__ == "__main__":
    configurar_y_medir()