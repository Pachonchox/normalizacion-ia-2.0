"""
👻 Ripley Ultra-Stealth v3.0 - MÁXIMA EVASIÓN
Sistema diseñado específicamente para evadir la detección de Cloudflare/WAF de Ripley
Implementa técnicas de bypass más avanzadas y sigilosas 🥷
"""

import sys
import io
import json
import time
import re
import random
import zipfile
import tempfile
import requests
import base64
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import logging
import os
from threading import Event
import urllib.parse
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc  # NUEVO: Driver anti-detección

# Configurar encoding para Windows con soporte de emojis 👻
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configurar logging ultra-detallado
output_log_dir = r"D:\Scrappers Normalizacion\1.1 ML\Datos de prueba\Ripley"
os.makedirs(output_log_dir, exist_ok=True)
log_file_path = os.path.join(output_log_dir, 'ripley_ultra_stealth_v3.log')

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

# === CONFIGURACIÓN ULTRA-STEALTH ===
ULTRA_BUSQUEDAS = {
    "smartphone": {
        "terms": ["celular samsung", "iphone", "android", "movil"],
        "name": "Smartphones 📱"
    },
    "smart_tv": {
        "terms": ["smart tv 55", "television samsung", "tv led"],  
        "name": "Smart TV 📺"
    }
}

# Proxies con más opciones de fallback
ULTRA_PROXY_POOL = [
    {
        "host": "cl.decodo.com",
        "port": "30000",
        "user": "sprhxdrm60", 
        "pass": "rdAZz6ddZf+kv71f1A",
        "country": "CL"
    }
]

# User agents ultra-realistas con datos de browsing reales
ULTRA_REALISTIC_UA = [
    {
        "agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept_lang": "es-CL,es;q=0.9,en;q=0.8",
        "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "platform": "Windows"
    },
    {
        "agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept_lang": "es-ES,es;q=0.9,en;q=0.8",
        "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "platform": "macOS"
    }
]

