
from __future__ import annotations

import random
import uuid
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel, Field


router = APIRouter()


# ============================================================
# CONFIGURACION DEL JUEGO
# ============================================================

RANKS = [
    "2", "3", "4", "5", "6", "7",
    "8", "9", "10", "J", "Q", "K", "A"
]

SUITS = ["♠", "♥", "♦", "♣"]

VALUES = {
    **{str(n): n for n in range(2, 11)},
    "J": 10,
    "Q": 10,
    "K": 10,
    "A": 11,
}


# ============================================================
# CLASE HAND: MANO DEL JUGADOR
# Reemplaza dataclass y field
# ============================================================

class Hand:
    def __init__(
        self,
        cards: list[str] | None = None,
        bet: int = 0,
        stood: bool = False,
        doubled: bool = False,
    ):
        self.cards = cards if cards is not None else []
        self.bet = bet
        self.stood = stood
        self.doubled = doubled

    def value(self) -> int:
        total = sum(VALUES[card_rank(card)] for card in self.cards)
        aces = sum(
            card_rank(card) == "A"
            for card in self.cards
        )

        while total > 21 and aces > 0:
            total -= 10
            aces -= 1

        return total

    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.value() == 21

    def is_bust(self) -> bool:
        return self.value() > 21


# ============================================================
# CLASE GAME: ESTADO DE UNA PARTIDA
# Reemplaza dataclass
# ============================================================

class Game:
    def __init__(
        self,
        game_id: str,
        balance: int,
        deck: list[str],
        dealer: list[str],
        hands: list[Hand],
        active_hand: int = 0,
        status: Literal[
            "active", "completed", "abandoned"
        ] = "active",
        result: Any = None,
        settled: bool = False,
        split_used: bool = False,
    ):
        self.game_id = game_id
        self.balance = balance
        self.deck = deck
        self.dealer = dealer
        self.hands = hands
        self.active_hand = active_hand
        self.status = status
        self.result = result
        self.settled = settled
        self.split_used = split_used


# ============================================================
# MODELOS DE ENTRADA
# ============================================================

class NewGameRequest(BaseModel):
    bet: int = Field(default=100, ge=1, le=1_000_000)
    starting_balance: int = Field(
        default=1000,
        ge=1,
        le=10_000_000,
    )


# Almacenamiento en memoria de las partidas
games: dict[str, Game] = {}


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def new_deck() -> list[str]:
    deck = [
        f"{rank}{suit}"
        for rank in RANKS
        for suit in SUITS
    ]
    random.shuffle(deck)
    return deck


def card_rank(card: str) -> str:
    return card[:-1]


def hand_value(cards: list[str]) -> int:
    total = sum(VALUES[card_rank(card)] for card in cards)

    aces = sum(
        card_rank(card) == "A"
        for card in cards
    )

    while total > 21 and aces > 0:
        total -= 10
        aces -= 1

    return total


def draw(game: Game) -> str:
    if not game.deck:
        game.deck = new_deck()

    return game.deck.pop()


def get_game(game_id: str) -> Game:
    game = games.get(game_id)

    if game is None:
        raise HTTPException(
            status_code=404,
            detail="No existe una partida con ese game_id.",
        )

    return game


def require_active(game: Game) -> None:
    if game.status != "active":
        raise HTTPException(
            status_code=409,
            detail=(
                "La partida ya no está activa "
                f"(estado: {game.status})."
            ),
        )


# ============================================================
# ESTADO PUBLICO DE LA PARTIDA
# ============================================================

