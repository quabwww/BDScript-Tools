
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4
import random

router = APIRouter(prefix="/ahorcado", tags=["Ahorcado"])

# Almacenamiento de partidas
games = {}

DIBUJOS = [
    # 0 errores
    "🪵🪵🪵🪵\n"
    "🪵      │\n"
    "🪵      │\n"
    "🪵      │\n"
    "🪵🪵🪵🪵",

    # 1 error
    "🪵🪵🪵🪵\n"
    "🪵      │\n"
    "🪵      😵\n"
    "🪵      │\n"
    "🪵🪵🪵🪵",

    # 2 errores
    "🪵🪵🪵🪵\n"
    "🪵      │\n"
    "🪵      😵\n"
    "🪵      👕\n"
    "🪵🪵🪵🪵",

    # 3 errores
    "🪵🪵🪵🪵\n"
    "🪵      │\n"
    "🪵      😵\n"
    "🪵     👕\n"
    "🪵🪵🪵🪵",

    # 4 errores
    "🪵🪵🪵🪵\n"
    "🪵      │\n"
    "🪵      😵\n"
    "🪵     👕\n"
    "🪵     👖\n"
    "🪵🪵🪵🪵",

    # 5 errores
    "🪵🪵🪵🪵\n"
    "🪵      │\n"
    "🪵      😵\n"
    "🪵     👕\n"
    "🪵     👖\n"
    "🪵      🦵\n"
    "🪵🪵🪵🪵",

    # 6 errores
    "🪵🪵🪵🪵\n"
    "🪵      │\n"
    "🪵      💀\n"
    "🪵     👕\n"
    "🪵     👖\n"
    "🪵     🦵🦵\n"
    "🪵🪵🪵🪵"
]


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


class GuessRequest(BaseModel):
    letra: str


class AhorcadoGame:

    def __init__(self):
        self.palabra = random.choice(PALABRAS)
        self.letras = []
        self.intentos = 6
        self.estado = "jugando"

    def adivinar(self, letra):

        letra = letra.strip().upper()

        if len(letra) != 1 or not letra.isalpha() or not letra.isascii():
            raise HTTPException(
                status_code=400,
                detail="Debes ingresar una sola letra válida."
            )

        if self.estado != "jugando":
            raise HTTPException(
                status_code=400,
                detail="La partida ya terminó."
            )

        if letra in self.letras:
            raise HTTPException(
                status_code=400,
                detail="Ya utilizaste esa letra."
            )

        self.letras.append(letra)

        if letra not in self.palabra:
            self.intentos -= 1

        if self.intentos == 0:
            self.estado = "perdido"

        elif all(c in self.letras for c in self.palabra):
            self.estado = "ganado"

        return self.obtener_estado()

    def obtener_estado(self):

        progreso = "".join(
            letra if letra in self.letras else "x"
            for letra in self.palabra
        )

        resultado = {
            "palabra_oculta": progreso,
            "letras_utilizadas": self.letras,
            "intentos_restantes": self.intentos,
            "estado": self.estado,
            "ahorcado": DIBUJOS[6 - self.intentos]
        }

        if self.estado == "ganado":
            resultado["mensaje"] = "¡Felicidades! Has ganado."
            resultado["palabra"] = self.palabra

        elif self.estado == "perdido":
            resultado["mensaje"] = "¡Has perdido!"
            resultado["palabra"] = self.palabra

        return resultado


# INICIAR PARTIDA
@router.post("/iniciar")
async def iniciar_juego():

    game_id = str(uuid4())

    games[game_id] = AhorcadoGame()

    return {
        "id_juego": game_id,
        **games[game_id].obtener_estado()
    }


# ADIVINAR LETRA
@router.post("/{game_id}/adivinar")
async def adivinar_letra(game_id: str, request: GuessRequest):

    game = games.get(game_id)

    if game is None:
        raise HTTPException(
            status_code=404,
            detail="Partida no encontrada."
        )

    return game.adivinar(request.letra)


# CONSULTAR PARTIDA
@router.get("/{game_id}")
async def consultar_juego(game_id: str):

    game = games.get(game_id)

    if game is None:
        raise HTTPException(
            status_code=404,
            detail="Partida no encontrada."
        )

    return {
        "id_juego": game_id,
        **game.obtener_estado()
    }


# REINICIAR PARTIDA
@router.post("/{game_id}/reiniciar")
async def reiniciar_juego(game_id: str):

    if game_id not in games:
        raise HTTPException(
            status_code=404,
            detail="Partida no encontrada."
        )

    games[game_id] = AhorcadoGame()

    return {
        "id_juego": game_id,
        **games[game_id].obtener_estado()
    }


# ELIMINAR PARTIDA
@router.delete("/{game_id}")
async def eliminar_juego(game_id: str):

    if game_id not in games:
        raise HTTPException(
            status_code=404,
            detail="Partida no encontrada."
        )

    del games[game_id]

    return {
        "mensaje": "Partida eliminada correctamente."
    }
