"""
🔄 Ripley Scraper con ROTACIÓN DE PROXIES
Usa un proxy diferente para cada página - máxima evasión de detección
Pool de 10 proxies validados con diferentes IPs chilenas 🇨🇱
"""

import sys
import io
import json
import time
import re
import random
import zipfile
import tempfile
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import logging
import os
from threading import Event

# Configurar encoding para Windows con soporte de emojis 🔄
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configurar logging
output_log_dir = r"D:\Scrappers Normalizacion\1.1 ML\Datos de prueba\Ripley"
os.makedirs(output_log_dir, exist_ok=True)
log_file_path = os.path.join(output_log_dir, 'ripley_proxy_rotation.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Global para controlar la ejecución
stop_event = Event()

# === CONFIGURACIÓN DE BÚSQUEDAS - PRUEBA DE FUEGO ===
BUSQUEDAS_ROTATION = {
    "perfume": {
        "term": "perfumes",
        "name": "Perfumes 🌸",
        "base_url": "https://simple.ripley.cl/belleza/perfumeria"
    },
    "smartv": {
        "term": "smartv",
        "name": "Smart TV 📺",
        "base_url": "https://simple.ripley.cl/search/smartv"
    },
    "smartphone": {
        "term": "smartphone", 
        "name": "Smartphones 📱",
        "base_url": "https://simple.ripley.cl/tecno/celulares"
    }
}

# === POOL DE PROXIES VALIDADOS ===
PROXY_POOL_VALIDATED = [
    {
        "host": "cl.decodo.com",
        "port": "30007",
        "user": "user-sprhxdrm60-sessionduration-1",
        "pass": "rdAZz6ddZf+kv71f1A",
        "country": "CL",
        "ip": "181.42.18.21",
        "latency": 4.29
    },
    {
        "host": "cl.decodo.com",
        "port": "30008", 
        "user": "user-sprhxdrm60-sessionduration-1",
        "pass": "rdAZz6ddZf+kv71f1A",
        "country": "CL",
        "ip": "190.5.38.0",
        "latency": 4.42
    },
    {
        "host": "cl.decodo.com",
        "port": "30006",
        "user": "user-sprhxdrm60-sessionduration-1",
        "pass": "rdAZz6ddZf+kv71f1A",
        "country": "CL",
        "ip": "190.114.32.6",
        "latency": 4.65
    },
    {
        "host": "cl.decodo.com",
        "port": "30010",
        "user": "user-sprhxdrm60-sessionduration-1",
        "pass": "rdAZz6ddZf+kv71f1A",
        "country": "CL",
        "ip": "200.86.8.11",
        "latency": 4.96
    },
    {
        "host": "cl.decodo.com",
        "port": "30004",
        "user": "user-sprhxdrm60-sessionduration-1",
        "pass": "rdAZz6ddZf+kv71f1A",
        "country": "CL",
        "ip": "143.255.104.108",
        "latency": 5.41
    },
    {
        "host": "cl.decodo.com",
        "port": "30005",
        "user": "user-sprhxdrm60-sessionduration-1",
        "pass": "rdAZz6ddZf+kv71f1A",
        "country": "CL",
        "ip": "201.188.24.243",
        "latency": 5.51
    },
    {
        "host": "cl.decodo.com",
        "port": "30001",
        "user": "user-sprhxdrm60-sessionduration-1",
        "pass": "rdAZz6ddZf+kv71f1A",
        "country": "CL",
        "ip": "190.171.174.137",
        "latency": 5.68
    },
    {
        "host": "cl.decodo.com",
        "port": "30009",
        "user": "user-sprhxdrm60-sessionduration-1",
        "pass": "rdAZz6ddZf+kv71f1A",
        "country": "CL",
        "ip": "190.114.38.165",
        "latency": 5.71
    },
    {
        "host": "cl.decodo.com",
        "port": "30002",
        "user": "user-sprhxdrm60-sessionduration-1",
        "pass": "rdAZz6ddZf+kv71f1A",
        "country": "CL",
        "ip": "190.12.168.252",
        "latency": 6.05
    },
    {
        "host": "cl.decodo.com",
        "port": "30003",
        "user": "user-sprhxdrm60-sessionduration-1",
        "pass": "rdAZz6ddZf+kv71f1A",
        "country": "CL",
        "ip": "181.43.212.211",
        "latency": 6.45
    }
]

class ProxyRotator:
    """🔄 Gestor de rotación de proxies"""
    
    def __init__(self):
        self.proxy_pool = PROXY_POOL_VALIDATED.copy()
        self.current_index = 0
        self.usage_count = {}
        
        # Inicializar contador de uso
        for i, proxy in enumerate(self.proxy_pool):
            self.usage_count[i] = 0
    
    def get_next_proxy(self):
        """🎯 Obtener siguiente proxy en rotación"""
        proxy = self.proxy_pool[self.current_index]
        self.usage_count[self.current_index] += 1
        
        logging.info(f"🔄 Proxy {self.current_index + 1}/10: {proxy['host']}:{proxy['port']} (IP: {proxy['ip']})")
        
        # Avanzar al siguiente proxy
        self.current_index = (self.current_index + 1) % len(self.proxy_pool)
        
        return proxy
    
    def get_usage_stats(self):
        """📊 Estadísticas de uso de proxies"""
        return self.usage_count

def create_rotation_extension(proxy_config):
    """🔄 Extensión específica para proxy rotativo"""
    
    manifest_json = """
    {
        "version": "3.0.0",
        "manifest_version": 2,
        "name": "Proxy Rotation Extension",
        "permissions": [
            "proxy",
            "webRequest", 
            "webRequestBlocking",
            "<all_urls>"
        ],
        "background": {
            "scripts": ["background.js"]
        }
    }
    """
    
    background_js = f"""
    // Configuración de proxy rotativo
    var config = {{
        mode: "fixed_servers",
        rules: {{
            singleProxy: {{
                scheme: "http",
                host: "{proxy_config['host']}",
                port: parseInt({proxy_config['port']})
            }},
            bypassList: ["localhost", "127.0.0.1"]
        }}
    }};

    chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{
        console.log("Proxy rotativo configurado: {proxy_config['host']}:{proxy_config['port']}");
    }});

    // Autenticación
    chrome.webRequest.onAuthRequired.addListener(
        function(details) {{
            return {{
                authCredentials: {{
                    username: "{proxy_config['user']}",
                    password: "{proxy_config['pass']}"
                }}
            }};
        }},
        {{urls: ["<all_urls>"]}},
        ['blocking']
    );
    
    // Bloqueo mínimo para velocidad
    var minimalBlocks = [
        "*google-analytics.com*",
        "*googletagmanager.com*",
        "*facebook.com/tr*"
    ];
    
    chrome.webRequest.onBeforeRequest.addListener(
        function(details) {{
            var url = details.url.toLowerCase();
            
            for (var i = 0; i < minimalBlocks.length; i++) {{
                var pattern = minimalBlocks[i].toLowerCase().replace(/\\*/g, '');
                if (url.includes(pattern)) {{
                    return {{cancel: true}};
                }}
            }}
            
            return {{cancel: false}};
        }},
        {{urls: ["<all_urls>"]}},
        ["blocking"]
    );
    """
    
    # Crear directorio temporal
    temp_dir = tempfile.mkdtemp()
    
    # Guardar archivos
    with open(os.path.join(temp_dir, 'manifest.json'), 'w') as f:
        f.write(manifest_json)
    
    with open(os.path.join(temp_dir, 'background.js'), 'w') as f:
        f.write(background_js)
    
    # Crear ZIP
    extension_path = os.path.join(temp_dir, 'rotation_extension.zip')
    with zipfile.ZipFile(extension_path, 'w') as zip_file:
        zip_file.write(os.path.join(temp_dir, 'manifest.json'), 'manifest.json')
        zip_file.write(os.path.join(temp_dir, 'background.js'), 'background.js')
    
    return extension_path

def setup_rotation_driver(proxy_config):
    """🔄 Driver con proxy específico para rotación"""
    logging.info(f"🔄 Configurando Chrome con proxy rotativo...")
    
    chrome_options = Options()
    
    # === CONFIGURACIÓN BASE OPTIMIZADA ===
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # === ANTI-DETECCIÓN PROBADA ===
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # === USER AGENT PROBADO ===
    ua_probado = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    chrome_options.add_argument(f"--user-agent={ua_probado}")
    
    # === CONFIGURACIONES DE CONTENIDO ===
    prefs = {
        "profile.default_content_setting_values": {
            "images": 2,  # Bloquear imágenes
            "plugins": 2,
            "popups": 2,
            "geolocation": 2,
            "notifications": 2,
        }
    }
    
    chrome_options.add_experimental_option("prefs", prefs)
    
    # === CARGAR EXTENSIÓN CON PROXY ESPECÍFICO ===
    try:
        extension_path = create_rotation_extension(proxy_config)
        chrome_options.add_extension(extension_path)
        logging.info("✅ Extensión proxy rotativo cargada")
    except Exception as e:
        logging.warning(f"⚠️ Error cargando extensión: {e}")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # === SCRIPT ANTI-DETECCIÓN ===
    anti_detection_script = """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
            {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'}
        ]
    });
    Object.defineProperty(navigator, 'languages', {get: () => ['es-CL', 'es', 'en']});
    """
    
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': anti_detection_script
    })
    
    driver.set_page_load_timeout(15)
    driver.implicitly_wait(3)
    
    logging.info(f"✅ Driver con proxy {proxy_config['host']}:{proxy_config['port']} configurado")
    return driver

