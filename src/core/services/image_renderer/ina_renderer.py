from PIL import Image, ImageDraw
from datetime import datetime
from .base_renderer import BaseRenderer


class InaRenderer(BaseRenderer):
    """
    Renderizador para o Painel INA (Inadimpl├¬ncia).
    """

    def generate_image(self, kpis, top10, output_path="ina_report.png", area_name="GERAL"):
        """
        Gera a imagem do relat├│rio di├írio do INA.
        """
        # Configurar dimens├Áes
        self.width = 800
        # Headers + KPIs + Tabela + Footer
        # Altura estimada: Header(100) + KPIs(150) + Tabela(50 + 10*40) + Footer(50) = ~750
        num_items = len(top10) if top10 else 0
        table_height = 60 + (num_items * 45)  # Header + rows
        kpi_section_h = 160

        # Footer precisa de espa├ºo extra para n├úo sobrepor o card
        total_height = 100 + kpi_section_h + table_height + 100

        img = Image.new("RGB", (self.width, total_height), self.bg_color)
        draw = ImageDraw.Draw(img)

        # 1. Header
        now_str = datetime.now().strftime("%d/%m/%Y")
        # Ajusta subt├¡tulo com a ├írea
        sub_text = f"Posi├º├úo: {now_str} | ├ürea: {area_name}"
        header_h = self._draw_header(draw, "PAINEL INA", sub_text)

        y = header_h + 20

        # 2. KPIs (Cards)
        # Layout: 2 linhas de 2 cards ou 1 linha de 4?
        # Vamos fazer 2 linhas de 2 cards para ficar leg├¡vel no mobile.
        self._draw_kpi_cards(draw, y, kpis)
        y += kpi_section_h + 20

        # 3. Tabela Top 10
        self._draw_top10_table(draw, y, top10)

        # 4. Footer
        self._draw_footer(draw, total_height)

        img.save(output_path)
        return output_path

    def _draw_kpi_cards(self, draw, start_y, kpis):
        """Desenha grid de KPIs"""
        margin = 30
        gap = 20
        card_h = 70

        # Defini├º├úo dos dados para exibir
        # Formato: (Titulo, Valor, CorDestaque?)
        cards_data = [
            ("VENCENDO HOJE", kpis.get("VencendoHoje"), True),  # Destaque
            ("INADIMPL├èNCIA TOTAL", kpis.get("Total"), False),
            ("M├ëDIA ATRASO (DIAS)", str(kpis.get("MediaAtraso", "-")), False),
            ("CONCILIA├ç├âO (D+2)", kpis.get("Conciliacao"), False),
        ]

        card_w = (self.width - 2 * margin - gap) / 2

        font_label = self._get_font(12, bold=True)
        font_value = self._get_font(18, bold=True)

        for i, (title, value, highlight) in enumerate(cards_data):
            col = i % 2
            row = i // 2

            x = margin + col * (card_w + gap)
            y = start_y + row * (card_h + gap)

            # Fundo do Card
            border = self.accent_color if highlight else self.card_color
            draw.rounded_rectangle(
                [(x, y), (x + card_w, y + card_h)],
                radius=10,
                fill=self.card_color,
                outline=border,
                width=2 if highlight else 0,
            )

            # Texto
            draw.text((x + 15, y + 10), title, font=font_label, fill=self.muted_text)

            # Valor (Alinhado a direita ou esquerda? Vamos esquerda mesmo)
            val_text = str(value) if value else "-"
            # Limpeza r├ípida visual
            # val_text = val_text.replace("R$ ", "R$") # Removido para manter estilo R$ 1.000

            draw.text((x + 15, y + 35), val_text, font=font_value, fill=self.text_color)

    def _draw_top10_table(self, draw, start_y, top10):
        """Desenha tabela Top 10 com estilo 'Big Black Card'"""
        margin = 30

        # Calcular altura da tabela
        num_rows = len(top10) if top10 else 1
        row_h = 45  # Aumentar um pouco a altura da linha para respiro
        header_h_space = 60
        table_h = header_h_space + (num_rows * row_h) + 30  # Padding bottom

        # 1. Desenhar o Card Preto de Fundo
        # Fundo bem escuro para contrastar
        card_bg = (15, 15, 15)
        draw.rounded_rectangle(
            [(margin, start_y), (self.width - margin, start_y + table_h)],
            radius=15,
            fill=card_bg,
            outline=(40, 40, 40),  # Borda sutil
            width=1,
        )

        # 2. T├¡tulo da Se├º├úo (Dentro do Card ou Fora? User disse "grande card com colunas", entao titulo pode ser dentro)
        # Vamos colocar padding interno
        inner_margin_x = margin + 20
        current_y = start_y + 20

        draw.text(
            (inner_margin_x, current_y),
            "TOP 10 INADIMPL├èNCIA AT├ë 90 DIAS",
            font=self._get_font(18, bold=True),
            fill=self.accent_color,
        )

        # 3. Cabe├ºalho da Tabela
        header_y = current_y + 40

        # Ajuste de Colunas com posi├º├Áes fixas e alinhamento consistente
        col_rank_x = inner_margin_x
        col_name_x = inner_margin_x + 40
        col_days_x = self.width - margin - 200  # Centro da coluna DIAS
        col_val_x = self.width - margin - 30  # Borda direita da coluna VALOR

        font_head = self._get_font(12, bold=True)
        header_color = (255, 255, 255)

        draw.text((col_rank_x, header_y), "#", font=font_head, fill=header_color)
        draw.text((col_name_x, header_y), "CLIENTE", font=font_head, fill=header_color)
        draw.text(
            (col_days_x, header_y),
            "DIAS",
            font=font_head,
            fill=header_color,
            anchor="mt",
        )  # Center-align
        draw.text(
            (col_val_x, header_y),
            "VALOR",
            font=font_head,
            fill=header_color,
            anchor="rt",
        )  # Right-align

        # Separator Line
        line_y = header_y + 25
        draw.line(
            [(inner_margin_x, line_y), (self.width - margin - 20, line_y)],
            fill=(60, 60, 60),
            width=1,
        )

        # 4. Linhas
        row_start_y = line_y + 15
        font_row = self._get_font(14)
        font_val_bold = self._get_font(14, bold=True)
        font_rank = self._get_font(14, bold=True)

        if not top10:
            draw.text(
                (self.width // 2, row_start_y + 20),
                "Nenhum dado encontrado.",
                font=font_row,
                fill=self.muted_text,
                anchor="mm",
            )
            return

        # Limites internos do card para o zebra striping
        card_left = margin + 2  # Dentro da borda do card
        card_right = self.width - margin - 2
        card_bottom = start_y + table_h - 2
        card_radius = 15

        for i, item in enumerate(top10):
            row_y = row_start_y + (i * row_h)
            row_center_y = row_y + row_h // 2  # Centro vertical da linha

            # Zebra Striping - TODAS as linhas t├¬m a mesma altura (row_h)
            if i % 2 == 1:
                bg_zebra = (28, 28, 28)
                row_top = row_y
                row_bottom = min(row_y + row_h, card_bottom)

                is_last_row = i == len(top10) - 1
                if is_last_row:
                    draw.rounded_rectangle(
                        [(card_left, row_top), (card_right, row_bottom)],
                        radius=card_radius,
                        fill=bg_zebra,
                    )
                    # Cobrir arredondamento superior indesejado
                    draw.rectangle(
                        [(card_left, row_top), (card_right, row_top + card_radius)],
                        fill=bg_zebra,
                    )
                else:
                    draw.rectangle([(card_left, row_top), (card_right, row_bottom)], fill=bg_zebra)

            # Dados
            nome = item.get("nome_fantasia") or item.get("Competencia[nome_fantasia]") or "Desconhecido"
            import html as html_mod

            nome = html_mod.unescape(nome)
            if len(nome) > 32:
                nome = nome[:29] + "..."

            # Dias
            dias_raw = item.get("Dias_Atraso") or item.get("Competencia[Dias_Atraso]")
            if dias_raw is not None:
                try:
                    dias_val = int(float(dias_raw))
                    dias_str = f"{dias_val} dias"
                except Exception:
                    dias_str = str(dias_raw)
            else:
                dias_str = "-"

            # Valor
            val_raw = item.get("Valor") or item.get("[Valor]")
            val_str = str(val_raw)
            if isinstance(val_raw, (int, float)):
                val_str = f"R$ {val_raw:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            # Rank (left-align, vertical center)
            draw.text(
                (col_rank_x, row_center_y),
                f"{i + 1}",
                font=font_rank,
                fill=self.accent_color,
                anchor="lm",
            )

            # Nome (left-align, vertical center)
            draw.text(
                (col_name_x, row_center_y),
                nome,
                font=font_row,
                fill=(220, 220, 220),
                anchor="lm",
            )

            # Dias (center-align, vertical center)
            draw.text(
                (col_days_x, row_center_y),
                dias_str,
                font=font_row,
                fill=(200, 200, 200),
                anchor="mm",
            )

            # Valor (right-align, vertical center)
            draw.text(
                (col_val_x, row_center_y),
                val_str,
                font=font_val_bold,
                fill=(255, 255, 255),
                anchor="rm",
            )
