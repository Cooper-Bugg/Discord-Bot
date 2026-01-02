import random

"""
Bugg Bot - Game Logic Module

Contains pure game logic classes and utility functions for Discord bot games.
All classes are Discord-independent and return game state/status strings.

Multiplayer Games:
- BlackjackGame: Card game with dealer AI, deck management, Ace handling
- DeathRollGame: Shrinking ceiling dice game, turn management
- PokemonBattle: Turn-based combat with 17 types, move selection, type effectiveness
- TicTacToeGame: 3x3 grid, win detection (rows/columns/diagonals)
- Connect4Game: 6x7 grid with gravity physics, 4-in-a-row detection
- RPSGame: Rock Paper Scissors with choice validation and winner determination

Single-Player Games:
- HangmanGame: Word guessing with 5 categories, ASCII art stages
- WordleGame: 5-letter word guessing with color feedback (80-word list)
- AkinatorGame: 20 questions guessing game with 10 items and 8 questions
- TypeRaceGame: Typing speed challenge with 10 sentences, WPM/accuracy calculation
- GuessTheNumberGame: Number guessing (1-100) with higher/lower hints

Utility Functions:
- flip_coin, roll_dice, random_number, random_choice
- spin_roulette (1/6 chance), play_duel (quick draw timing)
- spin_slots (3-row slot machine with triple jackpot)
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

# Coinflip
def flip_coin():
    return random.choice(["Heads", "Tails"])

# Dice Roll
def roll_dice(sides=6, amount=1):
    """
    Rolls dice like '3d6'. Returns the list of rolls and total.
    """
    if sides < 1 or amount < 1 or amount > 100:
        return None, 0 # Error check
    
    rolls = [random.randint(1, sides) for _ in range(amount)]
    return rolls, sum(rolls)

# Random Number
def random_number(min_val=1, max_val=100):
    """
    Generate a random number between min and max (inclusive).
    """
    if min_val > max_val:
        return None
    return random.randint(min_val, max_val)

# Random Choice
def random_choice(options):
    """
    Pick a random item from a list of options.
    """
    if not options or len(options) == 0:
        return None
    return random.choice(options)

# Death Roll Game 
class DeathRollGame:
    def __init__(self, starter_id, start_cap=100):
        self.players = [starter_id] # We can add a second player later
        self.current_cap = start_cap
        self.turn_index = 0
        self.game_over = False
        
    def take_turn(self):
        """
        Rolls 1 to current_cap.
        Returns: (roll_result, is_loss)
        """
        # Roll strictly between 1 and current_cap
        roll = random.randint(1, self.current_cap)
        
        # Update the ceiling for the next person
        self.current_cap = roll
        
        # Check for loss
        if roll == 1:
            self.game_over = True
            return roll, True # True means "They Lost"
            
        return roll, False
# Pokemon Battler
class PokemonBattle:
    def __init__(self, team_a, team_b, mode="pve"):
        # Store the teams as lists of Pokemon dictionaries
        self.team_a = team_a 
        self.team_b = team_b 
        
        # Store the game mode to determine if we need to wait for a second player
        self.mode = mode     
        
        # Track which Pokemon in the list is currently fighting (Index 0 is the starter)
        self.active_a = 0 
        self.active_b = 0
        
        # Store player references (will be set after creation in main.py)
        self.p1_user = None
        self.p2_user = None
        
        # Determine first turn based on speed (faster Pokemon goes first)
        if team_a[0]['speed'] >= team_b[0]['speed']:
            self.turn = "team_a"
        else:
            self.turn = "team_b"
        
        # A log to store the battle text so we can send it all in one Discord message
        self.log = [] 

    def get_active(self, side):
        # Helper method to get the current fighter dictionary based on the side
        if side == "team_a":
            return self.team_a[self.active_a]
        else:
            return self.team_b[self.active_b]
    
    def get_turn_name(self):
        # Helper method to get the display name of whose turn it is
        if self.turn == "team_a" and self.p1_user:
            return self.p1_user.display_name
        elif self.turn == "team_b" and self.p2_user:
            return self.p2_user.display_name
        else:
            return "Team A" if self.turn == "team_a" else "Team B"

    def attack_turn(self, attacker_side, move_index=None):
        """
        Executes one attack round.
        move_index: Optional index (0-3) to choose specific move. If None, picks random (for CPU).
        Returns: (is_game_over, winner_side)
        """
        # Import here to avoid circular imports
        from .poke_api import get_type_effectiveness
        
        # Determine who is the attacker and who is the defender based on the input
        if attacker_side == "team_a":
            attacker = self.team_a[self.active_a]
            defender = self.team_b[self.active_b]
            next_turn = "team_b" # Set the next turn to the opponent
        else:
            attacker = self.team_b[self.active_b]
            defender = self.team_a[self.active_a]
            next_turn = "team_a"

        # Clear the previous turn's log so we don't spam old messages
        self.log = []

        # Get available moves
        available_moves = attacker.get('moves', [{'name': 'Tackle', 'power': 40, 'type': 'normal'}])
        
        # Choose move - either by index or random (for CPU)
        if move_index is not None and 0 <= move_index < len(available_moves):
            move = available_moves[move_index]
        else:
            move = random.choice(available_moves)
        
        power = move['power']
        move_type = move['type']
        
        # Calculate type effectiveness
        type_multiplier = get_type_effectiveness(move_type, defender.get('types', ['normal']))
        
        # Add random variance (0.85 to 1.0) so damage isn't always identical
        variance = random.uniform(0.85, 1.0)
        
        # Calculate the ratio of Attack vs Defense
        ratio = attacker['attack'] / defender['defense']
        
        # The final damage formula with type effectiveness
        damage = int(((2 * attacker['level'] / 5 + 2) * power * ratio / 50 + 2) * variance * type_multiplier)
        
        # Apply the damage to the defender's HP
        defender['hp'] -= damage
        
        # Add a descriptive message to the log for the user to see
        self.log.append(f"👊 **{attacker['name']}** used **{move['name']}** on **{defender['name']}** for **{damage}** damage!")
        
        # Add type effectiveness message
        if type_multiplier > 1.0:
            self.log.append("🔥 It's super effective!")
        elif type_multiplier < 1.0 and type_multiplier > 0:
            self.log.append("💧 It's not very effective...")
        elif type_multiplier == 0:
            self.log.append("❌ It had no effect!")

        # Check if the defender has fainted (HP drops to 0 or less)
        if defender['hp'] <= 0:
            defender['hp'] = 0 # Clamp HP to 0 so we don't show negative numbers
            self.log.append(f"💀 **{defender['name']}** fainted!")
            
            # Check if the team has any other Pokemon left (Tag Team Logic)
            # If the current index is the last one in the list, they have no more Pokemon
            if attacker_side == "team_a":
                # Defender is Team B. Check if Team B has more pokemon.
                if self.active_b < len(self.team_b) - 1:
                    self.active_b += 1
                    next_mon = self.team_b[self.active_b]
                    player_name = self.p2_user.display_name if self.p2_user else "Opponent"
                    self.log.append(f"🔁 **{player_name}** sent out **{next_mon['name']}**!")
                    
                    # Pass the turn to the new Pokemon
                    self.turn = next_turn 
                    return False, None
                else:
                    # Team B is out of Pokemon. Team A wins.
                    return True, "team_a" 
            else:
                # Defender is Team A. Check if Team A has more pokemon.
                if self.active_a < len(self.team_a) - 1:
                    self.active_a += 1
                    next_mon = self.team_a[self.active_a]
                    player_name = self.p1_user.display_name if self.p1_user else "Opponent"
                    self.log.append(f"🔁 **{player_name}** sent out **{next_mon['name']}**!")
                    
                    # Pass the turn to the new Pokemon
                    self.turn = next_turn
                    return False, None
                else:
                    # Team A is out of Pokemon. Team B wins.
                    return True, "team_b"

        # If no one fainted, simply pass the turn to the other player
        self.turn = next_turn
        return False, None
    
    def cpu_turn(self):
        # A helper method to force the CPU (always Team B) to take their turn
        return self.attack_turn("team_b")

# === Standalone Game Functions ===

def spin_roulette(members):
    """
    Simulates Russian roulette with a voice channel.
    
    Args:
        members: List of discord.Member objects (should exclude bots and owner)
    
    Returns:
        tuple: (is_hit, victim) where is_hit is True if chamber = 1, victim is the chosen member or None
    """
    chamber = random.randint(1, 6)
    
    if chamber == 1 and len(members) > 0:
        victim = random.choice(members)
        return True, victim
    
    return False, None

def play_duel():
    """
    Returns the wait time (in seconds) before "FIRE!" signal for a duel.
    This is the suspense timer between 2-5 seconds.
    
    Returns:
        int: Random seconds between 2 and 5
    """
    return random.randint(2, 5)

def spin_slots():
    """
    Spins a 3-row slot machine and returns the results.
    
    Returns:
        dict: Contains 'top', 'middle', 'bottom' (lists of 3 symbols each),
              'middle_jackpot', 'top_jackpot', 'bottom_jackpot' (booleans),
              'triple_jackpot' (boolean), and 'partial_win' (boolean)
    """
    symbols = ["🍒", "🔔", "💎", "7️⃣", "🍇"]
    
    # Spin three rows of three reels each
    top = [random.choice(symbols) for _ in range(3)]
    middle = [random.choice(symbols) for _ in range(3)]
    bottom = [random.choice(symbols) for _ in range(3)]
    
    # Check jackpots
    top_jackpot = (top[0] == top[1] == top[2])
    middle_jackpot = (middle[0] == middle[1] == middle[2])
    bottom_jackpot = (bottom[0] == bottom[1] == bottom[2])
    triple_jackpot = top_jackpot and middle_jackpot and bottom_jackpot
    
    # Check partial win (2 matching in middle row)
    partial_win = not middle_jackpot and (middle[0] == middle[1] or middle[1] == middle[2] or middle[0] == middle[2])
    
    return {
        'top': top,
        'middle': middle,
        'bottom': bottom,
        'top_jackpot': top_jackpot,
        'middle_jackpot': middle_jackpot,
        'bottom_jackpot': bottom_jackpot,
        'triple_jackpot': triple_jackpot,
        'partial_win': partial_win
    }

# === Hangman Game ===
class HangmanGame:
    """
    Classic word guessing game.
    Player tries to guess a word letter by letter.
    """
    
    WORD_LISTS = {
        "animals": ["elephant", "giraffe", "penguin", "dolphin", "cheetah", "kangaroo", "octopus", "butterfly"],
        "food": ["pizza", "sushi", "tacos", "burger", "pasta", "chocolate", "strawberry", "sandwich"],
        "countries": ["france", "japan", "brazil", "canada", "egypt", "australia", "mexico", "italy"],
        "movies": ["inception", "titanic", "avatar", "frozen", "jaws", "matrix", "gladiator", "casablanca"],
        "random": ["computer", "keyboard", "rainbow", "mountain", "ocean", "thunder", "bicycle", "guitar"]
    }
    
    def __init__(self, category="random"):
        self.category = category if category in self.WORD_LISTS else "random"
        self.word = random.choice(self.WORD_LISTS[self.category]).upper()
        self.guessed_letters = set()
        self.wrong_guesses = 0
        self.max_wrong = 6
        
    def guess_letter(self, letter):
        """
        Process a letter guess.
        Returns: (is_correct, game_status)
        game_status: "continue", "won", "lost", "already_guessed"
        """
        letter = letter.upper()
        
        if letter in self.guessed_letters:
            return False, "already_guessed"
        
        self.guessed_letters.add(letter)
        
        if letter in self.word:
            # Check if word is complete
            if self.is_word_complete():
                return True, "won"
            return True, "continue"
        else:
            self.wrong_guesses += 1
            if self.wrong_guesses >= self.max_wrong:
                return False, "lost"
            return False, "continue"
    
    def is_word_complete(self):
        """Check if all letters have been guessed"""
        return all(letter in self.guessed_letters for letter in self.word)
    
    def get_display_word(self):
        """Get the word with unguessed letters as underscores"""
        return " ".join(letter if letter in self.guessed_letters else "_" for letter in self.word)
    
    def get_hangman_art(self):
        """Return ASCII art for current state"""
        stages = [
            "```\n  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========\n```",
            "```\n  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========\n```",
            "```\n  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========\n```",
            "```\n  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========\n```",
            "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========\n```",
            "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========\n```",
            "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n=========\n```",
        ]
        return stages[self.wrong_guesses]

# === Tic Tac Toe Game ===
class TicTacToeGame:
    """
    Classic 3x3 Tic Tac Toe game for two players.
    """
    
    def __init__(self, player1_id, player2_id):
        self.board = [" " for _ in range(9)]
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.current_turn = player1_id
        self.symbol_map = {player1_id: "❌", player2_id: "⭕"}
        
    def make_move(self, player_id, position):
        """
        Make a move at position (1-9).
        Returns: (success, result)
        result: "continue", "win", "draw", "invalid", "not_your_turn", "occupied"
        """
        if player_id != self.current_turn:
            return False, "not_your_turn"
        
        if position < 1 or position > 9:
            return False, "invalid"
        
        index = position - 1
        if self.board[index] != " ":
            return False, "occupied"
        
        # Place the symbol
        self.board[index] = self.symbol_map[player_id]
        
        # Check for win
        if self.check_win():
            return True, "win"
        
        # Check for draw
        if " " not in self.board:
            return True, "draw"
        
        # Switch turns
        self.current_turn = self.player2_id if self.current_turn == self.player1_id else self.player1_id
        return True, "continue"
    
    def check_win(self):
        """Check if current player has won"""
        win_conditions = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]              # Diagonals
        ]
        
        for condition in win_conditions:
            if (self.board[condition[0]] == self.board[condition[1]] == self.board[condition[2]] != " "):
                return True
        return False
    
    def get_board_display(self):
        """Return formatted board string"""
        board_str = "```\n"
        board_str += f" {self.board[0]} │ {self.board[1]} │ {self.board[2]} \n"
        board_str += "───┼───┼───\n"
        board_str += f" {self.board[3]} │ {self.board[4]} │ {self.board[5]} \n"
        board_str += "───┼───┼───\n"
        board_str += f" {self.board[6]} │ {self.board[7]} │ {self.board[8]} \n"
        board_str += "```"
        return board_str

# === Connect Four Game ===
class Connect4Game:
    """
    Connect Four game for two players.
    Drop pieces into columns to get 4 in a row.
    """
    
    def __init__(self, player1_id, player2_id):
        self.board = [[" " for _ in range(7)] for _ in range(6)]
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.current_turn = player1_id
        self.symbol_map = {player1_id: "🔴", player2_id: "🟡"}
        
    def drop_piece(self, player_id, column):
        """
        Drop a piece in column (1-7).
        Returns: (success, result)
        result: "continue", "win", "draw", "invalid", "not_your_turn", "column_full"
        """
        if player_id != self.current_turn:
            return False, "not_your_turn"
        
        if column < 1 or column > 7:
            return False, "invalid"
        
        col_index = column - 1
        
        # Find the lowest empty row in this column
        for row in range(5, -1, -1):
            if self.board[row][col_index] == " ":
                self.board[row][col_index] = self.symbol_map[player_id]
                
                # Check for win
                if self.check_win(row, col_index):
                    return True, "win"
                
                # Check for draw
                if all(self.board[0][c] != " " for c in range(7)):
                    return True, "draw"
                
                # Switch turns
                self.current_turn = self.player2_id if self.current_turn == self.player1_id else self.player1_id
                return True, "continue"
        
        return False, "column_full"
    
    def check_win(self, row, col):
        """Check if the last move resulted in a win"""
        symbol = self.board[row][col]
        
        # Check horizontal
        count = 1
        for c in range(col - 1, -1, -1):
            if self.board[row][c] == symbol:
                count += 1
            else:
                break
        for c in range(col + 1, 7):
            if self.board[row][c] == symbol:
                count += 1
            else:
                break
        if count >= 4:
            return True
        
        # Check vertical
        count = 1
        for r in range(row + 1, 6):
            if self.board[r][col] == symbol:
                count += 1
            else:
                break
        if count >= 4:
            return True
        
        # Check diagonal (top-left to bottom-right)
        count = 1
        r, c = row - 1, col - 1
        while r >= 0 and c >= 0 and self.board[r][c] == symbol:
            count += 1
            r -= 1
            c -= 1
        r, c = row + 1, col + 1
        while r < 6 and c < 7 and self.board[r][c] == symbol:
            count += 1
            r += 1
            c += 1
        if count >= 4:
            return True
        
        # Check diagonal (top-right to bottom-left)
        count = 1
        r, c = row - 1, col + 1
        while r >= 0 and c < 7 and self.board[r][c] == symbol:
            count += 1
            r -= 1
            c += 1
        r, c = row + 1, col - 1
        while r < 6 and c >= 0 and self.board[r][c] == symbol:
            count += 1
            r += 1
            c -= 1
        if count >= 4:
            return True
        
        return False
    
    def get_board_display(self):
        """Return formatted board string"""
        board_str = "```\n"
        board_str += " 1  2  3  4  5  6  7\n"
        for row in self.board:
            board_str += " " + "  ".join(row) + "\n"
        board_str += "```"
        return board_str

# === Wordle Game ===
class WordleGame:
    """
    Daily Wordle-style word guessing game.
    Guess a 5-letter word in 6 tries.
    """
    
    WORD_LIST = [
        "apple", "beach", "brain", "bread", "brush", "chair", "chest", "chord", "click", "clock",
        "cloud", "dance", "diary", "drink", "earth", "flute", "forum", "fruit", "ghost", "grace",
        "grape", "happy", "heart", "house", "input", "juice", "light", "magic", "money", "music",
        "ocean", "paint", "peace", "piano", "plant", "power", "queen", "quick", "radio", "river",
        "scale", "shape", "sleep", "smile", "snake", "sound", "space", "speak", "speed", "sport",
        "stand", "start", "stone", "storm", "story", "style", "sugar", "sweet", "table", "theme",
        "think", "tiger", "title", "today", "tower", "train", "trash", "trust", "truth", "unity",
        "video", "virus", "voice", "waste", "watch", "water", "wheel", "world", "worth", "young"
    ]
    
    def __init__(self):
        self.word = random.choice(self.WORD_LIST).upper()
        self.attempts = []
        self.max_attempts = 6
        
    def make_guess(self, guess):
        """
        Process a guess.
        Returns: (feedback, status)
        feedback: list of tuples (letter, color)
        status: "continue", "won", "lost", "invalid_length", "invalid_chars", "no_attempts"
        """
        guess = guess.upper()
        
        if len(guess) != 5:
            return None, "invalid_length"
        
        if not guess.isalpha():
            return None, "invalid_chars"
        
        if len(self.attempts) >= self.max_attempts:
            return None, "no_attempts"
        
        self.attempts.append(guess)
        
        # Generate feedback
        feedback = []
        word_letters = list(self.word)
        
        # First pass: mark correct positions (green)
        for i, letter in enumerate(guess):
            if letter == self.word[i]:
                feedback.append((letter, "🟩"))
                word_letters[i] = None
            else:
                feedback.append((letter, None))
        
        # Second pass: mark wrong positions (yellow) and incorrect (gray)
        for i, (letter, color) in enumerate(feedback):
            if color is None:
                if letter in word_letters:
                    feedback[i] = (letter, "🟨")
                    word_letters[word_letters.index(letter)] = None
                else:
                    feedback[i] = (letter, "⬜")
        
        # Check win/loss
        if guess == self.word:
            return feedback, "won"
        elif len(self.attempts) >= self.max_attempts:
            return feedback, "lost"
        else:
            return feedback, "continue"
    
    def get_board_display(self):
        """Return formatted board with all attempts"""
        board_str = ""
        for attempt in self.attempts:
            board_str += " ".join(list(attempt)) + "\n"
        
        # Add empty rows
        remaining = self.max_attempts - len(self.attempts)
        for _ in range(remaining):
            board_str += "_ _ _ _ _\n"
        
        return board_str

# === Akinator Game (20 Questions) ===
class AkinatorGame:
    """
    20 questions style guessing game where the bot tries to guess what you're thinking.
    Uses a tree of questions to narrow down possibilities.
    """
    def __init__(self):
        # Simplified question tree - in production this would be much larger
        self.items = {
            "dog": {"animal": True, "pet": True, "flies": False, "water": False},
            "cat": {"animal": True, "pet": True, "flies": False, "water": False},
            "eagle": {"animal": True, "pet": False, "flies": True, "water": False},
            "shark": {"animal": True, "pet": False, "flies": False, "water": True},
            "car": {"animal": False, "vehicle": True, "flies": False, "water": False},
            "plane": {"animal": False, "vehicle": True, "flies": True, "water": False},
            "boat": {"animal": False, "vehicle": True, "flies": False, "water": True},
            "tree": {"animal": False, "plant": True, "alive": True, "water": False},
            "phone": {"animal": False, "tech": True, "handheld": True},
            "computer": {"animal": False, "tech": True, "handheld": False}
        }
        
        self.questions = [
            ("Is it an animal?", "animal"),
            ("Can it fly?", "flies"),
            ("Does it live in water?", "water"),
            ("Is it a pet?", "pet"),
            ("Is it a vehicle?", "vehicle"),
            ("Is it technology?", "tech"),
            ("Is it a plant?", "plant"),
            ("Can you hold it in your hand?", "handheld")
        ]
        
        self.possible_items = list(self.items.keys())
        self.current_question_index = 0
        self.answers = {}
        
    def get_current_question(self):
        """Return the current question"""
        if self.current_question_index >= len(self.questions):
            return None
        return self.questions[self.current_question_index][0]
    
    def answer_question(self, yes_or_no):
        """Process yes/no answer and narrow down possibilities"""
        if self.current_question_index >= len(self.questions):
            return "no_more_questions"
        
        question_text, attribute = self.questions[self.current_question_index]
        answer = yes_or_no.lower() in ["yes", "y"]
        self.answers[attribute] = answer
        
        # Filter possible items based on answer
        self.possible_items = [
            item for item in self.possible_items
            if self.items[item].get(attribute, None) == answer or self.items[item].get(attribute) is None
        ]
        
        self.current_question_index += 1
        
        # Check if we can guess
        if len(self.possible_items) == 1:
            return "guess_ready"
        elif len(self.possible_items) == 0:
            return "stumped"
        elif self.current_question_index >= len(self.questions):
            return "guess_ready"
        else:
            return "continue"
    
    def make_guess(self):
        """Return the bot's guess"""
        if len(self.possible_items) > 0:
            return self.possible_items[0]
        return None

