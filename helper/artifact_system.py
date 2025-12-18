"""
Bugg Bot - Living Artifact Module

An evolving entity that changes based on bot usage patterns:
- Chaos stat: Increases with gambling (slots, roulette)
- Greed stat: Increases with market/economy checks
- Shadow stat: Increases with nighttime usage (12am-6am)

ArtifactSystem Class:
- loadState() / saveState(): JSON persistence to artifact.json
- modifyStat(stat, amount): Silently track hidden stats
- checkEvolution(): Trigger mood changes when stats exceed 50
- getRandomTouchResponse(mood): 40 mood-specific interaction responses
- getRandomDisturbOutcome(mood): 20 outcome scenarios (calm vs anger)
- generateImage(): Procedurally generate artifact visualization with PIL

Visual Generation:
- Color influenced by chaos/greed/shadow stats
- Polygon shapes morph based on hidden stats
- Aura lines reflect current mood intensity
- Blur effects create ethereal appearance

Moods: Dormant (baseline) → Unstable (chaos) → Voracious (greed) → Eerie (shadow)
"""

import json
import os
import random
import math
import datetime
from PIL import Image, ImageDraw, ImageFilter
from io import BytesIO
import discord

# File to save the artifact state so it survives bot restarts
FILE_PATH = "artifact.json"

