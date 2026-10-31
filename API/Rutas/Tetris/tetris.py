import random
import uuid
from copy import deepcopy
from fastapi import APIRouter, FastAPI, HTTPException, Query

router = APIRouter(prefix="/tetris", tags=["Tetris"])

# =========================================================
# CONFIGURACIÓN
# =========================================================

COLUMNAS = 8
FILAS = 20

# Área jugable: columnas 1 a 6, filas 1 a 18
COL_MIN = 1
COL_MAX = 6
FILA_MIN = 1
FILA_MAX = 18

VACIO = "-"

# =========================================================
# PIEZAS DE TETRIS
# Cada pieza tiene rotaciones dentro de una matriz 4x4
# =========================================================

PIEZAS = {
    "I": [
        [
            "----",
            "IIII",
            "----",
            "----",
        ],
        [
            "--I-",
            "--I-",
            "--I-",
            "--I-",
        ],
        [
            "----",
            "----",
            "IIII",
            "----",
        ],
        [
            "-I--",
            "-I--",
            "-I--",
            "-I--",
        ],
    ],

    "O": [
        [
            "----",
            "-OO-",
            "-OO-",
            "----",
        ],
        [
            "----",
            "-OO-",
            "-OO-",
            "----",
        ],
        [
            "----",
            "-OO-",
            "-OO-",
            "----",
        ],
        [
            "----",
            "-OO-",
            "-OO-",
            "----",
        ],
    ],

    "T": [
        [
            "----",
            "TTT-",
            "-T--",
            "----",
        ],
        [
            "-T--",
            "TT--",
            "-T--",
            "----",
        ],
        [
            "-T--",
            "TTT-",
            "----",
            "----",
        ],
        [
            "-T--",
            "-TT-",
            "-T--",
            "----",
        ],
    ],

    "S": [
        [
            "----",
            "-SS-",
            "SS--",
            "----",
        ],
        [
            "-S--",
            "-SS-",
            "--S-",
            "----",
        ],
        [
            "----",
            "-SS-",
            "SS--",
            "----",
        ],
        [
            "-S--",
            "-SS-",
            "--S-",
            "----",
        ],
    ],

    "Z": [
        [
            "----",
            "ZZ--",
            "-ZZ-",
            "----",
        ],
        [
            "--Z-",
            "-ZZ-",
            "-Z--",
            "----",
        ],
        [
            "----",
            "ZZ--",
            "-ZZ-",
            "----",
        ],
        [
            "--Z-",
            "-ZZ-",
            "-Z--",
            "----",
        ],
    ],

    "J": [
        [
            "----",
            "JJJ-",
            "--J-",
            "----",
        ],
        [
            "-J--",
            "-J--",
            "JJ--",
            "----",
        ],
        [
            "J---",
            "JJJ-",
            "----",
            "----",
        ],
        [
            "-JJ-",
            "-J--",
            "-J--",
            "----",
        ],
    ],

    "L": [
        [
            "----",
            "LLL-",
            "L---",
            "----",
        ],
        [
            "LL--",
            "-L--",
            "-L--",
            "----",
        ],
        [
            "--L-",
            "LLL-",
            "----",
            "----",
        ],
        [
            "-L--",
            "-L--",
            "-LL-",
            "----",
        ],
    ],
}

PUNTOS_LINEAS = {
    1: 100,
    2: 300,
    3: 500,
    4: 800,
}


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def crear_matriz_pieza(tipo, rotacion=0):
    """Devuelve la pieza como matriz 4x4."""
    forma = PIEZAS[tipo][rotacion % 4]
    return [list(fila) for fila in forma]


def obtener_celdas_pieza(tipo, rotacion, x, y):
    """Obtiene las coordenadas ocupadas de una pieza."""
    matriz = crear_matriz_pieza(tipo, rotacion)
    celdas = []

    for fila in range(4):
        for columna in range(4):
            if matriz[fila][columna] != VACIO:
                celdas.append((x + columna, y + fila))

    return celdas


# =========================================================
# CLASE DEL JUEGO
# =========================================================

