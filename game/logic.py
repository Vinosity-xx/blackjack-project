
import random
from dataclasses import dataclass, field
from typing import List, Tuple

#Create list of all cards and suits
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
SUITS = ["♠", "♥", "♦", "♣"]

#Simple card class with rank and suit attributes
@dataclass
class Card:
    rank: str
    suit: str

    def __repr__(self):
        return f"{self.rank}{self.suit}"

#Define face card/ace value
def card_value(rank: str) -> int:
    if rank in ("J", "Q", "K"):
        return 10
    if rank == "A":
        return 11 
    return int(rank)

#Simple deck class; Initalized deck with shuffling and draws cards from top of the deck and removes it from deck. When deck runs out of cards, re-shuffles and continues. 
@dataclass
class Deck:
    cards: List[Card] = field(default_factory=list)

    def __post_init__(self):
        if not self.cards:
            self.cards = [Card(rank, suit) for suit in SUITS for rank in RANKS]
            self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self) -> Card:
        if not self.cards:
            self.__post_init__()  # reshuffle new deck if exhausted
            random.shuffle(self.cards)
        return self.cards.pop()

#Contains methods related to the player hand. Ace logic: Try to use an Ace as an 11 if it doesn't bust. If it does bust, use the Ace as a 1. 
@dataclass
class Hand:
    cards: List[Card] = field(default_factory=list)

    def add(self, card: Card):
        self.cards.append(card)

    def values(self) -> Tuple[int, int]:
        """Return (min_value, max_value) where max_value tries to use one ace as 11 when possible."""
        total = 0
        aces = 0
        for c in self.cards:
            if c.rank == "A":
                aces += 1
            else:
                total += card_value(c.rank)
        min_val = total + aces * 1
        max_val = min_val
        if aces > 0 and min_val + 10 <= 21:
            max_val = min_val + 10
        return (min_val, max_val)

    def best_value(self) -> int:
        min_v, max_v = self.values()
        return max_v if max_v <= 21 else min_v

    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.best_value() == 21

    def is_bust(self) -> bool:
        return self.best_value() > 21

    def __repr__(self):
        return ", ".join(map(str, self.cards))

#All attributes neccesary for game flow. Keeps track of deck, player/dealer hands, bankroll, and bet size. Most importantly, it keep tracks of the game 'status', which controls the game flow and
#determines which state of the game the user is in and other attributes.  
@dataclass
class GameState:
    deck: Deck = field(default_factory=Deck)
    player: Hand = field(default_factory=Hand)
    dealer: Hand = field(default_factory=Hand)
    status: str = "waiting_for_bet"  # can be "playing", "split_playing", etc.
    message: str = ""
    bankroll: int = 1000
    current_bet: int = 0
    hands: list = field(default_factory=list)  # for split hands
    active_hand_index: int = 0

# ---------------------------------------
# Core Gameplay Logic
# ---------------------------------------

#Function that allows user to place a bet (checks that bet can be made without going over the player's bankroll) and updates gameState object accordingly. 
def place_bet(state: GameState, amount: int) -> GameState:
    if amount <= 0:
        state.message = "Bet must be greater than 0."
        return state
    if amount > state.bankroll:
        state.message = "Insufficient funds to place that bet."
        return state

    state.current_bet = amount
    state.bankroll -= amount
    state.message = f"Bet placed: ${amount}"
    state.status = "playing"  #Ready for deal
    return state

#Checks if gameState objects exists, if not, creates one. Will then deal out cards to dealer and player in order and update gameState object with those values. 
def start_game(state: GameState | None = None) -> GameState:
    """Initialize a new game by dealing cards to player and dealer."""
    g = state or GameState()

    if g.current_bet == 0:
        g.message = "Please place a bet first."
        g.status = "waiting_for_bet"
        return g

    g.player = Hand()
    g.dealer = Hand()
    g.deck.shuffle()
    g.message = ""

    #Deal initial cards
    g.player.add(g.deck.draw())
    g.dealer.add(g.deck.draw())
    g.player.add(g.deck.draw())
    g.dealer.add(g.deck.draw())

    #Check blackjacks (21 on initial 2 cards)
    if g.player.is_blackjack():
        if g.dealer.is_blackjack():
            g.message = "Push (both blackjack)."
            g.bankroll += g.current_bet  # refund
        else:
            g.message = "Player has Blackjack! You win 1.5x!"
            g.bankroll += int(g.current_bet * 2.5)
        g.current_bet = 0
        g.status = "waiting_for_bet"
    elif g.dealer.is_blackjack():
        g.message = "Dealer has Blackjack."
        g.current_bet = 0
        g.status = "waiting_for_bet"
    else:
        g.status = "playing"

    return g

#Adds a card to the player's current hand and checks for a player bust. Updates gameState. 
def player_hit(state: GameState) -> GameState:
    if state.status not in ("playing", "split_playing"):
        return state

    state.player.add(state.deck.draw())

    if state.player.is_bust():
        if state.status == "split_playing" and state.hands:
            state.message = f"Hand {state.active_hand_index + 1} busts with {state.player.best_value()}."
            state = advance_to_next_hand(state)
            return state
        else:
            state.status = "player_bust"
            state.message = f"Player busts with {state.player.best_value()}."
            state.current_bet = 0
            return state

    return state

