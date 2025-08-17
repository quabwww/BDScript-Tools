from fastapi import APIRouter, Query
import requests

app = APIRouter()

BASE_URL = "https://discord.com/api/v10"

@app.get("/miembros")
def obtener_miembros(
    bot_token: str = Query(..., description="Token del bot de Discord"),
    guild_id: str = Query(..., description="ID del servidor de Discord")
):
    """
    Obtiene todos los miembros de un servidor de Discord usando la API REST.
    Se pagina de 1000 en 1000 usando el parámetro 'after'.
    """
    url = f"{BASE_URL}/guilds/{guild_id}/members"
    headers = {"Authorization": f"Bot {bot_token}"}
    
    miembros = []
    after = None

    while True:
        params = {"limit": 1000}
        if after:
            params["after"] = after

        r = requests.get(url, headers=headers, params=params)

        if r.status_code != 200:
            return {"error": r.json()}

        data = r.json()
        if not data:
            break

        for miembro in data:
            miembros.append({
                "id": miembro["user"]["id"],
                "username": miembro["user"]["username"]
            })

        after = data[-1]["user"]["id"]

    return {"miembros": miembros, "total": len(miembros)}
  
