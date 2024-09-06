from fastapi import FastAPI, APIRouter, HTTPException
from typing import List, Dict, Tuple
import random

# Juego del Gusanito
class JuegoGusanito:
    def __init__(self, id_juego: int, ancho: int = 15, alto: int = 10):
        self.id_juego = id_juego
        self.ancho = ancho
        self.alto = alto
        self.gusano = [(ancho // 2, alto // 2)]
        self.direccion = 'DERECHA'
        self.juego_terminado = False
        self.comida = self.generar_comida()
        self.tablero = self.crear_tablero()
        self.manzanas_comidas = 0  # Contador de manzanas comidas

    def crear_tablero(self) -> List[List[str]]:
        tablero = [['-' for _ in range(self.ancho)] for _ in range(self.alto)]
        for i, (x, y) in enumerate(self.gusano):
            if i == 0:
                tablero[y][x] = 'O'  # Cabeza del gusano
            else:
                tablero[y][x] = 'x'  # Cuerpo del gusano
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
            return {"estado_juego": "true", "manzanas_comidas": self.manzanas_comidas, "juego": "Juego Terminado"}

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
            return {"estado_juego": "false", "manzanas_comidas": self.manzanas_comidas, "juego": "Movimiento no válido"}

        if (
            nueva_cabeza in self.gusano or
            nueva_cabeza[0] < 0 or nueva_cabeza[0] >= self.ancho or
            nueva_cabeza[1] < 0 or nueva_cabeza[1] >= self.alto
        ):
            self.juego_terminado = True
            return {"estado_juego": "true", "manzanas_comidas": self.manzanas_comidas, "juego": "Juego Terminado"}

        self.gusano = [nueva_cabeza] + self.gusano[:-1]

        if nueva_cabeza == self.comida:
            self.gusano.append(self.gusano[-1])
            self.comida = self.generar_comida()
            self.manzanas_comidas += 1  # Incrementar el contador de manzanas comidas

        self.tablero = self.crear_tablero()
        return self.obtener_estado_juego()

    def obtener_estado_juego(self) -> Dict[str, str]:
        estado_juego = "true" if self.juego_terminado else "false"
        return {
            "estado_juego": estado_juego,
            "manzanas_comidas": self.manzanas_comidas,
            "juego": '\n'.join([''.join(fila) for fila in self.tablero])
        }

# API Router
router = APIRouter()
juegos = {}
contador_juegos = 1

@router.get("/iniciar_juego/")
async def iniciar_juego():
    global contador_juegos
    id_juego = contador_juegos
    juegos[id_juego] = JuegoGusanito(id_juego)
    contador_juegos += 1
    return {"id_juego": id_juego, "estado": juegos[id_juego].obtener_estado_juego()}

@router.get("/mover/{id_juego}/")
async def mover(id_juego: int, direccion: str):
    if id_juego not in juegos:
        raise HTTPException(status_code=404, detail="Juego no encontrado")
    return juegos[id_juego].mover(direccion.upper())

@router.get("/estado/{id_juego}/")
async def obtener_estado(id_juego: int):
    if id_juego not in juegos:
        raise HTTPException(status_code=404, detail="Juego no encontrado")
    return juegos[id_juego].obtener_estado_juego()