def create_cloudflare_bypass_extension(proxy_config):
    """🛡️ Extensión específica para bypass de Cloudflare/WAF"""
    
    manifest_json = """
    {
        "version": "3.0.0",
        "manifest_version": 2,
        "name": "Cloudflare Bypass Extension",
        "permissions": [
            "proxy",
            "webRequest", 
            "webRequestBlocking",
            "storage",
            "tabs",
            "<all_urls>"
        ],
        "background": {
            "scripts": ["background.js"],
            "persistent": true
        },
        "content_scripts": [{
            "matches": ["<all_urls>"],
            "js": ["content.js"],
            "run_at": "document_start"
        }]
    }
    """
    
    background_js = f"""
    // Configuración de proxy con autenticación
    var config = {{
        mode: "fixed_servers",
        rules: {{
            singleProxy: {{
                scheme: "http",
                host: "{proxy_config['host']}",
                port: parseInt({proxy_config['port']})
            }},
            bypassList: ["localhost", "127.0.0.1", "*.local"]
        }}
    }};

    chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{
        console.log("Proxy configurado para Cloudflare bypass");
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

    // Modificar headers para bypass de Cloudflare
    chrome.webRequest.onBeforeSendHeaders.addListener(
        function(details) {{
            var headers = details.requestHeaders;
            
            // Headers específicos para evadir WAF
            var newHeaders = [
                {{name: "Cache-Control", value: "max-age=0"}},
                {{name: "Sec-Fetch-Dest", value: "document"}},
                {{name: "Sec-Fetch-Mode", value: "navigate"}},
                {{name: "Sec-Fetch-Site", value: "none"}},
                {{name: "Sec-Fetch-User", value: "?1"}},
                {{name: "Upgrade-Insecure-Requests", value: "1"}},
                {{name: "X-Forwarded-For", value: "{random.choice(['190.95.22.36', '181.200.55.78', '200.123.45.67'])}"}},
                {{name: "X-Real-IP", value: "{random.choice(['190.95.22.36', '181.200.55.78'])}"}},
                {{name: "CF-Connecting-IP", value: "190.95.22.36"}},
                {{name: "CF-IPCountry", value: "CL"}},
                {{name: "Accept-CH", value: "Sec-CH-UA, Sec-CH-UA-Mobile, Sec-CH-UA-Platform"}},
                {{name: "Purpose", value: "prefetch"}}
            ];
            
            // Remover headers sospechosos
            headers = headers.filter(function(header) {{
                var name = header.name.toLowerCase();
                return !name.includes('automation') && 
                       !name.includes('webdriver') &&
                       !name.includes('selenium') &&
                       !name.includes('bot');
            }});
            
            // Agregar headers nuevos
            for (var i = 0; i < newHeaders.length; i++) {{
                var exists = false;
                for (var j = 0; j < headers.length; j++) {{
                    if (headers[j].name.toLowerCase() === newHeaders[i].name.toLowerCase()) {{
                        headers[j].value = newHeaders[i].value;
                        exists = true;
                        break;
                    }}
                }}
                if (!exists) {{
                    headers.push(newHeaders[i]);
                }}
            }}
            
            return {{requestHeaders: headers}};
        }},
        {{urls: ["*://*.ripley.cl/*"]}},
        ["blocking", "requestHeaders"]
    );
    
    // Bloquear recursos pesados para mayor velocidad
    var blockedTypes = ['image', 'stylesheet', 'font', 'media'];
    chrome.webRequest.onBeforeRequest.addListener(
        function(details) {{
            if (Math.random() > 0.7 && blockedTypes.includes(details.type)) {{
                return {{cancel: true}};
            }}
            return {{cancel: false}};
        }},
        {{urls: ["<all_urls>"]}},
        ["blocking"]
    );
    """
    
    content_js = """
    // Script que se ejecuta en cada página para máximo stealth
    (function() {
        'use strict';
        
        // Eliminar todas las trazas de automatización
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
            configurable: true
        });
        
        // Sobrescribir propiedades detectables
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
                {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                {name: 'Native Client', filename: 'internal-nacl-plugin'}
            ]
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['es-CL', 'es', 'en-US', 'en']
        });
        
        // Ocultar Chrome automation
        if (window.chrome) {
            Object.defineProperty(window, 'chrome', {
                get: () => ({
                    runtime: {
                        onConnect: undefined,
                        onMessage: undefined,
                        connect: function() {
                            return {
                                postMessage: function() {},
                                onMessage: {addListener: function() {}}
                            };
                        }
                    }
                })
            });
        }
        
        // Interceptar detecciones de canvas fingerprinting
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {
            // Agregar ruido aleatorio
            if (type === 'image/png') {
                const canvas = this;
                const ctx = canvas.getContext('2d');
                if (ctx) {
                    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] += Math.floor(Math.random() * 3) - 1;
                        imageData.data[i+1] += Math.floor(Math.random() * 3) - 1;  
                        imageData.data[i+2] += Math.floor(Math.random() * 3) - 1;
                    }
                    ctx.putImageData(imageData, 0, 0);
                }
            }
            return originalToDataURL.call(this, type);
        };
        
        // Interceptar WebGL fingerprinting
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Google Inc. (Intel)';
            }
            if (parameter === 37446) {
                return 'ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)';
            }
            return getParameter.call(this, parameter);
        };
        
        // Ocultar propiedades de automatización adicionales
        delete Object.getPrototypeOf(navigator).webdriver;
        
        // Simular interacciones humanas
        document.addEventListener('DOMContentLoaded', function() {
            // Simular movimiento de mouse
            setTimeout(() => {
                const event = new MouseEvent('mousemove', {
                    bubbles: true,
                    cancelable: true,
                    clientX: Math.random() * window.innerWidth,
                    clientY: Math.random() * window.innerHeight
                });
                document.body.dispatchEvent(event);
            }, Math.random() * 2000 + 1000);
        });
        
        console.log('Cloudflare bypass content script loaded');
    })();
    """
    
    # Crear directorio temporal
    temp_dir = tempfile.mkdtemp()
    
    # Guardar archivos
    with open(os.path.join(temp_dir, 'manifest.json'), 'w') as f:
        f.write(manifest_json)
    
    with open(os.path.join(temp_dir, 'background.js'), 'w') as f:
        f.write(background_js)
        
    with open(os.path.join(temp_dir, 'content.js'), 'w') as f:
        f.write(content_js)
    
    # Crear ZIP
    extension_path = os.path.join(temp_dir, 'cloudflare_bypass_extension.zip')
    with zipfile.ZipFile(extension_path, 'w') as zip_file:
        zip_file.write(os.path.join(temp_dir, 'manifest.json'), 'manifest.json')
        zip_file.write(os.path.join(temp_dir, 'background.js'), 'background.js')
        zip_file.write(os.path.join(temp_dir, 'content.js'), 'content.js')
    
    return extension_path

