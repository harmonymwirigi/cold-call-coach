

# ===== API/CONFIG.PY =====
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
    
    # Supabase
    SUPABASE_URL = os.getenv('REACT_APP_SUPABASE_URL')
    SUPABASE_KEY = os.getenv('REACT_APP_SUPABASE_ANON_KEY')
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('REACT_APP_OPENAI_API_KEY')
    
    # ElevenLabs
    ELEVENLABS_API_KEY = os.getenv('REACT_APP_ELEVENLABS_API_KEY')
    ELEVENLABS_VOICE_ID = os.getenv('REACT_APP_ELEVENLABS_VOICE_ID')
    
    # Resend
    RESEND_API_KEY = os.getenv('REACT_APP_RESEND_API_KEY')
    
    # App settings
    APP_URL = os.getenv('REACT_APP_APP_URL', 'http://localhost:3001')
    ADMIN_EMAIL = os.getenv('REACT_APP_ADMIN_EMAIL', 'admin@example.com')
    print(ADMIN_EMAIL)
    # Usage limits
    TRIAL_HOURS_LIMIT = 3
    BASIC_MONTHLY_HOURS = 50
    PRO_MONTHLY_HOURS = 50
    
    # Unlock duration (hours)
    BASIC_UNLOCK_DURATION = 24