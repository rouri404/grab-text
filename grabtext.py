#!/usr/bin/env python3
# grabtext.py

import sys
import io
import subprocess
import pytesseract
from PIL import Image
import os
import logging
import time
import argparse
import json
import csv
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, 'grabtext.log')
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s'
)

LOG_MESSAGES = {
    'SESSION_START': "Session started.",
    'NO_IMAGE_DATA': "No image data received from stdin.",
    'OCR_SUCCESS': "OCR success: lang={lang}, chars={chars}, preview=\"{preview}\"",
    'OCR_NO_TEXT': "OCR complete: No text detected.",
    'CLIPBOARD_ERROR': "Clipboard tool not found (xclip/wl-copy).",
    'NOTIFY_SEND_MISSING': "notify-send command not found.",
    'NOTIFY_SEND_ERROR': "notify-send command failed: {e}",
    'UNEXPECTED_ERROR': "Unexpected error: {e}",
}

current_lang_code = os.environ.get('GRABTEXT_LANG', 'pt').lower()
tesseract_lang_code = 'por' if current_lang_code == 'pt' else 'eng'

MESSAGES = {
    'pt': {
        'error_clipboard_install': "Falha ao copiar texto. Instale 'xclip' ou 'wl-copy'.",
        'grabtext_error_title': "GrabText: Erro",
        'text_extracted_title': "Texto extraído com sucesso!",
        'text_extracted_content': "Conteúdo:\n\"{preview}\"",
        'no_text_detected_title': "GrabText",
        'no_text_detected_content': "Nenhum texto detectado na área selecionada.",
        'unexpected_error_title': "GrabText: Erro Inesperado",
        'unexpected_error_content': "Ocorreu um problema: {preview}",
    },
    'en': {
        'error_clipboard_install': "Failed to copy text. Please install 'xclip' or 'wl-copy'.",
        'grabtext_error_title': "GrabText: Error",
        'text_extracted_title': "Text successfully extracted!",
        'text_extracted_content': "Content:\n\"{preview}\"",
        'no_text_detected_title': "GrabText",
        'no_text_detected_content': "No text detected in the selected area.",
        'unexpected_error_title': "GrabText: Unexpected Error",
        'unexpected_error_content': "An issue occurred: {preview}",
    }
}

def get_message(key, **kwargs):
    return MESSAGES.get(current_lang_code, MESSAGES['pt']).get(key).format(**kwargs)

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
    try:
        subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode('utf-8'), check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        try:
            subprocess.run(['wl-copy'], input=text.encode('utf-8'), check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            logging.error(LOG_MESSAGES['CLIPBOARD_ERROR'])
            send_notification(
                get_message('grabtext_error_title'),
                get_message('error_clipboard_install'),
                icon_name="dialog-error",
                expire_timeout=7000
            )

class ImageHandler(FileSystemEventHandler):
    def __init__(self, process_func):
        self.process_func = process_func

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            self.process_func(event.src_path)

def process_image_file(image_path, format='text'):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang=tesseract_lang_code)
        
        if format == 'json':
            return json.dumps({'file': image_path, 'text': text.strip()})
        elif format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([image_path, text.strip()])
            return output.getvalue()
        else:
            return text.strip()
    except Exception as e:
        logging.error(f"Error processing {image_path}: {str(e)}")
        return None

def process_directory(dir_path, recursive=False, format='text'):
    pattern = '**/*' if recursive else '*'
    results = []
    path = Path(dir_path)
    for img_path in path.glob(pattern):
        if img_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            result = process_image_file(str(img_path), format)
            if result:
                results.append(result)
    return results

