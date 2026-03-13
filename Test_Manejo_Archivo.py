import sys
import Manejo_Archivos.Func_Datos
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def Test():
    print("Ejecutando test de Manejo de Archivos...")
    Manejo_Archivos.Func_Datos.Set_Directories(
        cliente="Test_Cliente",
        nombre_resistor="Test_Resistor"
    )



if __name__ == "__main__":
    Test()