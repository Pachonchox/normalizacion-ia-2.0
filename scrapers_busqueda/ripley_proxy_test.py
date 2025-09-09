"""
🔍 Ripley Test con PROXY + URL DIRECTA
Test para verificar si el proxy permite acceso a página 2
"""

import sys
import io
import json
import time
import re
import zipfile
import tempfile
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import logging

# Configurar encoding para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configurar logging simple
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Configuración de proxy (ESPECIAL RIPLEY)
PROXY_HOST = "cl.decodo.com"
PROXY_PORT = "30000"
PROXY_USER = "sprhxdrm60"
PROXY_PASS = "rdAZz6ddZf+kv71f1A"

def create_proxy_extension():
    """🔧 Crear extensión de proxy para Chrome"""
    
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = """
    var config = {
            mode: "fixed_servers",
            rules: {
              singleProxy: {
                scheme: "http",
                host: "%s",
                port: parseInt(%s)
              },
              bypassList: ["localhost"]
            }
          };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """ % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)

    # Crear archivo ZIP temporal para la extensión
    proxy_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    proxy_zip.close()

    with zipfile.ZipFile(proxy_zip.name, 'w') as zip_file:
        zip_file.writestr("manifest.json", manifest_json)
        zip_file.writestr("background.js", background_js)

    return proxy_zip.name

def setup_proxy_driver():
    """🚀 Driver con PROXY configurado para Ripley"""
    chrome_options = Options()
    
    # Configuraciones básicas
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-web-security")
    
    # Configuraciones para evitar advertencias de seguridad
    chrome_options.add_argument("--ignore-certificate-errors-spki-list")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-extensions-https-warnings")
    
    # Anti-detección avanzada
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Configuraciones de navegador normal
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    
    # User agent actualizado
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    
    # Configurar PROXY
    try:
        proxy_extension_path = create_proxy_extension()
        chrome_options.add_extension(proxy_extension_path)
        print(f"✅ Extensión de proxy creada: {proxy_extension_path}")
    except Exception as e:
        print(f"⚠️ Error creando extensión de proxy: {e}")
        print("🔄 Continuando sin proxy...")
    
    # Configuraciones experimentales
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.images": 1
    })
    
    print("🔧 NAVEGADOR CON PROXY CONFIGURADO")
    print(f"🌐 Proxy: {PROXY_HOST}:{PROXY_PORT}")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(15)
        
        print("✅ Navegador Chrome con proxy iniciado correctamente")
        return driver
    except Exception as e:
        print(f"❌ Error iniciando Chrome: {e}")
        raise

def test_proxy_pagina2():
    """🔍 Test de acceso a página 2 con proxy"""
    print("🔍 RIPLEY TEST - PROXY + URL DIRECTA")
    print("📺 Probando acceso directo a página 2 con proxy")
    print("="*60)
    
    driver = setup_proxy_driver()
    
    try:
        # PASO 1: Cargar página 1
        print("\n📄 PASO 1: Cargando página 1...")
        url_pagina1 = "https://simple.ripley.cl/tecno/celulares?source=search&term=smartphone&s=mdco&type=catalog"
        print(f"🔗 URL: {url_pagina1}")
        
        try:
            driver.get(url_pagina1)
            print("✅ Página 1 cargada exitosamente")
            time.sleep(8)
        except Exception as e:
            print(f"⚠️ Error cargando página 1: {e}")
            return
        
        # Scroll para cargar contenido dinámico
        print("📜 Haciendo scroll para cargar contenido...")
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(3)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(4)
            print("✅ Scroll completado")
        except Exception as e:
            print(f"⚠️ Error durante scroll: {e}")
        
        # Contar productos en página 1
        soup1 = BeautifulSoup(driver.page_source, 'lxml')
        products1 = soup1.find_all('a', href=True)
        product_links1 = [a for a in products1 if '/p/' in a.get('href', '')]
        print(f"📦 Productos encontrados en página 1: {len(product_links1)}")
        
        # Verificar título página 1
        title1 = driver.title
        print(f"📋 Título página 1: {title1}")
        
        print("\n⏰ PAUSA - Observa la página 1 por 12 segundos...")
        print("📱 Deberías ver productos de smartphones cargados en pantalla")
        time.sleep(12)
        
        # PASO 2: Cargar página 2 DIRECTAMENTE
        print("\n📄 PASO 2: Cargando página 2 DIRECTAMENTE...")
        url_pagina2 = "https://simple.ripley.cl/tecno/celulares?source=search&term=smartphone&page=2&s=mdco&type=catalog"
        print(f"🔗 URL: {url_pagina2}")
        
        try:
            driver.get(url_pagina2)
            print("✅ Página 2 cargada exitosamente")
            time.sleep(8)
        except Exception as e:
            print(f"⚠️ Error cargando página 2: {e}")
        
        # Scroll en página 2
        print("📜 Haciendo scroll en página 2...")
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(3)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(4)
            print("✅ Scroll página 2 completado")
        except Exception as e:
            print(f"⚠️ Error durante scroll página 2: {e}")
        
        # Contar productos en página 2
        soup2 = BeautifulSoup(driver.page_source, 'lxml')
        products2 = soup2.find_all('a', href=True)
        product_links2 = [a for a in products2 if '/p/' in a.get('href', '')]
        print(f"📦 Productos encontrados en página 2: {len(product_links2)}")
        
        # Verificar título página 2
        title2 = driver.title
        print(f"📋 Título página 2: {title2}")
        
        # Analizar resultado
        if "blocked" in title2.lower() or "error" in title2.lower():
            print("⚠️ Página 2 está BLOQUEADA incluso con proxy")
        elif len(product_links2) > 0:
            print("✅ Página 2 funcional - Productos encontrados con proxy")
        else:
            print("🤔 Página 2 carga pero no hay productos - Posible contenido dinámico")
        
        print(f"\n📊 RESUMEN:")
        print(f"   📄 Página 1: {len(product_links1)} productos")
        print(f"   📄 Página 2: {len(product_links2)} productos")
        print(f"   🔗 URL final: {driver.current_url}")
        
        print("\n⏰ PAUSA FINAL - Observa página 2 por 20 segundos...")
        print("📊 Verifica visualmente si hay productos o página bloqueada")
        time.sleep(20)
        
    except Exception as e:
        print(f"❌ Error durante test: {e}")
    finally:
        print("🔚 Cerrando navegador...")
        driver.quit()
        print("✅ Test completado")

if __name__ == "__main__":
    test_proxy_pagina2()