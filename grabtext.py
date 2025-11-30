#!/usr/bin/env python3
# grabtext.py

import sys
import io
import tempfile
import subprocess
import pytesseract
from PIL import Image
import os
import logging
import threading
import time
from collections import defaultdict
import argparse
import json
import csv
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Importar sistema de idioma unificado
try:
    from lang.strings import get_string, set_language, get_lang_manager
except ImportError:
    # Fallback se não conseguir importar strings
    def get_string(key, **kwargs):
        return key.format(**kwargs) if kwargs else key
    def set_language(lang):
        return False
    class DummyManager:
        def get_available_languages(self):
            return ['pt', 'en']
    def get_lang_manager():
        return DummyManager()

# Importar módulos de idioma OCR
try:
    from lang.ocr_languages import get_tesseract_lang_code, get_language_name, get_available_languages, is_language_supported
except ImportError:
    def get_tesseract_lang_code(lang):
        return 'por' if lang == 'pt' else 'eng'
    def get_language_name(lang, interface_lang='pt'):
        return lang.upper()
    def get_available_languages():
        return ['pt', 'en']
    def is_language_supported(lang):
        return lang in ['pt', 'en']

# Importar processador de imagem
try:
    from image_processor import ImageProcessor, get_preset_text_enhancement, get_preset_low_quality, CV2_AVAILABLE
except ImportError:
    CV2_AVAILABLE = False
    class ImageProcessor:
        def preprocess(self, img):
            return img

# Importar motores OCR
try:
    from ocr_engines import get_ocr_manager
except ImportError:
    class DummyOCRManager:
        def extract_text(self, img, lang='eng', engine_name=None):
            return {'text': '', 'word_count': 0, 'char_count': 0, 'avg_confidence': 0, 'language_used': lang, 'has_text': False, 'engine': 'tesseract', 'success': False}
        def get_engine_info(self):
            return {'tesseract': {'available': True, 'supported_languages': ['eng', 'por']}}
    def get_ocr_manager():
        return DummyOCRManager()

# Importar validador de texto
try:
    from text_validator import TextValidator, ConfidenceThresholdManager
except ImportError:
    class TextValidator:
        def validate_text(self, text, ocr_confidence=0.0):
            return {'text': text, 'is_valid': bool(text), 'final_score': ocr_confidence, 'recommendations': []}
    class ConfidenceThresholdManager:
        def get_threshold_level(self, confidence):
            return 'medium' if confidence > 50 else 'low'

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, 'grabtext.log')
CONFIG_FILE = os.path.join(SCRIPT_DIR, '.grabtext_config')

VERSION = "1.3.3"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s'
)

# Funções de configuração devem ser definidas antes de initialize_language()
def load_config():
    """Carrega configuração do arquivo"""
    config = {'language': 'pt'}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and '=' in line:
                        try:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
                        except ValueError:
                            logging.warning(f"Invalid config format at line {line_num}: {line}")
        except (IOError, OSError) as e:
            logging.warning(f"Error reading config file: {e}")
        except UnicodeDecodeError as e:
            logging.warning(f"Config file encoding error: {e}")
    return config

def save_config(config):
    """Salva configuração no arquivo"""
    try:
        # Criar backup do arquivo existente
        if os.path.exists(CONFIG_FILE):
            backup_file = CONFIG_FILE + '.backup'
            try:
                import shutil
                shutil.copy2(CONFIG_FILE, backup_file)
            except (IOError, OSError) as e:
                logging.warning(f"Could not create config backup: {e}")
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            for key, value in config.items():
                if isinstance(key, str) and isinstance(value, str):
                    f.write(f"{key.strip()}={value.strip()}\n")
        return True
    except (IOError, OSError) as e:
        logging.error(f"Error writing config file: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error saving config: {e}")
        return False

# Inicialização da linguagem deve ser chamada após as funções de configuração
def initialize_language():
    global current_lang_code, tesseract_lang_code
    config = load_config()
    current_lang_code = os.environ.get('GRABTEXT_LANG', config.get('language', 'pt')).lower()
    tesseract_lang_code = get_tesseract_lang_code(current_lang_code)
    
    # Configurar idioma no sistema unificado
    try:
        set_language(current_lang_code)
    except:
        pass  # Fallback silencioso
    
    logging.debug(get_string('MSG_LANGUAGE_INITIALIZED', current_lang_code=current_lang_code, tesseract_lang_code=tesseract_lang_code))

# Inicializar variáveis globais de idioma
current_lang_code = 'pt'  # Valor padrão
tesseract_lang_code = 'por'  # Valor padrão

# get_message deve ser definida antes dos dicionários de mensagens que a utilizam
def get_message(key, **kwargs):
    """Função de compatibilidade com código existente"""
    return get_string(f'MSG_{key.upper()}', **kwargs)

# Dicionários de mensagens devem vir após initialize_language() e get_message()
LOG_MESSAGES = {
    'SESSION_START': "Session started.",
    'NO_IMAGE_DATA': "No image data received from stdin.",
    'OCR_SUCCESS': "OCR success: lang={lang}, chars={chars}, text=\"{text}\"",
    'OCR_NO_TEXT': "OCR complete: No text detected.",
    'CLIPBOARD_ERROR': "Clipboard tool not found (xclip/wl-copy).",
    'NOTIFY_SEND_MISSING': "notify-send command not found.",
    'NOTIFY_SEND_ERROR': "notify-send command failed: {e}",
    'UNEXPECTED_ERROR': "Unexpected error: {e}",
}

MESSAGES = {
    'pt': {
        'error_clipboard_install': "Falha ao copiar texto. Instale 'xclip' ou 'wl-copy'.",
        'grabtext_error_title': "GrabText: Erro",
        'text_extracted_title': "GrabText: Texto Extraído",
        'text_extracted_content': "Texto copiado para a área de transferência:\n\"{preview}\"",
        'text_saved_title': "GrabText: Arquivo Salvo",
        'text_saved_content': "Arquivo salvo em:\n{path}",
        'no_text_detected_title': "GrabText: Sem Texto",
        'no_text_detected_content': "Nenhum texto detectado na área selecionada.",
        'processing_image_title': "GrabText: Processando",
        'processing_image_content': "Processando imagem...",
        'watching_directory_title': "GrabText: Monitoramento",
        'watching_directory_content': "Monitorando diretório por novas imagens:\n{path}",
        'unexpected_error_title': "GrabText: Erro",
        'unexpected_error_content': "Ocorreu um problema: {preview}",
        'batch_complete_title': "GrabText: Processamento em Lote",
        'batch_complete_content': "Processamento concluído\nArquivos processados: {count}\nDiretório: {path}",
        'invalid_command_error': "Erro: Comando inválido. Use 'grabtext help' para ver os comandos disponíveis.",
        'examples_header': "\nExemplos:",
        'grab_example': "  grabtext grab              # Capturar da tela",
        'process_image_example': "  grabtext grab -i imagem.png  # Processar arquivo de imagem",
        'language_name_pt': "Português",
        'language_name_en': "Inglês",
        'current_language_status': "Idioma atual: {lang} ({lang_name})",
        'set_lang_usage': "Uso: grabtext set-lang <idioma>",
        'available_languages': "Idiomas disponíveis: pt, en",
        'language_set_success': "Idioma definido com sucesso para {lang}",
        'language_changed_title': "GrabText: Idioma Alterado",
        'error_prefix': "Erro: {message}",
        'no_log_file_found': "Arquivo de log não encontrado.",
        'log_file_cleared': "Arquivo de log limpo.",
        'logs_exported_to': "Logs exportados para {export}",
        'debug_mode_enabled': "Modo depuração ativado",
        'verbose_mode_enabled': "Modo detalhado ativado",
        'configuration_header': "Configuração:",
        'version_label': "  Versão: {version}",
        'language_label': "  Idioma: {lang}",
        'log_file_label': "  Arquivo de log: {log_file}",
        'debug_mode_label': "  Modo depuração: {status}",
        'verbose_mode_label': "  Modo detalhado: {status}",
        'enabled_status': 'ativado',
        'disabled_status': 'desativado',
        'path_not_found': "Caminho não encontrado: {path}",
        'file_save_error': "Erro ao salvar arquivo: {error}"
    },
    'en': {
        'error_clipboard_install': "Failed to copy text. Please install 'xclip' or 'wl-copy'.",
        'grabtext_error_title': "GrabText: Error",
        'text_extracted_title': "GrabText: Text Extracted",
        'text_extracted_content': "Text copied to clipboard:\n\"{preview}\"",
        'text_saved_title': "GrabText: File Saved",
        'text_saved_content': "File saved at:\n{path}",
        'no_text_detected_title': "GrabText: No Text",
        'no_text_detected_content': "No text detected in the selected area.",
        'processing_image_title': "GrabText: Processing",
        'processing_image_content': "Processing image...",
        'watching_directory_title': "GrabText: Watching",
        'watching_directory_content': "Monitoring directory for new images:\n{path}",
        'unexpected_error_title': "GrabText: Error",
        'unexpected_error_content': "An error occurred: {preview}",
        'batch_complete_title': "GrabText: Batch Processing",
        'batch_complete_content': "Processing complete\nFiles processed: {count}\nDirectory: {path}",
        'invalid_command_error': "Error: Invalid command. Use 'grabtext help' to see available commands.",
        'examples_header': "\nExamples:",
        'grab_example': "  grabtext grab              # Capture from screen",
        'process_image_example': "  grabtext grab -i image.png  # Process image file",
        'language_name_pt': "Portuguese",
        'language_name_en': "English",
        'current_language_status': "Current language: {lang} ({lang_name})",
        'set_lang_usage': "Usage: grabtext set-lang <language>",
        'available_languages': "Available languages: pt, en",
        'language_set_success': "Language successfully set to {lang}",
        'language_changed_title': "GrabText: Language Changed",
        'error_prefix': "Error: {message}",
        'no_log_file_found': "No log file found.",
        'log_file_cleared': "Log file cleared.",
        'logs_exported_to': "Logs exported to {export}",
        'debug_mode_enabled': "Debug mode enabled",
        'verbose_mode_enabled': "Verbose mode enabled",
        'configuration_header': "Configuration:",
        'version_label': "  Version: {version}",
        'language_label': "  Language: {lang}",
        'log_file_label': "  Log file: {log_file}",
        'debug_mode_label': "  Debug mode: {status}",
        'verbose_mode_label': "  Verbose mode: {status}",
        'enabled_status': 'enabled',
        'disabled_status': 'disabled',
        'path_not_found': "Path not found: {path}",
        'file_save_error': "Error saving file: {error}"
    }
}

