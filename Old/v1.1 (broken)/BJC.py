import streamlit as st
import random
import math

# --- Constants and Styling ---
SUITS = {"Hearts": "♥️", "Diamonds": "♦️", "Clubs": "♣️", "Spades": "♠️"}
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
NUM_DECKS = 4 # Use multiple decks like in casinos
RESHUFFLE_THRESHOLD = 0.25 # Reshuffle when 25% or fewer cards remain

# --- Core Game Logic Classes (Modified for Multiple Decks) ---

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
    """Represents a collection of playing cards, potentially multiple decks."""
    def __init__(self, num_decks=1):
        self.num_decks = num_decks
        self.cards = []
        self.reshuffle_point = math.floor(52 * num_decks * RESHUFFLE_THRESHOLD)
        self.build_and_shuffle()

    def build_and_shuffle(self):
        self.cards = [Card(suit, rank) for _ in range(self.num_decks) for suit in SUITS for rank in RANKS]
        random.shuffle(self.cards)
        st.session_state.reshuffled_message = "Deck reshuffled!" # Signal reshuffle

    def needs_reshuffle(self):
        return len(self.cards) <= self.reshuffle_point

    def deal(self):
        if self.needs_reshuffle():
            self.build_and_shuffle()
        # Check again in case build failed or threshold is weirdly low
        if not self.cards:
            st.error("Error: Deck is unexpectedly empty even after reshuffle attempt.")
            return None # Should not happen with proper reshuffle logic
        return self.cards.pop()

class Hand:
    """Represents a hand of cards."""
    def __init__(self):
        self.cards = []

    def add_card(self, card):
        if card:
            self.cards.append(card)

# --- Helper Functions ---

def calculate_hand_value(hand):
    """Calculates the value of a hand, adjusting for Aces."""
    value = 0
    aces = 0
    if not hand or not hand.cards:
        return 0
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
    # Only initialize if not already done (persists across reruns)
    if 'game_state' not in st.session_state:
        st.session_state.game_state = 'HOME' # HOME, BETTING, PLAYER_TURN, DEALER_TURN, SHOWDOWN, GAME_OVER
        st.session_state.player_money = 500.00
        st.session_state.dealer_money = 5000000.00
        st.session_state.deck = Deck(num_decks=NUM_DECKS)
        st.session_state.player_hand = Hand()
        st.session_state.dealer_hand = Hand()
        st.session_state.bet = 0.00
        st.session_state.message = "" # Stores the final outcome message for the round
        st.session_state.round_over = False
        st.session_state.show_dealer_card = False
        st.session_state.player_busted = False
        st.session_state.dealer_busted = False
        st.session_state.player_blackjack = False
        st.session_state.dealer_blackjack = False
        st.session_state.reshuffled_message = "" # To notify user about reshuffles