def public_state(
    game: Game,
    reveal_dealer: bool | None = None,
) -> dict:
    if reveal_dealer is None:
        reveal_dealer = game.status != "active"

    dealer_cards = (
        game.dealer
        if reveal_dealer
        else game.dealer[:1]
    )

    state = {
        "game_id": game.game_id,
        "status": game.status,
        "balance": game.balance,
        "active_hand": (
            game.active_hand
            if game.status == "active"
            else None
        ),
        "dealer": {
            "cards": dealer_cards,
            "value": (
                hand_value(dealer_cards)
                if reveal_dealer
                else None
            ),
            "hidden_cards": (
                0
                if reveal_dealer
                else max(0, len(game.dealer) - 1)
            ),
        },
        "hands": [
            {
                "index": i,
                "cards": hand.cards,
                "value": hand.value(),
                "bet": hand.bet,
                "stood": hand.stood,
                "busted": hand.is_bust(),
                "blackjack": hand.is_blackjack(),
                "doubled": hand.doubled,
            }
            for i, hand in enumerate(game.hands)
        ],
        "result": game.result,
        "available_actions": [],
    }

    if game.status == "active":
        hand = game.hands[game.active_hand]
        actions = []

        if not hand.stood and not hand.is_bust():
            actions.extend(["hit", "stand"])

            if len(hand.cards) == 2 and game.balance >= hand.bet:
                actions.append("double")

            if (
                len(hand.cards) == 2
                and card_rank(hand.cards[0])
                == card_rank(hand.cards[1])
                and not game.split_used
                and len(game.hands) == 1
                and game.balance >= hand.bet
            ):
                actions.append("split")

        state["available_actions"] = actions

    return state


# ============================================================
# FINALIZAR Y PAGAR LAS MANOS
# ============================================================