def handle_logs(args):
    log_path = LOG_FILE
    if not os.path.exists(log_path):
        print("No log file found.")
        return

    if args.clear:
        open(log_path, 'w').close()
        print("Log file cleared.")
        return

    with open(log_path, 'r') as f:
        logs = f.readlines()

    if args.export:
        with open(args.export, 'w') as f:
            f.writelines(logs)
        print(f"Logs exported to {args.export}")
        return

    filtered_logs = logs
    if args.since:
        since_date = datetime.strptime(args.since, '%Y-%m-%d')
        filtered_logs = [log for log in filtered_logs if datetime.strptime(log.split()[0], '%Y-%m-%d') >= since_date]
    
    if args.until:
        until_date = datetime.strptime(args.until, '%Y-%m-%d')
        filtered_logs = [log for log in filtered_logs if datetime.strptime(log.split()[0], '%Y-%m-%d') <= until_date]
    
    if args.errors:
        filtered_logs = [log for log in filtered_logs if 'ERROR' in log]
    
    if args.filter:
        filtered_logs = [log for log in filtered_logs if args.filter in log]

    if args.tail:
        filtered_logs = filtered_logs[-args.tail:]

    for log in filtered_logs:
        print(log.strip())

HELP_MESSAGES = {
    'en': """
╭─────────────────────────────────────────────────╮
│                   GrabText                      │
│        Text extraction tool for Linux           │
╰─────────────────────────────────────────────────╯

Usage:
  grabtext <command> [options]

Commands:
  grab     Capture and extract text
    --gui                  Use GUI mode (default)
    -l, --lang            Language for OCR (pt/en)
    -i, --image           Process existing image/directory
    -o, --output          Save output to file
    -f, --format          Output format (text/json/csv)
    -r, --recursive       Process directory recursively
    --watch               Monitor directory for new images
    --batch               Process multiple images
    -s, --silent          No notifications

  logs     Manage log files
    --tail N              Show last N lines
    --since DATE          Show logs since date (YYYY-MM-DD)
    --until DATE          Show logs until date
    --errors              Show only errors
    --filter TEXT         Filter logs by text
    --export FILE         Export logs to file
    --clear               Clear log file

Examples:
  grabtext grab --gui           # Launch GUI mode
  grabtext grab -i image.png    # Process image file
  grabtext grab -i ./images -r  # Process directory
  grabtext logs --tail 10       # Show last 10 log entries

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

Comandos:
  grab     Capturar e extrair texto
    --gui                  Usar modo GUI (padrão)
    -l, --lang            Idioma para OCR (pt/en)
    -i, --image           Processar imagem/diretório existente
    -o, --output          Salvar saída em arquivo
    -f, --format          Formato de saída (text/json/csv)
    -r, --recursive       Processar diretório recursivamente
    --watch               Monitorar diretório por novas imagens
    --batch               Processar múltiplas imagens
    -s, --silent          Sem notificações

  logs     Gerenciar arquivos de log
    --tail N              Mostrar últimas N linhas
    --since DATA          Mostrar logs desde DATA (AAAA-MM-DD)
    --until DATA          Mostrar logs até DATA
    --errors              Mostrar apenas erros
    --filter TEXTO        Filtrar logs por texto
    --export ARQUIVO      Exportar logs para arquivo
    --clear               Limpar arquivo de log

Exemplos:
  grabtext grab --gui           # Iniciar modo GUI
  grabtext grab -i imagem.png   # Processar arquivo de imagem
  grabtext grab -i ./imagens -r # Processar diretório
  grabtext logs --tail 10       # Mostrar últimos 10 logs

Para mais informações, visite:
https://github.com/rouri404/grabtext

Feito por Gabriel Couto Ribeiro (rouri404) - 2025
"""
}

def print_help():
    # Use o mesmo código de idioma que já está configurado para o OCR
    help_text = HELP_MESSAGES.get(current_lang_code, HELP_MESSAGES['en'])
    print(help_text)

