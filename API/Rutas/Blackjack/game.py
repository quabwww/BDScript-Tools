from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from typing import Literal

from fastapi import FastAPI, HTTPException, APIRouter

from pydantic import BaseModel, Field

app = APIRouter()

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
SUITS = ["♠", "♥", "♦", "♣"]
VALUES = {str(n): n for n in range(2, 11)} | {"J": 10, "Q": 10, "K": 10, "A": 11}


@dataclass
class Hand:
    cards: list[str] = field(default_factory=list)
    bet: int = 0
    stood: bool = False
    doubled: bool = False

    def value(self) -> int:
        total = sum(VALUES[card[:-1]] for card in self.cards)
        aces = sum(card[:-1] == "A" for card in self.cards)
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.value() == 21

    def is_bust(self) -> bool:
        return self.value() > 21


@dataclass
class Game:
    game_id: str
    balance: int
    deck: list[str]
    dealer: list[str]
    hands: list[Hand]
    active_hand: int = 0
    status: Literal["active", "completed", "abandoned"] = "active"
    result: str | None = None
    settled: bool = False
    split_used: bool = False


class NewGameRequest(BaseModel):
    bet: int = Field(default=100, ge=1, le=1_000_000)
    starting_balance: int = Field(default=1000, ge=1, le=10_000_000)


games: dict[str, Game] = {}


def new_deck() -> list[str]:
    deck = [f"{rank}{suit}" for rank in RANKS for suit in SUITS]
    random.shuffle(deck)
    return deck


def draw(game: Game) -> str:
    if not game.deck:
        game.deck = new_deck()
    return game.deck.pop()


def card_rank(card: str) -> str:
    return card[:-1]


def hand_value(cards: list[str]) -> int:
    total = sum(VALUES[card_rank(card)] for card in cards)
    aces = sum(card_rank(card) == "A" for card in cards)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def get_game(game_id: str) -> Game:
    game = games.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="No existe una partida con ese game_id.")
    return game


def require_active(game: Game) -> None:
    if game.status != "active":
        raise HTTPException(status_code=409, detail=f"La partida ya no está activa (estado: {game.status}).")


