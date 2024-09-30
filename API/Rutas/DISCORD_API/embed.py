from fastapi import APIRouter, HTTPException
import requests
from pydantic import BaseModel, conlist

router = APIRouter()

class Field(BaseModel):
    name: str
    value: str
    inline: bool = False  # Por defecto, los campos no son inline

class Embed(BaseModel):
    description: str
    footer: str
    author: str
    author_icon: str
    fields: conlist(Field)  # Lista de campos

@router.post("/send_embed/")
def send_embed(channel_id: str, token: str, embed: Embed):
    """Envía un embed a un canal de Discord."""
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    embed_data = {
        "embeds": [
            {
                "description": embed.description,
                "footer": {
                    "text": embed.footer,
                },
                "author": {
                    "name": embed.author,
                    "icon_url": embed.author_icon
                },
                "fields": [
                    {
                        "name": field.name,
                        "value": field.value,
                        "inline": field.inline
                    } for field in embed.fields
                ]
            }
        ]
    }

    response = requests.post(url, json=embed_data, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return {"message": "Embed enviado con éxito"}