#Dealer play logic. Dealer must stand on 17 (Standard for most casinos). Checks if dealer has won, lost, or busts. Updates bankroll in gameState accordingly. 
#Since this will always be the last turn, resets status to wait for player bet. 
def dealer_play(state: GameState, hit_soft_17: bool = False) -> GameState:
    while True:
        min_v, max_v = state.dealer.values()
        best = state.dealer.best_value()
        is_soft_17 = (min_v + 10 == 17) if any(c.rank == "A" for c in state.dealer.cards) else False
        if best < 17 or (is_soft_17 and hit_soft_17):
            state.dealer.add(state.deck.draw())
            if state.dealer.is_bust():
                state.status = "dealer_bust"
                state.message = f"Dealer busts with {state.dealer.best_value()}!"
                state.bankroll += state.current_bet * 2
                state.current_bet = 0
                return state
            continue
        break

    p_best = state.player.best_value()
    d_best = state.dealer.best_value()

    if d_best > 21:
        state.message = "Dealer busts!"
        state.bankroll += state.current_bet * 2
    elif d_best > p_best:
        state.message = f"Dealer wins ({d_best} vs {p_best})"
    elif d_best < p_best:
        state.message = f"Player wins ({p_best} vs {d_best})"
        state.bankroll += state.current_bet * 2
    else:
        state.message = f"Push ({p_best}). Bet returned."
        state.bankroll += state.current_bet

    state.status = "waiting_for_bet"
    state.current_bet = 0
    return state

#Player stands, keeps current value and let's the dealer play. 
def player_stand(state: GameState) -> GameState:
    if state.status.startswith("split"):
        state = advance_to_next_hand(state)
        return state
    else:
        state = dealer_play(state)
        return state

#Simple double down logic. Checks balance to ensure player has enough to double down. Calls player_stand since player is only allowed to draw one card. 
def player_double_down(state: GameState) -> GameState:
    if state.bankroll < state.current_bet:
        state.message = "Not enough funds to double down."
        return state
    if len(state.player.cards) != 2:
        state.message = "Can only double down on the first move of a hand."
        return state

    state.bankroll -= state.current_bet
    state.current_bet *= 2
    state.player.add(state.deck.draw())

    if state.player.is_bust():
        if state.status == "split_playing" and state.hands:
            state.message = f"Hand {state.active_hand_index + 1} busts after double down."
            state = advance_to_next_hand(state)
            return state
        else:
            state.status = "player_bust"
            state.message = f"Player busts with {state.player.best_value()} after doubling down."
            state.current_bet = 0
            return state

    if state.status == "split_playing" and state.hands:
        state.message = "Doubled and standing on current hand."
        state = advance_to_next_hand(state)
        return state
    else:
        state = player_stand(state)
        #state.message = "Player doubled down and stands."
        return state

#Player split logic - Player can only split if the cards are the rank (this differs based on casino). If player does split, initalize a second hand with the second card. Sets active hand to hand 1.
#Once that hand is concluded, switch to hand 2. Once both hands are done, dealer play starts. 
def player_split(state: GameState) -> GameState:
    if len(state.player.cards) != 2 or state.player.cards[0].rank != state.player.cards[1].rank:
        state.message = "Cannot split unless you have a pair."
        return state
    if state.bankroll < state.current_bet:
        state.message = "Not enough funds to split."
        return state

    state.bankroll -= state.current_bet
    card1, card2 = state.player.cards
    hand1 = Hand([card1, state.deck.draw()])
    hand2 = Hand([card2, state.deck.draw()])
    state.hands = [hand1, hand2]
    state.active_hand_index = 0
    state.player = state.hands[state.active_hand_index]
    state.message = "Hand split — playing Hand 1."
    state.status = "split_playing"
    return state

#Used for when a player splits their hand. Transistions to second hand the player has. 
def advance_to_next_hand(state: GameState) -> GameState:
    if not state.hands:
        return state

    state.active_hand_index += 1

    if state.active_hand_index < len(state.hands):
        state.player = state.hands[state.active_hand_index]
        state.message = f"Now playing Hand {state.active_hand_index + 1}."
        state.status = "split_playing"
        return state

    # All hands done. Dealer plays and compare results
    results = []
    dealer_played = False
    for i, hand in enumerate(state.hands, start=1):
        state.player = hand
        if hand.is_bust():
            results.append(f"Hand {i}: Bust ({hand.best_value()}) – Lose")
            continue
        if not dealer_played:
            state = dealer_play(state)
            dealer_played = True
        p_best = hand.best_value()
        d_best = state.dealer.best_value()
        if d_best > 21:
            results.append(f"Hand {i}: Dealer busts with {d_best}! Player wins ({p_best})")
            state.bankroll += state.current_bet * 2
        elif d_best > p_best:
            results.append(f"Hand {i}: Dealer wins ({d_best} vs {p_best})")
        elif d_best < p_best:
            results.append(f"Hand {i}: Player wins ({p_best} vs {d_best})")
            state.bankroll += state.current_bet * 2
        else:
            results.append(f"Hand {i}: Push ({p_best})")
            state.bankroll += state.current_bet

    state.message = " | ".join(results)
    state.status = "waiting_for_bet"
    state.hands = []
    state.active_hand_index = 0
    state.player = Hand()
    state.current_bet = 0
    return state
