
from easy_pil import Editor, Canvas, Font
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
import requests
import uuid
import threading
import re

router = APIRouter()

BASE_URL = "https://bdscript-tools.onrender.com"
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

EXPIRATION = 300
timers = {}


def delete_image(filename):
    filepath = TEMP_DIR / filename

    try:
        filepath.unlink(missing_ok=True)
        timers.pop(filename, None)
    except Exception:
        pass


@router.get("/api/level_up/")
def level(
    avatar: str = None,
    level: int = 1,
    circle_color: str = "#FFFFFF",
    image: str = None
):

    # Mostrar imagen utilizando el mismo endpoint
    if image:
        if not re.fullmatch(r"[a-f0-9]{32}\.png", image):
            raise HTTPException(400, "Nombre inválido")

        filepath = TEMP_DIR / image

        if not filepath.is_file():
            raise HTTPException(404, "Imagen no encontrada o expirada")

        return FileResponse(
            filepath,
            media_type="image/png"
        )

    # Generar imagen
    if not avatar:
        raise HTTPException(400, "Debes proporcionar un avatar")

    parsed = urlparse(avatar)

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(400, "URL de avatar inválida")

    if level < 1:
        level = 1

    if not re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})", circle_color):
        circle_color = "#FFFFFF"

    try:
        response = requests.get(
            avatar,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()

        if not response.headers.get("Content-Type", "").startswith("image/"):
            raise HTTPException(400, "El avatar no es una imagen")

        canvas = Canvas((700, 130), color=(0, 0, 0, 0))
        editor = Editor(canvas.image)

        profile = (
            Editor(BytesIO(response.content))
            .resize((101, 101))
            .circle_image()
        )

        poppins = Font.poppins(size=30)
        desplazamiento_x = 17

        editor.rectangle(
            (110, 16),
            width=230,
            height=100,
            fill="#25262a",
            radius=15
        )

        editor.ellipse(
            (30 + desplazamiento_x, 11),
            width=110,
            height=110,
            outline=circle_color,
            stroke_width=8
        )

        editor.text(
            (180, 57),
            f"level {level}",
            font=poppins,
            color="white"
        )

        editor.paste(
            profile.image,
            (35 + desplazamiento_x, 16)
        )

        filename = f"{uuid.uuid4().hex}.png"
        filepath = TEMP_DIR / filename

        editor.image.save(filepath, format="PNG")

        # Eliminar después de 5 minutos
        timer = threading.Timer(EXPIRATION, delete_image, args=[filename])
        timer.daemon = True
        timer.start()
        timers[filename] = timer

        return {
            "success": True,
            "url": f"{BASE_URL}/api/level_up/?image={filename}",
            "filename": filename,
            "expires_in": EXPIRATION
        }

    except HTTPException:
        raise

    except requests.RequestException:
        raise HTTPException(400, "Error descargando el avatar")

    except Exception as e:
        raise HTTPException(500, str(e))