HELP_MESSAGES = {
    'en': """
╭─────────────────────────────────────────────────╮
│                   GrabText                      │
│        Text extraction tool for Linux           │
╰─────────────────────────────────────────────────╯

Usage:
  grabtext <command> [options]

Global Options:
  --debug                 Enable debug mode with verbose output
  --verbose               Show detailed progress information
  --config                Show current configuration
  --version               Display version information

Main Commands:
  grab                    Capture text from screen area
    -l, --lang            Language for OCR (pt/en)
    -o, --output          Save to file
    -s, --silent          No notifications
    --no-clipboard        Don't copy to clipboard
    --dry-run             Show what would be done

  process <path>          Process existing images or directories
    -l, --lang            Language for OCR (pt/en)
    -o, --output          Save to file
    -f, --format          Output format (text/json/csv)
    -r, --recursive       Process directory recursively
    --batch               Process multiple images
    -s, --silent          No notifications
    --no-clipboard        Don't copy to clipboard
    --dry-run             Show what would be done

  monitor <directory>     Monitor directory for new images
    -l, --lang            Language for OCR (pt/en)
    -f, --format          Output format (text/json/csv)
    -r, --recursive       Monitor recursively
    -o, --output          Save to file
    -s, --silent          No notifications
    --no-clipboard        Don't copy to clipboard

Utility Commands:
  logs                    Manage log files
    --tail N              Show last N lines
    --since DATE          Show logs since date (YYYY-MM-DD)
    --until DATE          Show logs until date
    --errors              Show only errors
    --filter TEXT         Filter logs by text
    --export FILE         Export logs to file
    --clear               Clear log file

  status                  Show system status and dependencies
  config                  Show current configuration
  get-lang                Show current language
  set-lang <lang>         Set global language (pt/en)
  help                    Show this help message
  version                 Show version information

Examples:
  grabtext grab                           # Capture from screen
  grabtext process image.png              # Process single image
  grabtext process ./images -r            # Process directory recursively
  grabtext monitor ./images               # Monitor directory
  grabtext logs --tail 10                 # Show last 10 log entries
  grabtext status                         # Show system status
  grabtext get-lang                       # Show current language
  grabtext set-lang en                    # Set language to English

For more information, visit:
https://github.com/rouri404/grabtext

Made by Gabriel Couto Ribeiro (rouri404) - 2025
""",
    'pt': """
╭─────────────────────────────────────────────────╮
│                   GrabText                      │
│     Ferramenta de extração de texto Linux       │
╰─────────────────────────────────────────────────╯

Uso:
  grabtext <comando> [opções]

Opções Globais:
  --debug                 Ativar modo de depuração com saída detalhada
  --verbose               Mostrar informações detalhadas de progresso
  --config                Mostrar configuração atual
  --version               Exibir informações de versão

Main Commands:
  grab                    Capturar texto da área da tela
    -l, --lang            Idioma para OCR (pt/en)
    -o, --output          Salvar em arquivo
    -s, --silent          Sem notificações
    --no-clipboard        Não copiar para área de transferência
    --dry-run             Mostrar o que seria feito

  process <caminho>       Processar imagens ou diretórios existentes
    -l, --lang            Idioma para OCR (pt/en)
    -o, --output          Salvar em arquivo
    -f, --format          Formato de saída (text/json/csv)
    -r, --recursive       Processar diretório recursivamente
    --batch               Processar múltiplas imagens
    -s, --silent          Sem notificações
    --no-clipboard        Não copiar para área de transferência
    --dry-run             Mostrar o que seria feito

  monitor <diretório>     Monitorar diretório por novas imagens
    -l, --lang            Idioma para OCR (pt/en)
    -f, --format          Formato de saída (text/json/csv)
    -r, --recursive       Monitorar recursivamente
    -o, --output          Salvar em arquivo
    -s, --silent          Sem notificações
    --no-clipboard        Não copiar para área de transferência

Comandos de Utilidade:
  logs                    Gerenciar arquivos de log
    --tail N              Mostrar últimas N linhas
    --since DATA          Mostrar logs desde DATA (AAAA-MM-DD)
    --until DATA          Mostrar logs até DATA
    --errors              Mostrar apenas erros
    --filter TEXTO        Filtrar logs por texto
    --export ARQUIVO      Exportar logs para arquivo
    --clear               Limpar arquivo de log

  status                  Mostrar status do sistema e dependências
  config                  Mostrar configuração atual
  get-lang                Mostrar idioma atual
  set-lang <idioma>       Definir idioma global (pt/en)
  help                    Mostrar esta mensagem de ajuda
  version                 Mostrar informações de versão

Para mais informações, visite:
https://github.com/rouri404/grabtext

Feito por Gabriel Couto Ribeiro (rouri404) - 2025
"""
}

GRAB_HELP_MESSAGES = {
    'en': """
╭─────────────────────────────────────────────────╮
│               GrabText: grab                    │
│         Text capture and extraction             │
╰─────────────────────────────────────────────────╯

Usage:
  grabtext grab [options]

Options:
    -l, --lang            OCR language (pt/en)
    --dry-run             Show what would be done without executing
    -o, --output          Save output to file
    --no-clipboard        Don't copy to clipboard
    -s, --silent          No notifications

Examples:
  grabtext grab                    # Capture screen area
  grabtext grab --lang en          # Capture with English OCR
""",
    'pt': """
╭─────────────────────────────────────────────────╮
│               GrabText: grab                    │
│      Captura e extração de texto                │
╰─────────────────────────────────────────────────╯

Uso:
  grabtext grab [opções]

Opções:
  -l, --lang            Idioma para OCR (pt/en)
  --dry-run             Mostrar o que seria feito sem executar
  -o, --output          Salvar saída em arquivo
  --no-clipboard        Não copiar para área de transferência
  -s, --silent          Sem notificações

Exemplos:
  grabtext grab                    # Capturar área da tela
  grabtext grab --lang en          # Capturar com OCR em inglês
"""
}

LOGS_HELP_MESSAGES = {
    'en': """
╭─────────────────────────────────────────────────╮
│               GrabText: logs                    │
│            Log file management                  │
╰─────────────────────────────────────────────────╯

Usage:
  grabtext logs [options]

Options:
  --tail N              Show last N lines
  --since DATE          Show logs since DATE (YYYY-MM-DD)
  --until DATE          Show logs until DATE
  --errors              Show only errors
  --filter TEXT         Filter logs by text
  --export FILE         Export logs to file
  --clear               Clear log file

Examples:
  grabtext logs --tail 10          # Last 10 lines
  grabtext logs --since 2023-10-08 # Logs since date
  grabtext logs --errors           # Only errors
  grabtext logs --clear            # Clear logs
""",
    'pt': """
╭─────────────────────────────────────────────────╮
│               GrabText: logs                    │
│      Gerenciamento de arquivos de log           │
╰─────────────────────────────────────────────────╯

Uso:
  grabtext logs [opções]

Opções:
  --tail N              Mostrar últimas N linhas
  --since DATA          Mostrar logs desde DATA (AAAA-MM-DD)
  --until DATA          Mostrar logs até DATA
  --errors              Mostrar apenas erros
  --filter TEXTO        Filtrar logs por texto
  --export ARQUIVO      Exportar logs para arquivo
  --clear               Limpar arquivo de log

Exemplos:
  grabtext logs --tail 10          # Últimas 10 linhas
  grabtext logs --since 2023-10-08 # Logs desde uma data
  grabtext logs --errors           # Apenas erros
  grabtext logs --clear            # Limpar logs
"""
}

