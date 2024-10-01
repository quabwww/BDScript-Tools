from fastapi import APIRouter, HTTPException
from typing import List, Tuple, Dict
import random

router = APIRouter()

# Definimos los valores de las cartas
VALORES_CARTAS = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11
}

# Almacenamiento de las partidas en curso
partidas: Dict[int, Dict] = {}
partida_counter = 0

def crear_baraja() -> List[Tuple[str, str]]:
    """Crea una baraja de cartas."""
    palos = ['Corazones', 'Diamantes', 'Tréboles', 'Picas']
    valores = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    return [(valor, palo) for valor in valores for palo in palos]

def barajar_baraja(baraja: List[Tuple[str, str]]):
    """Baraja la baraja de cartas."""
    random.shuffle(baraja)

def repartir_carta(baraja: List[Tuple[str, str]]) -> Tuple[str, str]:
    """Reparte una carta de la baraja."""
    return baraja.pop()

def calcular_valor_mano(mano: List[Tuple[str, str]]) -> int:
    """Calcula el valor total de una mano."""
    valor = 0
    num_ases = 0
    for carta, _ in mano:
        valor += VALORES_CARTAS[carta]
        if carta == 'A':
            num_ases += 1
    
    while valor > 21 and num_ases:
        valor -= 10
        num_ases -= 1
    
    return valor

def mostrar_mano(mano: List[Tuple[str, str]]) -> str:
    """Muestra las cartas y el valor de una mano."""
    return ', '.join(f"{valor} de {palo}" for valor, palo in mano)

@router.get("/blackjack/nuevo/")
def nueva_partida():
    """Inicia una nueva partida de Blackjack."""
    global partida_counter
    partida_counter += 1  # Incrementar el contador para el ID de la partida
    partida_id = partida_counter

    # Crear y barajar la baraja
    baraja = crear_baraja()
    barajar_baraja(baraja)

    # Repartir las cartas iniciales
    mano_jugador = [repartir_carta(baraja), repartir_carta(baraja)]
    mano_crupier = [repartir_carta(baraja), repartir_carta(baraja)]

    partidas[partida_id] = {
        "baraja": baraja,
        "mano_jugador": mano_jugador,
        "mano_crupier": mano_crupier,
        "finalizada": False
    }

    # Calcular valores
    valor_jugador = calcular_valor_mano(mano_jugador)
    valor_crupier = calcular_valor_mano([mano_crupier[0]])

    if valor_jugador == 21:
        return {
            "partida_id": partida_id,
            "resultado_inicial": "¡Felicidades! Blackjack, el jugador gana.",
            "acciones_disponibles": [],
            "valor_jugador": valor_jugador,
            "valor_crupier": valor_crupier,
            "mano_jugador": mostrar_mano(mano_jugador),
            "mano_crupier": f"{mano_crupier[0][0]} de {mano_crupier[0][1]} y una carta oculta",
            "cartas_restantes": len(baraja)
        }

    # Lista de acciones disponibles
    acciones_disponibles = ["pedir", "plantarse"]

    se_puede_split = mano_jugador[0][0] == mano_jugador[1][0]
    if se_puede_split:
        acciones_disponibles.append("split")

    se_puede_double_down = len(mano_jugador) == 2
    if se_puede_double_down:
        acciones_disponibles.append("doblar")

    return {
        "partida_id": partida_id,
        "resultado_inicial": None,
        "acciones_disponibles": acciones_disponibles,
        "valor_jugador": valor_jugador,
        "valor_crupier": valor_crupier,
        "mano_jugador": mostrar_mano(mano_jugador),
        "mano_crupier": f"{mano_crupier[0][0]} de {mano_crupier[0][1]} y una carta oculta",
        "cartas_restantes": len(baraja)
    }


@router.get("/blackjack/nuevo/")
def nueva_partida():
    """Inicia una nueva partida de Blackjack."""
    global partida_counter
    partida_counter += 1  # Incrementar el contador para el ID de la partida
    partida_id = partida_counter

    # Crear y barajar la baraja
    baraja = crear_baraja()
    barajar_baraja(baraja)

    # Repartir las cartas iniciales
    mano_jugador = [repartir_carta(baraja), repartir_carta(baraja)]
    mano_crupier = [repartir_carta(baraja), repartir_carta(baraja)]

    partidas[partida_id] = {
        "baraja": baraja,
        "mano_jugador": [mano_jugador],  # Cambiado para permitir múltiples manos
        "mano_crupier": mano_crupier,
        "finalizada": False
    }

    # Calcular valores
    valor_jugador = calcular_valor_mano(mano_jugador)
    valor_crupier = calcular_valor_mano([mano_crupier[0]])

    if valor_jugador == 21:
        return {
            "partida_id": partida_id,
            "resultado_inicial": "¡Felicidades! Blackjack, el jugador gana.",
            "acciones_disponibles": [],
            "valor_jugador": valor_jugador,
            "valor_crupier": valor_crupier,
            "mano_jugador": mostrar_mano(mano_jugador),
            "mano_crupier": f"{mano_crupier[0][0]} de {mano_crupier[0][1]} y una carta oculta",
            "cartas_restantes": len(baraja)
        }

    # Lista de acciones disponibles
    acciones_disponibles = ["pedir", "plantarse"]

    se_puede_split = mano_jugador[0][0] == mano_jugador[1][0]
    if se_puede_split:
        acciones_disponibles.append("split")

    se_puede_double_down = len(mano_jugador) == 2
    if se_puede_double_down:
        acciones_disponibles.append("doblar")

    return {
        "partida_id": partida_id,
        "resultado_inicial": None,
        "acciones_disponibles": acciones_disponibles,
        "valor_jugador": valor_jugador,
        "valor_crupier": valor_crupier,
        "mano_jugador": mostrar_mano(mano_jugador),
        "mano_crupier": f"{mano_crupier[0][0]} de {mano_crupier[0][1]} y una carta oculta",
        "cartas_restantes": len(baraja)
    }

