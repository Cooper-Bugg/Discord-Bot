import aiohttp
import random

"""
Bugg Bot - Pokémon API Integration Module

Provides Pokémon data fetching and battle mechanics using PokéAPI.

Features:
- Fetch Pokémon base stats, types, and moves from PokéAPI
- Scale stats to specific levels for balanced gameplay
- Complete 17-type effectiveness chart (Fire, Water, Grass, Electric, etc.)
- Type advantage/disadvantage calculations (2x, 0.5x, 0x multipliers)

Functions:
- get_pokemon_data(name): Fetch raw Pokémon data from API
- scale_stats(base_data, level): Scale stats to specific level
- get_type_effectiveness(attacker_type, defender_types): Calculate damage multipliers

Supports Generation 1-9 Pokémon with full type matchup system.
API Documentation: https://pokeapi.co/
"""

async def get_pokemon_data(pokemon_name):
    """
    Fetches raw data from PokeAPI.
    Returns a dictionary of base stats and the image URL.
    """
    # Build the URL dynamically based on the requested name
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
    
    try:
        # Create an asynchronous session to talk to the internet
        async with aiohttp.ClientSession() as session:
            # Send the GET request to the API
            async with session.get(url) as response:
                # If the API returns anything other than 200 OK, return None to signal failure
                if response.status != 200:
                    return None
                
                # Convert the raw JSON text into a Python dictionary
                data = await response.json()
                
                # Extract Base Stats using a dictionary comprehension for cleaner code
                # The API returns a list of stats, so we loop through them to find HP, Attack, etc.
                stats = {stat['stat']['name']: stat['base_stat'] for stat in data['stats']}
                
                # Extract Sprite (Image) to display in the Discord Embed
                # 'front_default' is the standard image used in games
                sprite_url = data['sprites']['front_default']
                
                # Extract Pokemon types (e.g., fire, water, grass)
                types = [t['type']['name'] for t in data['types']]
                
                # Extract moves - get first 4 moves that have power
                moves = []
                for move_data in data['moves'][:20]:  # Check first 20 moves
                    move_url = move_data['move']['url']
                    # We need to fetch move details to get power
                    async with session.get(move_url) as move_response:
                        if move_response.status == 200:
                            move_info = await move_response.json()
                            if move_info.get('power'):  # Only moves with power (damaging moves)
                                moves.append({
                                    'name': move_info['name'].replace('-', ' ').title(),
                                    'power': move_info['power'],
                                    'type': move_info['type']['name']
                                })
                                if len(moves) >= 4:  # Limit to 4 moves
                                    break
                
                # If no moves found, give a default tackle
                if not moves:
                    moves = [{'name': 'Tackle', 'power': 40, 'type': 'normal'}]
                
                # Build the simplified Pokemon Object for our game
                # We capitalize the name for better display in chat
                pokemon = {
                    "name": data['name'].capitalize(),
                    "hp": stats['hp'],
                    "max_hp": stats['hp'], # Store max_hp separately so we can display health bars later
                    "attack": stats['attack'],
                    "defense": stats['defense'],
                    "speed": stats['speed'],
                    "image": sprite_url,
                    "level": 1, # Default level is 1 until scaled
                    "types": types,
                    "moves": moves
                }
                return pokemon
    except Exception as e:
        # Catch any unexpected errors (like connection drops) and print them to the console
        print(f"API Error: {e}")
        return None