def setup_undetected_driver():
    """👻 Driver ultra-stealth usando undetected-chromedriver"""
    logging.info("👻 Configurando Undetected Chrome Ultra-Stealth...")
    
    proxy_config = random.choice(ULTRA_PROXY_POOL)
    ua_config = random.choice(ULTRA_REALISTIC_UA)
    
    logging.info(f"🌐 Proxy: {proxy_config['host']} ({proxy_config['country']})")
    logging.info(f"🎭 Platform: {ua_config['platform']}")
    
    # Configurar opciones para undetected-chromedriver
    options = uc.ChromeOptions()
    
    # === CONFIGURACIÓN BÁSICA ===
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1366,768")  # Tamaño típico
    
    # === ANTI-DETECCIÓN MEJORADA ===
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-extensions-http-throttling")
    options.add_argument("--disable-client-side-phishing-detection")
    
    # === CONFIGURACIÓN DE CONTENIDO ===
    prefs = {
        "profile.default_content_setting_values": {
            "images": 2,  # Bloquear imágenes para mayor velocidad
            "plugins": 2,
            "popups": 2,
            "geolocation": 2,
            "notifications": 2,
        },
        "profile.managed_default_content_settings": {
            "images": 2
        }
    }
    options.add_experimental_option("prefs", prefs)
    
    # === USER AGENT ===
    options.add_argument(f"--user-agent={ua_config['agent']}")
    
    # === PROXY CONFIGURATION ===
    proxy_url = f"http://{proxy_config['user']}:{proxy_config['pass']}@{proxy_config['host']}:{proxy_config['port']}"
    options.add_argument(f"--proxy-server={proxy_url}")
    
    try:
        # Usar undetected-chromedriver
        driver = uc.Chrome(
            options=options,
            version_main=None,  # Detectar automáticamente la versión
            driver_executable_path=None  # Descargar automáticamente
        )
        
        logging.info("✅ Undetected Chrome iniciado exitosamente")
        
    except Exception as e:
        logging.error(f"❌ Error con undetected-chromedriver: {e}")
        logging.info("🔄 Fallback a Chrome normal...")
        
        # Fallback a Chrome normal
        chrome_options = Options()
        for arg in options.arguments:
            chrome_options.add_argument(arg)
        for name, value in options.experimental_options.items():
            chrome_options.add_experimental_option(name, value)
            
        driver = webdriver.Chrome(options=chrome_options)
    
    # === SCRIPTS ANTI-DETECCIÓN POST-INICIALIZACIÓN ===
    ultra_stealth_script = """
    // Ultra-stealth script
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
            {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
            {name: 'Native Client', filename: 'internal-nacl-plugin'}
        ]
    });
    Object.defineProperty(navigator, 'languages', {get: () => ['es-CL', 'es', 'en']});
    
    // Eliminar propiedades de detección
    delete Object.getPrototypeOf(navigator).webdriver;
    
    // Ocultar Chrome automation
    window.chrome = {runtime: {}};
    
    // Configurar viewport
    Object.defineProperty(screen, 'width', {get: () => 1366});
    Object.defineProperty(screen, 'height', {get: () => 768});
    """
    
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': ultra_stealth_script
    })
    
    # === CONFIGURACIONES FINALES ===
    driver.set_page_load_timeout(45)  # Timeout más largo para manejar Cloudflare
    driver.implicitly_wait(10)
    
    logging.info("✅ Driver ultra-stealth configurado completamente")
    return driver, proxy_config, ua_config

def human_delay_pattern():
    """⏰ Patrones de delay ultra-humanos"""
    patterns = [
        # Patrón navegación normal
        lambda: random.uniform(2.0, 8.0),
        # Patrón lectura detenida
        lambda: random.uniform(5.0, 15.0),
        # Patrón navegación rápida
        lambda: random.uniform(0.8, 3.0),
        # Patrón pausa larga (como si el usuario se hubiera ido)
        lambda: random.uniform(20.0, 45.0) if random.random() > 0.9 else random.uniform(3.0, 8.0)
    ]
    
    return random.choice(patterns)()

