"""
🥷 Ripley Scraper STEALTH v2.0 - Anti-Detección Avanzada
Sistema ultra-furtivo con rotación de proxies, fingerprints aleatorios y comportamiento humano simulado
Configuraciones especiales para evadir todas las detecciones de automatización 🛡️
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

# Configurar encoding para Windows con soporte de emojis 🚀
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configurar logging continuo
output_log_dir = r"D:\Scrappers Normalizacion\1.1 ML\Datos de prueba\Ripley"
os.makedirs(output_log_dir, exist_ok=True)
log_file_path = os.path.join(output_log_dir, 'ripley_stealth_v2.log')

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

# === CONFIGURACIÓN DE BÚSQUEDAS STEALTH ===
BUSQUEDAS_STEALTH = {
    "smartphone": {
        "term": "smartphone",
        "name": "Smartphones 📱",
        "variations": ["celular", "movil", "telefono"]
    },
    "smartv": {
        "term": "smart tv", 
        "name": "Smart TV 📺",
        "variations": ["television", "tv", "smart-tv"]
    },
    "tablet": {
        "term": "tablet",
        "name": "Tablets 💻",
        "variations": ["ipad", "tableta", "tablet-pc"]
    },
    "notebook": {
        "term": "notebook",
        "name": "Notebooks 💻", 
        "variations": ["laptop", "computador", "portatil"]
    }
}

# Pool de proxies rotativos (agregar más proxies reales aquí)
PROXY_POOL = [
    {
        "host": "cl.decodo.com",
        "port": "30000", 
        "user": "sprhxdrm60",
        "pass": "rdAZz6ddZf+kv71f1A",
        "country": "CL"
    },
    # Agregar más proxies aquí para rotación
    # {
    #     "host": "proxy2.example.com",
    #     "port": "8080",
    #     "user": "user2", 
    #     "pass": "pass2",
    #     "country": "AR"
    # }
]

# User agents ultra-realistas con fingerprints específicos
STEALTH_USER_AGENTS = [
    {
        "agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "platform": "Windows",
        "webgl_vendor": "Google Inc. (Intel)",
        "webgl_renderer": "ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "screen": {"width": 1920, "height": 1080}
    },
    {
        "agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "platform": "MacIntel", 
        "webgl_vendor": "Apple",
        "webgl_renderer": "Apple GPU",
        "screen": {"width": 2560, "height": 1600}
    },
    {
        "agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "platform": "Linux x86_64",
        "webgl_vendor": "Mesa",
        "webgl_renderer": "Mesa DRI Intel(R) Iris(R) Xe Graphics",
        "screen": {"width": 1366, "height": 768}
    },
    {
        "agent": "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "platform": "Windows",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "screen": {"width": 2560, "height": 1440}
    }
]

# Headers dinámicos ultra-realistas
def get_dynamic_headers(user_agent_data):
    """Genera headers dinámicos basados en el user agent 🎭"""
    base_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': random.choice(['es-CL,es;q=0.9,en;q=0.8', 'es-ES,es;q=0.9,en;q=0.8', 'es-MX,es;q=0.9,en;q=0.8']),
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate', 
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': random.choice(['max-age=0', 'no-cache', 'must-revalidate']),
        'User-Agent': user_agent_data['agent']
    }
    
    # Headers específicos según plataforma
    if 'Windows' in user_agent_data['platform']:
        base_headers['Sec-Ch-Ua'] = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
        base_headers['Sec-Ch-Ua-Mobile'] = '?0'
        base_headers['Sec-Ch-Ua-Platform'] = '"Windows"'
    elif 'Mac' in user_agent_data['platform']:
        base_headers['Sec-Ch-Ua'] = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
        base_headers['Sec-Ch-Ua-Mobile'] = '?0'
        base_headers['Sec-Ch-Ua-Platform'] = '"macOS"'
    
    return base_headers

def create_ultra_stealth_extension(proxy_config):
    """🛡️ Extensión ultra-stealth con proxy + bloqueos avanzados + anti-detección"""
    
    manifest_json = """
    {
        "version": "2.0.0",
        "manifest_version": 2,
        "name": "Ultra Stealth Proxy Extension",
        "permissions": [
            "proxy",
            "webRequest", 
            "webRequestBlocking",
            "storage",
            "<all_urls>"
        ],
        "background": {
            "scripts": ["background.js"],
            "persistent": true
        }
    }
    """
    
    # Patrones de bloqueo ultra-agresivos
    blocked_patterns_js = json.dumps([
        "*google-analytics.com*", "*googletagmanager.com*", "*doubleclick.net*",
        "*googlesyndication.com*", "*facebook.com/tr*", "*hotjar.com*",
        "*segment.com*", "*optimizely.com*", "*salesforce.com*",
        "*youtube.com*", "*instagram.com*", "*twitter.com*", "*pinterest.com*",
        "*tiktok.com*", "*.mp4*", "*.webm*", "*.mov*", "*.avi*",
        "*fonts.googleapis.com*", "*fonts.gstatic.com*", "*jsdelivr.net*",
        "*cdnjs.cloudflare.com*", "*adsystem.com*", "*banner*", "*promo*",
        "*advertising*", "*ads.*", "*analytics.*", "*tracking.*", "*metrics.*",
        "*telemetry.*", "*crash*", "*error*", "*report*", "*beacon*",
        "*pixel*", "*tag*", "*gtm*", "*fbpx*", "*intercom*", "*zendesk*",
        "*livechat*", "*drift*", "*calendly*", "*typeform*"
    ])
    
    background_js = f"""
    // Configuración de proxy con failover
    var proxyConfigs = [
        {{
            scheme: "http",
            host: "{proxy_config['host']}",
            port: parseInt({proxy_config['port']})
        }}
    ];
    
    var currentProxyIndex = 0;
    
    function setProxy(index) {{
        var config = {{
            mode: "fixed_servers",
            rules: {{
                singleProxy: proxyConfigs[index],
                bypassList: ["localhost", "127.0.0.1", "*.local"]
            }}
        }};
        
        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{
            console.log("Proxy configurado:", proxyConfigs[index]);
        }});
    }}
    
    // Establecer proxy inicial
    setProxy(currentProxyIndex);
    
    // Autenticación de proxy con retry
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
    
    // Bloqueo ultra-agresivo de recursos
    var blockedPatterns = {blocked_patterns_js};
    
    chrome.webRequest.onBeforeRequest.addListener(
        function(details) {{
            var url = details.url.toLowerCase();
            var shouldBlock = false;
            
            // Verificar patrones de bloqueo
            for (var i = 0; i < blockedPatterns.length; i++) {{
                var pattern = blockedPatterns[i].toLowerCase().replace(/\\*/g, '');
                if (url.includes(pattern)) {{
                    shouldBlock = true;
                    break;
                }}
            }}
            
            // Bloquear recursos pesados
            var resourceTypes = ['image', 'media', 'font', 'stylesheet'];
            if (resourceTypes.includes(details.type) && Math.random() > 0.7) {{
                shouldBlock = true;
            }}
            
            if (shouldBlock) {{
                console.log("Blocked:", url);
                return {{cancel: true}};
            }}
            
            return {{cancel: false}};
        }},
        {{urls: ["<all_urls>"]}},
        ["blocking"]
    );
    
    // Modificar headers para mayor stealth
    chrome.webRequest.onBeforeSendHeaders.addListener(
        function(details) {{
            var headers = details.requestHeaders;
            
            // Remover headers sospechosos
            headers = headers.filter(function(header) {{
                var name = header.name.toLowerCase();
                return !name.includes('automation') && 
                       !name.includes('webdriver') &&
                       !name.includes('selenium');
            }});
            
            // Agregar variación aleatoria a Accept-Language
            var acceptLangOptions = [
                'es-CL,es;q=0.9,en;q=0.8',
                'es-ES,es;q=0.9,en;q=0.8', 
                'es-MX,es;q=0.9,en;q=0.8'
            ];
            
            for (var i = 0; i < headers.length; i++) {{
                if (headers[i].name.toLowerCase() === 'accept-language') {{
                    headers[i].value = acceptLangOptions[Math.floor(Math.random() * acceptLangOptions.length)];
                    break;
                }}
            }}
            
            return {{requestHeaders: headers}};
        }},
        {{urls: ["<all_urls>"]}},
        ["blocking", "requestHeaders"]
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
    extension_path = os.path.join(temp_dir, 'ultra_stealth_extension.zip')
    with zipfile.ZipFile(extension_path, 'w') as zip_file:
        zip_file.write(os.path.join(temp_dir, 'manifest.json'), 'manifest.json')
        zip_file.write(os.path.join(temp_dir, 'background.js'), 'background.js')
    
    return extension_path

def get_random_proxy():
    """Selecciona un proxy aleatorio del pool 🎲"""
    return random.choice(PROXY_POOL)

def get_random_user_agent():
    """Selecciona un user agent aleatorio con fingerprints 🎭"""
    return random.choice(STEALTH_USER_AGENTS)

def setup_ultra_stealth_driver():
    """🥷 Driver ultra-stealth con todas las evasiones avanzadas"""
    logging.info("🥷 Configurando Chrome Ultra-Stealth...")
    
    # Seleccionar configuraciones aleatorias
    proxy_config = get_random_proxy()
    ua_config = get_random_user_agent()
    
    logging.info(f"🌐 Proxy seleccionado: {proxy_config['host']} ({proxy_config['country']})")
    logging.info(f"🎭 User Agent: {ua_config['platform']}")
    
    chrome_options = Options()
    
    # === CONFIGURACIÓN STEALTH BÁSICA ===
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    
    # === ANTI-DETECCIÓN AVANZADA ===
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # === CONFIGURACIÓN DE PANTALLA DINÁMICA ===
    screen_config = ua_config['screen']
    chrome_options.add_argument(f"--window-size={screen_config['width']},{screen_config['height']}")
    
    # === CONFIGURACIÓN HEADLESS AVANZADA ===
    if random.choice([True, False]):  # 50% headless
        chrome_options.add_argument("--headless=new")  # Nuevo headless más stealth
        logging.info("🔒 Modo: Headless Stealth")
    else:
        chrome_options.add_argument("--start-maximized")
        logging.info("🖥️ Modo: Visible")
    
    # === USER AGENT DINÁMICO ===
    chrome_options.add_argument(f"--user-agent={ua_config['agent']}")
    
    # === CONFIGURACIONES DE RENDIMIENTO ===
    chrome_options.add_argument("--memory-pressure-off")
    chrome_options.add_argument("--aggressive-cache-discard")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    
    # === CONFIGURACIONES ULTRA-STEALTH ===
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-extensions-http-throttling")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-login-animations") 
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-permissions-api")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-prompt-on-repost")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--disable-translate")
    
    # === PREFERENCIAS AVANZADAS ===
    prefs = {
        "profile.default_content_setting_values": {
            "images": random.choice([1, 2]),  # Randomizar carga de imágenes
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
            "images": random.choice([1, 2])
        },
        "profile.content_settings.exceptions.automatic_downloads.*.setting": 2,
        "profile.default_content_settings.popups": 0,
        "managed_default_content_settings.images": 2
    }
    
    chrome_options.add_experimental_option("prefs", prefs)
    
    # === CARGAR EXTENSIÓN ULTRA-STEALTH ===
    try:
        extension_path = create_ultra_stealth_extension(proxy_config)
        chrome_options.add_extension(extension_path)
        logging.info("✅ Extensión ultra-stealth cargada")
    except Exception as e:
        logging.warning(f"⚠️ Error cargando extensión: {e}")
    
    # === INICIALIZAR DRIVER ===
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except WebDriverException as e:
        logging.error(f"❌ Error iniciando Chrome: {e}")
        raise
    
    # === SCRIPTS ULTRA-STEALTH POST-INICIALIZACIÓN ===
    stealth_script = f"""
    // Eliminar todas las trazas de webdriver
    Object.defineProperty(navigator, 'webdriver', {{
        get: () => undefined,
        configurable: true
    }});
    
    // Sobrescribir propiedades del navigator
    Object.defineProperty(navigator, 'plugins', {{
        get: () => [
            {{name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'}},
            {{name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: 'Portable Document Format'}},
            {{name: 'Native Client', filename: 'internal-nacl-plugin', description: 'Native Client Executable'}}
        ]
    }});
    
    Object.defineProperty(navigator, 'languages', {{
        get: () => ['es-CL', 'es', 'en-US', 'en']
    }});
    
    Object.defineProperty(navigator, 'platform', {{
        get: () => '{ua_config["platform"]}'
    }});
    
    // WebGL fingerprinting evasion
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
        if (parameter === 37445) {{
            return '{ua_config["webgl_vendor"]}';
        }}
        if (parameter === 37446) {{
            return '{ua_config["webgl_renderer"]}';
        }}
        return getParameter(parameter);
    }};
    
    // Canvas fingerprinting evasion
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type) {{
        if (type === 'image/png') {{
            // Agregar ruido aleatorio para evitar fingerprinting
            const canvas = this;
            const ctx = canvas.getContext('2d');
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            for (let i = 0; i < imageData.data.length; i += 4) {{
                imageData.data[i] += Math.floor(Math.random() * 3) - 1;
                imageData.data[i+1] += Math.floor(Math.random() * 3) - 1;  
                imageData.data[i+2] += Math.floor(Math.random() * 3) - 1;
            }}
            ctx.putImageData(imageData, 0, 0);
        }}
        return originalToDataURL.call(this, type);
    }};
    
    // Ocultar Chrome automation
    window.chrome = {{
        runtime: {{
            onConnect: undefined,
            onMessage: undefined,
            connect: function() {{ return {{ postMessage: function() {{}}, onMessage: {{addListener: function() {{}}}} }}; }}
        }}
    }};
    
    // Screen fingerprinting evasion
    Object.defineProperty(screen, 'width', {{
        get: () => {screen_config['width']}
    }});
    Object.defineProperty(screen, 'height', {{
        get: () => {screen_config['height']}
    }});
    Object.defineProperty(screen, 'availWidth', {{
        get: () => {screen_config['width']}
    }});
    Object.defineProperty(screen, 'availHeight', {{
        get: () => {screen_config['height'] - 40}
    }});
    
    // Permissions API evasion
    Object.defineProperty(navigator, 'permissions', {{
        get: () => ({{
            query: () => Promise.resolve({{state: 'granted'}})
        }})
    }});
    
    // Battery API evasion
    Object.defineProperty(navigator, 'getBattery', {{
        get: () => undefined
    }});
    
    // Media devices evasion
    Object.defineProperty(navigator, 'mediaDevices', {{
        get: () => undefined
    }});
    
    // Connection API evasion
    Object.defineProperty(navigator, 'connection', {{
        get: () => undefined
    }});
    
    // DeviceMemory evasion
    Object.defineProperty(navigator, 'deviceMemory', {{
        get: () => {random.choice([4, 8, 16])}
    }});
    
    // HardwareConcurrency randomization
    Object.defineProperty(navigator, 'hardwareConcurrency', {{
        get: () => {random.choice([4, 6, 8, 12])}
    }});
    """
    
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': stealth_script
    })
    
    # === CONFIGURACIONES ADICIONALES ===
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(10)
    
    # Configurar window object adicional
    driver.execute_script("""
        window.outerHeight = window.innerHeight;
        window.outerWidth = window.innerWidth;
        
        // Agregar event listeners falsos
        window.addEventListener = new Proxy(window.addEventListener, {
            apply: function(target, thisArg, argumentsList) {
                // Simular eventos normales
                return target.apply(thisArg, argumentsList);
            }
        });
    """)
    
    logging.info("✅ Driver ultra-stealth configurado exitosamente")
    return driver, proxy_config, ua_config

