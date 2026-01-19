from fpdf import FPDF
import datetime

def create_pdf(params, info, direccion, df_data, img_stream, font_family, font_size):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    f_fam = font_family
    f_size = font_size
    
    # Encabezado
    pdf.set_font(f_fam, "B", f_size + 6)
    pdf.cell(0, 10, "MEMORIA DE CALCULO - NORMA E.030", ln=True, align="C")
    
    # Parámetros (Resumen)
    pdf.ln(5)
    pdf.set_font(f_fam, "B", f_size + 2)
    pdf.cell(0, 10, "1. PARAMETROS SISMICOS Y UBICACION", ln=True)
    pdf.set_font(f_fam, "", f_size)
    pdf.cell(0, 7, f"Lugar: {info['distrito']} ({direccion})", ln=True)
    pdf.cell(0, 7, f"Z={params['Z']} | U={params['U']} | S={params['S']} | Tp={info['Tp']}s | Tl={info['Tl']}s", ln=True)
    pdf.cell(0, 7, f"Coeficientes R: Dir X={params['rx']} | Dir Y={params['ry']}", ln=True)
    
    # Gráfico
    pdf.ln(5)
    pdf.image(img_stream, x=10, w=190)
    
    # Tabla de Resultados con paso de 0.02s
    pdf.ln(10)
    pdf.set_font(f_fam, "B", f_size)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(40, 8, "Periodo T(s)", 1, 0, "C", True)
    pdf.cell(50, 8, "Sa Elastic (g)", 1, 0, "C", True)
    pdf.cell(50, 8, "Sa Dir X (g)", 1, 0, "C", True)
    pdf.cell(50, 8, "Sa Dir Y (g)", 1, 1, "C", True)
    
    pdf.set_font(f_fam, "", f_size - 1)
    
    # IMPORTANTE: Aquí controlamos el paso visual en el PDF. 
    # Usamos un paso de 1 (cada fila del dataframe) para mostrar el 0.02s exacto.
    # Nota: Esto hará que el PDF tenga muchas páginas.
    for i in range(len(df_data)):
        row = df_data.iloc[i]
        pdf.cell(40, 7, f"{row['T(s)']:.2f}", 1, 0, "C")
        pdf.cell(50, 7, f"{row['Sa_Elastic']:.4f}", 1, 0, "C")
        pdf.cell(50, 7, f"{row['Sa_X']:.4f}", 1, 0, "C")
        pdf.cell(50, 7, f"{row['Sa_Y']:.4f}", 1, 1, "C")

    # Retorno en formato bytes para Streamlit
    return bytes(pdf.output())