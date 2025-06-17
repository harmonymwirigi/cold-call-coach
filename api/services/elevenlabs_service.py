# ===== API/SERVICES/ELEVENLABS_SERVICE.PY =====
import requests
import os
import logging
from io import BytesIO
from typing import Optional, Dict, Any, List
import time

logger = logging.getLogger(__name__)

class ElevenLabsService:
    def __init__(self):
        self.api_key = os.getenv('REACT_APP_ELEVENLABS_API_KEY')
        self.voice_id = os.getenv('REACT_APP_ELEVENLABS_VOICE_ID')
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # Default voice settings for prospect simulation
        self.default_voice_settings = {
            "stability": 0.75,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
        
        # Cache for commonly used phrases to save API calls
        self.phrase_cache = {}
        
        if not self.api_key:
            logger.warning("ElevenLabs API key not found. TTS will not work.")
        if not self.voice_id:
            logger.warning("ElevenLabs Voice ID not found. Using default voice.")
            
    def text_to_speech(self, text: str, voice_settings: Optional[Dict] = None, 
                      use_cache: bool = True) -> Optional[BytesIO]:
        """
        Convert text to speech using ElevenLabs API
        
        Args:
            text: Text to convert to speech
            voice_settings: Custom voice settings (optional)
            use_cache: Whether to use cached audio for common phrases
            
        Returns:
            BytesIO stream containing audio data or None if failed
        """
        try:
            if not self.api_key:
                logger.error("ElevenLabs API key not configured")
                return None
                
            if not text or len(text.strip()) == 0:
                logger.warning("Empty text provided for TTS")
                return None
            
            # Clean and validate text
            text = text.strip()
            if len(text) > 2500:  # ElevenLabs limit
                logger.warning(f"Text too long ({len(text)} chars), truncating")
                text = text[:2500]
            
            # Check cache for common phrases
            cache_key = self._get_cache_key(text, voice_settings)
            if use_cache and cache_key in self.phrase_cache:
                logger.info("Using cached audio for phrase")
                return BytesIO(self.phrase_cache[cache_key])
            
            # Prepare voice settings
            if not voice_settings:
                voice_settings = self.default_voice_settings.copy()
            
            # Prepare request
            url = f"{self.base_url}/text-to-speech/{self.voice_id or 'default'}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": voice_settings
            }
            
            # Make API request with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        audio_data = response.content
                        
                        # Cache common phrases (under 100 chars)
                        if use_cache and len(text) < 100:
                            self.phrase_cache[cache_key] = audio_data
                            # Limit cache size
                            if len(self.phrase_cache) > 50:
                                # Remove oldest entries
                                oldest_key = next(iter(self.phrase_cache))
                                del self.phrase_cache[oldest_key]
                        
                        logger.info(f"Successfully generated TTS for text: {text[:50]}...")
                        return BytesIO(audio_data)
                        
                    elif response.status_code == 401:
                        logger.error("ElevenLabs API authentication failed")
                        return None
                        
                    elif response.status_code == 422:
                        logger.error(f"ElevenLabs API validation error: {response.text}")
                        return None
                        
                    elif response.status_code == 429:
                        # Rate limit hit, wait and retry
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt  # Exponential backoff
                            logger.warning(f"Rate limit hit, waiting {wait_time} seconds...")
                            time.sleep(wait_time)
                            continue
                        else:
                            logger.error("Rate limit exceeded, max retries reached")
                            return None
                            
                    else:
                        logger.error(f"ElevenLabs API error {response.status_code}: {response.text}")
                        if attempt < max_retries - 1:
                            time.sleep(1)
                            continue
                        return None
                        
                except requests.exceptions.Timeout:
                    logger.warning(f"TTS request timeout (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    return None
                    
                except requests.exceptions.RequestException as e:
                    logger.error(f"TTS request error: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error in text_to_speech: {e}")
            return None

    def text_to_speech_streaming(self, text: str, voice_settings: Optional[Dict] = None) -> Optional[requests.Response]:
        """
        Convert text to speech with streaming response (for real-time playback)
        
        Args:
            text: Text to convert to speech
            voice_settings: Custom voice settings (optional)
            
        Returns:
            Streaming response object or None if failed
        """
        try:
            if not self.api_key:
                logger.error("ElevenLabs API key not configured")
                return None
                
            if not text or len(text.strip()) == 0:
                return None
            
            text = text.strip()
            if len(text) > 2500:
                text = text[:2500]
            
            if not voice_settings:
                voice_settings = self.default_voice_settings.copy()
            
            url = f"{self.base_url}/text-to-speech/{self.voice_id or 'default'}/stream"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": voice_settings
            }
            
            response = requests.post(url, json=data, headers=headers, stream=True, timeout=30)
            
            if response.status_code == 200:
                return response
            else:
                logger.error(f"Streaming TTS error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error in streaming TTS: {e}")
            return None

    def get_available_voices(self) -> Optional[List[Dict]]:
        """
        Get list of available voices from ElevenLabs
        
        Returns:
            List of voice objects or None if failed
        """
        try:
            if not self.api_key:
                return None
            
            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                voices_data = response.json()
                return voices_data.get('voices', [])
            else:
                logger.error(f"Error getting voices: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching voices: {e}")
            return None

    def get_voice_settings_for_prospect(self, prospect_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get optimized voice settings based on prospect profile
        
        Args:
            prospect_profile: Dictionary with prospect information
            
        Returns:
            Voice settings optimized for the prospect type
        """
        # Base settings
        settings = self.default_voice_settings.copy()
        
        # Adjust based on job title
        job_title = prospect_profile.get('prospect_job_title', '').lower()
        industry = prospect_profile.get('prospect_industry', '').lower()
        
        # C-level executives: more authoritative, stable voice
        if any(title in job_title for title in ['ceo', 'cto', 'cfo', 'coo', 'president', 'founder']):
            settings.update({
                "stability": 0.85,  # More stable/authoritative
                "similarity_boost": 0.80,
                "style": 0.1  # Slightly more expressive
            })
            
        # Managers: balanced, professional
        elif 'manager' in job_title or 'director' in job_title:
            settings.update({
                "stability": 0.75,
                "similarity_boost": 0.75,
                "style": 0.05
            })
            
        # Technical roles: more analytical tone
        elif any(tech in job_title for tech in ['engineer', 'developer', 'technical', 'it']):
            settings.update({
                "stability": 0.80,
                "similarity_boost": 0.70,
                "style": 0.0  # More neutral
            })
        
        # Industry adjustments
        if 'healthcare' in industry:
            settings["stability"] = min(settings["stability"] + 0.05, 1.0)  # More professional
        elif 'finance' in industry or 'banking' in industry:
            settings["stability"] = min(settings["stability"] + 0.05, 1.0)  # Conservative
        elif 'startup' in industry or 'tech' in industry:
            settings["style"] = min(settings["style"] + 0.05, 1.0)  # Slightly more dynamic
        
        return settings

    def _get_cache_key(self, text: str, voice_settings: Optional[Dict]) -> str:
        """Generate cache key for text and settings"""
        # Simple hash-like key based on text and main settings
        settings_key = ""
        if voice_settings:
            stability = voice_settings.get('stability', 0.75)
            similarity = voice_settings.get('similarity_boost', 0.75)
            settings_key = f"_{stability}_{similarity}"
        
        # Use first 50 chars of text + settings
        return f"{text[:50].lower().replace(' ', '_')}{settings_key}"

    def preload_common_phrases(self) -> None:
        """Preload common roleplay phrases into cache"""
        common_phrases = [
            "Hello?",
            "What's this about?",
            "I'm not interested.",
            "Now is not a good time.",
            "Can you send me an email?",
            "Who is this?",
            "I'm in a meeting.",
            "Call me back later.",
            "What are you selling?",
            "Is this a sales call?",
            "We don't take cold calls.",
            "I've never heard of you.",
            "Send me information.",
            "I'm not the decision maker.",
            "We're happy with our current provider.",
            "It's too expensive.",
            "We have no budget.",
            "Hello? Are you still there?",
            "Can you hear me?",
            "I don't have much time."
        ]
        
        logger.info("Preloading common phrases for TTS cache...")
        
        for phrase in common_phrases:
            try:
                self.text_to_speech(phrase, use_cache=True)
                time.sleep(0.1)  # Small delay to avoid rate limits
            except Exception as e:
                logger.warning(f"Failed to preload phrase '{phrase}': {e}")
                
        logger.info(f"Preloaded {len(self.phrase_cache)} phrases into TTS cache")

    def get_usage_info(self) -> Optional[Dict[str, Any]]:
        """
        Get current API usage information
        
        Returns:
            Usage information dictionary or None if failed
        """
        try:
            if not self.api_key:
                return None
            
            url = f"{self.base_url}/user"
            headers = {"xi-api-key": self.api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    'character_count': user_data.get('character_count', 0),
                    'character_limit': user_data.get('character_limit', 0),
                    'can_extend_character_limit': user_data.get('can_extend_character_limit', False)
                }
            else:
                logger.error(f"Error getting usage info: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching usage info: {e}")
            return None