
from fastapi import FastAPI, APIRouter, HTTPException
from typing import List, Dict, Tuple
import random

# ==========================================
# JUEGO TETRIS
# ==========================================

class JuegoTetris:
    def __init__(self, id_juego: int, ancho: int = 8, alto: int = 20):
        self.id_juego = id_juego
        self.ancho = ancho
        self.alto = alto

        self.tablero = [
            ['-' for _ in range(ancho)]
            for _ in range(alto)
        ]

        self.piezas = {
            'I': [
                [(0, 1), (1, 1), (2, 1), (3, 1)],
                [(2, 0), (2, 1), (2, 2), (2, 3)]
            ],
            'O': [
                [(1, 0), (2, 0), (1, 1), (2, 1)]
            ],
            'T': [
                [(1, 0), (0, 1), (1, 1), (2, 1)],
                [(1, 0), (1, 1), (2, 1), (1, 2)],
                [(0, 1), (1, 1), (2, 1), (1, 2)],
                [(1, 0), (0, 1), (1, 1), (1, 2)]
            ],
            'S': [
                [(1, 0), (2, 0), (0, 1), (1, 1)],
                [(1, 0), (1, 1), (2, 1), (2, 2)]
            ],
            'Z': [
                [(0, 0), (1, 0), (1, 1), (2, 1)],
                [(2, 0), (1, 1), (2, 1), (1, 2)]
            ],
            'J': [
                [(0, 0), (0, 1), (1, 1), (2, 1)],
                [(1, 0), (2, 0), (1, 1), (1, 2)],
                [(0, 1), (1, 1), (2, 1), (2, 2)],
                [(1, 0), (1, 1), (0, 2), (1, 2)]
            ],
            'L': [
                [(2, 0), (0, 1), (1, 1), (2, 1)],
                [(1, 0), (1, 1), (1, 2), (2, 2)],
                [(0, 1), (1, 1), (2, 1), (0, 2)],
                [(0, 0), (1, 0), (1, 1), (1, 2)]
            ]
        }

        self.pieza_actual = None
        self.x = 3
        self.y = 0
        self.rotacion = 0

        self.puntuacion = 0
        self.lineas = 0
        self.nivel = 1
        self.juego_terminado = False

        self.generar_pieza()

    # --------------------------------------
    # GENERAR PIEZA
    # --------------------------------------

    def generar_pieza(self):
        tipo = random.choice(list(self.piezas.keys()))

        self.pieza_actual = tipo
        self.rotacion = 0
        self.x = 3
        self.y = 0

        if self.colisiona(self.x, self.y, self.rotacion):
            self.juego_terminado = True

    def obtener_bloques(self, rotacion=None):
        if rotacion is None:
            rotacion = self.rotacion

        formas = self.piezas[self.pieza_actual]
        return formas[rotacion % len(formas)]

    # --------------------------------------
    # DETECTAR COLISIONES
    # --------------------------------------

    def colisiona(self, x, y, rotacion):
        formas = self.piezas[self.pieza_actual]
        bloques = formas[rotacion % len(formas)]

        for dx, dy in bloques:
            nx = x + dx
            ny = y + dy

            if nx < 0 or nx >= self.ancho:
                return True

            if ny >= self.alto:
                return True

            if ny >= 0 and self.tablero[ny][nx] != '-':
                return True

        return False

    # --------------------------------------
    # FIJAR PIEZA EN EL TABLERO
    # --------------------------------------

    def fijar_pieza(self):
        for dx, dy in self.obtener_bloques():
            nx = self.x + dx
            ny = self.y + dy

            if 0 <= ny < self.alto:
                self.tablero[ny][nx] = self.pieza_actual

        self.eliminar_lineas()
        self.generar_pieza()

    # --------------------------------------
    # ELIMINAR LINEAS COMPLETAS
    # --------------------------------------

    def eliminar_lineas(self):
        tablero_nuevo = [
            fila for fila in self.tablero
            if '-' in fila
        ]

        lineas_eliminadas = self.alto - len(tablero_nuevo)

        for _ in range(lineas_eliminadas):
            tablero_nuevo.insert(
                0, ['-' for _ in range(self.ancho)]
            )

        self.tablero = tablero_nuevo

        self.lineas += lineas_eliminadas

        puntos = {
            1: 100,
            2: 300,
            3: 500,
            4: 800
        }

        self.puntuacion += puntos.get(
            lineas_eliminadas, 0
        ) * self.nivel

        self.nivel = (self.lineas // 10) + 1

    # --------------------------------------
    # MOVIMIENTOS
    # --------------------------------------

    def mover(self, direccion: str) -> Dict:
        if self.juego_terminado:
            return self.obtener_estado_juego()

        direccion = direccion.upper()

        # Validar movimiento
        if direccion not in self.MOVIMIENTOS:
            return {
                "estado_juego": "false",
                "mensaje": "Movimiento no válido",
                "movimientos_disponibles": self.MOVIMIENTOS
            }

    # Mover izquierda
    if direccion == "IZQUIERDA":
        if not self.colisiona(
            self.x - 1, self.y, self.rotacion
        ):
            self.x -= 1

        # Mover derecha
        elif direccion == "DERECHA":
            if not self.colisiona(
                self.x + 1, self.y, self.rotacion
            ):
                self.x += 1

        # Rotar pieza
        elif direccion == "ROTAR":
            formas = self.piezas[self.pieza_actual]

            nueva_rotacion = (
                self.rotacion + 1
            ) % len(formas)

            if not self.colisiona(
                self.x, self.y, nueva_rotacion
            ):
                self.rotacion = nueva_rotacion

    # Bajar una posición
    elif direccion == "BAJAR":
        if not self.colisiona(
            self.x, self.y + 1, self.rotacion
        ):
            self.y += 1
        else:
            self.fijar_pieza()

        # Caída instantánea
        elif direccion == "CAIDA":
            while not self.colisiona(
                self.x, self.y + 1, self.rotacion
            ):
                self.y += 1

            self.fijar_pieza()

        return self.obtener_estado_juego()

    # --------------------------------------
    # CAIDA AUTOMATICA (UN PASO)
    # --------------------------------------

    def avanzar(self) -> Dict:
        if self.juego_terminado:
            return self.obtener_estado_juego()

        if not self.colisiona(
            self.x, self.y + 1, self.rotacion
        ):
            self.y += 1
        else:
            self.fijar_pieza()

        return self.obtener_estado_juego()

    # --------------------------------------
    # CREAR TABLERO VISIBLE
    # --------------------------------------

    def crear_tablero(self) -> List[List[str]]:
        tablero = [fila[:] for fila in self.tablero]

        if not self.juego_terminado:
            for dx, dy in self.obtener_bloques():
                nx = self.x + dx
                ny = self.y + dy

                if 0 <= ny < self.alto:
                    tablero[ny][nx] = self.pieza_actual

        return tablero

    # --------------------------------------
    # ESTADO DEL JUEGO
    # --------------------------------------

    def obtener_estado_juego(self) -> Dict:
        tablero = self.crear_tablero()

        return {
            "id_juego": self.id_juego,
            "estado_juego": str(
                self.juego_terminado
            ).lower(),
            "puntuacion": self.puntuacion,
            "lineas": self.lineas,
            "nivel": self.nivel,
            "pieza_actual": self.pieza_actual,
            "juego": '\n'.join(
                ''.join(fila) for fila in tablero
            )
        }


# ==========================================
# API FASTAPI
# ==========================================



router = APIRouter(prefix="/tetris", tags=["Tetris"])

juegos = {}
contador_juegos = 1


# --------------------------------------
# INICIAR JUEGO
# --------------------------------------

@router.get("/iniciar_juego/")
async def iniciar_juego():
    global contador_juegos

    id_juego = contador_juegos

    juegos[id_juego] = JuegoTetris(id_juego)

    contador_juegos += 1

    return {
        "id_juego": id_juego,
        "estado": juegos[id_juego].obtener_estado_juego()
    }


# --------------------------------------
# MOVER PIEZA
# --------------------------------------

@router.get("/mover/{id_juego}/")
async def mover(id_juego: int, direccion: str):
    if id_juego not in juegos:
        raise HTTPException(
            status_code=404,
            detail="Juego no encontrado"
        )

    return juegos[id_juego].mover(direccion)


# --------------------------------------
# AVANZAR / CAIDA AUTOMATICA
# --------------------------------------

@router.get("/avanzar/{id_juego}/")
async def avanzar(id_juego: int):
    if id_juego not in juegos:
        raise HTTPException(
            status_code=404,
            detail="Juego no encontrado"
        )

    return juegos[id_juego].avanzar()


# --------------------------------------
# CONSULTAR ESTADO
# --------------------------------------

@router.get("/estado/{id_juego}/")
async def obtener_estado(id_juego: int):
    if id_juego not in juegos:
        raise HTTPException(
            status_code=404,
            detail="Juego no encontrado"
        )

    return juegos[id_juego].obtener_estado_juego()