def extract_products_rotation(soup, page_num, search_term):
    """🔄 Extracción optimizada para rotación"""
    products = []
    
    # Usar selectores probados
    product_containers = soup.select('div.catalog-product-item')
    
    if not product_containers:
        product_containers = soup.select('div[data-cy*="product-"]')
    
    logging.info(f"📦 '{search_term}' P{page_num}: {len(product_containers)} productos detectados")
    
    for i, container in enumerate(product_containers, 1):
        try:
            # === EXTRACCIÓN BÁSICA ===
            product_name = ""
            product_code = ""
            product_link = ""
            
            # Nombre
            name_elem = container.select_one('div.catalog-product-details__name')
            if name_elem:
                product_name = name_elem.get_text(strip=True)
            
            if not product_name:
                name_elem = container.select_one('[data-product-name]')
                if name_elem:
                    product_name = name_elem.get('data-product-name', '')
            
            # Link y código
            link_elem = container.select_one('a[href*="/p/"]')
            if link_elem:
                href = link_elem.get('href', '')
                if href:
                    product_link = f"https://simple.ripley.cl{href}" if href.startswith('/') else href
                    if '/p/' in href:
                        code_match = re.search(r'/p/([^/?]+)', href)
                        if code_match:
                            product_code = code_match.group(1)
            
            if not product_name:
                continue
            
            # === PRECIOS BÁSICOS ===
            price_info = extract_basic_prices_rotation(container)
            
            # === ESTRUCTURA DE DATOS ===
            product_data = {
                'product_code': product_code,
                'name': product_name,
                'product_link': product_link,
                'ripley_price_text': price_info.get('ripley_price', ''),
                'card_price_text': price_info.get('card_price', ''),
                'normal_price_text': price_info.get('normal_price', ''),
                'page_scraped': page_num,
                'search_term': search_term,
                'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            products.append(product_data)
            
        except Exception as e:
            logging.warning(f"⚠️ Error producto {i}: {e}")
            continue
    
    logging.info(f"✅ '{search_term}' P{page_num}: {len(products)} productos extraídos")
    return products

def extract_basic_prices_rotation(container):
    """💰 Extracción básica de precios para rotación"""
    prices = {'ripley_price': '', 'card_price': '', 'normal_price': ''}
    
    price_pattern = re.compile(r'\$[\s]*[\d.,]+')
    price_elements = container.select('.price, [class*="price"], span')
    
    all_prices = []
    for elem in price_elements:
        text = elem.get_text(strip=True)
        if '$' in text:
            price_match = price_pattern.search(text)
            if price_match:
                all_prices.append(price_match.group(0))
    
    # Asignar precios
    if len(all_prices) >= 3:
        prices['ripley_price'] = all_prices[0]
        prices['card_price'] = all_prices[1]
        prices['normal_price'] = all_prices[2]
    elif len(all_prices) >= 2:
        prices['ripley_price'] = all_prices[0]
        prices['normal_price'] = all_prices[1]
    elif len(all_prices) == 1:
        prices['ripley_price'] = all_prices[0]
    
    return prices

def scrape_busqueda_rotation(search_key, search_info, ciclo_num, proxy_rotator):
    """🔄 Scraping con rotación de proxies por página"""
    logging.info(f"🔄 CICLO {ciclo_num} - Rotación: {search_info['name']}")
    
    all_products = []
    
    # 10 páginas por categoría - PRUEBA DE FUEGO 🔥
    max_pages = 10
    
    for page_num in range(1, max_pages + 1):
        if stop_event.is_set():
            break
        
        # === OBTENER PROXY ESPECÍFICO PARA ESTA PÁGINA ===
        proxy_config = proxy_rotator.get_next_proxy()
        
        driver = None
        try:
            # === CREAR DRIVER CON PROXY ESPECÍFICO ===
            driver = setup_rotation_driver(proxy_config)
            
            # === URL CORREGIDA CON BASE_URL ESPECÍFICA ===
            if search_key == "smartv":
                # Smart TV usa estructura especial
                if page_num == 1:
                    url = f"{search_info['base_url']}?sort=relevance_desc&page=1"
                else:
                    url = f"{search_info['base_url']}?sort=relevance_desc&page={page_num}"
            else:
                # Perfumes y smartphones usan estructura source/term
                if page_num == 1:
                    url = f"{search_info['base_url']}?source=search&term={search_info['term']}"
                else:
                    url = f"{search_info['base_url']}?source=search&term={search_info['term']}&page={page_num}"
            
            logging.info(f"📄 {search_info['name']} - Página {page_num}/10")
            logging.info(f"🔗 URL: {url}")
            
            # === CARGAR PÁGINA ===
            driver.get(url)
            
            # Espera optimizada
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.catalog-product-item, div[data-cy*="product"]'))
                )
            except TimeoutException:
                logging.warning(f"⚠️ Timeout en página {page_num}")
            
            time.sleep(2)
            
            # Scroll optimizado
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
            time.sleep(0.8)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(0.8)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # === PROCESAR PÁGINA ===
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'lxml')
            
            page_products = extract_products_rotation(soup, page_num, search_info['term'])
            
            # Metadata incluyendo info del proxy
            for product in page_products:
                product.update({
                    'search_key': search_key,
                    'search_name': search_info['name'],
                    'ciclo_number': ciclo_num,
                    'proxy_ip': proxy_config['ip'],
                    'proxy_port': proxy_config['port']
                })
            
            all_products.extend(page_products)
            
            if not page_products:
                logging.warning(f"⚠️ Sin productos en página {page_num} con proxy {proxy_config['ip']}")
            
            # Pausa entre páginas - más conservador para 10 páginas
            time.sleep(random.uniform(4.0, 8.0))
            
        except Exception as e:
            logging.error(f"❌ Error página {page_num} con proxy {proxy_config['ip']}: {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    # Guardar resultados con info de rotación
    if all_products:
        current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(output_log_dir, f"rotation_{search_key}_c{ciclo_num:03d}_{current_datetime}.json")
        
        json_data = {
            "metadata": {
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "search_term": search_info['term'],
                "search_name": search_info['name'],
                "search_key": search_key,
                "total_products": len(all_products),
                "pages_scraped": len(set(p['page_scraped'] for p in all_products)),
                "ciclo_number": ciclo_num,
                "proxy_rotation": True,
                "unique_ips_used": len(set(p['proxy_ip'] for p in all_products)),
                "scraper": "Ripley Proxy Rotation 🔄"
            },
            "products": all_products
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        logging.info(f"💾 CICLO {ciclo_num} - {search_info['name']}: {len(all_products)} productos → {filename}")
        
    return len(all_products)

def ejecutar_proxy_rotation():
    """🔄 Ejecutor principal con rotación de proxies"""
    logging.info("🔄 INICIANDO RIPLEY PROXY ROTATION")
    logging.info(f"📅 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"🔄 Pool de proxies: {len(PROXY_POOL_VALIDATED)} validados")
    logging.info(f"🔍 Búsquedas: {len(BUSQUEDAS_ROTATION)}")
    logging.info("📄 10 páginas por búsqueda - PRUEBA DE FUEGO 🔥 (proxy diferente por página)")
    logging.info("="*70)
    
    # Inicializar rotador de proxies
    proxy_rotator = ProxyRotator()
    
    ciclo_num = 1
    search_keys = list(BUSQUEDAS_ROTATION.keys())
    search_index = 0
    
    try:
        while not stop_event.is_set():
            search_key = search_keys[search_index]
            search_info = BUSQUEDAS_ROTATION[search_key]
            
            start_time = time.time()
            
            productos = scrape_busqueda_rotation(search_key, search_info, ciclo_num, proxy_rotator)
            
            execution_time = time.time() - start_time
            
            logging.info(f"⏱️ CICLO {ciclo_num} completado en {execution_time:.2f}s")
            logging.info(f"📊 Productos: {productos}")
            logging.info(f"🔄 Stats proxies: {proxy_rotator.get_usage_stats()}")
            logging.info("-" * 60)
            
            # Avanzar
            search_index = (search_index + 1) % len(search_keys)
            ciclo_num += 1
            
            # Pausa entre ciclos - más larga para 10 páginas
            if not stop_event.is_set():
                pause_time = random.uniform(60.0, 120.0)
                logging.info(f"😴 Pausa rotativa: {pause_time:.1f}s")
                time.sleep(pause_time)
    
    except KeyboardInterrupt:
        logging.info("⚠️ Detenido por usuario")
        stop_event.set()
    finally:
        logging.info("🏁 PROXY ROTATION FINALIZADO")
        logging.info(f"📊 Total ciclos: {ciclo_num - 1}")
        logging.info(f"🔄 Stats finales: {proxy_rotator.get_usage_stats()}")

if __name__ == "__main__":
    print("🔄 RIPLEY PROXY ROTATION SCRAPER")
    print(f"🌐 {len(PROXY_POOL_VALIDATED)} proxies validados")
    print(f"🔍 {len(BUSQUEDAS_ROTATION)} búsquedas configuradas")
    print("📄 10 páginas por búsqueda - PRUEBA DE FUEGO 🔥")
    print("🔄 Proxy diferente por página")
    print("Para detener: Ctrl+C")
    print("="*50)
    
    try:
        ejecutar_proxy_rotation()
    except KeyboardInterrupt:
        print("\n⚠️ Deteniendo rotación de proxies...")
        stop_event.set()