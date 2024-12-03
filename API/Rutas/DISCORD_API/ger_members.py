
import httpx
from fastapi import APIRouter, HTTPException, Query, Body

from typing import List, Dict

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



def sort_and_paginate(data: Dict[str, int], page: int = 1, paginate: int = 10) -> List[Dict[str, int]]:
    """
    Ordena un diccionario de mayor a menor por valor y pagina los resultados.
    """
    if page < 1 or paginate < 1:
        raise ValueError("La página y la paginación deben ser mayores a 0.")
    
    # Ordenar los datos de mayor a menor por valor
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)

    # Calcular los índices de la paginación
    start_index = (page - 1) * paginate
    end_index = start_index + paginate

    # Paginar los resultados
    paginated_data = sorted_data[start_index:end_index]
    
    return [{"user": k, "value": v} for k, v in paginated_data]

@router.post("/sort-and-paginate")
async def sort_and_paginate_endpoint(
    body: Dict[str, any] = Body(..., description="JSON con datos y parámetros de paginación")
):
    """
    Endpoint que recibe un JSON con un diccionario de usuarios y valores, 
    los ordena de mayor a menor y devuelve los resultados paginados.
    """
    try:
        # Extraer datos y parámetros del JSON recibido
        data = body.get("dic", {})
        page = int(body.get("page", 1))
        paginate = int(body.get("paginas", 10))

        if not isinstance(data, dict) or not data:
            raise ValueError("El campo 'dic' debe ser un diccionario no vacío.")
        
        # Convertir valores de cadenas a enteros
        try:
            data = {k: int(v) for k, v in data.items()}
        except ValueError:
            raise ValueError("Todos los valores en 'dic' deben ser convertibles a enteros.")

        paginated_results = sort_and_paginate(data, page, paginate)
        return {
            "page": page,
            "paginate": paginate,
            "total": len(data),
            "results": paginated_results,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")
