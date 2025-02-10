from fastapi import FastAPI, APIRouter
import requests
from io import BytesIO
from easy_pil import Editor
from petpetgif import petpet

# API Key de ImgBB (Reemplázala con tu propia clave)
IMGBB_API_KEY = "c8739bb1c4981c66f1d91d6172550697"

router = APIRouter()

@router.get("/api/petpet")
async def generate_petpet(url: str):
    """Genera un GIF tipo petpet desde una imagen dada por URL y lo sube a ImgBB."""
    try:
        # Descargar la imagen de la URL
        response = requests.get(url)
        response.raise_for_status()  # Lanza error si la descarga falla
        
        # Abrir la imagen con EasyPIL (Editor)
        img = Editor(BytesIO(response.content)).image
        
        # Guardar temporalmente la imagen en BytesIO
        temp_input = BytesIO()
        img.save(temp_input, format="PNG")
        temp_input.seek(0)

        # Generar el GIF con petpet
        temp_output = BytesIO()
        petpet.make(temp_input, temp_output)
        temp_output.seek(0)

        # Subir el GIF a ImgBB
        upload_response = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": IMGBB_API_KEY},
            files={"image": temp_output}
        )

        # Verificar si la subida fue exitosa
        if upload_response.status_code == 200:
            gif_url = upload_response.json()["data"]["url"]
            return {"success": True, "gif_url": gif_url}
        else:
            return {"error": "No se pudo subir el GIF a ImgBB", "details": upload_response.text}

    except requests.exceptions.RequestException as e:
        return {"error": f"Error al descargar la imagen: {str(e)}"}
    except Exception as e:
        return {"error": f"Error procesando la imagen: {str(e)}"}

from main import app
app.include_router(router)
