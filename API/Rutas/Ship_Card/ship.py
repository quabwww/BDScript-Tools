
from easy_pil import Editor, Font
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from PIL import ImageColor
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
import requests
import threading
import uuid
import re

router = APIRouter()

BASE_URL = "https://bdscript-tools.onrender.com"

# Carpeta exclusiva
TEMP_DIR = Path("temp/ship_card")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

EXPIRATION = 300
timers = {}


# Eliminar imagen
def delete_image(filename):
    filepath = TEMP_DIR / filename

    try:
        filepath.unlink(missing_ok=True)
        timers.pop(filename, None)
    except Exception:
        pass


# Descargar imagen con errores específicos
def download_image(url, name="imagen"):
    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise HTTPException(
                400,
                f"{name}: URL inválida"
            )

        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        if response.status_code != 200:
            raise HTTPException(
                400,
                f"{name}: Error HTTP {response.status_code}"
            )

        content_type = response.headers.get("Content-Type", "")

        if not content_type.startswith("image/"):
            raise HTTPException(
                400,
                f"{name}: El enlace no devuelve una imagen. Content-Type: {content_type}"
            )

        return BytesIO(response.content)

    except HTTPException:
        raise

    except requests.Timeout:
        raise HTTPException(
            400,
            f"{name}: Tiempo de espera agotado"
        )

    except requests.RequestException as e:
        raise HTTPException(
            400,
            f"{name}: Error de descarga: {str(e)}"
        )


@router.get("/api/ship-card/")
def image(
    avatar1: str = None,
    avatar2: str = None,
    love: int = 0,
    background_url: str = None,
    circle_color1: str = "#FF0000",
    circle_color2: str = "#FF0000",
    image: str = None
):

    # Visualizar imagen guardada
    if image:
        if not re.fullmatch(r"[a-f0-9]{32}\.png", image):
            raise HTTPException(400, "Nombre de imagen inválido")

        filepath = TEMP_DIR / image

        if not filepath.is_file():
            raise HTTPException(
                404,
                "Imagen no encontrada o expirada"
            )

        return FileResponse(
            filepath,
            media_type="image/png"
        )

    # Validar avatares
    if not avatar1 or not avatar2:
        raise HTTPException(
            400,
            "Debes proporcionar avatar1 y avatar2"
        )

    # Validar colores
    if not re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})", circle_color1):
        circle_color1 = "#FF0000"

    if not re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})", circle_color2):
        circle_color2 = "#FF0000"

    color1 = ImageColor.getrgb(circle_color1)
    color2 = ImageColor.getrgb(circle_color2)

    try:
        # Fondo personalizado o predeterminado
        if background_url:
            background = download_image(
                background_url,
                "Fondo"
            )

            gen = Editor(background).resize((900, 300))

        else:
            gen = Editor(
                "API/Rutas/Ship_Card/fondo.png"
            ).resize((900, 300))

        # Primer avatar
        profile = (
            Editor(download_image(avatar1, "Avatar 1"))
            .resize((200, 200))
            .circle_image()
        )

        # Segundo avatar
        profile_2 = (
            Editor(download_image(avatar2, "Avatar 2"))
            .resize((200, 200))
            .circle_image()
        )

        # Corazón
        corazon = Editor(
            "API/Rutas/Ship_Card/corz.png"
        ).resize((240, 240))

        poppins = Font.poppins(size=80)

        # Pegar corazón
        gen.paste(corazon, (330, 36))

        # Porcentaje
        gen.text(
            (380, 110),
            f"{love}%",
            font=poppins,
            color="white"
        )

        # Primer avatar y círculo
        gen.paste(profile, (100, 50))

        gen.ellipse(
            (100, 50),
            200,
            200,
            outline=color1,
            stroke_width=4
        )

        # Segundo avatar y círculo
        gen.paste(profile_2, (600, 50))

        gen.ellipse(
            (600, 50),
            200,
            200,
            outline=color2,
            stroke_width=4
        )

        # Guardar imagen
        filename = f"{uuid.uuid4().hex}.png"
        filepath = TEMP_DIR / filename

        gen.image.save(filepath, format="PNG")

        # Eliminar después de 5 minutos
        timer = threading.Timer(
            EXPIRATION,
            delete_image,
            args=[filename]
        )

        timer.daemon = True
        timer.start()

        timers[filename] = timer

        # URL pública
        return {
            "success": True,
            "url": f"{BASE_URL}/api/ship-card/?image={filename}",
            "filename": filename,
            "love": love,
            "circle_color1": circle_color1,
            "circle_color2": circle_color2,
            "expires_in": EXPIRATION
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            500,
            f"Error generando Ship Card: {str(e)}"
        )
