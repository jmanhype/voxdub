"""
NLLB Neural Translation Module
Handles multilingual translation with 200+ languages
"""

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch
from typing import Optional, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NLLBTranslator:
    """Professional NLLB translation with caching and optimization"""
    
    # NLLB-200 language code mappings
    LANG_CODES = {
        "en": "eng_Latn",
        "es": "spa_Latn",
        "fr": "fra_Latn",
        "de": "deu_Latn",
        "hi": "hin_Deva",
        "zh": "zho_Hans",
        "ja": "jpn_Jpan",
        "ko": "kor_Hang",
        "pt": "por_Latn",
        "ru": "rus_Cyrl",
        "ar": "arb_Arab",
        "it": "ita_Latn"
    }
    
    def __init__(self, model_name: str = "facebook/nllb-200-distilled-600M"):
        """
        Initialize NLLB translation model
        
        Args:
            model_name: HuggingFace model identifier
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = None
        self.model = None
        
        logger.info(f"Initializing NLLB translator on {self.device}")
    
    def load_model(self):
        """Load NLLB model and tokenizer"""
        if self.model is None:
            try:
                logger.info(f"Loading NLLB model: {self.model_name}")
                
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    use_fast=True
                )
                
                self.model = AutoModelForSeq2SeqLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                ).to(self.device)
                
                logger.info("✅ NLLB translation model loaded successfully")
                
            except Exception as e:
                logger.error(f"❌ Failed to load NLLB model: {e}")
                raise RuntimeError(f"NLLB model loading failed: {e}")
        
        return self.tokenizer, self.model
    
    def get_lang_code(self, lang: str) -> str:
        """Convert ISO code to NLLB format"""
        return self.LANG_CODES.get(lang.lower(), f"{lang}_Latn")
    
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        max_length: int = 512
    ) -> str:
        """
        Translate text between languages
        
        Args:
            text: Source text to translate
            source_lang: Source language code (e.g., 'en')
            target_lang: Target language code (e.g., 'es')
            max_length: Maximum output length
        
        Returns:
            Translated text
        """
        try:
            if not text or not text.strip():
                raise ValueError("Empty text provided for translation")
            
            tokenizer, model = self.load_model()
            
            # Convert language codes
            src_code = self.get_lang_code(source_lang)
            tgt_code = self.get_lang_code(target_lang)
            
            logger.info(f"Translating: {source_lang} → {target_lang}")
            logger.info(f"Input length: {len(text)} characters")
            
            # Tokenize input
            inputs = tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max_length
            ).to(self.device)
            
            # Generate translation
            with torch.no_grad():
                translated_tokens = model.generate(
                    **inputs,
                    forced_bos_token_id=tokenizer.lang_code_to_id[tgt_code],
                    max_length=max_length,
                    num_beams=5,  # Beam search for better quality
                    early_stopping=True
                )
            
            # Decode translation
            translated_text = tokenizer.decode(
                translated_tokens[0],
                skip_special_tokens=True
            )
            
            logger.info(f"✅ Translation complete")
            logger.info(f"   Output length: {len(translated_text)} characters")
            
            return translated_text
            
        except Exception as e:
            logger.error(f"❌ Translation failed: {e}")
            logger.warning("⚠️  Returning original text")
            return text  # Fallback to original text

# Global instance
_translator = None

def get_translator() -> NLLBTranslator:
    """Get or create global translator instance"""
    global _translator
    if _translator is None:
        _translator = NLLBTranslator()
    return _translator

def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """
    Convenience function for translation
    
    Args:
        text: Text to translate
        source_lang: Source language code
        target_lang: Target language code
    
    Returns:
        Translated text
    """
    translator = get_translator()
    return translator.translate(text, source_lang, target_lang)