class ArtifactSystem:
    def __init__(self):
        # Default state if no file exists
        self.state = {
            "name": "The Cracked Compass",
            "ageDays": 0,
            "mood": "Dormant",
            "traits": ["Humming", "Cold"],
            "hiddenStats": {
                "chaos": 0,    # Driven by gambling
                "greed": 0,    # Driven by market
                "shadow": 0    # Driven by night usage
            },
            "lastInteraction": str(datetime.datetime.now())
        }
        
        # Randomized response pools for !touch command
        self.touchResponses = {
            "Dormant": [
                "It feels cold and smooth, like polished glass.",
                "The surface is oddly warm despite appearing dormant.",
                "You feel a faint vibration, barely noticeable.",
                "It's surprisingly heavy for its size.",
                "Your fingers leave no mark on its pristine surface.",
                "A low hum resonates through your fingertips.",
                "The texture shifts between rough and smooth.",
                "It feels like touching frozen metal.",
                "A strange comfort washes over you as you touch it.",
                "You sense something sleeping deep within."
            ],
            "Unstable": [
                "It zaps your finger! Static electricity radiates from it.",
                "The artifact jerks away from your touch!",
                "Sparks dance across its surface where you touched.",
                "It's uncomfortably hot - you pull your hand back.",
                "The vibrations intensify at your touch, almost painful.",
                "Colors swirl violently across its surface.",
                "Your hand tingles for several seconds afterward.",
                "It emits a high-pitched whine when touched.",
                "The artifact seems to pulse with your heartbeat.",
                "You feel dizzy and disoriented for a moment."
            ],
            "Voracious": [
                "It feels heavy, almost as if it's pulling your hand down.",
                "The artifact seems to grip your fingers - you have to pull away.",
                "Your hand sinks into its surface slightly, like thick mud.",
                "It's warm and pulsing, as if alive.",
                "You feel an overwhelming urge to keep holding it.",
                "The weight seems to double the moment you touch it.",
                "Golden light seeps from beneath your fingertips.",
                "It feels sticky, as if reluctant to let go.",
                "A deep hunger emanates from within.",
                "Your reflection in its surface looks... different."
            ],
            "Eerie": [
                "Your hand passes through a mist. You feel a chill in your spine.",
                "The artifact isn't quite solid - your fingers sink through its edges.",
                "Whispers echo in your mind the moment you touch it.",
                "You see fleeting shadows move across its surface.",
                "It feels like touching frozen smoke.",
                "Your hand goes numb where you touched it.",
                "You swear you hear your name whispered.",
                "The temperature drops noticeably around it.",
                "Dark tendrils of shadow wrap around your wrist briefly.",
                "You feel watched as your fingers make contact."
            ]
        }
        
        # Randomized outcomes for !disturb command
        self.disturbCalm = [
            "The artifact shudders and goes silent. The energy dissipates.",
            "A wave of calm washes over it. All tension fades.",
            "It releases a long sigh-like sound and settles.",
            "The chaotic energies drain away into nothingness.",
            "For a moment, it glows peacefully before returning to stillness.",
            "The artifact seems to... forgive you?",
            "All its accumulated energy releases as a gentle breeze.",
            "It resets itself, as if nothing ever happened.",
            "The artifact purrs softly and becomes docile.",
            "You feel a sense of mutual understanding."
        ]
        
        self.disturbAnger = [
            "💥 The artifact flares up violently! You shouldn't have done that.",
            "💥 It SCREAMS with rage! Dark energy erupts from it!",
            "💥 The artifact cracks further, glowing with fury!",
            "💥 A shockwave knocks you backward! It's ANGRY.",
            "💥 Lightning arcs between it and nearby objects!",
            "💥 You hear glass shattering inside your mind!",
            "💥 The air around it distorts with pure chaos!",
            "💥 It brands a mark on your hand that burns!",
            "💥 Reality itself seems to glitch near the artifact!",
            "💥 You've awakened something that should have stayed asleep!"
        ]
        
        self.loadState()

    def loadState(self):
        # Load JSON from disk
        if os.path.exists(FILE_PATH):
            with open(FILE_PATH, "r") as f:
                self.state = json.load(f)

    def saveState(self):
        # Save JSON to disk
        with open(FILE_PATH, "w") as f:
            json.dump(self.state, f, indent=4)

    def modifyStat(self, statName, amount):
        # Safely update hidden counters and save
        if statName in self.state["hiddenStats"]:
            self.state["hiddenStats"][statName] += amount
            self.checkEvolution()
            self.saveState()
    
    def getRandomTouchResponse(self):
        """Get a random touch response based on current mood"""
        mood = self.state["mood"]
        return random.choice(self.touchResponses.get(mood, self.touchResponses["Dormant"]))
    
    def getRandomDisturbOutcome(self, outcome_type):
        """Get a random disturb outcome"""
        if outcome_type == "calm":
            return random.choice(self.disturbCalm)
        else:
            return random.choice(self.disturbAnger)

    def checkEvolution(self):
        # Logic to change Mood/Traits based on counters
        stats = self.state["hiddenStats"]
        
        # Determine Dominant Stat
        highestStat = max(stats, key=stats.get)
        maxValue = stats[highestStat]

        # Threshold to trigger a mood change
        if maxValue > 50:
            if highestStat == "chaos":
                self.state["mood"] = "Unstable"
                self.state["traits"] = ["Vibrating", "Hot"]
            elif highestStat == "greed":
                self.state["mood"] = "Voracious"
                self.state["traits"] = ["Golden", "Heavy"]
            elif highestStat == "shadow":
                self.state["mood"] = "Eerie"
                self.state["traits"] = ["Whispering", "Dark"]
        else:
            self.state["mood"] = "Dormant"
            self.state["traits"] = ["Humming", "Cold"]

    def generateImage(self):
        # Procedural Generation based on stats
        # Create a blank black canvas
        width, height = 400, 400
        img = Image.new("RGB", (width, height), "black")
        draw = ImageDraw.Draw(img)

        # Center point
        cx, cy = width // 2, height // 2

        # STATS DETERMINE VISUALS
        chaos = self.state["hiddenStats"]["chaos"]
        greed = self.state["hiddenStats"]["greed"]
        shadow = self.state["hiddenStats"]["shadow"]

        # Base Color (R, G, B) mixed by stats
        # Chaos adds Red, Greed adds Green, Shadow adds Blue
        red = min(255, 50 + chaos * 2)
        green = min(255, 50 + greed * 2)
        blue = min(255, 50 + shadow * 2)
        baseColor = (int(red), int(green), int(blue))

        # Shape Logic:
        # Chaos increases the number of points (makes it jagged)
        # Greed increases the size (makes it bloated)
        numPoints = 5 + int(chaos / 5)
        radius = 50 + greed
        
        # Calculate polygon points using trigonometry
        points = []
        for i in range(numPoints):
            # Angle for this point
            angle = (math.pi * 2 * i) / numPoints
            
            # Add random jitter if chaos is high
            jitter = random.randint(0, int(chaos)) if chaos > 0 else 0
            
            x = cx + math.cos(angle) * (radius + jitter)
            y = cy + math.sin(angle) * (radius + jitter)
            points.append((x, y))

        # Draw the main shape
        draw.polygon(points, outline=baseColor, fill=None)

        # Add "Aura" lines connecting random points
        # Higher Shadow = More connecting lines
        for _ in range(int(shadow)):
            p1 = random.choice(points)
            p2 = random.choice(points)
            draw.line([p1, p2], fill=(100, 100, 100), width=1)

        # Apply a Blur filter if the mood is "Eerie" or "Dormant"
        if self.state["mood"] in ["Eerie", "Dormant"]:
            img = img.filter(ImageFilter.GaussianBlur(2))

        # Save to buffer
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf

# Initialize the system globally
artifact = ArtifactSystem()