class JuegoTetris:

    def __init__(self):
        self.tablero = [
            [VACIO for _ in range(COLUMNAS)]
            for _ in range(FILAS)
        ]

        self.puntaje = 0
        self.nivel = 1
        self.lineas = 0
        self.game_over = False

        self.pieza_siguiente = random.choice(list(PIEZAS.keys()))

        self.pieza_actual = None
        self.rotacion = 0
        self.x = 2
        self.y = 1

        self.generar_pieza()

    # -----------------------------------------------------
    # GENERAR PIEZA
    # -----------------------------------------------------

    def generar_pieza(self):
        self.pieza_actual = self.pieza_siguiente
        self.pieza_siguiente = random.choice(list(PIEZAS.keys()))

        self.rotacion = 0
        self.x = 2
        self.y = 1

        if self.colisiona(self.x, self.y, self.rotacion):
            self.game_over = True

    # -----------------------------------------------------
    # COLISIONES
    # -----------------------------------------------------

    def colisiona(self, nuevo_x, nuevo_y, nueva_rotacion):
        celdas = obtener_celdas_pieza(
            self.pieza_actual,
            nueva_rotacion,
            nuevo_x,
            nuevo_y
        )

        for x, y in celdas:

            # Límites del área jugable
            if x < COL_MIN or x > COL_MAX:
                return True

            if y > FILA_MAX:
                return True

            # No permitir que la pieza salga por arriba
            if y < FILA_MIN:
                return True

            # Colisión con piezas fijadas
            if self.tablero[y][x] != VACIO:
                return True

        return False

    # -----------------------------------------------------
    # FIJAR PIEZA EN EL TABLERO
    # -----------------------------------------------------

    def fijar_pieza(self):
        celdas = obtener_celdas_pieza(
            self.pieza_actual,
            self.rotacion,
            self.x,
            self.y
        )

        for x, y in celdas:
            if 0 <= y < FILAS and 0 <= x < COLUMNAS:
                self.tablero[y][x] = self.pieza_actual

        self.eliminar_lineas()
        self.generar_pieza()

    # -----------------------------------------------------
    # ELIMINAR LÍNEAS COMPLETAS
    # -----------------------------------------------------

    def eliminar_lineas(self):
        lineas_eliminadas = 0

        filas_nuevas = []

        for y in range(FILA_MIN, FILA_MAX + 1):
            fila = self.tablero[y]

            if all(
                fila[x] != VACIO
                for x in range(COL_MIN, COL_MAX + 1)
            ):
                lineas_eliminadas += 1
            else:
                filas_nuevas.append(fila)

        if lineas_eliminadas == 0:
            return

        # Agregar filas vacías arriba
        for _ in range(lineas_eliminadas):
            filas_nuevas.insert(
                0,
                [VACIO for _ in range(COLUMNAS)]
            )

        # Reconstruir únicamente el área jugable
        for indice, fila in enumerate(filas_nuevas):
            self.tablero[FILA_MIN + indice] = fila

        self.lineas += lineas_eliminadas

        # Aumentar nivel por cada línea eliminada
        self.nivel += lineas_eliminadas

        # Calcular puntaje
        puntos = PUNTOS_LINEAS.get(lineas_eliminadas, 0)
        self.puntaje += puntos * self.nivel

    # -----------------------------------------------------
    # MOVIMIENTOS DISPONIBLES
    # -----------------------------------------------------

    def movimientos_disponibles(self):
        if self.game_over:
            return []

        movimientos = []

        if not self.colisiona(self.x - 1, self.y, self.rotacion):
            movimientos.append("IZQUIERDA")

        if not self.colisiona(self.x + 1, self.y, self.rotacion):
            movimientos.append("DERECHA")

        nueva_rotacion = (self.rotacion + 1) % 4

        if not self.colisiona(self.x, self.y, nueva_rotacion):
            movimientos.append("ROTAR")

        if not self.colisiona(self.x, self.y + 1, self.rotacion):
            movimientos.append("BAJAR")
            movimientos.append("CAIDA")

        return movimientos

    # -----------------------------------------------------
    # MOVER PIEZA
    # -----------------------------------------------------

    def mover(self, direccion):
        if self.game_over:
            return False

        movimientos = self.movimientos_disponibles()

        if direccion not in movimientos:
            return False

        if direccion == "IZQUIERDA":
            self.x -= 1

        elif direccion == "DERECHA":
            self.x += 1

        elif direccion == "ROTAR":
            self.rotacion = (self.rotacion + 1) % 4

        elif direccion == "BAJAR":
            self.y += 1

        elif direccion == "CAIDA":
            while not self.colisiona(
                self.x,
                self.y + 1,
                self.rotacion
            ):
                self.y += 1

            self.fijar_pieza()

        return True

    # -----------------------------------------------------
    # AVANZAR AUTOMÁTICAMENTE
    # -----------------------------------------------------

    def avanzar(self):
        if self.game_over:
            return False

        if not self.colisiona(
            self.x,
            self.y + 1,
            self.rotacion
        ):
            self.y += 1
        else:
            self.fijar_pieza()

        return True

    # -----------------------------------------------------
    # TABLERO VISIBLE CON BORDES
    # -----------------------------------------------------

    def crear_tablero(self):
        tablero_visible = []

        # Borde superior
        tablero_visible.append("#" * COLUMNAS)

        for y in range(FILA_MIN, FILA_MAX + 1):
            fila = self.tablero[y].copy()

            # Dibujar pieza actual sobre el tablero
            if not self.game_over:
                celdas = obtener_celdas_pieza(
                    self.pieza_actual,
                    self.rotacion,
                    self.x,
                    self.y
                )

                for x_pieza, y_pieza in celdas:
                    if y_pieza == y and COL_MIN <= x_pieza <= COL_MAX:
                        fila[x_pieza] = self.pieza_actual

            # Bordes laterales
            fila[0] = "|"
            fila[COLUMNAS - 1] = "|"

            tablero_visible.append("".join(fila))

        # Borde inferior
        tablero_visible.append("#" * COLUMNAS)

        return tablero_visible

    # -----------------------------------------------------
    # ESTADO COMPLETO DEL JUEGO
    # -----------------------------------------------------

    def obtener_estado(self):
        matriz_actual = crear_matriz_pieza(
            self.pieza_actual,
            self.rotacion
        )

        matriz_siguiente = crear_matriz_pieza(
            self.pieza_siguiente,
            0
        )

        return {
            "tablero": self.crear_tablero(),

            "pieza_en_uso": [
                "".join(fila)
                for fila in matriz_actual
            ],

            "pieza_actual_tipo": self.pieza_actual,

            "pieza_siguiente": [
                "".join(fila)
                for fila in matriz_siguiente
            ],

            "pieza_siguiente_tipo": self.pieza_siguiente,

            "posicion": {
                "x": self.x,
                "y": self.y,
                "rotacion": self.rotacion
            },

            "movimientos_disponibles": (
                self.movimientos_disponibles()
            ),

            "puntaje": self.puntaje,
            "nivel": self.nivel,
            "lineas": self.lineas,
            "game_over": self.game_over
        }


