#!/usr/bin/env python3
# Módulo de pré-processamento de imagem para GrabText

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import logging

class ImageProcessor:
    def __init__(self):
        self.preprocessing_steps = []
    
    def add_grayscale(self):
        """Adiciona conversão para escala de cinza"""
        self.preprocessing_steps.append('grayscale')
        return self
    
    def add_blur(self, kernel_size=3):
        """Adiciona desfoque para reduzir ruído"""
        self.preprocessing_steps.append(('blur', kernel_size))
        return self
    
    def add_threshold(self, method='adaptive', block_size=11, c=2):
        """Adiciona binarização"""
        self.preprocessing_steps.append(('threshold', method, block_size, c))
        return self
    
    def add_denoise(self):
        """Adiciona remoção de ruído"""
        self.preprocessing_steps.append('denoise')
        return self
    
    def add_contrast_enhancement(self, factor=1.5):
        """Adiciona aumento de contraste"""
        self.preprocessing_steps.append(('contrast', factor))
        return self
    
    def add_sharpen(self):
        """Adiciona nitidez"""
        self.preprocessing_steps.append('sharpen')
        return self
    
    def add_resize(self, scale_factor=2.0):
        """Adiciona redimensionamento"""
        self.preprocessing_steps.append(('resize', scale_factor))
        return self
    
    def clear_steps(self):
        """Limpa todos os passos de pré-processamento"""
        self.preprocessing_steps.clear()
        return self
    
    def preprocess(self, image):
        """Aplica pré-processamento na imagem"""
        try:
            # Converter PIL Image para OpenCV format se necessário
            if isinstance(image, Image.Image):
                img_array = np.array(image)
                if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                    # RGB para BGR
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            else:
                img_array = image.copy()
            
            original_shape = img_array.shape
            
            for step in self.preprocessing_steps:
                try:
                    if step == 'grayscale':
                        if len(img_array.shape) == 3:
                            img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
                        logging.debug("Applied grayscale conversion")
                    
                    elif isinstance(step, tuple) and step[0] == 'blur':
                        kernel_size = step[1]
                        img_array = cv2.GaussianBlur(img_array, (kernel_size, kernel_size), 0)
                        logging.debug(f"Applied blur with kernel size {kernel_size}")
                    
                    elif isinstance(step, tuple) and step[0] == 'threshold':
                        method, block_size, c = step[1], step[2], step[3]
                        
                        if len(img_array.shape) == 3:
                            img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
                        
                        if method == 'adaptive':
                            img_array = cv2.adaptiveThreshold(
                                img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                cv2.THRESH_BINARY, block_size, c
                            )
                        elif method == 'otsu':
                            _, img_array = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                        else:
                            _, img_array = cv2.threshold(img_array, 127, 255, cv2.THRESH_BINARY)
                        
                        logging.debug(f"Applied {method} threshold")
                    
                    elif step == 'denoise':
                        if len(img_array.shape) == 3:
                            img_array = cv2.fastNlMeansDenoisingColored(img_array, None, 10, 10, 7, 21)
                        else:
                            img_array = cv2.fastNlMeansDenoising(img_array, None, 10, 7, 21)
                        logging.debug("Applied denoising")
                    
                    elif isinstance(step, tuple) and step[0] == 'contrast':
                        factor = step[1]
                        # Converter para PIL para enhance
                        if len(img_array.shape) == 2:
                            pil_img = Image.fromarray(img_array, mode='L')
                        else:
                            pil_img = Image.fromarray(cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB))
                        
                        enhancer = ImageEnhance.Contrast(pil_img)
                        pil_img = enhancer.enhance(factor)
                        
                        # Voltar para OpenCV
                        if len(img_array.shape) == 2:
                            img_array = np.array(pil_img)
                        else:
                            img_array = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                        
                        logging.debug(f"Applied contrast enhancement with factor {factor}")
                    
                    elif step == 'sharpen':
                        # Converter para PIL para sharpen
                        if len(img_array.shape) == 2:
                            pil_img = Image.fromarray(img_array, mode='L')
                        else:
                            pil_img = Image.fromarray(cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB))
                        
                        pil_img = pil_img.filter(ImageFilter.SHARPEN)
                        
                        # Voltar para OpenCV
                        if len(img_array.shape) == 2:
                            img_array = np.array(pil_img)
                        else:
                            img_array = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                        
                        logging.debug("Applied sharpening")
                    
                    elif isinstance(step, tuple) and step[0] == 'resize':
                        scale_factor = step[1]
                        height, width = img_array.shape[:2]
                        new_height, new_width = int(height * scale_factor), int(width * scale_factor)
                        img_array = cv2.resize(img_array, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                        logging.debug(f"Applied resize with scale factor {scale_factor}")
                
                except Exception as e:
                    logging.warning(f"Failed to apply preprocessing step {step}: {e}")
                    continue
            
            # Converter de volta para PIL Image
            if len(img_array.shape) == 2:
                return Image.fromarray(img_array, mode='L')
            else:
                return Image.fromarray(cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB))
        
        except Exception as e:
            logging.error(f"Error in image preprocessing: {e}")
            return image  # Retorna imagem original se falhar

# Presets de pré-processamento comuns
def get_preset_text_enhancement():
    """Preset para melhorar texto em imagens"""
    return (ImageProcessor()
            .add_grayscale()
            .add_blur(3)
            .add_contrast_enhancement(1.5)
            .add_sharpen()
            .add_threshold('adaptive', 11, 2))

def get_preset_low_quality():
    """Preset para imagens de baixa qualidade"""
    return (ImageProcessor()
            .add_grayscale()
            .add_denoise()
            .add_contrast_enhancement(2.0)
            .add_resize(2.0)
            .add_threshold('otsu'))

def get_preset_handwriting():
    """Preset para texto manuscrito"""
    return (ImageProcessor()
            .add_grayscale()
            .add_blur(5)
            .add_contrast_enhancement(1.8)
            .add_sharpen()
            .add_threshold('adaptive', 15, 3))

def get_preset_document_scan():
    """Preset para documentos digitalizados"""
    return (ImageProcessor()
            .add_grayscale()
            .add_denoise()
            .add_contrast_enhancement(1.3)
            .add_threshold('otsu'))

# Verificar se OpenCV está disponível
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("OpenCV not available. Image preprocessing features will be limited.")
