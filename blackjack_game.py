import random

class BlackjackGame:
    def __init__(self, channel_id, dealer_id):
        self.channel_id = channel_id
        self.deck = self._create_shuffled_deck() # A list of (rank, suit) tuples
        self.dealer_hand = []
        self.players = {} # Dictionary: {user_id: [hand, status, score]}
        self.status = "joining" # Can be "joining", "playing", or "finished"
        self.current_turn = None # The ID of the player whose turn it is

    def _create_shuffled_deck(self):
        # A helper method to create and shuffle the 52 cards
        rank = ['2','3','4','5','6','7','8','9','10','Jack','Queen','King','Ace']
        suits = ['♠️', '♥️', '♦️', '♣️'] # Spades, Hearts, Diamonds, Clubs
        deck = []
        
        for x in rank:
            for y in suits:
                deck.append((x, y))

        random.shuffle(deck)
        return deck
""""    
    def add_player(self, user_id):
        # Add a player and deal them two cards
        pass # Implementation required

    def get_hand_value(self, hand):
        # Calculate the score, handling Aces (1 or 11)

        
    def dealer_play(self):
        # Logic for the dealer to hit until 17 or more
        pass # Implementation required
"""
    # === TESTING ===
