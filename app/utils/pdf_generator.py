from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from typing import Optional, Dict, Any, List
import structlog
import os
from pathlib import Path
from PIL import Image as PILImage
import io

logger = structlog.get_logger()

class PDFGenerator:
    """Generador de PDFs para stickers y documentos"""
    
    def __init__(self):
        self.output_dir = Path("static/pdfs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
    
    async def generate_sticker_pdf(
        self, 
        sticker_data: Dict[str, Any],
        site_config: Dict[str, Any],
        filename: str
    ) -> Optional[str]:
        """Generar PDF del sticker"""
        try:
            file_path = self.output_dir / filename
            
            # Crear documento PDF
            doc = SimpleDocTemplate(
                str(file_path),
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Contenido del PDF
            story = []
            
            # Título
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=HexColor(site_config.get('primary_color', '#e74c3c'))
            )
            
            title = Paragraph(f"Sticker de Descuento - {site_config.get('site_name', 'Sitio')}", title_style)
            story.append(title)
            story.append(Spacer(1, 20))
            
            # Información del sticker
            info_data = [
                ['Código de Descuento:', sticker_data.get('codigo_descuento', 'N/A')],
                ['Porcentaje:', f"{sticker_data.get('porcentaje_descuento', 0)}%"],
                ['Tipo:', sticker_data.get('tipo_sticker', 'N/A')],
                ['Fecha de Expiración:', sticker_data.get('fecha_expiracion', 'N/A')],
                ['Usuario:', sticker_data.get('usuario_nombre', 'N/A')],
            ]
            
            info_table = Table(info_data, colWidths=[2*inch, 3*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), HexColor(site_config.get('secondary_color', '#2c3e50'))),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (1, 0), (1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 30))
            
            # Código QR si está disponible
            if sticker_data.get('qr_code_url'):
                qr_path = f"static/qr_codes/{os.path.basename(sticker_data['qr_code_url'])}"
                if os.path.exists(qr_path):
                    qr_img = Image(qr_path, width=2*inch, height=2*inch)
                    story.append(qr_img)
                    story.append(Spacer(1, 20))
            
            # Instrucciones de uso
            instructions_style = ParagraphStyle(
                'Instructions',
                parent=self.styles['Normal'],
                fontSize=12,
                spaceAfter=12,
                alignment=TA_LEFT
            )
            
            instructions = [
                "Instrucciones de Uso:",
                "1. Presenta este código al momento de realizar tu compra",
                "2. El descuento se aplicará automáticamente",
                "3. Este código es válido hasta la fecha de expiración indicada",
                "4. No se puede combinar con otras ofertas",
                "5. Un código por compra"
            ]
            
            for instruction in instructions:
                story.append(Paragraph(instruction, instructions_style))
            
            # Pie de página
            story.append(Spacer(1, 30))
            footer_style = ParagraphStyle(
                'Footer',
                parent=self.styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                textColor=HexColor(site_config.get('secondary_color', '#2c3e50'))
            )
            
            footer = Paragraph(
                f"Generado por {site_config.get('site_name', 'Sistema de Fidelización')} - "
                f"Fecha: {sticker_data.get('fecha_generacion', 'N/A')}",
                footer_style
            )
            story.append(footer)
            
            # Construir PDF
            doc.build(story)
            
            # Generar URL
            pdf_url = f"/static/pdfs/{filename}"
            
            logger.info("Sticker PDF generated", 
                       filename=filename, 
                       site_id=site_config.get('site_id'))
            
            return pdf_url
            
        except Exception as e:
            logger.error("Error generating sticker PDF", 
                        filename=filename, 
                        error=str(e))
            return None
    
    async def generate_sticker_image(
        self, 
        sticker: Any,
        site_config: Any,
        template_id: str = "default"
    ) -> Optional[str]:
        """Generar imagen del sticker"""
        try:
            # Crear imagen del sticker usando PIL
            width, height = 400, 300
            img = PILImage.new('RGB', (width, height), 'white')
            draw = PILImage.Draw(img)
            
            # Colores del sitio
            primary_color = site_config.primary_color if hasattr(site_config, 'primary_color') else '#e74c3c'
            secondary_color = site_config.secondary_color if hasattr(site_config, 'secondary_color') else '#2c3e50'
            
            # Convertir colores hex a RGB
            primary_rgb = tuple(int(primary_color[i:i+2], 16) for i in (1, 3, 5))
            secondary_rgb = tuple(int(secondary_color[i:i+2], 16) for i in (1, 3, 5))
            
            # Dibujar fondo
            draw.rectangle([0, 0, width, height], fill='white', outline=secondary_rgb, width=3)
            
            # Dibujar header
            draw.rectangle([0, 0, width, 80], fill=primary_rgb)
            
            # Título del sitio
            try:
                from PIL import ImageFont
                title_font = ImageFont.truetype("arial.ttf", 24)
            except:
                title_font = ImageFont.load_default()
            
            site_name = site_config.site_name if hasattr(site_config, 'site_name') else 'Sitio'
            draw.text((width//2, 40), site_name, fill='white', font=title_font, anchor='mm')
            
            # Código de descuento
            try:
                code_font = ImageFont.truetype("arial.ttf", 32)
            except:
                code_font = ImageFont.load_default()
            
            codigo = sticker.codigo_descuento if hasattr(sticker, 'codigo_descuento') else 'N/A'
            draw.text((width//2, 150), codigo, fill=primary_rgb, font=code_font, anchor='mm')
            
            # Porcentaje de descuento
            try:
                discount_font = ImageFont.truetype("arial.ttf", 48)
            except:
                discount_font = ImageFont.load_default()
            
            porcentaje = sticker.porcentaje_descuento if hasattr(sticker, 'porcentaje_descuento') else 0
            draw.text((width//2, 200), f"{porcentaje}%", fill=secondary_rgb, font=discount_font, anchor='mm')
            
            # Fecha de expiración
            try:
                date_font = ImageFont.truetype("arial.ttf", 12)
            except:
                date_font = ImageFont.load_default()
            
            fecha = sticker.fecha_expiracion.strftime('%d/%m/%Y') if hasattr(sticker, 'fecha_expiracion') else 'N/A'
            draw.text((width//2, 270), f"Válido hasta: {fecha}", fill='black', font=date_font, anchor='mm')
            
            # Guardar imagen
            filename = f"sticker_{sticker.id if hasattr(sticker, 'id') else 'unknown'}.png"
            file_path = self.output_dir / filename
            img.save(file_path, "PNG")
            
            # Generar URL
            image_url = f"/static/pdfs/{filename}"
            
            logger.info("Sticker image generated", 
                       filename=filename, 
                       site_id=site_config.site_id if hasattr(site_config, 'site_id') else 'unknown')
            
            return image_url
            
        except Exception as e:
            logger.error("Error generating sticker image", 
                        error=str(e))
            return None
    
    async def generate_batch_stickers_pdf(
        self, 
        stickers: List[Dict[str, Any]],
        site_config: Dict[str, Any],
        filename: str
    ) -> Optional[str]:
        """Generar PDF con múltiples stickers"""
        try:
            file_path = self.output_dir / filename
            
            # Crear documento PDF
            doc = SimpleDocTemplate(
                str(file_path),
                pagesize=A4,
                rightMargin=36,
                leftMargin=36,
                topMargin=36,
                bottomMargin=36
            )
            
            story = []
            
            # Título del documento
            title_style = ParagraphStyle(
                'BatchTitle',
                parent=self.styles['Heading1'],
                fontSize=20,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=HexColor(site_config.get('primary_color', '#e74c3c'))
            )
            
            title = Paragraph(f"Lote de Stickers - {site_config.get('site_name', 'Sitio')}", title_style)
            story.append(title)
            story.append(Spacer(1, 20))
            
            # Crear tabla con stickers
            table_data = [['Código', 'Tipo', 'Descuento', 'Expiración', 'Usuario']]
            
            for sticker in stickers:
                table_data.append([
                    sticker.get('codigo_descuento', 'N/A'),
                    sticker.get('tipo_sticker', 'N/A'),
                    f"{sticker.get('porcentaje_descuento', 0)}%",
                    sticker.get('fecha_expiracion', 'N/A'),
                    sticker.get('usuario_nombre', 'N/A')
                ])
            
            # Crear tabla
            table = Table(table_data, colWidths=[1.5*inch, 1*inch, 0.8*inch, 1.2*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor(site_config.get('primary_color', '#e74c3c'))),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            
            # Construir PDF
            doc.build(story)
            
            # Generar URL
            pdf_url = f"/static/pdfs/{filename}"
            
            logger.info("Batch stickers PDF generated", 
                       filename=filename, 
                       sticker_count=len(stickers))
            
            return pdf_url
            
        except Exception as e:
            logger.error("Error generating batch stickers PDF", 
                        filename=filename, 
                        error=str(e))
            return None
    
    async def generate_analytics_report(
        self, 
        analytics_data: Dict[str, Any],
        site_config: Dict[str, Any],
        filename: str
    ) -> Optional[str]:
        """Generar reporte de analytics en PDF"""
        try:
            file_path = self.output_dir / filename
            
            # Crear documento PDF
            doc = SimpleDocTemplate(
                str(file_path),
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            story = []
            
            # Título del reporte
            title_style = ParagraphStyle(
                'ReportTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=HexColor(site_config.get('primary_color', '#e74c3c'))
            )
            
            title = Paragraph(f"Reporte de Analytics - {site_config.get('site_name', 'Sitio')}", title_style)
            story.append(title)
            story.append(Spacer(1, 20))
            
            # Resumen ejecutivo
            summary_style = ParagraphStyle(
                'Summary',
                parent=self.styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                textColor=HexColor(site_config.get('secondary_color', '#2c3e50'))
            )
            
            summary = Paragraph("Resumen Ejecutivo", summary_style)
            story.append(summary)
            
            # Métricas principales
            metrics_data = [
                ['Métrica', 'Valor'],
                ['Total de Stickers Generados', str(analytics_data.get('total_generados', 0))],
                ['Total de Stickers Usados', str(analytics_data.get('total_usados', 0))],
                ['Porcentaje de Uso', f"{analytics_data.get('porcentaje_uso', 0)}%"],
                ['Stickers Expirados', str(analytics_data.get('total_expirados', 0))]
            ]
            
            metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor(site_config.get('secondary_color', '#2c3e50'))),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(metrics_table)
            story.append(Spacer(1, 30))
            
            # Construir PDF
            doc.build(story)
            
            # Generar URL
            pdf_url = f"/static/pdfs/{filename}"
            
            logger.info("Analytics report PDF generated", 
                       filename=filename, 
                       site_id=site_config.get('site_id'))
            
            return pdf_url
            
        except Exception as e:
            logger.error("Error generating analytics report PDF", 
                        filename=filename, 
                        error=str(e))
            return None
    
    def cleanup_old_pdfs(self, days_old: int = 30) -> int:
        """Limpiar PDFs antiguos"""
        try:
            import time
            current_time = time.time()
            cutoff_time = current_time - (days_old * 24 * 60 * 60)
            
            deleted_count = 0
            for file_path in self.output_dir.glob("*.pdf"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
            
            logger.info("Old PDFs cleaned up", 
                       deleted_count=deleted_count, 
                       days_old=days_old)
            
            return deleted_count
            
        except Exception as e:
            logger.error("Error cleaning up old PDFs", 
                        error=str(e))
            return 0
