from fpdf import FPDF
import datetime
import pandas as pd

class PDFReport(FPDF):
    def __init__(self, title_doc):
        super().__init__()
        self.title_doc = title_doc
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        try:
            self.image('assets/logo.png', 10, 8, 33) 
        except: pass 
        self.set_font('helvetica', 'B', 15)
        self.cell(80); self.cell(30, 10, 'MEMORIA DE CÁLCULO', 0, 1, 'C')
        self.set_font('helvetica', 'B', 10)
        self.cell(80); self.cell(30, 5, 'ANÁLISIS SÍSMICO - NORMA E.030', 0, 1, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()} | SOFIPS (Desains Ingenieros)', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font('helvetica', 'B', 12)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 10, f"  {label}", 0, 1, 'L', fill=True)
        self.ln(4)

def create_pdf(params, info, direccion, df_data, img_stream):
    pdf = PDFReport("Reporte")
    pdf.add_page()
    
    # 1. INFORMACIÓN
    pdf.chapter_title("1. GENERALIDADES")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(40, 8, "Ubicación:", 0, 0)
    pdf.multi_cell(0, 8, str(direccion))
    pdf.ln(2)

    # 2. PARÁMETROS DE SITIO
    pdf.chapter_title("2. PARÁMETROS DE SITIO")
    def fila(n, v):
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(50, 7, n, 1, 0)
        pdf.set_font("helvetica", "", 9)
        pdf.cell(0, 7, str(v), 1, 1)

    fila("Zona Sísmica (Z)", f"{info['Z']}g")
    fila("Perfil de Suelo (S)", f"{info['S']} ({params['suelo']})")
    fila("Categoría (U)", f"{info['U']} ({params['categoria']})")
    fila("Periodos (TP / TL)", f"{info['TP']} s / {info['TL']} s")
    pdf.ln(5)

    # 3. SISTEMA ESTRUCTURAL (NUEVO)
    pdf.chapter_title("3. SISTEMA ESTRUCTURAL Y REGULARIDAD")
    
    pdf.set_font("helvetica", "B", 10); pdf.cell(0, 8, "Dirección X-X:", 0, 1)
    pdf.set_font("helvetica", "", 9)
    pdf.multi_cell(0, 6, f"Sistema: {params['sistema_x']}")
    pdf.cell(0, 6, f"R Calculado = {params['rx_final']:.2f}", 0, 1)
    pdf.ln(2)
    
    pdf.set_font("helvetica", "B", 10); pdf.cell(0, 8, "Dirección Y-Y:", 0, 1)
    pdf.set_font("helvetica", "", 9)
    pdf.multi_cell(0, 6, f"Sistema: {params['sistema_y']}")
    pdf.cell(0, 6, f"R Calculado = {params['ry_final']:.2f}", 0, 1)
    pdf.ln(5)

    # 4. GRÁFICO
    pdf.chapter_title("4. ESPECTRO DE DISEÑO")
    if img_stream: pdf.image(img_stream, x=15, w=180)
    pdf.ln(5)

    return bytes(pdf.output())