
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4
import random

router = APIRouter(prefix="/ahorcado", tags=["Ahorcado"])

# Almacenamiento de partidas
games = {}


# ==========================================
# SISTEMA DE ERRORES
# ==========================================

def error_api(status, code, message):
    raise HTTPException(
        status_code=status,
        detail={
            "code": code,
            "message": message
        }
    )


# ==========================================
# DIBUJOS DEL AHORCADO
# ==========================================

DIBUJOS = [
    "🪵🪵🪵🪵\n🪵      │\n🪵      │\n🪵      │\n🪵🪵🪵🪵",

    "🪵🪵🪵🪵\n🪵      │\n🪵      😵\n🪵      │\n🪵🪵🪵🪵",

    "🪵🪵🪵🪵\n🪵      │\n🪵      😵\n🪵      👕\n🪵🪵🪵🪵",

    "🪵🪵🪵🪵\n🪵      │\n🪵      😵\n🪵     👕\n🪵🪵🪵🪵",

    "🪵🪵🪵🪵\n🪵      │\n🪵      😵\n🪵     👕\n🪵     👖\n🪵🪵🪵🪵",

    "🪵🪵🪵🪵\n🪵      │\n🪵      😵\n🪵     👕\n🪵     👖\n🪵      /\n🪵🪵🪵🪵",

    "🪵🪵🪵🪵\n🪵      │\n🪵      💀\n🪵     👕\n🪵     👖\n🪵     / \\\n🪵🪵🪵🪵"
]


# ==========================================
# PALABRAS
# ==========================================

PALABRAS = [
    "AGRICULTURA",
    "GIRASOL",
    "TOMATE",
    "PLANTACION",
    "SEMILLA",
    "FOTOSINTESIS",
    "ANIMALES",
    "COMPUTADORA",
    "BOTANICA",
    "GENETICA"
]


# ==========================================
# MODELOS
# ==========================================

class StartRequest(BaseModel):
    intentos_extras: int = 0


class GuessRequest(BaseModel):
    letra: str


# ==========================================
# CLASE DEL JUEGO
# ==========================================

class AhorcadoGame:

    def __init__(self, intentos_extras=0):

        self.palabra = random.choice(PALABRAS)
        self.letras = []

        self.intentos = 6
        self.intentos_extras = intentos_extras
        self.extras_utilizados = 0

        self.estado = "jugando"

    # ADIVINAR LETRA
    def adivinar(self, letra):

        letra = letra.strip().upper()

        if len(letra) != 1 or not letra.isalpha() or not letra.isascii():
            error_api(400, 501, "Debes ingresar una sola letra válida.")

        if self.estado != "jugando":
            error_api(400, 502, "La partida ya terminó.")

        if letra in self.letras:
            error_api(400, 503, "Ya utilizaste esa letra.")

        self.letras.append(letra)

        mensaje_extra = None

        if letra not in self.palabra:

            if self.intentos > 0:

                self.intentos -= 1

            else:

                self.extras_utilizados += 1

                restantes = (
                    self.intentos_extras - self.extras_utilizados
                )

                if restantes > 0:
                    mensaje_extra = (
                        f"¡Un intento extra más! Te quedan {restantes}."
                    )
                else:
                    mensaje_extra = "Ya no tienes intentos extras."

        # Comprobar victoria
        if all(c in self.letras for c in self.palabra):
            self.estado = "ganado"

        # Comprobar derrota
        elif (
            self.intentos == 0
            and self.extras_utilizados >= self.intentos_extras
        ):
            self.estado = "perdido"

        resultado = self.obtener_estado()

        if mensaje_extra:
            resultado["mensaje_extra"] = mensaje_extra

        return resultado

    # OBTENER ESTADO
    def obtener_estado(self):

        progreso = "".join(
            letra if letra in self.letras else "x"
            for letra in self.palabra
        )

        errores = 6 - self.intentos + self.extras_utilizados

        resultado = {
            "palabra_oculta": progreso,
            "letras_utilizadas": self.letras,
            "intentos_restantes": self.intentos,
            "intentos_extras": self.intentos_extras,
            "extras_utilizados": self.extras_utilizados,
            "extras_disponibles": (
                self.intentos_extras - self.extras_utilizados
            ),
            "estado": self.estado,
            "ahorcado": DIBUJOS[min(errores, 6)]
        }

        if self.estado == "ganado":
            resultado["mensaje"] = "¡Felicidades! Has ganado."
            resultado["palabra"] = self.palabra

        elif self.estado == "perdido":
            resultado["mensaje"] = "¡Has perdido! Ya no tienes intentos."
            resultado["palabra"] = self.palabra

        return resultado


# ==========================================
# INICIAR PARTIDA
# ==========================================

@router.post("/iniciar")
async def iniciar_juego(request: StartRequest):

    if request.intentos_extras < 0:
        error_api(
            400,
            504,
            "Los intentos extras no pueden ser negativos."
        )

    game_id = str(uuid4())

    games[game_id] = AhorcadoGame(
        intentos_extras=request.intentos_extras
    )

    return {
        "id_juego": game_id,
        **games[game_id].obtener_estado()
    }


# ==========================================
# ADIVINAR LETRA
# ==========================================

@router.post("/{game_id}/adivinar")
async def adivinar_letra(game_id: str, request: GuessRequest):

    game = games.get(game_id)

    if game is None:
        error_api(404, 505, "Partida no encontrada.")

    return game.adivinar(request.letra)


# ==========================================
# CONSULTAR PARTIDA
# ==========================================

@router.get("/{game_id}")
async def consultar_juego(game_id: str):

    game = games.get(game_id)

    if game is None:
        error_api(404, 506, "Partida no encontrada.")

    return {
        "id_juego": game_id,
        **game.obtener_estado()
    }


# ==========================================
# REINICIAR PARTIDA
# ==========================================

@router.post("/{game_id}/reiniciar")
async def reiniciar_juego(game_id: str):

    game = games.get(game_id)

    if game is None:
        error_api(404, 507, "No se puede reiniciar: partida no encontrada.")

    intentos_extras = game.intentos_extras

    games[game_id] = AhorcadoGame(
        intentos_extras=intentos_extras
    )

    return {
        "id_juego": game_id,
        **games[game_id].obtener_estado()
    }


# ==========================================
# ELIMINAR PARTIDA
# ==========================================

@router.delete("/{game_id}")
async def eliminar_juego(game_id: str):

    if game_id not in games:
        error_api(404, 509, "No se puede eliminar: partida no encontrada.")

    del games[game_id]

    return {
        "mensaje": "Partida eliminada correctamente."
    }
