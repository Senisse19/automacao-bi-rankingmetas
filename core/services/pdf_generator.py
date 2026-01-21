from fpdf import FPDF
from datetime import datetime
import os

class PdfGenerator(FPDF):
    def __init__(self, base_url="https://bi.grupostudio.tec.br"):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.base_url = base_url.rstrip('/')
        self.font_family_main = "Arial"
        
        # Colors (RGB) - Strict Match from BaseRenderer.py
        self.colors = {
            "bg": (195, 195, 195),          # BaseRenderer.bg_color
            "card": (26, 26, 26),           # BaseRenderer.card_color
            "text": (255, 255, 255),        # BaseRenderer.text_color
            "accent": (201, 169, 98),       # BaseRenderer.accent_color (Gold)
            "muted": (180, 180, 180),       # BaseRenderer.muted_text
            "label": (140, 140, 140),       # BaseRenderer.label_color
            "header_bg": (26, 26, 26)       # BaseRenderer.header_color is same as card? No, usually distinct or same. 
                                            # BaseRenderer._draw_header fills rect with bg_color (195), then text.
        }

        # Locate font
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.font_path = os.path.join(base_dir, "assets", "fonts", "arial.ttf")
        
        # Register Font
        if os.path.exists(self.font_path):
            self.add_font("Arial", "", self.font_path)
            self.add_font("Arial", "B", self.font_path) 
            self.add_font("Arial", "I", self.font_path) 
        else:
            self.font_family_main = "Helvetica"

    def header(self):
        # Background Fill (Entire Page) - Critical to match image look
        # FPDF header runs on every page. We want full page BG.
        # Draw a big rect.
        self.set_fill_color(*self.colors["bg"])
        self.rect(0, 0, 210, 297, 'F')
        
        # Draw Top Header Block (Matches BaseRenderer._draw_header)
        # It says: draw.rectangle([(0, 0), (self.width, header_h)], fill=self.bg_color) 
        # Wait, BaseRenderer header bg IS the page bg (195,195,195).
        # But it draws a Gold Line at header_h - 4.
        
        header_height = 35 # approx 70px / 2 (mm conversion rough)
        
        # Gold Line at bottom of header
        self.set_fill_color(*self.colors["accent"])
        self.rect(0, header_height - 2, 210, 2, 'F')
        
        # GS Logo Simulation (Top Right)
        # Logic: Rounded Box (Dark) + Gold Border + "GS" text
        logo_size = 15
        logo_x = 185
        logo_y = 8
        
        # Box
        self.set_fill_color(*self.colors["card"])
        self.set_draw_color(*self.colors["accent"])
        self.set_line_width(0.5)
        self.rect(logo_x, logo_y, logo_size, logo_size, 'DF') # Draw and Fill
        
        # Text "GS"
        self.set_text_color(*self.colors["accent"])
        self.set_font(self.font_family_main, 'B', 14)
        # Center approx
        self.set_xy(logo_x, logo_y + 4)
        self.cell(logo_size, 6, "GS", 0, 0, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font(self.font_family_main, 'I', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'Grupo Studio • Automação Power BI • Página {self.page_no()}', 0, 0, 'C')

    def generate_unidades_pdf(self, data, report_type="daily", output_path="unidades_report.pdf"):
        self.add_page()
        
        # --- TITLE ---
        # BaseRenderer draws title at y=25px ~ 8mm? No, logic is relative.
        # Let's place it nicely.
        self.set_y(15) 
        self.set_text_color(*self.colors["card"]) # Title is dark (26,26,26)
        self.set_font(self.font_family_main, 'B', 14)
        
        title_type = "SEMANAL" if report_type == "weekly" else "DIÁRIO"
        start_date = data.get("start_date")
        end_date = data.get("date")
        
        if start_date == end_date:
            date_str = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        else:
            d1 = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d/%m/%Y")
            d2 = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d/%m/%Y")
            date_str = f"{d1} a {d2}"
            
        title_text = f"RELATÓRIO DE UNIDADES {title_type} - {date_str}"
        self.cell(0, 10, title_text, ln=True, align='L')
        
        self.ln(12) # Gap after header line

        # --- SECTIONS ---
        novas = data.get("new", [])
        canceladas = data.get("cancelled", [])
        upsell = data.get("upsell", [])

        self._render_section("NOVAS UNIDADES", novas, "new")
        self.ln(5)
        self._render_section("CANCELADAS", canceladas, "cancelled")
        self.ln(5)
        self._render_section("UPSELL", upsell, "upsell")

        self.output(output_path)
        return output_path

    def _render_section(self, title, items, context):
        if self.get_y() > 250:
            self.add_page()
            self.set_y(40)

        # Section Title
        self.set_text_color(40, 40, 40) # Slightly lighter than full black
        self.set_font(self.font_family_main, 'B', 12)
        count = len(items)
        self.cell(0, 6, f"{title} ({count})", ln=True)
        
        # Gold Line under section title
        self.set_draw_color(*self.colors["accent"])
        self.set_line_width(0.5)
        # Line length approx 60mm
        self.line(10, self.get_y()+1, 70, self.get_y()+1)
        self.ln(5)

        if not items:
            # Empty Box
            self.set_fill_color(*self.colors["card"])
            self.rect(10, self.get_y(), 190, 15, 'F')
            
            self.set_xy(10, self.get_y())
            self.set_text_color(*self.colors["muted"])
            self.set_font(self.font_family_main, 'B', 10)
            
            msg = f"Nenhuma unidade {context} nesta data"
            self.cell(190, 15, msg, 0, 1, 'C')
            self.ln(5)
            return

        # Render Items
        for i, item in enumerate(items):
            self._render_item_row(item, context, is_last=(i == len(items)-1))

    def _render_item_row(self, item, context, is_last):
        # Card Height approx 60px ~ 25mm? 
        # BaseRenderer uses variable height. Fixed height is cleaner for PDF.
        h = 28
        
        if self.get_y() + h > 280:
            self.add_page()
            self.set_y(40)

        x = 10
        y = self.get_y()
        w = 190
        
        # Background (Dark)
        self.set_fill_color(*self.colors["card"])
        self.rect(x, y, w, h, 'F')
        
        # Define Link Area (Entire Card)
        # Link to: https://bi.grupostudio.tec.br/reports/unidades?search={id}
        cid = item.get("codigo") or item.get("id")
        if cid:
             link_url = f"{self.base_url}/reports/unidades?search={cid}"
             self.link(x, y, w, h, link_url)

        # --- CONTENT ---
        # 1. Title (Gold)
        self.set_xy(x + 5, y + 2)
        self.set_text_color(*self.colors["accent"])
        self.set_font(self.font_family_main, 'B', 11)
        
        nome = str(item.get("nome") or "UNIDADE S/N").upper()
        codigo = str(item.get("codigo") or "")
        
        # Logic from BaseRenderer: if Code in Name -> Name, else "Unid: Code - Name"
        if codigo in nome and "UNIDADE" in nome:
            display_name = nome
        elif codigo:
            display_name = f"UNID: {codigo} - {nome}"
        else:
            display_name = nome
            
        self.cell(120, 6, display_name[:50], 0, 1)

        # 2. Value (Right)
        val = item.get("valor") or 0.0
        val_str = f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        self.set_xy(x + 130, y + 2)
        self.set_text_color(*self.colors["label"])
        self.set_font(self.font_family_main, '', 7)
        self.cell(55, 4, "VALOR AQUISIÇÃO", 0, 1, 'R')
        
        self.set_xy(x + 130, y + 6)
        self.set_text_color(*self.colors["text"])
        self.set_font(self.font_family_main, 'B', 10)
        self.cell(55, 5, val_str, 0, 0, 'R')

        # 3. Details (Row 2) - 3 Columns
        # Y position approx 15mm from top
        y_det = y + 14
        
        # Col 1: Cidade
        cidade = item.get("cidade") or "--"
        uf = item.get("uf") or "--"
        loc = f"{cidade} - {uf}"
        self._render_field(x + 5, y_det, "CIDADE / UF", loc[:30])
        
        # Col 2: Modelo
        lbl2 = "MODELO"
        val2 = str(item.get("modelo") or "-")
        if context == "cancelled": 
            lbl2 = "MOTIVO"
            val2 = str(item.get("motivo_cancelamento") or item.get("motivo") or "-")
            
        self._render_field(x + 70, y_det, lbl2, val2[:30])
        
        # Col 3: Consultor
        lbl3 = "CONSULTOR"
        val3 = str(item.get("consultor") or "-")
        if context == "cancelled":
            lbl3 = "DATA"
            val3 = str(item.get("data") or "-")
            
        self._render_field(x + 130, y_det, lbl3, val3[:25])
        
        # Separator Line (Simulated by gap or line? Original image has line)
        if not is_last:
             self.set_draw_color(60, 60, 60)
             self.line(x + 5, y + h, x + w - 5, y + h)

        self.set_y(y + h) # Next row
        
    def _render_field(self, x, y, label, value):
        self.set_xy(x, y)
        self.set_text_color(*self.colors["label"])
        self.set_font(self.font_family_main, '', 6)
        self.cell(50, 3, label, 0, 1)
        
        self.set_xy(x, y + 3)
        self.set_text_color(*self.colors["text"])
        self.set_font(self.font_family_main, 'B', 8)
        self.cell(50, 4, value, 0, 0)
