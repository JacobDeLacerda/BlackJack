import streamlit as st
import random
import time # Keep for potential subtle delays if desired, but avoid blocking sleeps
import os # Not needed for screen clearing anymore

# --- Constants and Styling ---
# Use emojis for suits for better visuals
SUITS = {"Hearts": "♥️", "Diamonds": "♦️", "Clubs": "♣️", "Spades": "♠️"}
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
CARD_BACK = "CARD_BACK.png" # Placeholder, we'll use text "[Hidden]" for simplicity first

# --- Core Game Logic Classes (Slightly Modified for Display) ---

class Card:
    """Represents a standard playing card."""
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        if rank in ("J", "Q", "K"):
            self.value = 10
        elif rank == "A":
            self.value = 11 # Ace initially counts as 11
        else:
            self.value = int(rank)

    def __str__(self):
        # Returns a visually appealing string representation
        return f"{self.rank}{SUITS[self.suit]}"

class Deck:
    """Represents a deck of cards."""
    def __init__(self):
        self.cards = [Card(suit, rank) for suit in SUITS for rank in RANKS]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self):
        if not self.cards:
            # In a real scenario, might reshuffle or use multiple decks
            st.warning("Deck is empty! Reshuffling a new one.")
            self.cards = [Card(suit, rank) for suit in SUITS for rank in RANKS]
            self.shuffle()
        return self.cards.pop() if self.cards else None

class Hand:
    """Represents a hand of cards."""
    def __init__(self):
        self.cards = []
        # No need to track value/aces here, calculate dynamically
        # self.value = 0
        # self.aces = 0

    def add_card(self, card):
        if card:
            self.cards.append(card)

    # Removed adjust_for_ace, calculate_hand_value does this
    # Removed __str__, we'll format display elsewhere

# --- Helper Functions ---

def calculate_hand_value(hand):
    """Calculates the value of a hand, adjusting for Aces."""
    value = 0
    aces = 0
    for card in hand.cards:
        value += card.value
        if card.rank == 'A':
            aces += 1
    # Adjust for Aces: If value > 21 and there's an Ace counted as 11, count it as 1
    while value > 21 and aces > 0:
        value -= 10
        aces -= 1
    return value

def format_cards(hand, hide_one=False):
    """Formats cards in a hand for display, optionally hiding the first card."""
    if not hand or not hand.cards:
        return "*No cards yet*"
    if hide_one and len(hand.cards) > 0:
        # Using Markdown for simple styling
        return f"`{str(hand.cards[0])}` `[Hidden]`"
    else:
        # Join card strings with spaces, wrapped in backticks for monospace look
        return " ".join([f"`{str(card)}`" for card in hand.cards])

# --- Streamlit UI and Game Flow Functions ---

def initialize_game():
    """Sets up the initial game state in st.session_state."""
    if 'game_state' not in st.session_state:
        st.session_state.game_state = 'HOME' # Possible states: HOME, BETTING, PLAYER_TURN, DEALER_TURN, SHOWDOWN, GAME_OVER
        st.session_state.player_money = 500.00
        st.session_state.dealer_money = 5000000.00 # Casino always has more ;)
        st.session_state.deck = Deck()
        st.session_state.player_hand = Hand()
        st.session_state.dealer_hand = Hand()
        st.session_state.bet = 0.00
        st.session_state.message = "" # For status updates (e.g., "Player busts!")
        st.session_state.round_over = False
        st.session_state.show_dealer_card = False # Whether dealer's hidden card is revealed

def display_home_screen():
    """Shows the initial welcome screen and Play/Quit buttons."""
    st.title("♠️ ♥️ Streamlit Blackjack ♦️ ♣️")
    st.markdown(r"""
 ____  _            _       _            _    
| __ )| | __ _  ___| | __  | | __ _  ___| | __
|  _ \| |/ _` |/ __| |/ /  | |/ _` |/ __| |/ /
| |_) | | (_| | (__|   < |_| | (_| | (__|   < 
|____/|_|\__,_|\___|_|\_\___/ \__,_|\___|_|\_\
    
 """)
    st.subheader("Welcome to the Table!")

    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if st.button("Play Game", key="play_home", type="primary", use_container_width=True):
            st.session_state.game_state = 'BETTING'
            st.rerun() # Rerun to show the betting screen

        # Quit functionality is implicit by closing the browser tab in Streamlit
        # We can add a message if needed.
        # if st.button("Quit", key="quit_home", use_container_width=True):
        #     st.info("Thanks for playing! You can close the browser tab.")
        #     st.stop() # Stop execution


