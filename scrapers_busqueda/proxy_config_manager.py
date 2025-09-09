"""
🌐 Proxy Configuration Manager para Ripley Stealth
Gestor avanzado de configuración de proxies con validación y rotación automática
"""

import sys
import io
import requests
import json
import time
import random
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import os

# Configurar encoding para Windows con soporte de emojis
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ProxyManager:
    def __init__(self):
        self.proxy_pool = []
        self.working_proxies = []
        self.failed_proxies = []
        
    def add_proxy(self, host, port, user, password, country="Unknown", provider="Manual"):
        """➕ Agregar proxy al pool"""
        proxy_config = {
            "host": host,
            "port": str(port),
            "user": user,
            "pass": password,
            "country": country,
            "provider": provider,
            "last_tested": None,
            "success_rate": 0.0,
            "total_tests": 0,
            "successful_tests": 0
        }
        
        self.proxy_pool.append(proxy_config)
        logging.info(f"➕ Proxy agregado: {host}:{port} ({country})")
        
    def test_proxy(self, proxy_config, timeout=10):
        """🧪 Probar un proxy individual"""
        proxy_url = f"http://{proxy_config['user']}:{proxy_config['pass']}@{proxy_config['host']}:{proxy_config['port']}"
        
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        test_urls = [
            'http://httpbin.org/ip',
            'http://www.google.com',
            'https://simple.ripley.cl'
        ]
        
        results = {'working': False, 'latency': None, 'ip': None, 'errors': []}
        
        for test_url in test_urls:
            try:
                start_time = time.time()
                response = requests.get(
                    test_url, 
                    proxies=proxies, 
                    timeout=timeout,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )
                
                latency = time.time() - start_time
                
                if response.status_code == 200:
                    results['working'] = True
                    results['latency'] = latency
                    
                    # Extraer IP si es httpbin
                    if 'httpbin.org/ip' in test_url:
                        try:
                            ip_data = response.json()
                            results['ip'] = ip_data.get('origin', 'Unknown')
                        except:
                            pass
                    
                    break  # Proxy funciona, no probar más URLs
                    
            except Exception as e:
                results['errors'].append(f"{test_url}: {str(e)}")
                continue
        
        # Actualizar estadísticas
        proxy_config['total_tests'] += 1
        proxy_config['last_tested'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if results['working']:
            proxy_config['successful_tests'] += 1
            
        proxy_config['success_rate'] = (proxy_config['successful_tests'] / proxy_config['total_tests']) * 100
        
        return results
    
    def test_all_proxies(self, max_workers=5):
        """🔄 Probar todos los proxies en paralelo"""
        logging.info(f"🧪 Probando {len(self.proxy_pool)} proxies...")
        
        self.working_proxies = []
        self.failed_proxies = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Enviar todas las pruebas
            future_to_proxy = {
                executor.submit(self.test_proxy, proxy): proxy 
                for proxy in self.proxy_pool
            }
            
            # Recopilar resultados
            for future in future_to_proxy:
                proxy = future_to_proxy[future]
                try:
                    result = future.result(timeout=30)
                    
                    if result['working']:
                        proxy['test_result'] = result
                        self.working_proxies.append(proxy)
                        logging.info(f"✅ {proxy['host']}:{proxy['port']} - OK ({result['latency']:.2f}s) IP: {result.get('ip', 'N/A')}")
                    else:
                        proxy['test_result'] = result
                        self.failed_proxies.append(proxy)
                        logging.warning(f"❌ {proxy['host']}:{proxy['port']} - FAILED")
                        
                except Exception as e:
                    logging.error(f"💥 Error probando {proxy['host']}:{proxy['port']}: {e}")
                    proxy['test_result'] = {'working': False, 'error': str(e)}
                    self.failed_proxies.append(proxy)
        
        # Ordenar working proxies por latencia
        self.working_proxies.sort(key=lambda p: p['test_result'].get('latency', 999))
        
        logging.info(f"📊 Resultado: {len(self.working_proxies)} proxies funcionando, {len(self.failed_proxies)} fallaron")
        
    def get_best_proxies(self, count=3):
        """🏆 Obtener los mejores proxies"""
        return self.working_proxies[:count]
    
    def get_random_working_proxy(self):
        """🎲 Obtener proxy aleatorio que funciona"""
        if not self.working_proxies:
            return None
        return random.choice(self.working_proxies)
    
    def save_results(self, filename=None):
        """💾 Guardar resultados de pruebas"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"proxy_test_results_{timestamp}.json"
        
        results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_proxies': len(self.proxy_pool),
            'working_proxies': len(self.working_proxies),
            'failed_proxies': len(self.failed_proxies),
            'success_rate': (len(self.working_proxies) / len(self.proxy_pool) * 100) if self.proxy_pool else 0,
            'proxies': self.proxy_pool
        }
        
        output_dir = r"D:\Scrappers Normalizacion\1.1 ML\Datos de prueba\Ripley"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logging.info(f"💾 Resultados guardados en: {filepath}")
        return filepath
    
    def generate_stealth_config(self):
        """🥷 Generar configuración para el scraper stealth"""
        if not self.working_proxies:
            logging.warning("⚠️ No hay proxies funcionando disponibles")
            return []
        
        # Crear configuración optimizada
        stealth_config = []
        
        for proxy in self.working_proxies:
            config = {
                "host": proxy['host'],
                "port": proxy['port'],
                "user": proxy['user'],
                "pass": proxy['pass'],
                "country": proxy['country'],
                "latency": proxy['test_result'].get('latency', 0),
                "success_rate": proxy['success_rate'],
                "last_tested": proxy['last_tested']
            }
            stealth_config.append(config)
        
        return stealth_config

# Configuración predeterminada de proxies para Chile/Latam
def setup_default_proxies():
    """🌐 Configurar pool completo de 10 proxies Decodo"""
    manager = ProxyManager()
    
    # Pool completo de 10 proxies con diferentes puertos
    proxy_configs = [
        {"port": 30001, "session": "sessionduration-1"},
        {"port": 30002, "session": "sessionduration-1"},
        {"port": 30003, "session": "sessionduration-1"},
        {"port": 30004, "session": "sessionduration-1"},
        {"port": 30005, "session": "sessionduration-1"},
        {"port": 30006, "session": "sessionduration-1"},
        {"port": 30007, "session": "sessionduration-1"},
        {"port": 30008, "session": "sessionduration-1"},
        {"port": 30009, "session": "sessionduration-1"},
        {"port": 30010, "session": "sessionduration-1"}
    ]
    
    for i, config in enumerate(proxy_configs, 1):
        manager.add_proxy(
            host="cl.decodo.com",
            port=config["port"],
            user=f"user-sprhxdrm60-{config['session']}",
            password="rdAZz6ddZf+kv71f1A",
            country="CL",
            provider=f"Decodo-{i:02d}"
        )
    
    return manager

def main():
    """🚀 Función principal de prueba de proxies"""
    print("🌐 PROXY CONFIGURATION MANAGER")
    print("="*50)
    
    # Configurar manager con proxies predeterminados
    manager = setup_default_proxies()
    
    print(f"📋 Proxies configurados: {len(manager.proxy_pool)}")
    
    # Probar todos los proxies
    manager.test_all_proxies()
    
    # Mostrar resultados
    print("\n📊 RESULTADOS:")
    print(f"✅ Proxies funcionando: {len(manager.working_proxies)}")
    print(f"❌ Proxies fallidos: {len(manager.failed_proxies)}")
    
    if manager.working_proxies:
        print("\n🏆 MEJORES PROXIES:")
        for i, proxy in enumerate(manager.get_best_proxies(5), 1):
            result = proxy['test_result']
            print(f"   {i}. {proxy['host']}:{proxy['port']} ({proxy['country']}) - {result['latency']:.2f}s")
    
    # Guardar resultados
    results_file = manager.save_results()
    
    # Generar configuración para stealth scraper
    stealth_config = manager.generate_stealth_config()
    
    if stealth_config:
        print("\n🥷 CONFIGURACIÓN STEALTH GENERADA:")
        print("Copia esta configuración al scraper stealth:")
        print("-" * 40)
        print("PROXY_POOL = [")
        for proxy in stealth_config:
            print(f'    {{')
            print(f'        "host": "{proxy["host"]}",')
            print(f'        "port": "{proxy["port"]}",')  
            print(f'        "user": "{proxy["user"]}",')
            print(f'        "pass": "{proxy["pass"]}",')
            print(f'        "country": "{proxy["country"]}"')
            print(f'    }},')
        print("]")
        print("-" * 40)
    else:
        print("⚠️ No se pudo generar configuración stealth - no hay proxies funcionando")

if __name__ == "__main__":
    main()