def main():
    parser = argparse.ArgumentParser(description='GrabText - Text extraction tool', add_help=False)
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Help command
    help_parser = subparsers.add_parser('help', help='Show this help message')

    # Grab command
    grab_parser = subparsers.add_parser('grab', help='Capture and extract text')
    grab_parser.add_argument('--lang', '-l', choices=['pt', 'en'], help='Language for OCR')
    grab_parser.add_argument('--silent', '-s', action='store_true', help='No notifications')
    grab_parser.add_argument('--output', '-o', help='Save to file')
    grab_parser.add_argument('--clipboard', '-c', action='store_true', default=True, help='Copy to clipboard')
    grab_parser.add_argument('--image', '-i', help='Use existing image or directory')
    grab_parser.add_argument('--recursive', '-r', action='store_true', help='Process directory recursively')
    grab_parser.add_argument('--format', '-f', choices=['text', 'json', 'csv'], default='text', help='Output format')
    grab_parser.add_argument('--batch', action='store_true', help='Process multiple images')
    grab_parser.add_argument('--watch', action='store_true', help='Monitor directory for new images')

    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Manage log files')
    logs_parser.add_argument('--show', '-s', action='store_true', help='Show logs')
    logs_parser.add_argument('--clear', '-c', action='store_true', help='Clear log file')
    logs_parser.add_argument('--tail', '-t', type=int, default=50, help='Show last N lines')
    logs_parser.add_argument('--since', '-S', help='Show logs since date (YYYY-MM-DD)')
    logs_parser.add_argument('--until', '-u', help='Show logs until date (YYYY-MM-DD)')
    logs_parser.add_argument('--export', '-e', help='Export logs to file')
    logs_parser.add_argument('--errors', action='store_true', help='Show only errors')
    logs_parser.add_argument('--filter', '-f', help='Filter logs by text')

    try:
        args = parser.parse_args()
    except:
        print_help()
        return

    if not args.command:
        print_help()
        return

    if args.command == 'logs':
        handle_logs(args)
        return

    if args.command == 'help':
        print_help()
        return

    logging.info(LOG_MESSAGES['SESSION_START'])
    try:
        if args.command == 'grab' and args.image:
            if os.path.isdir(args.image):
                if args.watch:
                    event_handler = ImageHandler(lambda x: process_image_file(x, args.format))
                    observer = Observer()
                    observer.schedule(event_handler, args.image, recursive=args.recursive)
                    observer.start()
                    print(f"Watching directory {args.image} for new images...")
                    try:
                        while True:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        observer.stop()
                    observer.join()
                else:
                    results = process_directory(args.image, args.recursive, args.format)
                    if args.output:
                        with open(args.output, 'w') as f:
                            for result in results:
                                f.write(f"{result}\n")
                    else:
                        for result in results:
                            print(result)
            else:
                result = process_image_file(args.image, args.format)
                if result:
                    if args.output:
                        with open(args.output, 'w') as f:
                            f.write(result)
                    if args.clipboard:
                        copy_to_clipboard(result)
                    if not args.silent:
                        print(result)
        else:
            image_data = sys.stdin.buffer.read()
            if not image_data:
                logging.warning(LOG_MESSAGES['NO_IMAGE_DATA'])
                return

        image_stream = io.BytesIO(image_data)
        img = Image.open(image_stream)
        
        extracted_text = pytesseract.image_to_string(img, lang=tesseract_lang_code)

        if extracted_text.strip():
            clean_text = extracted_text.strip()
            copy_to_clipboard(clean_text)
            
            preview = (clean_text[:70]).replace("\n", " ")

            logging.info(LOG_MESSAGES['OCR_SUCCESS'].format(
                lang=tesseract_lang_code,
                chars=len(clean_text),
                preview=preview
            ))
            
            send_notification(
                get_message('text_extracted_title'),
                get_message('text_extracted_content', preview=preview),
                icon_name="edit-copy",
                expire_timeout=6000
            )
        else:
            logging.info(LOG_MESSAGES['OCR_NO_TEXT'])
            send_notification(
                get_message('no_text_detected_title'),
                get_message('no_text_detected_content'),
                icon_name="dialog-information",
                expire_timeout=4000
            )

    except Exception as e:
        logging.error(LOG_MESSAGES['UNEXPECTED_ERROR'].format(e=e), exc_info=True)
        
        error_message = str(e)
        preview = (error_message[:100] + '...') if len(error_message) > 100 else error_message
        
        send_notification(
            get_message('unexpected_error_title'),
            get_message('unexpected_error_content', preview=preview),
            icon_name="dialog-error",
            expire_timeout=8000
        )

if __name__ == "__main__":
    main()