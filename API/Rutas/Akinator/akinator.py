
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from akinator import AsyncClient
from typing import Optional
from uuid import uuid4
import asyncio

router = APIRouter()

# Partidas independientes
games = {}
games_lock = asyncio.Lock()


class AkinatorRequest(BaseModel):
    game_id: str
    answer: Optional[str] = None
    correct: Optional[bool] = None


def get_game_response(game_id, aki, status):
    """Construye la respuesta con información e imágenes."""

    is_guess = bool(aki.win)

    return {
        "success": True,
        "game_id": game_id,
        "status": status,
        "game": {
            "question": aki.question if not is_guess else None,
            "step": aki.step,
            "progression": aki.progression,
            "confidence": aki.confidence,
            "theme": aki.theme_name,
            "finished": aki.finished
        },
        "guess": {
            "name": aki.name_proposition,
            "description": aki.description_proposition,
            "confidence": aki.confidence
        } if is_guess else None,
        "images": {
            "akinator": aki.akitude_url,
            "character": aki.photo if is_guess else None,
            "flag": aki.flag_photo
        },
        "answers": [
            "yes",
            "no",
            "idk",
            "probably",
            "probably_not",
            "back"
        ] if not is_guess else None
    }


@router.api_route(
    "/akinator/",
    methods=["GET", "POST", "DELETE"]
)
async def akinator(
    action: str = Query("start"),
    game_id: Optional[str] = None,
    language: str = Query("es"),
    theme: str = Query("c"),
    child_mode: bool = Query(False),
    data: Optional[AkinatorRequest] = None
):

    # ==========================
    # INICIAR PARTIDA
    # ==========================

    if action == "start":

        if theme not in ["c", "a", "o"]:
            raise HTTPException(
                status_code=400,
                detail="Tema inválido: c, a u o."
            )

        aki = AsyncClient()

        try:
            await aki.start_game(
                language=language,
                theme=theme,
                child_mode=child_mode
            )

            new_id = str(uuid4())

            async with games_lock:
                games[new_id] = {
                    "aki": aki,
                    "lock": asyncio.Lock(),
                    "finished": False
                }

            return get_game_response(
                new_id,
                aki,
                "playing"
            )

        except HTTPException:
            raise

        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"No se pudo iniciar Akinator: {str(exc)}"
            )

    # ==========================
    # OBTENER ID DE PARTIDA
    # ==========================

    if action in ["status", "delete"]:

        if not game_id:
            raise HTTPException(
                status_code=400,
                detail="Debes proporcionar game_id."
            )

    elif data is None or not data.game_id:
        raise HTTPException(
            status_code=400,
            detail="Debes proporcionar game_id en el JSON."
        )

    current_id = (
        game_id if action in ["status", "delete"]
        else data.game_id
    )

    # ==========================
    # BUSCAR PARTIDA
    # ==========================

    game = games.get(current_id)

    if not game:
        raise HTTPException(
            status_code=404,
            detail="Partida no encontrada."
        )

    aki = game["aki"]

    # ==========================
    # CONSULTAR ESTADO
    # ==========================

    if action == "status":

        return get_game_response(
            current_id,
            aki,
            "finished" if game["finished"] else (
                "guess" if aki.win else "playing"
            )
        )

    # ==========================
    # ELIMINAR PARTIDA
    # ==========================

    if action == "delete":

        async with games_lock:
            removed = games.pop(current_id, None)

        if not removed:
            raise HTTPException(
                status_code=404,
                detail="La partida ya no existe."
            )

        return {
            "success": True,
            "message": "Partida eliminada.",
            "game_id": current_id
        }

    # ==========================
    # ACCIONES DE LA PARTIDA
    # ==========================

    async with game["lock"]:

        if game["finished"] or aki.finished:
            raise HTTPException(
                status_code=400,
                detail="La partida ya ha terminado."
            )

        try:

            # ----------------------
            # RESPONDER PREGUNTA
            # ----------------------

            if action == "answer":

                answer = (data.answer or "").strip().lower()

                answers = {
                    "yes": "yes",
                    "no": "no",
                    "idk": "i don't know",
                    "i don't know": "i don't know",
                    "probably": "probably",
                    "probably_not": "probably not",
                    "probably not": "probably not"
                }

                if answer not in answers:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Respuesta inválida. "
                            "Usa yes, no, idk, probably o probably_not."
                        )
                    )

                if aki.win:
                    raise HTTPException(
                        status_code=400,
                        detail="Primero debes confirmar o rechazar la propuesta."
                    )

                await aki.answer(answers[answer])

                if aki.win:
                    return get_game_response(
                        current_id,
                        aki,
                        "guess"
                    )

                if aki.finished:
                    game["finished"] = True

                    return get_game_response(
                        current_id,
                        aki,
                        "finished"
                    )

                return get_game_response(
                    current_id,
                    aki,
                    "playing"
                )

            # ----------------------
            # RETROCEDER
            # ----------------------

            elif action == "back":

                if aki.step <= 0:
                    raise HTTPException(
                        status_code=400,
                        detail="No puedes retroceder más."
                    )

                await aki.back()

                return get_game_response(
                    current_id,
                    aki,
                    "guess" if aki.win else "playing"
                )

            # ----------------------
            # CONFIRMAR / RECHAZAR
            # ----------------------

            elif action == "guess":

                if data.correct is None:
                    raise HTTPException(
                        status_code=400,
                        detail="Indica correct: true o false."
                    )

                if not aki.win:
                    raise HTTPException(
                        status_code=400,
                        detail="Akinator todavía no ha propuesto un personaje."
                    )

                if data.correct:

                    await aki.choose()
                    game["finished"] = True

                    return {
                        "success": True,
                        "game_id": current_id,
                        "status": "won",
                        "message": "¡Akinator acertó!",
                        "guess": {
                            "name": aki.name_proposition,
                            "description": aki.description_proposition
                        },
                        "images": {
                            "akinator": aki.akitude_url,
                            "character": aki.photo
                        }
                    }

                await aki.exclude()

                if aki.finished:
                    game["finished"] = True

                    return get_game_response(
                        current_id,
                        aki,
                        "finished"
                    )

                return get_game_response(
                    current_id,
                    aki,
                    "guess" if aki.win else "playing"
                )

            else:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Acción inválida. "
                        "Usa start, answer, back, guess o status."
                    )
                )

        except HTTPException:
            raise

        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Error de Akinator: {str(exc)}"
            )
