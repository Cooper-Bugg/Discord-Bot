import random

"""
Blackjack Game Logic Module

Handles all blackjack game mechanics including:
- Deck creation and shuffling
- Player and dealer hand management
- Score calculation with Ace handling
- Game state tracking and round reset

Death Roll Rules:
- Two players agree on starting wager and ceiling (e.g., 1000)
- Player A rolls 1-1000, gets a number (e.g., 842)
- Player B must roll 1-842, gets a number (e.g., 230)
- Continue back and forth with shrinking ceiling
- First player to roll 1 loses

Future additions: Dice rolling, coin flipping, death roll
"""

class BlackjackGame:
    def __init__(self, channel_id, dealer_id):
        self.channel_id = channel_id
        self.deck = self._create_shuffled_deck() # A list of (rank, suit) tuples
        self.dealer_hand = []
        self.dealer_hand = [self.deck.pop(), self.deck.pop()] # Immediately give the deal 2 cards
        self.players = {} # Dictionary: {user_id: [hand, status, score]}
        self.status = "joining" # Can be "joining", "playing", or "finished"
        self.current_turn = None # The ID of the player whose turn it is
        self.rank_values = {'2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, '10':10, # Gives each card its value
                            'Jack':10, 'Queen':10, 'King':10, 'Ace':11}
        self.hidden_card = '?'  # Emoji for dealer's face-down card 



    def _create_shuffled_deck(self):
        # A helper method to create and shuffle the 52 cards
        rank = ['2','3','4','5','6','7','8','9','10','Jack','Queen','King','Ace']
        suits = ['♤', '♡', '♢', '♧'] # Spades, Hearts, Diamonds, Clubs
        deck = []
        
        for x in rank:
            for y in suits:
                deck.append((x, y))

        random.shuffle(deck)
        return deck
   
    def add_player(self, user_id):
        # Add a player and deal them two cards
        # Draw 2 cards from the deck and pop them to discard
        card1 = self.deck.pop()
        card2 = self.deck.pop()
        hand = [card1, card2]

        # Calculate score
        score = self.get_hand_value(hand)

        # Save to dictionary [Hand List, Status, Score]
        self.players[user_id] = [hand, "playing", score]

        return hand # Return hand to print later

    def get_hand_value(self, hand):
        # Calculate the score, handling Aces (1 or 11)
        score = 0
        ace_count = 0

        for card in hand:
            rank = card[0]

            if rank == 'Ace':
                ace_count += 1

            value = self.rank_values[rank]
            score += value

            while score > 21 and ace_count > 0:
                score -= 10
                ace_count -= 1 

        return score
  
    def dealer_play(self):
        # Logic for the dealer to hit until 17 or more
        score = self.get_hand_value(self.dealer_hand)

        while score < 17:
            new_card = self.deck.pop()
            self.dealer_hand.append(new_card)
            score = self.get_hand_value(self.dealer_hand)

        return score
    
    def everyone_is_done(self):
        # Check if all players have either busted or stood
        for user_id, data in self.players.items():
            status = data[1]
            if status == "playing":
                return False
        return True
    
    def reset_round(self):
        # Check deck and refill if needed
        if len(self.deck) < 15:
            self.deck = self._create_shuffled_deck()
        
        # Reset dealer hand
        self.dealer_hand = [self.deck.pop(), self.deck.pop()]
        
        # Reset all players
        for user_id, data in self.players.items():
            # Give new hand
            new_hand = [self.deck.pop(), self.deck.pop()]
            # Calculate new score
            new_score = self.get_hand_value(new_hand)
            # Update player data: [hand, status, score]
            self.players[user_id] = [new_hand, "playing", new_score]
    
    # Formatting for the dealers hidden card
    def display_hand(self, hand, hide_second_card=False):
        if hide_second_card:
            # Get the first card (tuple)
            first_card = hand[0] 
            # Return string: "[RankSuit], [❓]"
            return f"[{first_card[0]}{first_card[1]}], [{self.hidden_card}]"
        
        else:
            # Join all cards into a string like "[10♥️], [J♣️]"
            formatted_cards = []
            for card in hand:
                formatted_cards.append(f"[{card[0]}{card[1]}]")
            return ", ".join(formatted_cards)
        
        def everyone_is_done(self):
        # Checks if anyone is still "playing". Returns True if everyone is "stood" or "busted"
            for player_data in self.players.values():
                status = player_data[1] # status is the second item
            if status == "playing":
                return False 
            return True
