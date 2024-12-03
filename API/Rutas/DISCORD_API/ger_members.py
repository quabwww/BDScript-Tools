from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import math

# Configura el router de FastAPI
router = APIRouter()

# Define el modelo de entrada
class PaginationRequest(BaseModel):
    dic: Dict[str, str]
    page: int
    paginas: int
    id: Optional[str] = None  # Parámetro opcional para buscar un ID específico

def sort_and_paginate(data: Dict[str, int], page: int = 1, paginate: int = 10) -> List[Dict[str, int]]:
    """
    Ordena un diccionario de mayor a menor por valor y pagina los resultados.
    """
    if page < 1 or paginate < 1:
        raise ValueError("La página y la paginación deben ser mayores a 0.")
    
    # Ordenar los datos de mayor a menor por valor
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)

    # Calcular los índices de la paginación
    start_index = (page - 1) * paginate
    end_index = start_index + paginate

    # Paginar los resultados
    paginated_data = sorted_data[start_index:end_index]
    
    # Incluir la enumeración a partir de 1
    return [{"position": idx + 1, "user": k, "value": v} for idx, (k, v) in enumerate(paginated_data, start=start_index)]

def find_position(data: Dict[str, int], user_id: str) -> Optional[int]:
    """
    Busca la posición de un usuario por su ID en la lista ordenada.
    """
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    for idx, (k, _) in enumerate(sorted_data, start=1):
        if k == user_id:
            return idx
    return None

@router.post("/sort-and-paginate")
async def sort_and_paginate_endpoint(body: PaginationRequest):
    """
    Endpoint que recibe un JSON con un diccionario de usuarios y valores, 
    los ordena de mayor a menor y devuelve los resultados paginados.
    """
    try:
        # Convertir los valores del diccionario de cadenas a enteros
        try:
            data = {k: int(v) for k, v in body.dic.items()}
        except ValueError:
            raise ValueError("Todos los valores en 'dic' deben ser convertibles a enteros.")

        # Total de elementos y cálculo de páginas
        total_items = len(data)
        total_pages = math.ceil(total_items / body.paginas)

        # Validar que la página solicitada esté dentro del rango válido
        if body.page > total_pages:
            raise ValueError("La página solicitada excede el número total de páginas disponibles.")

        # Buscar la posición del usuario si se proporciona un ID
        user_position = None
        if body.id:
            user_position = find_position(data, body.id)
            if user_position is None:
                raise ValueError(f"El ID '{body.id}' no se encontró en los datos.")

        # Realizar la paginación
        paginated_results = sort_and_paginate(data, body.page, body.paginas)
        return {
            "current_page": body.page,
            "items_per_page": body.paginas,
            "total_items": total_items,
            "total_pages": total_pages,
            "user_position": user_position,
            "results": paginated_results,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


