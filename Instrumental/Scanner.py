from pyvisa import ResourceManager
import time

ADDRESS_GPIB = "hpib7,18"
SALIDA_1 = "S"
SALIDA_2 = "X"
NADA = 63
RESET_TODO = 112 

class ScannerInti(object):
    
    def __init__(self):
        self._scanner = ResourceManager().open_resource("GPIB0::18::INSTR", open_timeout = 1000)
        self._scanner.open()
        self._scanner.clear()
        self._scanner.timeout = 1000
    
    def ConfiguracionPuerto(self, direccion):
        self._scanner.write(str(direccion)+"C2X\n")
    
    def ConfiguracionFormato(self, direccion):
        self._scanner.write(str(direccion)+"F3X\n")
    
    def Configuracion(self, direccion):
        self.ConfiguracionPuerto(direccion)
        self.ConfiguracionFormato(direccion)
    
    def EnviarDato(self, direccion, dato):
        seleccionarPuerto1 = "P1X\n"
        enviarDato = str(direccion) + "D%dZX\n" + str(dato)
        self._scanner.write(seleccionarPuerto1)
        self._scanner.write(enviarDato)
    
    def ResetGeneral(self, direccion):
        self.EnviarDato(direccion, RESET_TODO)
    
    def Decodificacion(self, puerto, entrada):
        entrada -= 1
        if puerto == SALIDA_1:
            entrada += 16
        elif puerto == SALIDA_2:
            entrada += 32
        else:
            entrada = 0
        return entrada
    
    def Codificacion(self, puerto, entrada):
        if puerto == SALIDA_1:
            if entrada != NADA:
                entrada += 1
            else:
                entrada = 0
        elif puerto == SALIDA_2:
            if entrada != NADA:
                entrada += 1-24
            else:
                entrada = 0
        return entrada
    
    def Ver(self, direccion, salida): 
        if salida == SALIDA_1:
            self._scanner.write("P3X\n")
            dato = self._scanner.read()
        elif salida == SALIDA_2:
            self._scanner.write("P4X\n")
            dato = self._scanner.read()
        return int(dato)
    
    def InvertirCanal(self, direccion):
        temp1 = self.Ver(direccion, SALIDA_1)
        temp2 = self.Ver(direccion, SALIDA_2)
        if temp1!=NADA and temp2!=NADA:
            temp2 -=24
            self.ResetCanal(direccion, SALIDA_1, temp1 + 1)
            time.sleep(20)
            self.SetearCanal(direccion, SALIDA_2, temp1 + 1)
            time.sleep(40)
            self.SetearCanal(direccion, SALIDA_1, temp2 + 1)
            
    def SetearCanal(self, direccion, puerto, entrada):
        datoaescribir = self.Decodificacion(puerto, entrada)
        if datoaescribir != 0 :
            self.EnviarDato(direccion,datoaescribir)
        else:
            raise("Error en SetearCanal")
            
    def ResetCanal(self, direccion, puerto, entrada):
        datoaescribir = self.Decodificacion(puerto, entrada)
        if datoaescribir != 0:
            datoaescribir += 64
            self.EnviarDato(direccion, datoaescribir)
        else:
            raise("Error en ResetCanal")

    def Test(self):             
        e = self.ScannerInti()
        e.Configuracion(65535)
        e.SetearCanal(ADDRESS_GPIB,SALIDA_2,4)
        [x for x in dir(e._scanner) if "addr" in x]
        e._scanner.primary_address
        e._scanner.secondary_address