def human_like_scroll(driver):
    """🧑 Scroll humano ultra-realista con patrones aleatorios"""
    scroll_patterns = [
        # Patrón 1: Scroll gradual con pausas variables
        lambda: [
            ("window.scrollTo(0, 0);", random.uniform(0.2, 0.5)),
            ("window.scrollTo(0, document.body.scrollHeight/6);", random.uniform(0.3, 0.8)),
            ("window.scrollTo(0, document.body.scrollHeight/3);", random.uniform(0.2, 0.6)),
            ("window.scrollTo(0, document.body.scrollHeight/2);", random.uniform(0.4, 1.0)),
            ("window.scrollTo(0, document.body.scrollHeight*2/3);", random.uniform(0.3, 0.7)),
            ("window.scrollTo(0, document.body.scrollHeight);", random.uniform(0.5, 1.2))
        ],
        # Patrón 2: Scroll con retrocesos (comportamiento humano típico)
        lambda: [
            ("window.scrollTo(0, document.body.scrollHeight/4);", random.uniform(0.3, 0.7)),
            ("window.scrollTo(0, document.body.scrollHeight/6);", random.uniform(0.2, 0.4)),  # Retroceso
            ("window.scrollTo(0, document.body.scrollHeight/2);", random.uniform(0.4, 0.9)),
            ("window.scrollTo(0, document.body.scrollHeight*3/4);", random.uniform(0.3, 0.8)),
            ("window.scrollTo(0, document.body.scrollHeight/2);", random.uniform(0.2, 0.5)),  # Retroceso
            ("window.scrollTo(0, document.body.scrollHeight);", random.uniform(0.6, 1.4))
        ],
        # Patrón 3: Scroll rápido con pausas largas
        lambda: [
            ("window.scrollTo(0, document.body.scrollHeight/3);", random.uniform(0.1, 0.3)),
            ("window.scrollTo(0, document.body.scrollHeight*2/3);", random.uniform(0.8, 1.5)),  # Pausa larga
            ("window.scrollTo(0, document.body.scrollHeight);", random.uniform(0.2, 0.4))
        ]
    ]
    
    # Seleccionar patrón aleatorio
    selected_pattern = random.choice(scroll_patterns)()
    
    logging.info(f"🧑 Ejecutando scroll humano ({len(selected_pattern)} pasos)")
    
    for script, delay in selected_pattern:
        try:
            driver.execute_script(script)
            time.sleep(delay)
        except Exception as e:
            logging.warning(f"⚠️ Error en scroll: {e}")
            break