# === Type Race Game ===
class TypeRaceGame:
    """
    Typing speed challenge - measures words per minute and accuracy
    """
    SENTENCES = [
        "The quick brown fox jumps over the lazy dog.",
        "Pack my box with five dozen liquor jugs.",
        "How vexingly quick daft zebras jump!",
        "The five boxing wizards jump quickly.",
        "Sphinx of black quartz, judge my vow.",
        "Two driven jocks help fax my big quiz.",
        "Five quacking zephyrs jolt my wax bed.",
        "The jay, pig, fox, zebra and my wolves quack!",
        "A wizard's job is to vex chumps quickly in fog.",
        "Watch Jeopardy, Alex Trebek's fun TV quiz game."
    ]
    
    def __init__(self):
        self.sentence = random.choice(self.SENTENCES)
        self.start_time = None
        self.end_time = None
        self.user_input = None
        
    def start(self):
        """Mark the start time"""
        import time
        self.start_time = time.time()
        
    def finish(self, user_input):
        """Calculate results"""
        import time
        self.end_time = time.time()
        self.user_input = user_input
        
        # Calculate time taken
        time_taken = self.end_time - self.start_time
        
        # Calculate accuracy
        correct_chars = sum(1 for a, b in zip(self.sentence, user_input) if a == b)
        accuracy = (correct_chars / len(self.sentence)) * 100
        
        # Calculate WPM (words per minute)
        # Standard: 5 characters = 1 word
        words_typed = len(user_input) / 5
        minutes = time_taken / 60
        wpm = words_typed / minutes if minutes > 0 else 0
        
        return {
            "time": time_taken,
            "accuracy": accuracy,
            "wpm": wpm,
            "correct": user_input == self.sentence
        }