def display_home_screen():
    """Shows the initial welcome screen and Play button."""
    st.title("♠️ ♥️ Streamlit Blackjack ♦️ ♣️")
    # Removed ASCII Art
    st.subheader("Welcome to the Table!")
    st.markdown(f"Using **{NUM_DECKS}** decks. Reshuffling when **{st.session_state.deck.reshuffle_point}** cards or fewer remain.")

    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if st.button("Play Game", key="play_home", type="primary", use_container_width=True):
            # Reset relevant states for a potentially new game session
            st.session_state.player_money = 500.00
            st.session_state.dealer_money = 5000000.00
            st.session_state.deck = Deck(num_decks=NUM_DECKS) # Fresh decks
            st.session_state.game_state = 'BETTING'
            st.session_state.message = ""
            st.session_state.reshuffled_message = ""
            st.rerun()

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
        # Hide casino money if it's too large or distracting
        # st.metric("Casino Money", f"${st.session_state.dealer_money:,.2f}")
        st.metric("Casino Money", "Plenty 😉")


    # Bet input
    default_bet = min(10.0, max_bet) if max_bet >= 10.0 else max(0.01, max_bet)
    bet_amount = st.number_input(
        f"Enter your bet (Min: $0.01, Max: ${max_bet:,.2f})",
        min_value=0.01,
        max_value=float(max_bet), # Ensure max_value is float
        value=float(default_bet), # Sensible default
        step=1.0,
        format="%.2f",
        key="bet_input"
    )

    if st.button("Place Bet & Deal", key="place_bet", type="primary"):
        if 0.01 <= bet_amount <= max_bet:
            st.session_state.bet = bet_amount
            st.session_state.game_state = 'PLAYER_TURN'
            st.session_state.message = "" # Clear previous round outcome message
            st.session_state.round_over = False
            st.session_state.show_dealer_card = False
            st.session_state.player_busted = False
            st.session_state.dealer_busted = False
            st.session_state.player_blackjack = False
            st.session_state.dealer_blackjack = False

            # Check for reshuffle *before* dealing
            if st.session_state.deck.needs_reshuffle():
                 st.session_state.deck.build_and_shuffle()
            else:
                 st.session_state.reshuffled_message = "" # Clear message if no reshuffle

            # Reset hands and deal
            st.session_state.player_hand = Hand()
            st.session_state.dealer_hand = Hand()
            for _ in range(2):
                st.session_state.player_hand.add_card(st.session_state.deck.deal())
                st.session_state.dealer_hand.add_card(st.session_state.deck.deal())

            # Check for immediate Blackjacks (affects available actions)
            player_value = calculate_hand_value(st.session_state.player_hand)
            dealer_value = calculate_hand_value(st.session_state.dealer_hand)

            st.session_state.player_blackjack = (player_value == 21)
            st.session_state.dealer_blackjack = (dealer_value == 21) # Check now, even if hidden

            # If player or dealer has BJ, game goes straight to dealer's turn/showdown
            if st.session_state.player_blackjack or st.session_state.dealer_blackjack:
                 st.session_state.game_state = 'DEALER_TURN'

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
        # st.metric("Casino Money", f"${st.session_state.dealer_money:,.2f}")
         st.metric("Casino Money", "Plenty 😉")
    with col3:
        st.metric("Current Bet", f"${st.session_state.bet:,.2f}")

    # Display reshuffle message if it occurred
    if st.session_state.reshuffled_message:
        st.info(st.session_state.reshuffled_message)
        # Don't clear here, clear when next bet is placed

    st.divider()

    # Display hands using containers for better structure
    player_container = st.container()
    dealer_container = st.container()

    player_value = calculate_hand_value(st.session_state.player_hand)
    # Show dealer's visible card value, or full value if revealed
    dealer_val_display = "?"
    if st.session_state.show_dealer_card:
        dealer_val_display = str(calculate_hand_value(st.session_state.dealer_hand))
    elif st.session_state.dealer_hand and st.session_state.dealer_hand.cards:
        # Ensure dealer hand exists before accessing cards[0]
        dealer_val_display = f"{st.session_state.dealer_hand.cards[0].value} + ?"


    with player_container:
        st.subheader("Your Hand")
        st.markdown(format_cards(st.session_state.player_hand), unsafe_allow_html=True)
        st.subheader(f"Value: {player_value}")

    with dealer_container:
        st.subheader("Dealer's Hand")
        st.markdown(format_cards(st.session_state.dealer_hand, hide_one=(not st.session_state.show_dealer_card)), unsafe_allow_html=True)
        st.subheader(f"Value: {dealer_val_display}")

    st.divider()

    # Display FINAL outcome message only when round is over
    if st.session_state.round_over and st.session_state.message:
        if "win" in st.session_state.message.lower() or "blackjack!" in st.session_state.message.lower():
             st.success(st.session_state.message)
        elif "lose" in st.session_state.message.lower() or "bust" in st.session_state.message.lower():
            st.error(st.session_state.message)
        else: # Push
            st.info(st.session_state.message)

    # --- Action Buttons ---
    if st.session_state.game_state == 'PLAYER_TURN':
        st.subheader("Your Action")
        # Check if Double Down is possible
        can_double_down = (len(st.session_state.player_hand.cards) == 2) and \
                          (st.session_state.player_money >= st.session_state.bet) # Can afford to double

        cols = st.columns(3 if can_double_down else 2)

        with cols[0]:
            if st.button("Hit", key="hit", type="primary", use_container_width=True):
                st.session_state.player_hand.add_card(st.session_state.deck.deal())
                player_value = calculate_hand_value(st.session_state.player_hand)
                if player_value > 21:
                    st.session_state.player_busted = True
                    st.session_state.game_state = 'SHOWDOWN' # Go to showdown to process loss
                st.rerun()

        with cols[1]:
            if st.button("Stand", key="stand", use_container_width=True):
                st.session_state.game_state = 'DEALER_TURN'
                # st.session_state.message = "You stand. Dealer's turn..." # No intermediate messages
                st.rerun()

        if can_double_down:
            with cols[2]:
                if st.button("Double Down", key="double_down", use_container_width=True):
                    # Double the bet
                    st.session_state.player_money -= st.session_state.bet # Take the extra bet amount now
                    st.session_state.bet *= 2
                    # Deal one card
                    st.session_state.player_hand.add_card(st.session_state.deck.deal())
                    player_value = calculate_hand_value(st.session_state.player_hand)
                    if player_value > 21:
                         st.session_state.player_busted = True
                         st.session_state.game_state = 'SHOWDOWN' # Go straight to showdown if busted on double
                    else:
                         st.session_state.game_state = 'DEALER_TURN' # Otherwise, dealer plays
                    st.rerun()

    elif st.session_state.round_over:
         st.subheader("Round Over")
         if st.button("Play Next Hand?", key="play_again", type="primary"):
             # Reset for next round, keeping money changes
             st.session_state.game_state = 'BETTING'
             # Message, bet, hands, flags reset during betting confirmation
             st.rerun()


