
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from akinator import Akinator
from typing import Optional
from uuid import uuid4
import asyncio

router = APIRouter()

games = {}
games_lock = asyncio.Lock()


class AkinatorRequest(BaseModel):
    game_id: str
    answer: Optional[str] = None
    correct: Optional[bool] = None


def get_game_response(game_id, aki, status):
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
            "yes", "no", "idk",
            "probably", "probably_not", "back"
        ] if not is_guess else None
    }


def get_game(game_id):
    game = games.get(game_id)

    if not game:
        raise HTTPException(
            status_code=404,
            detail="Partida no encontrada."
        )

    return game


# =====================================
# 1. INICIAR PARTIDA
# =====================================

@router.get("/akinator/start/")
async def start_game(
    language: str = Query("es"),
    theme: str = Query("c"),
    child_mode: bool = Query(False)
):
    if theme not in ["c", "a", "o"]:
        raise HTTPException(
            status_code=400,
            detail="Tema inválido: c, a u o."
        )

    aki = Akinator()

    try:
        await aki.start_game(
            language=language,
            theme=theme,
            child_mode=child_mode
        )

        game_id = str(uuid4())

        async with games_lock:
            games[game_id] = {
                "aki": aki,
                "lock": asyncio.Lock(),
                "finished": False
            }

        return get_game_response(game_id, aki, "playing")

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo iniciar Akinator: {str(exc)}"
        )


# =====================================
# 2. RESPONDER PREGUNTA
# =====================================

@router.post("/akinator/answer/")
async def answer_question(data: AkinatorRequest):
    game = get_game(data.game_id)
    aki = game["aki"]

    answers = {
        "yes": "yes",
        "no": "no",
        "idk": "i don't know",
        "i don't know": "i don't know",
        "probably": "probably",
        "probably_not": "probably not",
        "probably not": "probably not"
    }

    answer = (data.answer or "").strip().lower()

    if answer not in answers:
        raise HTTPException(
            status_code=400,
            detail="Usa yes, no, idk, probably o probably_not."
        )

    async with game["lock"]:
        if game["finished"] or aki.finished:
            raise HTTPException(
                status_code=400,
                detail="La partida ya terminó."
            )

        if aki.win:
            raise HTTPException(
                status_code=400,
                detail="Debes confirmar o rechazar la propuesta."
            )

        try:
            await aki.answer(answers[answer])

            if aki.finished:
                game["finished"] = True
                status = "finished"
            elif aki.win:
                status = "guess"
            else:
                status = "playing"

            return get_game_response(data.game_id, aki, status)

        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Error al responder: {str(exc)}"
            )


# =====================================
# 3. RETROCEDER
# =====================================

@router.post("/akinator/back/")
async def back_question(data: AkinatorRequest):
    game = get_game(data.game_id)
    aki = game["aki"]

    async with game["lock"]:
        if game["finished"] or aki.finished:
            raise HTTPException(
                status_code=400,
                detail="La partida ya terminó."
            )

        if aki.step <= 0:
            raise HTTPException(
                status_code=400,
                detail="No puedes retroceder más."
            )

        try:
            await aki.back()

            return get_game_response(
                data.game_id,
                aki,
                "guess" if aki.win else "playing"
            )

        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Error al retroceder: {str(exc)}"
            )


# =====================================
# 4. CONFIRMAR O RECHAZAR PERSONAJE
# =====================================

@router.post("/akinator/guess/")
async def confirm_guess(data: AkinatorRequest):
    game = get_game(data.game_id)
    aki = game["aki"]

    if data.correct is None:
        raise HTTPException(
            status_code=400,
            detail="Indica correct: true o false."
        )

    async with game["lock"]:
        if game["finished"] or aki.finished:
            raise HTTPException(
                status_code=400,
                detail="La partida ya terminó."
            )

        if not aki.win:
            raise HTTPException(
                status_code=400,
                detail="Akinator todavía no ha propuesto un personaje."
            )

        try:
            if data.correct:
                await aki.choose()
                game["finished"] = True

                return {
                    "success": True,
                    "game_id": data.game_id,
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
                status = "finished"
            else:
                status = "guess" if aki.win else "playing"

            return get_game_response(data.game_id, aki, status)

        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Error al procesar la propuesta: {str(exc)}"
            )


# =====================================
# 5. CONSULTAR PARTIDA
# =====================================

@router.get("/akinator/status/{game_id}/")
async def game_status(game_id: str):
    game = get_game(game_id)
    aki = game["aki"]

    status = (
        "finished" if game["finished"]
        else "guess" if aki.win
        else "playing"
    )

    return get_game_response(game_id, aki, status)


# =====================================
# 6. ELIMINAR PARTIDA
# =====================================

@router.delete("/akinator/delete/{game_id}/")
async def delete_game(game_id: str):
    async with games_lock:
        game = games.pop(game_id, None)

    if not game:
        raise HTTPException(
            status_code=404,
            detail="Partida no encontrada."
        )

    return {
        "success": True,
        "message": "Partida eliminada.",
        "game_id": game_id
    }
