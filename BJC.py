import streamlit as st
import random

# Define suits and ranks for cards
suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

# Functions for card and hand handling
def card_to_str(card):
    """Convert a card tuple to a string."""
    return f"{card[1]} of {card[0]}"

def hand_to_str(hand):
    """Convert a hand (list of card tuples) to a string."""
    return ", ".join(card_to_str(card) for card in hand)

def calculate_hand_value(hand):
    """Calculate the total value of a hand, adjusting for aces."""
    value = 0
    aces = 0
    for card in hand:
        rank = card[1]
        if rank in ("J", "Q", "K"):
            value += 10
        elif rank == "A":
            aces += 1
            value += 11
        else:
            value += int(rank)
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

# Initialize session state
def initialize_session_state():
    """Set up initial game state."""
    if 'game_phase' not in st.session_state:
        st.session_state.game_phase = 'start'
        st.session_state.player_money = 500.00
        st.session_state.dealer_money = 5000000.00
        st.session_state.deck = []
        st.session_state.player_hand = []
        st.session_state.dealer_hand = []
        st.session_state.bet = 0.0
        st.session_state.message = ""

# Main application logic
initialize_session_state()

# Sidebar for money display, reset, and quit
with st.sidebar:
    st.header("Balances")
    st.metric("Your Money", f"${st.session_state.player_money:.2f}")
    st.metric("Casino Money", f"${st.session_state.dealer_money:.2f}")
    st.divider()
    if st.button("Reset Game"):
        st.session_state.game_phase = 'start'
        st.session_state.player_money = 500.00
        st.session_state.dealer_money = 5000000.00
        st.session_state.deck = []
        st.session_state.player_hand = []
        st.session_state.dealer_hand = []
        st.session_state.bet = 0.0
        st.session_state.message = ""
        st.rerun()
    if st.button("Quit"):
        st.session_state.game_phase = 'quit'
        st.rerun()

# Main game area
st.title("🎲 Blackjack")
st.write("Welcome to Blackjack! Beat the dealer without going over 21.")

phase = st.session_state.game_phase

if phase == 'quit':
    st.write("Thanks for playing!")
    st.stop()

elif phase == 'start':
    st.header("Start Game")
    st.info("Click 'Play' to begin.")
    if st.button("Play"):
        st.session_state.game_phase = 'betting'
        st.session_state.deck = [(suit, rank) for suit in suits for rank in ranks]
        random.shuffle(st.session_state.deck)
        st.rerun()

elif phase == 'betting':
    st.header("Place Your Bet")
    st.info("Enter your bet amount and click 'Place Bet' to start.")
    bet = st.number_input("Enter your bet", min_value=0.01, step=0.01, value=0.01)
    if st.button("Place Bet"):
        if bet > st.session_state.player_money:
            st.error("Bet exceeds balance. Place another.")
        else:
            st.session_state.bet = bet
            st.session_state.player_hand = [st.session_state.deck.pop(), st.session_state.deck.pop()]
            st.session_state.dealer_hand = [st.session_state.deck.pop(), st.session_state.deck.pop()]
            st.session_state.game_phase = 'player_turn'
            st.rerun()

elif phase == 'player_turn':
    st.header("Your Turn")
    st.info("Hit to take another card, or Stand to end your turn.")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Your Hand:**")
        st.write(hand_to_str(st.session_state.player_hand))
        st.markdown(f"**Value:** {calculate_hand_value(st.session_state.player_hand)}")
    with col2:
        st.markdown("**Dealer Hand:**")
        st.write(f"{card_to_str(st.session_state.dealer_hand[0])}, [Hidden]")
    st.markdown(f"**Current Bet:** ${st.session_state.bet:.2f}")
    col3, col4 = st.columns(2)
    with col3:
        if st.button("Hit"):
            st.session_state.player_hand.append(st.session_state.deck.pop())
            if calculate_hand_value(st.session_state.player_hand) > 21:
                st.session_state.game_phase = 'result'
            st.rerun()
    with col4:
        if st.button("Stand"):
            st.session_state.game_phase = 'dealer_turn'
            st.rerun()

elif phase == 'dealer_turn':
    while calculate_hand_value(st.session_state.dealer_hand) < 17:
        st.session_state.dealer_hand.append(st.session_state.deck.pop())
    st.session_state.game_phase = 'result'
    st.rerun()

elif phase == 'result':
    st.header("Game Result")
    player_value = calculate_hand_value(st.session_state.player_hand)
    dealer_value = calculate_hand_value(st.session_state.dealer_hand)
    # Determine winner
    if player_value > 21:
        st.session_state.message = "You busted! You lose."
        st.session_state.dealer_money += st.session_state.bet
        st.session_state.player_money -= st.session_state.bet
    elif dealer_value > 21:
        st.session_state.message = "Dealer busted! You win."
        st.session_state.player_money += st.session_state.bet
        st.session_state.dealer_money -= st.session_state.bet
    elif player_value > dealer_value:
        st.session_state.message = "You win!"
        st.session_state.player_money += st.session_state.bet
        st.session_state.dealer_money -= st.session_state.bet
    elif dealer_value > player_value:
        st.session_state.message = "You lose!"
        st.session_state.dealer_money += st.session_state.bet
        st.session_state.player_money -= st.session_state.bet
    else:
        st.session_state.message = "Push!"
    # Display game state
    st.markdown(f"**Your Hand:** {hand_to_str(st.session_state.player_hand)} (Value: {player_value})")
    st.markdown(f"**Dealer Hand:** {hand_to_str(st.session_state.dealer_hand)} (Value: {dealer_value})")
    st.markdown(f"### {st.session_state.message}")
    # Check game over conditions
    if st.session_state.player_money <= 0:
        st.error("Too Bad! No money left.")
        st.stop()
    elif st.session_state.dealer_money <= 0:
        st.success("Casino Bankrupt!")
        st.stop()
    else:
        if st.button("Play Again"):
            st.session_state.game_phase = 'betting'
            st.session_state.deck = [(suit, rank) for suit in suits for rank in ranks]
            random.shuffle(st.session_state.deck)
            st.session_state.player_hand = []
            st.session_state.dealer_hand = []
            st.session_state.bet = 0.0
            st.rerun()

