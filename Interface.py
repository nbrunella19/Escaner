import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import datetime

# Carpeta predeterminada donde se guardarán los archivos
ruta_predeterminada = Path.cwd() / "Config"
ruta_predeterminada.mkdir(exist_ok=True)  # Crear la carpeta si no existe

def generar_nombre_archivo():
    """ Genera un nombre de archivo con fecha y hora. """
    fecha_hora = datetime.datetime.now()
    return fecha_hora.strftime("Medicion_%Y-%m-%d_%H-%M-%S.txt")

def guardar_texto():
    """ Guarda el contenido del TextBox en la ruta seleccionada. """
    texto = entrada.get("1.0", tk.END).strip()
    if texto:
        nombre_archivo = generar_nombre_archivo()
        ruta_archivo = ruta_predeterminada / nombre_archivo
        with open(ruta_archivo, "w", encoding="utf-8") as archivo:
            archivo.write(texto)
        messagebox.showinfo("Éxito", f"Texto guardado en:\n{ruta_archivo}")
    else:
        messagebox.showwarning("Advertencia", "La caja de texto está vacía.")

def cambiar_carpeta():
    """ Permite al usuario seleccionar una nueva carpeta y actualiza la ruta predeterminada. """
    global ruta_predeterminada
    nueva_ruta = filedialog.askdirectory(title="Seleccionar carpeta de guardado")
    if nueva_ruta:
        ruta_predeterminada = Path(nueva_ruta)
        label_ruta.config(text=f"Carpeta de guardado:\n{ruta_predeterminada.resolve()}")

def limpiar_texto():
    """ Borra el contenido de la caja de entrada. """
    entrada.delete("1.0", tk.END)

def cargar_texto():
    """ Permite seleccionar un archivo y carga su contenido en la caja de salida. """
    ruta_archivo = filedialog.askopenfilename(
        title="Seleccionar archivo de texto",
        filetypes=[("Archivos de texto", "*.txt")]
    )
    
    if ruta_archivo:
        with open(ruta_archivo, "r", encoding="utf-8") as archivo:
            contenido = archivo.read()
        
        salida.config(state=tk.NORMAL)
        salida.delete("1.0", tk.END)
        salida.insert("1.0", contenido)
        salida.config(state=tk.DISABLED)

        messagebox.showinfo("Éxito", f"Archivo cargado:\n{ruta_archivo}")

# Crear la ventana principal
ventana = tk.Tk()
ventana.title("Programador de Escáner")
ventana.geometry("900x450")

# Crear Notebook (pestañas)
notebook = ttk.Notebook(ventana)
notebook.pack(expand=True, fill="both")

# Crear los frames para cada pestaña
frame_configuracion = ttk.Frame(notebook)
frame_dispositivos = ttk.Frame(notebook)
frame_ejecucion = ttk.Frame(notebook)


# Agregar las pestañas al Notebook
notebook.add(frame_configuracion, text="Configuración")
notebook.add(frame_dispositivos, text="Instrmentos")
notebook.add(frame_ejecucion, text="Ejecución")


# ========== Pestaña "Configuración" ==========
label_ruta = tk.Label(frame_configuracion, text=f"Carpeta de guardado de configuración:\n{ruta_predeterminada.resolve()}", font=("Arial", 10), wraplength=350, justify="left")
label_ruta.pack(pady=5, anchor="w")

boton_cambiar_carpeta = tk.Button(frame_configuracion, text="Cambiar Carpeta", command=cambiar_carpeta)
boton_cambiar_carpeta.pack(pady=5, anchor="w")

label_entrada = tk.Label(frame_configuracion, text="Configuración:", font=("Arial", 12))
label_entrada.pack(pady=5, anchor="w")

entrada = tk.Text(frame_configuracion, height=10, wrap="word", font=("Arial", 10))
entrada.pack(pady=5, fill="x", padx=10)  # Se expande horizontalmente y queda alineado

frame_botones = tk.Frame(frame_configuracion)
frame_botones.pack(pady=5, anchor="w")

boton_guardar = tk.Button(frame_botones, text="Guardar", command=guardar_texto)
boton_guardar.grid(row=0, column=0, padx=5)

boton_limpiar = tk.Button(frame_botones, text="Limpiar", command=limpiar_texto)
boton_limpiar.grid(row=0, column=1, padx=5)

# ========== Pestaña "Ejecucion" ==========
boton_cargar = tk.Button(frame_ejecucion, text="Cargar Archivo", command=cargar_texto)
boton_cargar.pack(pady=5, anchor="w")

salida = tk.Text(frame_ejecucion, height=5, width=50, wrap="word", state=tk.DISABLED, font=("Arial", 10))
salida.pack(pady=5, fill="x", padx=10)

boton_ejecutar = tk.Button(frame_ejecucion, text="Ejecutar programa", command=cargar_texto)
boton_ejecutar.pack(pady=5, anchor="w")

frame_checkbuttons = tk.Frame(frame_ejecucion)
frame_checkbuttons.pack(pady=5, anchor="w")

label_output_s = tk.Label(frame_checkbuttons, text="Output S", font=("Arial", 12))
label_output_s.grid(row=0, column=0, sticky="w", padx=10)

checks_s = [tk.IntVar() for _ in range(5)]
frame_s = tk.Frame(frame_checkbuttons)
frame_s.grid(row=0, column=1, sticky="w")

for i in range(5):
    chk = tk.Checkbutton(frame_s, variable=checks_s[i])
    chk.pack(side=tk.LEFT, padx=2)

label_output_x = tk.Label(frame_checkbuttons, text="Output X", font=("Arial", 12))
label_output_x.grid(row=1, column=0, sticky="w", padx=10)

checks_x = [tk.IntVar() for _ in range(5)]
frame_x = tk.Frame(frame_checkbuttons)
frame_x.grid(row=1, column=1, sticky="w")

for i in range(5):
    chk = tk.Checkbutton(frame_x, variable=checks_x[i])
    chk.pack(side=tk.LEFT, padx=2)

# ========== Pestaña "Instrumentos" ==========
label_dispositivo1 = tk.Label(frame_dispositivos, text="Medición de Temperatura de Rs:", font=("Arial", 12))
label_dispositivo1.pack(pady=5, anchor="w")

opciones_dispositivos = ["HP3458A", "HP34401", "HP34420"]
opciones_GPIB = ["GPIB0::13::INSTR", "GPIB0::14::INSTR","GPIB0::15::INSTR", "GPIB0::18::INSTR", "GPIB0::26::INSTR"]

combobox_dispositivo1 = ttk.Combobox(frame_dispositivos, values=opciones_dispositivos, state="readonly")
combobox_dispositivo1.pack(pady=5, anchor="w")
combobox_dispositivo1.current(0)  # Seleccionar el primer elemento por defecto

label_dispositivo2 = tk.Label(frame_dispositivos, text="Medición de Temperatura de Rx:", font=("Arial", 12))
label_dispositivo2.pack(pady=5, anchor="w")

combobox_dispositivo2 = ttk.Combobox(frame_dispositivos, values=opciones_dispositivos, state="readonly")
combobox_dispositivo2.pack(pady=5, anchor="w")
combobox_dispositivo2.current(0)  # Seleccionar el primer elemento por defecto

# Ejecutar la ventana
ventana.mainloop()


#pyinstaller --onefile --windowed Text_box.py#