import secrets
import string
from typing import Optional, List
import structlog

logger = structlog.get_logger()

class CodeGenerator:
    """Generador de códigos únicos para stickers"""
    
    def __init__(self):
        self.used_codes = set()  # Cache de códigos usados en memoria
    
    def generate_discount_code(
        self, 
        site_id: str, 
        sticker_type: str, 
        length: int = 8
    ) -> str:
        """Generar código de descuento único"""
        try:
            # Crear prefijo basado en el sitio y tipo
            prefix = self._create_prefix(site_id, sticker_type)
            
            # Generar parte aleatoria
            random_part = self._generate_random_part(length)
            
            # Combinar prefijo y parte aleatoria
            code = f"{prefix}-{random_part}"
            
            # Verificar unicidad
            if code in self.used_codes:
                # Si ya existe, generar uno nuevo
                return self.generate_discount_code(site_id, sticker_type, length)
            
            # Agregar a cache
            self.used_codes.add(code)
            
            logger.debug("Discount code generated", 
                        site_id=site_id, 
                        sticker_type=sticker_type, 
                        code=code)
            
            return code
            
        except Exception as e:
            logger.error("Error generating discount code", 
                        site_id=site_id, 
                        sticker_type=sticker_type, 
                        error=str(e))
            # Fallback: usar timestamp
            return self._generate_fallback_code(site_id, sticker_type)
    
    def generate_batch_codes(
        self, 
        site_id: str, 
        sticker_type: str, 
        quantity: int,
        length: int = 8
    ) -> List[str]:
        """Generar múltiples códigos únicos"""
        try:
            codes = []
            
            for _ in range(quantity):
                code = self.generate_discount_code(site_id, sticker_type, length)
                codes.append(code)
            
            logger.info("Batch codes generated", 
                       site_id=site_id, 
                       sticker_type=sticker_type, 
                       quantity=quantity)
            
            return codes
            
        except Exception as e:
            logger.error("Error generating batch codes", 
                        site_id=site_id, 
                        sticker_type=sticker_type, 
                        quantity=quantity, 
                        error=str(e))
            return []
    
    def generate_custom_code(
        self, 
        site_id: str, 
        pattern: str,
        variables: Optional[dict] = None
    ) -> str:
        """Generar código con patrón personalizado"""
        try:
            # Reemplazar variables en el patrón
            if variables:
                for key, value in variables.items():
                    pattern = pattern.replace(f"{{{key}}}", str(value))
            
            # Reemplazar placeholders con valores aleatorios
            code = self._replace_placeholders(pattern)
            
            # Verificar unicidad
            if code in self.used_codes:
                # Si ya existe, modificar ligeramente
                code = self._make_unique(code)
            
            # Agregar a cache
            self.used_codes.add(code)
            
            logger.debug("Custom code generated", 
                        site_id=site_id, 
                        pattern=pattern, 
                        code=code)
            
            return code
            
        except Exception as e:
            logger.error("Error generating custom code", 
                        site_id=site_id, 
                        pattern=pattern, 
                        error=str(e))
            return self._generate_fallback_code(site_id, "custom")
    
    def validate_code_format(self, code: str, expected_pattern: str) -> bool:
        """Validar formato de código"""
        try:
            # Convertir patrón a regex
            import re
            regex_pattern = self._pattern_to_regex(expected_pattern)
            
            # Validar código
            is_valid = bool(re.match(regex_pattern, code))
            
            logger.debug("Code format validated", 
                        code=code, 
                        pattern=expected_pattern, 
                        is_valid=is_valid)
            
            return is_valid
            
        except Exception as e:
            logger.error("Error validating code format", 
                        code=code, 
                        pattern=expected_pattern, 
                        error=str(e))
            return False
    
    def _create_prefix(self, site_id: str, sticker_type: str) -> str:
        """Crear prefijo para el código"""
        # Tomar primeras 3 letras del site_id
        site_prefix = site_id.upper()[:3]
        
        # Mapear tipo de sticker a código
        type_map = {
            "registro": "REG",
            "instagram": "IG",
            "reseña": "RES",
            "video": "VID",
            "especial": "ESP"
        }
        
        type_prefix = type_map.get(sticker_type.lower(), "STK")
        
        return f"{site_prefix}{type_prefix}"
    
    def _generate_random_part(self, length: int) -> str:
        """Generar parte aleatoria del código"""
        # Usar letras mayúsculas y números, excluyendo caracteres confusos
        characters = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')
        return ''.join(secrets.choices(characters, k=length))
    
    def _replace_placeholders(self, pattern: str) -> str:
        """Reemplazar placeholders en el patrón"""
        import re
        
        # Reemplazar {RANDOM} con caracteres aleatorios
        pattern = re.sub(r'\{RANDOM:(\d+)\}', 
                        lambda m: self._generate_random_part(int(m.group(1))), 
                        pattern)
        
        # Reemplazar {RANDOM} con 8 caracteres por defecto
        pattern = re.sub(r'\{RANDOM\}', 
                        lambda m: self._generate_random_part(8), 
                        pattern)
        
        # Reemplazar {DATE} con fecha actual
        from datetime import datetime
        pattern = re.sub(r'\{DATE\}', 
                        datetime.now().strftime('%Y%m%d'), 
                        pattern)
        
        # Reemplazar {TIME} con timestamp
        pattern = re.sub(r'\{TIME\}', 
                        str(int(datetime.now().timestamp())), 
                        pattern)
        
        return pattern
    
    def _pattern_to_regex(self, pattern: str) -> str:
        """Convertir patrón a expresión regular"""
        import re
        
        # Escapar caracteres especiales
        pattern = re.escape(pattern)
        
        # Reemplazar placeholders con regex
        pattern = pattern.replace(r'\{RANDOM:(\d+)\}', r'[A-HJ-NP-Z2-9]{\1}')
        pattern = pattern.replace(r'\{RANDOM\}', r'[A-HJ-NP-Z2-9]{8}')
        pattern = pattern.replace(r'\{DATE\}', r'\d{8}')
        pattern = pattern.replace(r'\{TIME\}', r'\d{10}')
        
        return f"^{pattern}$"
    
    def _make_unique(self, code: str) -> str:
        """Hacer el código único modificándolo ligeramente"""
        # Agregar sufijo numérico
        counter = 1
        while f"{code}{counter}" in self.used_codes:
            counter += 1
        
        return f"{code}{counter}"
    
    def _generate_fallback_code(self, site_id: str, sticker_type: str) -> str:
        """Generar código de respaldo usando timestamp"""
        from datetime import datetime
        timestamp = int(datetime.now().timestamp())
        return f"{site_id.upper()[:3]}{sticker_type.upper()[:3]}{timestamp}"
    
    def clear_cache(self):
        """Limpiar cache de códigos usados"""
        self.used_codes.clear()
        logger.info("Code cache cleared")
    
    def get_cache_size(self) -> int:
        """Obtener tamaño del cache"""
        return len(self.used_codes)
    
    def add_used_code(self, code: str):
        """Agregar código usado al cache"""
        self.used_codes.add(code)
        logger.debug("Code added to cache", code=code)
    
    def is_code_used(self, code: str) -> bool:
        """Verificar si un código ya fue usado"""
        return code in self.used_codes