ARGPARSE_MESSAGES = {
    'pt': {
        'description': 'GrabText - Ferramenta de extração de texto',
        'grab_help': 'Capturar texto da área da tela, processar imagens/diretórios existentes ou monitorar por novas imagens',
        'grab_usage': 'grabtext grab [opções] [caminho]\n\nExemplos:\n  grabtext grab              # Capturar da tela\n  grabtext grab --lang en    # Capturar com OCR em inglês\n  grabtext grab -i imagem.png # Processar uma imagem única\n  grabtext grab -i ./imagens -r # Processar diretório recursivamente\n  grabtext grab -w ./imagens  # Monitorar diretório',
        'process_help': 'Processar imagens ou diretórios existentes',
        'process_usage': 'grabtext process [opções] <arquivo/diretório>\n\nExemplos:\n  grabtext process imagem.png     # Processar imagem única\n  grabtext process ./imagens -r    # Processar diretório recursivamente',
        'monitor_help': 'Monitorar diretório por novas imagens',
        'monitor_usage': 'grabtext monitor [opções] <diretório>\n\nExemplos:\n  grabtext monitor ./imagens     # Monitorar diretório\n  grabtext monitor ./imagens -r  # Monitorar recursivamente',
        'logs_help': 'Gerenciar arquivos de log',
        'status_help': 'Mostrar status do sistema e dependências',
        'config_help': 'Mostrar configuração atual',
        'get_lang_help': 'Mostrar idioma atual',
        'set_lang_help': 'Definir idioma global',
        'help_help': 'Mostrar esta mensagem de ajuda',
        'version_help': 'Mostrar informações de versão',
        'grabtext_usage_full': 'grabtext <comando> [opções]\n\nComandos Principais:\n  grab     Capturar e extrair texto\n  process  Processar imagens/arquivos existentes\n  monitor  Monitorar diretórios por novas imagens\n\nComandos de Utilidade:\n  logs     Gerenciar arquivos de log\n  status   Mostrar status do sistema\n  config   Mostrar configuração\n  help     Mostrar mensagem de ajuda\n  version  Mostrar informações de versão'
    },
    'en': {
        'description': 'GrabText - Text extraction tool',
        'grab_help': 'Capture text from screen area, process existing images/directories, or monitor for new images',
        'grab_usage': 'grabtext grab [options] [path]\n\nExamples:\n  grabtext grab              # Capture from screen\n  grabtext grab --lang en    # Capture with English OCR\n  grabtext grab -i image.png # Process a single image\n  grabtext grab -i ./images -r # Process directory recursively\n  grabtext grab -w ./images  # Monitor directory',
        'process_help': 'Process existing images or directories',
        'process_usage': 'grabtext process [options] <file/directory>\n\nExamples:\n  grabtext process image.png     # Process single image\n  grabtext process ./images -r    # Process directory recursively',
        'monitor_help': 'Monitor directory for new images',
        'monitor_usage': 'grabtext monitor [options] <directory>\n\nExamples:\n  grabtext monitor ./images     # Monitor directory\n  grabtext monitor ./images -r  # Monitor recursively',
        'logs_help': 'Manage log files',
        'status_help': 'Show system status and dependencies',
        'config_help': 'Show current configuration',
        'get_lang_help': 'Show current language',
        'set_lang_help': 'Set global language',
        'help_help': 'Show this help message',
        'version_help': 'Show version information',
        'grabtext_usage_full': 'grabtext <command> [options]\n\nMain Commands:\n  grab     Capture and extract text\n  process  Process existing images/files\n  monitor  Monitor Directories for new images\n\nUtility Commands:\n  logs     Manage log files\n  status   Show system status\n  config   Show configuration\n  help     Show help message\n  version  Show version information'
    }
}

STATUS_MESSAGES = {
    'pt': {
        'header': "╭─────────────────────────────────────────────────╮\n│               GrabText: Status                  │\n│         Status do Sistema e Dependências        │\n╰─────────────────────────────────────────────────╯",
        'system_dependencies': "Dependências do Sistema:",
        'dependency_ok': "  [OK] {cmd:<12} - {desc}",
        'dependency_not_found': "  [NO] {cmd:<12} - {desc} (não encontrado)",
        'dependency_check_failed': "  [?]  {cmd:<12} - {desc} (verificação falhou)",
        'python_environment': "Ambiente Python:",
        'python_version': "  Versão do Python: {version}",
        'virtual_env': "  Ambiente virtual: {status}",
        'yes': 'Sim',
        'no': 'Não',
        'python_packages': "Pacotes Python:",
        'package_ok': "  [OK] {pkg}",
        'package_not_installed': "  [NO] {pkg} (não instalado)",
        'configuration': "Configuração:",
        'language': "  Idioma: {lang}",
        'tesseract_lang': "  Idioma do Tesseract: {tesseract_lang}",
        'log_file': "  Arquivo de log: {log_file}",
        'log_exists': "  Log existe: {status}",
        'display_environment': "Ambiente de Exibição:",
        'x11_display': "  Display X11: {display}",
        'wayland_display': "  Display Wayland: {display}",
        'no_display_warning': "  [AVISO] Nenhum ambiente de exibição detectado"
    },
    'en': {
        'header': "╭─────────────────────────────────────────────────╮\n│               GrabText: Status                  │\n│         System Status and Dependencies          │\n╰─────────────────────────────────────────────────╯",
        'system_dependencies': "System Dependencies:",
        'dependency_ok': "  [OK] {cmd:<12} - {desc}",
        'dependency_not_found': "  [NO] {cmd:<12} - {desc} (not found)",
        'dependency_check_failed': "  [?]  {cmd:<12} - {desc} (check failed)",
        'python_environment': "Python Environment:",
        'python_version': "  Python version: {version}",
        'virtual_env': "  Virtual env: {status}",
        'yes': 'Yes',
        'no': 'No',
        'python_packages': "Python Packages:",
        'package_ok': "  [OK] {pkg}",
        'package_not_installed': "  [NO] {pkg} (not installed)",
        'configuration': "Configuration:",
        'language': "  Language: {lang}",
        'tesseract_lang': "  Tesseract lang: {tesseract_lang}",
        'log_file': "  Log file: {log_file}",
        'log_exists': "  Log exists: {status}",
        'display_environment': "Display Environment:",
        'x11_display': "  X11 Display: {display}",
        'wayland_display': "  Wayland Display: {display}",
        'no_display_warning': "  [WARN] No display environment detected"
    }
}

CONFIG_MESSAGES = {
    'pt': {
        'header': "╭─────────────────────────────────────────────────╮\n│               GrabText: Config                  │\n│              Configuração Atual                 │\n╰─────────────────────────────────────────────────╯",
        'version': "Versão: {version}",
        'language': "Idioma: {lang}",
        'tesseract_language': "Idioma do Tesseract: {tesseract_lang}",
        'log_file': "Arquivo de Log: {log_file}",
        'script_directory': "Diretório do Script: {script_dir}",
        'debug_mode': "Modo Depuração: {status}",
        'verbose_mode': "Modo Detalhado: {status}",
        'enabled': 'ativado',
        'disabled': 'desativado',
        'environment_variables': "Variáveis de Ambiente:",
        'env_var_status': "  {var_name}: {status}",
        'not_set': 'não definido'
    },
    'en': {
        'header': "╭─────────────────────────────────────────────────╮\n│               GrabText: Config                  │\n│              Current Configuration              │\n╰─────────────────────────────────────────────────╯",
        'version': "Version: {version}",
        'language': "Language: {lang}",
        'tesseract_language': "Tesseract Language: {tesseract_lang}",
        'log_file': "Log File: {log_file}",
        'script_directory': "Script Directory: {script_dir}",
        'debug_mode': "Debug Mode: {status}",
        'verbose_mode': "Verbose Mode: {status}",
        'enabled': 'enabled',
        'disabled': 'disabled',
        'environment_variables': "Environment Variables:",
        'env_var_status': "  {var_name}: {status}",
        'not_set': 'not set'
    }
}

def print_help():
    help_text = HELP_MESSAGES.get(current_lang_code, HELP_MESSAGES['en'])
    print(help_text)

def handle_get_lang_command():
    """Mostra o idioma atual"""
    lang_name = get_language_name(current_lang_code, current_lang_code)
    print(get_string('MSG_CURRENT_LANGUAGE_STATUS', lang=current_lang_code, lang_name=lang_name))

def set_language(lang):
    """Define o idioma globalmente"""
    if not is_language_supported(lang):
        available = ', '.join(get_available_languages())
        return False, f"Idioma não suportado: {lang}. Disponíveis: {available}"
    
    config = load_config()
    config['language'] = lang
    if save_config(config):
        global current_lang_code, tesseract_lang_code
        current_lang_code = lang
        tesseract_lang_code = get_tesseract_lang_code(lang)
        # Re-inicializar logging para usar o novo idioma
        initialize_language()
        return True, get_string('MSG_LANGUAGE_SET_SUCCESS', lang=lang)
    else:
        return False, "Erro ao salvar configuração"

