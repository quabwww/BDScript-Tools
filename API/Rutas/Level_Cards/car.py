
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
import os

router = APIRouter()

# Configuración
BASE_URL = "https://bdscript-tools.onrender.com"
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Tiempo de vida: 5 minutos
IMAGE_EXPIRATION = 300


# Eliminar imagen automáticamente
def delete_image(filepath):
    def remove():
        try:
            if filepath.exists():
                filepath.unlink()
        except Exception:
            pass

    timer = threading.Timer(IMAGE_EXPIRATION, remove)
    timer.daemon = True
    timer.start()


# Limpiar archivos antiguos al iniciar
def clean_temp():
    for file in TEMP_DIR.glob("*.png"):
        try:
            if file.is_file():
                file.unlink()
        except Exception:
            pass


clean_temp()


# Generar imagen
@router.get("/api/level_up/")
def level(
    avatar: str,
    level: int = 1,
    circle_color: str = "#FFFFFF"
):

    # Validar nivel
    if level < 1:
        level = 1

    # Validar color hexadecimal
    if not re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})", circle_color):
        circle_color = "#FFFFFF"

    # Validar URL
    parsed = urlparse(avatar)

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(
            status_code=400,
            detail="URL del avatar inválida."
        )

    try:
        # Descargar avatar
        response = requests.get(
            avatar,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()

        if not response.headers.get("Content-Type", "").startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="La URL no contiene una imagen válida."
            )

        # Crear canvas
        canvas = Canvas((700, 130), color=(0, 0, 0, 0))
        editor = Editor(canvas.image)

        # Procesar avatar
        profile = (
            Editor(BytesIO(response.content))
            .resize((101, 101))
            .circle_image()
        )

        # Fuente
        poppins = Font.poppins(size=30)

        desplazamiento_x = 17

        # Fondo
        editor.rectangle(
            (110, 16),
            width=230,
            height=100,
            fill="#25262a",
            radius=15
        )

        # Borde circular personalizable
        editor.ellipse(
            (30 + desplazamiento_x, 11),
            width=110,
            height=110,
            outline=circle_color,
            stroke_width=8
        )

        # Texto
        editor.text(
            (180, 57),
            f"level {level}",
            font=poppins,
            color="white"
        )

        # Avatar
        editor.paste(
            profile.image,
            (35 + desplazamiento_x, 16)
        )

        # Guardar imagen
        filename = f"{uuid.uuid4().hex}.png"
        filepath = TEMP_DIR / filename

        editor.image.save(filepath, format="PNG")

        # Programar eliminación
        delete_image(filepath)

        # URL pública
        image_url = f"{BASE_URL}/api/level_up/image/{filename}"

        return {
            "success": True,
            "url": image_url,
            "filename": filename,
            "expires_in": IMAGE_EXPIRATION
        }

    except HTTPException:
        raise

    except requests.RequestException:
        raise HTTPException(
            status_code=400,
            detail="No se pudo descargar el avatar."
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