def settle(game: Game) -> None:
    """Resuelve la partida y paga cada mano una sola vez."""

    if game.settled:
        return

    live_hands = [
        hand
        for hand in game.hands
        if not hand.is_bust()
    ]

    if live_hands:
        while hand_value(game.dealer) < 17:
            game.dealer.append(draw(game))

    dealer_total = hand_value(game.dealer)
    dealer_bust = dealer_total > 21
    outcomes = []

    for index, hand in enumerate(game.hands):
        player_total = hand.value()

        if hand.is_bust():
            outcome = "loss"

        elif (
            hand.is_blackjack()
            and len(game.hands) == 1
        ):
            # Blackjack natural: beneficio de 3:2.
            game.balance += hand.bet + (hand.bet * 3 // 2)
            outcome = "blackjack"

        elif dealer_bust or player_total > dealer_total:
            game.balance += hand.bet * 2
            outcome = "win"

        elif player_total == dealer_total:
            game.balance += hand.bet
            outcome = "push"

        else:
            outcome = "loss"

        outcomes.append({
            "hand": index,
            "outcome": outcome,
            "player_value": player_total,
        })

    game.result = {
        "hands": outcomes,
        "dealer_value": dealer_total,
        "dealer_bust": dealer_bust,
    }

    game.status = "completed"
    game.settled = True


def advance_hand(game: Game) -> None:
    """Avanza a la siguiente mano o termina la partida."""

    while game.active_hand < len(game.hands):
        hand = game.hands[game.active_hand]

        if hand.stood or hand.is_bust():
            game.active_hand += 1
        else:
            break

    if game.active_hand >= len(game.hands):
        settle(game)


# ============================================================
# RUTA DE SALUD
# GET /health
# ============================================================

@router.get("/health")
def health():
    return {"status": "ok"}


# ============================================================
# CREAR PARTIDA
# POST /games
# ============================================================

@router.post("/games", status_code=201)
def create_game(payload: NewGameRequest):
    if payload.bet > payload.starting_balance:
        raise HTTPException(
            status_code=422,
            detail="La apuesta no puede superar el saldo inicial.",
        )

    game = Game(
        game_id=str(uuid.uuid4()),
        balance=payload.starting_balance - payload.bet,
        deck=new_deck(),
        dealer=[],
        hands=[Hand(bet=payload.bet)],
    )

    hand = game.hands[0]

    hand.cards.extend([
        draw(game),
        draw(game),
    ])

    game.dealer.extend([
        draw(game),
        draw(game),
    ])

    games[game.game_id] = game

    player_bj = hand.is_blackjack()

    dealer_bj = (
        hand_value(game.dealer) == 21
        and len(game.dealer) == 2
    )

    if player_bj or dealer_bj:
        if player_bj and dealer_bj:
            game.balance += payload.bet
            outcome = "push"

        elif player_bj:
            game.balance += (
                payload.bet
                + (payload.bet * 3 // 2)
            )
            outcome = "blackjack"

        else:
            outcome = "loss"

        game.status = "completed"
        game.result = {
            "hands": [{
                "hand": 0,
                "outcome": outcome,
                "player_value": hand.value(),
            }],
            "dealer_value": hand_value(game.dealer),
        }
        game.settled = True

    return public_state(game)


# ============================================================
# CONSULTAR PARTIDA
# GET /games/{game_id}
# ============================================================

@router.get("/games/{game_id}")
def get_game_state(game_id: str):
    return public_state(get_game(game_id))


# ============================================================
# PEDIR CARTA
# POST /games/{game_id}/hit
# ============================================================

@router.post("/games/{game_id}/hit")
def hit(game_id: str):
    game = get_game(game_id)
    require_active(game)

    hand = game.hands[game.active_hand]
    hand.cards.append(draw(game))

    if hand.is_bust():
        hand.stood = True
        advance_hand(game)

    return public_state(game)


# ============================================================
# PLANTARSE
# POST /games/{game_id}/stand
# ============================================================

@router.post("/games/{game_id}/stand")
def stand(game_id: str):
    game = get_game(game_id)
    require_active(game)

    game.hands[game.active_hand].stood = True

    advance_hand(game)

    return public_state(game)


# ============================================================
# DOBLAR APUESTA
# POST /games/{game_id}/double
# ============================================================

@router.post("/games/{game_id}/double")
def double_down(game_id: str):
    game = get_game(game_id)
    require_active(game)

    hand = game.hands[game.active_hand]

    if len(hand.cards) != 2:
        raise HTTPException(
            status_code=409,
            detail="Solo puedes doblar con las dos primeras cartas.",
        )

    if game.balance < hand.bet:
        raise HTTPException(
            status_code=409,
            detail="Saldo insuficiente para doblar.",
        )

    game.balance -= hand.bet
    hand.bet *= 2
    hand.doubled = True

    hand.cards.append(draw(game))
    hand.stood = True

    advance_hand(game)

    return public_state(game)


# ============================================================
# DIVIDIR PAREJA
# POST /games/{game_id}/split
# ============================================================

@router.post("/games/{game_id}/split")
def split(game_id: str):
    game = get_game(game_id)
    require_active(game)

    hand = game.hands[game.active_hand]

    if game.split_used or len(game.hands) != 1:
        raise HTTPException(
            status_code=409,
            detail=(
                "Esta versión permite dividir "
                "una sola pareja por partida."
            ),
        )

    if (
        len(hand.cards) != 2
        or card_rank(hand.cards[0])
        != card_rank(hand.cards[1])
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Necesitas dos cartas del mismo valor "
                "para dividir."
            ),
        )

    if game.balance < hand.bet:
        raise HTTPException(
            status_code=409,
            detail="Saldo insuficiente para dividir.",
        )

    game.balance -= hand.bet

    second_card = hand.cards.pop()

    second_hand = Hand(
        cards=[second_card],
        bet=hand.bet,
    )

    hand.cards.append(draw(game))
    second_hand.cards.append(draw(game))

    game.hands.append(second_hand)
    game.split_used = True
    game.active_hand = 0

    return public_state(game)


# ============================================================
# ABANDONAR PARTIDA
# POST /games/{game_id}/finish
# ============================================================

@router.post("/games/{game_id}/finish")
def finish_game(game_id: str):
    game = get_game(game_id)
    require_active(game)

    game.status = "abandoned"

    game.result = {
        "outcome": "abandoned",
        "message": (
            "Partida finalizada por el cliente; "
            "la apuesta no se devuelve."
        ),
    }

    return public_state(
        game,
        reveal_dealer=True,
    )


from main import app
app.include_router(router)
