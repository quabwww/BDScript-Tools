from fastapi import FastAPI, APIRouter, HTTPException
from typing import List, Dict, Tuple
import random

# Definir las piezas del Tetris usando emojis
PIEZAS = {
    'I': [['⬛', '⬛', '⬛', '⬛']],
    'O': [['🟨', '🟨'], ['🟨', '🟨']],
    'T': [['⬛', '🟪', '⬛'], ['🟪', '🟪', '🟪']],
    'S': [['⬛', '🟩', '🟩'], ['🟩', '🟩', '⬛']],
    'Z': [['🟦', '🟦', '⬛'], ['⬛', '🟦', '🟦']],
    'J': [['🟫', '⬛', '⬛'], ['🟫', '🟫', '🟫']],
    'L': [['⬛', '⬛', '🟧'], ['🟧', '🟧', '🟧']]
}

# Clase del juego Tetris
class JuegoTetris:
    def __init__(self, ancho: int = 10, alto: int = 18):
        self.ancho = ancho
        self.alto = alto
        self.tablero = [['⬛' for _ in range(ancho)] for _ in range(alto)]
        self.pieza_actual = self.generar_pieza()
        self.posicion_pieza = [0, ancho // 2 - 1]
        self.juego_terminado = False
        self.actualizar_tablero()  # Colocar la primera pieza en el tablero

    def generar_pieza(self) -> List[List[str]]:
        pieza = random.choice(list(PIEZAS.values()))
        return pieza

    def colision(self, nueva_posicion: Tuple[int, int]) -> bool:
        for i, fila in enumerate(self.pieza_actual):
            for j, cuadro in enumerate(fila):
                if cuadro != '⬛':
                    x, y = nueva_posicion[0] + i, nueva_posicion[1] + j
                    if x >= self.alto or y < 0 or y >= self.ancho or self.tablero[x][y] != '⬛':
                        return True
        return False

    def fijar_pieza(self):
        for i, fila in enumerate(self.pieza_actual):
            for j, cuadro in enumerate(fila):
                if cuadro != '⬛':
                    x, y = self.posicion_pieza[0] + i, self.posicion_pieza[1] + j
                    self.tablero[x][y] = cuadro
        self.pieza_actual = self.generar_pieza()
        self.posicion_pieza = [0, self.ancho // 2 - 1]

        if self.colision(self.posicion_pieza):
            self.juego_terminado = True

    def limpiar_lineas(self):
        self.tablero = [fila for fila in self.tablero if '⬛' in fila]
        while len(self.tablero) < self.alto:
            self.tablero.insert(0, ['⬛' for _ in range(self.ancho)])

    def mover_pieza(self, direccion: str):
        if self.juego_terminado:
            return

        nueva_posicion = self.posicion_pieza.copy()
        if direccion == "IZQUIERDA":
            nueva_posicion[1] -= 1
        elif direccion == "DERECHA":
            nueva_posicion[1] += 1
        elif direccion == "ABAJO":
            while not self.colision([nueva_posicion[0] + 1, nueva_posicion[1]]):
                nueva_posicion[0] += 1

        if not self.colision(nueva_posicion):
            self.posicion_pieza = nueva_posicion
        elif direccion == "ABAJO":
            self.fijar_pieza()
            self.limpiar_lineas()

        self.actualizar_tablero()

    def actualizar_tablero(self):
        # Limpiar el tablero
        self.tablero = [['⬛' for _ in range(self.ancho)] for _ in range(self.alto)]
        
        # Dibujar la pieza en su nueva posición
        for i, fila in enumerate(self.pieza_actual):
            for j, cuadro in enumerate(fila):
                if cuadro != '⬛':
                    x, y = self.posicion_pieza[0] + i, self.posicion_pieza[1] + j
                    if 0 <= x < self.alto and 0 <= y < self.ancho:
                        self.tablero[x][y] = cuadro

    def obtener_estado_juego(self) -> str:
        if self.juego_terminado:
            return "Juego Terminado"
        
        return '\n'.join([''.join(fila) for fila in self.tablero])

# API Router
router = APIRouter()
juegos = {}
contador_juegos = 1

@router.get("/iniciar-tetris/")
async def iniciar_juego():
    global contador_juegos
    id_juego = contador_juegos
    juegos[id_juego] = JuegoTetris()
    contador_juegos += 1
    return {"id_juego": id_juego, "estado": juegos[id_juego].obtener_estado_juego()}

@router.get("/mover-tetris/{id_juego}/")
async def mover(id_juego: int, direccion: str):
    if id_juego not in juegos:
        raise HTTPException(status_code=404, detail="Juego no encontrado")
    juegos[id_juego].mover_pieza(direccion.upper())
    return {"estado": juegos[id_juego].obtener_estado_juego()}

@router.get("/estado-tetris/{id_juego}/")
async def obtener_estado(id_juego: int):
    if id_juego not in juegos:
        raise HTTPException(status_code=404, detail="Juego no encontrado")
    return {"estado": juegos[id_juego].obtener_estado_juego()}


@router.get("/estado-tetris/{id_juego}/")
async def obtener_estado(id_juego: int):
    if id_juego not in juegos:
        raise HTTPException(status_code=404, detail="Juego no encontrado")
    return {"estado": juegos[id_juego].obtener_estado_juego()}


