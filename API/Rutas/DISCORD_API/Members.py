import time
from fastapi import APIRouter, HTTPException
import requests
from typing import Dict, List

router = APIRouter()

DISCORD_API_BASE_URL = "https://discord.com/api/v10"
MEMBERS_LIMIT_PER_REQUEST = 1000

def fetch_with_rate_limit(url: str, headers: dict, params: dict = None):
    while True:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 1))
            print(f"Rate limit hit, retrying after {retry_after} seconds.")
            time.sleep(retry_after)
        else:
            return response

def fetch_members_with_role(guild_id: str, role_id: str, token: str, page: int, limit: int) -> Dict:
    headers = {"Authorization": f"Bot {token}"}
    url = f"{DISCORD_API_BASE_URL}/guilds/{guild_id}/members"

    role_members = []
    after = None

    while True:
        params = {"limit": MEMBERS_LIMIT_PER_REQUEST}
        if after:
            params["after"] = after

        response = fetch_with_rate_limit(url, headers, params)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Error fetching members from Discord API")

        members = response.json()

        if not members:
            break

        # Filtrar miembros que tienen el rol específico
        for member in members:
            if role_id in member.get('roles', []):
                role_members.append({
                    'id': member['user']['id'],
                    'assigned_at': "Fecha ficticia"
                })

        after = members[-1]['user']['id'] if members else None
        if len(role_members) >= limit or not after:
            break

    total_count = len(role_members)
    total_pages = (total_count + limit - 1) // limit

    # Paginación de resultados
    start = (page - 1) * limit
    end = start + limit
    paginated_members = role_members[start:end]

    return {
        "page": page,
        "limit": limit,
        "total_members": total_count,
        "total_pages": total_pages,
        "member_ids": [member['id'] for member in paginated_members],
        "assigned_at_dates": {member['id']: member['assigned_at'] for member in paginated_members}
    }

@router.get("/api-discord/roles/{guild_id}/{role_id}/{page}/{limit}/")
def get_members_by_role(guild_id: str, role_id: str, page: int, limit: int, token: str):
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="Page and limit must be greater than 0")
    
    response = fetch_members_with_role(guild_id, role_id, token, page, limit)
    return response


router.include_router(router)
