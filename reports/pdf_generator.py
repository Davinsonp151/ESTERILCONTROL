import os
from docx import Document
from io import BytesIO

def generar_pdf_informe(datos):
    """
    Genera un documento Word basado en plantilla utilizando python-docx,
    reemplazando etiquetas dinámicas, aplicando fuente Calibri y quitando negritas a los datos.
    """
    plantilla_path = "reports/plantilla_base.docx"
    
    if not os.path.exists(plantilla_path):
        plantilla_path = "plantilla_base.docx"
        
    doc = Document(plantilla_path)

    # 1. Diccionario completo con todas las etiquetas de la plantilla oficial CIR-FT-01
    reemplazos = {
        "{{fecha}}": str(datos.get("fecha_inicio", "")),
        "{{hora_inicio}}": str(datos.get("hora_inicio", "")),
        "{{hora_fin}}": str(datos.get("hora_fin", "En Proceso")),
        "{{metodo}}": str(datos.get("metodo", "Óxido de Etileno")),
        "{{control_carga}}": str(datos.get("control_carga", "Conforme")),
        "{{esterilizador}}": str(datos.get("esterilizador", "")),
        "{{n_cic}}": str(datos.get("n_cic", "")),
        "{{tipo_carga}}": str(datos.get("tipo_carga", "Textil")),
        "{{presion}}": str(datos.get("presion", "")),
        "{{tiempo_exposicion}}": str(datos.get("tiempo_exposicion", "")),
        "{{temperatura}}": str(datos.get("temperatura", "")),
        "{{operador}}": str(datos.get("operador", "")),
        "{{estado}}": str(datos.get("estado", ""))
    }

    # Función auxiliar para unificar fragmentos XML, reemplazar etiquetas, asignar Calibri y quitar negrita
    def procesar_parrafo(p):
        texto_completo = "".join([run.text for run in p.runs])
        modificado = False
        for clave, valor in reemplazos.items():
            if clave in texto_completo:
                texto_completo = texto_completo.replace(clave, str(valor))
                modificado = True
        
        if modificado and p.runs:
            p.runs[0].text = texto_completo
            p.runs[0].font.name = 'Calibri'
            p.runs[0].font.bold = False  # Forzar a que NO sea negrita
            for run in p.runs[1:]:
                run.text = ""
        else:
            # Asegurar que el resto del texto también mantenga la fuente Calibri si se desea
            for run in p.runs:
                run.font.name = 'Calibri'

    # Recorremos los párrafos del documento principal[cite: 5]
    for p in doc.paragraphs:
        procesar_parrafo(p)

    # Recorremos las tablas para asegurar el reemplazo y estilo en celdas[cite: 5]
    for tabla in doc.tables:
        for fila in tabla.rows:
            for celda in fila.cells:
                for p in celda.paragraphs:
                    procesar_parrafo(p)

    # 2. Inyección de ítems en la tabla correspondiente[cite: 5]
    items = datos.get("items", [])
    
    if items and len(doc.tables) > 0:
        tabla_items = None
        for tabla in doc.tables:
            if len(tabla.rows) > 1:
                tabla_items = tabla
                break
        
        if tabla_items and len(tabla_items.rows) >= 2:
            for idx, item in enumerate(items):
                if idx + 1 < len(tabla_items.rows):
                    row = tabla_items.rows[idx + 1]
                else:
                    row = tabla_items.add_row()
                
                try:
                    row.cells[0].text = str(item.get("nombre", ""))
                    row.cells[1].text = str(item.get("cantidad", 0))
                    row.cells[2].text = str(item.get("lote", ""))
                    
                    # Asegurar fuente Calibri y texto normal en la tabla de ítems
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            for run in p.runs:
                                run.font.name = 'Calibri'
                                run.font.bold = False
                except Exception:
                    pass

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer