#!/usr/bin/env python3
# Mapeamento de idiomas OCR para GrabText

# Mapeamento de códigos de idioma para códigos Tesseract
OCR_LANGUAGE_MAPPING = {
    # Idiomas principais
    'pt': 'por',      # Português
    'en': 'eng',      # Inglês
    'es': 'spa',      # Espanhol
    'fr': 'fra',      # Francês
    'de': 'deu',      # Alemão
    'it': 'ita',      # Italiano
    
    # Idiomas asiáticos
    'zh': 'chi_sim',  # Chinês (Simplificado)
    'zh-tw': 'chi_tra', # Chinês (Tradicional)
    'ja': 'jpn',      # Japonês
    'ko': 'kor',      # Coreano
    
    # Outros idiomas europeus
    'ru': 'rus',      # Russo
    'nl': 'nld',      # Holandês
    'sv': 'swe',      # Sueco
    'no': 'nor',      # Norueguês
    'da': 'dan',      # Dinamarquês
    'fi': 'fin',      # Finlandês
    'pl': 'pol',      # Polonês
    'cs': 'ces',      # Tcheco
    'hu': 'hun',      # Húngaro
    'ro': 'ron',      # Romeno
    'bg': 'bul',      # Búlgaro
    'hr': 'hrv',      # Croata
    'sk': 'slk',      # Eslovaco
    'sl': 'slv',      # Esloveno
    
    # Idiomas do Oriente Médio
    'ar': 'ara',      # Árabe
    'he': 'heb',      # Hebraico
    'fa': 'fas',      # Persa (Farsi)
    'ur': 'urd',      # Urdu
    'hi': 'hin',      # Hindi
    'th': 'tha',      # Tailandês
    'vi': 'vie',      # Vietnamita
    
    # Outros
    'tr': 'tur',      # Turco
    'el': 'ell',      # Grego
    'uk': 'ukr',      # Ucraniano
    'et': 'est',      # Estoniano
    'lv': 'lav',      # Letão
    'lt': 'lit',      # Lituano
}

# Nomes de idiomas em português
LANGUAGE_NAMES_PT = {
    'pt': 'Português',
    'en': 'Inglês',
    'es': 'Espanhol',
    'fr': 'Francês',
    'de': 'Alemão',
    'it': 'Italiano',
    'zh': 'Chinês (Simplificado)',
    'zh-tw': 'Chinês (Tradicional)',
    'ja': 'Japonês',
    'ko': 'Coreano',
    'ru': 'Russo',
    'nl': 'Holandês',
    'sv': 'Sueco',
    'no': 'Norueguês',
    'da': 'Dinamarquês',
    'fi': 'Finlandês',
    'pl': 'Polonês',
    'cs': 'Tcheco',
    'hu': 'Húngaro',
    'ro': 'Romeno',
    'bg': 'Búlgaro',
    'hr': 'Croata',
    'sk': 'Eslovaco',
    'sl': 'Eslovaco',
    'ar': 'Árabe',
    'he': 'Hebraico',
    'fa': 'Persa',
    'ur': 'Urdu',
    'hi': 'Hindi',
    'th': 'Tailandês',
    'vi': 'Vietnamita',
    'tr': 'Turco',
    'el': 'Grego',
    'uk': 'Ucraniano',
    'et': 'Estoniano',
    'lv': 'Letão',
    'lt': 'Lituano',
}

# Nomes de idiomas em inglês
LANGUAGE_NAMES_EN = {
    'pt': 'Portuguese',
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'zh': 'Chinese (Simplified)',
    'zh-tw': 'Chinese (Traditional)',
    'ja': 'Japanese',
    'ko': 'Korean',
    'ru': 'Russian',
    'nl': 'Dutch',
    'sv': 'Swedish',
    'no': 'Norwegian',
    'da': 'Danish',
    'fi': 'Finnish',
    'pl': 'Polish',
    'cs': 'Czech',
    'hu': 'Hungarian',
    'ro': 'Romanian',
    'bg': 'Bulgarian',
    'hr': 'Croatian',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'ar': 'Arabic',
    'he': 'Hebrew',
    'fa': 'Persian',
    'ur': 'Urdu',
    'hi': 'Hindi',
    'th': 'Thai',
    'vi': 'Vietnamese',
    'tr': 'Turkish',
    'el': 'Greek',
    'uk': 'Ukrainian',
    'et': 'Estonian',
    'lv': 'Latvian',
    'lt': 'Lithuanian',
}

def get_tesseract_lang_code(lang_code):
    """Converte código de idioma para código Tesseract"""
    return OCR_LANGUAGE_MAPPING.get(lang_code, lang_code)

def get_language_name(lang_code, interface_lang='pt'):
    """Obtém nome do idioma no idioma da interface"""
    if interface_lang == 'pt':
        return LANGUAGE_NAMES_PT.get(lang_code, lang_code.upper())
    else:
        return LANGUAGE_NAMES_EN.get(lang_code, lang_code.upper())

def get_available_languages():
    """Retorna lista de idiomas disponíveis"""
    return list(OCR_LANGUAGE_MAPPING.keys())

def is_language_supported(lang_code):
    """Verifica se idioma é suportado"""
    return lang_code in OCR_LANGUAGE_MAPPING
