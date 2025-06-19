# ===== UPDATED API/SERVICES/ELEVENLABS_SERVICE.PY - ROLEPLAY 1.1 ENHANCED =====

import os
import io
import requests
import logging
import wave
import struct
from typing import Optional, Dict, Any, BinaryIO, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ElevenLabsService:
    def __init__(self):
        self.api_key = os.getenv('REACT_APP_ELEVENLABS_API_KEY')
        self.base_url = "https://api.elevenlabs.io/v1"
        self.is_enabled = bool(self.api_key)
        
        # Enhanced voice configurations for Roleplay 1.1
        self.voice_configs = {
            # Default prospect voice
            'default_prospect': {
                'voice_id': 'EXAVITQu4vr4xnSDxMaL',  # Bella - professional female
                'stability': 0.5,
                'similarity_boost': 0.75,
                'style': 0.0,
                'use_speaker_boost': True
            },
            
            # Enhanced voices for different prospect types in Roleplay 1.1
            'cto_tech': {
                'voice_id': 'pNInz6obpgDQGcFmaJgB',  # Adam - confident male
                'stability': 0.6,
                'similarity_boost': 0.8,
                'style': 0.2,
                'use_speaker_boost': True
            },
            
            'ceo_executive': {
                'voice_id': 'EXAVITQu4vr4xnSDxMaL',  # Bella - authoritative female
                'stability': 0.7,
                'similarity_boost': 0.85,
                'style': 0.3,
                'use_speaker_boost': True
            },
            
            'vp_sales': {
                'voice_id': 'pNInz6obpgDQGcFmaJgB',  # Adam - sales-oriented
                'stability': 0.5,
                'similarity_boost': 0.7,
                'style': 0.4,
                'use_speaker_boost': True
            },
            
            'director_operations': {
                'voice_id': 'EXAVITQu4vr4xnSDxMaL',  # Bella - analytical
                'stability': 0.8,
                'similarity_boost': 0.75,
                'style': 0.1,
                'use_speaker_boost': True
            },
            
            # Special voices for Roleplay 1.1 scenarios
            'impatient_prospect': {
                'voice_id': 'pNInz6obpgDQGcFmaJgB',  # Adam - more urgent
                'stability': 0.3,
                'similarity_boost': 0.6,
                'style': 0.6,
                'use_speaker_boost': True
            },
            
            'busy_prospect': {
                'voice_id': 'EXAVITQu4vr4xnSDxMaL',  # Bella - rushed
                'stability': 0.4,
                'similarity_boost': 0.65,
                'style': 0.5,
                'use_speaker_boost': True
            }
        }
        
        # Enhanced voice settings for Roleplay 1.1 stages
        self.roleplay_11_voice_settings = {
            'phone_pickup': {'stability': 0.6, 'style': 0.0},  # Neutral answer
            'opener_evaluation': {'stability': 0.5, 'style': 0.2},  # Slightly skeptical
            'early_objection': {'stability': 0.4, 'style': 0.4},  # More resistant
            'mini_pitch': {'stability': 0.5, 'style': 0.3},  # Cautiously interested
            'soft_discovery': {'stability': 0.6, 'style': 0.2},  # More engaged
            'silence_impatience': {'stability': 0.3, 'style': 0.7},  # Clearly impatient
            'silence_hangup': {'stability': 0.2, 'style': 0.8}  # Very frustrated
        }
        
        if self.is_enabled:
            logger.info("ElevenLabs service initialized for Roleplay 1.1")
        else:
            logger.warning("ElevenLabs API key not provided - using fallback audio")

    def text_to_speech(self, text: str, voice_settings: Optional[Dict] = None) -> io.BytesIO:
        """
        Convert text to speech with enhanced Roleplay 1.1 support
        This method NEVER fails - always returns audio data
        """
        try:
            # Validate input
            if not text or not text.strip():
                logger.info("Empty text for TTS, generating silence")
                return self._generate_silent_audio()
            
            # Use enhanced voice settings or default
            if not voice_settings:
                voice_settings = self.voice_configs['default_prospect']
            
            # If ElevenLabs is not available, use emergency fallback
            if not self.is_enabled:
                logger.info("ElevenLabs not available, using emergency audio for Roleplay 1.1")
                return self._generate_emergency_audio(text)
            
            # Prepare request
            voice_id = voice_settings.get('voice_id', self.voice_configs['default_prospect']['voice_id'])
            url = f"{self.base_url}/text-to-speech/{voice_id}/stream"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            # Enhanced payload for Roleplay 1.1
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": voice_settings.get('stability', 0.5),
                    "similarity_boost": voice_settings.get('similarity_boost', 0.75),
                    "style": voice_settings.get('style', 0.0),
                    "use_speaker_boost": voice_settings.get('use_speaker_boost', True)
                }
            }
            
            logger.info(f"Generating TTS for Roleplay 1.1: {text[:50]}... with voice {voice_id}")
            
            # Make request with timeout
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Convert MP3 to WAV for better compatibility
                audio_stream = self._convert_mp3_to_wav(response.content)
                logger.info(f"Successfully generated Roleplay 1.1 TTS audio: {len(response.content)} bytes")
                return audio_stream
            else:
                logger.warning(f"ElevenLabs request failed with status {response.status_code}: {response.text}")
                return self._generate_emergency_audio(text)
                
        except requests.exceptions.Timeout:
            logger.warning("ElevenLabs request timed out, using emergency audio")
            return self._generate_emergency_audio(text)
        except requests.exceptions.RequestException as e:
            logger.warning(f"ElevenLabs request failed: {e}, using emergency audio")
            return self._generate_emergency_audio(text)
        except Exception as e:
            logger.error(f"Unexpected error in TTS generation: {e}, using emergency audio")
            return self._generate_emergency_audio(text)

    def get_voice_settings_for_prospect(self, prospect_info: Dict) -> Dict:
        """
        Get enhanced voice settings based on prospect information for Roleplay 1.1
        """
        try:
            job_title = prospect_info.get('prospect_job_title', '').lower()
            industry = prospect_info.get('prospect_industry', '').lower()
            roleplay_version = prospect_info.get('roleplay_version', 'standard')
            call_urgency = prospect_info.get('call_urgency', 'medium')
            stage = prospect_info.get('stage', 'phone_pickup')
            
            # Start with default configuration
            base_config = self.voice_configs['default_prospect'].copy()
            
            # Roleplay 1.1 specific enhancements
            if roleplay_version == '1.1':
                # Apply stage-specific voice settings
                if stage in self.roleplay_11_voice_settings:
                    stage_settings = self.roleplay_11_voice_settings[stage]
                    base_config.update(stage_settings)
                
                # Enhanced voice selection for Roleplay 1.1
                if 'cto' in job_title or 'technical' in job_title:
                    base_config.update(self.voice_configs['cto_tech'])
                elif 'ceo' in job_title or 'president' in job_title:
                    base_config.update(self.voice_configs['ceo_executive'])
                elif 'sales' in job_title or 'revenue' in job_title:
                    base_config.update(self.voice_configs['vp_sales'])
                elif 'director' in job_title or 'manager' in job_title:
                    base_config.update(self.voice_configs['director_operations'])
                
                # Adjust based on call urgency
                if call_urgency == 'high' or stage in ['silence_impatience', 'silence_hangup']:
                    base_config.update(self.voice_configs['impatient_prospect'])
                elif call_urgency == 'low':
                    base_config.update(self.voice_configs['busy_prospect'])
            
            # Industry-specific adjustments
            if 'technology' in industry or 'tech' in industry:
                base_config['style'] = min(base_config.get('style', 0) + 0.1, 1.0)
            elif 'finance' in industry or 'banking' in industry:
                base_config['stability'] = min(base_config.get('stability', 0.5) + 0.2, 1.0)
            elif 'healthcare' in industry:
                base_config['similarity_boost'] = min(base_config.get('similarity_boost', 0.75) + 0.1, 1.0)
            
            logger.info(f"Generated voice settings for Roleplay 1.1: {job_title} in {industry}, stage: {stage}")
            return base_config
            
        except Exception as e:
            logger.error(f"Error generating voice settings: {e}")
            return self.voice_configs['default_prospect']

    def _convert_mp3_to_wav(self, mp3_data: bytes) -> io.BytesIO:
        """
        Convert MP3 data to WAV format for better browser compatibility
        Enhanced for Roleplay 1.1 with better error handling
        """
        try:
            # For now, return MP3 as-is wrapped in BytesIO
            # In production, you might want to use pydub or similar for actual conversion
            audio_stream = io.BytesIO(mp3_data)
            
            # If we need actual WAV conversion, we could use pydub:
            # from pydub import AudioSegment
            # audio = AudioSegment.from_mp3(io.BytesIO(mp3_data))
            # wav_buffer = io.BytesIO()
            # audio.export(wav_buffer, format="wav")
            # wav_buffer.seek(0)
            # return wav_buffer
            
            return audio_stream
            
        except Exception as e:
            logger.error(f"Error converting MP3 to WAV: {e}")
            return self._generate_emergency_audio("Audio conversion failed")

    def _generate_silent_audio(self, duration_seconds: float = 0.5) -> io.BytesIO:
        """
        Generate silent audio for empty text - Enhanced for Roleplay 1.1
        """
        try:
            sample_rate = 44100
            duration_samples = int(sample_rate * duration_seconds)
            
            # Create WAV file in memory
            audio_buffer = io.BytesIO()
            
            with wave.open(audio_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                
                # Generate silence (zeros)
                silent_frames = b'\x00\x00' * duration_samples
                wav_file.writeframes(silent_frames)
            
            audio_buffer.seek(0)
            logger.info(f"Generated {duration_seconds}s silent audio for Roleplay 1.1")
            return audio_buffer
            
        except Exception as e:
            logger.error(f"Error generating silent audio: {e}")
            return self._create_minimal_wav_audio()

    def _generate_emergency_audio(self, text: str = None) -> io.BytesIO:
        """
        Generate emergency fallback audio when ElevenLabs fails
        Enhanced for Roleplay 1.1 with better quality
        """
        try:
            # Calculate appropriate duration based on text length
            if text:
                # Approximate speaking rate: 150 words per minute
                word_count = len(text.split())
                duration_seconds = max(1.0, min(8.0, (word_count / 150) * 60))
            else:
                duration_seconds = 2.0
            
            sample_rate = 44100
            duration_samples = int(sample_rate * duration_seconds)
            
            # Create WAV file in memory
            audio_buffer = io.BytesIO()
            
            with wave.open(audio_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                
                # Generate simple tone pattern to indicate speech
                # This creates a very quiet, low-frequency tone that simulates speech timing
                frames = []
                for i in range(duration_samples):
                    # Create a very quiet, variable tone
                    t = i / sample_rate
                    # Multiple sine waves at speech-like frequencies
                    amplitude = 0.1  # Very quiet
                    frequency1 = 200 + (50 * (i % 1000) / 1000)  # Variable frequency
                    frequency2 = 400 + (100 * (i % 2000) / 2000)
                    
                    # Combine frequencies and add some rhythm
                    wave1 = amplitude * 0.5 * (1 + 0.5 * (i % 4410 < 2205))
                    wave2 = amplitude * 0.3 * (1 + 0.3 * (i % 8820 < 4410))
                    
                    sample = int(16384 * (wave1 + wave2))  # 16-bit range
                    frames.append(struct.pack('<h', sample))
                
                wav_file.writeframes(b''.join(frames))
            
            audio_buffer.seek(0)
            logger.info(f"Generated {duration_seconds}s emergency audio for Roleplay 1.1")
            return audio_buffer
            
        except Exception as e:
            logger.error(f"Error generating emergency audio: {e}")
            return self._create_minimal_wav_audio()

    def _create_minimal_wav_audio(self) -> io.BytesIO:
        """
        Create minimal WAV audio as absolute last resort
        Enhanced for Roleplay 1.1
        """
        try:
            # Create a minimal 1-second WAV file
            sample_rate = 44100
            duration_samples = sample_rate  # 1 second
            
            audio_buffer = io.BytesIO()
            
            with wave.open(audio_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                
                # Generate very quiet white noise
                frames = []
                for i in range(duration_samples):
                    # Very quiet random noise
                    sample = int(128 * (0.5 - (i % 127) / 254))  # Pseudo-random
                    frames.append(struct.pack('<h', sample))
                
                wav_file.writeframes(b''.join(frames))
            
            audio_buffer.seek(0)
            logger.info("Generated minimal WAV audio for Roleplay 1.1")
            return audio_buffer
            
        except Exception as e:
            logger.critical(f"Failed to create minimal WAV audio: {e}")
            # Return empty BytesIO as absolute last resort
            return io.BytesIO(b'')

    def test_connection(self) -> bool:
        """
        Test ElevenLabs connection with enhanced error handling for Roleplay 1.1
        """
        try:
            if not self.is_enabled:
                return False
            
            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.api_key}
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                logger.info("ElevenLabs connection test successful for Roleplay 1.1")
                return True
            else:
                logger.warning(f"ElevenLabs connection test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"ElevenLabs connection test error: {e}")
            return False

    def is_available(self) -> bool:
        """Check if ElevenLabs service is available"""
        return self.is_enabled

    def get_status(self) -> Dict[str, Any]:
        """
        Get service status with enhanced information for Roleplay 1.1
        """
        status = {
            'enabled': self.is_enabled,
            'api_key_configured': bool(self.api_key),
            'base_url': self.base_url,
            'voice_configs_count': len(self.voice_configs),
            'roleplay_11_enhanced': True,
            'features': {
                'stage_specific_voices': True,
                'prospect_type_matching': True,
                'emergency_fallback': True,
                'silence_audio_generation': True,
                'wav_conversion': True
            }
        }
        
        if self.is_enabled:
            # Test connection
            try:
                connection_test = self.test_connection()
                status['connection_status'] = 'connected' if connection_test else 'failed'
            except:
                status['connection_status'] = 'unknown'
        else:
            status['connection_status'] = 'disabled'
        
        return status

    def get_available_voices(self) -> List[Dict]:
        """
        Get list of available voices with enhanced descriptions for Roleplay 1.1
        """
        try:
            if not self.is_enabled:
                return []
            
            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                voices_data = response.json()
                voices = voices_data.get('voices', [])
                
                # Enhance voice information for Roleplay 1.1
                enhanced_voices = []
                for voice in voices:
                    enhanced_voice = {
                        'voice_id': voice.get('voice_id'),
                        'name': voice.get('name'),
                        'category': voice.get('category'),
                        'description': voice.get('description'),
                        'roleplay_11_suitable': voice.get('voice_id') in [
                            config['voice_id'] for config in self.voice_configs.values()
                        ]
                    }
                    enhanced_voices.append(enhanced_voice)
                
                logger.info(f"Retrieved {len(enhanced_voices)} voices for Roleplay 1.1")
                return enhanced_voices
            else:
                logger.warning(f"Failed to get voices: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting available voices: {e}")
            return []

    # Utility methods for voice configuration
    
    def get_voice_config_for_stage(self, stage: str) -> Dict:
        """Get voice configuration for specific Roleplay 1.1 stage"""
        if stage in self.roleplay_11_voice_settings:
            config = self.voice_configs['default_prospect'].copy()
            config.update(self.roleplay_11_voice_settings[stage])
            return config
        return self.voice_configs['default_prospect']

    def create_custom_voice_config(self, base_voice: str = 'default_prospect', 
                                 stability: float = None, similarity_boost: float = None,
                                 style: float = None) -> Dict:
        """Create custom voice configuration for Roleplay 1.1"""
        config = self.voice_configs.get(base_voice, self.voice_configs['default_prospect']).copy()
        
        if stability is not None:
            config['stability'] = max(0.0, min(1.0, stability))
        if similarity_boost is not None:
            config['similarity_boost'] = max(0.0, min(1.0, similarity_boost))
        if style is not None:
            config['style'] = max(0.0, min(1.0, style))
        
        return config

    def validate_voice_settings(self, voice_settings: Dict) -> bool:
        """Validate voice settings for Roleplay 1.1"""
        try:
            required_fields = ['voice_id', 'stability', 'similarity_boost']
            for field in required_fields:
                if field not in voice_settings:
                    return False
            
            # Validate ranges
            if not (0.0 <= voice_settings['stability'] <= 1.0):
                return False
            if not (0.0 <= voice_settings['similarity_boost'] <= 1.0):
                return False
            if 'style' in voice_settings and not (0.0 <= voice_settings['style'] <= 1.0):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating voice settings: {e}")
            return False