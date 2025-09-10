"""
🔄 Falabella Scraper CONTINUO con BÚSQUEDAS
Sistema que ejecuta búsquedas cada 10 minutos de forma rotativa
Busca términos específicos y extrae 20 páginas por búsqueda
"""

import sys
import io
import json
import time
import re
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import logging
import os
from threading import Event

# Configurar encoding para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configurar logging continuo
output_log_dir = r"D:\Scrappers Normalizacion\1.1 ML\Datos de prueba\Falabella"
os.makedirs(output_log_dir, exist_ok=True)
log_file_path = os.path.join(output_log_dir, 'falabella_continuo.log')

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
    "perfume": {
        "term": "perfume",
        "name": "Perfumes"
    },
    "smartv": {
        "term": "smart tv",
        "name": "Smart TV"
    },
    "smartphone": {
        "term": "smartphone",
        "name": "Smartphones"
    }
}

def setup_driver_continuo():
    """Driver optimizado para operación continua Falabella"""
    logging.info("🔄 Configurando Chrome para operación continua Falabella...")
    
    chrome_options = Options()
    
    # Configuración optimizada para operación continua
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-web-security")
    
    # Anti-detección
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Optimizaciones para uso continuo
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")  # Ahorrar ancho de banda
    
    # Configuraciones de memoria
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.media_stream": 2,
        "profile.managed_default_content_settings.stylesheets": 1,
        "profile.managed_default_content_settings.cookies": 1,
        "profile.managed_default_content_settings.javascript": 1,
        "profile.managed_default_content_settings.plugins": 2,
        "profile.managed_default_content_settings.popups": 2,
        "profile.managed_default_content_settings.geolocation": 2,
        "profile.managed_default_content_settings.notifications": 2
    }
    
    chrome_options.add_experimental_option("prefs", prefs)
    
    # User agent rotativo
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ]
    chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.set_page_load_timeout(15)
    driver.implicitly_wait(3)
    
    logging.info("✅ Driver continuo Falabella configurado")
    return driver

