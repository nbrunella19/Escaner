def limpiar_pantalla():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def Menu_Temp(GPIB_DMM1,GPIB_DMM2, GPIB_DMM3):
    """Menú principal del sistema de medición"""
    while True:
        limpiar_pantalla()
        print("=" * 60)
        print("  SISTEMA DE MEDICIÓN Y CALIBRACIÓN - ESCANER INTI-MI6010D")
        print("=" * 60)
        print("\nConfiguración de sensores y multímetros para medición de temperatura")
        print("1 - Comenzar configuración")
        print("2 - Salir del programa")
        print("\n" + "-" * 60)

        opcion = input("Seleccione una opción (1-2): ")

        if opcion == "1":
            resultado = menu_sensores(GPIB_DMM1, GPIB_DMM2, GPIB_DMM3)
            if resultado:
                configuracion, GPIB_DMM1, GPIB_DMM2, GPIB_DMM3 = resultado
                mostrar_resumen(configuracion)
                return configuracion, GPIB_DMM1, GPIB_DMM2, GPIB_DMM3
        elif opcion == "2":
            limpiar_pantalla()
            print("Gracias por usar el sistema. ¡Hasta pronto!")
            return None, GPIB_DMM1, GPIB_DMM2, GPIB_DMM3
        else:
            print("❌ Opción inválida. Intente de nuevo.")
            input("Presione Enter para continuar...")
            
    

def menu_sensores(GPIB_DMM1,GPIB_DMM2, GPIB_DMM3):
    
    """Menú para seleccionar sensores/resistores"""
    configuracion = {
        "sensores": [],
        "multimetros": {}
    }
    
    while True:
        limpiar_pantalla()
        print("=" * 60)
        print("  SELECCIONAR SENSORES/RESISTORES")
        print("=" * 60)
        print("\n¿Cuántos sensores desea utilizar?")
        print("1 - 1 sensor")
        print("2 - 2 sensores")
        print("3 - 3 sensores")
        print("4 - Volver al menú principal")
        print("\n" + "-" * 60)

        opcion = input("Seleccione una opción (1-4): ")

        if opcion in ["1", "2", "3"]:
            
            cantidad = int(opcion)
            configuracion["sensores"] = []
            configuracion["multimetros"] = {}
            
            # Seleccionar cada sensor y su multímetro asociado
            for i in range(cantidad):
                sensor = seleccionar_sensor(i + 1)
                if sensor is None:
                    break

                resultado_mmm = seleccionar_multimetro(sensor, configuracion["multimetros"], GPIB_DMM1, GPIB_DMM2, GPIB_DMM3)
                if resultado_mmm is None:
                    break

                multimetro, GPIB_DMM1, GPIB_DMM2, GPIB_DMM3 = resultado_mmm
                configuracion["sensores"].append(sensor)
                configuracion["multimetros"][sensor] = multimetro
            
            if len(configuracion["sensores"]) == cantidad:
                return configuracion, GPIB_DMM1, GPIB_DMM2, GPIB_DMM3
        elif opcion == "4":
            return None
        else:
            print("❌ Opción inválida. Intente de nuevo.")
            input("Presione Enter para continuar...")


def seleccionar_sensor(numero):
    """Menú para seleccionar un sensor específico"""
    sensores_disponibles = {
        "1": "LPC-PT100-01",
        "2": "LPC-PT100-02",
        "3": "LPC-PT100-03",
        "4": "LPC-PT100-04",
        "5": "LPC-PT100-05",
        "6": "LPC-PT100-06",
        "7": "ROSEMOUNT"
    }
    
    while True:
        limpiar_pantalla()
        print("=" * 60)
        print(f"  SELECCIONAR SENSOR #{numero}")
        print("=" * 60)
        print("\nSensores disponibles:")
        for clave, nombre in sensores_disponibles.items():
            print(f"{clave} - {nombre}")
        print("0 - Volver")
        print("\n" + "-" * 60)

        opcion = input("Seleccione una opción: ")

        if opcion in sensores_disponibles:
            return sensores_disponibles[opcion]
        elif opcion == "0":
            return None
        else:
            print("❌ Opción inválida. Intente de nuevo.")
            input("Presione Enter para continuar...")


