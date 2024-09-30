from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
import httpx

app = FastAPI()
router = APIRouter()

class EmbedButton(BaseModel):
    label: str
    style: int
    custom_id: str

class EmbedRequest(BaseModel):
    channel_id: str
    token: str

@router.post("/send_blackjack_embed/{user_id}/")
async def send_blackjack_embed(user_id: str, request: EmbedRequest):
    # Obtener los datos del juego de Blackjack
    async with httpx.AsyncClient() as client:
        blackjack_response = await client.get("https://bdscript-tools.onrender.com/blackjack/nuevo/")
    
    if blackjack_response.status_code != 200:
        raise HTTPException(status_code=blackjack_response.status_code, detail=blackjack_response.json())
    
    blackjack_data = blackjack_response.json()

    # Construir la descripción
    description_parts = []
    if "pedir" in blackjack_data['acciones_disponibles']:
        description_parts.append("Toma otra carta")
    if "plantarse" in blackjack_data['acciones_disponibles']:
        description_parts.append("Termina el juego")
    if "doblar" in blackjack_data['acciones_disponibles']:
        description_parts.append("Duplica tu apuesta, pide una vez, luego parate.")
    if "dividir" in blackjack_data['acciones_disponibles']:
        description_parts.append("Divide tus cartas en dos manos.")

    description = "\n".join(description_parts) if description_parts else "No hay acciones disponibles."

    # Construir el embed
    embed_data = {
        "description": description,
        "fields": [
            {
                "name": "Tu mano",
                "value": f"{blackjack_data['mano_jugador']}\n\nValor: {str(blackjack_data['valor_jugador'])}",
                "inline": True
            },
            {
                "name": "Mano del crupier",
                "value": f"{blackjack_data['mano_crupier']}\n\nValor: {str(blackjack_data['valor_crupier'])}",
                "inline": True
            }
        ],
        "footer": {
            "text": f"Partida ID: {blackjack_data['partida_id']}"
        }
    }

    # Construir botones según las acciones disponibles
    buttons = []
    for action in blackjack_data['acciones_disponibles']:
        if action == "pedir":
            buttons.append({"label": "Pedir", "style": 1, "custom_id": f"boton-pedir-{user_id})
        elif action == "plantarse":
            buttons.append({"label": "Plantarse", "style": 1, "custom_id": f"boton-plantarse-{user_id}"})
        elif action == "doblar":
            buttons.append({"label": "Doblar", "style": 2, "custom_id": f"boton-doblar-{user_id}"})
        elif action == "dividir":
            buttons.append({"label": "Dividir", "style": 2, "custom_id":f "boton-split-{user_id}"})

    # Preparar el payload para Discord
    data = {
        "channel_id": request.channel_id,
        "embed": embed_data,
        "buttons": buttons
    }

    # Enviar el embed a Discord
    headers = {
        "Authorization": f"Bot {request.token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        discord_response = await client.post(f"https://discord.com/api/v10/channels/{request.channel_id}/messages", json=data, headers=headers)

    if discord_response.status_code != 200:
        raise HTTPException(status_code=discord_response.status_code, detail=discord_response.json())

    return {"detail": "Embed enviado correctamente."}

app.include_router(router)