def process_dealer_turn():
    """Handles the dealer's logic (hitting until 17+) after revealing card."""
    st.session_state.show_dealer_card = True # Reveal hidden card

    # If player already busted or got Blackjack, dealer might not need to hit (or hits differently based on rules)
    # Simple Rule: Always play out dealer hand unless player busted.
    if not st.session_state.player_busted:
        dealer_hand = st.session_state.dealer_hand
        # Dealer hits based on standard rules (Hit soft 17 often, stand hard 17+)
        # Simple rule: Hit if total < 17
        while calculate_hand_value(dealer_hand) < 17:
            dealer_hand.add_card(st.session_state.deck.deal())
            # Optional: Add a tiny delay and rerun to show dealer hits one by one?
            # time.sleep(0.5) # Be cautious with sleep
            # st.rerun() # This would make the dealer turn take multiple steps

        # Check if dealer busted after hitting
        if calculate_hand_value(dealer_hand) > 21:
            st.session_state.dealer_busted = True

    # Regardless of dealer action, move to showdown to determine winner & message
    st.session_state.game_state = 'SHOWDOWN'
    st.rerun() # Rerun to trigger showdown processing and display final hands


def process_showdown():
    """Determines the winner, sets the final message, and updates money."""
    player_value = calculate_hand_value(st.session_state.player_hand)
    dealer_value = calculate_hand_value(st.session_state.dealer_hand)
    bet = st.session_state.bet
    win_amount = bet
    final_message = ""

    # --- Determine Outcome ---
    if st.session_state.player_busted:
        final_message = f"You Busted with {player_value}! You lose ${bet:,.2f}. 💥"
        st.session_state.player_money -= bet
        st.session_state.dealer_money += bet

    elif st.session_state.dealer_busted:
        final_message = f"Dealer Busts with {dealer_value}! You Win! You win ${bet:,.2f}. ✅"
        st.session_state.player_money += bet
        st.session_state.dealer_money -= bet

    elif st.session_state.player_blackjack:
        if st.session_state.dealer_blackjack:
            final_message = f"Push! Both have Blackjack. Bet returned. 🤝"
            # No money change
        else:
            # Player Blackjack wins 1.5x (3:2 payout)
            win_amount = bet * 1.5
            final_message = f"Blackjack! You win ${win_amount:,.2f}! 🎉"
            st.session_state.player_money += win_amount
            st.session_state.dealer_money -= win_amount

    elif st.session_state.dealer_blackjack:
        # Dealer has Blackjack, player doesn't (player BJ handled above)
        final_message = f"Dealer Blackjack! You lose ${bet:,.2f}. 😞"
        st.session_state.player_money -= bet
        st.session_state.dealer_money += bet

    # --- Standard Hand Comparison (No busts, no BJs) ---
    elif player_value > dealer_value:
        final_message = f"You Win! Your {player_value} beats Dealer's {dealer_value}. You win ${bet:,.2f}. ✅"
        st.session_state.player_money += bet
        st.session_state.dealer_money -= bet
    elif dealer_value > player_value:
        final_message = f"You Lose! Dealer's {dealer_value} beats Your {player_value}. You lose ${bet:,.2f}. ❌"
        st.session_state.player_money -= bet
        st.session_state.dealer_money += bet
    else: # Push
        final_message = f"Push! Both score {player_value}. Bet returned. 🤝"
        # No money change

    # --- Update state for display ---
    st.session_state.message = final_message
    st.session_state.round_over = True
    st.session_state.show_dealer_card = True # Ensure dealer card is shown at end

    # Check for game over conditions AFTER updating money
    if st.session_state.player_money <= 0:
        st.session_state.game_state = 'GAME_OVER'
        # Keep the final hand message, maybe add a game over note?
        st.session_state.message += "\n\n**Game Over: You're out of money!**"
    elif st.session_state.dealer_money <= 0:
         st.session_state.game_state = 'GAME_OVER'
         st.balloons() # Celebrate bankrupting the casino!
         st.session_state.message += "\n\n**Game Over: You bankrupted the casino!**"

    # No automatic rerun here; display_game_state_ui will show the final state
    # and the "Play Next Hand?" button based on round_over flag.