def seleccionar_multimetro(sensor, multimetros_seleccionados, GPIB_DMM1, GPIB_DMM2, GPIB_DMM3):
    """Menú para seleccionar el multímetro asociado a un sensor y editar su puerto GPIB"""
    multimetros_disponibles = {
        "1": {"nombre": "HP34401A", "GPIB Default": f"GPIB0::{GPIB_DMM1}::INSTR"},
        "2": {"nombre": "HP34420A", "GPIB Default": f"GPIB0::{GPIB_DMM2}::INSTR"},
        "3": {"nombre": "HP3458A",  "GPIB Default": f"GPIB0::{GPIB_DMM3}::INSTR"}
    }
    
    puertos_usados = {
        int(dmm["GPIB Default"].split("::")[1])
        for dmm in multimetros_seleccionados.values()
    }
    
    while True:
        limpiar_pantalla()
        print("=" * 60)
        print(f"  ASIGNAR MULTÍMETRO PARA SENSOR: {sensor}")
        print("=" * 60)
        print("\nMultímetros disponibles:")
        for clave, dmm in multimetros_disponibles.items():
            print(f"{clave} - {dmm['nombre']} ({dmm['GPIB Default']})")
        print("0 - Volver")
        print("\n" + "-" * 60)

        opcion = input("Seleccione una opción: ")

        if opcion in multimetros_disponibles:
            dmm = multimetros_disponibles[opcion].copy()
            default_num = int(dmm["GPIB Default"].split("::")[1])

            while True:
                entrada = input(
                    f"Para cambiar el puerto GPIB por defecto que es el {dmm['nombre']} [{default_num}] Ingresarlo" \
                    "(Sino dejar vacío para cargar valor por default o escribir 'cancelar' para volver): "
                ).strip()

                if entrada.lower() in {"cancelar", "cancel", "c"}:
                    return None

                if entrada == "":
                    puerto_num = default_num
                else:
                    if not entrada.isdigit():
                        print("❌ Debe introducir solo dígitos para el número de GPIB.")
                        continue
                    puerto_num = int(entrada)

                if puerto_num in puertos_usados:
                    print(f"❌ El puerto GPIB {puerto_num} ya está asignado. Intente con otro.")
                    continue

                if puerto_num < 0 or puerto_num > 30:
                    print("❌ El número de GPIB debe estar entre 0 y 30.")
                    continue

                dmm["GPIB Default"] = f"GPIB0::{puerto_num}::INSTR"
                
                if opcion == "1":
                    GPIB_DMM1 = puerto_num
                elif opcion == "2":
                    GPIB_DMM2 = puerto_num
                else:
                    GPIB_DMM3 = puerto_num
                
                return dmm, GPIB_DMM1, GPIB_DMM2, GPIB_DMM3

        elif opcion == "0":
            return None
        else:
            print("❌ Opción inválida. Intente de nuevo.")
            input("Presione Enter para continuar...")


def mostrar_resumen(configuracion):
    """Muestra el resumen de la configuración elegida"""
    while True:
        limpiar_pantalla()
        print("=" * 60)
        print("  RESUMEN DE CONFIGURACIÓN")
        print("=" * 60)
        
        print("\n📊 SENSORES/RESISTORES SELECCIONADOS:")
        for i, sensor in enumerate(configuracion["sensores"], 1):
            print(f"  Sensor {i}: {sensor}")
        
        print("\n🔌 MULTÍMETROS ASIGNADOS:")
        for i, sensor in enumerate(configuracion["sensores"], 1):
            dmm_info = configuracion["multimetros"].get(sensor, {})
            nombre = dmm_info.get("nombre", "No asignado")
            puerto = dmm_info.get("GPIB Default", "-")
            print(f"  Sensor {i}: {sensor}")
            print(f"    Instrumento: {nombre}")
            print(f"    Puerto GPIB: {puerto}")
        
        print("\n" + "=" * 60)
        print("1 - Confirmar y continuar")
        print("2 - Editar configuración")
        print("3 - Volver al menú principal")
        print("\n" + "-" * 60)

        opcion = input("Seleccione una opción (1-3): ")

        if opcion == "1":
            limpiar_pantalla()
            print("=" * 60)
            print("  ✓ CONFIGURACIÓN GUARDADA")
            print("=" * 60)
            print("\n¡Sistema listo para comenzar mediciones!")
            print("\nPresione Enter para terminar...")
            input()
            return
        elif opcion == "2":
            return
        elif opcion == "3":
            return
        else:
            print("❌ Opción inválida. Intente de nuevo.")
            input("Presione Enter para continuar...")



# Ejecutar programa
if __name__ == "__main__":
    resultado = Menu_Temp(14, 13, 26)
    if resultado:
        configuracion, GP1, GP2, GP3 = resultado
        print(f"\n✅ GPIB Finales: DMM1={GP1}, DMM2={GP2}, DMM3={GP3}")