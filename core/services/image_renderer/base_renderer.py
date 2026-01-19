from PIL import Image, ImageDraw, ImageFont
import os

class BaseRenderer:
    """
    Classe base para renderização de imagens.
    Contém métodos comuns de desenho (header, footer) e gerenciamento de fontes.
    """
    def __init__(self):
        # Cores do tema - Paleta do Dashboard GS
        self.bg_color = (195, 195, 195)
        self.card_color = (26, 26, 26)
        self.text_color = (255, 255, 255)
        self.accent_color = (201, 169, 98)
        self.gold_color = (201, 169, 98)
        self.header_color = (26, 26, 26)
        self.muted_text = (180, 180, 180)
        self.label_color = (140, 140, 140)
        
        # Dimensões
        self.width = 800
        self.padding = 40
        self.line_height = 50
        
        # Carregar fonte padrao
        self.font_path = self._find_font()
    
    def _find_font(self):
        """Encontra uma fonte disponível no sistema (Prioridade: Montserrat)"""
        possible_fonts = [
            "C:/Windows/Fonts/Montserrat-Regular.ttf",
            "C:/Windows/Fonts/Montserrat-Medium.ttf",
            "C:/Windows/Fonts/segoeuil.ttf",
            "C:/Windows/Fonts/segoeuisl.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/calibril.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
        for font in possible_fonts:
            if os.path.exists(font):
                return font
        return None
    
    def _find_bold_font(self):
        """Encontra fonte bold (Prioridade: Montserrat-Bold)"""
        possible_fonts = [
            "C:/Windows/Fonts/Montserrat-Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/verdanab.ttf",
            "C:/Windows/Fonts/tahomabd.ttf",
        ]
        for font in possible_fonts:
            if os.path.exists(font):
                return font
        return self.font_path
    
    def _find_serif_font(self):
        """Encontra fonte Serif para o Logo (Prioridade: Times/Georgia)"""
        possible_fonts = [
            "C:/Windows/Fonts/times.ttf", 
            "C:/Windows/Fonts/georgia.ttf",
            "C:/Windows/Fonts/constan.ttf",
        ]
        for font in possible_fonts:
            if os.path.exists(font):
                return font
        return None
    
    def _get_font(self, size, bold=False):
        """Retorna uma instância de fonte (Montserrat/fallback)"""
        if bold:
            font_path = self._find_bold_font() or self.font_path
        else:
            font_path = self.font_path
            
        if font_path:
            return ImageFont.truetype(font_path, size)
        else:
            return ImageFont.load_default()

    def _draw_header(self, draw, title_text, date_text):
        """
        Desenha o cabeçalho padrão com ajuste dinâmico de fonte.
        """
        header_h = 70
        margin = self.padding
        
        # Fundo do header
        draw.rectangle([(0, 0), (self.width, header_h)], fill=self.bg_color)
        
        # Título composto
        full_header = f"{title_text} - {date_text}"
        
        # Calcular largura disponível
        logo_size = 50
        max_width = self.width - (2 * margin) - logo_size - 10
        
        # Ajuste dinâmico de fonte
        font_size = 18
        font = self._get_font(font_size, bold=True)
        bbox = draw.textbbox((0, 0), full_header, font=font)
        text_width = bbox[2] - bbox[0]
        
        while text_width > max_width and font_size > 10:
            font_size -= 1
            font = self._get_font(font_size, bold=True)
            bbox = draw.textbbox((0, 0), full_header, font=font)
            text_width = bbox[2] - bbox[0]
            
        draw.text((margin, 25), full_header, font=font, fill=self.card_color)
        
        # Logo GS
        try:
            serif_font_path = self._find_serif_font()
            if serif_font_path:
                font_gs = ImageFont.truetype(serif_font_path, 28)
            else:
                font_gs = self._get_font(28, bold=True)
                
            logo_size = 50
            logo_x = self.width - margin - logo_size
            
            # Caixa preta com borda amarela
            draw.rounded_rectangle(
                [(logo_x, 10), (logo_x + logo_size, 10 + logo_size)],
                radius=6, fill=self.card_color, outline=self.accent_color, width=2
            )
            
            # Texto GS
            gs_bbox = draw.textbbox((0, 0), "GS", font=font_gs)
            gs_tw = gs_bbox[2] - gs_bbox[0]
            gs_th = gs_bbox[3] - gs_bbox[1]
            draw.text((logo_x + (logo_size - gs_tw)/2, 10 + (logo_size - gs_th)/2 - 4), "GS", font=font_gs, fill=self.accent_color)
            
        except Exception:
            draw.text((self.width - 50, 20), "GS", font=self._get_font(20, bold=True), fill=self.accent_color)
        
        # Linha dourada
        draw.rectangle([(0, header_h - 4), (self.width, header_h)], fill=self.accent_color)
        
        return header_h

    def _draw_footer(self, draw, y_bottom):
        """
        Desenha o rodapé padrão no final da imagem.
        """
        footer_text = "Grupo Studio • Automação Power BI"
        
        font_footer = self._get_font(14)
        bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
        text_w = bbox[2] - bbox[0]
        
        x = (self.width - text_w) / 2
        y = y_bottom - 40 
        
        draw.text((x, y), footer_text, font=font_footer, fill=(100, 100, 100))
