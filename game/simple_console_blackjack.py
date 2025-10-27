# simple_console_blackjack.py
import logic  # Import logic.py from the same directory

def print_state(state):
    dealer_display = ", ".join(map(str, state.dealer.cards[:-1])) + "+ [Hidden]" if len(state.dealer.cards) > 1 else ", ".join(map(str, state.dealer.cards))
    print("\nDealer's Hand:", dealer_display)
    print("Player's Hand:", ", ".join(map(str, state.player.cards)))
    print(state.message)

def play_console():
    # Initialize game state with a default bet
    state = logic.GameState()
    state.current_bet = 50  # Default bet to start the game
    state = logic.start_game(state)
    print("=== Welcome to Blackjack ===")
    print_state(state)

    while state.status in ["playing", "split_playing"]:  # Continue until round is resolved
        move = input("\n(H)it or (S)tand? ").lower().strip()
        if move.startswith("h"):
            state = logic.player_hit(state)
        elif move.startswith("s"):
            state = logic.player_stand(state)
        else:
            print("Invalid choice. Please enter 'h' or 's'.")
            continue
        print_state(state)
        if "bust" in state.status or "waiting_for_bet" in state.status:
            break

    # Reveal dealer's full hand and final result
    print("\nFinal Hands:")
    print("Dealer:", ", ".join(map(str, state.dealer.cards)))
    print("Player:", ", ".join(map(str, state.player.cards)))
    print(state.message)

if __name__ == "__main__":
    play_console()