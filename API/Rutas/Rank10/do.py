import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import asyncio
from easy_pil import Editor, Font
import tempfile
from fastapi import APIRouter, Response, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from fastapi import Request


import requests
import os



def descargar_imagen(url, tamaño=None):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            imagen = Image.open(BytesIO(response.content)).convert("RGBA")
            if tamaño:
                imagen = imagen.resize(tamaño)
            return imagen
    except Exception:
        pass
    return None

def truncar_nombre(texto, max_largo=15):
    return texto[:max_largo-2] + ".." if len(texto) > max_largo else texto

# 🔹 Función para convertir números a formato abreviado
def abreviar_numero(num):
    num = int(num)
    return f"{num // 1_000_000}M" if num >= 1_000_000 else f"{num // 1_000}k" if num >= 1_000 else str(num)



API_KEY_IMGBB = "c8739bb1c4981c66f1d91d6172550697"

def subir_a_imgbb(imagen_path):
    """Sube una imagen a ImgBB y retorna la URL de la imagen."""
    url = "https://api.imgbb.com/1/upload"
    with open(imagen_path, "rb") as archivo:
        response = requests.post(url, data={"key": API_KEY_IMGBB, "expiration": 3600}, files={"image": archivo})
    
    if response.status_code == 200:
        return response.json().get("data", {}).get("url")
    return None


def crear_imagen(ID_EMOJI, URL_FONDO, AVATARES_URLS, nombres, valores_extra, color_texto, numeracion, number_espace: int=120):
    emoji_img = descargar_imagen(f"https://cdn.discordapp.com/emojis/{ID_EMOJI}.png?v=1", (30, 30))

    ancho, alto = 900, 730  

# 📌 Descargar fondo
    fondo = descargar_imagen(URL_FONDO, (ancho, alto))
    if not fondo:
        fondo = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))

# 📌 Configuración de rectángulos y elementos
    num_rectangulos = 10
    ancho_rectangulo, alto_rectangulo = 780, 60
    espacio_entre_rectangulos, radio_redondeo = 10, 20
    desplazamiento_x, desplazamiento_y = 100, 20
    espacio_columnas, espacio_columna_extra, espacio_columna_numeros = 50, -180, -20
    margen_texto_x, margen_texto_y, tamaño_texto = 20, 20, 30
    color_texto = color_texto

# 📌 Configuración de círculos
    radio_circulo, color_circulo = 5, (111, 111, 111, 255)
    espacio_circulo_x, ajuste_circulo_x, ajuste_circulo_y = number_espace, -1, 0

# 📌 Configuración de avatares
    TAMAÑO_AVATAR = (53, 53)
    DESPLAZAMIENTO_AVATAR_X = -80  # 🔹 Cambia este valor para mover los avatares (positivo = derecha, negativo = izquierda)



# 🔹 Función para truncar nombres largos


# 📌 Cargar la fuente
    try:
        fuente = ImageFont.truetype("API/Rutas/Rank10/n.otf", tamaño_texto)
    except IOError:
        fuente = ImageFont.load_default()

# 📌 Dibujar sobre el fondo
    dibujar = ImageDraw.Draw(fondo)
    color_rectangulo = (47, 49, 54, 255)

    n = numeracion
    for i in range(num_rectangulos):
        x1, x2 = desplazamiento_x, desplazamiento_x + ancho_rectangulo
        y1, y2 = desplazamiento_y + i * (alto_rectangulo + espacio_entre_rectangulos), desplazamiento_y + i * (alto_rectangulo + espacio_entre_rectangulos) + alto_rectangulo

        dibujar.rounded_rectangle([x1, y1, x2, y2], fill=color_rectangulo, radius=radio_redondeo)
        dibujar.text((x1 + margen_texto_x, y1 + margen_texto_y), f"#{n}", fill=color_texto, font=fuente)
        n += 1

        x_circulo_izq = x1 + espacio_circulo_x + ajuste_circulo_x
        y_circulo = y1 + (alto_rectangulo // 2) - radio_circulo + ajuste_circulo_y
        dibujar.ellipse([x_circulo_izq, y_circulo, x_circulo_izq + 2 * radio_circulo, y_circulo + 2 * radio_circulo], fill=color_circulo)

        x_circulo_der = x2 + espacio_columna_extra
        dibujar.ellipse([x_circulo_der, y_circulo, x_circulo_der + 2 * radio_circulo, y_circulo + 2 * radio_circulo], fill=color_circulo)

        dibujar.text((x_circulo_izq + espacio_columnas, y_circulo - 5), truncar_nombre(nombres[i]), fill=color_texto, font=fuente)

        if emoji_img:
            fondo.paste(emoji_img, (x_circulo_der + 25, y_circulo - 10), emoji_img)

        dibujar.text((x_circulo_der + 55 - espacio_columna_numeros, y_circulo - 5), abreviar_numero(valores_extra[i]), fill=color_texto, font=fuente)

    # 📌 Descargar y colocar avatar único para cada usuario
        avatar_url = AVATARES_URLS[i] if i < len(AVATARES_URLS) else AVATARES_URLS[0]  
        avatar_img = descargar_imagen(avatar_url, TAMAÑO_AVATAR)
    
        if avatar_img:
            fondo.paste(avatar_img, (x1 + DESPLAZAMIENTO_AVATAR_X, y1 + 5), avatar_img)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        fondo.save(temp_file, format="PNG")
        temp_file_path = temp_file.name

    url_imgbb = subir_a_imgbb(temp_file_path)

    return url_imgbb  # 🔹 Retorna la URL de la imagen subida

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

class Estruc(BaseModel):
    id_emoji: str
    url_fondo: str
    avatares_url: List[str]
    nombres: List[str] 
    valores_extra: List[str]
    color_texto: str
    numeracion: int
    number_espace: int = 120


router = APIRouter()



@router.post("/api/board10/")
async def bck(request: Request, body: Estruc):
    imagen = crear_imagen(body.id_emoji, 
                          body.url_fondo, 
                          body.avatares_url, 
                          body.nombres, 
                          body.valores_extra, 
                          body.color_texto, 
                          body.numeracion, 
                          body.number_espace)
    return imagen
    
from main import app
app.include_router(router)