def display_game_over_screen():
    """Shows the appropriate game over message (called if state is GAME_OVER)."""
    st.header("Game Over")

    # Display the final message from the last hand first
    if st.session_state.message:
         # Re-display message using appropriate type based on win/loss
        if "win" in st.session_state.message.lower() or "blackjack!" in st.session_state.message.lower() or "bankrupted" in st.session_state.message.lower():
             st.success(st.session_state.message)
        elif "lose" in st.session_state.message.lower() or "bust" in st.session_state.message.lower() or "out of money" in st.session_state.message.lower():
            st.error(st.session_state.message)
        else: # Push on the last hand? Unlikely game over state but possible
            st.info(st.session_state.message)

    # Add specific Game Over visuals (removed ASCII)
    if st.session_state.player_money <= 0:
        st.error("Better luck next time! 💸")
    elif st.session_state.dealer_money <= 0:
        st.success("Truly Legendary! 🏆")

    if st.button("Start New Game", key="new_game", type="primary"):
        # Completely reset the state by deleting all session keys
        keys_to_delete = list(st.session_state.keys())
        for key in keys_to_delete:
            del st.session_state[key]
        # initialize_game() will be called automatically on rerun after state clear
        st.rerun()

# --- Main App Logic ---

# Set page config for wider layout potentially
st.set_page_config(layout="wide")

# Initialize state variables ONCE
initialize_game()

# --- Game State Router ---
current_state = st.session_state.game_state

if current_state == 'HOME':
    display_home_screen()

elif current_state == 'BETTING':
    display_betting_screen()

elif current_state in ['PLAYER_TURN', 'DEALER_TURN', 'SHOWDOWN']:
    # Display the main game UI. Actions/logic are embedded or called below.
    display_game_state_ui()

    # If it's dealer's turn logic time (triggered by Stand or Double Down w/o bust)
    if current_state == 'DEALER_TURN':
        # Add a slight delay visual cue if desired, but avoid blocking sleep
        # with st.spinner("Dealer playing..."):
        process_dealer_turn() # This function handles dealer logic and moves state to SHOWDOWN

    # If it's time to determine the winner (triggered by Busts or process_dealer_turn)
    elif current_state == 'SHOWDOWN':
         # Check if showdown processing is needed (e.g., if message isn't set yet)
         if not st.session_state.round_over:
             process_showdown()
         # If process_showdown resulted in GAME_OVER, rerun to display that screen
         if st.session_state.game_state == 'GAME_OVER':
             st.rerun()
         # Otherwise, display_game_state_ui already showed the results and Play Again button

elif current_state == 'GAME_OVER':
    display_game_over_screen()
