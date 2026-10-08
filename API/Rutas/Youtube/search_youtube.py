
import subprocess
import sys
import os
import json

from youtube_search import YoutubeSearch
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_PATH = os.path.join(BASE_DIR, "cookies.txt")


class SearchRequest(BaseModel):
    query: str


def get_youtube_audio_url(video_url):
    try:
        command = [
            sys.executable,
            "-m", "yt_dlp",
            "-g",
            "-f", "bestaudio/best"
        ]

        if os.path.isfile(COOKIES_PATH):
            command.extend(["--cookies", COOKIES_PATH])

        command.append(video_url)

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            cwd=BASE_DIR,
            timeout=60
        )

        return result.stdout.strip().splitlines()[0]

    except Exception as e:
        print(f"Error obteniendo URL del audio: {e}")
        return None


def search_youtube(query):
    try:
        results = YoutubeSearch(
            query,
            max_results=1
        ).to_json()

        data = json.loads(results)
        videos = data.get("videos", [])

        if not videos:
            return None

        # Conservar todos los datos de la búsqueda
        video = videos[0].copy()

        video_id = video.get("id")
        video_url = video.get("url")

        if video_url and video_url.startswith("/"):
            video_url = "https://www.youtube.com" + video_url

        if not video_url and video_id:
            video_url = (
                f"https://www.youtube.com/watch?v={video_id}"
            )

        # Añadir datos al mismo objeto
        video["id"] = video_id
        video["youtube_url"] = video_url
        video["audio_url"] = (
            get_youtube_audio_url(video_url)
            if video_url else None
        )

        return video

    except Exception as e:
        print(f"Error en la búsqueda: {e}")
        return None


class SearchRequest(BaseModel):
    query: str


@router.post("/search_youtube")
def search_youtube_endpoint(request: SearchRequest):
    result = search_youtube(request.query)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron resultados."
        )

    return result