def display_betting_screen():
    """Shows the betting interface."""
    st.header("Place Your Bet")

    max_bet = st.session_state.player_money
    if max_bet <= 0:
        st.session_state.game_state = 'GAME_OVER'
        st.rerun()

    # Display money
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Your Money", f"${st.session_state.player_money:,.2f}")
    with col2:
        st.metric("Casino Money", f"${st.session_state.dealer_money:,.2f}")

    # Bet input
    bet_amount = st.number_input(
        f"Enter your bet (Min: $0.01, Max: ${max_bet:,.2f})",
        min_value=0.01,
        max_value=float(max_bet), # Ensure max_value is float
        value=min(10.0, max_bet) if max_bet >= 10.0 else max_bet, # Sensible default
        step=1.0,
        format="%.2f",
        key="bet_input"
    )

    if st.button("Place Bet & Deal", key="place_bet", type="primary"):
        if 0.01 <= bet_amount <= max_bet:
            st.session_state.bet = bet_amount
            st.session_state.game_state = 'PLAYER_TURN'
            st.session_state.message = "" # Clear previous messages
            st.session_state.round_over = False
            st.session_state.show_dealer_card = False

            # Reset hands and deal
            st.session_state.deck = Deck() # Fresh deck each round
            st.session_state.player_hand = Hand()
            st.session_state.dealer_hand = Hand()
            for _ in range(2):
                st.session_state.player_hand.add_card(st.session_state.deck.deal())
                st.session_state.dealer_hand.add_card(st.session_state.deck.deal())

            # Check for immediate Blackjack
            player_value = calculate_hand_value(st.session_state.player_hand)
            dealer_value = calculate_hand_value(st.session_state.dealer_hand) # Check dealer for display later
            if player_value == 21:
                 st.session_state.message = "Blackjack! 🎉"
                 # If dealer also has BJ, it's a push, otherwise player wins 1.5x
                 # We'll handle this full logic in the dealer's turn / showdown for simplicity
                 st.session_state.game_state = 'DEALER_TURN' # Go straight to dealer reveal

            st.rerun()
        else:
            st.error(f"Invalid bet amount. Please bet between $0.01 and ${max_bet:,.2f}.")

