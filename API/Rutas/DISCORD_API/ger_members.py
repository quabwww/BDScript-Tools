from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, List

# Configura el router de FastAPI
router = APIRouter()

# Define el modelo de entrada
class PaginationRequest(BaseModel):
    dic: Dict[str, str]
    page: int
    paginas: int

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
    
    return [{"user": k, "value": v} for k, v in paginated_data]

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

        # Realizar la paginación
        paginated_results = sort_and_paginate(data, body.page, body.paginas)
        return {
            "page": body.page,
            "paginate": body.paginas,
            "total": len(data),
            "results": paginated_results,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")