def simulate_human_behavior(driver):
    """🧑 Simula comportamiento humano avanzado"""
    behaviors = [
        # Movimiento de mouse aleatorio
        lambda: ActionChains(driver).move_by_offset(
            random.randint(-100, 100), 
            random.randint(-100, 100)
        ).perform(),
        
        # Click en área vacía ocasionalmente  
        lambda: driver.execute_script(f"""
            var event = new MouseEvent('click', {{
                bubbles: true,
                cancelable: true,
                clientX: {random.randint(100, 800)},
                clientY: {random.randint(100, 600)}
            }});
            document.body.dispatchEvent(event);
        """),
        
        # Cambio de tamaño de ventana (si no es headless)
        lambda: driver.set_window_size(
            random.randint(1200, 1920),
            random.randint(800, 1080)
        ),
        
        # Simular teclas de navegación
        lambda: driver.execute_script("""
            document.body.focus();
            var keyEvent = new KeyboardEvent('keydown', {
                key: 'PageDown',
                code: 'PageDown'  
            });
            document.dispatchEvent(keyEvent);
        """)
    ]
    
    # Ejecutar 1-3 comportamientos aleatorios
    num_behaviors = random.randint(1, 3)
    selected_behaviors = random.sample(behaviors, num_behaviors)
    
    for behavior in selected_behaviors:
        try:
            behavior()
            time.sleep(random.uniform(0.1, 0.5))
        except Exception as e:
            logging.warning(f"⚠️ Error simulando comportamiento: {e}")

