from fastapi import APIRouter, HTTPException
import requests
from pydantic import BaseModel, conlist

router = APIRouter()

class Field(BaseModel):
    name: str
    value: str
    inline: bool = False  # Por defecto, los campos no son inline

class Button(BaseModel):
    type: int = 2  # 2 es el tipo de botón
    label: str
    style: int  # Estilo del botón (1 = primario, 2 = secundario, 3 = éxito, 4 = peligro)
    custom_id: str

class Embed(BaseModel):
    description: str
    footer: str
    author: str
    author_icon: str
    fields: conlist(Field)  # Lista de campos

class MessageData(BaseModel):
    embed: Embed
    buttons: conlist(Button)  # Lista de botones

@router.post("/send_embed/")
def send_embed(channel_id: str, token: str, message_data: MessageData):
    """Envía un embed a un canal de Discord con botones."""
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    
    embed_data = {
        "embeds": [
            {
                "description": message_data.embed.description,
                "footer": {
                    "text": message_data.embed.footer,
                },
                "author": {
                    "name": message_data.embed.author,
                    "icon_url": message_data.embed.author_icon
                },
                "fields": [
                    {
                        "name": field.name,
                        "value": field.value,
                        "inline": field.inline
                    } for field in message_data.embed.fields
                ]
            }
        ],
        "components": [
            {
                "type": 1,
                "components": [
                    {
                        "type": button.type,
                        "label": button.label,
                        "style": button.style,
                        "custom_id": button.custom_id
                    } for button in message_data.buttons
                ]
            }
        ]
    }

    response = requests.post(url, json=embed_data, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return {"message": "Embed con botones enviado con éxito"}
