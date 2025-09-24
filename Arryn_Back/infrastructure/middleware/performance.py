"""
Middleware personalizado para manejo de concurrencia alta
"""
import os
import time
import hashlib
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger('arryn')


class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware para limitar la tasa de requests por IP
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Configuración desde variables de entorno
        self.rate_limit = int(os.getenv("RATE_LIMIT_REQUESTS", 100))  # requests por minuto
        self.window_size = int(os.getenv("RATE_LIMIT_WINDOW", 60))  # ventana de tiempo en segundos
        super().__init__(get_response)
        
    def process_request(self, request):
        # Obtener IP del cliente
        ip = self.get_client_ip(request)
        
        # Generar clave para cache
        cache_key = f"rate_limit_{ip}"
        
        # Obtener datos actuales del cache
        current_data = cache.get(cache_key, {'count': 0, 'window_start': time.time()})
        
        current_time = time.time()
        
        # Si ha pasado la ventana de tiempo, resetear contador
        if current_time - current_data['window_start'] > self.window_size:
            current_data = {'count': 1, 'window_start': current_time}
        else:
            current_data['count'] += 1
        
        # Guardar en cache
        cache.set(cache_key, current_data, self.window_size)
        
        # Verificar si se excede el límite
        if current_data['count'] > self.rate_limit:
            logger.warning(f"Rate limit exceeded for IP {ip}: {current_data['count']} requests")
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'limit': self.rate_limit,
                'window': self.window_size,
                'retry_after': int(self.window_size - (current_time - current_data['window_start']))
            }, status=429)
        
        return None
    
    def get_client_ip(self, request):
        """Obtiene la IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ResponseCacheMiddleware(MiddlewareMixin):
    """
    Middleware para cache de respuestas API
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.cacheable_paths = [
            '/api/brands/',
            '/api/offers/',
            '/api/best-prices/',
            '/api/ranked-offers/',
            '/api/trending-offers/',
            '/api/reports/'
        ]
        self.cache_timeout = int(os.getenv("RESPONSE_CACHE_TIMEOUT", 300))  # 5 minutos por defecto
        super().__init__(get_response)
    
    def process_request(self, request):
        # Solo cachear GET requests
        if request.method != 'GET':
            return None
        
        # Verificar si la ruta es cacheable
        if not any(request.path.startswith(path) for path in self.cacheable_paths):
            return None
        
        # Generar clave de cache basada en URL y parámetros
        cache_key = self.generate_cache_key(request)
        
        # Intentar obtener respuesta del cache
        cached_response = cache.get(cache_key)
        if cached_response:
            logger.info(f"Cache hit for {request.path}")
            return JsonResponse(cached_response)
        
        return None
    
    def process_response(self, request, response):
        # Solo cachear respuestas exitosas de GET
        if (request.method == 'GET' and 
            response.status_code == 200 and
            any(request.path.startswith(path) for path in self.cacheable_paths)):
            
            cache_key = self.generate_cache_key(request)
            
            # Cachear el contenido de la respuesta
            try:
                import json
                response_data = json.loads(response.content.decode('utf-8'))
                cache.set(cache_key, response_data, self.cache_timeout)
                logger.info(f"Cached response for {request.path}")
            except Exception as e:
                logger.error(f"Failed to cache response: {e}")
        
        return response
    
    def generate_cache_key(self, request):
        """Genera una clave única para el cache"""
        url_with_params = request.get_full_path()
        hash_key = hashlib.md5(url_with_params.encode('utf-8')).hexdigest()
        return f"api_cache_{hash_key}"


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware para logging de requests para monitoreo de performance
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log requests lentos (configurable desde .env)
            slow_threshold = float(os.getenv("REQUEST_LOG_SLOW_THRESHOLD", 1.0))
            if duration > slow_threshold:
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration:.2f}s - Status: {response.status_code}"
                )
            else:
                logger.info(
                    f"{request.method} {request.path} - "
                    f"{duration:.3f}s - Status: {response.status_code}"
                )
        
        return response