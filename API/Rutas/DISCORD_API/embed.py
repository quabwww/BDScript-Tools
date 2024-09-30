from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx  # Importar httpx para solicitudes asíncronas

router = APIRouter()

class EmbedRequest(BaseModel):
    channel_id: str
    token: str

@router.post("/send_blackjack_embed/{user_id}/")
async def send_blackjack_embed(user_id: str, author: str, url_author: str, request: EmbedRequest):
    async with httpx.AsyncClient() as client:  # Usar un cliente asíncrono
        # Obtener los datos del juego de Blackjack
        blackjack_response = await client.get("https://bdscript-tools.onrender.com/blackjack/nuevo/")
        
        if blackjack_response.status_code != 200:
            raise HTTPException(status_code=blackjack_response.status_code, detail=blackjack_response.json())
        
        blackjack_data = blackjack_response.json()

        # Imprimir los datos de blackjack para depuración
        print("Datos de Blackjack:", blackjack_data)

        # Construir la descripción
        description_parts = []
        if "pedir" in blackjack_data['acciones_disponibles']:
            description_parts.append("Toma otra carta")
        if "plantarse" in blackjack_data['acciones_disponibles']:
            description_parts.append("Termina el juego")
        if "doblar" in blackjack_data['acciones_disponibles']:
            description_parts.append("Duplica tu apuesta, pide una vez, luego parate.")

        description = "\n".join(description_parts) if description_parts else "No hay acciones disponibles."

        # Verificar que las manos no estén vacías
        if not blackjack_data['mano_jugador'] or not blackjack_data['mano_crupier']:
            raise HTTPException(status_code=400, detail="Las manos están vacías.")

        # Construir el embed
        embed_data = {
            "description": description,
            "color": 0x03a8f4,
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
                "text": f"Cartas Restantes: {blackjack_data['cartas_restantes']} | Partida ID: {blackjack_data['partida_id']}"
            },
             "author": {
                "name": author,  # Cambia esto al nombre deseado
                "url": url_author  # Cambia esto a la URL deseada
            }
        }

        # Verifica que haya al menos un botón
        buttons = []
        for action in blackjack_data['acciones_disponibles']:
            if action == "pedir":
                buttons.append({"type": 2, "label": "Pedir", "style": 1, "custom_id": f"boton-pedir-{user_id}"})
            elif action == "plantarse":
                buttons.append({"type": 2, "label": "Plantarse", "style": 3, "custom_id": f"boton-plantarse-{user_id}"})
            elif action == "doblar":
                buttons.append({"type": 2, "label": "Doblar", "style": 2, "custom_id": f"boton-doblar-{user_id}"})
            elif action == "dividir":
                buttons.append({"type": 2, "label": "Dividir", "style": 2, "custom_id": f"boton-split-{user_id}"})

        # Asegúrate de que haya botones disponibles
        if not buttons:
            raise HTTPException(status_code=400, detail="No hay acciones disponibles para crear botones.")

        # Preparar el payload para Discord
        data = {
            "content": None,  # Puedes dejar esto como None si no quieres un mensaje adicional
            "embeds": [embed_data],  # Asegúrate de usar "embeds" en lugar de "embed"
            "components": [{"type": 1, "components": buttons}]  # Asegúrate de que los botones estén en el formato correcto
        }

        # Enviar el embed a Discord
        headers = {
            "Authorization": f"Bot {request.token}",
            "Content-Type": "application/json"
        }

        discord_response = await client.post(f"https://discord.com/api/v10/channels/{request.channel_id}/messages", json=data, headers=headers)

        if discord_response.status_code != 200:
            raise HTTPException(status_code=discord_response.status_code, detail=discord_response.json())

    return {"detail": "Embed enviado correctamente."}

from main import app
app.include_router(router)

