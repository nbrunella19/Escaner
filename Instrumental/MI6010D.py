import time
import re
import pyvisa
import warnings
warnings.filterwarnings("ignore", message="read string doesn't end with termination characters")

class MI60100Error(Exception):
    """Excepción para errores devueltos por el 60100 (mensajes Ecnn)."""
    def __init__(self, code, message=None):
        super().__init__(f"MI60100 Error {code}: {message or ''}")
        self.code = code
        self.message = message

class MI60100:
    """
    Wrapper simple para controlar el MI-60100 por GPIB usando pyvisa.

    Constructor:
        MI60100(gpib_address, visa_backendspec=None, timeout_ms=20000)

    gpib_address: entero GPIB (ej: 15) o resource string completa "GPIB0::15::INSTR".
    timeout_ms: timeout de lectura/escritura (ms).
    """

    # Mapeo parcial de errores (ver Apéndice A4). Completar según necesidad.
    ERROR_LOOKUP = {
        2: "VALUE MISSING",
        3: "ILLEGAL NOW",
        5: "TERM EXPECTED",
        6: "VAL INVALID CHAR",
        7: "NOT REMOTE CTRL",
        8: "VALUE TOO LONG",
        9: "VAL BAD",
        10: "VALUE CANNOT DECODE",
        11: "NEED STANDBY OFF",
        12: "NEED IX ON",
        13: "CHECK CONNS",
        14: "LOW VOLT",
        15: "RATIO RANGE",
        25: "ERROR UNKNOWN",
    }

    def __init__(self, gpib_address, visa_backendspec=None, timeout_ms=20000):
        self.rm = pyvisa.ResourceManager(visa_backendspec) if visa_backendspec else pyvisa.ResourceManager()
        if isinstance(gpib_address, int):
            self.resource_name = f'GPIB0::{gpib_address}::INSTR'
        else:
            self.resource_name = gpib_address
        self.instr = self.rm.open_resource(self.resource_name)
        self.instr.timeout = int(timeout_ms)  # ms
        # Termination: manual reports in manual appear to be ASCII text (use default)
        # A menudo los dispositivos GPIB usan '\n' terminador; si hace falta, ajustar.
        self.instr.read_termination = '\r\n'
        self.instr.write_termination = '\r\n'
        #self.instr.read_termination = '\n'
        #self.instr.write_termination = '\n'
        #print(f"DEBUG: Write termination set to: '{self.instr.write_termination}'") # ¡Añade esta línea!

    # ---------------------
    # Low level helpers
    # ---------------------

    def _write(self, cmd: str):
        if not cmd.endswith("\r\n"):
            cmd = cmd + "\r\n"
        print(f"[DEBUG] Enviando: {repr(cmd)}")
        self.instr.write_raw(cmd.encode())  # fuerza bytes con CRLF
    """
    def _write(self, cmd: str):
        print(f"[DEBUG] Enviando: {repr(cmd)}")
        self.instr.write(cmd)
    """
    def _read(self, timeout_s=None):
        resp = self.instr.read().strip()
        # Si no termina con terminador esperado, añadirlo virtualmente
        if self.instr.read_termination and not resp.endswith(self.instr.read_termination.strip()):
            resp += self.instr.read_termination.strip()
        if resp.startswith('E') and len(resp) >= 2:
            m = re.search(r'E(.)(\d{1,2})', resp)
            if m:
                code = int(m.group(2))
                raise MI60100Error(code, self.ERROR_LOOKUP.get(code, "Unknown"))
            else:
                raise MI60100Error(None, f"Unknown error format: {resp}")
        return resp

    def _query(self, cmd: str, read=True):
        """Escribe y lee (si read=True) — combina write+read."""
        self._write(cmd)
        if read:
            return self._read()
        return None
    # ---------------------
    # Comandos básicos (según Apéndice A1/A3)
    # ---------------------
    def local_lockout(self):
        """K - Disables 'remote' (pasar a local lockout)."""
        self._write('K')

    def local_unlock(self):
        """u - Enables 'remote' (quita local lockout)."""
        self._write('u')   
    
    def standby(self):
        """s - Pone STANDBY ON para detener medición/calibración."""
        self._write('s')

    def calibrate(self):
        """e - Inicia calibración (puede devolver informe o error)."""
        self._write('e')
    
    def query(self):
        """Q - query según manual: devuelve cadena de estado tipo 'R S q' (leer doc)."""
        # El manual indica que el dispositivo responde con 3 caracteres, e.g. 'RSq' (R S q).
        self._write('Q')
        return self._read()
    

    def set_primary_current(self, value):
        """
        Establece la corriente primaria (formato: lxxx o jxxx según presencia de extender).
        El manual documenta jxxx para extenders; usare 'l' para set corriente primaria estándar.
        value: número float -> comando 'l{value}' (usualmente ASCII float).
        """
        cmd = f"l{value}"
        self._write(cmd)

    def send_set_current_extender(self, value):
        """jxxx - enviar corriente cuando hay extender (6011) en el sistema."""
        cmd = f"j{value}"
        self._write(cmd)

    def set_delay_seconds(self, seconds:int):
        """Tnnn - Setea el tiempo de delay (reversa) en segundos (4..1000s)."""
        if not (4 <= seconds <= 1000):
            raise ValueError("Delay fuera de rango (4..1000).")
        self._write(f"T{int(seconds)}")

    def set_num_measurements(self, n:int):
        """Mnnn - Setea número de medidas a tomar (1..1e9)."""
        if n < 1:
            raise ValueError("num_measurements debe >= 1")
        self._write(f"M{int(n)}")

    def set_num_statistics(self, n:int):
        """Jnn - Setea número de estadísticas (2..50)."""
        if not (2 <= n <= 50):
            raise ValueError("num_statistics debe estar entre 2 y 50 (el bridge solo promedia hasta 50).")
        self._write(f"J{int(n)}")

    def start_measurements(self):
        """Comando que inicia mediciones (según el manual, enviar 'J' inicia si ya Jnn fue enviado)."""
        # En el manual: enviar 'Jnn' establece stats y luego otro comando inicia la medición.
        # Aquí asumimos que ya hubo configuración; el manual indica que el inicio es parte de Mnnn/Jnnn flow.
        # Si el dispositivo requiere un comando de inicio explícito distinto, usar send_raw.
        # En la sección A3/A1: la propia Mnnn arranca la secuencia si es aceptada. No obstante,
        # dejaremos un alias que puede enviar 'M1' para forzar inicio de una medida si hace falta.
        self._write('M1')

    def send_rx_value(self, value):
        """rxxx - envía valor de Rx al instrumento (floating point)."""
        self._write(f"r{value}")

    def set_rx_as_standard(self):
        """x - establecer Rx como estándar (según manual 'x')."""
        self._write('x')

    def set_rs_as_standard(self):
        """s - establecer Rs como estándar (según manual 's' en ciertas tablas). Atención: 's' también es STANDBY en otra parte."""
        # Nota: en manual hay múltiples usos del carácter 's' (standby) y 's' para Rs as standard;
        # para evitar ambigüedad se puede enviar 's' solo cuando el contexto lo permite.
        self._write('s')

    def increase_current_by_2(self):
        """V o L ??? - en manual hay indicación de increase/decrease currents; uno es 'V'/'X'/'L' segun snippet.
        Implementamos métodos directos para enviar las letras que el manual describe:
        - 'V' (increase current factor) y 'z'/'X' para otros.
        """
        # según extractos: 'V' = Send Current Factor? 'z' 'X' usados para cambiar factor.
        # Aquí dejamos 'V' como incremento (el comportamiento real depende del firmware).
        self._write('V')

    def decrease_current_by_2(self):
        """X - Decrease current (según manual 'X' indica decrease -v2)."""
        self._write('X')

    def set_filter_factor(self, n:int):
        """Gn - Setea filtro: n=1 (3 values), 2 (10 values), 3 (30 values)."""
        if n not in (1,2,3):
            raise ValueError("filter factor must be 1,2 or 3")
        self._write(f"G{n}")

    def send_prt_coefficients(self, a=None, b=None, c=None, d=None, c1=None, c2=None, c3=None, c4=None, c5=None):
        """Enviar coeficientes PRT: axxx, bxxx, cxxx, dxxx, exxx (c1), fxxx (c2) ... ixxx (c5)."""
        if a is not None: self._write(f"a{a}")
        if b is not None: self._write(f"b{b}")
        if c is not None: self._write(f"c{c}")
        if d is not None: self._write(f"d{d}")
        if c1 is not None: self._write(f"e{c1}")
        if c2 is not None: self._write(f"f{c2}")
        if c3 is not None: self._write(f"g{c3}")
        if c4 is not None: self._write(f"h{c4}")
        if c5 is not None: self._write(f"i{c5}")

    def send_raw(self, text:str, read_response=True):
        """Envia texto tal cual (útil para comandos no cubiertos) y devuelve respuesta opcional."""
        self._write(text)
        if read_response:
            return self._read()
        return None
    
    def single_measurement(self):
        """
        Realiza una única medición y devuelve el reporte crudo.
        Usa M1R para evitar problemas de sincronización.
        """
        return self._query("M1R")
    # ---------------------
    # Lectura de reportes (SRQ / Reports)
    # ---------------------
    def read_report(self):
        """
        Lee un reporte (cuando el 60100 ha hecho SRQ y hay datos).
        Simple wrapper para read(). Dependiendo del controlador GPIB y configuración,
        puede ser necesario hacer serial poll/handle SRQ en el controlador.
        """
        return self._read()
    
    # ---------------------
    # Método de reinicio
    # ---------------------
    def reset_bridge(self):
        """
        Intenta restablecer el puente MI-60100 a un estado conocido y limpio.
        Esto incluye:
        1. Poner el puente en modo STANDBY.
        2. Apagar la corriente primaria Ix.
        3. Intentar limpiar cualquier mensaje de error o reporte pendiente del búfer del instrumento.
        4. Verificar el estado para confirmar un reset parcial.
        """
        print("Intentando restablecer el puente MI-60100 a un estado conocido...")
        try:
            # 1. Poner en STANDBY [7, A1]
            print("Enviando comando 'standby'...")
            self.standby()
            # Una pequeña pausa puede ser útil para que el instrumento procese el comando [conversación anterior]
            time.sleep(0.1) 

            # 2. Intentar limpiar cualquier mensaje de error o reporte pendiente
            # Se usa un timeout más corto para esta operación de limpieza.
            print("Intentando limpiar el búfer de comunicación de cualquier mensaje pendiente...")
            original_timeout = self.instr.timeout
            # Establecer un timeout más corto (ej. 1 segundo = 1000 ms) para la limpieza
            self.instr.timeout = 1000 

            messages_cleared = []
            while True:
                try:
                    # Intentar leer cualquier cosa que el instrumento pueda haber enviado.
                    # El método _read() ya maneja los errores Ecnn elevando MI60100Error [3].
                    cleared_message = self._read()
                    messages_cleared.append(cleared_message)
                    print(f"Mensaje/Reporte leído durante la limpieza: '{cleared_message}'")
                except MI60100Error as e_mi:
                    # Si el instrumento reporta un error, lo registramos y continuamos intentando limpiar.
                    messages_cleared.append(f"Error MI60100: {e_mi.message} (Código: {e_mi.code})")
                    print(f"Error del instrumento durante la limpieza: {e_mi.message} (Código: {e_mi.code})")
                except pyvisa.errors.VisaIOError as e_visa:
                    # Esto es lo esperado cuando el búfer de lectura del instrumento está vacío y se produce un timeout.
                    print(f"Timeout de lectura durante la limpieza, búfer probablemente vacío: {e_visa}")
                    break # Salir del bucle de limpieza, ya no hay más mensajes.
                except Exception as e_generic:
                    # Capturar cualquier otro error inesperado que pudiera ocurrir durante la lectura.
                    print(f"Error inesperado durante la limpieza del búfer: {e_generic}")
                    break # Salir para evitar un bucle infinito en caso de un error irrecuperable.
            
            # Restaurar el timeout original del instrumento
            self.instr.timeout = original_timeout 

            if messages_cleared:
                print(f"Se limpiaron los siguientes mensajes/errores del búfer: {messages_cleared}")
            else:
                print("No se encontraron mensajes pendientes en el búfer de comunicación.")

            # 3. Verificar el estado final [A1, 7]
            # Después de la limpieza, se intenta una consulta de estado para confirmar la comunicación.
            final_status = self.query()
            print(f"Puente MI-60100 restablecido a estado: '{final_status}'")
            return True # Retorna True si el proceso de restablecimiento parece exitoso

        except MI60100Error as e:
            # Capturar errores del propio instrumento que impiden un reinicio.
            print(f"ERROR: Fallo al restablecer el puente MI-60100 debido a un error persistente del instrumento: {e.message} (Código: {e.code})")
            # Es importante relanzar el error para que el código que llamó a este método sepa que falló.
            raise 
        except Exception as e:
            # Capturar cualquier otro tipo de error inesperado (ej. problemas de conexión PyVISA).
            print(f"ERROR: Ocurrió un error inesperado al intentar restablecer el puente: {e}")
            raise 
    # ---------------------
    # Cierre
    # ---------------------
    def close(self):
        try:
            self.instr.close()
        except Exception:
            pass
        try:
            self.rm.close()
        except Exception:
            pass