def display_game_state_ui():
    """Displays the main game UI: money, bet, hands, action buttons."""
    st.header("Blackjack Round")

    # Display money and current bet
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Your Money", f"${st.session_state.player_money:,.2f}")
    with col2:
        st.metric("Casino Money", f"${st.session_state.dealer_money:,.2f}")
    with col3:
        st.metric("Current Bet", f"${st.session_state.bet:,.2f}")

    st.divider()

    # Display hands
    col_player, col_dealer = st.columns(2)
    player_value = calculate_hand_value(st.session_state.player_hand)
    dealer_value_shown = calculate_hand_value(st.session_state.dealer_hand) if st.session_state.show_dealer_card else st.session_state.dealer_hand.cards[0].value if st.session_state.dealer_hand.cards else 0

    with col_player:
        st.subheader("Your Hand")
        st.markdown(format_cards(st.session_state.player_hand), unsafe_allow_html=True)
        st.subheader(f"Value: {player_value}")

    with col_dealer:
        st.subheader("Dealer's Hand")
        st.markdown(format_cards(st.session_state.dealer_hand, hide_one=(not st.session_state.show_dealer_card)), unsafe_allow_html=True)
        if st.session_state.show_dealer_card:
            st.subheader(f"Value: {dealer_value_shown}")
        else:
             st.subheader(f"Value: {dealer_value_shown} + ?") # Show value of visible card only

    st.divider()

    # Display messages (like "Bust!")
    if st.session_state.message:
        if "win" in st.session_state.message.lower() or "blackjack" in st.session_state.message.lower():
             st.success(st.session_state.message)
        elif "lose" in st.session_state.message.lower() or "bust" in st.session_state.message.lower():
            st.error(st.session_state.message)
        else: # Push
            st.info(st.session_state.message)

    # --- Action Buttons ---
    if st.session_state.game_state == 'PLAYER_TURN':
        st.subheader("Your Action")
        col_hit, col_stand = st.columns(2)
        with col_hit:
            if st.button("Hit", key="hit", type="primary", use_container_width=True):
                st.session_state.player_hand.add_card(st.session_state.deck.deal())
                player_value = calculate_hand_value(st.session_state.player_hand)
                if player_value > 21:
                    st.session_state.message = "You Busted! 💥"
                    st.session_state.game_state = 'SHOWDOWN' # Go to showdown to process loss
                    st.session_state.round_over = True
                st.rerun()

        with col_stand:
            if st.button("Stand", key="stand", use_container_width=True):
                st.session_state.game_state = 'DEALER_TURN'
                st.session_state.message = "You stand. Dealer's turn..."
                st.rerun()

    elif st.session_state.round_over:
         st.subheader("Round Over")
         if st.button("Play Again?", key="play_again", type="primary"):
             # Reset for next round, keep money changes
             st.session_state.game_state = 'BETTING'
             st.session_state.message = ""
             st.session_state.bet = 0.0
             st.session_state.round_over = False
             st.session_state.show_dealer_card = False
             # Hands and deck reset happens during betting confirmation
             st.rerun()
         # Add a quit option maybe?
         # if st.button("Quit Game", key="quit_round"):
         #     st.session_state.game_state = 'HOME' # Go back to home
         #     # Optionally reset money? Or keep score?
         #     # initialize_game() # Full reset if desired
         #     st.rerun()


def process_dealer_turn():
    """Handles the dealer's logic (hitting until 17+)"""
    st.session_state.show_dealer_card = True # Reveal hidden card
    dealer_hand = st.session_state.dealer_hand
    dealer_value = calculate_hand_value(dealer_hand)

    # Check for player Blackjack win condition first (if player stood on 21)
    player_value = calculate_hand_value(st.session_state.player_hand)
    if player_value == 21 and len(st.session_state.player_hand.cards) == 2 and dealer_value != 21:
         st.session_state.message = "Blackjack! You win 1.5x your bet! 🎉"
         st.session_state.game_state = 'SHOWDOWN'
         st.session_state.round_over = True
         st.rerun() # Rerun to show final state before asking "Play Again"

    # Dealer hits based on rules (typically hit on soft 17, stand on hard 17+)
    # Simple rule: Hit if total < 17
    while calculate_hand_value(st.session_state.dealer_hand) < 17:
        # No sleep needed, Streamlit will rerender after state changes
        st.session_state.dealer_hand.add_card(st.session_state.deck.deal())
        # No need to display intermediate hits, just the final result

    # Final dealer value
    dealer_value = calculate_hand_value(st.session_state.dealer_hand)
    if dealer_value > 21:
        st.session_state.message = "Dealer Busts! You Win! ✅"
    # Winner determination logic moved to process_showdown

    st.session_state.game_state = 'SHOWDOWN'
    st.session_state.round_over = True
    st.rerun() # Rerun to trigger showdown processing

