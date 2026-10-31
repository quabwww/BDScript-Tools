
from fastapi import FastAPI, APIRouter, HTTPException
from typing import List, Dict
import random

# ==========================================
# JUEGO TETRIS
# ==========================================

class JuegoTetris:

    MOVIMIENTOS = [
        "IZQUIERDA",
        "DERECHA",
        "ROTAR",
        "BAJAR",
        "CAIDA"
    ]

    def __init__(self, id_juego: int, ancho: int = 8, alto: int = 10):
        self.id_juego = id_juego
        self.ancho = ancho
        self.alto = alto

        self.tablero = [
            ['-' for _ in range(ancho)]
            for _ in range(alto)
        ]

        # Formas y rotaciones de las piezas
        self.piezas = {
            "I": [
                [(0, 0), (1, 0), (2, 0), (3, 0)],
                [(0, 0), (0, 1), (0, 2), (0, 3)]
            ],
            "O": [
                [(0, 0), (1, 0), (0, 1), (1, 1)]
            ],
            "T": [
                [(1, 0), (0, 1), (1, 1), (2, 1)],
                [(0, 0), (0, 1), (1, 1), (0, 2)],
                [(0, 0), (1, 0), (2, 0), (1, 1)],
                [(1, 0), (0, 1), (1, 1), (1, 2)]
            ],
            "S": [
                [(1, 0), (2, 0), (0, 1), (1, 1)],
                [(0, 0), (0, 1), (1, 1), (1, 2)]
            ],
            "Z": [
                [(0, 0), (1, 0), (1, 1), (2, 1)],
                [(1, 0), (0, 1), (1, 1), (0, 2)]
            ],
            "J": [
                [(0, 0), (0, 1), (1, 1), (2, 1)],
                [(0, 0), (1, 0), (0, 1), (0, 2)],
                [(0, 0), (1, 0), (2, 0), (2, 1)],
                [(1, 0), (1, 1), (0, 2), (1, 2)]
            ],
            "L": [
                [(2, 0), (0, 1), (1, 1), (2, 1)],
                [(0, 0), (0, 1), (0, 2), (1, 2)],
                [(0, 0), (1, 0), (2, 0), (0, 1)],
                [(0, 0), (1, 0), (1, 1), (1, 2)]
            ]
        }

        self.pieza_actual = None
        self.x = 2
        self.y = 0
        self.rotacion = 0

        self.puntuacion = 0
        self.lineas = 0
        self.nivel = 1
        self.juego_terminado = False

        self.generar_pieza()

    # ======================================
    # GENERAR NUEVA PIEZA
    # ======================================

    def generar_pieza(self):
        self.pieza_actual = random.choice(
            list(self.piezas.keys())
        )

        self.rotacion = 0
        self.x = 2
        self.y = 0

        # Si la nueva pieza no puede aparecer, termina
        if self.colisiona(self.x, self.y, self.rotacion):
            self.juego_terminado = True

    # ======================================
    # OBTENER BLOQUES DE LA PIEZA
    # ======================================

    def obtener_bloques(self, rotacion=None):
        if rotacion is None:
            rotacion = self.rotacion

        formas = self.piezas[self.pieza_actual]
        return formas[rotacion % len(formas)]

    # ======================================
    # COMPROBAR COLISIONES
    # ======================================

    def colisiona(self, x, y, rotacion):
        bloques = self.piezas[self.pieza_actual][
            rotacion % len(self.piezas[self.pieza_actual])
        ]

        for dx, dy in bloques:
            nx = x + dx
            ny = y + dy

            # Bordes laterales y base
            if nx < 0 or nx >= self.ancho:
                return True

            if ny >= self.alto:
                return True

            # Colisión con bloques fijados
            if ny >= 0 and self.tablero[ny][nx] != '-':
                return True

        return False

    # ======================================
    # FIJAR PIEZA EN EL TABLERO
    # ======================================

    def fijar_pieza(self):
        bloques = self.obtener_bloques()

        # Si algún bloque queda fuera por arriba
        for dx, dy in bloques:
            if self.y + dy < 0:
                self.juego_terminado = True
                return

        # Fijar la pieza
        for dx, dy in bloques:
            nx = self.x + dx
            ny = self.y + dy

            self.tablero[ny][nx] = self.pieza_actual

        # Eliminar líneas completas
        self.eliminar_lineas()

        # Generar la siguiente pieza
        self.generar_pieza()

    # ======================================
    # ELIMINAR LINEAS COMPLETAS
    # ======================================

    def eliminar_lineas(self):
        tablero_nuevo = [
            fila for fila in self.tablero
            if '-' in fila
        ]

        eliminadas = self.alto - len(tablero_nuevo)

        for _ in range(eliminadas):
            tablero_nuevo.insert(
                0, ['-' for _ in range(self.ancho)]
            )

        self.tablero = tablero_nuevo
        self.lineas += eliminadas

        puntos = {
            1: 100,
            2: 300,
            3: 500,
            4: 800
        }

        self.puntuacion += (
            puntos.get(eliminadas, 0) * self.nivel
        )

        self.nivel = (self.lineas // 10) + 1

    # ======================================
    # MOVIMIENTOS DE LA PIEZA
    # ======================================

    def mover(self, direccion: str) -> Dict:
        direccion = direccion.upper()

        if self.juego_terminado:
            return self.obtener_estado_juego()

        if direccion not in self.MOVIMIENTOS:
            return {
                "estado_juego": "false",
                "mensaje": "Movimiento no válido",
                "movimientos_disponibles": self.MOVIMIENTOS
            }

        # Mover a la izquierda
        if direccion == "IZQUIERDA":
            if not self.colisiona(
                self.x - 1, self.y, self.rotacion
            ):
                self.x -= 1

        # Mover a la derecha
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

    # ======================================
    # CAIDA AUTOMATICA
    # ======================================

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

    # ======================================
    # CREAR TABLERO VISIBLE
    # ======================================

    def crear_tablero(self) -> List[List[str]]:
        tablero = [
            fila[:] for fila in self.tablero
        ]

        if not self.juego_terminado:
            for dx, dy in self.obtener_bloques():
                nx = self.x + dx
                ny = self.y + dy

                if 0 <= ny < self.alto:
                    tablero[ny][nx] = self.pieza_actual

        return tablero

    # ======================================
    # ESTADO DEL JUEGO
    # ======================================

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
            "movimientos_disponibles": self.MOVIMIENTOS,
            "juego": '\n'.join(
                ''.join(fila) for fila in tablero
            )
        }


