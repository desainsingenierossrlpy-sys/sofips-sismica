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
    # Limpiamos caracteres raros de la dirección
    clean_dir = str(direccion).encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, clean_dir)
    pdf.ln(2)

    # 2. PARÁMETROS DE SITIO
    pdf.chapter_title("2. PARÁMETROS DE SITIO")
    
    # Función para fila de tabla
    def row_table(label, val):
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(80, 7, label, 1, 0)
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 7, str(val), 1, 1, 'C')

    # Convertimos strings para evitar errores de tildes
    suelo_str = params['suelo'].encode('latin-1', 'replace').decode('latin-1')
    
    row_table("Zona Sísmica (Z)", f"{info['Z']}g")
    row_table("Perfil de Suelo (S)", f"{info['S']} ({suelo_str})")
    row_table("Categoría (U)", f"{info['U']}")
    row_table("Periodos (TP / TL)", f"{info['TP']} s / {info['TL']} s")
    pdf.ln(5)

    # 3. SISTEMA ESTRUCTURAL Y R (Tabla Detallada)
    pdf.chapter_title("3. CÁLCULO DE COEFICIENTE DE REDUCCIÓN (R)")
    
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 8, "DIRECCIÓN X-X", 1, 1, 'L', True)
    
    pdf.set_font("helvetica", "", 9)
    sis_x = params['sistema_x'].split(':')[0] # Solo nombre corto
    pdf.cell(50, 7, f"Sistema: {sis_x}", 1, 0)
    pdf.cell(30, 7, f"R0 = {params['r0_x']}", 1, 0, 'C')
    pdf.cell(30, 7, f"Ia = {params['ia_x']}", 1, 0, 'C')
    pdf.cell(30, 7, f"Ip = {params['ip_x']}", 1, 0, 'C')
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(0, 7, f"R = {params['rx']:.2f}", 1, 1, 'C') # R Final

    pdf.ln(2)
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 8, "DIRECCIÓN Y-Y", 1, 1, 'L', True)
    
    pdf.set_font("helvetica", "", 9)
    sis_y = params['sistema_y'].split(':')[0]
    pdf.cell(50, 7, f"Sistema: {sis_y}", 1, 0)
    pdf.cell(30, 7, f"R0 = {params['r0_y']}", 1, 0, 'C')
    pdf.cell(30, 7, f"Ia = {params['ia_y']}", 1, 0, 'C')
    pdf.cell(30, 7, f"Ip = {params['ip_y']}", 1, 0, 'C')
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(0, 7, f"R = {params['ry']:.2f}", 1, 1, 'C')
    
    pdf.ln(10)

    # 4. GRÁFICO
    pdf.chapter_title("4. ESPECTRO DE DISEÑO")
    if img_stream: 
        pdf.image(img_stream, x=15, w=180)
    pdf.ln(5)
    
    pdf.set_font("helvetica", "I", 8)
    pdf.cell(0, 5, f"* Aceleración expresada en: {params['unidad']}", 0, 1)

    return bytes(pdf.output())