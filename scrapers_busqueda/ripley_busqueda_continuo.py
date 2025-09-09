"""
🔄 Ripley Scraper CONTINUO con BÚSQUEDAS
Sistema que ejecuta búsquedas de 20 páginas corridas sin tiempo de espera
Mantiene configuraciones especiales de proxy y anti-detección
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

# Configurar encoding para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configurar logging continuo
output_log_dir = r"D:\Scrappers Normalizacion\1.1 ML\Datos de prueba\Ripley"
os.makedirs(output_log_dir, exist_ok=True)
log_file_path = os.path.join(output_log_dir, 'ripley_busqueda_continuo.log')

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

# === CONFIGURACIÓN DE BÚSQUEDAS CONTINUAS ===
BUSQUEDAS_CONTINUAS = {
    "smartphone": {
        "term": "smartphone",
        "name": "Smartphones"
    },
    "smartv": {
        "term": "smartv", 
        "name": "Smart TV"
    },
    "tablet": {
        "term": "tablet",
        "name": "Tablets"
    }
}

# Configuración de proxy (ESPECIAL RIPLEY)
PROXY_HOST = "cl.decodo.com"
PROXY_PORT = "30000"
PROXY_USER = "sprhxdrm60"
PROXY_PASS = "rdAZz6ddZf+kv71f1A"

# Recursos a bloquear (ESPECIAL RIPLEY)
BLOCKED_PATTERNS = [
    "*google-analytics.com*",
    "*googletagmanager.com*",
    "*doubleclick.net*",
    "*googlesyndication.com*",
    "*facebook.com/tr*",
    "*hotjar.com*",
    "*segment.com*",
    "*optimizely.com*",
    "*salesforce.com*",
    "*youtube.com*",
    "*instagram.com*", 
    "*twitter.com*",
    "*pinterest.com*",
    "*tiktok.com*",
    "*.mp4*",
    "*.webm*",
    "*.mov*",
    "*.avi*",
    "*fonts.googleapis.com*",
    "*fonts.gstatic.com*",
    "*jsdelivr.net*",
    "*cdnjs.cloudflare.com*",
    "*adsystem.com*",
    "*banner*",
    "*promo*",
    "*advertising*",
]

def create_optimized_extension():
    """🔐 Extensión optimizada con proxy y bloqueos ESPECIAL RIPLEY"""
    
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Ripley Search Scraper Proxy",
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
    
    blocked_patterns_js = str(BLOCKED_PATTERNS).replace("'", '"')
    
    background_js = f"""
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

    var blockedPatterns = {blocked_patterns_js};
    
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
    extension_path = os.path.join(temp_dir, 'proxy_extension.zip')
    with zipfile.ZipFile(extension_path, 'w') as zip_file:
        zip_file.write(os.path.join(temp_dir, 'manifest.json'), 'manifest.json')
        zip_file.write(os.path.join(temp_dir, 'background.js'), 'background.js')
    
    return extension_path

