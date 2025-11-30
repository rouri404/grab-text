#!/usr/bin/env python3
# Módulo de validação e score de confiança de texto para GrabText

import re
import logging
from typing import Dict, Any, List, Tuple
from collections import Counter

class TextValidator:
    """Validador de texto extraído com cálculo de score de confiança"""
    
    def __init__(self, language='pt'):
        self.language = language
        self.min_confidence_threshold = 30.0  # Mínimo 30% de confiança
        self.min_text_length = 3  # Mínimo 3 caracteres
        
        # Padrões de validação por idioma
        self.patterns = {
            'pt': {
                'words': r'[a-zA-Zá-úÁ-Úç-Ç]+',
                'numbers': r'\b\d+(?:[.,]\d+)?\b',
                'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'url': r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?',
                'phone': r'(?:\+?55\s?)?(?:\(?[1-9]{2}\)?\s?)?(?:9?\s?\d{4}[-.\s]?\d{4})',
                'currency': r'R\$\s*\d+(?:[.,]\d{2})?',
                'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'
            },
            'en': {
                'words': r'[a-zA-Z]+',
                'numbers': r'\b\d+(?:[.,]\d+)?\b',
                'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'url': r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?',
                'phone': r'(?:\+?1\s?)?(?:\(?[0-9]{3}\)?\s?)?[0-9]{3}[-.\s]?[0-9]{4}',
                'currency': r'\$\s*\d+(?:[.,]\d{2})?',
                'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'
            }
        }
    
    def validate_text(self, text: str, ocr_confidence: float = 0.0) -> Dict[str, Any]:
        """Valida texto e calcula score de confiança"""
        if not text or not text.strip():
            return self._empty_result()
        
        text = text.strip()
        
        # Análise básica
        basic_analysis = self._analyze_basic_properties(text)
        
        # Análise de padrões
        pattern_analysis = self._analyze_patterns(text)
        
        # Análise de qualidade
        quality_analysis = self._analyze_quality(text)
        
        # Calcular score final
        final_score = self._calculate_final_score(
            ocr_confidence, basic_analysis, pattern_analysis, quality_analysis
        )
        
        # Validação final
        is_valid = self._is_text_valid(final_score, basic_analysis)
        
        return {
            'text': text,
            'is_valid': is_valid,
            'final_score': final_score,
            'ocr_confidence': ocr_confidence,
            'basic_analysis': basic_analysis,
            'pattern_analysis': pattern_analysis,
            'quality_analysis': quality_analysis,
            'recommendations': self._get_recommendations(final_score, basic_analysis, quality_analysis)
        }
    
    def _analyze_basic_properties(self, text: str) -> Dict[str, Any]:
        """Análise básica das propriedades do texto"""
        words = text.split()
        char_count = len(text)
        word_count = len(words)
        
        # Contar diferentes tipos de caracteres
        letters = sum(1 for c in text if c.isalpha())
        numbers = sum(1 for c in text if c.isdigit())
        spaces = sum(1 for c in text if c.isspace())
        punctuation = sum(1 for c in text if not c.isalnum() and not c.isspace())
        
        # Calcular proporções
        if char_count > 0:
            letter_ratio = letters / char_count
            number_ratio = numbers / char_count
            space_ratio = spaces / char_count
            punctuation_ratio = punctuation / char_count
        else:
            letter_ratio = number_ratio = space_ratio = punctuation_ratio = 0
        
        # Comprimento médio das palavras
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
        
        return {
            'char_count': char_count,
            'word_count': word_count,
            'letter_count': letters,
            'number_count': numbers,
            'space_count': spaces,
            'punctuation_count': punctuation,
            'letter_ratio': letter_ratio,
            'number_ratio': number_ratio,
            'space_ratio': space_ratio,
            'punctuation_ratio': punctuation_ratio,
            'avg_word_length': avg_word_length,
            'longest_word': max(words, key=len) if words else '',
            'shortest_word': min(words, key=len) if words else ''
        }
    
    def _analyze_patterns(self, text: str) -> Dict[str, Any]:
        """Análise de padrões no texto"""
        patterns = self.patterns.get(self.language, self.patterns['en'])
        results = {}
        
        for pattern_name, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            results[pattern_name] = {
                'count': len(matches),
                'matches': matches[:5]  # Limitar para economizar espaço
            }
        
        # Detectar palavras comuns (stopwords)
        common_words = self._get_common_words()
        words = re.findall(patterns['words'], text.lower())
        stopword_count = sum(1 for word in words if word in common_words)
        
        results['common_words'] = {
            'count': stopword_count,
            'ratio': stopword_count / len(words) if words else 0
        }
        
        return results
    
    def _analyze_quality(self, text: str) -> Dict[str, Any]:
        """Análise da qualidade do texto"""
        # Detectar caracteres suspeitos
        suspicious_chars = re.findall(r'[^\w\s\.,!?;:()\-"\'+@#$%&*=<>/\\|`~\[\]{}]', text)
        
        # Detectar repetições excessivas
        repeated_chars = re.findall(r'(.)\1{3,}', text)
        
        # Detectar palavras com caracteres misturados (possíveis erros OCR)
        mixed_case_words = []
        for word in text.split():
            if len(word) > 3 and any(c.islower() for c in word) and any(c.isupper() for c in word):
                mixed_case_words.append(word)
        
        # Detectar espaços irregulares
        multiple_spaces = re.findall(r' {2,}', text)
        irregular_spacing = len(multiple_spaces) > 0
        
        # Calcular score de legibilidade (simplificado)
        readability_score = self._calculate_readability(text)
        
        return {
            'suspicious_chars': {
                'count': len(suspicious_chars),
                'chars': list(set(suspicious_chars))
            },
            'repeated_chars': {
                'count': len(repeated_chars),
                'patterns': repeated_chars[:5]
            },
            'mixed_case_words': {
                'count': len(mixed_case_words),
                'words': mixed_case_words[:5]
            },
            'irregular_spacing': irregular_spacing,
            'readability_score': readability_score
        }
    
    def _calculate_final_score(self, ocr_confidence: float, basic: Dict, patterns: Dict, quality: Dict) -> float:
        """Calcula score final de confiança"""
        score = 0.0
        
        # Peso da confiança OCR (40%)
        ocr_score = min(ocr_confidence / 100, 1.0) * 40
        score += ocr_score
        
        # Peso da análise básica (30%)
        basic_score = 0
        if basic['char_count'] >= self.min_text_length:
            basic_score += 10  # Texto com tamanho mínimo
        if basic['word_count'] >= 1:
            basic_score += 10  # Tem pelo menos uma palavra
        if 0.3 <= basic['letter_ratio'] <= 0.9:  # Proporção razoável de letras
            basic_score += 10
        score += basic_score
        
        # Peso dos padrões (20%)
        pattern_score = 0
        if patterns['common_words']['ratio'] > 0.1:  # Tem palavras comuns
            pattern_score += 5
        if patterns['words']['count'] > 0:
            pattern_score += 5
        if patterns['numbers']['count'] > 0:
            pattern_score += 5
        if patterns['email']['count'] > 0 or patterns['url']['count'] > 0:
            pattern_score += 5
        score += pattern_score
        
        # Peso da qualidade (10%)
        quality_score = 0
        if quality['suspicious_chars']['count'] == 0:
            quality_score += 3
        if quality['repeated_chars']['count'] == 0:
            quality_score += 3
        if not quality['irregular_spacing']:
            quality_score += 2
        if quality['readability_score'] > 50:
            quality_score += 2
        score += quality_score
        
        return min(score, 100.0)  # Limitar a 100%
    
    def _is_text_valid(self, final_score: float, basic: Dict) -> bool:
        """Determina se o texto é válido"""
        if final_score < self.min_confidence_threshold:
            return False
        if basic['char_count'] < self.min_text_length:
            return False
        if basic['word_count'] == 0:
            return False
        return True
    
    def _get_recommendations(self, score: float, basic: Dict, quality: Dict) -> List[str]:
        """Gera recomendações para melhorar o texto"""
        recommendations = []
        
        if score < 30:
            recommendations.append("Texto muito baixa qualidade. Consiste em capturar novamente.")
        elif score < 50:
            recommendations.append("Qualidade baixa. Tente pré-processamento da imagem.")
        elif score < 70:
            recommendations.append("Qualidade razoável. Pode haver alguns erros.")
        
        if quality['suspicious_chars']['count'] > 0:
            recommendations.append("Verificar caracteres incomuns detectados.")
        
        if quality['repeated_chars']['count'] > 0:
            recommendations.append("Possíveis erros de OCR em caracteres repetidos.")
        
        if quality['mixed_case_words']['count'] > 0:
            recommendations.append("Verificar palavras com maiúsculas/minúsculas misturadas.")
        
        if quality['irregular_spacing']:
            recommendations.append("Verificar espaçamento irregular no texto.")
        
        if basic['letter_ratio'] < 0.3:
            recommendations.append("Texto com poucas letras. Pode ser principalmente números ou símbolos.")
        
        return recommendations
    
    def _calculate_readability(self, text: str) -> float:
        """Calcula score de legibilidade simplificado"""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        
        if not words or not sentences:
            return 0
        
        avg_words_per_sentence = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Fórmula simplificada baseada em Flesch Reading Ease
        readability = 100 - (avg_words_per_sentence * 1.5) - (avg_word_length * 10)
        return max(0, min(100, readability))
    
    def _get_common_words(self) -> set:
        """Retorna palavras comuns por idioma"""
        if self.language == 'pt':
            return {'o', 'a', 'os', 'as', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 'nos', 'nas', 
                   'por', 'para', 'com', 'sem', 'como', 'mais', 'menos', 'muito', 'pouco', 'que', 'quem', 
                   'qual', 'quando', 'onde', 'como', 'porque', 'mas', 'e', 'ou', 'se', 'não', 'sim', 'um', 
                   'uma', 'uns', 'umas', 'este', 'esta', 'isto', 'esse', 'essa', 'isso', 'aquele', 'aquela', 'aquilo'}
        else:  # inglês
            return {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 
                   'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 
                   'below', 'between', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 
                   'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 
                   'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 
                   'too', 'very', 'can', 'will', 'just', 'don', 'should', 'now'}
    
    def _empty_result(self) -> Dict[str, Any]:
        """Retorna resultado vazio para texto inválido"""
        return {
            'text': '',
            'is_valid': False,
            'final_score': 0.0,
            'ocr_confidence': 0.0,
            'basic_analysis': {},
            'pattern_analysis': {},
            'quality_analysis': {},
            'recommendations': ['Nenhum texto detectado']
        }

class ConfidenceThresholdManager:
    """Gerenciador de thresholds de confiança"""
    
    def __init__(self):
        self.thresholds = {
            'very_low': 20.0,
            'low': 40.0,
            'medium': 60.0,
            'high': 80.0,
            'very_high': 95.0
        }
    
    def get_threshold_level(self, confidence: float) -> str:
        """Retorna nível de confiança"""
        if confidence < self.thresholds['very_low']:
            return 'very_low'
        elif confidence < self.thresholds['low']:
            return 'low'
        elif confidence < self.thresholds['medium']:
            return 'medium'
        elif confidence < self.thresholds['high']:
            return 'high'
        else:
            return 'very_high'
    
    def should_retry(self, confidence: float) -> bool:
        """Determina se deve tentar novamente com diferentes configurações"""
        return confidence < self.thresholds['medium']
    
    def get_preprocessing_suggestion(self, confidence: float) -> str:
        """Sugere tipo de pré-processamento baseado na confiança"""
        if confidence < self.thresholds['very_low']:
            return 'low_quality'
        elif confidence < self.thresholds['low']:
            return 'text_enhancement'
        elif confidence < self.thresholds['medium']:
            return 'document_scan'
        else:
            return 'none'