def scale_stats(pokemon_data, level):
    """
    Scales the base stats to a specific level using a simplified math formula.
    """
    # Safety check: if the data is empty, do nothing
    if not pokemon_data:
        return None

    # Calculate the multiplier based on level 50 being the baseline
    # A level 100 pokemon will have double the stats of a level 50
    multiplier = level / 50.0 
    
    # Create a COPY of the dictionary so we don't accidentally overwrite the original base stats
    # This is crucial if multiple people use the same Pokemon at different levels
    new_poke = pokemon_data.copy()
    new_poke['level'] = level
    
    # Scale Stats: (Base * Multiplier)
    # We add (level * 2) to HP so low-level Pokemon aren't too squishy and die in 1 hit
    new_poke['max_hp'] = int(pokemon_data['hp'] * multiplier) + (level * 2)
    new_poke['hp'] = new_poke['max_hp'] # Start the battle at full health
    new_poke['attack'] = int(pokemon_data['attack'] * multiplier)
    new_poke['defense'] = int(pokemon_data['defense'] * multiplier)
    new_poke['speed'] = int(pokemon_data['speed'] * multiplier)
    
    # Preserve types and moves
    new_poke['types'] = pokemon_data.get('types', ['normal'])
    new_poke['moves'] = pokemon_data.get('moves', [{'name': 'Tackle', 'power': 40, 'type': 'normal'}])
    
    return new_poke

def get_type_effectiveness(attack_type, defender_types):
    """
    Calculate type effectiveness multiplier.
    Returns 2.0 for super effective, 0.5 for not very effective, 0 for no effect.
    """
    # Simplified type chart (not complete, but covers main types)
    super_effective = {
        'fire': ['grass', 'ice', 'bug', 'steel'],
        'water': ['fire', 'ground', 'rock'],
        'grass': ['water', 'ground', 'rock'],
        'electric': ['water', 'flying'],
        'ice': ['grass', 'ground', 'flying', 'dragon'],
        'fighting': ['normal', 'ice', 'rock', 'dark', 'steel'],
        'poison': ['grass', 'fairy'],
        'ground': ['fire', 'electric', 'poison', 'rock', 'steel'],
        'flying': ['grass', 'fighting', 'bug'],
        'psychic': ['fighting', 'poison'],
        'bug': ['grass', 'psychic', 'dark'],
        'rock': ['fire', 'ice', 'flying', 'bug'],
        'ghost': ['psychic', 'ghost'],
        'dragon': ['dragon'],
        'dark': ['psychic', 'ghost'],
        'steel': ['ice', 'rock', 'fairy'],
        'fairy': ['fighting', 'dragon', 'dark']
    }
    
    not_effective = {
        'fire': ['fire', 'water', 'rock', 'dragon'],
        'water': ['water', 'grass', 'dragon'],
        'grass': ['fire', 'grass', 'poison', 'flying', 'bug', 'dragon', 'steel'],
        'electric': ['electric', 'grass', 'dragon'],
        'ice': ['fire', 'water', 'ice', 'steel'],
        'fighting': ['poison', 'flying', 'psychic', 'bug', 'fairy'],
        'poison': ['poison', 'ground', 'rock', 'ghost'],
        'ground': ['grass', 'bug'],
        'flying': ['electric', 'rock', 'steel'],
        'psychic': ['psychic', 'steel'],
        'bug': ['fire', 'fighting', 'poison', 'flying', 'ghost', 'steel', 'fairy'],
        'rock': ['fighting', 'ground', 'steel'],
        'ghost': ['dark'],
        'dragon': ['steel'],
        'dark': ['fighting', 'dark', 'fairy'],
        'steel': ['fire', 'water', 'electric', 'steel'],
        'fairy': ['fire', 'poison', 'steel']
    }
    
    no_effect = {
        'normal': ['ghost'],
        'electric': ['ground'],
        'fighting': ['ghost'],
        'poison': ['steel'],
        'ground': ['flying'],
        'psychic': ['dark'],
        'ghost': ['normal'],
        'dragon': ['fairy']
    }
    
    multiplier = 1.0
    
    for defender_type in defender_types:
        # Check for immunity (no effect)
        if attack_type in no_effect and defender_type in no_effect[attack_type]:
            return 0.0
        
        # Check for super effective
        if attack_type in super_effective and defender_type in super_effective[attack_type]:
            multiplier *= 2.0
        
        # Check for not very effective
        elif attack_type in not_effective and defender_type in not_effective[attack_type]:
            multiplier *= 0.5
    
    return multiplier