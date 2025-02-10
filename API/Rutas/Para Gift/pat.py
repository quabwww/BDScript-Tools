from fastapi import FastAPI, APIRouter, Response
import requests
from io import BytesIO
from easy_pil import Editor
from petpetgif import petpet


router = APIRouter()

@router.get("/api/petpet")
async def generate_petpet(url: str):
    """Genera un GIF tipo petpet desde una imagen dada por URL."""
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

        # Devolver el GIF en la respuesta
        return Response(content=temp_output.getvalue(), media_type="image/gif")

    except requests.exceptions.RequestException as e:
        return {"error": f"Error al descargar la imagen: {str(e)}"}
    except Exception as e:
        return {"error": f"Error procesando la imagen: {str(e)}"}


from main import app
app.include_router(router)
