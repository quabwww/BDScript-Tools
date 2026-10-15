
import requests
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

KITSU_API = "https://kitsu.io/api/edge/anime"


@router.get("/buscar")
def buscar_anime(
    busqueda: str = Query(..., min_length=1),
    limite: int = Query(10, ge=1, le=20)
):
    try:
        respuesta = requests.get(
            KITSU_API,
            params={
                "filter[text]": busqueda,
                "page[limit]": limite
            },
            timeout=15
        )
        respuesta.raise_for_status()
        datos = respuesta.json().get("data", [])

        resultados = []

        for anime in datos:
            info = anime.get("attributes", {})

            resultados.append({
                "id": anime.get("id"),
                "titulo": info.get("canonicalTitle"),
                "titulos": info.get("titles", {}),
                "sinopsis": info.get("synopsis"),
                "episodios": info.get("episodeCount"),
                "duracion": info.get("episodeLength"),
                "puntuacion": info.get("averageRating"),
                "estado": info.get("status"),
                "fecha_inicio": info.get("startDate"),
                "fecha_fin": info.get("endDate"),
                "generos": [],
                "imagen": (
                    info.get("posterImage") or {}
                ).get("large"),
                "portada": (
                    info.get("coverImage") or {}
                ).get("large"),
                "url": f"https://kitsu.io/anime/{info.get('slug', '')}"
            })

        return {
            "busqueda": busqueda,
            "numero_resultados": len(resultados),
            "resultados": resultados
        }

    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error al consultar Kitsu API: {str(e)}"
        )