@router.get("/blackjack_action/{partida_id}/")
def accion_partida(partida_id: int, accion: str, mano_index: int = 0):
    """Realiza una acción en la partida (pedir, plantarse, doblar, split)."""
    partida = partidas.get(partida_id)
    if not partida:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    if partida["finalizada"]:
        raise HTTPException(status_code=400, detail="La partida ya ha finalizado")

    opciones_disponibles = ["pedir", "plantarse", "doblar", "split"]

    if accion not in opciones_disponibles:
        raise HTTPException(status_code=400, detail="Acción no válida")

    # Manejo de la acción "split"
    if accion == "split":
        if len(partida["mano_jugador"]) == 1:
            mano_original = partida["mano_jugador"][0]
            if mano_original[0][0] == mano_original[1][0]:  # Verificar si se puede dividir
                nueva_mano = [mano_original[1]]  # Segunda mano con la segunda carta
                partida["mano_jugador"] = [mano_original[0], nueva_mano]  # Actualizar las manos
                partida["baraja"].append(repartir_carta(partida["baraja"]))  # Repartir una carta a la nueva mano
                partida["baraja"].append(repartir_carta(partida["baraja"]))  # Repartir una carta a la mano original

                return {
                    "mensaje": "¡Has dividido tu mano!",
                    "mano_jugador": [mostrar_mano(mano) for mano in partida["mano_jugador"]],
                    "cartas_restantes": len(partida["baraja"]),
                    "acciones_disponibles": ["pedir", "plantarse"]  # Opciones de acción actualizadas
                }
            else:
                raise HTTPException(status_code=400, detail="No se puede dividir esta mano")

    # Si se selecciona "pedir"
    if accion == "pedir":
        mano_actual = partida["mano_jugador"][mano_index]
        mano_actual.append(repartir_carta(partida["baraja"]))
        valor_jugador = calcular_valor_mano(mano_actual)
        if valor_jugador > 21:
            partida["finalizada"] = True
            return {
                "mensaje": "¡El jugador se pasa! El crupier gana.",
                "mano_jugador": mostrar_mano(mano_actual),
                "valor_jugador": valor_jugador,
                "mano_crupier": mostrar_mano(partida["mano_crupier"]),
                "valor_crupier": calcular_valor_mano(partida["mano_crupier"]),
                "cartas_restantes": len(partida["baraja"]),
                "ganador": "crupier"
            }

    # Si se selecciona "doblar"
    if accion == "doblar":
        mano_actual = partida["mano_jugador"][mano_index]
        mano_actual.append(repartir_carta(partida["baraja"]))
        valor_jugador = calcular_valor_mano(mano_actual)
        if valor_jugador > 21:
            partida["finalizada"] = True
            return {
                "mensaje": "¡El jugador se pasa al doblar! El crupier gana.",
                "mano_jugador": mostrar_mano(mano_actual),
                "valor_jugador": valor_jugador,
                "mano_crupier": mostrar_mano(partida["mano_crupier"]),
                "valor_crupier": calcular_valor_mano(partida["mano_crupier"]),
                "cartas_restantes": len(partida["baraja"]),
                "ganador": "crupier"
            }
        return {
            "mensaje": "El jugador ha doblado.",
            "mano_jugador": mostrar_mano(mano_actual),
            "valor_jugador": valor_jugador,
            "opciones_disponibles": ["plantarse"],
            "ganador": None
        }

    # Si se selecciona "plantarse"
    if accion == "plantarse":
        valor_jugador = calcular_valor_mano(partida["mano_jugador"][mano_index])
        valor_crupier = calcular_valor_mano(partida["mano_crupier"])

        while valor_crupier < 17:
            partida["mano_crupier"].append(repartir_carta(partida["baraja"]))
            valor_crupier = calcular_valor_mano(partida["mano_crupier"])

        partida["finalizada"] = True

        if valor_crupier > 21 or valor_jugador > valor_crupier:
            return {
                "mensaje": "¡El jugador gana!",
                "mano_jugador": mostrar_mano(partida["mano_jugador"]),
                "valor_jugador": valor_jugador,
                "mano_crupier": mostrar_mano(partida["mano_crupier"]),
                "valor_crupier": valor_crupier,
                "cartas_restantes": len(partida["baraja"]),
                "ganador": "jugador"
            }
        elif valor_jugador < valor_crupier:
            return {
                "mensaje": "¡El crupier gana!",
                "mano_jugador": mostrar_mano(partida["mano_jugador"]),
                "valor_jugador": valor_jugador,
                "mano_crupier": mostrar_mano(partida["mano_crupier"]),
                "valor_crupier": valor_crupier,
                "cartas_restantes": len(partida["baraja"]),
                "ganador": "crupier"
            }
        else:
            return {
                "mensaje": "¡Es un empate!",
                "mano_jugador": mostrar_mano(partida["mano_jugador"]),
                "valor_jugador": valor_jugador,
                "mano_crupier": mostrar_mano(partida["mano_crupier"]),
                "valor_crupier": valor_crupier,
                "cartas_restantes": len(partida["baraja"]),
                "ganador": "empate"
            }

    return {"message": "Acción realizada", "partida_id": partida_id, "accion": accion}

