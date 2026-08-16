import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generar_pdf_informe(c, logo_path="assets/logo_esterilcontrol.jpg"):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=25, 
        leftMargin=25, 
        topMargin=25, 
        bottomMargin=25
    )
    elementos = []
    styles = getSampleStyleSheet()
    
    estilo_titulo_hdr = ParagraphStyle('HdrTitle', parent=styles['Heading1'], fontSize=10, leading=12, alignment=1, fontName='Helvetica-Bold')
    estilo_meta_hdr = ParagraphStyle('HdrMeta', parent=styles['Normal'], fontSize=8, leading=10, fontName='Helvetica-Bold')
    estilo_cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontSize=8, leading=10, fontName='Helvetica-Bold')
    estilo_cell_norm = ParagraphStyle('CellNorm', parent=styles['Normal'], fontSize=8, leading=10, fontName='Helvetica')

    cod_ciclo_fmt = f"{int(c['n_ciclo']):05d}"

    # 1. Encabezado Oficial CIR-FT-01
    img_logo = None
    if os.path.exists(logo_path):
        img_logo = Image(logo_path, width=110, height=35)
    else:
        img_logo = Paragraph("<b>AM Medical</b>", estilo_cell_bold)

    p_titulo = Paragraph("FORMATO PARA EL CONTROL DEL PROCESO DE ESTERILIZACION", estilo_titulo_hdr)
    p_meta = Paragraph("<b>CODIGO:</b> CIR-FT-01<br/><b>VERSION:</b> 01<br/><b>VIGENCIA:</b> 24/06/2028<br/><b>PAGINA:</b> 01", estilo_meta_hdr)

    data_hdr = [[img_logo, p_titulo, p_meta]]
    t_hdr = Table(data_hdr, colWidths=[130, 290, 140])
    t_hdr.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elementos.append(t_hdr)
    elementos.append(Spacer(1, 4))

    # 2. Parámetros Generales
    is_eo = "EO" if "EO" in c['equipo'].upper() or "OXIDO" in str(c.get('metodo','')).upper() else "X"
    is_vap = "" if is_eo == "EO" else "X"

    data_params = [
        [
            Paragraph(f"<b>METODO DE ESTERILIZACIÓN :</b> VAPOR: [ {is_vap} ]  OXIDO DE ETILENO: [ {is_eo} ]", estilo_cell_norm),
            Paragraph(f"<b>N° ESTERILIZADOR:</b> {c['equipo']}", estilo_cell_norm)
        ],
        [
            Paragraph(f"<b>N° CICLO:</b> {cod_ciclo_fmt}", estilo_cell_bold),
            Paragraph(f"<b>FECHA:</b> {c['fecha']}", estilo_cell_norm)
        ],
        [
            Paragraph(f"<b>HORA DE INICIO:</b> {c['hora_inicio']}", estilo_cell_norm),
            Paragraph(f"<b>HORA DE FINALIZACIÓN:</b> {c['hora_fin'] if c['hora_fin'] else 'En Proceso'}", estilo_cell_norm)
        ],
        [
            Paragraph(f"<b>TEMPERATURA:</b> {c['temp']} °C", estilo_cell_norm),
            Paragraph(f"<b>PRESIÓN DE CÁMARA:</b> {c.get('presion_camara', '-49kPa')}", estilo_cell_norm)
        ],
        [
            Paragraph(f"<b>TIEMPO EXPOSICIÓN:</b> {c['t_exp']} Min / 2H", estilo_cell_norm),
            Paragraph(f"<b>TIPO DE CARGA:</b> {c['observaciones'] if c['observaciones'] else 'Textil / Médico'}", estilo_cell_norm)
        ],
        [
            Paragraph(f"<b>NOMBRE RESPONSABLE DE ESTERILIZACIÓN:</b> {c['operador']}", estilo_cell_norm),
            Paragraph(f"<b>RESULTADO PROCESO:</b> {c['resultado']}", estilo_cell_norm)
        ]
    ]

    t_params = Table(data_params, colWidths=[280, 280])
    t_params.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.8, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
    ]))
    elementos.append(t_params)
    elementos.append(Spacer(1, 4))

    # 3. Descripción de Carga
    data_carga_pdf = [
        [Paragraph("<b>DESCRIPCIÓN DE CARGA</b>", estilo_cell_bold), Paragraph("<b>CANT.</b>", estilo_cell_bold), Paragraph("<b>LOTE</b>", estilo_cell_bold)]
    ]

    items_carga = [
        ("PAQUETE LAPARATOMIA", c.get('q_lap', 0), c.get('l_lap', '0')),
        ("U. HEMODINAMIA", c.get('q_hemo', 0), c.get('l_hemo', '0')),
        ("CIRUGÍA VALLEDUPAR", c.get('q_cir', 0), c.get('l_cir', '0')),
        ("SÁBANAS ESTÉRILES", c.get('q_sab', 0), c.get('l_sab', '0')),
        ("PAQUETE CENTRAL ADULTO", c.get('q_adult', 0), c.get('l_adult', '0')),
        ("NEUROINTERVENCIONISMO", c.get('q_neuro', 0), c.get('l_neuro', '0')),
        ("APÓSITOS ESTÉRILES", c.get('q_apos', 0), c.get('l_apos', '0')),
    ]

    alguno_agregado = False
    for nombre_i, cant_i, lote_i in items_carga:
        if cant_i > 0:
            data_carga_pdf.append([
                Paragraph(nombre_i, estilo_cell_norm),
                Paragraph(f"{cant_i} U", estilo_cell_norm),
                Paragraph(str(lote_i), estilo_cell_norm)
            ])
            alguno_agregado = True

    if not alguno_agregado:
        data_carga_pdf.append([
            Paragraph("CARGA GENERAL / MATERIAL VARIO", estilo_cell_norm),
            Paragraph(f"{c['tot_unidades']} U", estilo_cell_norm),
            Paragraph("LT080327", estilo_cell_norm)
        ])

    data_carga_pdf.append([
        Paragraph(f"<b>TOTALES: {c['tot_peso']} kg ({c['ocupacion']}% Ocupación)</b>", estilo_cell_bold),
        Paragraph(f"<b>{c['tot_unidades']} U</b>", estilo_cell_bold),
        Paragraph(f"<b>Canastas: {c['canastas_grandes']}G / {c['canastas_pequenas']}P</b>", estilo_cell_bold)
    ])

    t_carga = Table(data_carga_pdf, colWidths=[300, 100, 160])
    t_carga.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f0f0f0")),
        ('GRID', (0,0), (-1,-1), 0.8, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
    ]))
    elementos.append(t_carga)
    elementos.append(Spacer(1, 4))

    # 4. Controles Biológicos y Químicos
    res_pos = "X" if str(c.get('res_ib','')).upper() == "POSITIVO" else " "
    res_neg = "X" if str(c.get('res_ib','')).upper() == "NEGATIVO" or c.get('res_ib','') == "Conforme" else "X"

    data_bio = [
        [
            Paragraph("<b>STIKER INDICADOR BIOLOGICO</b><br/><br/><br/><br/><i>(Pegar sticker de lectura aquí)</i>", estilo_cell_norm),
            Paragraph(f"""
                <b>CONTROL DE CARGA</b><br/><br/>
                <b>RESULTADO DE LECTURA:</b><br/>
                POSITIVO: [ {res_pos} ]   NEGATIVO: [ {res_neg} ]<br/><br/>
                <b>NOMBRE RESPONSABLE DE LECTURA INDICADOR:</b><br/>
                {c['operador']}
            """, estilo_cell_norm)
        ]
    ]

    t_bio = Table(data_bio, colWidths=[280, 280])
    t_bio.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.8, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
    ]))
    elementos.append(t_bio)
    elementos.append(Spacer(1, 4))

    data_tirillas = [
        [
            Paragraph("<b>TIRILLA INDICADORA INTERNA / CONTROL DE EXPOSICIÓN / INDICADOR QUÍMICO EXTERNO</b><br/><br/><br/><br/><br/><i>(Espacio reservado para fijación de tirilla física de control)</i>", estilo_cell_norm)
        ]
    ]
    t_tirillas = Table(data_tirillas, colWidths=[560])
    t_tirillas.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.8, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
    ]))
    elementos.append(t_tirillas)

    doc.build(elementos)
    buffer.seek(0)
    return buffer