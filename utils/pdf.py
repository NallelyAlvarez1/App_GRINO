import tempfile
import os
from turtle import st
import streamlit
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from fpdf import FPDF
from utils.db import get_presupuesto_detallado
import locale

try:
    locale.setlocale(locale.LC_TIME, 'es_ES.utf8') 
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'es')
        except locale.Error:
            print("No se pudo configurar el locale a español. Las fechas pueden aparecer en inglés.")

# ========== FORMATO TEXTO ==========
def formato_moneda(valor: float) -> str:
    """Formatea valores monetarios con separadores de miles"""
    # Usa coma como separador de decimales y punto para miles
    return f"${valor:,.0f}".replace(",", ".")

# ==========  SECCION PDF ==========
# Datos constantes
EMPRESA = "Jardines Alvarez"
CONTACTO_NOMBRE = "Jhonny Nicolas Alvarez"
CONTACTO_TELEFONO = "+569 6904 2513"
CONTACTO_EMAIL = "jhonnynicolasalvarez@gmail.com"

def generar_pdf(cliente_nombre: str, categorias: Dict[str, Any], lugar_cliente: str, descripcion: Optional[str] = None) -> str:
    """
    Genera un archivo PDF con los datos del presupuesto
    """
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=11)
        
        # Configurar márgenes
        pdf.set_margins(left=10, top=10, right=10)
        pdf.set_auto_page_break(auto=True, margin=15)

        # Encabezado
        COLOR_FONDO = (157, 178, 111)
        pdf.set_fill_color(*COLOR_FONDO)

        ALTO_FRANJA = 26
        MARGEN_X = 10

        # 1. Crear la franja de fondo verde
        y_inicio_fondo = pdf.get_y()
        pdf.set_xy(0, y_inicio_fondo)
        pdf.set_fill_color(175, 192, 138)
        pdf.cell(pdf.w, ALTO_FRANJA, "", border=0, ln=1, fill=True)

        # 2. Texto sobre la franja
        pdf.set_text_color(36, 36, 36)

        # a)"Presupuesto"
        pdf.set_y(y_inicio_fondo + 5)
        pdf.set_x(MARGEN_X)
        pdf.set_font("helvetica", style='B', size=24)
        pdf.cell(100, 10, "Presupuesto", border=0, ln=0, align='L', fill=False)

        # b)Nombre de la Empresa
        pdf.set_x(MARGEN_X)
        pdf.set_font("helvetica", style='', size=18)
        pdf.cell(102, 26, EMPRESA.title(), border=0, ln=0, align='L', fill=False)

        # c)Línea negra debajo del nombre de la empresa
        y_linea = pdf.get_y() + 17
        pdf.set_draw_color(56, 56, 56)
        pdf.set_line_width(0.8)
        pdf.line(MARGEN_X, y_linea, MARGEN_X + 85, y_linea)

        # d)Línea verde debajo franja verde
        y_linea = pdf.get_y() + 23 
        pdf.set_draw_color(175, 192, 138)
        pdf.set_line_width(0.8)
        pdf.line(0, y_linea, pdf.w, y_linea)

        # e)Lugar del cliente
        pdf.set_font("helvetica", style='B', size=22)
        pdf.set_y(y_inicio_fondo + (ALTO_FRANJA / 2) - 6)

        ANCHO_UTIL_PAGINA = 190 
        MARGEN_DERECHO = 10 
        ANCHO_MULTICELL = 90
        POSICION_X_INICIO = ANCHO_UTIL_PAGINA - ANCHO_MULTICELL + MARGEN_DERECHO

        pdf.set_x(POSICION_X_INICIO) 
        pdf.multi_cell(
            w=ANCHO_MULTICELL, 
            h=7,
            txt=lugar_cliente.title(), 
            border=0, 
            align='C', 
            fill=False
        )

        pdf.ln(15) 

        # Fecha y datos de contacto
        fecha_actual = datetime.now().strftime("%d %B, %Y")
        pdf.ln(2)
        pdf.set_font("helvetica", size=12)

        # --- Columna izquierda: datos de contacto ---
        x_inicio = pdf.get_x()
        y_inicio = pdf.get_y()

        pdf.cell(95, 5, CONTACTO_NOMBRE, border=0, ln=True)
        pdf.cell(95, 5, CONTACTO_TELEFONO, border=0, ln=True)
        pdf.cell(95, 5, CONTACTO_EMAIL, border=0, ln=True)

        y_fin_contacto = pdf.get_y()

        # Línea vertical
        pdf.set_draw_color(56, 56, 56)
        pdf.set_line_width(0.6)
        x_linea = x_inicio + 80
        pdf.line(x_linea, y_inicio, x_linea, y_fin_contacto)

        # --- Columna derecha: Cliente y fecha ---
        pdf.set_xy(x_linea + 5, y_inicio)

        pdf.set_font("helvetica", style='B', size=10)
        pdf.cell(40, 5, "Cliente:", border=0)

        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 5, fecha_actual, border=0, ln=True, align='R')

        pdf.set_x(x_linea + 5)
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 6, cliente_nombre.title(), border=0, ln=True)

        # Franja 2
        y_inicio_fondo = pdf.get_y()
        MARGEN_X_FRANJA = 10
        ALTO = 7

        pdf.set_xy(MARGEN_X_FRANJA, y_inicio_fondo + 10)
        pdf.set_fill_color(175, 192, 138)
        pdf.cell(pdf.w - 2 * MARGEN_X_FRANJA, ALTO, "", border=0, ln=1, fill=True)

        pdf.set_text_color(36, 36, 36)
        pdf.set_font("helvetica", style='B', size=12)

        pdf.set_y(y_inicio_fondo + (ALTO / 2) + 7) 
        pdf.set_x(MARGEN_X_FRANJA + 5)
        
        texto_franja = descripcion.strip().capitalize() if descripcion else "Trabajo a Realizar"
        pdf.cell(0, 6, texto_franja, border=0, ln=1, align='C')

        pdf.ln(3)

        # Presupuesto por categoría
        total_general = 0

        for categoria, data in categorias.items():
            items = data.get('items', [])
            mano_obra = data.get('mano_obra', 0)

            # 👍 Insertar mano de obra como un ítem
            if mano_obra > 0:
                items.append({
                    'nombre_personalizado': 'Mano de Obra',
                    'unidad': 'Unidad',
                    'cantidad': 1,
                    'precio_unitario': mano_obra,
                    'total': mano_obra,
                    'es_mano_obra': True
                })

            if not items:
                continue

            # Nueva página si es necesario
            if pdf.get_y() > 270:
                pdf.add_page()
                pdf.set_y(10)

            # Título categoría
            pdf.set_font("helvetica", style='B', size=12)
            pdf.cell(200, 6, categoria.title(), ln=True)

            # Línea debajo del título con ancho 0.5
            pdf.set_line_width(0.8)
            pdf.set_draw_color(194, 207, 165)
            margen_izquierdo = 10
            ancho_total = 190
            y_linea = pdf.get_y() + 0.2
            pdf.line(margen_izquierdo, y_linea, margen_izquierdo + ancho_total, y_linea)
            pdf.ln(2)

            # Encabezados de tabla con ancho 0.3
            pdf.set_font("helvetica", style='B', size=11)
            pdf.set_draw_color(56, 56, 56)
            pdf.set_line_width(0.3)  # Establecemos 0.3 para la tabla
            pdf.cell(75, 6, "Insumo", border='B')
            pdf.cell(25, 6, "Unidad", border='B', align='C')
            pdf.cell(20, 6, "Cantidad", border='B', align='C')
            pdf.cell(35, 6, "Precio Unitario", border='B', align='C')
            pdf.cell(35, 6, "Total", border='B', ln=True, align='C')

            total_categoria = 0

            for item in items:

                if pdf.get_y() > 270:
                    pdf.add_page()
                    pdf.set_font("helvetica", style='B', size=11)
                    pdf.cell(75, 6, "Insumo", border='B')
                    pdf.cell(25, 6, "Unidad", border='B', align='C')
                    pdf.cell(20, 6, "Cantidad", border='B', align='C')
                    pdf.cell(35, 6, "Precio Unitario", border='B', align='C')
                    pdf.cell(35, 6, "Total", border='B', ln=True, align='C')

                pdf.set_font("helvetica", size=11)

                # 🟢 Caso 1: Trabajo simple
                if item.get("es_trabajo_simple"):
                    pdf.cell(155, 6, item.get("nombre_personalizado", "").title(), border=1)
                    pdf.cell(35, 6, formato_moneda(item.get("total", 0)), border=1, ln=True, align="R")
                    total_categoria += item.get("total", 0)
                    continue

                # 🟡 Caso 2: Mano de obra especial
                if item.get("es_mano_obra"):
                    pdf.cell(155, 6, item.get("nombre_personalizado", "").title(), border=1)
                    pdf.cell(35, 6, formato_moneda(item.get("total", 0)), border=1, ln=True, align="R")
                    total_categoria += item.get("total", 0)
                    continue

                # 🟠 Caso 3: Insumos regulares (ESTE ERA EL PROBLEMA)
                # --- NUEVA LÓGICA PARA INSUMOS REGULARES ---
                texto_insumo = item.get('nombre_personalizado', '').title()
                if not texto_insumo:
                    texto_insumo = item.get('nombre', '').title()  # Fallback por si no hay nombre_personalizado

                # Posición inicial
                x_inicial = pdf.get_x()
                y_inicial = pdf.get_y()

                ANCHO_INSUMO = 75
                ALTO_LINEA = 6

                # Calcular cuántas líneas necesitamos
                lineas = pdf.multi_cell(ANCHO_INSUMO, ALTO_LINEA, texto_insumo, split_only=True)
                num_lineas = len(lineas)
                alto_necesario = max(ALTO_LINEA, num_lineas * ALTO_LINEA)

                # Dibujar celda de insumo con el alto calculado
                pdf.set_xy(x_inicial, y_inicial)
                pdf.multi_cell(
                    ANCHO_INSUMO,
                    ALTO_LINEA,
                    texto_insumo,
                    border=1,
                    align='L'
                )

                # Obtener la posición Y después del multi_cell
                y_despues = pdf.get_y()
                alto_real = y_despues - y_inicial

                # Mover a la posición correcta para las otras celdas
                pdf.set_xy(x_inicial + ANCHO_INSUMO, y_inicial)
                
                # Dibujar las otras celdas con el alto calculado
                pdf.cell(25, alto_real, item.get('unidad', '').title(), border=1, align='C')
                pdf.cell(20, alto_real, str(int(item.get('cantidad', 0))), border=1, align='C')
                pdf.cell(35, alto_real, formato_moneda(item.get('precio_unitario', 0)), border=1, align='R')
                pdf.cell(35, alto_real, formato_moneda(item.get('total', 0)), border=1, ln=True, align='R')

                total_categoria += item.get("total", 0)

            pdf.set_font("helvetica", style='B', size=11)
            pdf.cell(155, 6, "Total", border=1, align='R')
            pdf.cell(35, 6, formato_moneda(total_categoria), border=1, ln=True, align='R')
            pdf.ln(5)
            total_general += total_categoria

        # Total general
        if pdf.get_y() > 270:
            pdf.add_page()

        pdf.set_fill_color(194, 207, 165)
        ANCHO_TOTAL = 40
        ALTO_TOTAL = 15
        margen_derecho = 10
        x_inicial = pdf.w - ANCHO_TOTAL - margen_derecho
        y_inicial = pdf.get_y()

        pdf.rect(x_inicial, y_inicial, ANCHO_TOTAL, ALTO_TOTAL, style='F')

        pdf.set_xy(x_inicial + 4, y_inicial + 2)
        pdf.set_font("helvetica", style='B', size=11)
        pdf.cell(0, 5, "Total", border=0)

        pdf.set_font("helvetica", style='B', size=14)
        pdf.set_xy(x_inicial, y_inicial + 6)
        pdf.cell(ANCHO_TOTAL, 8, formato_moneda(total_general), border=0, align='C')

        # Guardar archivo
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        temp_path = temp_file.name
        temp_file.close()
        pdf.output(temp_path)
        
        return temp_path
        
    except Exception as e:
        raise Exception(f"Error al generar PDF: {str(e)}")
    
def mostrar_boton_descarga_pdf(presupuesto_id: int, label: str = "📄 Descargar PDF") -> bool:
    """
    Genera un PDF y muestra automáticamente el botón de descarga.
    Retorna True si todo salió bien.
    """
    try:
        presupuesto = get_presupuesto_detallado(presupuesto_id)

        if not presupuesto:
            st.error("No se encontró el presupuesto")
            return False

        categorias = {}

        for item in presupuesto.get('items', []):
            cat_nombre = item.get('categoria') or 'Sin categoría'

            if cat_nombre not in categorias:
                categorias[cat_nombre] = {
                    'items': [],
                    'mano_obra': 0
                }

            if item.get('nombre') == 'Mano de Obra':
                categorias[cat_nombre]['mano_obra'] = item.get('precio_unitario', 0)

            else:
                categorias[cat_nombre]['items'].append({
                    'nombre': item.get('nombre', 'Sin nombre'),
                    'unidad': item.get('unidad', 'Unidad'),
                    'cantidad': item.get('cantidad', 1),
                    'precio_unitario': item.get('precio_unitario', 0),
                    'total': item.get('total', 0),
                    'descripcion': item.get('notas', '')
                })

        pdf_path = generar_pdf(
            presupuesto['cliente']['nombre'],
            categorias,
            presupuesto['lugar']['nombre'],
            descripcion=presupuesto.get('descripcion', ''),
        )

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        try:
            os.unlink(pdf_path)
        except Exception as e:
            print(f"Error al eliminar archivo temporal: {str(e)}")

        lugar_nombre = presupuesto['lugar']['nombre'].strip().replace(" ", "_")
        file_name = f"Presupuesto_{lugar_nombre}.pdf"

        st.download_button(
            label=label,
            data=pdf_bytes,
            file_name=file_name,
            mime="application/pdf",
            use_container_width=True
        )

        return True

    except Exception as e:
        st.error(f"Error al generar PDF: {str(e)}")
        return False
    