def process_showdown():
    """Determines the winner and updates money after both turns are complete."""
    player_value = calculate_hand_value(st.session_state.player_hand)
    dealer_value = calculate_hand_value(st.session_state.dealer_hand)
    bet = st.session_state.bet

    # Player bust condition was handled during player turn, just process money
    if player_value > 21:
        # Message already set to "You Busted!"
        st.session_state.player_money -= bet
        st.session_state.dealer_money += bet
        st.session_state.message += f" You lose ${bet:,.2f}." # Append loss info

    # Dealer bust condition
    elif dealer_value > 21:
        # Message already set to "Dealer Busts!"
        st.session_state.player_money += bet
        st.session_state.dealer_money -= bet
        st.session_state.message += f" You win ${bet:,.2f}! 🎉"

    # Blackjack checks (handle payout and pushes)
    elif player_value == 21 and len(st.session_state.player_hand.cards) == 2:
        if dealer_value == 21 and len(st.session_state.dealer_hand.cards) == 2:
             st.session_state.message = "Push! Both have Blackjack. 🤝"
             # No money change
        else:
             # Player Blackjack wins 1.5x (often 3:2)
             win_amount = bet * 1.5
             st.session_state.player_money += win_amount
             st.session_state.dealer_money -= win_amount
             st.session_state.message = f"Blackjack! You win ${win_amount:,.2f}! 🎉"

    elif dealer_value == 21 and len(st.session_state.dealer_hand.cards) == 2:
        # Dealer has Blackjack, player doesn't
        st.session_state.player_money -= bet
        st.session_state.dealer_money += bet
        st.session_state.message = f"Dealer Blackjack! You lose ${bet:,.2f}. 😞"

    # Standard comparison
    elif player_value > dealer_value:
        st.session_state.player_money += bet
        st.session_state.dealer_money -= bet
        st.session_state.message = f"You Win! ✅ You score {player_value} vs Dealer's {dealer_value}. You win ${bet:,.2f}."
    elif dealer_value > player_value:
        st.session_state.player_money -= bet
        st.session_state.dealer_money += bet
        st.session_state.message = f"You Lose! ❌ Dealer scores {dealer_value} vs Your {player_value}. You lose ${bet:,.2f}."
    else: # Push
        st.session_state.message = f"Push! 🤝 Both score {player_value}."
        # No money change

    # Check for game over conditions
    if st.session_state.player_money <= 0:
        st.session_state.game_state = 'GAME_OVER'
        st.session_state.message = "You've run out of money!"
    elif st.session_state.dealer_money <= 0:
         st.session_state.game_state = 'GAME_OVER'
         st.session_state.message = "You've bankrupted the casino!"

    st.session_state.round_over = True
    # Don't rerun here, let display_game_state_ui handle showing the final state and "Play Again" button

def display_game_over_screen():
    """Shows the appropriate game over message."""
    st.header("Game Over")

    if st.session_state.player_money <= 0:
        st.error("Too Bad! No money left. 💸")
        st.markdown(r"""
 ____            _        
| __ ) _ __ ___ | | _____ 
|  _ \| '__/ _ \| |/ / _ \
| |_) | | | (_) |   <  __/
|____/|_|  \___/|_|\_\___|
                          
""")
    elif st.session_state.dealer_money <= 0:
        st.balloons()
        st.success("Congratulations! You Bankrupted the Casino! 🏆")
        st.markdown(r"""
 ____              _                     _   _ 
| __ )  __ _ _ __ | | ___ __ _   _ _ __ | |_| |
|  _ \ / _` | '_ \| |/ / '__| | | | '_ \| __| |
| |_) | (_| | | | |   <| |  | |_| | |_) | |_|_|
|____/ \__,_|_| |_|_|\_\_|   \__,_| .__/ \__(_)
                                  |_|  

""")

    if st.button("Start New Game", key="new_game"):
        # Completely reset the state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        initialize_game() # Re-initialize
        st.rerun()

# --- Main App Logic ---

# Initialize state variables
initialize_game()

# Control flow based on game state
if st.session_state.game_state == 'HOME':
    display_home_screen()

elif st.session_state.game_state == 'BETTING':
    display_betting_screen()

elif st.session_state.game_state in ['PLAYER_TURN', 'DEALER_TURN', 'SHOWDOWN']:
    # Display the main game UI first
    display_game_state_ui()

    # Process state-specific logic *after* displaying the current state
    if st.session_state.game_state == 'DEALER_TURN':
        # Use a placeholder to simulate dealer thinking time if desired
        # with st.spinner("Dealer playing..."):
        #     time.sleep(1) # Short delay, but be careful with sleeps in Streamlit
        process_dealer_turn() # This will change state to SHOWDOWN and rerun

    elif st.session_state.game_state == 'SHOWDOWN':
        process_showdown() # This calculates results, sets messages, might change state to GAME_OVER
        # After processing, display_game_state_ui will be called again on the next rerun,
        # showing the final hands, message, and the "Play Again" button because round_over is True.

elif st.session_state.game_state == 'GAME_OVER':
    display_game_over_screen()