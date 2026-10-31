from fastapi import FastAPI, APIRouter, HTTPException
import random

# ==========================================
# JUEGO TETRIS
# ==========================================

class JuegoTetris:

    def __init__(self, id_juego: int, ancho: int = 8, alto: int = 20):
        self.id_juego = id_juego
        self.ancho = ancho
        self.alto = alto

        # Tablero interno
        self.tablero = [
            ['-' for _ in range(ancho)]
            for _ in range(alto)
        ]

        # Piezas y rotaciones
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

        # Pieza siguiente
        self.pieza_siguiente = random.choice(
            list(self.piezas.keys())
        )

        self.x = 2
        self.y = 1
        self.rotacion = 0

        self.puntuacion = 0
        self.lineas = 0
        self.nivel = 1
        self.juego_terminado = False

        self.generar_pieza()

    # ======================================
    # GENERAR PIEZA
    # ======================================

    def generar_pieza(self):

        self.pieza_actual = self.pieza_siguiente

        self.pieza_siguiente = random.choice(
            list(self.piezas.keys())
        )

        self.rotacion = 0
        self.x = 2
        self.y = 1

        # Si la pieza no puede aparecer, Game Over
        if self.colisiona(self.x, self.y, self.rotacion):
            self.juego_terminado = True

    # ======================================
    # OBTENER BLOQUES
    # ======================================

    def obtener_bloques(self, rotacion=None):

        if rotacion is None:
            rotacion = self.rotacion

        formas = self.piezas[self.pieza_actual]

        return formas[rotacion % len(formas)]

    # ======================================
    # CREAR MATRIZ 4x4 DE UNA PIEZA
    # ======================================

    def crear_matriz_pieza(self, tipo, rotacion=0):

        matriz = [
            ['-' for _ in range(4)]
            for _ in range(4)
        ]

        formas = self.piezas[tipo]
        bloques = formas[rotacion % len(formas)]

        for dx, dy in bloques:
            matriz[dy][dx] = tipo

        return '\n'.join(
            ''.join(fila) for fila in matriz
        )

    # ======================================
    # DETECTAR COLISIONES
    # ======================================

    def colisiona(self, x, y, rotacion):

        bloques = self.piezas[self.pieza_actual][
            rotacion % len(self.piezas[self.pieza_actual])
        ]

        for dx, dy in bloques:

            nx = x + dx
            ny = y + dy

            # Bordes laterales
            if nx < 1 or nx >= self.ancho - 1:
                return True

            # Borde inferior y superior
            if ny < 1 or ny >= self.alto - 1:
                return True

            # Colisión con bloques fijados
            if self.tablero[ny][nx] != '-':
                return True

        return False

    # ======================================
    # FIJAR PIEZA
    # ======================================

    def fijar_pieza(self):

        # Si algún bloque quedó fuera del espacio,
        # termina la partida
        for dx, dy in self.obtener_bloques():

            nx = self.x + dx
            ny = self.y + dy

            if not (1 <= nx < self.ancho - 1):
                self.juego_terminado = True
                return

            if not (1 <= ny < self.alto - 1):
                self.juego_terminado = True
                return

        # Guardar pieza en el tablero
        for dx, dy in self.obtener_bloques():

            nx = self.x + dx
            ny = self.y + dy

            self.tablero[ny][nx] = self.pieza_actual

        # Eliminar filas completas
        self.eliminar_lineas()

        # Generar nueva pieza
        self.generar_pieza()

    # ======================================
    # ELIMINAR LINEAS COMPLETAS
    # ======================================

    def eliminar_lineas(self):

        filas_completas = []

        # Revisar solamente filas interiores
        for y in range(1, self.alto - 1):

            if all(
                self.tablero[y][x] != '-'
                for x in range(1, self.ancho - 1)
            ):
                filas_completas.append(y)

        cantidad = len(filas_completas)

        if cantidad == 0:
            return

        # Eliminar filas completas
        for y in reversed(filas_completas):
            del self.tablero[y]

        # Insertar filas vacías debajo del borde superior
        for _ in range(cantidad):

            self.tablero.insert(
                1, ['-' for _ in range(self.ancho)]
            )

        # Actualizar estadísticas
        self.lineas += cantidad

        # Subir un nivel por cada línea eliminada
        self.nivel += cantidad

        # Puntuación
        puntos = {
            1: 100,
            2: 300,
            3: 500,
            4: 800
        }

        self.puntuacion += (
            puntos.get(cantidad, 0) * self.nivel
        )

    # ======================================
    # MOVIMIENTOS DISPONIBLES
    # ======================================

    def obtener_movimientos_disponibles(self):

        movimientos = []

        if self.juego_terminado:
            return movimientos

        # Izquierda
        if not self.colisiona(
            self.x - 1, self.y, self.rotacion
        ):
            movimientos.append("IZQUIERDA")

        # Derecha
        if not self.colisiona(
            self.x + 1, self.y, self.rotacion
        ):
            movimientos.append("DERECHA")

        # Rotar
        formas = self.piezas[self.pieza_actual]

        nueva_rotacion = (
            self.rotacion + 1
        ) % len(formas)

        if not self.colisiona(
            self.x, self.y, nueva_rotacion
        ):
            movimientos.append("ROTAR")

        # Bajar
        if not self.colisiona(
            self.x, self.y + 1, self.rotacion
        ):
            movimientos.append("BAJAR")
            movimientos.append("CAIDA")

        return movimientos

    # ======================================
    # MOVER PIEZA
    # ======================================

    def mover(self, direccion: str):

        direccion = direccion.upper()

        if self.juego_terminado:
            return self.obtener_estado_juego()

        movimientos = self.obtener_movimientos_disponibles()

        if direccion not in [
            "IZQUIERDA", "DERECHA", "ROTAR", "BAJAR", "CAIDA"
        ]:

            return {
                "estado_juego": "false",
                "mensaje": "Movimiento no válido",
                "movimientos_disponibles": movimientos
            }

        # Izquierda
        if direccion == "IZQUIERDA":

            if "IZQUIERDA" in movimientos:
                self.x -= 1

        # Derecha
        elif direccion == "DERECHA":

            if "DERECHA" in movimientos:
                self.x += 1

        # Rotación
        elif direccion == "ROTAR":

            if "ROTAR" in movimientos:

                self.rotacion = (
                    self.rotacion + 1
                ) % len(self.piezas[self.pieza_actual])

        # Bajar una posición
        elif direccion == "BAJAR":

            if "BAJAR" in movimientos:
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

    def avanzar(self):

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

    def crear_tablero(self):

        tablero = [
            ['-' for _ in range(self.ancho)]
            for _ in range(self.alto)
        ]

        # Bordes laterales
        for y in range(self.alto):

            tablero[y][0] = '|'
            tablero[y][self.ancho - 1] = '|'

        # Bordes superior e inferior
        for x in range(self.ancho):

            tablero[0][x] = '#'
            tablero[self.alto - 1][x] = '#'

        # Dibujar piezas fijas
        for y in range(1, self.alto - 1):

            for x in range(1, self.ancho - 1):

                if self.tablero[y][x] != '-':
                    tablero[y][x] = self.tablero[y][x]

        # Dibujar pieza actual
        if not self.juego_terminado:

            for dx, dy in self.obtener_bloques():

                nx = self.x + dx
                ny = self.y + dy

                if (
                    1 <= nx < self.ancho - 1
                    and 1 <= ny < self.alto - 1
                ):
                    tablero[ny][nx] = self.pieza_actual

        return tablero

    # ======================================
    # ESTADO DEL JUEGO
    # ======================================

    def obtener_estado_juego(self):

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

            # MATRIZ 4x4 DE LA PIEZA ACTUAL
            "pieza_actual_4x4": self.crear_matriz_pieza(
                self.pieza_actual, self.rotacion
            ),

            # MATRIZ 4x4 DE LA SIGUIENTE PIEZA
            "siguiente_pieza_4x4": self.crear_matriz_pieza(
                self.pieza_siguiente, 0
            ),

            "pieza_siguiente": self.pieza_siguiente,

            "movimientos_disponibles":
                self.obtener_movimientos_disponibles(),

            "juego": '\n'.join(
                ''.join(fila) for fila in tablero
            )
        }


# ==========================================
# API FASTAPI
# ==========================================



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
# CAIDA AUTOMATICA
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

