"""
🔍 Ripley Navegación Avanzada - BOTÓN DE PAGINACIÓN
Navegación correcta usando botones de página en lugar de URLs directas
"""

import sys
import io
import json
import time
import re
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

def setup_navigation_driver():
    """🚀 Driver optimizado para navegación por botones de paginación"""
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
    
    # Configuraciones experimentales
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.images": 1
    })
    
    print("🔧 NAVEGADOR CONFIGURADO PARA NAVEGACIÓN POR BOTONES")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(10)
        
        print("✅ Navegador Chrome iniciado correctamente")
        return driver
    except Exception as e:
        print(f"❌ Error iniciando Chrome: {e}")
        raise

def buscar_boton_siguiente(driver):
    """🔍 Busca el botón de página siguiente en diferentes ubicaciones"""
    
    # Lista de selectores posibles para el botón siguiente
    selectores = [
        # Selectores por texto
        "//button[contains(text(), 'Siguiente')]",
        "//a[contains(text(), 'Siguiente')]",
        "//button[contains(text(), '›')]",
        "//a[contains(text(), '›')]",
        "//button[contains(text(), '2')]",
        "//a[contains(text(), '2')]",
        
        # Selectores por clase CSS comunes para paginación
        "//div[contains(@class, 'pagination')]//button[2]",
        "//div[contains(@class, 'pagination')]//a[2]",
        "//ul[contains(@class, 'pagination')]//li[2]//a",
        "//ul[contains(@class, 'pagination')]//li[2]//button",
        
        # Selectores por atributos data
        "//button[@data-page='2']",
        "//a[@data-page='2']",
        "//button[@aria-label='Go to page 2']",
        "//a[@aria-label='Go to page 2']",
        
        # Selectores genéricos de navegación
        "//nav//button[contains(text(), '2')]",
        "//nav//a[contains(text(), '2')]",
        ".pagination-next",
        ".page-next",
        "[data-testid='pagination-next']",
    ]
    
    print("🔍 Buscando botón de página siguiente...")
    
    for i, selector in enumerate(selectores):
        try:
            if selector.startswith('//'):
                # XPath selector
                elementos = driver.find_elements(By.XPATH, selector)
            else:
                # CSS selector
                elementos = driver.find_elements(By.CSS_SELECTOR, selector)
            
            if elementos:
                print(f"✅ Encontrado botón con selector {i+1}: {selector}")
                print(f"📊 Elementos encontrados: {len(elementos)}")
                
                for j, elemento in enumerate(elementos):
                    try:
                        texto = elemento.text.strip()
                        es_clickeable = elemento.is_enabled() and elemento.is_displayed()
                        print(f"   Elemento {j+1}: '{texto}' - Clickeable: {es_clickeable}")
                        
                        if es_clickeable and (texto == '2' or 'siguiente' in texto.lower() or '›' in texto):
                            return elemento
                    except Exception as e:
                        print(f"   ⚠️ Error verificando elemento {j+1}: {e}")
                        continue
        except Exception as e:
            print(f"⚠️ Error con selector {i+1}: {e}")
            continue
    
    print("❌ No se encontró botón de página siguiente")
    return None

def navegacion_avanzada():
    """🚀 Navegación avanzada usando botones de paginación"""
    print("🔍 RIPLEY NAVEGACIÓN AVANZADA - BOTONES DE PAGINACIÓN")
    print("📺 Navegando de página 1 a página 2 usando botones")
    print("="*60)
    
    driver = setup_navigation_driver()
    
    try:
        # PASO 1: Cargar página 1
        print("\n📄 PASO 1: Cargando página 1...")
        url_pagina1 = "https://simple.ripley.cl/tecno/celulares?source=search&term=smartphone&s=mdco&type=catalog"
        print(f"🔗 URL: {url_pagina1}")
        
        try:
            driver.get(url_pagina1)
            print("✅ Página 1 cargada exitosamente")
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ Error cargando página 1: {e}")
            return
        
        # Scroll para cargar contenido dinámico
        print("📜 Haciendo scroll para cargar contenido...")
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            print("✅ Scroll completado")
        except Exception as e:
            print(f"⚠️ Error durante scroll: {e}")
        
        # Contar productos en página 1
        soup1 = BeautifulSoup(driver.page_source, 'lxml')
        products1 = soup1.find_all('a', href=True)
        product_links1 = [a for a in products1 if '/p/' in a.get('href', '')]
        print(f"📦 Productos encontrados en página 1: {len(product_links1)}")
        
        print("\n⏰ PAUSA - Observa la página 1 por 12 segundos...")
        print("📱 Deberías ver productos de smartphones cargados en pantalla")
        time.sleep(12)
        
        # PASO 2: Buscar y hacer clic en botón siguiente
        print("\n🔘 PASO 2: Buscando botón de página siguiente...")
        
        # Scroll hacia abajo para encontrar la paginación
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        boton_siguiente = buscar_boton_siguiente(driver)
        
        if boton_siguiente:
            try:
                print(f"🖱️ Haciendo clic en botón: '{boton_siguiente.text}'")
                
                # Scroll al botón
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_siguiente)
                time.sleep(1)
                
                # Hacer clic
                driver.execute_script("arguments[0].click();", boton_siguiente)
                print("✅ Clic ejecutado exitosamente")
                print("⏳ Esperando carga de página 2...")
                time.sleep(8)
                
                # Verificar si la navegación funcionó
                current_url = driver.current_url
                print(f"🔗 URL actual después del clic: {current_url}")
                
                # Contar productos en página 2
                soup2 = BeautifulSoup(driver.page_source, 'lxml')
                products2 = soup2.find_all('a', href=True)
                product_links2 = [a for a in products2 if '/p/' in a.get('href', '')]
                print(f"📦 Productos encontrados en página 2: {len(product_links2)}")
                
                # Verificar título para detectar bloqueo
                title = driver.title
                print(f"📋 Título de página 2: {title}")
                
                if "blocked" in title.lower() or "error" in title.lower():
                    print("⚠️ Página 2 está bloqueada")
                else:
                    print("✅ Navegación exitosa a página 2")
                
            except Exception as e:
                print(f"❌ Error haciendo clic: {e}")
        else:
            print("❌ No se pudo encontrar el botón de siguiente")
        
        print("\n⏰ PAUSA FINAL - Observa los resultados por 20 segundos...")
        print("📊 Puedes revisar si la página 2 se cargó o está bloqueada")
        time.sleep(20)
        
    except Exception as e:
        print(f"❌ Error durante navegación: {e}")
    finally:
        print("🔚 Cerrando navegador...")
        driver.quit()
        print("✅ Debug completado")

if __name__ == "__main__":
    navegacion_avanzada()