def setup_driver_continuo():
    """Driver optimizado para operación continua Ripley con configuraciones especiales"""
    logging.info("🔄 Configurando Chrome para operación continua Ripley...")
    
    chrome_options = Options()
    
    # Configuración ESPECIAL RIPLEY - Modo headless con tamaño específico
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    
    # Anti-detección ESPECIAL RIPLEY
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Optimizaciones para uso continuo
    chrome_options.add_argument("--memory-pressure-off")
    chrome_options.add_argument("--aggressive-cache-discard")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    
    # Configuraciones de contenido
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
    
    # User agent rotativo ESPECIAL RIPLEY
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ]
    chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    # Cargar extensión con proxy
    try:
        extension_path = create_optimized_extension()
        chrome_options.add_extension(extension_path)
        logging.info("✅ Extensión proxy cargada")
    except Exception as e:
        logging.warning(f"⚠️ No se pudo cargar extensión proxy: {e}")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Configuraciones adicionales anti-detección
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['es-CL', 'es', 'en']});
            window.chrome = {runtime: {}};
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({
                    query: () => Promise.resolve({state: 'granted'})
                })
            });
        '''
    })
    
    driver.set_page_load_timeout(20)
    driver.implicitly_wait(5)
    
    logging.info("✅ Driver continuo Ripley configurado con protecciones especiales")
    return driver

def extract_products_continuo(soup, page_num, search_term):
    """Extracción optimizada para búsquedas en Ripley"""
    products = []
    
    # Buscar contenedores de productos - selectores específicos Ripley
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
            # === DATOS ESENCIALES ===
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
            
            # Método 4: desde URL si no hay nombre
            if not product_name and product_link:
                if '/p/' in product_link:
                    slug = product_link.split('/p/')[-1].split('?')[0]
                    product_name = slug.replace('-', ' ').title()
            
            # Buscar marca
            brand_elem = container.select_one('[data-product-brand]')
            if brand_elem:
                brand = brand_elem.get('data-product-brand', '')
            
            if not brand:
                text_content = container.get_text().upper()
                common_brands = ['SAMSUNG', 'APPLE', 'XIAOMI', 'HUAWEI', 'MOTOROLA', 'LG', 'SONY', 'HONOR', 'OPPO', 'REALME', 'NOKIA', 'ALCATEL']
                for b in common_brands:
                    if b in text_content:
                        brand = b
                        break
            
            if not product_name:
                continue
            
            # === PRECIOS OPTIMIZADOS (3 niveles Ripley) ===
            ripley_price_text = ""
            ripley_price_numeric = None
            card_price_text = ""
            card_price_numeric = None
            normal_price_text = ""
            normal_price_numeric = None
            original_price_text = ""
            original_price_numeric = None
            
            # Buscar todos los elementos con precios
            price_pattern = re.compile(r'\$[\s]*[\d.,]+')
            
            # Método 1: Buscar spans con precios específicos
            price_spans = container.select('span[class*="price"], div[class*="price"]')
            prices_found = []
            
            for elem in price_spans:
                text = elem.get_text(strip=True)
                if '$' in text:
                    # Verificar tipo de precio por clases
                    classes = ' '.join(elem.get('class', []))
                    is_old = 'old' in classes or 'previous' in classes or 'before' in classes
                    is_ripley = 'ripley' in classes.lower()
                    is_card = 'card' in classes or 'tc' in classes
                    
                    price_match = price_pattern.search(text)
                    if price_match:
                        price_text = price_match.group(0)
                        price_numeric = int(re.sub(r'[^\d]', '', price_text))
                        
                        prices_found.append({
                            'text': price_text,
                            'numeric': price_numeric,
                            'is_old': is_old,
                            'is_ripley': is_ripley,
                            'is_card': is_card
                        })
            
            # Asignar precios según tipo
            for price in prices_found:
                if price['is_old'] and not original_price_text:
                    original_price_text = price['text']
                    original_price_numeric = price['numeric']
                elif price['is_ripley'] and not ripley_price_text:
                    ripley_price_text = price['text']
                    ripley_price_numeric = price['numeric']
                elif price['is_card'] and not card_price_text:
                    card_price_text = price['text']
                    card_price_numeric = price['numeric']
                elif not normal_price_text:
                    normal_price_text = price['text']
                    normal_price_numeric = price['numeric']
            
            # Si no se encontraron precios específicos, buscar todos los precios
            if not prices_found:
                all_prices = price_pattern.findall(container.get_text())
                if len(all_prices) >= 3:
                    # 3 precios: Ripley, tarjeta, original
                    ripley_price_text = all_prices[0]
                    card_price_text = all_prices[1]
                    original_price_text = all_prices[2]
                elif len(all_prices) == 2:
                    # 2 precios: normal y original
                    normal_price_text = all_prices[0]
                    original_price_text = all_prices[1]
                elif len(all_prices) == 1:
                    # Solo precio normal
                    normal_price_text = all_prices[0]
            
            # === ESTRUCTURA DE DATOS CONTINUA ===
            product_data = {
                'product_code': product_code,
                'name': product_name,
                'brand': brand,
                'ripley_price_text': ripley_price_text,
                'ripley_price': ripley_price_numeric,
                'card_price_text': card_price_text,
                'card_price': card_price_numeric,
                'normal_price_text': normal_price_text,
                'normal_price': normal_price_numeric,
                'original_price_text': original_price_text,
                'original_price': original_price_numeric,
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

def scrape_busqueda_continuo(search_key, search_info, ciclo_num):
    """Scraping de una búsqueda Ripley en modo continuo"""
    logging.info(f"🔄 CICLO {ciclo_num} - Iniciando búsqueda: {search_info['name']}")
    
    driver = None
    all_products = []
    
    try:
        driver = setup_driver_continuo()
        
        # Scrapear 20 páginas
        for page_num in range(1, 21):  # 20 páginas fijas
            if stop_event.is_set():
                logging.info("🛑 Deteniendo por señal de parada")
                break
            
            # Construir URL de búsqueda Ripley
            if page_num == 1:
                url = f"https://simple.ripley.cl/tecno/celulares?source=search&term={search_info['term']}&s=mdco&type=catalog"
            else:
                url = f"https://simple.ripley.cl/tecno/celulares?source=search&term={search_info['term']}&page={page_num}&s=mdco&type=catalog"
            
            logging.info(f"📄 {search_info['name']} - Página {page_num}/20")
            logging.info(f"🔗 URL: {url}")
            
            try:
                driver.get(url)
                
                # Esperar carga con timeout específico Ripley
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-cy*="product"], div.catalog-product-item, a[href*="/p/"]'))
                    )
                except TimeoutException:
                    logging.warning(f"⚠️ Timeout esperando productos en página {page_num}")
                
                time.sleep(2)
                
                # Scroll progresivo ESPECIAL RIPLEY
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
                time.sleep(0.5)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(0.5)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight*3/4);")
                time.sleep(0.5)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # Procesar
                html_content = driver.page_source
                soup = BeautifulSoup(html_content, 'lxml')
                
                page_products = extract_products_continuo(soup, page_num, search_info['term'])
                
                # Agregar metadata
                for product in page_products:
                    product['search_key'] = search_key
                    product['search_name'] = search_info['name']
                    product['ciclo_number'] = ciclo_num
                
                all_products.extend(page_products)
                
                if not page_products:
                    logging.warning(f"⚠️ Sin productos en página {page_num}")
                    if page_num > 5:
                        break
                
                # Pausa corta entre páginas
                time.sleep(random.uniform(0.5, 1.5))
                
            except Exception as e:
                logging.error(f"❌ Error página {page_num}: {e}")
                continue
        
        # Guardar resultados del ciclo
        if all_products:
            current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(output_log_dir, f"busqueda_{search_key}_ciclo{ciclo_num:03d}_{current_datetime}.json")
            
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
                    "scraper": "Ripley Scraper CONTINUO con BÚSQUEDAS 🔄"
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

def ejecutar_scraping_continuo():
    """Ejecutor principal del scraping continuo Ripley con búsquedas"""
    logging.info("🔄 INICIANDO SCRAPING CONTINUO DE RIPLEY CON BÚSQUEDAS")
    logging.info(f"📅 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"🔍 Total búsquedas: {len(BUSQUEDAS_CONTINUAS)}")
    logging.info(f"📋 Términos: {', '.join([b['term'] for b in BUSQUEDAS_CONTINUAS.values()])}")
    logging.info("⏱️ Intervalo: SIN ESPERA entre búsquedas")
    logging.info("📄 Páginas por ejecución: 20")
    logging.info("🔄 Modo: Rotación continua entre búsquedas")
    logging.info("🔐 Proxy y anti-detección: ACTIVADO")
    logging.info("="*70)
    
    ciclo_num = 1
    busqueda_keys = list(BUSQUEDAS_CONTINUAS.keys())
    busqueda_index = 0
    
    try:
        while not stop_event.is_set():
            # Seleccionar búsqueda actual
            search_key = busqueda_keys[busqueda_index]
            search_info = BUSQUEDAS_CONTINUAS[search_key]
            
            start_time = time.time()
            
            # Ejecutar scraping de la búsqueda
            productos_extraidos = scrape_busqueda_continuo(search_key, search_info, ciclo_num)
            
            execution_time = time.time() - start_time
            
            logging.info(f"⏱️ CICLO {ciclo_num} completado en {execution_time:.2f}s")
            logging.info(f"📊 Productos extraídos: {productos_extraidos}")
            logging.info("-" * 50)
            
            # Avanzar a siguiente búsqueda
            busqueda_index = (busqueda_index + 1) % len(busqueda_keys)
            ciclo_num += 1
            
            # SIN ESPERA - Continuar inmediatamente con la siguiente búsqueda
            logging.info(f"➡️ Continuando inmediatamente con próxima búsqueda...")
            logging.info(f"🔄 Próxima búsqueda: {BUSQUEDAS_CONTINUAS[busqueda_keys[busqueda_index]]['name']} ('{BUSQUEDAS_CONTINUAS[busqueda_keys[busqueda_index]]['term']}')")
            
            # Solo una pausa mínima de 3 segundos entre categorías
            time.sleep(3)
            
            if stop_event.is_set():
                break
    
    except KeyboardInterrupt:
        logging.info("⚠️ Recibida señal de interrupción")
        stop_event.set()
    except Exception as e:
        logging.error(f"💥 Error crítico en bucle principal: {e}")
        stop_event.set()
    finally:
        logging.info("🏁 SCRAPING CONTINUO DETENIDO")
        logging.info(f"📊 Total ciclos ejecutados: {ciclo_num - 1}")
        logging.info(f"⏰ Finalización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    print("🔄 RIPLEY SCRAPER CONTINUO CON BÚSQUEDAS")
    print(f"🔍 {len(BUSQUEDAS_CONTINUAS)} búsquedas configuradas:")
    for key, info in BUSQUEDAS_CONTINUAS.items():
        print(f"   • {info['name']}: '{info['term']}'")
    print("⏱️ Intervalo: SIN ESPERA entre ejecuciones")
    print("📄 20 páginas por búsqueda por ciclo")
    print("🔄 Rotación automática entre búsquedas")
    print("🔐 Proxy y anti-detección: ACTIVADO")
    print()
    print("Para detener: Ctrl+C")
    print("="*50)
    
    try:
        ejecutar_scraping_continuo()
    except KeyboardInterrupt:
        print("\n⚠️ Deteniendo scraper continuo...")
        stop_event.set()
    except Exception as e:
        print(f"\n💥 Error crítico: {e}")
        stop_event.set()