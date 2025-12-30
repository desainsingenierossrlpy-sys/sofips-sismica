from fpdf import FPDF
import datetime
import pandas as pd
import io # Para manejar la imagen en memoria

class PDFReport(FPDF):
    def __init__(self, title_doc):
        super().__init__()
        self.title_doc = title_doc
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        try:
            self.image('assets/logo.png', 10, 8, 33) 
        except:
            pass 
            
        self.set_font('helvetica', 'B', 15)
        self.cell(80) 
        self.cell(30, 10, 'MEMORIA DE CÁLCULO', 0, 1, 'C')
        
        self.set_font('helvetica', 'B', 10)
        self.cell(80)
        self.cell(30, 5, 'ANÁLISIS SÍSMICO - NORMA E.030', 0, 1, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()} | Generado por SOFIPS (Desains Ingenieros)', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font('helvetica', 'B', 12)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 10, f"  {label}", 0, 1, 'L', fill=True)
        self.ln(4)

# MODIFICACIÓN: AHORA RECIBE 'img_stream'
def create_pdf(params, info, direccion, df_data, img_stream):
    pdf = PDFReport("Reporte Sísmico")
    pdf.add_page()
    
    # 1. INFORMACIÓN
    pdf.chapter_title("1. INFORMACIÓN DEL PROYECTO")
    fecha = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    
    pdf.set_font("helvetica", "", 10)
    pdf.cell(50, 8, "Fecha de Cálculo:", 0, 0)
    pdf.cell(0, 8, fecha, 0, 1)
    
    pdf.cell(50, 8, "Ubicación:", 0, 0)
    pdf.multi_cell(0, 8, str(direccion)) 
    pdf.ln(5)

    # 2. PARÁMETROS
    pdf.chapter_title("2. PARÁMETROS DE DISEÑO")
    
    def fila_param(nombre, valor):
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(60, 8, nombre, 1, 0)
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 8, str(valor), 1, 1, 'C')

    fila_param("Zona Sísmica (Z)", f"{info['Z']}g")
    fila_param("Perfil de Suelo (S)", f"{info['S']} ({params['suelo']})")
    fila_param("Categoría (U)", f"{info['U']} ({params['categoria']})")
    fila_param("Periodo TP", f"{info['TP']} s")
    fila_param("Periodo TL", f"{info['TL']} s")
    fila_param("Coef. Reducción Rx", str(params['rx']))
    fila_param("Coef. Reducción Ry", str(params['ry']))
    pdf.ln(5)

    # 3. GRÁFICO (NUEVO BLOQUE)
    pdf.chapter_title("3. ESPECTRO DE DISEÑO")
    # Insertamos la imagen desde la memoria
    if img_stream:
        # x=15 (margen izq), w=180 (ancho casi total A4)
        pdf.image(img_stream, x=15, w=180) 
    pdf.ln(5)

    # 4. TABLA DE RESULTADOS
    pdf.chapter_title("4. VALORES TABULADOS (Resumen)")
    
    # Cabecera
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("helvetica", "B", 9)
    col_w = 30
    pdf.cell(col_w, 8, "T (s)", 1, 0, 'C', True)
    pdf.cell(col_w, 8, "Sa Elástico", 1, 0, 'C', True)
    pdf.cell(col_w, 8, "Sa Diseño X", 1, 0, 'C', True)
    pdf.cell(col_w, 8, "Sa Diseño Y", 1, 1, 'C', True)
    
    pdf.set_font("helvetica", "", 9)
    
    # Muestreo
    df_print = df_data.iloc[::10].head(15) # Reduje a 15 para que quepa bien con el gráfico
    
    for i, row in df_print.iterrows():
        t_val = f"{row.iloc[0]:.2f}"
        el_val = f"{row.iloc[1]:.3f}"
        sx_val = f"{row.iloc[2]:.3f}"
        sy_val = f"{row.iloc[3]:.3f}"
        
        pdf.cell(col_w, 6, t_val, 1, 0, 'C')
        pdf.cell(col_w, 6, el_val, 1, 0, 'C')
        pdf.cell(col_w, 6, sx_val, 1, 0, 'C')
        pdf.cell(col_w, 6, sy_val, 1, 1, 'C')

    pdf.ln(5)
    pdf.set_font("helvetica", "I", 8)
    pdf.cell(0, 5, f"* Unidad de aceleración: {params['unidad']}", 0, 1)

    return bytes(pdf.output())