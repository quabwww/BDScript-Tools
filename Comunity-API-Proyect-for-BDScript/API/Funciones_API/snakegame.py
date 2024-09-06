from typing import List, Dict, Tuple
import random

class JuegoGusanito:
    def __init__(self, id_juego: int, ancho: int = 15, alto: int = 15):
        self.id_juego = id_juego
        self.ancho = ancho
        self.alto = alto
        self.gusano = [(ancho // 2, alto // 2)]
        self.direccion = 'DERECHA'
        self.juego_terminado = False
        self.comida = self.generar_comida()
        self.tablero = self.crear_tablero()

    def crear_tablero(self) -> List[List[str]]:
        tablero = [[' ' for _ in range(self.ancho)] for _ in range(self.alto)]
        for x, y in self.gusano:
            tablero[y][x] = 'x'
        tablero[self.comida[1]][self.comida[0]] = 'o'
        return tablero

    def generar_comida(self) -> Tuple[int, int]:
        posiciones_libres = [
            (x, y) for x in range(self.ancho) for y in range(self.alto)
            if (x, y) not in self.gusano
        ]

        if not posiciones_libres:
            self.juego_terminado = True
            return None  # Juego terminado por falta de espacio

        return random.choice(posiciones_libres)

    def mover(self, direccion: str) -> Dict[str, str]:
        if self.juego_terminado:
            return {"juego": "Juego Terminado"}

        self.direccion = direccion
        cabeza_x, cabeza_y = self.gusano[0]

        if direccion == 'ARRIBA':
            nueva_cabeza = (cabeza_x, cabeza_y - 1)
        elif direccion == 'ABAJO':
            nueva_cabeza = (cabeza_x, cabeza_y + 1)
        elif direccion == 'IZQUIERDA':
            nueva_cabeza = (cabeza_x - 1, cabeza_y)
        elif direccion == 'DERECHA':
            nueva_cabeza = (cabeza_x + 1, cabeza_y)
        else:
            return {"juego": "Movimiento no válido"}

        if (
            nueva_cabeza in self.gusano or
            nueva_cabeza[0] < 0 or nueva_cabeza[0] >= self.ancho or
            nueva_cabeza[1] < 0 or nueva_cabeza[1] >= self.alto
        ):
            self.juego_terminado = True
            return {"juego": "Juego Terminado"}

        self.gusano = [nueva_cabeza] + self.gusano[:-1]

        if nueva_cabeza == self.comida:
            self.gusano.append(self.gusano[-1])
            self.comida = self.generar_comida()

        self.tablero = self.crear_tablero()
        return self.obtener_estado_juego()

    def obtener_estado_juego(self) -> Dict[str, str]:
        if self.juego_terminado:
            return {"juego": "Juego Terminado"}
        
        return {"juego": '\n'.join([''.join(fila) for fila in self.tablero])}
