#!/usr/bin/env python3
# Motores OCR alternativos para GrabText

import pytesseract
from PIL import Image
import logging
import subprocess
import tempfile
import os
from typing import Dict, Any, Optional

class BaseOCREngine:
    """Classe base para motores OCR"""
    
    def __init__(self, name: str):
        self.name = name
        self.available = False
    
    def is_available(self) -> bool:
        """Verifica se o motor OCR está disponível"""
        return self.available
    
    def extract_text(self, image: Image.Image, lang: str = 'eng') -> Dict[str, Any]:
        """Extrai texto da imagem"""
        raise NotImplementedError
    
    def get_supported_languages(self) -> list:
        """Retorna lista de idiomas suportados"""
        return []

class TesseractEngine(BaseOCREngine):
    """Motor OCR Tesseract (padrão)"""
    
    def __init__(self):
        super().__init__('tesseract')
        self.available = True
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            logging.warning(f"Tesseract not available: {e}")
            self.available = False
    
    def extract_text(self, image: Image.Image, lang: str = 'eng') -> Dict[str, Any]:
        """Extrai texto usando Tesseract"""
        try:
            # Obter dados OCR com confiança
            data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
            
            # Extrair texto
            text = pytesseract.image_to_string(image, lang=lang).strip()
            
            # Calcular confiança média
            confidences = [int(conf) for conf in data.get('conf', []) if conf and int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Contar palavras e caracteres
            word_count = len([word for word in data.get('text', []) if word and word.strip()])
            char_count = len(text) if text else 0
            
            return {
                'text': text,
                'word_count': word_count,
                'char_count': char_count,
                'avg_confidence': round(avg_confidence, 2),
                'language_used': lang,
                'has_text': bool(text),
                'engine': self.name,
                'success': True
            }
            
        except Exception as e:
            logging.error(f"Tesseract OCR error: {e}")
            return {
                'text': '',
                'word_count': 0,
                'char_count': 0,
                'avg_confidence': 0,
                'language_used': lang,
                'has_text': False,
                'engine': self.name,
                'success': False,
                'error': str(e)
            }
    
    def get_supported_languages(self) -> list:
        """Retorna idiomas suportados pelo Tesseract"""
        try:
            return pytesseract.get_languages(config='')
        except Exception:
            return ['eng', 'por']  # Fallback básico

class EasyOCREngine(BaseOCREngine):
    """Motor OCR EasyOCR (alternativa baseada em IA)"""
    
    def __init__(self):
        super().__init__('easyocr')
        self.reader = None
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Verifica se EasyOCR está disponível"""
        try:
            import easyocr
            # Tentar inicializar reader para verificar disponibilidade
            self.reader = easyocr.Reader(['en', 'pt'])
            return True
        except ImportError:
            logging.info("EasyOCR not available. Install with: pip install easyocr")
            return False
        except Exception as e:
            logging.warning(f"EasyOCR initialization failed: {e}")
            return False
    
    def extract_text(self, image: Image.Image, lang: str = 'eng') -> Dict[str, Any]:
        """Extrai texto usando EasyOCR"""
        if not self.is_available():
            return self._error_result(lang, "EasyOCR not available")
        
        try:
            import easyocr
            
            # Mapear idiomas para EasyOCR
            lang_map = {'eng': 'en', 'por': 'pt', 'spa': 'es', 'fra': 'fr', 'deu': 'de'}
            easyocr_lang = lang_map.get(lang, 'en')
            
            # Extrair texto
            results = self.reader.readtext(image, lang=[easyocr_lang])
            
            # Combinar todos os textos detectados
            text_parts = []
            total_confidence = 0
            word_count = 0
            
            for (bbox, detected_text, confidence) in results:
                if detected_text.strip():
                    text_parts.append(detected_text)
                    total_confidence += confidence
                    word_count += len(detected_text.split())
            
            text = ' '.join(text_parts)
            avg_confidence = total_confidence / len(results) if results else 0
            
            return {
                'text': text,
                'word_count': word_count,
                'char_count': len(text),
                'avg_confidence': round(avg_confidence * 100, 2),  # Converter para percentual
                'language_used': lang,
                'has_text': bool(text),
                'engine': self.name,
                'success': True,
                'detections': len(results)
            }
            
        except Exception as e:
            logging.error(f"EasyOCR error: {e}")
            return self._error_result(lang, str(e))
    
    def _error_result(self, lang: str, error: str) -> Dict[str, Any]:
        """Retorna resultado de erro padrão"""
        return {
            'text': '',
            'word_count': 0,
            'char_count': 0,
            'avg_confidence': 0,
            'language_used': lang,
            'has_text': False,
            'engine': self.name,
            'success': False,
            'error': error
        }
    
    def get_supported_languages(self) -> list:
        """Retorna idiomas suportados pelo EasyOCR"""
        return ['eng', 'por', 'spa', 'fra', 'deu', 'ita', 'rus', 'chi_sim', 'kor', 'jpn']

class GoogleCloudOCREngine(BaseOCREngine):
    """Motor OCR Google Cloud Vision"""
    
    def __init__(self):
        super().__init__('google_cloud')
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Verifica se Google Cloud Vision está disponível"""
        try:
            from google.cloud import vision
            # Verificar se há credenciais configuradas
            if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                return True
            else:
                logging.info("Google Cloud Vision requires GOOGLE_APPLICATION_CREDENTIALS environment variable")
                return False
        except ImportError:
            logging.info("Google Cloud Vision not available. Install with: pip install google-cloud-vision")
            return False
    
    def extract_text(self, image: Image.Image, lang: str = 'eng') -> Dict[str, Any]:
        """Extrai texto usando Google Cloud Vision"""
        if not self.is_available():
            return self._error_result(lang, "Google Cloud Vision not available")
        
        try:
            from google.cloud import vision
            
            # Mapear idiomas para Google Cloud Vision
            lang_map = {'eng': 'en', 'por': 'pt', 'spa': 'es', 'fra': 'fr', 'deu': 'de'}
            gcv_lang = lang_map.get(lang, 'en')
            
            # Converter imagem para bytes
            import io
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            content = img_byte_arr.getvalue()
            
            # Criar cliente e processar imagem
            client = vision.ImageAnnotatorClient()
            vision_image = vision.Image(content=content)
            
            response = client.text_detection(image=vision_image, image_context={'language_hints': [gcv_lang]})
            texts = response.text_annotations
            
            if texts:
                full_text = texts[0].description
                word_count = len(full_text.split())
                char_count = len(full_text)
                
                # Google Cloud não fornece confiança por palavra, mas sim por bloco
                avg_confidence = 0.95  # Estimativa conservadora
                
                return {
                    'text': full_text.strip(),
                    'word_count': word_count,
                    'char_count': char_count,
                    'avg_confidence': avg_confidence,
                    'language_used': lang,
                    'has_text': bool(full_text.strip()),
                    'engine': self.name,
                    'success': True,
                    'blocks_detected': len(texts) - 1  # Excluindo o texto completo
                }
            else:
                return self._empty_result(lang)
                
        except Exception as e:
            logging.error(f"Google Cloud Vision error: {e}")
            return self._error_result(lang, str(e))
    
    def _error_result(self, lang: str, error: str) -> Dict[str, Any]:
        """Retorna resultado de erro padrão"""
        return {
            'text': '',
            'word_count': 0,
            'char_count': 0,
            'avg_confidence': 0,
            'language_used': lang,
            'has_text': False,
            'engine': self.name,
            'success': False,
            'error': error
        }
    
    def _empty_result(self, lang: str) -> Dict[str, Any]:
        """Retorna resultado vazio"""
        return {
            'text': '',
            'word_count': 0,
            'char_count': 0,
            'avg_confidence': 0,
            'language_used': lang,
            'has_text': False,
            'engine': self.name,
            'success': True
        }
    
    def get_supported_languages(self) -> list:
        """Retorna idiomas suportados pelo Google Cloud Vision"""
        return ['eng', 'por', 'spa', 'fra', 'deu', 'ita', 'rus', 'chi_sim', 'chi_tra', 'kor', 'jpn', 'ar', 'hi', 'th', 'vi']

class OCREngineManager:
    """Gerenciador de motores OCR"""
    
    def __init__(self):
        self.engines = {
            'tesseract': TesseractEngine(),
            'easyocr': EasyOCREngine(),
            'google_cloud': GoogleCloudOCREngine()
        }
        self.default_engine = 'tesseract'
    
    def get_available_engines(self) -> Dict[str, BaseOCREngine]:
        """Retorna motores disponíveis"""
        return {name: engine for name, engine in self.engines.items() if engine.is_available()}
    
    def get_engine(self, engine_name: str = None) -> BaseOCREngine:
        """Obtém motor OCR específico"""
        if engine_name is None:
            engine_name = self.default_engine
        
        engine = self.engines.get(engine_name)
        if engine and engine.is_available():
            return engine
        
        # Fallback para Tesseract
        tesseract = self.engines.get('tesseract')
        if tesseract and tesseract.is_available():
            return tesseract
        
        # Se nenhum estiver disponível, retornar Tesseract mesmo que não funcione
        return self.engines.get('tesseract', TesseractEngine())
    
    def extract_text(self, image: Image.Image, lang: str = 'eng', engine_name: str = None) -> Dict[str, Any]:
        """Extrai texto usando o motor especificado"""
        engine = self.get_engine(engine_name)
        return engine.extract_text(image, lang)
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Retorna informações sobre motores disponíveis"""
        info = {}
        for name, engine in self.engines.items():
            info[name] = {
                'available': engine.is_available(),
                'supported_languages': engine.get_supported_languages() if engine.is_available() else []
            }
        return info

# Instância global do gerenciador
_ocr_manager = None

def get_ocr_manager() -> OCREngineManager:
    """Obtém instância global do gerenciador OCR"""
    global _ocr_manager
    if _ocr_manager is None:
        _ocr_manager = OCREngineManager()
    return _ocr_manager
