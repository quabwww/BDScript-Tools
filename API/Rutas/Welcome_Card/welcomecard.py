
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from easy_pil import Editor, Font
from io import BytesIO
import requests
import logging
import os
import uuid
import threading
import time

router = APIRouter()

# Configuración
IMAGE_DIR = "temp_images"
BASE_URL = "https://bdscript-tools.onrender.com"

DEFAULT_BACKGROUND = (
    "https://template.canva.com/EAFTHbpVvzs/1/0/1600w-ogSbUIXfnvw.jpg"
)

os.makedirs(IMAGE_DIR, exist_ok=True)


# ==========================================
# GENERAR WELCOME CARD
# ==========================================

@router.get("/api/welcomecard/")
def get_custom_image(
    avatar: str,
    background: str = DEFAULT_BACKGROUND,
    ctx1: str = "WELCOME",
    ctx2: str = "xquab#0",
    ctx3: str = "You are the 457th Member"
):
    try:

        # Descargar avatar
        avatar_response = requests.get(avatar, timeout=20)
        avatar_response.raise_for_status()

        avatar_image = Editor(
            BytesIO(avatar_response.content)
        ).resize((150, 150)).circle_image()

        # Descargar fondo
        background_response = requests.get(background, timeout=20)
        background_response.raise_for_status()

        background_image = Editor(
            BytesIO(background_response.content)
        ).resize((800, 400)).image

        # Fuentes
        poppins = Font.poppins(size=50, variant="bold")
        poppins_small = Font.poppins(size=25, variant="regular")

        editor = Editor(background_image)

        horizontal_shift = 63

        # Avatar circular
        editor.paste(
            avatar_image.image,
            (250 + horizontal_shift, 90)
        )

        # Borde blanco
        editor.ellipse(
            (250 + horizontal_shift, 90),
            150,
            150,
            outline="white",
            stroke_width=5
        )

        # Textos
        editor.text(
            (320 + horizontal_shift, 260),
            ctx1,
            color="white",
            font=poppins,
            align="center"
        )

        editor.text(
            (320 + horizontal_shift, 315),
            ctx2,
            color="white",
            font=poppins_small,
            align="center"
        )

        editor.text(
            (320 + horizontal_shift, 350),
            ctx3,
            color="white",
            font=poppins_small,
            align="center"
        )

        # Guardar imagen temporalmente
        filename = f"{uuid.uuid4().hex}.png"
        filepath = os.path.join(IMAGE_DIR, filename)

        editor.image.save(filepath, format="PNG")

        # Crear URL pública
        image_url = (
            f"{BASE_URL}/api/welcomecard/image/{filename}"
        )

        return JSONResponse({
            "success": True,
            "message": "Welcome card generated successfully",
            "image_url": image_url,
            "download_url": image_url
        })

    except requests.RequestException:
        raise HTTPException(
            status_code=400,
            detail="Failed to download avatar or background."
        )

    except Exception as e:
        logging.exception("Error generating welcome card")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==========================================
# MOSTRAR / DESCARGAR IMAGEN
# ==========================================

@router.get("/api/welcomecard/image/{filename}")
def get_welcome_image(filename: str):

    if (
        not filename.endswith(".png")
        or os.path.basename(filename) != filename
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename"
        )

    filepath = os.path.join(IMAGE_DIR, filename)

    if not os.path.isfile(filepath):
        raise HTTPException(
            status_code=404,
            detail="Image not found or expired"
        )

    return FileResponse(
        filepath,
        media_type="image/png",
        filename=filename,
        content_disposition_type="inline"
    )


# ==========================================
# LIMPIEZA AUTOMÁTICA (30 MINUTOS)
# ==========================================

def cleanup_images():

    while True:
        try:
            now = time.time()

            for filename in os.listdir(IMAGE_DIR):

                filepath = os.path.join(IMAGE_DIR, filename)

                if os.path.isfile(filepath):

                    file_age = now - os.path.getmtime(filepath)

                    if file_age > 1800:
                        os.remove(filepath)

        except Exception:
            logging.exception("Error cleaning temporary images")

        time.sleep(300)


# Iniciar limpieza automática
threading.Thread(
    target=cleanup_images,
    daemon=True
).start()
