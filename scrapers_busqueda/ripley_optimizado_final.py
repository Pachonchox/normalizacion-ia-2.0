"""
🏆 Ripley Scraper OPTIMIZADO FINAL
Versión definitiva basada en tests exitosos - máxima estabilidad y efectividad
Configuración anti-detección probada que funciona con Ripley 🎯
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

# Configurar encoding para Windows con soporte de emojis 🏆
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configurar logging optimizado
output_log_dir = r"D:\Scrappers Normalizacion\1.1 ML\Datos de prueba\Ripley"
os.makedirs(output_log_dir, exist_ok=True)
log_file_path = os.path.join(output_log_dir, 'ripley_optimizado_final.log')

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

# === CONFIGURACIÓN OPTIMIZADA PROBADA ===
BUSQUEDAS_OPTIMIZADAS = {
    "smartphone": {
        "term": "smartphone",
        "name": "Smartphones 📱"
    },
    "iphone": {
        "term": "iphone",
        "name": "iPhone 🍎"
    },
    "samsung": {
        "term": "samsung galaxy",
        "name": "Samsung Galaxy 📱"
    }
}

# Configuración de proxy probada
PROXY_HOST = "cl.decodo.com"
PROXY_PORT = "30000"
PROXY_USER = "sprhxdrm60"
PROXY_PASS = "rdAZz6ddZf+kv71f1A"

def create_optimized_extension():
    """🏆 Extensión optimizada probada y funcional"""
    
    manifest_json = """
    {
        "version": "2.0.0",
        "manifest_version": 2,
        "name": "Ripley Optimized Extension",
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
    // Configuración de proxy probada
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

    chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{
        console.log("Proxy optimizado configurado");
    }});

    // Autenticación probada
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
    
    // Bloqueo selectivo - solo analytics críticos
    var criticalBlocks = [
        "*google-analytics.com*",
        "*googletagmanager.com*",
        "*facebook.com/tr*"
    ];
    
    chrome.webRequest.onBeforeRequest.addListener(
        function(details) {{
            var url = details.url.toLowerCase();
            
            for (var i = 0; i < criticalBlocks.length; i++) {{
                var pattern = criticalBlocks[i].toLowerCase().replace(/\\*/g, '');
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
    extension_path = os.path.join(temp_dir, 'optimized_extension.zip')
    with zipfile.ZipFile(extension_path, 'w') as zip_file:
        zip_file.write(os.path.join(temp_dir, 'manifest.json'), 'manifest.json')
        zip_file.write(os.path.join(temp_dir, 'background.js'), 'background.js')
    
    return extension_path

def setup_optimized_driver():
    """🏆 Driver optimizado basado en configuración probada"""
    logging.info("🏆 Configurando Chrome Optimizado...")
    
    chrome_options = Options()
    
    # === CONFIGURACIÓN BASE PROBADA ===
    chrome_options.add_argument("--headless")  # Probado que funciona
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # === ANTI-DETECCIÓN MÍNIMA EFECTIVA ===
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # === USER AGENT PROBADO ===
    ua_probado = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    chrome_options.add_argument(f"--user-agent={ua_probado}")
    
    # === CONFIGURACIONES DE CONTENIDO OPTIMIZADAS ===
    prefs = {
        "profile.default_content_setting_values": {
            "images": 2,  # Bloquear imágenes (probado)
            "plugins": 2,
            "popups": 2,
            "geolocation": 2,
            "notifications": 2,
        }
    }
    
    chrome_options.add_experimental_option("prefs", prefs)
    
    # === CARGAR EXTENSIÓN OPTIMIZADA ===
    try:
        extension_path = create_optimized_extension()
        chrome_options.add_extension(extension_path)
        logging.info("✅ Extensión optimizada cargada")
    except Exception as e:
        logging.warning(f"⚠️ Error cargando extensión: {e}")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # === SCRIPT ANTI-DETECCIÓN PROBADO ===
    proven_script = """
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
        'source': proven_script
    })
    
    driver.set_page_load_timeout(15)  # Timeout reducido
    driver.implicitly_wait(3)  # Wait reducido
    
    logging.info("✅ Driver optimizado configurado")
    return driver

def extract_products_optimized(soup, page_num, search_term):
    """🎯 Extracción optimizada basada en resultados exitosos"""
    products = []
    
    # Usar selector probado que funcionó
    product_containers = soup.select('div.catalog-product-item')
    
    if not product_containers:
        # Fallback probado
        product_containers = soup.select('div[data-cy*="product-"]')
    
    logging.info(f"📦 '{search_term}' P{page_num}: {len(product_containers)} productos detectados")
    
    for i, container in enumerate(product_containers, 1):
        try:
            # === EXTRACCIÓN BÁSICA PROBADA ===
            product_name = ""
            product_code = ""
            product_link = ""
            
            # Nombre - método probado exitoso
            name_elem = container.select_one('div.catalog-product-details__name')
            if name_elem:
                product_name = name_elem.get_text(strip=True)
            
            # Fallback para nombre
            if not product_name:
                name_elem = container.select_one('[data-product-name]')
                if name_elem:
                    product_name = name_elem.get('data-product-name', '')
            
            # Link del producto
            link_elem = container.select_one('a[href*="/p/"]')
            if link_elem:
                href = link_elem.get('href', '')
                if href:
                    product_link = f"https://simple.ripley.cl{href}" if href.startswith('/') else href
                    # Extraer código
                    if '/p/' in href:
                        code_match = re.search(r'/p/([^/?]+)', href)
                        if code_match:
                            product_code = code_match.group(1)
            
            if not product_name:
                continue
            
            # === EXTRACCIÓN DE PRECIOS BÁSICA ===
            price_info = extract_basic_prices(container)
            
            # === ESTRUCTURA OPTIMIZADA ===
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

def extract_basic_prices(container):
    """💰 Extracción básica de precios"""
    prices = {'ripley_price': '', 'card_price': '', 'normal_price': ''}
    
    # Buscar precios con patrón básico
    price_pattern = re.compile(r'\$[\s]*[\d.,]+')
    
    # Buscar todos los elementos con precios
    price_elements = container.select('.price, [class*="price"], span')
    
    all_prices = []
    for elem in price_elements:
        text = elem.get_text(strip=True)
        if '$' in text:
            price_match = price_pattern.search(text)
            if price_match:
                all_prices.append(price_match.group(0))
    
    # Asignar precios encontrados
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

def scrape_busqueda_optimized(search_key, search_info, ciclo_num):
    """🏆 Scraping optimizado - configuración probada"""
    logging.info(f"🏆 CICLO {ciclo_num} - Optimizado: {search_info['name']}")
    
    driver = None
    all_products = []
    
    try:
        driver = setup_optimized_driver()
        
        # 3 páginas por categoría como solicitado
        max_pages = 3
        
        for page_num in range(1, max_pages + 1):
            if stop_event.is_set():
                break
            
            # URL corregida según indicación del usuario
            if page_num == 1:
                url = f"https://simple.ripley.cl/tecno/celulares?source=search&term={search_info['term']}&s=mdco&type=catalog"
            else:
                url = f"https://simple.ripley.cl/tecno/celulares?source=search&term={search_info['term']}&page={page_num}"
            
            logging.info(f"📄 {search_info['name']} - Página {page_num}")
            logging.info(f"🔗 URL: {url}")
            
            try:
                driver.get(url)
                
                # Espera probada
                try:
                    WebDriverWait(driver, 8).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.catalog-product-item, div[data-cy*="product"]'))
                    )
                except TimeoutException:
                    logging.warning(f"⚠️ Timeout en página {page_num}")
                
                time.sleep(2)
                
                # Scroll probado exitoso
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
                time.sleep(0.8)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(0.8)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # Procesar
                html_content = driver.page_source
                soup = BeautifulSoup(html_content, 'lxml')
                
                page_products = extract_products_optimized(soup, page_num, search_info['term'])
                
                # Metadata
                for product in page_products:
                    product.update({
                        'search_key': search_key,
                        'search_name': search_info['name'],
                        'ciclo_number': ciclo_num
                    })
                
                all_products.extend(page_products)
                
                if not page_products:
                    logging.warning(f"⚠️ Sin productos en página {page_num}")
                    # Continuar con las siguientes páginas aunque una esté vacía
                
                time.sleep(random.uniform(2.0, 4.0))
                
            except Exception as e:
                logging.error(f"❌ Error página {page_num}: {e}")
                break  # Salir al primer error para mantener estabilidad
        
        # Guardar resultados
        if all_products:
            current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(output_log_dir, f"optimized_{search_key}_c{ciclo_num:03d}_{current_datetime}.json")
            
            json_data = {
                "metadata": {
                    "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "search_term": search_info['term'],
                    "search_name": search_info['name'],
                    "search_key": search_key,
                    "total_products": len(all_products),
                    "pages_scraped": len(set(p['page_scraped'] for p in all_products)),
                    "ciclo_number": ciclo_num,
                    "scraper": "Ripley Optimizado FINAL 🏆",
                    "optimization_features": [
                        "proven_configuration", "stable_proxy", "minimal_anti_detection",
                        "conservative_paging", "error_recovery"
                    ]
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
            try:
                driver.quit()
            except:
                pass

def ejecutar_optimizado_final():
    """🏆 Ejecutor principal optimizado"""
    logging.info("🏆 INICIANDO RIPLEY SCRAPER OPTIMIZADO FINAL")
    logging.info(f"📅 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"🔍 Búsquedas: {len(BUSQUEDAS_OPTIMIZADAS)}")
    
    for key, info in BUSQUEDAS_OPTIMIZADAS.items():
        logging.info(f"   🎯 {info['name']}: '{info['term']}'")
    
    logging.info("📄 Estrategia: 1-2 páginas por búsqueda (conservador)")
    logging.info("🏆 Configuración: Probada y optimizada")
    logging.info("="*60)
    
    ciclo_num = 1
    search_keys = list(BUSQUEDAS_OPTIMIZADAS.keys())
    search_index = 0
    
    try:
        while not stop_event.is_set():
            search_key = search_keys[search_index]
            search_info = BUSQUEDAS_OPTIMIZADAS[search_key]
            
            start_time = time.time()
            
            productos = scrape_busqueda_optimized(search_key, search_info, ciclo_num)
            
            execution_time = time.time() - start_time
            
            logging.info(f"⏱️ CICLO {ciclo_num} completado en {execution_time:.2f}s")
            logging.info(f"📊 Productos: {productos}")
            logging.info("-" * 50)
            
            # Avanzar
            search_index = (search_index + 1) % len(search_keys)
            ciclo_num += 1
            
            # Pausa optimizada
            if not stop_event.is_set():
                pause_time = random.uniform(15.0, 45.0)
                logging.info(f"😴 Pausa optimizada: {pause_time:.1f}s")
                time.sleep(pause_time)
    
    except KeyboardInterrupt:
        logging.info("⚠️ Detenido por usuario")
        stop_event.set()
    finally:
        logging.info("🏁 SCRAPER OPTIMIZADO FINALIZADO")
        logging.info(f"📊 Total ciclos: {ciclo_num - 1}")

if __name__ == "__main__":
    print("🏆 RIPLEY SCRAPER OPTIMIZADO FINAL")
    print("✅ Configuración probada y funcional")
    print("🎯 Máxima estabilidad y efectividad")
    print(f"🔍 {len(BUSQUEDAS_OPTIMIZADAS)} búsquedas optimizadas")
    print("📄 1-2 páginas por búsqueda (conservador)")
    print("Para detener: Ctrl+C")
    print("="*50)
    
    try:
        ejecutar_optimizado_final()
    except KeyboardInterrupt:
        print("\n⚠️ Deteniendo scraper optimizado...")
        stop_event.set()