def extract_products_continuo(soup, page_num, search_term):
    """Extracción optimizada para operación continua Falabella"""
    products = []
    
    # Selectores para búsquedas en Falabella (diferentes a categorías)
    containers = soup.select('a[data-pod="catalyst-pod"]')
    
    if not containers:
        containers = soup.select('.pod')
    
    if not containers:
        containers = soup.select('.grid-pod')
    
    logging.info(f"📦 Búsqueda '{search_term}' P{page_num}: {len(containers)} productos")
    
    for i, container in enumerate(containers, 1):
        try:
            # === DATOS ESENCIALES (optimizado) ===
            product_name = ""
            product_code = ""
            product_link = ""
            
            # Marca
            brand_elem = container.select_one('.pod-title')
            brand = brand_elem.get_text(strip=True) if brand_elem else ""
            
            # Nombre
            name_elem = container.select_one('.pod-subTitle, b.pod-subTitle')
            if name_elem:
                product_name = name_elem.get_text(strip=True)
            
            # Link del producto 🔗
            product_link = ""

            # El container es el <a> tag directamente
            if container.name == 'a':
                href = container.get('href', '')
                if href:
                    product_link = f"https://www.falabella.com{href}" if href.startswith('/') else href

            # Si no es <a>, buscar padre o hijo <a>
            if not product_link:
                parent_link = container.find_parent('a')
                if parent_link:
                    href = parent_link.get('href', '')
                    if href:
                        product_link = f"https://www.falabella.com{href}" if href.startswith('/') else href     
                else:
                    link_elem = container.select_one('a[href*="/product/"]')
                    if link_elem:
                        href = link_elem.get('href', '')
                        if href:
                            product_link = f"https://www.falabella.com{href}" if href.startswith('/') else href
            
            # Código
            if product_link:
                code_match = re.search(r'/product/(\d+)', product_link)
                if code_match:
                    product_code = code_match.group(1)
            
            if not product_code:
                pod_elem = container.select_one('[data-pod]')
                if pod_elem:
                    pod_data = pod_elem.get('data-pod', '{}')
                    try:
                        pod_json = json.loads(pod_data)
                        product_code = str(pod_json.get('id', f"FAL_{i:04d}_{page_num}"))
                    except:
                        product_code = f"FAL_{i:04d}_{page_num}"
            
            if not product_name:
                continue
            
            # === PRECIOS OPTIMIZADOS (3 niveles Falabella) ===
            card_price_text = ""
            card_price_numeric = None
            normal_price_text = ""
            normal_price_numeric = None
            original_price_text = ""
            original_price_numeric = None
            
            # Precio CMR (data attribute)
            cmr_elem = container.select_one('[data-cmr-price]')
            if cmr_elem:
                cmr_value = cmr_elem.get('data-cmr-price', '')
                if cmr_value:
                    try:
                        card_price_numeric = int(cmr_value.replace('.', '').replace(',', ''))
                        card_price_text = f"${cmr_value}"
                    except:
                        pass
            
            # Precio Internet (data attribute)
            internet_elem = container.select_one('[data-internet-price]')
            if internet_elem:
                internet_value = internet_elem.get('data-internet-price', '')
                if internet_value:
                    try:
                        normal_price_numeric = int(internet_value.replace('.', '').replace(',', ''))
                        normal_price_text = f"${internet_value}"
                    except:
                        pass
            
            # Si no hay precios con data attributes, buscar en spans
            if not card_price_text and not normal_price_text:
                price_spans = container.select('.prices span')
                prices_found = []
                for span in price_spans:
                    price_text = span.get_text(strip=True)
                    if '$' in price_text:
                        try:
                            price_num = int(re.sub(r'[^\d]', '', price_text))
                            prices_found.append((price_text, price_num))
                        except:
                            pass
                
                # Asignar precios según cantidad encontrada
                if len(prices_found) >= 3:
                    card_price_text, card_price_numeric = prices_found[0]
                    normal_price_text, normal_price_numeric = prices_found[1]
                    original_price_text, original_price_numeric = prices_found[2]
                elif len(prices_found) == 2:
                    normal_price_text, normal_price_numeric = prices_found[0]
                    original_price_text, original_price_numeric = prices_found[1]
                elif len(prices_found) == 1:
                    normal_price_text, normal_price_numeric = prices_found[0]
            
            # === ESTRUCTURA DE DATOS CONTINUA ===
            product_data = {
                'product_code': product_code,
                'name': product_name,
                'brand': brand,
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
    """Scraping de una búsqueda Falabella en modo continuo"""
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
            
            # Construir URL de búsqueda
            if page_num == 1:
                url = f"https://www.falabella.com/falabella-cl/search?Ntt={search_info['term']}"
            else:
                url = f"https://www.falabella.com/falabella-cl/search?Ntt={search_info['term']}&page={page_num}"
            
            logging.info(f"📄 {search_info['name']} - Página {page_num}/20")
            logging.info(f"🔗 URL: {url}")
            
            try:
                driver.get(url)
                time.sleep(2)
                
                # Scroll rápido
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight*2/3);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
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
                    if page_num > 5:  # Si es página tardía, probablemente no hay más
                        break
                
                # Pausa corta entre páginas
                time.sleep(0.5)
                
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
                    "base_url": f"https://www.falabella.com/falabella-cl/search?Ntt={search_info['term']}",
                    "total_products": len(all_products),
                    "pages_scraped": len(set(p['page_scraped'] for p in all_products)),
                    "ciclo_number": ciclo_num,
                    "scraper": "Falabella Scraper CONTINUO con BÚSQUEDAS 🔄"
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
    """Ejecutor principal del scraping continuo Falabella con búsquedas"""
    logging.info("🔄 INICIANDO SCRAPING CONTINUO DE FALABELLA CON BÚSQUEDAS")
    logging.info(f"📅 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"🔍 Total búsquedas: {len(BUSQUEDAS_CONTINUAS)}")
    logging.info(f"📋 Términos: {', '.join([b['term'] for b in BUSQUEDAS_CONTINUAS.values()])}")
    logging.info("⏱️ Intervalo: SIN ESPERA entre búsquedas")
    logging.info("📄 Páginas por ejecución: 20")
    logging.info("🔄 Modo: Rotación continua entre búsquedas")
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
            
            # SIN PAUSAS - Continuar inmediatamente con la siguiente búsqueda
            logging.info(f"➡️ Continuando inmediatamente con próxima búsqueda...")
            logging.info(f"🔜 Próxima búsqueda: {BUSQUEDAS_CONTINUAS[busqueda_keys[busqueda_index]]['name']} ('{BUSQUEDAS_CONTINUAS[busqueda_keys[busqueda_index]]['term']}')")
            
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
    print("🔄 FALABELLA SCRAPER CONTINUO CON BÚSQUEDAS")
    print(f"🔍 {len(BUSQUEDAS_CONTINUAS)} búsquedas configuradas:")
    for key, info in BUSQUEDAS_CONTINUAS.items():
        print(f"   • {info['name']}: '{info['term']}'")
    print("⏱️ Intervalo: SIN ESPERA entre ejecuciones")
    print("📄 20 páginas por búsqueda por ciclo")
    print("🔄 Rotación automática entre búsquedas")
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