# ==========================================
# API FASTAPI
# ==========================================

app = FastAPI(title="API Tetris")

router = APIRouter(
    prefix="/tetris",
    tags=["Tetris"]
)

juegos = {}
contador_juegos = 1


# ======================================
# INICIAR JUEGO
# ======================================

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


# ======================================
# MOVER PIEZA
# ======================================

@router.get("/mover/{id_juego}/")
async def mover(id_juego: int, direccion: str):
    if id_juego not in juegos:
        raise HTTPException(
            status_code=404,
            detail="Juego no encontrado"
        )

    return juegos[id_juego].mover(direccion)


# ======================================
# AVANZAR CAIDA AUTOMATICA
# ======================================

@router.get("/avanzar/{id_juego}/")
async def avanzar(id_juego: int):
    if id_juego not in juegos:
        raise HTTPException(
            status_code=404,
            detail="Juego no encontrado"
        )

    return juegos[id_juego].avanzar()


# ======================================
# CONSULTAR ESTADO
# ======================================

@router.get("/estado/{id_juego}/")
async def obtener_estado(id_juego: int):
    if id_juego not in juegos:
        raise HTTPException(
            status_code=404,
            detail="Juego no encontrado"
        )

    return juegos[id_juego].obtener_estado_juego()


# ======================================
# REGISTRAR ROUTER
# ======================================

app.include_router(router)
