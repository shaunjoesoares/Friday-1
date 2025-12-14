# Configuration for Friday Agent

# Gemini API Keys (Multiple keys for automatic rotation when quota exhausted)
# Get your keys from: https://aistudio.google.com/app/apikey
GEMINI_API_KEYS = [
    "YOUR_GEMINI_API_KEY_1",  # Key 1
    "YOUR_GEMINI_API_KEY_2",  # Key 2
    "YOUR_GEMINI_API_KEY_3",  # Key 3
    # Add more keys for higher quota (20 requests per key per day)
]

# For backward compatibility
GEMINI_API_KEY = GEMINI_API_KEYS[0]