def handle_set_lang_command(args):
    """Define o idioma globalmente"""
    if args.language:
        success, msg = set_language(args.language)
        if success:
            lang_name = get_language_name(args.language, args.language)
            print(get_string('MSG_LANGUAGE_SET_SUCCESS', lang=args.language))
            if not args.silent:
                send_notification(
                    get_string('MSG_LANGUAGE_CHANGED_TITLE'),
                    get_string('MSG_LANGUAGE_SET_SUCCESS', lang=args.language),
                    icon_name="preferences-system-time"
                )
        else:
            print(get_string('MSG_ERROR_PREFIX', message=msg))
    else:
        available = ', '.join(get_available_languages())
        print(f"Uso: grabtext set-lang <idioma>")
        print(f"Idiomas disponíveis: {available}")

def send_notification(title, message, icon_name="", expire_timeout=5000):
    cmd = ['notify-send', '-a', 'GrabText', title, message, '-t', str(expire_timeout)]
    if icon_name:
        cmd.extend(['-i', icon_name])
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        logging.error(LOG_MESSAGES['NOTIFY_SEND_MISSING'])
    except subprocess.CalledProcessError as e:
        logging.error(LOG_MESSAGES['NOTIFY_SEND_ERROR'].format(e=e))

def copy_to_clipboard(text):
    if not text:
        return False

    try:
        # Primeiro tenta xclip (X11)
        if subprocess.run(['which', 'xclip'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
            subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode('utf-8'), check=True)
            return True
        
        # Se não tiver xclip, tenta wl-copy (Wayland)
        if subprocess.run(['which', 'wl-copy'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
            subprocess.run(['wl-copy'], input=text.encode('utf-8'), check=True)
            return True
        
        # Se chegou aqui, nenhuma ferramenta está disponível
        raise FileNotFoundError("No clipboard tool (xclip or wl-copy) found")
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        logging.error(f"{LOG_MESSAGES['CLIPBOARD_ERROR']} Details: {str(e)}")
        send_notification(
                get_string('MSG_GRABTEXT_ERROR_TITLE'),
                get_string('MSG_ERROR_CLIPBOARD_INSTALL'),
                icon_name="dialog-error"
            )
        return False

class ImageHandler(FileSystemEventHandler):
    def __init__(self, process_func):
        self.process_func = process_func
        self.processing_files = set()  # Arquivos sendo processados
        self.file_lock = threading.Lock()
        self.file_sizes = defaultdict(int)  # Tamanhos dos arquivos para detectar quando estão completos
        
    def _is_file_ready(self, file_path):
        """Verifica se o arquivo está pronto para processamento"""
        try:
            # Verificar se o arquivo ainda está sendo escrito
            current_size = os.path.getsize(file_path)
            
            # Se o tamanho mudou recentemente, ainda pode estar sendo escrito
            with self.file_lock:
                last_size = self.file_sizes[file_path]
                self.file_sizes[file_path] = current_size
                
                # Se é a primeira verificação ou o tamanho mudou, esperar
                if last_size == 0 or current_size != last_size:
                    return False
            
            # Verificar se o arquivo pode ser aberto em modo exclusivo
            try:
                with open(file_path, 'rb') as f:
                    f.read(1)  # Tentar ler um byte
                return True
            except (IOError, OSError):
                return False
                
        except (IOError, OSError):
            return False
    
    def _wait_for_file_completion(self, file_path, max_wait=5):
        """Espera até que o arquivo esteja completo"""
        wait_time = 0
        check_interval = 0.5
        
        while wait_time < max_wait:
            if self._is_file_ready(file_path):
                return True
            time.sleep(check_interval)
            wait_time += check_interval
        
        logging.warning(f"File {file_path} may still be being written after {max_wait}s")
        return False

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            # Evitar processamento duplicado
            with self.file_lock:
                if event.src_path in self.processing_files:
                    return
                self.processing_files.add(event.src_path)
            
            try:
                # Esperar o arquivo estar completo
                if self._wait_for_file_completion(event.src_path):
                    logging.debug(f"Processing file: {event.src_path}")
                    self.process_func(event.src_path)
                else:
                    logging.warning(f"Skipping incomplete file: {event.src_path}")
            except Exception as e:
                logging.error(f"Error processing file {event.src_path}: {e}")
            finally:
                # Limpar do conjunto de processamento
                with self.file_lock:
                    self.processing_files.discard(event.src_path)
                    # Limpar do registro de tamanhos após algum tempo
                    threading.Timer(10.0, lambda: self.file_sizes.pop(event.src_path, None)).start()

def validate_image_path(image_path):
    """Valida se o caminho é uma imagem válida"""
    if not image_path or not isinstance(image_path, str):
        return False, get_string('MSG_INVALID_PATH_PROVIDED')
    
    # Verificar se o arquivo existe
    if not os.path.exists(image_path):
        return False, get_string('MSG_FILE_NOT_FOUND', path=image_path)
    
    # Verificar se é um arquivo (não diretório)
    if not os.path.isfile(image_path):
        return False, get_string('MSG_PATH_NOT_FILE', path=image_path)
    
    # Verificar extensão
    valid_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif', '.webp'}
    file_ext = os.path.splitext(image_path)[1].lower()
    if file_ext not in valid_extensions:
        return False, get_string('MSG_UNSUPPORTED_IMAGE_FORMAT', format=file_ext)
    
    # Verificar se o arquivo pode ser aberto como imagem
    try:
        with Image.open(image_path) as img:
            # Verificar dimensões mínimas
            if img.width < 1 or img.height < 1:
                return False, "Invalid image dimensions"
            
            # Verificar tamanho máximo (50MB)
            file_size = os.path.getsize(image_path)
            if file_size > 50 * 1024 * 1024:  # 50MB
                return False, get_string('MSG_IMAGE_TOO_LARGE', size=file_size / (1024*1024))
            
        return True, "Valid image file"
        
    except (IOError, OSError, Image.UnidentifiedImageError) as e:
        return False, get_string('MSG_CANNOT_READ_IMAGE', error=e)
    except Exception as e:
        return False, f"Unexpected error validating image: {e}"

def validate_directory_path(dir_path):
    """Valida se o caminho é um diretório válido"""
    if not dir_path or not isinstance(dir_path, str):
        return False, get_string('MSG_INVALID_PATH_PROVIDED')
    
    # Verificar se o diretório existe
    if not os.path.exists(dir_path):
        return False, get_string('MSG_DIRECTORY_NOT_FOUND', path=dir_path)
    
    # Verificar se é um diretório
    if not os.path.isdir(dir_path):
        return False, get_string('MSG_PATH_NOT_DIRECTORY', path=dir_path)
    
    # Verificar permissões de leitura
    if not os.access(dir_path, os.R_OK):
        return False, get_string('MSG_NO_READ_PERMISSION', path=dir_path)
    
    return True, "Valid directory"

def validate_output_path(output_path):
    """Valida se o caminho de saída é válido"""
    if not output_path or not isinstance(output_path, str):
        return False, get_string('MSG_INVALID_PATH_PROVIDED')
    
    try:
        # Verificar se o diretório pai existe e tem permissão de escrita
        parent_dir = os.path.dirname(os.path.abspath(output_path))
        if parent_dir and not os.path.exists(parent_dir):
            return False, get_string('MSG_DIRECTORY_NOT_FOUND', path=parent_dir)
        
        if parent_dir and not os.access(parent_dir, os.W_OK):
            return False, get_string('MSG_NO_WRITE_PERMISSION', path=parent_dir)
        
        # Verificar se o arquivo já existe e se pode ser sobrescrito
        if os.path.exists(output_path):
            if not os.access(output_path, os.W_OK):
                return False, get_string('MSG_CANNOT_OVERWRITE_FILE', path=output_path)
        
        return True, "Valid output path"
        
    except Exception as e:
        return False, f"Error validating output path: {e}"

def get_image_metadata(image_path, img=None):
    try:
        if img is None:
            try:
                img = Image.open(image_path)
            except (IOError, OSError) as e:
                logging.error(f"Cannot open image {image_path}: {e}")
                return {
                    'filename': os.path.basename(image_path),
                    'filepath': os.path.abspath(image_path),
                    'error': f'Cannot open image: {e}'
                }
        
        # Obter informações do arquivo
        try:
            file_stats = os.stat(image_path)
        except (IOError, OSError) as e:
            logging.warning(f"Cannot get file stats for {image_path}: {e}")
            file_stats = None
        
        metadata = {
            'filename': os.path.basename(image_path),
            'filepath': os.path.abspath(image_path),
            'image_width': img.width,
            'image_height': img.height,
            'image_format': img.format,
            'image_mode': img.mode
        }
        
        if file_stats:
            metadata.update({
                'file_size_bytes': file_stats.st_size,
                'file_modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat()
            })
        
        return metadata
        
    except AttributeError as e:
        logging.error(f"Invalid image object for {image_path}: {e}")
        return {
            'filename': os.path.basename(image_path),
            'filepath': os.path.abspath(image_path),
            'error': f'Invalid image object: {e}'
        }
    except Exception as e:
        logging.error(f"Unexpected error getting metadata for {image_path}: {e}")
        return {
            'filename': os.path.basename(image_path),
            'filepath': os.path.abspath(image_path),
            'error': f'Unexpected error: {e}'
        }

def get_ocr_data(img, lang_code):
    """Extrai dados OCR com informações de confiança"""
    try:
        # Validar objeto de imagem
        if not hasattr(img, 'width') or not hasattr(img, 'height'):
            raise ValueError("Invalid image object provided")
        
        # Usar gerenciador de motores OCR
        ocr_manager = get_ocr_manager()
        engine_name = getattr(ocr_manager, 'default_engine', 'tesseract')
        
        # Obter dados OCR usando o motor disponível
        ocr_result = ocr_manager.extract_text(img, lang_code, engine_name)
        
        if ocr_result.get('success', False):
            return {
                'text': ocr_result.get('text', ''),
                'word_count': ocr_result.get('word_count', 0),
                'char_count': ocr_result.get('char_count', 0),
                'avg_confidence': ocr_result.get('avg_confidence', 0),
                'language_used': lang_code,
                'has_text': ocr_result.get('has_text', False),
                'processing_timestamp': datetime.now().isoformat(),
                'engine_used': ocr_result.get('engine', 'tesseract')
            }
        else:
            error_msg = ocr_result.get('error', 'Unknown OCR error')
            logging.error(f"OCR processing failed: {error_msg}")
            return {
                'text': '',
                'word_count': 0,
                'char_count': 0,
                'avg_confidence': 0,
                'language_used': lang_code,
                'has_text': False,
                'processing_timestamp': datetime.now().isoformat(),
                'error': error_msg,
                'engine_used': ocr_result.get('engine', 'tesseract')
            }
        
    except ValueError as e:
        logging.error(f"Invalid input for OCR: {e}")
        return {
            'text': '',
            'word_count': 0,
            'char_count': 0,
            'avg_confidence': 0,
            'language_used': lang_code,
            'has_text': False,
            'processing_timestamp': datetime.now().isoformat(),
            'error': f'Input validation error: {e}'
        }
    except Exception as e:
        logging.error(f"Unexpected OCR error: {e}")
        return {
            'text': '',
            'word_count': 0,
            'char_count': 0,
            'avg_confidence': 0,
            'language_used': lang_code,
            'has_text': False,
            'processing_timestamp': datetime.now().isoformat(),
            'error': f'Unexpected error: {e}'
        }

def process_image_file(image_path, format='text', preprocessing='none'):
    try:
        img = Image.open(image_path)
        
        # Aplicar pré-processamento se solicitado
        if preprocessing != 'none' and CV2_AVAILABLE:
            processor = ImageProcessor()
            
            if preprocessing == 'text_enhancement':
                processor = get_preset_text_enhancement()
            elif preprocessing == 'low_quality':
                processor = get_preset_low_quality()
            elif preprocessing == 'handwriting':
                from image_processor import get_preset_handwriting
                processor = get_preset_handwriting()
            elif preprocessing == 'document_scan':
                from image_processor import get_preset_document_scan
                processor = get_preset_document_scan()
            
            try:
                img = processor.preprocess(img)
                logging.debug(f"Applied {preprocessing} preprocessing to {image_path}")
            except Exception as e:
                logging.warning(f"Preprocessing failed for {image_path}: {e}")
        
        # Obter metadados da imagem
        metadata = get_image_metadata(image_path, img)
        
        # Obter dados OCR
        ocr_data = get_ocr_data(img, tesseract_lang_code)
        
        # Validar texto extraído
        validator = TextValidator(current_lang_code)
        validation_result = validator.validate_text(ocr_data.get('text', ''), ocr_data.get('avg_confidence', 0))
        
        # Adicionar informações de validação ao resultado
        ocr_data['validation'] = validation_result
        ocr_data['final_confidence'] = validation_result.get('final_score', ocr_data.get('avg_confidence', 0))
        ocr_data['is_text_valid'] = validation_result.get('is_valid', True)
        
        if format == 'json':
            result = {
                'metadata': metadata,
                'ocr': ocr_data,
                'processing_info': {
                    'grabtext_version': VERSION,
                    'processed_at': datetime.now().isoformat()
                }
            }
            return json.dumps(result, indent=2, ensure_ascii=False)
        
        elif format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Para CSV individual, incluir cabeçalho
            writer.writerow([
                'filename', 'filepath', 'file_size_bytes', 'file_modified',
                'image_width', 'image_height', 'image_format', 'image_mode',
                'text', 'word_count', 'char_count', 'avg_confidence',
                'language_used', 'has_text', 'processing_timestamp'
            ])
            
            writer.writerow([
                metadata.get('filename', ''),
                metadata.get('filepath', ''),
                metadata.get('file_size_bytes', ''),
                metadata.get('file_modified', ''),
                metadata.get('image_width', ''),
                metadata.get('image_height', ''),
                metadata.get('image_format', ''),
                metadata.get('image_mode', ''),
                ocr_data.get('text', ''),
                ocr_data.get('word_count', ''),
                ocr_data.get('char_count', ''),
                ocr_data.get('avg_confidence', ''),
                ocr_data.get('language_used', ''),
                ocr_data.get('has_text', ''),
                ocr_data.get('processing_timestamp', '')
            ])
            return output.getvalue()
        
        else:
            return ocr_data.get('text', '')
            
    except Exception as e:
        logging.error(f"Error processing {image_path}: {str(e)}")
        return None

def process_directory(dir_path, recursive=False, format='text'):
    pattern = '**/*' if recursive else '*'
    results = []
    path = Path(dir_path)
    processed_files = []
    
    # Coletar todos os arquivos de imagem primeiro
    image_files = [p for p in path.glob(pattern) if p.suffix.lower() in ['.png', '.jpg', '.jpeg']]
    
    if format == 'json':
        # Para JSON, criar uma estrutura unificada com todos os resultados
        batch_data = {
            'batch_info': {
                'total_files': len(image_files),
                'processed_at': datetime.now().isoformat(),
                'directory': os.path.abspath(dir_path),
                'recursive': recursive,
                'grabtext_version': VERSION
            },
            'results': []
        }
        
        for img_path in image_files:
            result = process_image_file(str(img_path), format)
            if result:
                # Parse do JSON individual e adicionar à lista
                try:
                    individual_data = json.loads(result)
                    batch_data['results'].append(individual_data)
                    processed_files.append(str(img_path))
                except json.JSONDecodeError:
                    logging.error(f"Failed to parse JSON for {img_path}")
        
        batch_data['batch_info']['successfully_processed'] = len(processed_files)
        return [json.dumps(batch_data, indent=2, ensure_ascii=False)]
    
    elif format == 'csv':
        # Para CSV, criar um arquivo com cabeçalho e todos os dados
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escrever cabeçalho
        writer.writerow([
            'filename', 'filepath', 'file_size_bytes', 'file_modified',
            'image_width', 'image_height', 'image_format', 'image_mode',
            'text', 'word_count', 'char_count', 'avg_confidence',
            'language_used', 'has_text', 'processing_timestamp'
        ])
        
        for img_path in image_files:
            result = process_image_file(str(img_path), format)
            if result:
                # O resultado já inclui o cabeçalho, então precisamos extrair apenas os dados
                lines = result.strip().split('\n')
                if len(lines) > 1:  # Pular o cabeçalho
                    # Usar csv.reader para lidar com vírgulas dentro do texto
                    csv_reader = csv.reader([lines[1]])
                    row = next(csv_reader)
                    writer.writerow(row)
                    processed_files.append(str(img_path))
        
        return [output.getvalue()]
    
    else:
        # Para texto simples, manter comportamento original
        for img_path in image_files:
            result = process_image_file(str(img_path), format)
            if result:
                results.append(result)
                processed_files.append(str(img_path))
    
    return results

def handle_status_command():
    """Mostra o status do sistema e dependências"""
    print(STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['header'])
    print()
    
    # Verificar dependências do sistema
    print(STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['system_dependencies'])
    dependencies = {
        'flameshot': 'Screenshot tool',
        'tesseract': 'OCR engine',
        'xclip': 'Clipboard tool (X11)',
        'wl-copy': 'Clipboard tool (Wayland)',
        'notify-send': 'Desktop notifications'
    }
    
    for cmd, desc in dependencies.items():
        try:
            result = subprocess.run(['which', cmd], capture_output=True, text=True)
            if result.returncode == 0:
                print(STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['dependency_ok'].format(cmd=cmd, desc=desc))
            else:
                print(STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['dependency_not_found'].format(cmd=cmd, desc=desc))
        except Exception:
            print(STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['dependency_check_failed'].format(cmd=cmd, desc=desc))
    
    print()
    
    # Verificar ambiente Python
    print(STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['python_environment'])
    print(STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['python_version'].format(version=sys.version.split()[0]))
    print(STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['virtual_env'].format(status=STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['yes'] if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['no']))
    
    # Verificar pacotes Python
    print(STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['python_packages'])
    python_packages = ['pytesseract', 'PIL', 'watchdog']
    for pkg in python_packages:
        try:
            __import__(pkg)
            print(STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['package_ok'].format(pkg=pkg))
        except ImportError:
            print(STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['package_not_installed'].format(pkg=pkg))
    
    print()
    
    # Verificar configuração
    print(STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['configuration'])
    print(STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['language'].format(lang=current_lang_code))
    print(STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['tesseract_lang'].format(tesseract_lang=tesseract_lang_code))
    print(STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['log_file'].format(log_file=LOG_FILE, status=STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['yes'] if os.path.exists(LOG_FILE) else STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['no']))
    
    # Verificar ambiente gráfico
    print()
    print(STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['display_environment'])
    if os.environ.get('DISPLAY'):
        print(STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['x11_display'].format(display=os.environ.get('DISPLAY')))
    if os.environ.get('WAYLAND_DISPLAY'):
        print(STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['wayland_display'].format(display=os.environ.get('WAYLAND_DISPLAY')))
    
    if not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY'):
        print(STATUS_MESSAGES.get(current_lang_code, STATUS_MESSAGES['en'])['no_display_warning'])

def process_single_image(image_path, args):
    # Validar entrada
    is_valid, error_msg = validate_image_path(image_path)
    if not is_valid:
        logging.error(f"Invalid image path: {error_msg}")
        print(get_string('MSG_ERROR_PREFIX', message=error_msg))
        return
    
    # Validar caminho de saída se fornecido
    if args.output:
        output_valid, output_error = validate_output_path(args.output)
        if not output_valid:
            logging.error(f"Invalid output path: {output_error}")
            print(get_string('MSG_ERROR_PREFIX', message=output_error))
            return

    if args.dry_run:
        print(get_string('MSG_DRY_RUN_WOULD_PROCESS_IMAGE', path=image_path))
        return

    if not args.silent:
        send_notification(
            get_string('MSG_PROCESSING_IMAGE_TITLE'),
            get_string('MSG_PROCESSING_IMAGE_CONTENT'),
            icon_name="image-x-generic"
        )

    try:
        extracted_text = process_image_file(image_path, args.format if hasattr(args, 'format') else 'text', 
                                   args.preprocessing if hasattr(args, 'preprocessing') else 'none')

        if extracted_text:
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(extracted_text)
                if not args.silent:
                    send_notification(
                        get_string('MSG_TEXT_SAVED_TITLE'),
                        get_string('MSG_TEXT_SAVED_CONTENT', path=os.path.abspath(args.output)),
                        icon_name="document-save"
                    )
            
            if not args.no_clipboard:
                copy_to_clipboard(extracted_text)
                if not args.silent:
                    send_notification(
                        get_string('MSG_TEXT_EXTRACTED_TITLE'),
                        get_string('MSG_TEXT_EXTRACTED_CONTENT', preview=extracted_text[:100].replace('\n', ' ')),
                        icon_name="text-x-generic"
                    )
            print(extracted_text)
        else:
            if not args.silent:
                send_notification(
                    get_string('MSG_NO_TEXT_DETECTED_TITLE'),
                    get_string('MSG_NO_TEXT_DETECTED_CONTENT'),
                    icon_name="dialog-warning"
                )
            logging.info(LOG_MESSAGES['OCR_NO_TEXT'])
    except Exception as e:
        logging.error(LOG_MESSAGES['UNEXPECTED_ERROR'].format(e=e))
        if not args.silent:
            send_notification(
                get_string('MSG_UNEXPECTED_ERROR_TITLE'),
                get_string('MSG_UNEXPECTED_ERROR_CONTENT', preview=str(e)[:100].replace('\n', ' ')),
                icon_name="dialog-error"
            )

def handle_process_command(args):
    # Validar entrada
    is_valid, error_msg = validate_directory_path(args.path) if os.path.isdir(args.path) else validate_image_path(args.path)
    if not is_valid:
        logging.error(f"Invalid path: {error_msg}")
        print(get_string('MSG_ERROR_PREFIX', message=error_msg))
        return

    if args.lang:
        global current_lang_code, tesseract_lang_code
        if is_language_supported(args.lang):
            current_lang_code = args.lang
            tesseract_lang_code = get_tesseract_lang_code(args.lang)
            logging.debug(get_string('MSG_LANGUAGE_OVERRIDDEN_FOR_PROCESS', current_lang_code=current_lang_code))
        else:
            print(f"Idioma não suportado: {args.lang}")
            return

    if os.path.isfile(args.path):
        process_single_image(args.path, args)
    elif os.path.isdir(args.path):
        if args.dry_run:
            print(f"Dry run: Would process directory '{args.path}' (recursive: {args.recursive})")
            return
        
        results = process_directory(args.path, args.recursive, args.format)
        if results:
            full_output = '\n'.join(results)
            if args.output:
                try:
                    with open(args.output, 'w') as f:
                        f.write(full_output)
                    if not args.silent:
                        send_notification(
                            get_string('MSG_BATCH_COMPLETE_TITLE'),
                            get_string('MSG_TEXT_SAVED_CONTENT', path=os.path.abspath(args.output)),
                            icon_name="document-save"
                        )
                except Exception as e:
                    logging.error(get_string('MSG_FILE_SAVE_ERROR', error=str(e)))
                    print(get_string('MSG_ERROR_PREFIX', message=get_string('MSG_FILE_SAVE_ERROR', error=str(e))))
            
            if not args.no_clipboard:
                copy_to_clipboard(full_output)
                if not args.silent:
                    send_notification(
                        get_string('MSG_TEXT_EXTRACTED_TITLE'),
                        get_string('MSG_TEXT_EXTRACTED_CONTENT', preview=full_output[:100].replace('\n', ' ')),
                        icon_name="text-x-generic"
                    )
            print(full_output)

        if not args.silent:
            send_notification(
                get_string('MSG_BATCH_COMPLETE_TITLE'),
                get_string('MSG_BATCH_COMPLETE_CONTENT', count=len(results), path=args.path),
                icon_name="document-multiple"
            )
    else:
        print(get_string('MSG_PATH_NOT_FOUND', path=args.path))
    print(get_string('MSG_ERROR_PREFIX', message=get_string('MSG_PATH_NOT_FOUND', path=args.path)))

def handle_monitor_command(args):
    # Validar diretório
    is_valid, error_msg = validate_directory_path(args.directory)
    if not is_valid:
        logging.error(f"Invalid directory: {error_msg}")
        print(get_string('MSG_ERROR_PREFIX', message=error_msg))
        return

    if args.lang:
        global current_lang_code, tesseract_lang_code
        if is_language_supported(args.lang):
            current_lang_code = args.lang
            tesseract_lang_code = get_tesseract_lang_code(args.lang)
            logging.debug(get_string('MSG_LANGUAGE_OVERRIDDEN_FOR_MONITOR', current_lang_code=current_lang_code))
        else:
            print(f"Idioma não suportado: {args.lang}")
            return

    print(get_string('MSG_WATCHING_DIRECTORY_CONTENT', path=args.directory))
    if not args.silent:
        send_notification(
            get_string('MSG_WATCHING_DIRECTORY_TITLE'),
            get_string('MSG_WATCHING_DIRECTORY_CONTENT', path=args.directory),
            icon_name="folder-open"
        )

    event_handler = ImageHandler(lambda img_path: process_single_image(img_path, args))
    observer = Observer()
    observer.schedule(event_handler, args.directory, recursive=args.recursive)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def handle_grab_command(args):
    if args.path:
        if os.path.isfile(args.path) or os.path.isdir(args.path):
            # Se um caminho é fornecido e é um arquivo/diretório, trata como process/monitor
            if args.watch or args.batch or args.recursive:
                # Se qualquer flag de processamento/monitoramento está ativa, chama handle_monitor_command ou handle_process_command
                if args.watch:
                    handle_monitor_command(argparse.Namespace(directory=args.path, lang=args.lang, recursive=args.recursive, format=args.format, output=args.output, silent=args.silent, no_clipboard=args.no_clipboard))
                else:
                    # Assume batch/recursive para handle_process_command
                    handle_process_command(argparse.Namespace(path=args.path, lang=args.lang, output=args.output, format=args.format, recursive=args.recursive, batch=args.batch, silent=args.silent, no_clipboard=args.no_clipboard, dry_run=args.dry_run))
            else:
                # Caso contrário, trata como processamento de imagem única
                process_single_image(args.path, args)
        else:
            print(get_message('error_prefix', message=get_message('path_not_found', path=args.path)))
    else:
        # Comportamento padrão: capturar da tela
        if args.dry_run:
            print("Dry run: Would capture screen area")
            return

        if not args.silent:
            send_notification(
                get_string('MSG_PROCESSING_IMAGE_TITLE'),
                get_string('MSG_PROCESSING_IMAGE_CONTENT'),
                icon_name="image-x-generic"
            )

        try:
            # Prefer stdout capture (Flameshot v13+ supports --raw to stdout)
            screenshot_process = subprocess.Popen(['flameshot', 'gui', '--raw'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            image_data, stderr = screenshot_process.communicate()

            if screenshot_process.returncode != 0:
                error_message = stderr.decode('utf-8').strip()
                if "User cancelled" in error_message or "Operação cancelada pelo usuário" in error_message:
                    logging.info("Screenshot cancelled by user.")
                else:
                    logging.error(f"Flameshot error: {error_message}")
                    if not args.silent:
                        send_notification(
                            get_string('MSG_GRABTEXT_ERROR_TITLE'),
                            get_string('MSG_GRABTEXT_ERROR_CONTENT', preview=error_message[:100]),
                            icon_name="dialog-error"
                        )
                return

            # If no image data received on stdout, fallback to temp file approach
            if not image_data:
                temp_path = None
                try:
                    # Criar arquivo temporário com contexto seguro
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png', prefix='grabtext_') as tmp_file:
                        temp_path = tmp_file.name
                    
                    fallback_proc = subprocess.Popen(['flameshot', 'gui', '-p', temp_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    _, fb_stderr = fallback_proc.communicate()
                    
                    if fallback_proc.returncode != 0:
                        error_message = fb_stderr.decode('utf-8').strip()
                        if "User cancelled" in error_message or "Operação cancelada pelo usuário" in error_message:
                            logging.info("Screenshot cancelled by user (fallback).")
                        else:
                            logging.error(f"Flameshot error (fallback): {error_message}")
                            if not args.silent:
                                send_notification(
                                    get_string('MSG_GRABTEXT_ERROR_TITLE'),
                                    get_string('MSG_GRABTEXT_ERROR_CONTENT', preview=error_message[:100]),
                                    icon_name="dialog-error"
                                )
                        return

                    # Verificar se o arquivo foi criado e tem conteúdo
                    if not temp_path or not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                        logging.warning(LOG_MESSAGES['NO_IMAGE_DATA'])
                        return

                    # Ler dados do arquivo temporário
                    try:
                        with open(temp_path, 'rb') as f:
                            image_data = f.read()
                    except (IOError, OSError) as e:
                        logging.error(f"Error reading temp file {temp_path}: {e}")
                        return
                        
                except (subprocess.SubprocessError, OSError) as e:
                    logging.error(f"Error creating temp file: {e}")
                    return
                finally:
                    # Limpeza garantida do arquivo temporário
                    if temp_path and os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                            logging.debug(f"Cleaned up temp file: {temp_path}")
                        except (IOError, OSError) as e:
                            logging.warning(f"Could not remove temp file {temp_path}: {e}")

            img = Image.open(io.BytesIO(image_data))
            lang_code_to_use = args.lang if args.lang else current_lang_code
            tesseract_lang_code_to_use = get_tesseract_lang_code(lang_code_to_use)

            extracted_text = pytesseract.image_to_string(img, lang=tesseract_lang_code_to_use)
            extracted_text = extracted_text.strip()

            if extracted_text:
                logging.info(LOG_MESSAGES['OCR_SUCCESS'].format(lang=tesseract_lang_code_to_use, chars=len(extracted_text), text=extracted_text[:50]))
                if args.output:
                    try:
                        with open(args.output, 'w') as f:
                            f.write(extracted_text)
                        if not args.silent:
                            send_notification(
                                get_string('MSG_TEXT_SAVED_TITLE'),
                                get_string('MSG_TEXT_SAVED_CONTENT', path=os.path.abspath(args.output)),
                                icon_name="document-save"
                            )
                    except Exception as e:
                        logging.error(get_string('MSG_FILE_SAVE_ERROR', error=str(e)))
                        print(get_string('MSG_ERROR_PREFIX', message=get_string('MSG_FILE_SAVE_ERROR', error=str(e))))
                
                if not args.no_clipboard:
                    copy_to_clipboard(extracted_text)
                    if not args.silent:
                        send_notification(
                            get_string('MSG_TEXT_EXTRACTED_TITLE'),
                            get_string('MSG_TEXT_EXTRACTED_CONTENT', preview=extracted_text[:100].replace('\n', ' ')),
                            icon_name="text-x-generic"
                        )
                send_notification(
                    get_message('grabtext_error_title'),
                    get_message('unexpected_error_content', preview=error_msg),
                    icon_name="dialog-error"
                )
        except Exception as e:
            logging.error(LOG_MESSAGES['UNEXPECTED_ERROR'].format(e=e))
            print(get_message('error_prefix', message=LOG_MESSAGES['UNEXPECTED_ERROR'].format(e=e)))
            if not args.silent:
                send_notification(
                    get_message('unexpected_error_title'),
                    get_message('unexpected_error_content', preview=str(e)[:100].replace('\n', ' ')),
                    icon_name="dialog-error"
                )

def handle_config_command():
    """Mostra a configuração atual"""
    print(CONFIG_MESSAGES.get(current_lang_code, CONFIG_MESSAGES['en'])['header'])
    print()
    print(CONFIG_MESSAGES.get(current_lang_code, CONFIG_MESSAGES['en'])['version'].format(version=VERSION))
    print(CONFIG_MESSAGES.get(current_lang_code, CONFIG_MESSAGES['en'])['language'].format(lang=current_lang_code))
    print(CONFIG_MESSAGES.get(current_lang_code, CONFIG_MESSAGES['en'])['tesseract_language'].format(tesseract_lang=tesseract_lang_code))
    print(CONFIG_MESSAGES.get(current_lang_code, CONFIG_MESSAGES['en'])['log_file'].format(log_file=LOG_FILE))
    print(CONFIG_MESSAGES.get(current_lang_code, CONFIG_MESSAGES['en'])['script_directory'].format(script_dir=SCRIPT_DIR))
    
    # Verificar variáveis de ambiente
    print()
    print(CONFIG_MESSAGES.get(current_lang_code, CONFIG_MESSAGES['en'])['environment_variables'])
    env_vars = ['GRABTEXT_LANG', 'DISPLAY', 'WAYLAND_DISPLAY']
    for var in env_vars:
        value = os.environ.get(var, CONFIG_MESSAGES.get(current_lang_code, CONFIG_MESSAGES['en'])['not_set'])
        print(CONFIG_MESSAGES.get(current_lang_code, CONFIG_MESSAGES['en'])['env_var_status'].format(var_name=var, status=value))

def print_logs_help():
    """Mostra ajuda específica para o comando logs"""
    help_text = LOGS_HELP_MESSAGES.get(current_lang_code, LOGS_HELP_MESSAGES['en'])
    print(help_text)

def handle_logs(args):
    """Gerencia arquivos de log"""
    if not os.path.exists(LOG_FILE):
        print(get_string('MSG_NO_LOG_FILE_FOUND'))
        return
    
    if args.clear:
        try:
            with open(LOG_FILE, 'w') as f:
                f.write('')
            print(get_string('MSG_LOG_FILE_CLEARED'))
        except Exception as e:
            print(get_string('MSG_ERROR_PREFIX', message=f"Erro ao limpar log: {e}"))
        return
    
    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
        
        # Filtrar por data se especificado
        if args.since or args.until:
            filtered_lines = []
            for line in lines:
                if line.strip():
                    try:
                        date_str = line.split(' - ')[0]
                        log_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S,%f')
                        
                        if args.since:
                            since_date = datetime.strptime(args.since, '%Y-%m-%d')
                            if log_date.date() < since_date.date():
                                continue
                        
                        if args.until:
                            until_date = datetime.strptime(args.until, '%Y-%m-%d')
                            if log_date.date() > until_date.date():
                                continue
                        
                        filtered_lines.append(line)
                    except ValueError:
                        # Se não conseguir parsear a data, inclui a linha
                        filtered_lines.append(line)
            lines = filtered_lines
        
        # Filtrar por texto se especificado
        if args.filter:
            lines = [line for line in lines if args.filter.lower() in line.lower()]
        
        # Filtrar apenas erros se especificado
        if args.errors:
            lines = [line for line in lines if 'ERROR' in line]
        
        # Pegar últimas N linhas se especificado
        if args.tail:
            lines = lines[-args.tail:]
        
        # Exportar se especificado
        if args.export:
            try:
                with open(args.export, 'w') as f:
                    f.writelines(lines)
                print(get_string('MSG_LOGS_EXPORTED_TO', export=args.export))
            except Exception as e:
                print(get_string('MSG_ERROR_PREFIX', message=f"Erro ao exportar: {e}"))
        else:
            # Mostrar logs
            for line in lines:
                print(line.rstrip())
    
    except Exception as e:
        print(get_string('MSG_ERROR_PREFIX', message=f"Erro ao ler logs: {e}"))

def main():
    
    # Inicializar idioma
    initialize_language()

    parser = argparse.ArgumentParser(
        description=ARGPARSE_MESSAGES.get(current_lang_code, ARGPARSE_MESSAGES['en'])['description'],
        add_help=True,
        usage=ARGPARSE_MESSAGES.get(current_lang_code, ARGPARSE_MESSAGES['en'])['grabtext_usage_full']
    )
    
    # Argumentos globais
    parser.add_argument('--version', action='version', version=f'GrabText {VERSION}')
    parser.add_argument('--ocr-engine', choices=['tesseract', 'easyocr', 'google_cloud'], 
                       default='tesseract', help='Motor OCR a ser utilizado')
    parser.add_argument('--preprocessing', choices=['none', 'text_enhancement', 'low_quality', 'handwriting', 'document_scan'], 
                       default='none', help='Tipo de pré-processamento de imagem')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode with verbose output')
    parser.add_argument('--verbose', action='store_true', help='Show detailed progress information')
    parser.add_argument('--config', action='store_true', help='Show current configuration')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands', required=False)

    # === COMANDOS PRINCIPAIS ===
    
    # Grab command - Captura da tela
    grab_parser = subparsers.add_parser(
        'grab',
        help=ARGPARSE_MESSAGES.get(current_lang_code, ARGPARSE_MESSAGES['en'])['grab_help'],
        usage=ARGPARSE_MESSAGES.get(current_lang_code, ARGPARSE_MESSAGES['en'])['grab_usage']
    )
    grab_parser.add_argument('--lang', '-l', choices=['pt', 'en'], help='Language for OCR (default: pt)')
    grab_parser.add_argument('--silent', '-s', action='store_true', help='No notifications')
    grab_parser.add_argument('--output', '-o', help='Save to file')
    grab_parser.add_argument('--no-clipboard', action='store_true', help='Don\'t copy to clipboard')
    grab_parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    grab_parser.add_argument('path', nargs='?', help='Image file or directory to process/monitor')
    grab_parser.add_argument('--format', '-f', choices=['text', 'json', 'csv'], default='text', help='Output format')
    grab_parser.add_argument('--recursive', '-r', action='store_true', help='Process directory recursively')
    grab_parser.add_argument('--watch', '-w', action='store_true', help='Monitor directory for new images')
    grab_parser.add_argument('--batch', '-b', action='store_true', help='Process multiple images')

    # Process command - Processar arquivos existentes
    process_parser = subparsers.add_parser(
        'process',
        help=ARGPARSE_MESSAGES.get(current_lang_code, ARGPARSE_MESSAGES['en'])['process_help'],
        usage=ARGPARSE_MESSAGES.get(current_lang_code, ARGPARSE_MESSAGES['en'])['process_usage']
    )
    process_parser.add_argument('path', help='Image file or directory to process')
    process_parser.add_argument('--lang', '-l', choices=['pt', 'en'], help='Language for OCR (default: pt)')
    process_parser.add_argument('--output', '-o', help='Save to file')
    process_parser.add_argument('--format', '-f', choices=['text', 'json', 'csv'], default='text', help='Output format')
    process_parser.add_argument('--recursive', '-r', action='store_true', help='Process directory recursively')
    process_parser.add_argument('--batch', action='store_true', help='Process multiple images')
    process_parser.add_argument('--silent', '-s', action='store_true', help='No notifications')
    process_parser.add_argument('--no-clipboard', action='store_true', help='Don\'t copy to clipboard')
    process_parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')

    # Monitor command - Monitorar diretórios
    monitor_parser = subparsers.add_parser(
        'monitor',
        help=ARGPARSE_MESSAGES.get(current_lang_code, ARGPARSE_MESSAGES['en'])['monitor_help'],
        usage=ARGPARSE_MESSAGES.get(current_lang_code, ARGPARSE_MESSAGES['en'])['monitor_usage']
    )
    monitor_parser.add_argument('directory', help='Directory to monitor')
    monitor_parser.add_argument('--lang', '-l', choices=['pt', 'en'], help='Language for OCR (default: pt)')
    monitor_parser.add_argument('--recursive', '-r', action='store_true', help='Monitor recursively')
    monitor_parser.add_argument('--format', '-f', choices=['text', 'json', 'csv'], default='text', help='Output format')
    monitor_parser.add_argument('--output', '-o', help='Save to file')
    monitor_parser.add_argument('--silent', '-s', action='store_true', help='No notifications')
    monitor_parser.add_argument('--no-clipboard', action='store_true', help='Don\'t copy to clipboard')

    # === COMANDOS DE UTILIDADE ===
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help=ARGPARSE_MESSAGES.get(current_lang_code, ARGPARSE_MESSAGES['en'])['logs_help'])
    logs_parser.add_argument('--show', '-s', action='store_true', help='Show logs')
    logs_parser.add_argument('--clear', '-c', action='store_true', help='Clear log file')
    logs_parser.add_argument('--tail', '-t', type=int, default=50, help='Show last N lines')
    logs_parser.add_argument('--since', '-S', help='Show logs since date (YYYY-MM-DD)')
    logs_parser.add_argument('--until', '-u', help='Show logs until date (YYYY-MM-DD)')
    logs_parser.add_argument('--export', '-e', help='Export logs to file')
    logs_parser.add_argument('--errors', action='store_true', help='Show only errors')
    logs_parser.add_argument('--filter', '-f', help='Filter logs by text')

    # Status command
    status_parser = subparsers.add_parser('status', help=ARGPARSE_MESSAGES.get(current_lang_code, ARGPARSE_MESSAGES['en'])['status_help'])
    
    # Config command
    config_parser = subparsers.add_parser('config', help=ARGPARSE_MESSAGES.get(current_lang_code, ARGPARSE_MESSAGES['en'])['config_help'])
    
    # Language commands
    get_lang_parser = subparsers.add_parser('get-lang', help=ARGPARSE_MESSAGES.get(current_lang_code, ARGPARSE_MESSAGES['en'])['get_lang_help'])
    
    set_lang_parser = subparsers.add_parser('set-lang', help=ARGPARSE_MESSAGES.get(current_lang_code, ARGPARSE_MESSAGES['en'])['set_lang_help'])
    set_lang_parser.add_argument('language', nargs='?', choices=['pt', 'en'], help='Language to set (pt/en)')
    set_lang_parser.add_argument('--silent', '-s', action='store_true', help='No notifications')
    
    # Help command
    help_parser = subparsers.add_parser('help', help=ARGPARSE_MESSAGES.get(current_lang_code, ARGPARSE_MESSAGES['en'])['help_help'])
    
    # Version command
    version_parser = subparsers.add_parser('version', help=ARGPARSE_MESSAGES.get(current_lang_code, ARGPARSE_MESSAGES['en'])['version_help'])
    version_parser.set_defaults(func=lambda _: print(f'GrabText {VERSION}'))

    try:
        args = parser.parse_args()
        
        # Salvar nível de log atual
        original_log_level = logging.getLogger().level
        
        # Configurar logging baseado nas opções globais
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logging.debug(get_message('debug_mode_enabled'))
        elif args.verbose:
            logging.getLogger().setLevel(logging.INFO)
            logging.info(get_message('verbose_mode_enabled'))
            
        # Mostrar configuração se solicitado
        if args.config:
            handle_config_command()
            return
        
        # Se nenhum comando foi fornecido
        if not args.command:
            # Em modo debug/verbose sem subcomando, exibir status em vez de abrir GUI
            if args.debug or args.verbose or args.config:
                handle_status_command()
                return

            # Caso contrário, comportamento padrão: captura da tela
            grab_args = argparse.Namespace(
                path=None,
                lang=None,
                output=None,
                format='text',
                recursive=False,
                watch=False,
                batch=False,
                silent=False,
                no_clipboard=False,
                dry_run=args.dry_run
            )
            handle_grab_command(grab_args)
            return
    except argparse.ArgumentError as e:
        print(get_string('MSG_INVALID_COMMAND_ERROR'))
        print(get_string('MSG_EXAMPLES_HEADER'))
        print(get_string('MSG_GRAB_EXAMPLE'))
        print(get_string('MSG_PROCESS_IMAGE_EXAMPLE'))
        return

    if args.command == 'help':
        print_help()
        return
        
    if args.command == 'version':
        print(f'GrabText {VERSION}')
        return

    if args.command == 'config':
        handle_config_command()
        return

    if args.command == 'status':
        handle_status_command()
        return

    if args.command == 'get-lang':
        handle_get_lang_command()
        return

    if args.command == 'set-lang':
        handle_set_lang_command(args)
        return

    if args.command == 'logs':
        # Se não houver argumentos para logs, mostra ajuda específica
        if len(sys.argv) == 2:
            print_logs_help()
            return
        # Registrar início da sessão apenas para comandos que realmente executam
        logging.info(LOG_MESSAGES['SESSION_START'])
        handle_logs(args)
        return
        
    if args.command == 'grab':
        # Registrar início da sessão apenas para comandos que realmente executam
        logging.info(LOG_MESSAGES['SESSION_START'])
        # Modo GUI - capturar da tela
        try:
            handle_grab_command(args)
        finally:
            # Restaurar nível de log original
            logging.getLogger().setLevel(original_log_level)
        return

    if args.command == 'process':
        # Registrar início da sessão apenas para comandos que realmente executam
        logging.info(LOG_MESSAGES['SESSION_START'])
        # Processar arquivo ou diretório existente
        try:
            handle_process_command(args)
        finally:
            # Restaurar nível de log original
            logging.getLogger().setLevel(original_log_level)
        return

    if args.command == 'monitor':
        # Registrar início da sessão apenas para comandos que realmente executam
        logging.info(LOG_MESSAGES['SESSION_START'])
        # Monitorar diretório
        try:
            handle_monitor_command(args)
        finally:
            # Restaurar nível de log original
            logging.getLogger().setLevel(original_log_level)
        return

if __name__ == "__main__":
    main()