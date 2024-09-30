from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests

router = APIRouter()

# Configuraciones
BOT_TOKEN = 'TU_TOKEN_AQUI'
DISCORD_API_URL = "https://discord.com/api/v10/channels/{channel_id}/messages"

# Headers para autenticar la API de Discord
headers = {
    "Authorization": f"Bot {BOT_TOKEN}",
    "Content-Type": "application/json"
}

# Modelo Pydantic para el embed
class EmbedModel(BaseModel):
    channel_id: str  # ID del canal de Discord
    description: str
    color: int = 5814783  # Color en decimal (por defecto: verde)
    footer: str = None
    footer_icon_url: str = None
    author_name: str = None
    author_icon_url: str = None
    thumbnail_url: str = None

@router.post("/send_embed")
def send_embed(embed_data: EmbedModel):
    """
    Endpoint para enviar un embed a Discord en un canal específico.
    """

    # Estructura del embed
    embed = {
        "description": embed_data.description,
        "color": embed_data.color,
    }

    # Agregar autor si está disponible
    if embed_data.author_name:
        embed["author"] = {"name": embed_data.author_name}
        if embed_data.author_icon_url:
            embed["author"]["icon_url"] = embed_data.author_icon_url

    # Agregar footer si está disponible
    if embed_data.footer:
        embed["footer"] = {"text": embed_data.footer}
        if embed_data.footer_icon_url:
            embed["footer"]["icon_url"] = embed_data.footer_icon_url

    # Agregar thumbnail si está disponible
    if embed_data.thumbnail_url:
        embed["thumbnail"] = {"url": embed_data.thumbnail_url}

    # Cuerpo de la solicitud con el embed
    data = {
        "embeds": [embed]
    }

    # Reemplazar el canal ID en la URL
    discord_url = DISCORD_API_URL.format(channel_id=embed_data.channel_id)

    # Enviar el mensaje a Discord
    response = requests.post(discord_url, json=data, headers=headers)

    # Verificar el resultado de la solicitud
    if response.status_code == 200:
        return {"message": "Embed enviado exitosamente a Discord."}
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)
