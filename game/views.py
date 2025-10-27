import pickle
import base64
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from .logic import (
    GameState,
    start_game,
    player_hit,
    player_stand,
    player_double_down,
    player_split,
    place_bet,
)

SESSION_KEY = "bj_state"

#Saves gameState as a byte string with the SESSION_KEY. 
def _save_state(request, state: GameState):
    pickled = pickle.dumps(state)
    encoded = base64.b64encode(pickled).decode('utf-8')
    request.session[SESSION_KEY] = encoded
    request.session.modified = True

#Check SESSION_KEY to see if a session exists. Will load gameState from it if it does. 
def _load_state(request) -> GameState | None:
    data = request.session.get(SESSION_KEY)
    if not data:
        return None
    try:
        decoded = base64.b64decode(data)
        return pickle.loads(decoded)
    except Exception:
        return None

#HTML main page. Loads web applications and elements. 
def index(request):
    return render(request, "game/index.html")

#Calls start_game() from logic.py. Checks if dealer has blackjack. Ensure player places a bet first.
@require_POST
def new_game(request):
    state = _load_state(request)
    if not state or state.current_bet == 0:
        return JsonResponse({"error": "Place a bet first"}, status=400)
    state = start_game(state)
    _save_state(request, state)

    # Determine dealer cards payload
    dealer_cards = [str(c) for c in state.dealer.cards] if state.dealer.is_blackjack() else [str(state.dealer.cards[0]), "Hidden"] if state.dealer.cards else []

    return JsonResponse({
        "message": state.message,
        "bankroll": state.bankroll,
        "status": state.status,
        "hands": [[str(c) for c in state.player.cards]],
        "active": 0,
        "dealer": dealer_cards,
    })

#Calls player_hit(). Updates gameState with updated player hand/ 
@require_POST
def hit(request):
    state = _load_state(request)
    if not state:
        return JsonResponse({"error": "No game in progress"}, status=400)

    state = player_hit(state)
    _save_state(request, state)

    hands_payload = [[str(c) for c in h.cards] for h in state.hands] if state.hands else [[str(c) for c in state.player.cards]]
    dealer_payload = [str(state.dealer.cards[0]), "Hidden"] if state.status in ("playing", "split_playing") and len(state.dealer.cards) >= 1 else [str(c) for c in state.dealer.cards]

    return JsonResponse({
        "message": state.message,
        "bankroll": state.bankroll,
        "status": state.status,
        "hands": hands_payload,
        "active": state.active_hand_index,
        "dealer": dealer_payload,
    })

#Calls player_stand. Ends player's turn and goes to dealer's turn. 
@require_POST
def stand(request):
    state = _load_state(request)
    if not state:
        return JsonResponse({"error": "No game in progress"}, status=400)
    state = player_stand(state)
    _save_state(request, state)

    return JsonResponse({
        "message": state.message,
        "bankroll": state.bankroll,
        "status": state.status,
        "hands": [[str(c) for c in h.cards] for h in state.hands] if state.hands else [ [str(c) for c in state.player.cards] ],
        "active": state.active_hand_index,
        "dealer": [str(c) for c in state.dealer.cards],
    })

#Calls place_bet. If bet is valid, calls start_game() to start the turn. 
@require_POST
def bet(request):
    import json
    state = _load_state(request) or GameState()
    data = json.loads(request.body or '{}')
    amount = data.get("amount", 0)
    state = place_bet(state, amount)
    _save_state(request, state)
    
    #If bet is successful, start the game immediately
    if state.status == "playing":
        state = start_game(state)
        _save_state(request, state)
        dealer_cards = [str(state.dealer.cards[0]), "Hidden"] if state.dealer.cards else []
        return JsonResponse({
            "message": state.message,
            "bankroll": state.bankroll,
            "status": state.status,
            "hands": [[str(c) for c in state.player.cards]],
            "active": 0,
            "dealer": dealer_cards,
        })
    
    return JsonResponse({
        "message": state.message,
        "bankroll": state.bankroll,
        "status": state.status,
    })

#Calls player_double_down(). Double's the player's bet and draws one card. 
@require_POST
def double(request):
    state = _load_state(request)
    if not state:
        return JsonResponse({"error": "No game in progress"}, status=400)

    state = player_double_down(state)
    _save_state(request, state)

    hands_payload = [[str(c) for c in h.cards] for h in state.hands] if state.hands else [[str(c) for c in state.player.cards]]
    dealer_payload = [str(state.dealer.cards[0]), "Hidden"] if state.status in ("playing", "split_playing") and len(state.dealer.cards) >= 1 else [str(c) for c in state.dealer.cards]

    return JsonResponse({
        "message": state.message,
        "bankroll": state.bankroll,
        "status": state.status,
        "hands": hands_payload,
        "active": state.active_hand_index,
        "dealer": dealer_payload,
    })

#Calls player_split. Allows player to split if cards are the same rank. 
@require_POST
def split(request):
    state = _load_state(request)
    if not state:
        return JsonResponse({"error": "No game in progress"}, status=400)
    state = player_split(state)
    _save_state(request, state)
    return JsonResponse({
        "message": state.message,
        "bankroll": state.bankroll,
        "status": state.status,
        "hands": [[str(c) for c in h.cards] for h in state.hands],
        "active": state.active_hand_index,
        "dealer": [str(state.dealer.cards[0]), "Hidden"] if state.dealer.cards else [],
    })

#Reset button. Resets session by deleteing the SESSION_KEY and setting bankroll back to 1000. Sets status to waiting_for_bet.  
@require_POST
def reset_game(request):
    # Clear the session data
    if SESSION_KEY in request.session:
        del request.session[SESSION_KEY]
    # Reset bankroll to initial value
    request.session['bankroll'] = 1000
    request.session.modified = True
    return JsonResponse({"message": "Game reset successfully", "bankroll": 1000, "status": "waiting_for_bet"})