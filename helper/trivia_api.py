import aiohttp
import html
import random

"""
Bugg Bot - Trivia API Integration Module

Fetches trivia questions from Open Trivia Database (opentdb.com).

Features:
- Multiple-choice questions with 4 answers
- Automatic HTML entity decoding (e.g., &quot; → ")
- Randomized answer order for fair gameplay
- Category and difficulty information included

Main Function:
- get_trivia_question(): Returns dict with:
  - question: The trivia question text
  - correct_answer: The correct answer
  - all_answers: List of 4 shuffled answers
  - category: Question category (e.g., Science, History)
  - difficulty: easy/medium/hard

API Documentation: https://opentdb.com/api_config.php
"""

async def get_trivia_question():
    """
    Fetches a random multiple-choice trivia question from Open Trivia DB.
    
    Returns:
        dict: Contains 'question', 'correct_answer', 'all_answers' (shuffled list), 
              and 'correct_index' (position of correct answer in shuffled list).
        None: If the API request fails.
    """
    url = "https://opentdb.com/api.php?amount=1&type=multiple"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                # Extract the question data
                # We use html.unescape because the API sends symbols like &quot; instead of "
                q_data = data['results'][0]
                question = html.unescape(q_data['question'])
                correct_answer = html.unescape(q_data['correct_answer'])
                incorrect_answers = [html.unescape(ans) for ans in q_data['incorrect_answers']]
                category = html.unescape(q_data['category'])
                difficulty = q_data['difficulty'].capitalize()
                
                # Combine all answers and shuffle them so the answer isn't always in the same position
                all_answers = incorrect_answers + [correct_answer]
                random.shuffle(all_answers)
                
                # Find the index of the correct answer in the shuffled list
                correct_index = all_answers.index(correct_answer)
                
                return {
                    'question': question,
                    'correct_answer': correct_answer,
                    'all_answers': all_answers,
                    'correct_index': correct_index,
                    'category': category,
                    'difficulty': difficulty
                }
    except Exception as e:
        print(f"Error fetching trivia: {e}")
        return None