def public_state(game: Game, reveal_dealer: bool | None = None) -> dict:
    if reveal_dealer is None:
        reveal_dealer = game.status != "active"

    dealer_cards = game.dealer if reveal_dealer else game.dealer[:1]
    state = {
        "game_id": game.game_id,
        "status": game.status,
        "balance": game.balance,
        "active_hand": game.active_hand if game.status == "active" else None,
        "dealer": {
            "cards": dealer_cards,
            "value": hand_value(dealer_cards) if reveal_dealer else None,
            "hidden_cards": 0 if reveal_dealer else max(0, len(game.dealer) - 1),
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
                and card_rank(hand.cards[0]) == card_rank(hand.cards[1])
                and not game.split_used
                and len(game.hands) == 1
                and game.balance >= hand.bet
            ):
                actions.append("split")
        state["available_actions"] = actions
    return state


def settle(game: Game) -> None:
    """Resolve dealer play and pay all hands exactly once."""
    if game.settled:
        return

    live_hands = [hand for hand in game.hands if not hand.is_bust()]
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
        elif hand.is_blackjack() and len(game.hands) == 1:
            # Natural blackjack pays 3:2 profit (stake already deducted).
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
        outcomes.append({"hand": index, "outcome": outcome, "player_value": player_total})

    game.result = {
        "hands": outcomes,
        "dealer_value": dealer_total,
        "dealer_bust": dealer_bust,
    }  # type: ignore[assignment]
    game.status = "completed"
    game.settled = True


def advance_hand(game: Game) -> None:
    """Move to the next hand or settle when every hand is finished."""
    while game.active_hand < len(game.hands):
        hand = game.hands[game.active_hand]
        if hand.stood or hand.is_bust():
            game.active_hand += 1
        else:
            break

    if game.active_hand >= len(game.hands):
        settle(game)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/games", status_code=201)
def create_game(payload: NewGameRequest):
    if payload.bet > payload.starting_balance:
        raise HTTPException(status_code=422, detail="La apuesta no puede superar el saldo inicial.")

    game = Game(
        game_id=str(uuid.uuid4()),
        balance=payload.starting_balance - payload.bet,
        deck=new_deck(),
        dealer=[],
        hands=[Hand(bet=payload.bet)],
    )
    hand = game.hands[0]
    hand.cards.extend([draw(game), draw(game)])
    game.dealer.extend([draw(game), draw(game)])
    games[game.game_id] = game

    player_bj = hand.is_blackjack()
    dealer_bj = hand_value(game.dealer) == 21 and len(game.dealer) == 2
    if player_bj or dealer_bj:
        if player_bj and dealer_bj:
            game.balance += payload.bet
            game.status = "completed"
            game.result = {"hands": [{"hand": 0, "outcome": "push", "player_value": 21}], "dealer_value": 21}
            game.settled = True
        elif player_bj:
            game.balance += payload.bet + (payload.bet * 3 // 2)
            game.status = "completed"
            game.result = {"hands": [{"hand": 0, "outcome": "blackjack", "player_value": 21}], "dealer_value": hand_value(game.dealer)}
            game.settled = True
        else:
            game.status = "completed"
            game.result = {"hands": [{"hand": 0, "outcome": "loss", "player_value": hand.value()}], "dealer_value": 21}
            game.settled = True

    return public_state(game)


@app.get("/games/{game_id}")
def get_game_state(game_id: str):
    return public_state(get_game(game_id))


@app.post("/games/{game_id}/hit")
def hit(game_id: str):
    game = get_game(game_id)
    require_active(game)
    hand = game.hands[game.active_hand]
    hand.cards.append(draw(game))
    if hand.is_bust():
        hand.stood = True
        advance_hand(game)
    return public_state(game)


@app.post("/games/{game_id}/stand")
def stand(game_id: str):
    game = get_game(game_id)
    require_active(game)
    game.hands[game.active_hand].stood = True
    advance_hand(game)
    return public_state(game)


@app.post("/games/{game_id}/double")
def double_down(game_id: str):
    game = get_game(game_id)
    require_active(game)
    hand = game.hands[game.active_hand]
    if len(hand.cards) != 2:
        raise HTTPException(status_code=409, detail="Solo puedes doblar con las dos primeras cartas.")
    if game.balance < hand.bet:
        raise HTTPException(status_code=409, detail="Saldo insuficiente para doblar.")
    game.balance -= hand.bet
    hand.bet *= 2
    hand.doubled = True
    hand.cards.append(draw(game))
    hand.stood = True
    advance_hand(game)
    return public_state(game)


@app.post("/games/{game_id}/split")
def split(game_id: str):
    game = get_game(game_id)
    require_active(game)
    hand = game.hands[game.active_hand]

    if game.split_used or len(game.hands) != 1:
        raise HTTPException(status_code=409, detail="Esta versión permite dividir una sola pareja por partida.")
    if len(hand.cards) != 2 or card_rank(hand.cards[0]) != card_rank(hand.cards[1]):
        raise HTTPException(status_code=409, detail="Necesitas dos cartas del mismo valor para dividir.")
    if game.balance < hand.bet:
        raise HTTPException(status_code=409, detail="Saldo insuficiente para dividir.")

    game.balance -= hand.bet
    second_card = hand.cards.pop()
    second_hand = Hand(cards=[second_card], bet=hand.bet)
    hand.cards.append(draw(game))
    second_hand.cards.append(draw(game))
    game.hands.append(second_hand)
    game.split_used = True
    game.active_hand = 0
    return public_state(game)


@app.post("/games/{game_id}/finish")
def finish_game(game_id: str):
    """Abandon the current game; the already-placed bet is not refunded."""
    game = get_game(game_id)
    require_active(game)
    game.status = "abandoned"
    game.result = {"outcome": "abandoned", "message": "Partida finalizada por el cliente; la apuesta no se devuelve."}
    return public_state(game, reveal_dealer=True)