def generar_pdf_estado_cuenta(id_documento: int, cliente_nombre: str, lugar_nombre: str, items: list, abono: float, total: float) -> Tuple[bytes, str]:
    """
    Generar un archivo PDF con el diseño corporativo de Jardines Alvarez
    adaptado para múltiples meses y cobros en el Estado de Cuenta.
    """
    import tempfile
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=11)
        
        # Configurar márgenes idénticos
        pdf.set_margins(left=10, top=10, right=10)
        pdf.set_auto_page_break(auto=True, margin=15)

        # Encabezado - Franja de fondo verde corporativo
        y_inicio_fondo = pdf.get_y()
        pdf.set_xy(0, y_inicio_fondo)
        pdf.set_fill_color(175, 192, 138)
        ALTO_FRANJA = 26
        MARGEN_X = 10
        pdf.cell(pdf.w, ALTO_FRANJA, "", border=0, ln=1, fill=True)

        # Texto sobre la franja
        pdf.set_text_color(36, 36, 36)

        # a) "Estado de Cuenta" en lugar de Presupuesto
        pdf.set_y(y_inicio_fondo + 5)
        pdf.set_x(MARGEN_X)
        pdf.set_font("helvetica", style='B', size=22)
        pdf.cell(100, 10, "Estado de Cuenta N°", border=0, ln=0, align='L', fill=False)

        # b) Nombre de la Empresa
        pdf.set_x(MARGEN_X)
        pdf.set_font("helvetica", style='', size=16)
        pdf.cell(102, 26, EMPRESA.title(), border=0, ln=0, align='L', fill=False)

        # c) Línea negra debajo del nombre de la empresa
        y_linea = pdf.get_y() + 17
        pdf.set_draw_color(56, 56, 56)
        pdf.set_line_width(0.8)
        pdf.line(MARGEN_X, y_linea, MARGEN_X + 85, y_linea)

        # d) Línea verde debajo de la franja
        y_linea = pdf.get_y() + 23 
        pdf.set_draw_color(175, 192, 138)
        pdf.set_line_width(0.8)
        pdf.line(0, y_linea, pdf.w, y_linea)

        # e) Lugar del cliente en el extremo derecho
        pdf.set_font("helvetica", style='B', size=20)
        pdf.set_y(y_inicio_fondo + (ALTO_FRANJA / 2) - 6)

        ANCHO_UTIL_PAGINA = 190 
        MARGEN_DERECHO = 10 
        ANCHO_MULTICELL = 90
        POSICION_X_INICIO = ANCHO_UTIL_PAGINA - ANCHO_MULTICELL + MARGEN_DERECHO

        pdf.set_x(POSICION_X_INICIO) 
        pdf.multi_cell(
            w=ANCHO_MULTICELL, 
            h=7,
            txt=lugar_nombre.title(), 
            border=0, 
            align='C', 
            fill=False
        )

        pdf.ln(15) 

        # Fecha y datos de contacto
        fecha_actual = datetime.now().strftime("%d %B, %Y")
        pdf.ln(2)
        pdf.set_font("helvetica", size=12)

        # --- Columna izquierda: datos de contacto ---
        x_inicio = pdf.get_x()
        y_inicio = pdf.get_y()

        pdf.cell(95, 5, CONTACTO_NOMBRE, border=0, ln=True)
        pdf.cell(95, 5, CONTACTO_TELEFONO, border=0, ln=True)
        pdf.cell(95, 5, CONTACTO_EMAIL, border=0, ln=True)

        y_fin_contacto = pdf.get_y()

        # Línea vertical divisoria
        pdf.set_draw_color(56, 56, 56)
        pdf.set_line_width(0.6)
        x_linea = x_inicio + 80
        pdf.line(x_linea, y_inicio, x_linea, y_fin_contacto)

        # --- Columna derecha: Cliente y fecha ---
        pdf.set_xy(x_linea + 5, y_inicio)

        pdf.set_font("helvetica", style='B', size=10)
        pdf.cell(40, 5, "Cliente:", border=0)

        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 5, fecha_actual, border=0, ln=True, align='R')

        pdf.set_x(x_linea + 5)
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 6, cliente_nombre.title(), border=0, ln=True)

        # Franja 2 Informativa central
        y_inicio_fondo = pdf.get_y()
        MARGEN_X_FRANJA = 10
        ALTO = 7

        pdf.set_xy(MARGEN_X_FRANJA, y_inicio_fondo + 10)
        pdf.set_fill_color(175, 192, 138)
        pdf.cell(pdf.w - 2 * MARGEN_X_FRANJA, ALTO, "", border=0, ln=1, fill=True)

        pdf.set_text_color(36, 36, 36)
        pdf.set_font("helvetica", style='B', size=12)

        pdf.set_y(y_inicio_fondo + (ALTO / 2) + 7) 
        pdf.set_x(MARGEN_X_FRANJA + 5)
        pdf.cell(0, 6, "Resumen de Servicios y Cobros Pendientes", border=0, ln=1, align='C')

        pdf.ln(5)

        # --- TABLA DE DETALLES (Mismos anchos e indices que el presupuesto) ---
        pdf.set_font("helvetica", style='B', size=11)
        pdf.set_draw_color(56, 56, 56)
        pdf.set_line_width(0.3)
        
        pdf.cell(140, 6, "Descripción del Servicio / Período", border='B')
        pdf.cell(50, 6, "Total", border='B', ln=True, align='R')

        # Listar todos los conceptos agregados (Meses y Servicios extras)
        pdf.set_font("helvetica", size=11)
        total_cargos = 0
        
        for item in items:
            if pdf.get_y() > 260:
                pdf.add_page()
                pdf.set_font("helvetica", style='B', size=11)
                pdf.cell(140, 6, "Descripción del Servicio / Período", border='B')
                pdf.cell(50, 6, "Total", border='B', ln=True, align='R')

            pdf.set_font("helvetica", size=11)
            texto_detalle = item.get('descripcion', '').strip()
            
            # Lógica multilínea para que se adapte si colocas una descripción larga
            x_inicial = pdf.get_x()
            y_inicial = pdf.get_y()
            ANCHO_DESC = 140
            ALTO_LINEA = 6
            
            lineas = pdf.multi_cell(ANCHO_DESC, ALTO_LINEA, texto_detalle, split_only=True)
            alto_real = max(ALTO_LINEA, len(lineas) * ALTO_LINEA)
            
            pdf.set_xy(x_inicial, y_inicial)
            pdf.multi_cell(ANCHO_DESC, ALTO_LINEA, texto_detalle, border=1, align='L')
            
            pdf.set_xy(x_inicial + ANCHO_DESC, y_inicial)
            pdf.cell(50, alto_real, formato_moneda(item.get('monto', 0)), border=1, ln=True, align='R')
            
            total_cargos += item.get('monto', 0)

        # Fila adicional para reflejar Abonos si es que existen
        if abono > 0:
            if pdf.get_y() > 260:
                pdf.add_page()
            pdf.set_font("helvetica", style='I', size=11)
            pdf.set_text_color(150, 0, 0) # Texto rojo sutil para descuento
            pdf.cell(140, 6, " Abonos / Pagos Recibidos (Descuento)", border=1, align='L')
            pdf.cell(50, 6, f"-{formato_moneda(abono)} ", border=1, ln=True, align='R')
            pdf.set_text_color(36, 36, 36)

        pdf.ln(5)

        # --- CUADRO DE TOTAL FINAL GENERAL ---
        if pdf.get_y() > 260:
            pdf.add_page()

        pdf.set_fill_color(194, 207, 165)
        ANCHO_TOTAL = 55
        ALTO_TOTAL = 15
        x_inicial_total = pdf.w - ANCHO_TOTAL - 10
        y_inicial_total = pdf.get_y()

        pdf.rect(x_inicial_total, y_inicial_total, ANCHO_TOTAL, ALTO_TOTAL, style='F')

        pdf.set_xy(x_inicial_total + 4, y_inicial_total + 2)
        pdf.set_font("helvetica", style='B', size=10)
        pdf.cell(0, 5, "Total Pendiente", border=0)

        pdf.set_font("helvetica", style='B', size=13)
        pdf.set_xy(x_inicial_total, y_inicial_total + 7)
        pdf.cell(ANCHO_TOTAL, 8, formato_moneda(total), border=0, align='C')

        # Guardar en archivo temporal para retornar bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf.output(tmp.name)
            with open(tmp.name, "rb") as f:
                pdf_bytes = f.read()
                
        try:
            import os
            os.unlink(tmp.name)
        except:
            pass
            
        lugar_slug = lugar_nombre.replace(" ", "_").strip()
        file_name = f"Estado_Cuenta_{lugar_slug}.pdf"
        
        return pdf_bytes, file_name

    except Exception as e:
        raise Exception(f"Error en la maquetación del PDF: {str(e)}")