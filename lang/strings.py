#!/usr/bin/env python3
# Sistema de idioma unificado para GrabText

import os
import sys
from typing import Dict, Any

# Diretório de idiomas
LANG_DIR = os.path.dirname(os.path.abspath(__file__))

class LanguageManager:
    def __init__(self, default_lang='pt'):
        self.default_lang = default_lang
        self.current_lang = default_lang
        self.strings = {}
        self.load_all_languages()
    
    def load_all_languages(self):
        """Carrega todos os arquivos de idioma disponíveis"""
        for lang_file in os.listdir(LANG_DIR):
            if (lang_file.endswith('.sh') and 
                lang_file != 'strings.py' and 
                not lang_file.startswith('ocr_')):  # Todos os arquivos .sh válidos
                
                lang_code = lang_file.replace('.sh', '')
                try:
                    # Carregar arquivo .sh como variáveis de ambiente
                    lang_file_path = os.path.join(LANG_DIR, lang_file)
                    strings = {}
                    
                    with open(lang_file_path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            line = line.strip()
                            # Ignorar comentários e linhas vazias
                            if line and not line.startswith('#') and '=' in line:
                                # Extrair variável no formato VAR="valor"
                                if '=' in line:
                                    var_name, var_value = line.split('=', 1)
                                    var_name = var_name.strip()
                                    var_value = var_value.strip()
                                    
                                    # Remover aspas se presentes
                                    if var_value.startswith('"') and var_value.endswith('"'):
                                        var_value = var_value[1:-1]
                                    elif var_value.startswith("'") and var_value.endswith("'"):
                                        var_value = var_value[1:-1]
                                    
                                    # Substituir \n por quebra de linha real
                                    var_value = var_value.replace('\\n', '\n')
                                    
                                    strings[var_name] = var_value
                    
                    if strings:
                        self.strings[lang_code] = strings
                    
                except Exception as e:
                    print(f"Warning: Could not load language file {lang_file}: {e}")
                    # Fallback: carregar strings hardcoded
                    if lang_code == 'pt':
                        self.strings[lang_code] = {
                            # Success messages
                            'MSG_TEXT_EXTRACTED_TITLE': "GrabText: Texto Extraído",
                            'MSG_TEXT_EXTRACTED_CONTENT': "Texto copiado para a área de transferência:\n\"{preview}\"",
                            'MSG_TEXT_SAVED_TITLE': "GrabText: Arquivo Salvo",
                            'MSG_TEXT_SAVED_CONTENT': "Arquivo salvo em:\n{path}",
                            'MSG_LANGUAGE_CHANGED_TITLE': "GrabText: Idioma Alterado",
                            'MSG_LANGUAGE_SET_SUCCESS': "Idioma alterado para: {lang}",
                            
                            # Processing messages
                            'MSG_PROCESSING_IMAGE_TITLE': "GrabText: Processando",
                            'MSG_PROCESSING_IMAGE_CONTENT': "Processando imagem...",
                            'MSG_LANGUAGE_INITIALIZED': "Idioma inicializado: current_lang_code={current_lang_code}, tesseract_lang_code={tesseract_lang_code}",
                            'MSG_LANGUAGE_OVERRIDDEN_FOR_PROCESS': "Idioma sobrescrito para comando process: {current_lang_code}",
                            'MSG_LANGUAGE_OVERRIDDEN_FOR_MONITOR': "Idioma sobrescrito para comando monitor: {current_lang_code}",
                            
                            # Error messages
                            'MSG_NO_TEXT_DETECTED_TITLE': "GrabText: Sem Texto",
                            'MSG_NO_TEXT_DETECTED_CONTENT': "Nenhum texto detectado na área selecionada.",
                            'MSG_GRABTEXT_ERROR_TITLE': "GrabText: Erro",
                            'MSG_GRABTEXT_ERROR_CONTENT': "Ocorreu um problema: {preview}",
                            'MSG_UNEXPECTED_ERROR_TITLE': "GrabText: Erro",
                            'MSG_UNEXPECTED_ERROR_CONTENT': "Ocorreu um problema inesperado: {preview}",
                            'MSG_ERROR_CLIPBOARD_INSTALL': "Falha ao copiar texto. Instale 'xclip' ou 'wl-copy'.",
                            'MSG_FILE_SAVE_ERROR': "Erro ao salvar arquivo: {error}",
                            'MSG_ERROR_PREFIX': "Erro: {message}",
                            
                            # Batch processing
                            'MSG_BATCH_COMPLETE_TITLE': "GrabText: Processamento em Lote",
                            'MSG_BATCH_COMPLETE_CONTENT': "Processamento concluído\nArquivos processados: {count}\nDiretório: {path}",
                            
                            # Monitoring
                            'MSG_WATCHING_DIRECTORY_TITLE': "GrabText: Monitoramento",
                            'MSG_WATCHING_DIRECTORY_CONTENT': "Monitorando diretório por novas imagens:\n{path}",
                            
                            # Status and info
                            'MSG_CURRENT_LANGUAGE_STATUS': "Idioma atual: {lang} ({lang_name})",
                            'MSG_AVAILABLE_LANGUAGES': "Idiomas disponíveis: pt, en",
                            
                            # Validation messages
                            'MSG_INVALID_PATH_PROVIDED': "Caminho inválido fornecido.",
                            'MSG_FILE_NOT_FOUND': "Arquivo não encontrado: {path}",
                            'MSG_PATH_NOT_FILE': "O caminho não é um arquivo: {path}",
                            'MSG_UNSUPPORTED_IMAGE_FORMAT': "Formato de imagem não suportado: {format}",
                            'MSG_IMAGE_TOO_LARGE': "Imagem muito grande: {size:.1f}MB (limite: 10MB)",
                            'MSG_CANNOT_READ_IMAGE': "Não foi possível ler a imagem: {error}",
                            'MSG_DIRECTORY_NOT_FOUND': "Diretório não encontrado: {path}",
                            'MSG_PATH_NOT_DIRECTORY': "O caminho não é um diretório: {path}",
                            'MSG_NO_READ_PERMISSION': "Sem permissão de leitura: {path}",
                            'MSG_NO_WRITE_PERMISSION': "Sem permissão de escrita: {path}",
                            'MSG_CANNOT_OVERWRITE_FILE': "Não foi possível sobrescrever o arquivo: {path}",
                            'MSG_PATH_NOT_FOUND': "Caminho não encontrado: {path}",
                            'MSG_INVALID_COMMAND_ERROR': "Erro: Comando inválido. Use 'grabtext help' para ver os comandos disponíveis.",
                            
                            # Dry run
                            'MSG_DRY_RUN_WOULD_PROCESS_IMAGE': "Dry run: Would process image '{path}'",
                            
                            # Logs
                            'MSG_NO_LOG_FILE_FOUND': "Arquivo de log não encontrado.",
                            'MSG_LOG_FILE_CLEARED': "Arquivo de log limpo.",
                            'MSG_LOGS_EXPORTED_TO': "Logs exportados para {export}",
                            
                            # Examples
                            'MSG_EXAMPLES_HEADER': "\nExemplos:",
                            'MSG_GRAB_EXAMPLE': "  grabtext grab              # Capturar da tela",
                            'MSG_PROCESS_IMAGE_EXAMPLE': "  grabtext grab -i imagem.png  # Processar arquivo de imagem"
                        }
                    elif lang_code == 'en':
                        self.strings[lang_code] = {
                            # Success messages
                            'MSG_TEXT_EXTRACTED_TITLE': "GrabText: Text Extracted",
                            'MSG_TEXT_EXTRACTED_CONTENT': "Text copied to clipboard:\n\"{preview}\"",
                            'MSG_TEXT_SAVED_TITLE': "GrabText: File Saved",
                            'MSG_TEXT_SAVED_CONTENT': "File saved to:\n{path}",
                            'MSG_LANGUAGE_CHANGED_TITLE': "GrabText: Language Changed",
                            'MSG_LANGUAGE_SET_SUCCESS': "Language set to: {lang}",
                            
                            # Processing messages
                            'MSG_PROCESSING_IMAGE_TITLE': "GrabText: Processing",
                            'MSG_PROCESSING_IMAGE_CONTENT': "Processing image...",
                            'MSG_LANGUAGE_INITIALIZED': "Language initialized: current_lang_code={current_lang_code}, tesseract_lang_code={tesseract_lang_code}",
                            'MSG_LANGUAGE_OVERRIDDEN_FOR_PROCESS': "Language overridden for process command: {current_lang_code}",
                            'MSG_LANGUAGE_OVERRIDDEN_FOR_MONITOR': "Language overridden for monitor command: {current_lang_code}",
                            
                            # Error messages
                            'MSG_NO_TEXT_DETECTED_TITLE': "GrabText: No Text",
                            'MSG_NO_TEXT_DETECTED_CONTENT': "No text detected in selected area.",
                            'MSG_GRABTEXT_ERROR_TITLE': "GrabText: Error",
                            'MSG_GRABTEXT_ERROR_CONTENT': "A problem occurred: {preview}",
                            'MSG_UNEXPECTED_ERROR_TITLE': "GrabText: Error",
                            'MSG_UNEXPECTED_ERROR_CONTENT': "An unexpected problem occurred: {preview}",
                            'MSG_ERROR_CLIPBOARD_INSTALL': "Failed to copy text. Please install 'xclip' or 'wl-copy'.",
                            'MSG_FILE_SAVE_ERROR': "Error saving file: {error}",
                            'MSG_ERROR_PREFIX': "Error: {message}",
                            
                            # Batch processing
                            'MSG_BATCH_COMPLETE_TITLE': "GrabText: Batch Processing",
                            'MSG_BATCH_COMPLETE_CONTENT': "Processing completed\nFiles processed: {count}\nDirectory: {path}",
                            
                            # Monitoring
                            'MSG_WATCHING_DIRECTORY_TITLE': "GrabText: Monitoring",
                            'MSG_WATCHING_DIRECTORY_CONTENT': "Monitoring directory for new images:\n{path}",
                            
                            # Status and info
                            'MSG_CURRENT_LANGUAGE_STATUS': "Current language: {lang} ({lang_name})",
                            'MSG_AVAILABLE_LANGUAGES': "Available languages: pt, en",
                            
                            # Validation messages
                            'MSG_INVALID_PATH_PROVIDED': "Invalid path provided.",
                            'MSG_FILE_NOT_FOUND': "File not found: {path}",
                            'MSG_PATH_NOT_FILE': "Path is not a file: {path}",
                            'MSG_UNSUPPORTED_IMAGE_FORMAT': "Unsupported image format: {format}",
                            'MSG_IMAGE_TOO_LARGE': "Image too large: {size:.1f}MB (limit: 10MB)",
                            'MSG_CANNOT_READ_IMAGE': "Cannot read image: {error}",
                            'MSG_DIRECTORY_NOT_FOUND': "Directory not found: {path}",
                            'MSG_PATH_NOT_DIRECTORY': "Path is not a directory: {path}",
                            'MSG_NO_READ_PERMISSION': "No read permission: {path}",
                            'MSG_NO_WRITE_PERMISSION': "No write permission: {path}",
                            'MSG_CANNOT_OVERWRITE_FILE': "Cannot overwrite file: {path}",
                            'MSG_PATH_NOT_FOUND': "Path not found: {path}",
                            'MSG_INVALID_COMMAND_ERROR': "Error: Invalid command. Use 'grabtext help' to see available commands.",
                            
                            # Dry run
                            'MSG_DRY_RUN_WOULD_PROCESS_IMAGE': "Dry run: Would process image '{path}'",
                            
                            # Logs
                            'MSG_NO_LOG_FILE_FOUND': "Log file not found.",
                            'MSG_LOG_FILE_CLEARED': "Log file cleared.",
                            'MSG_LOGS_EXPORTED_TO': "Logs exported to {export}",
                            
                            # Examples
                            'MSG_EXAMPLES_HEADER': "\nExamples:",
                            'MSG_GRAB_EXAMPLE': "  grabtext grab              # Capture from screen",
                            'MSG_PROCESS_IMAGE_EXAMPLE': "  grabtext grab -i image.png  # Process image file"
                        }
    
    def set_language(self, lang_code):
        """Define o idioma atual"""
        if lang_code in self.strings:
            self.current_lang = lang_code
            return True
        return False
    
    def get_string(self, key: str, **kwargs) -> str:
        """Obtém uma string formatada no idioma atual"""
        try:
            # Tentar obter no idioma atual
            template = self.strings.get(self.current_lang, {}).get(key)
            if not template:
                # Fallback para idioma padrão
                template = self.strings.get(self.default_lang, {}).get(key)
            
            if not template:
                # Se não encontrar, retornar a chave
                return key
            
            # Formatar com os argumentos fornecidos
            if kwargs:
                try:
                    return template.format(**kwargs)
                except (KeyError, ValueError) as e:
                    print(f"Warning: Error formatting string '{key}': {e}")
                    return template
            
            return template
            
        except Exception as e:
            print(f"Error getting string '{key}': {e}")
            return key
    
    def get_available_languages(self) -> list:
        """Retorna lista de idiomas disponíveis"""
        return list(self.strings.keys())

# Instância global do gerenciador de idiomas
_lang_manager = None

def get_lang_manager() -> LanguageManager:
    """Obtém a instância global do gerenciador de idiomas"""
    global _lang_manager
    if _lang_manager is None:
        _lang_manager = LanguageManager()
    return _lang_manager

def set_language(lang_code: str) -> bool:
    """Define o idioma global"""
    return get_lang_manager().set_language(lang_code)

def get_string(key: str, **kwargs) -> str:
    """Obtém uma string formatada no idioma atual"""
    return get_lang_manager().get_string(key, **kwargs)

# Função de conveniência para compatibilidade com código existente
def _(key: str, **kwargs) -> str:
    """Alias para get_string"""
    return get_string(key, **kwargs)