def cloudflare_safe_get(driver, url, max_retries=3):
    """🛡️ Carga segura de página con bypass de Cloudflare"""
    for attempt in range(max_retries):
        try:
            logging.info(f"🔗 Intento {attempt + 1}/{max_retries}: {url}")
            
            driver.get(url)
            
            # Esperar un poco para que Cloudflare procese
            time.sleep(random.uniform(3.0, 8.0))
            
            # Verificar si fuimos bloqueados
            page_source = driver.page_source.lower()
            
            blocked_indicators = [
                "cloudflare", "security check", "attention required",
                "alto, no puedes acceder", "challenge", "blocked",
                "verificando que eres humano", "just a moment"
            ]
            
            is_blocked = any(indicator in page_source for indicator in blocked_indicators)
            
            if is_blocked:
                logging.warning(f"⚠️ Posible bloqueo detectado en intento {attempt + 1}")
                if attempt < max_retries - 1:
                    # Esperar más tiempo y cambiar comportamiento
                    wait_time = random.uniform(15.0, 30.0) * (attempt + 1)
                    logging.info(f"⏳ Esperando {wait_time:.1f}s antes del siguiente intento...")
                    time.sleep(wait_time)
                    continue
                else:
                    return False, "blocked"
            else:
                logging.info("✅ Página cargada exitosamente")
                return True, "success"
                
        except TimeoutException:
            logging.warning(f"⚠️ Timeout en intento {attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep(random.uniform(5.0, 15.0))
                continue
        except Exception as e:
            logging.error(f"❌ Error en intento {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(random.uniform(10.0, 20.0))
                continue
    
    return False, "failed"

def scrape_ultra_stealth_search(search_key, search_info, ciclo_num):
    """👻 Scraping ultra-stealth con bypass completo"""
    logging.info(f"👻 CICLO {ciclo_num} - Ultra-Stealth: {search_info['name']}")
    
    driver = None
    all_products = []
    
    try:
        driver, proxy_config, ua_config = setup_undetected_driver()
        
        # Seleccionar término aleatorio
        selected_term = random.choice(search_info['terms'])
        logging.info(f"🔍 Término: '{selected_term}'")
        
        # Intentar solo 3-5 páginas para ser más conservador
        max_pages = random.randint(3, 5)
        
        for page_num in range(1, max_pages + 1):
            if stop_event.is_set():
                break
            
            # Construir URL correcta de Ripley (igual al original)
            if page_num == 1:
                url = f"https://simple.ripley.cl/tecno/celulares?source=search&term={selected_term}&s=mdco&type=catalog"
            else:
                url = f"https://simple.ripley.cl/tecno/celulares?source=search&term={selected_term}&page={page_num}&s=mdco&type=catalog"
            
            # Delay humano antes de cargar
            delay = human_delay_pattern()
            logging.info(f"⏳ Pausa humana: {delay:.1f}s")
            time.sleep(delay)
            
            # Intento de carga con bypass de Cloudflare
            success, status = cloudflare_safe_get(driver, url)
            
            if not success:
                logging.error(f"❌ No se pudo cargar página {page_num}: {status}")
                if status == "blocked":
                    logging.error("🚨 BLOQUEADO POR CLOUDFLARE - Deteniendo")
                    break
                continue
            
            # Simular comportamiento humano post-carga
            time.sleep(random.uniform(2.0, 5.0))
            
            # Scroll muy humano
            scroll_steps = random.randint(3, 8)
            for step in range(scroll_steps):
                scroll_amount = random.randint(200, 600)
                driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(0.3, 1.2))
            
            # Procesar página
            try:
                html_content = driver.page_source
                soup = BeautifulSoup(html_content, 'lxml')
                
                # Buscar productos con selectores conservadores
                products = extract_products_ultra_safe(soup, page_num, selected_term)
                
                for product in products:
                    product.update({
                        'search_key': search_key,
                        'search_name': search_info['name'],
                        'ciclo_number': ciclo_num,
                        'proxy_country': proxy_config['country'],
                        'platform': ua_config['platform'],
                        'selected_term': selected_term
                    })
                
                all_products.extend(products)
                
                logging.info(f"📦 P{page_num}: {len(products)} productos extraídos")
                
                if not products and page_num > 2:
                    logging.info("🛑 Sin productos, finalizando búsqueda")
                    break
                    
            except Exception as e:
                logging.error(f"❌ Error procesando página {page_num}: {e}")
                continue
        
        # Guardar resultados
        if all_products:
            current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(
                output_log_dir, 
                f"ultra_{search_key}_c{ciclo_num:03d}_{current_datetime}.json"
            )
            
            json_data = {
                "metadata": {
                    "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "search_term": selected_term,
                    "search_name": search_info['name'],
                    "search_key": search_key,
                    "total_products": len(all_products),
                    "pages_scraped": len(set(p['page_scraped'] for p in all_products)),
                    "ciclo_number": ciclo_num,
                    "proxy_config": proxy_config,
                    "platform": ua_config['platform'],
                    "scraper": "Ripley Ultra-Stealth v3.0 👻",
                    "ultra_features": [
                        "undetected_chromedriver", "cloudflare_bypass", "ultra_human_behavior",
                        "advanced_fingerprinting_evasion", "conservative_scraping"
                    ]
                },
                "products": all_products
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"💾 CICLO {ciclo_num} - Ultra Complete: {len(all_products)} productos → {filename}")
        
        return len(all_products)
        
    except Exception as e:
        logging.error(f"💥 Error crítico ultra-stealth ciclo {ciclo_num}: {e}")
        return 0
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def extract_products_ultra_safe(soup, page_num, search_term):
    """🔍 Extracción ultra-segura y conservadora"""
    products = []
    
    # Selectores muy conservadores
    selectors = [
        'div.catalog-product-item',
        'div[data-testid*="product"]',
        'article',
        '.product'
    ]
    
    containers = []
    for selector in selectors:
        found = soup.select(selector)
        if found:
            containers = found
            logging.info(f"🎯 Selector exitoso: {selector} ({len(found)} elementos)")
            break
    
    for i, container in enumerate(containers[:20], 1):  # Máximo 20 productos
        try:
            product_name = ""
            product_link = ""
            price = ""
            
            # Nombre (muy conservador)
            name_selectors = ['h3', 'h4', '.name', '[data-testid*="name"]']
            for sel in name_selectors:
                elem = container.select_one(sel)
                if elem:
                    product_name = elem.get_text(strip=True)
                    if product_name:
                        break
            
            # Link
            link_elem = container.select_one('a[href]')
            if link_elem:
                href = link_elem.get('href', '')
                if href:
                    product_link = f"https://simple.ripley.cl{href}" if href.startswith('/') else href
            
            # Precio básico
            price_elem = container.select_one('.price, [class*="price"]')
            if price_elem:
                price = price_elem.get_text(strip=True)
            
            if product_name:
                products.append({
                    'name': product_name,
                    'link': product_link,
                    'price': price,
                    'page_scraped': page_num,
                    'search_term': search_term,
                    'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
        except Exception as e:
            logging.warning(f"⚠️ Error producto {i}: {e}")
            continue
    
    return products

def ejecutar_ultra_stealth():
    """👻 Ejecutor principal ultra-stealth"""
    logging.info("👻 INICIANDO RIPLEY ULTRA-STEALTH v3.0")
    logging.info(f"📅 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("🛡️ Características: Undetected ChromeDriver + Cloudflare Bypass")
    logging.info("⏰ Modo: Ultra-Conservador (3-5 páginas por búsqueda)")
    logging.info("="*70)
    
    ciclo_num = 1
    search_keys = list(ULTRA_BUSQUEDAS.keys())
    search_index = 0
    
    try:
        while not stop_event.is_set():
            search_key = search_keys[search_index]
            search_info = ULTRA_BUSQUEDAS[search_key]
            
            start_time = time.time()
            
            productos = scrape_ultra_stealth_search(search_key, search_info, ciclo_num)
            
            execution_time = time.time() - start_time
            
            logging.info(f"⏱️ CICLO {ciclo_num} completado en {execution_time:.2f}s")
            logging.info(f"📊 Productos: {productos}")
            logging.info("-" * 50)
            
            # Avanzar
            search_index = (search_index + 1) % len(search_keys)
            ciclo_num += 1
            
            # Pausa ultra-larga entre búsquedas para máximo stealth
            if not stop_event.is_set():
                inter_cycle_delay = random.uniform(60.0, 180.0)  # 1-3 minutos
                logging.info(f"😴 Pausa ultra-stealth: {inter_cycle_delay:.1f}s")
                time.sleep(inter_cycle_delay)
    
    except KeyboardInterrupt:
        logging.info("⚠️ Detenido por usuario")
        stop_event.set()
    finally:
        logging.info("🏁 ULTRA-STEALTH FINALIZADO")

if __name__ == "__main__":
    print("👻 RIPLEY ULTRA-STEALTH v3.0")
    print("🛡️ Máxima evasión de Cloudflare/WAF")
    print("⏰ Modo conservador: 3-5 páginas por búsqueda")
    print("😴 Delays: 1-3 minutos entre búsquedas")
    print("🥷 Undetected ChromeDriver + Bypass avanzado")
    print("Para detener: Ctrl+C")
    print("="*50)
    
    try:
        ejecutar_ultra_stealth()
    except KeyboardInterrupt:
        print("\n⚠️ Deteniendo ultra-stealth...")
        stop_event.set()