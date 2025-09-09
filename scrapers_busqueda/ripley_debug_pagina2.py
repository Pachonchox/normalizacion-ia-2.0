"""
🔍 Debug Ripley Página 2 - NAVEGADOR ABIERTO
Análisis específico de por qué la página 2 no carga productos
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
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import logging

# Configurar encoding para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configurar logging simple
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def setup_debug_driver():
    """🚀 Driver con navegador VISIBLE para debug con configuración de seguridad mejorada"""
    chrome_options = Options()
    
    # NO HEADLESS - queremos ver el navegador
    # chrome_options.add_argument("--headless")  # COMENTADO para debug
    
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
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--ignore-certificate-verification")
    
    # Anti-detección mejorada
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Configuraciones de navegador normal
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    
    # User agent actualizado
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    
    # Configuraciones experimentales para estabilidad
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.images": 1
    })
    
    print("🔧 DEBUG CON CONFIGURACIÓN DE SEGURIDAD MEJORADA")
    print("⚠️ SIN PROXY - Solo para análisis de estructura de página")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.set_page_load_timeout(60)  # Aumentado timeout
        driver.implicitly_wait(15)  # Aumentado wait
        
        print("✅ Navegador Chrome iniciado correctamente")
        return driver
    except Exception as e:
        print(f"❌ Error iniciando Chrome: {e}")
        raise

def debug_pagina2():
    """🔍 Debug específico de la página 2"""
    print("🔍 RIPLEY DEBUG - PÁGINA 2 CON NAVEGADOR ABIERTO")
    print("📺 Analizando: smartphone página 2")
    print("="*60)
    
    driver = setup_debug_driver()
    
    try:
        # PASO 1: Cargar página 1 primero
        print("\n📄 PASO 1: Cargando página 1...")
        url_pagina1 = "https://simple.ripley.cl/tecno/celulares?source=search&term=smartphone&s=mdco&type=catalog"
        print(f"🔗 URL: {url_pagina1}")
        
        try:
            driver.get(url_pagina1)
            print("✅ Página 1 cargada exitosamente")
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ Error cargando página 1: {e}")
            print("🔄 Continuando con el debug...")
        
        # Scroll en página 1
        print("📜 Haciendo scroll en página 1...")
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            print("✅ Scroll en página 1 completado")
        except Exception as e:
            print(f"⚠️ Error durante scroll: {e}")
            print("🔄 Continuando con el análisis...")
        
        # Buscar productos en página 1
        soup1 = BeautifulSoup(driver.page_source, 'lxml')
        products1 = soup1.find_all('a', href=True)
        product_links1 = [a for a in products1 if '/p/' in a.get('href', '')]
        print(f"✅ Productos encontrados en página 1: {len(product_links1)}")
        
        print("⏸️ NAVEGADOR ABIERTO - Revisa la página 1 en pantalla...")
        print("⏸️ Continuando a página 2 en 10 segundos...")
        time.sleep(10)
        
        # PASO 2: Cargar página 2 directamente
        print("\n📄 PASO 2: Cargando página 2 DIRECTAMENTE...")
        url_pagina2 = "https://simple.ripley.cl/tecno/celulares?source=search&term=smartphone&page=2&s=mdco&type=catalog"
        print(f"🔗 URL: {url_pagina2}")
        
        driver.get(url_pagina2)
        time.sleep(5)
        
        # Scroll en página 2
        print("📜 Haciendo scroll en página 2...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # Buscar productos en página 2
        soup2 = BeautifulSoup(driver.page_source, 'lxml')
        products2 = soup2.find_all('a', href=True)
        product_links2 = [a for a in products2 if '/p/' in a.get('href', '')]
        print(f"⚠️ Productos encontrados en página 2: {len(product_links2)}")
        
        # Analizar el HTML de la página 2
        print("\n🔍 ANALIZANDO HTML DE PÁGINA 2...")
        title = driver.title
        print(f"📋 Título de página: {title}")
        
        # Buscar mensajes de error
        error_messages = soup2.find_all(['div', 'span', 'p'], string=re.compile(r'no.*encontr|error|bloqueado|forbidden', re.IGNORECASE))
        if error_messages:
            print("⚠️ Mensajes de error encontrados:")
            for msg in error_messages:
                print(f"   - {msg.get_text(strip=True)}")
        
        # Buscar indicadores de paginación
        pagination = soup2.find_all(['div', 'ul', 'nav'], class_=re.compile(r'pagin|page', re.IGNORECASE))
        if pagination:
            print(f"🔢 Elementos de paginación encontrados: {len(pagination)}")
        
        # Guardar HTML para análisis
        with open('ripley_debug_pagina2.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("💾 HTML guardado: ripley_debug_pagina2.html")
        
        print("⏸️ NAVEGADOR ABIERTO - Revisa la página 2 en pantalla...")
        print("⏸️ Continuando a navegación por clicks en 10 segundos...")
        time.sleep(10)
        
        # PASO 3: Intentar navegar desde página 1 usando clicks
        print("\n📄 PASO 3: Navegando desde página 1 con CLICKS...")
        driver.get(url_pagina1)
        time.sleep(5)
        
        # Buscar botón "Siguiente" o "2"
        try:
            # Intentar encontrar botón de página 2
            next_buttons = driver.find_elements(By.XPATH, "//a[contains(text(),'2')] | //button[contains(text(),'2')] | //a[contains(text(),'Siguiente')] | //button[contains(text(),'Siguiente')]")
            
            if next_buttons:
                print(f"🔘 Botones de navegación encontrados: {len(next_buttons)}")
                for i, btn in enumerate(next_buttons[:3]):  # Solo los primeros 3
                    try:
                        print(f"   Botón {i+1}: {btn.text} - {btn.tag_name}")
                        if '2' in btn.text or 'Siguiente' in btn.text:
                            print(f"🖱️ Haciendo click en: {btn.text}")
                            driver.execute_script("arguments[0].scrollIntoView();", btn)
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", btn)
                            time.sleep(5)
                            
                            # Ver si funcionó
                            current_url = driver.current_url
                            print(f"🔗 URL después del click: {current_url}")
                            
                            soup3 = BeautifulSoup(driver.page_source, 'lxml')
                            products3 = soup3.find_all('a', href=True)
                            product_links3 = [a for a in products3 if '/p/' in a.get('href', '')]
                            print(f"📦 Productos tras click: {len(product_links3)}")
                            break
                    except Exception as e:
                        print(f"❌ Error con botón {i+1}: {e}")
            else:
                print("❌ No se encontraron botones de navegación")
                
        except Exception as e:
            print(f"❌ Error buscando navegación: {e}")
        
        print("⏸️ NAVEGADOR ABIERTO - Debug completado, revisa los resultados...")
        print("⏸️ Cerrando navegador en 15 segundos...")
        time.sleep(15)
        
    except Exception as e:
        print(f"❌ Error durante debug: {e}")
        print("⏸️ Error ocurrido. Cerrando automáticamente...")
        time.sleep(2)
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_pagina2()