class RPSGame:
    """Rock Paper Scissors game for two players"""
    def __init__(self, challenger_id, opponent_id):
        self.challenger_id = challenger_id
        self.opponent_id = opponent_id
        self.choices = {}  # {user_id: choice}
        self.status = "waiting"  # waiting, ready
        
    def make_choice(self, user_id, choice):
        """Record a player's choice"""
        choice = choice.lower()
        if choice not in ["rock", "paper", "scissors"]:
            return False
        self.choices[user_id] = choice
        if len(self.choices) == 2:
            self.status = "ready"
        return True
    
    def determine_winner(self):
        """Determine winner based on choices"""
        if len(self.choices) != 2:
            return None
        
        c1 = self.choices[self.challenger_id]
        c2 = self.choices[self.opponent_id]
        
        if c1 == c2:
            return "tie"
        
        # Check if challenger wins
        if (c1 == "rock" and c2 == "scissors") or \
           (c1 == "paper" and c2 == "rock") or \
           (c1 == "scissors" and c2 == "paper"):
            return self.challenger_id
        
        return self.opponent_id


class GuessTheNumberGame:
    """Number guessing game (1-100)"""
    def __init__(self):
        self.number = random.randint(1, 100)
        self.attempts = 0
        self.guesses = []
        
    def make_guess(self, guess):
        """Make a guess and get feedback"""
        self.attempts += 1
        self.guesses.append(guess)
        
        if guess == self.number:
            return "correct"
        elif guess < self.number:
            return "higher"
        else:
            return "lower"
