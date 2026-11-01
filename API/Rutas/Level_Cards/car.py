
from easy_pil import Editor, Canvas, Font
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from io import BytesIO
from pathlib import Path
import requests
import uuid
import os
import threading

router = APIRouter()

# Carpeta temporal
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

# Eliminar imagen después de 5 minutos
def delete_image(path):
    def remove():
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    timer = threading.Timer(300, remove)
    timer.daemon = True
    timer.start()


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
    if not isinstance(circle_color, str) or not (
        len(circle_color) in (4, 7)
        and circle_color.startswith("#")
        and all(c in "0123456789abcdefABCDEF" for c in circle_color[1:])
    ):
        circle_color = "#FFFFFF"

    try:
        # Descargar avatar
        avatar_response = requests.get(avatar, timeout=15)
        avatar_response.raise_for_status()

        canvas = Canvas((700, 130), color=(0, 0, 0, 0))
        editor = Editor(canvas.image)

        profile = (
            Editor(BytesIO(avatar_response.content))
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

        # Círculo personalizable
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

        # Guardar imagen
        filename = f"{uuid.uuid4().hex}.png"
        filepath = TEMP_DIR / filename

        editor.image.save(filepath, format="PNG")

        # Programar eliminación
        delete_image(str(filepath))

        # Devolver URL
        return {
            "success": True,
            "url": f"/api/level_up/image/{filename}",
            "expires_in": 300
        }

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