def extract_products_stealth(soup, page_num, search_term):
    """🕵️ Extracción stealth optimizada para Ripley con múltiples estrategias"""
    products = []
    
    # Estrategias de selección múltiples para evasión
    selector_strategies = [
        'div[data-cy*="product-"]',
        'div.catalog-product-item',
        'a[href*="/p/"]',
        '[data-testid*="product"]',
        '.product-card',
        '.product-item',
        '[data-product-id]'
    ]
    
    product_containers = []
    
    # Intentar múltiples estrategias
    for strategy in selector_strategies:
        containers = soup.select(strategy)
        if containers and len(containers) > len(product_containers):
            product_containers = containers
            logging.info(f"🎯 Estrategia exitosa: {strategy} ({len(containers)} productos)")
            break
    
    if not product_containers:
        logging.warning(f"⚠️ No se encontraron productos con ninguna estrategia")
        return products
    
    logging.info(f"📦 Búsqueda '{search_term}' P{page_num}: {len(product_containers)} productos detectados")
    
    for i, container in enumerate(product_containers, 1):
        try:
            # === EXTRACCIÓN DE DATOS CORE ===
            product_name = ""
            product_code = ""
            product_link = ""
            brand = ""
            
            # === LINK Y CÓDIGO ===
            if container.name == 'a':
                link_elem = container
            else:
                link_elem = container.select_one('a[href*="/p/"], a[href*="producto"]')
            
            if link_elem:
                href = link_elem.get('href', '')
                if href:
                    product_link = f"https://simple.ripley.cl{href}" if href.startswith('/') else href
                    # Extraer código con múltiples patrones
                    code_patterns = [r'/p/([^/?]+)', r'producto/([^/?]+)', r'sku[=:]([^&/]+)']
                    for pattern in code_patterns:
                        code_match = re.search(pattern, href)
                        if code_match:
                            product_code = code_match.group(1)
                            break
            
            # === NOMBRE DEL PRODUCTO (múltiples estrategias) ===
            name_selectors = [
                'div.catalog-product-details__name',
                '[data-product-name]',
                '.product-name',
                '.product-title',
                'h3', 'h4', 'h5',
                '.name'
            ]
            
            for selector in name_selectors:
                name_elem = container.select_one(selector)
                if name_elem:
                    if selector == '[data-product-name]':
                        product_name = name_elem.get('data-product-name', '')
                    else:
                        product_name = name_elem.get_text(strip=True)
                    if product_name:
                        break
            
            # Fallback: nombre desde imagen alt
            if not product_name:
                img_elem = container.select_one('img')
                if img_elem:
                    alt_text = img_elem.get('alt', '')
                    if alt_text and alt_text not in ['Image', 'image', '']:
                        product_name = alt_text
            
            # Fallback: nombre desde URL
            if not product_name and product_link:
                if '/p/' in product_link:
                    slug = product_link.split('/p/')[-1].split('?')[0]
                    product_name = slug.replace('-', ' ').title()
            
            if not product_name:
                continue
            
            # === DETECCIÓN DE MARCA ===
            brand_selectors = ['[data-product-brand]', '.brand', '.marca']
            for selector in brand_selectors:
                brand_elem = container.select_one(selector)
                if brand_elem:
                    brand = brand_elem.get('data-product-brand', '') or brand_elem.get_text(strip=True)
                    if brand:
                        break
            
            # Detección de marca en texto
            if not brand:
                text_content = container.get_text().upper()
                common_brands = [
                    'SAMSUNG', 'APPLE', 'XIAOMI', 'HUAWEI', 'MOTOROLA', 'LG', 'SONY', 
                    'HONOR', 'OPPO', 'REALME', 'NOKIA', 'ALCATEL', 'ONEPLUS', 'VIVO'
                ]
                for b in common_brands:
                    if b in text_content:
                        brand = b
                        break
            
            # === SISTEMA DE PRECIOS AVANZADO ===
            price_data = extract_advanced_prices(container)
            
            # === DATOS ADICIONALES ===
            image_url = ""
            img_elem = container.select_one('img')
            if img_elem:
                image_url = img_elem.get('src', '') or img_elem.get('data-src', '')
            
            rating = ""
            rating_elem = container.select_one('.rating, .stars, [data-rating]')
            if rating_elem:
                rating = rating_elem.get_text(strip=True) or rating_elem.get('data-rating', '')
            
            reviews_count = ""
            reviews_elem = container.select_one('.reviews, .review-count, [data-reviews]')
            if reviews_elem:
                reviews_count = re.sub(r'[^\d]', '', reviews_elem.get_text())
            
            # === ESTRUCTURA DE DATOS STEALTH ===
            product_data = {
                'product_code': product_code,
                'name': product_name,
                'brand': brand,
                'ripley_price_text': price_data.get('ripley_price_text', ''),
                'ripley_price': price_data.get('ripley_price_numeric'),
                'card_price_text': price_data.get('card_price_text', ''),
                'card_price': price_data.get('card_price_numeric'),
                'normal_price_text': price_data.get('normal_price_text', ''),
                'normal_price': price_data.get('normal_price_numeric'),
                'original_price_text': price_data.get('original_price_text', ''),
                'original_price': price_data.get('original_price_numeric'),
                'discount_percent': price_data.get('discount_percent', ''),
                'rating': rating,
                'reviews_count': reviews_count,
                'image_url': image_url,
                'product_link': product_link,
                'page_scraped': page_num,
                'search_term': search_term,
                'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            products.append(product_data)
            
        except Exception as e:
            logging.warning(f"⚠️ Error procesando producto {i}: {e}")
            continue
    
    logging.info(f"✅ Búsqueda '{search_term}' P{page_num}: {len(products)} productos extraídos exitosamente")
    return products

def extract_advanced_prices(container):
    """💰 Sistema avanzado de extracción de precios Ripley"""
    price_data = {
        'ripley_price_text': '',
        'ripley_price_numeric': None,
        'card_price_text': '',
        'card_price_numeric': None, 
        'normal_price_text': '',
        'normal_price_numeric': None,
        'original_price_text': '',
        'original_price_numeric': None,
        'discount_percent': ''
    }
    
    price_pattern = re.compile(r'\$[\s]*[\d.,]+')
    
    # Estrategia 1: Selectores específicos de Ripley
    price_selectors = [
        {'selector': '.catalog-prices__card-price, [data-testid*="card-price"]', 'type': 'card'},
        {'selector': '.catalog-prices__offer-price, [data-testid*="offer-price"]', 'type': 'ripley'},
        {'selector': '.catalog-prices__list-price, [data-testid*="list-price"]', 'type': 'original'},
        {'selector': '.price, .precio', 'type': 'normal'},
        {'selector': '.old-price, .before-price, .previous-price', 'type': 'original'},
    ]
    
    prices_found = []
    
    for selector_config in price_selectors:
        elements = container.select(selector_config['selector'])
        for elem in elements:
            text = elem.get_text(strip=True)
            if '$' in text:
                price_match = price_pattern.search(text)
                if price_match:
                    price_text = price_match.group(0)
                    try:
                        price_numeric = int(re.sub(r'[^\d]', '', price_text))
                        prices_found.append({
                            'text': price_text,
                            'numeric': price_numeric,
                            'type': selector_config['type']
                        })
                    except ValueError:
                        continue
    
    # Estrategia 2: Análisis por clases CSS
    if not prices_found:
        all_price_elements = container.select('span, div')
        for elem in all_price_elements:
            text = elem.get_text(strip=True)
            if '$' in text:
                classes = ' '.join(elem.get('class', [])).lower()
                
                price_type = 'normal'
                if any(keyword in classes for keyword in ['card', 'tc', 'tarjeta']):
                    price_type = 'card'
                elif any(keyword in classes for keyword in ['ripley', 'offer', 'oferta']):
                    price_type = 'ripley'
                elif any(keyword in classes for keyword in ['old', 'previous', 'before', 'original']):
                    price_type = 'original'
                
                price_match = price_pattern.search(text)
                if price_match:
                    price_text = price_match.group(0)
                    try:
                        price_numeric = int(re.sub(r'[^\d]', '', price_text))
                        prices_found.append({
                            'text': price_text,
                            'numeric': price_numeric,
                            'type': price_type
                        })
                    except ValueError:
                        continue
    
    # Estrategia 3: Todos los precios del contenedor
    if not prices_found:
        all_prices = price_pattern.findall(container.get_text())
        if all_prices:
            for i, price_text in enumerate(all_prices):
                try:
                    price_numeric = int(re.sub(r'[^\d]', '', price_text))
                    price_type = 'ripley' if i == 0 else 'card' if i == 1 else 'original'
                    prices_found.append({
                        'text': price_text,
                        'numeric': price_numeric,
                        'type': price_type
                    })
                except ValueError:
                    continue
    
    # Asignar precios por tipo
    for price in prices_found:
        if price['type'] == 'ripley' and not price_data['ripley_price_text']:
            price_data['ripley_price_text'] = price['text']
            price_data['ripley_price_numeric'] = price['numeric']
        elif price['type'] == 'card' and not price_data['card_price_text']:
            price_data['card_price_text'] = price['text']
            price_data['card_price_numeric'] = price['numeric']
        elif price['type'] == 'normal' and not price_data['normal_price_text']:
            price_data['normal_price_text'] = price['text']
            price_data['normal_price_numeric'] = price['numeric']
        elif price['type'] == 'original' and not price_data['original_price_text']:
            price_data['original_price_text'] = price['text']
            price_data['original_price_numeric'] = price['numeric']
    
    # Calcular descuento si hay precio original
    if price_data['original_price_numeric'] and price_data['ripley_price_numeric']:
        discount = ((price_data['original_price_numeric'] - price_data['ripley_price_numeric']) / price_data['original_price_numeric']) * 100
        price_data['discount_percent'] = f"{discount:.0f}%"
    
    return price_data

def scrape_busqueda_stealth(search_key, search_info, ciclo_num):
    """🥷 Scraping stealth de una búsqueda Ripley con evasión completa"""
    logging.info(f"🥷 CICLO {ciclo_num} - Stealth Mode: {search_info['name']}")
    
    driver = None
    proxy_config = None
    ua_config = None
    all_products = []
    
    try:
        driver, proxy_config, ua_config = setup_ultra_stealth_driver()
        
        # Usar términos de búsqueda aleatorios
        search_terms = [search_info['term']] + search_info.get('variations', [])
        selected_term = random.choice(search_terms)
        
        logging.info(f"🔍 Término seleccionado: '{selected_term}'")
        
        # Scrapear páginas con variación aleatoria
        max_pages = random.randint(15, 20)  # Entre 15-20 páginas
        
        for page_num in range(1, max_pages + 1):
            if stop_event.is_set():
                logging.info("🛑 Deteniendo por señal de parada")
                break
            
            # URL con parámetros aleatorios para mayor stealth
            base_params = {
                'source': 'search',
                'term': selected_term,
                's': random.choice(['mdco', 'relevance', 'price_asc']),
                'type': 'catalog'
            }
            
            if page_num > 1:
                base_params['page'] = page_num
            
            # Agregar parámetros aleatorios ocasionalmente
            if random.random() > 0.7:
                base_params['sort'] = random.choice(['relevance', 'price_asc', 'price_desc'])
            
            url = f"https://simple.ripley.cl/tecno/celulares?{urllib.parse.urlencode(base_params)}"
            
            logging.info(f"🔗 P{page_num}/{max_pages}: {url}")
            
            try:
                # Delay humanizado variable
                pre_load_delay = random.uniform(1.0, 4.0)
                time.sleep(pre_load_delay)
                
                driver.get(url)
                
                # Simular comportamiento humano después de la carga
                simulate_human_behavior(driver)
                
                # Esperar carga con timeout variable
                timeout = random.randint(8, 15)
                try:
                    WebDriverWait(driver, timeout).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-cy*="product"]')),
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.catalog-product-item')),
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/p/"]'))
                        )
                    )
                except TimeoutException:
                    logging.warning(f"⚠️ Timeout en página {page_num}")
                
                # Delay post-carga
                time.sleep(random.uniform(1.5, 3.5))
                
                # Scroll humano avanzado
                human_like_scroll(driver)
                
                # Comportamiento adicional aleatorio
                if random.random() > 0.6:
                    simulate_human_behavior(driver)
                
                # Procesar contenido
                html_content = driver.page_source
                soup = BeautifulSoup(html_content, 'lxml')
                
                page_products = extract_products_stealth(soup, page_num, selected_term)
                
                # Metadata de stealth
                for product in page_products:
                    product.update({
                        'search_key': search_key,
                        'search_name': search_info['name'],
                        'ciclo_number': ciclo_num,
                        'proxy_country': proxy_config.get('country', 'Unknown'),
                        'user_agent_platform': ua_config.get('platform', 'Unknown'),
                        'selected_search_term': selected_term
                    })
                
                all_products.extend(page_products)
                
                # Lógica de parada inteligente
                if not page_products:
                    consecutive_empty = consecutive_empty + 1 if 'consecutive_empty' in locals() else 1
                    if consecutive_empty >= 3:
                        logging.info(f"🛑 Deteniendo tras {consecutive_empty} páginas vacías")
                        break
                else:
                    consecutive_empty = 0
                
                # Delay entre páginas ultra-variable
                inter_page_delay = random.uniform(2.0, 6.0)
                if random.random() > 0.8:  # 20% probabilidad de pausa larga
                    inter_page_delay = random.uniform(8.0, 15.0)
                
                logging.info(f"⏳ Pausa de {inter_page_delay:.1f}s antes de siguiente página")
                time.sleep(inter_page_delay)
                
            except Exception as e:
                logging.error(f"❌ Error en página {page_num}: {e}")
                # Delay de recuperación
                time.sleep(random.uniform(5.0, 10.0))
                continue
        
        # Guardar resultados con metadata completa
        if all_products:
            current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(
                output_log_dir, 
                f"stealth_{search_key}_c{ciclo_num:03d}_{current_datetime}.json"
            )
            
            json_data = {
                "metadata": {
                    "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "search_term": selected_term,
                    "original_term": search_info['term'],
                    "search_name": search_info['name'],
                    "search_key": search_key,
                    "total_products": len(all_products),
                    "pages_scraped": len(set(p['page_scraped'] for p in all_products)),
                    "ciclo_number": ciclo_num,
                    "proxy_config": {
                        "host": proxy_config['host'],
                        "country": proxy_config['country']
                    },
                    "user_agent_platform": ua_config['platform'],
                    "scraper": "Ripley Scraper STEALTH v2.0 🥷",
                    "stealth_features": [
                        "rotating_proxies", "dynamic_user_agents", "human_behavior_simulation",
                        "advanced_fingerprinting_evasion", "randomized_timings", 
                        "variable_scroll_patterns", "ultra_stealth_extension"
                    ]
                },
                "products": all_products
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"💾 CICLO {ciclo_num} - Stealth Complete: {len(all_products)} productos → {filename}")
        
        return len(all_products)
        
    except Exception as e:
        logging.error(f"💥 Error crítico stealth ciclo {ciclo_num}: {e}")
        return 0
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logging.warning(f"⚠️ Error cerrando driver: {e}")

