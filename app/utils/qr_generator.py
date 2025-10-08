import qrcode
from qrcode.image.pil import PilImage
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from typing import Optional, Dict, Any
import structlog
import os
from pathlib import Path

logger = structlog.get_logger()

class QRGenerator:
    """Generador de códigos QR para stickers"""
    
    def __init__(self):
        self.output_dir = Path("static/qr_codes")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_qr(
        self, 
        data: str, 
        filename: str,
        size: int = 200,
        border: int = 4,
        error_correction: str = "M",
        fill_color: str = "black",
        back_color: str = "white"
    ) -> Optional[str]:
        """Generar código QR y guardar como archivo"""
        try:
            # Crear código QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=self._get_error_correction(error_correction),
                box_size=10,
                border=border,
            )
            
            qr.add_data(data)
            qr.make(fit=True)
            
            # Crear imagen
            img = qr.make_image(
                fill_color=fill_color,
                back_color=back_color,
                image_factory=PilImage
            )
            
            # Redimensionar si es necesario
            if size != 200:
                img = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Guardar archivo
            file_path = self.output_dir / filename
            img.save(file_path, "PNG")
            
            # Generar URL
            qr_url = f"/static/qr_codes/{filename}"
            
            logger.info("QR code generated", 
                       filename=filename, 
                       size=size, 
                       data_length=len(data))
            
            return qr_url
            
        except Exception as e:
            logger.error("Error generating QR code", 
                        filename=filename, 
                        error=str(e))
            return None
    
    async def generate_qr_with_logo(
        self, 
        data: str, 
        filename: str,
        logo_path: str,
        size: int = 200,
        logo_size: int = 50
    ) -> Optional[str]:
        """Generar código QR con logo en el centro"""
        try:
            # Generar QR base
            qr_url = await self.generate_qr(data, filename, size)
            if not qr_url:
                return None
            
            # Cargar imagen QR
            qr_path = self.output_dir / filename
            qr_img = Image.open(qr_path)
            
            # Cargar logo
            logo_img = Image.open(logo_path)
            
            # Redimensionar logo
            logo_img = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Crear máscara circular para el logo
            mask = Image.new('L', (logo_size, logo_size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, logo_size, logo_size), fill=255)
            
            # Aplicar máscara al logo
            logo_img.putalpha(mask)
            
            # Calcular posición del logo (centro del QR)
            qr_width, qr_height = qr_img.size
            logo_x = (qr_width - logo_size) // 2
            logo_y = (qr_height - logo_size) // 2
            
            # Pegar logo en el QR
            qr_img.paste(logo_img, (logo_x, logo_y), logo_img)
            
            # Guardar imagen final
            qr_img.save(qr_path, "PNG")
            
            logger.info("QR code with logo generated", 
                       filename=filename, 
                       logo_path=logo_path)
            
            return qr_url
            
        except Exception as e:
            logger.error("Error generating QR with logo", 
                        filename=filename, 
                        logo_path=logo_path, 
                        error=str(e))
            return None
    
    async def generate_qr_base64(
        self, 
        data: str,
        size: int = 200,
        format: str = "PNG"
    ) -> Optional[str]:
        """Generar código QR y devolver como base64"""
        try:
            # Crear código QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            
            qr.add_data(data)
            qr.make(fit=True)
            
            # Crear imagen
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Redimensionar si es necesario
            if size != 200:
                img = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Convertir a base64
            buffer = io.BytesIO()
            img.save(buffer, format=format)
            buffer.seek(0)
            
            # Codificar en base64
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            logger.info("QR code generated as base64", 
                       size=size, 
                       format=format, 
                       data_length=len(data))
            
            return img_base64
            
        except Exception as e:
            logger.error("Error generating QR base64", 
                        error=str(e))
            return None
    
    async def generate_qr_with_text(
        self, 
        data: str, 
        filename: str,
        text: str,
        size: int = 200,
        text_size: int = 20
    ) -> Optional[str]:
        """Generar código QR con texto debajo"""
        try:
            # Generar QR base
            qr_url = await self.generate_qr(data, filename, size)
            if not qr_url:
                return None
            
            # Cargar imagen QR
            qr_path = self.output_dir / filename
            qr_img = Image.open(qr_path)
            
            # Crear imagen con texto
            text_height = text_size + 20  # Altura del texto + padding
            final_img = Image.new('RGB', (size, size + text_height), 'white')
            
            # Pegar QR en la parte superior
            final_img.paste(qr_img, (0, 0))
            
            # Agregar texto
            draw = ImageDraw.Draw(final_img)
            
            # Intentar cargar fuente, usar default si no está disponible
            try:
                font = ImageFont.truetype("arial.ttf", text_size)
            except:
                font = ImageFont.load_default()
            
            # Calcular posición del texto (centrado)
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = (size - text_width) // 2
            text_y = size + 10
            
            # Dibujar texto
            draw.text((text_x, text_y), text, fill='black', font=font)
            
            # Guardar imagen final
            final_img.save(qr_path, "PNG")
            
            logger.info("QR code with text generated", 
                       filename=filename, 
                       text=text)
            
            return qr_url
            
        except Exception as e:
            logger.error("Error generating QR with text", 
                        filename=filename, 
                        text=text, 
                        error=str(e))
            return None
    
    async def generate_qr_sticker(
        self, 
        data: str, 
        filename: str,
        site_config: Dict[str, Any],
        size: int = 200
    ) -> Optional[str]:
        """Generar código QR personalizado para sticker"""
        try:
            # Crear código QR base
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            
            qr.add_data(data)
            qr.make(fit=True)
            
            # Crear imagen con colores del sitio
            primary_color = site_config.get('primary_color', '#e74c3c')
            secondary_color = site_config.get('secondary_color', '#2c3e50')
            
            img = qr.make_image(
                fill_color=primary_color,
                back_color='white',
                image_factory=PilImage
            )
            
            # Redimensionar
            img = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Agregar borde decorativo
            border_size = 10
            final_img = Image.new('RGB', (size + 2*border_size, size + 2*border_size), secondary_color)
            final_img.paste(img, (border_size, border_size))
            
            # Guardar archivo
            file_path = self.output_dir / filename
            final_img.save(file_path, "PNG")
            
            # Generar URL
            qr_url = f"/static/qr_codes/{filename}"
            
            logger.info("Custom QR sticker generated", 
                       filename=filename, 
                       site_id=site_config.get('site_id'))
            
            return qr_url
            
        except Exception as e:
            logger.error("Error generating custom QR sticker", 
                        filename=filename, 
                        error=str(e))
            return None
    
    def _get_error_correction(self, level: str):
        """Obtener nivel de corrección de errores"""
        levels = {
            "L": qrcode.constants.ERROR_CORRECT_L,
            "M": qrcode.constants.ERROR_CORRECT_M,
            "Q": qrcode.constants.ERROR_CORRECT_Q,
            "H": qrcode.constants.ERROR_CORRECT_H,
        }
        return levels.get(level.upper(), qrcode.constants.ERROR_CORRECT_M)
    
    async def cleanup_old_qr_codes(self, days_old: int = 30):
        """Limpiar códigos QR antiguos"""
        try:
            import time
            current_time = time.time()
            cutoff_time = current_time - (days_old * 24 * 60 * 60)
            
            deleted_count = 0
            for file_path in self.output_dir.glob("*.png"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
            
            logger.info("Old QR codes cleaned up", 
                       deleted_count=deleted_count, 
                       days_old=days_old)
            
            return deleted_count
            
        except Exception as e:
            logger.error("Error cleaning up old QR codes", 
                        error=str(e))
            return 0
    
    def get_qr_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """Obtener información de un código QR"""
        try:
            file_path = self.output_dir / filename
            
            if not file_path.exists():
                return None
            
            stat = file_path.stat()
            
            return {
                "filename": filename,
                "size_bytes": stat.st_size,
                "created_at": stat.st_ctime,
                "modified_at": stat.st_mtime,
                "path": str(file_path)
            }
            
        except Exception as e:
            logger.error("Error getting QR info", 
                        filename=filename, 
                        error=str(e))
            return None