# =========================================================
# ALMACENAMIENTO DE PARTIDAS
# =========================================================

juegos = {}


# =========================================================
# ENDPOINTS FASTAPI
# =========================================================

@router.get("/iniciar_juego/")
def iniciar_juego():
    id_juego = str(uuid.uuid4())

    juego = JuegoTetris()
    juegos[id_juego] = juego

    return {
        "id_juego": id_juego,
        **juego.obtener_estado()
    }


@router.get("/estado/{id_juego}/")
def obtener_estado(id_juego: str):
    juego = juegos.get(id_juego)

    if juego is None:
        raise HTTPException(
            status_code=404,
            detail="Juego no encontrado"
        )

    return juego.obtener_estado()


@router.get("/mover/{id_juego}/")
def mover_pieza(
    id_juego: str,
    direccion: str = Query(...)
):
    juego = juegos.get(id_juego)

    if juego is None:
        raise HTTPException(
            status_code=404,
            detail="Juego no encontrado"
        )

    direccion = direccion.upper()

    direcciones_validas = {
        "IZQUIERDA",
        "DERECHA",
        "ROTAR",
        "BAJAR",
        "CAIDA"
    }

    if direccion not in direcciones_validas:
        raise HTTPException(
            status_code=400,
            detail="Dirección inválida"
        )

    juego.mover(direccion)

    return juego.obtener_estado()


@router.get("/avanzar/{id_juego}/")
def avanzar_juego(id_juego: str):
    juego = juegos.get(id_juego)

    if juego is None:
        raise HTTPException(
            status_code=404,
            detail="Juego no encontrado"
        )

    juego.avanzar()

    return juego.obtener_estado()


@router.delete("/eliminar/{id_juego}/")
def eliminar_juego(id_juego: str):
    juego = juegos.pop(id_juego, None)

    if juego is None:
        raise HTTPException(
            status_code=404,
            detail="Juego no encontrado"
        )

    return {
        "mensaje": "Juego eliminado",
        "id_juego": id_juego
    }


