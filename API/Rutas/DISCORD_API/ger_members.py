from fastapi import APIRouter, HTTPException, Query
import httpx

# Configura el router de FastAPI
router = APIRouter()

DISCORD_BASE_URL = "https://discord.com/api/v10"

async def fetch_guild_members(guild_id: int, bot_token: str):
    """
    Función que consulta la API de Discord para obtener los miembros de un servidor.
    """
    url = f"{DISCORD_BASE_URL}/guilds/{guild_id}/members"
    headers = {
        "Authorization": f"Bot {bot_token}"
    }
    params = {
        "limit": 1000  # Límite máximo permitido por Discord
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Error al obtener miembros: {response.json().get('message', 'Unknown error')}"
        )

    members = response.json()
    return [member["user"]["id"] for member in members]

@router.get("/guild/{guild_id}/members")
async def get_guild_members(
    guild_id: int,
    bot_token: str = Query(..., description="Token del bot de Discord")
):
    """
    Endpoint para obtener los IDs de los miembros de un servidor.
    """
    try:
        member_ids = await fetch_guild_members(guild_id, bot_token)
        return {"guild_id": guild_id, "member_ids": member_ids}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
