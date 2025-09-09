"""
🤫 Ripley Stealth MÍNIMO - Mejoras Anti-Detección Sutiles
Basado en el original pero con mejoras mínimas para evitar detección
Mantiene la misma estructura pero agrega protecciones específicas 🛡️
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

# Configurar encoding para Windows con soporte de emojis 🤫
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configurar logging
output_log_dir = r"D:\Scrappers Normalizacion\1.1 ML\Datos de prueba\Ripley"
os.makedirs(output_log_dir, exist_ok=True)
log_file_path = os.path.join(output_log_dir, 'ripley_stealth_minimo.log')

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

# === CONFIGURACIÓN MÍNIMA STEALTH ===
BUSQUEDAS_MINIMAS = {
    "smartphone": {
        "term": "smartphone",
        "name": "Smartphones 📱"
    },
    "smartv": {
        "term": "smart tv", 
        "name": "Smart TV 📺"
    }
}

# Configuración de proxy (MISMO DEL ORIGINAL)
PROXY_HOST = "cl.decodo.com"
PROXY_PORT = "30000"
PROXY_USER = "sprhxdrm60"
PROXY_PASS = "rdAZz6ddZf+kv71f1A"

def create_minimal_stealth_extension():
    """🤫 Extensión stealth mínima - solo lo esencial"""
    
    manifest_json = """
    {
        "version": "1.5.0",
        "manifest_version": 2,
        "name": "Minimal Stealth Extension",
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
    // Configuración básica de proxy
    var config = {{
        mode: "fixed_servers",
        rules: {{
            singleProxy: {{
                scheme: "http",
                host: "{PROXY_HOST}",
                port: parseInt({PROXY_PORT})
            }},
            bypassList: ["localhost"]
        }}
    }};

    chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

    // Autenticación simple
    chrome.webRequest.onAuthRequired.addListener(
        function(details) {{
            return {{
                authCredentials: {{
                    username: "{PROXY_USER}",
                    password: "{PROXY_PASS}"
                }}
            }};
        }},
        {{urls: ["<all_urls>"]}},
        ['blocking']
    );
    
    // Bloqueo mínimo - solo analytics obvios
    var blockedPatterns = [
        "*google-analytics.com*",
        "*googletagmanager.com*",
        "*doubleclick.net*"
    ];
    
    chrome.webRequest.onBeforeRequest.addListener(
        function(details) {{
            var url = details.url.toLowerCase();
            
            for (var i = 0; i < blockedPatterns.length; i++) {{
                var pattern = blockedPatterns[i].toLowerCase().replace(/\\*/g, '');
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
    extension_path = os.path.join(temp_dir, 'minimal_stealth_extension.zip')
    with zipfile.ZipFile(extension_path, 'w') as zip_file:
        zip_file.write(os.path.join(temp_dir, 'manifest.json'), 'manifest.json')
        zip_file.write(os.path.join(temp_dir, 'background.js'), 'background.js')
    
    return extension_path

def setup_minimal_stealth_driver():
    """🤫 Driver con stealth mínimo - basado en el original"""
    logging.info("🤫 Configurando Chrome Stealth Mínimo...")
    
    chrome_options = Options()
    
    # === CONFIGURACIÓN BÁSICA (IGUAL AL ORIGINAL) ===
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    
    # === MEJORAS MÍNIMAS ANTI-DETECCIÓN ===
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # === USER AGENT ROTATIVO MÍNIMO ===
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    # === CONFIGURACIONES DE CONTENIDO (IGUAL AL ORIGINAL) ===
    prefs = {
        "profile.default_content_setting_values": {
            "images": 2,
            "plugins": 2,
            "popups": 2,
            "geolocation": 2,
            "notifications": 2,
            "media_stream": 2,
            "media_stream_mic": 2,
            "media_stream_camera": 2,
            "protocol_handlers": 2,
            "push_messaging": 2,
            "ppapi_broker": 2,
            "automatic_downloads": 2,
            "midi_sysex": 2,
            "ssl_cert_decisions": 2,
            "metro_switch_to_desktop": 2,
            "protected_media_identifier": 2,
            "app_banner": 2,
            "site_engagement": 2,
            "durable_storage": 2
        },
        "profile.managed_default_content_settings": {
            "images": 2
        }
    }
    
    chrome_options.add_experimental_option("prefs", prefs)
    
    # === CARGAR EXTENSIÓN MÍNIMA ===
    try:
        extension_path = create_minimal_stealth_extension()
        chrome_options.add_extension(extension_path)
        logging.info("✅ Extensión stealth mínima cargada")
    except Exception as e:
        logging.warning(f"⚠️ Error cargando extensión: {e}")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # === SCRIPT ANTI-DETECCIÓN MÍNIMO ===
    minimal_stealth_script = """
    // Solo lo esencial para anti-detección
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
        'source': minimal_stealth_script
    })
    
    driver.set_page_load_timeout(20)
    driver.implicitly_wait(5)
    
    logging.info("✅ Driver stealth mínimo configurado")
    return driver

def extract_products_minimal(soup, page_num, search_term):
    """🔍 Extracción idéntica al original"""
    products = []
    
    # Buscar contenedores de productos - selectores específicos Ripley (IGUAL AL ORIGINAL)
    product_containers = soup.select('div[data-cy*="product-"]')
    
    if not product_containers:
        # Busqueda alternativa
        product_containers = soup.select('div.catalog-product-item')
    
    if not product_containers:
        # Otra alternativa
        product_containers = soup.select('a[href*="/p/"]')
    
    logging.info(f"📦 Búsqueda '{search_term}' P{page_num}: {len(product_containers)} productos")
    
    for i, container in enumerate(product_containers, 1):
        try:
            # === DATOS ESENCIALES (IGUAL AL ORIGINAL) ===
            product_name = ""
            product_code = ""
            product_link = ""
            brand = ""
            
            # Link del producto
            if container.name == 'a':
                link_elem = container
            else:
                link_elem = container.select_one('a[href*="/p/"]')
            
            if link_elem:
                href = link_elem.get('href', '')
                if href:
                    product_link = f"https://simple.ripley.cl{href}" if href.startswith('/') else href
                    # Extraer código del link (formato: /p/codigo)
                    if '/p/' in href:
                        code_match = re.search(r'/p/([^/?]+)', href)
                        if code_match:
                            product_code = code_match.group(1)
            
            # Nombre del producto - Método 1: div.catalog-product-details__name (ESPECÍFICO RIPLEY)
            name_elem = container.select_one('div.catalog-product-details__name')
            if name_elem:
                product_name = name_elem.get_text(strip=True)
            
            # Método 2: data-product-name
            if not product_name:
                name_elem = container.select_one('[data-product-name]')
                if name_elem:
                    product_name = name_elem.get('data-product-name', '')
            
            # Método 3: desde imagen alt
            if not product_name:
                img_elem = container.select_one('img')
                if img_elem:
                    alt_text = img_elem.get('alt', '')
                    if alt_text and alt_text != 'Image':
                        product_name = alt_text
            
            if not product_name:
                continue
            
            # === ESTRUCTURA DE DATOS MÍNIMA ===
            product_data = {
                'product_code': product_code,
                'name': product_name,
                'brand': brand,
                'product_link': product_link,
                'page_scraped': page_num,
                'search_term': search_term,
                'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            products.append(product_data)
            
        except Exception as e:
            logging.warning(f"⚠️ Error producto {i}: {e}")
            continue
    
    logging.info(f"✅ Búsqueda '{search_term}' P{page_num}: {len(products)} productos extraídos")
    return products

def scrape_busqueda_minimal(search_key, search_info, ciclo_num):
    """🤫 Scraping mínimo - estructura igual al original"""
    logging.info(f"🤫 CICLO {ciclo_num} - Stealth Mínimo: {search_info['name']}")
    
    driver = None
    all_products = []
    
    try:
        driver = setup_minimal_stealth_driver()
        
        # Scrapear 5 páginas (menos que el original para ser conservador)
        for page_num in range(1, 6):  # Solo 5 páginas
            if stop_event.is_set():
                logging.info("🛑 Deteniendo por señal de parada")
                break
            
            # Construir URL de búsqueda Ripley (IGUAL AL ORIGINAL)
            if page_num == 1:
                url = f"https://simple.ripley.cl/tecno/celulares?source=search&term={search_info['term']}&s=mdco&type=catalog"
            else:
                url = f"https://simple.ripley.cl/tecno/celulares?source=search&term={search_info['term']}&page={page_num}&s=mdco&type=catalog"
            
            logging.info(f"📄 {search_info['name']} - Página {page_num}/5")
            logging.info(f"🔗 URL: {url}")
            
            try:
                driver.get(url)
                
                # Esperar carga (IGUAL AL ORIGINAL)
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-cy*="product"], div.catalog-product-item, a[href*="/p/"]'))
                    )
                except TimeoutException:
                    logging.warning(f"⚠️ Timeout esperando productos en página {page_num}")
                
                time.sleep(2)
                
                # Scroll básico (SIMILAR AL ORIGINAL pero más humano)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
                time.sleep(random.uniform(0.5, 1.0))  # Delay aleatorio
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(random.uniform(0.5, 1.0))
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # Procesar (IGUAL AL ORIGINAL)
                html_content = driver.page_source
                soup = BeautifulSoup(html_content, 'lxml')
                
                page_products = extract_products_minimal(soup, page_num, search_info['term'])
                
                # Agregar metadata
                for product in page_products:
                    product['search_key'] = search_key
                    product['search_name'] = search_info['name']
                    product['ciclo_number'] = ciclo_num
                
                all_products.extend(page_products)
                
                if not page_products:
                    logging.warning(f"⚠️ Sin productos en página {page_num}")
                    if page_num > 2:
                        break
                
                # Pausa entre páginas (un poco más variable que el original)
                time.sleep(random.uniform(1.0, 3.0))
                
            except Exception as e:
                logging.error(f"❌ Error página {page_num}: {e}")
                continue
        
        # Guardar resultados (IGUAL AL ORIGINAL)
        if all_products:
            current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(output_log_dir, f"minimal_{search_key}_ciclo{ciclo_num:03d}_{current_datetime}.json")
            
            json_data = {
                "metadata": {
                    "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "search_term": search_info['term'],
                    "search_name": search_info['name'],
                    "search_key": search_key,
                    "base_url": f"https://simple.ripley.cl/tecno/celulares?source=search&term={search_info['term']}",
                    "total_products": len(all_products),
                    "pages_scraped": len(set(p['page_scraped'] for p in all_products)),
                    "ciclo_number": ciclo_num,
                    "scraper": "Ripley Stealth MÍNIMO 🤫"
                },
                "products": all_products
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"💾 CICLO {ciclo_num} - {search_info['name']}: {len(all_products)} productos → {filename}")
            
        return len(all_products)
        
    except Exception as e:
        logging.error(f"💥 Error crítico ciclo {ciclo_num}: {e}")
        return 0
    finally:
        if driver:
            driver.quit()

def ejecutar_stealth_minimo():
    """🤫 Ejecutor principal stealth mínimo"""
    logging.info("🤫 INICIANDO RIPLEY STEALTH MÍNIMO")
    logging.info(f"📅 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"🔍 Total búsquedas: {len(BUSQUEDAS_MINIMAS)}")
    logging.info("📄 Páginas por búsqueda: 5 (conservador)")
    logging.info("🤫 Cambios mínimos vs original")
    logging.info("="*60)
    
    ciclo_num = 1
    busqueda_keys = list(BUSQUEDAS_MINIMAS.keys())
    busqueda_index = 0
    
    try:
        while not stop_event.is_set():
            # Seleccionar búsqueda actual
            search_key = busqueda_keys[busqueda_index]
            search_info = BUSQUEDAS_MINIMAS[search_key]
            
            start_time = time.time()
            
            # Ejecutar scraping
            productos_extraidos = scrape_busqueda_minimal(search_key, search_info, ciclo_num)
            
            execution_time = time.time() - start_time
            
            logging.info(f"⏱️ CICLO {ciclo_num} completado en {execution_time:.2f}s")
            logging.info(f"📊 Productos extraídos: {productos_extraidos}")
            logging.info("-" * 40)
            
            # Avanzar a siguiente búsqueda
            busqueda_index = (busqueda_index + 1) % len(busqueda_keys)
            ciclo_num += 1
            
            # Pausa entre ciclos (un poco más que el original)
            if not stop_event.is_set():
                pause_time = random.uniform(10.0, 30.0)
                logging.info(f"😴 Pausa entre búsquedas: {pause_time:.1f}s")
                time.sleep(pause_time)
            
            if stop_event.is_set():
                break
    
    except KeyboardInterrupt:
        logging.info("⚠️ Recibida señal de interrupción")
        stop_event.set()
    except Exception as e:
        logging.error(f"💥 Error crítico en bucle principal: {e}")
        stop_event.set()
    finally:
        logging.info("🏁 STEALTH MÍNIMO DETENIDO")
        logging.info(f"📊 Total ciclos ejecutados: {ciclo_num - 1}")
        logging.info(f"⏰ Finalización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    print("🤫 RIPLEY STEALTH MÍNIMO")
    print(f"🔍 {len(BUSQUEDAS_MINIMAS)} búsquedas configuradas:")
    for key, info in BUSQUEDAS_MINIMAS.items():
        print(f"   • {info['name']}: '{info['term']}'")
    print("📄 5 páginas por búsqueda")
    print("🤫 Mejoras mínimas vs original")
    print("Para detener: Ctrl+C")
    print("="*40)
    
    try:
        ejecutar_stealth_minimo()
    except KeyboardInterrupt:
        print("\n⚠️ Deteniendo stealth mínimo...")
        stop_event.set()
    except Exception as e:
        print(f"\n💥 Error crítico: {e}")
        stop_event.set()