def ejecutar_stealth_continuo():
    """🥷 Ejecutor principal del scraping stealth continuo"""
    logging.info("🥷 INICIANDO RIPLEY STEALTH SCRAPER v2.0")
    logging.info(f"📅 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"🔍 Búsquedas configuradas: {len(BUSQUEDAS_STEALTH)}")
    
    for key, info in BUSQUEDAS_STEALTH.items():
        logging.info(f"   🎯 {info['name']}: '{info['term']}' + variaciones {info.get('variations', [])}")
    
    logging.info(f"🌐 Proxies disponibles: {len(PROXY_POOL)}")
    logging.info(f"🎭 User agents disponibles: {len(STEALTH_USER_AGENTS)}")
    logging.info("📄 Páginas por ciclo: 15-20 (variable)")
    logging.info("⏱️ Delays: Ultra-variables (1-15s)")
    logging.info("🛡️ Features: Proxies + Fingerprinting + Comportamiento Humano")
    logging.info("="*80)
    
    ciclo_num = 1
    busqueda_keys = list(BUSQUEDAS_STEALTH.keys())
    busqueda_index = 0
    
    try:
        while not stop_event.is_set():
            # Seleccionar búsqueda actual
            search_key = busqueda_keys[busqueda_index]
            search_info = BUSQUEDAS_STEALTH[search_key]
            
            start_time = time.time()
            
            # Ejecutar scraping stealth
            productos_extraidos = scrape_busqueda_stealth(search_key, search_info, ciclo_num)
            
            execution_time = time.time() - start_time
            
            logging.info(f"⏱️ CICLO {ciclo_num} completado en {execution_time:.2f}s")
            logging.info(f"📊 Productos extraídos: {productos_extraidos}")
            logging.info("-" * 60)
            
            # Avanzar a siguiente búsqueda
            busqueda_index = (busqueda_index + 1) % len(busqueda_keys)
            ciclo_num += 1
            
            # Delay entre ciclos ultra-variable para máximo stealth
            if not stop_event.is_set():
                inter_cycle_delay = random.uniform(5.0, 20.0)
                if random.random() > 0.7:  # 30% probabilidad de pausa extra larga
                    inter_cycle_delay = random.uniform(30.0, 60.0)
                
                next_search = BUSQUEDAS_STEALTH[busqueda_keys[busqueda_index]]
                logging.info(f"🔄 Próximo: {next_search['name']} en {inter_cycle_delay:.1f}s")
                
                time.sleep(inter_cycle_delay)
            
            if stop_event.is_set():
                break
    
    except KeyboardInterrupt:
        logging.info("⚠️ Recibida señal de interrupción manual")
        stop_event.set()
    except Exception as e:
        logging.error(f"💥 Error crítico en bucle principal: {e}")
        stop_event.set()
    finally:
        logging.info("🏁 RIPLEY STEALTH SCRAPER DETENIDO")
        logging.info(f"📊 Total ciclos ejecutados: {ciclo_num - 1}")
        logging.info(f"⏰ Finalización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    print("🥷 RIPLEY STEALTH SCRAPER v2.0")
    print(f"🔍 {len(BUSQUEDAS_STEALTH)} búsquedas stealth configuradas:")
    for key, info in BUSQUEDAS_STEALTH.items():
        variations = info.get('variations', [])
        print(f"   • {info['name']}: '{info['term']}' + {len(variations)} variaciones")
    
    print(f"🌐 {len(PROXY_POOL)} proxies rotativos")
    print(f"🎭 {len(STEALTH_USER_AGENTS)} user agents con fingerprints")
    print("📄 15-20 páginas por búsqueda (variable)")
    print("⏱️ Delays ultra-variables (1-60s)")
    print("🛡️ Anti-detección: MÁXIMO NIVEL")
    print()
    print("Para detener: Ctrl+C")
    print("="*60)
    
    try:
        ejecutar_stealth_continuo()
    except KeyboardInterrupt:
        print("\n⚠️ Deteniendo stealth scraper...")
        stop_event.set()
    except Exception as e:
        print(f"\n💥 Error crítico: {e}")
        stop_event.set()