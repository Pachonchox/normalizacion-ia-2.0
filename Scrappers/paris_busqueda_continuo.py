"""
🔄 París Scraper CONTINUO con BÚSQUEDAS
Sistema que ejecuta búsquedas cada 10 minutos de forma rotativa
Busca términos específicos y extrae 5 páginas por búsqueda
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
output_log_dir = r"D:\Normalizacion IA 2.0\datos\paris"
os.makedirs(output_log_dir, exist_ok=True)
log_file_path = os.path.join(output_log_dir, 'paris_busqueda_continuo.log')

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

# === CONFIGURACIÓN DE BÚSQUEDAS CONTINUAS (PRUEBA: 3 CATEGORÍAS) ===
BUSQUEDAS_CONTINUAS = {
    "smartphone": {
        "term": "smartphone",
        "name": "📱 Smartphones"
    },
    "notebook": {
        "term": "notebook",
        "name": "💻 Notebooks"
    },
    "perfume": {
        "term": "perfume",
        "name": "🌸 Perfumes"
    }
}

# Comuna por defecto (Las Condes)
COMUNA_DEFAULT = "13114"

def setup_driver_continuo():
    """Driver optimizado para operación continua París"""
    logging.info("🔄 Configurando Chrome para operación continua París...")
    
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
    chrome_options.add_argument("--disable-images")
    
    # Configuraciones de memoria - París necesita JS y CSS
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.media_stream": 2,
        "profile.managed_default_content_settings.stylesheets": 1,  # París necesita CSS
        "profile.managed_default_content_settings.cookies": 1,
        "profile.managed_default_content_settings.javascript": 1,  # París necesita JS
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
    
    logging.info("✅ Driver continuo París configurado")
    return driver

def extract_products_continuo(soup, page_num, search_term):
    """Extracción optimizada para búsquedas en París"""
    products = []
    
    # Buscar la grilla principal de productos
    grid = soup.select_one('div[class*="grid grid-cols-"]')
    
    if not grid:
        # Busqueda alternativa
        grid = soup.select_one('div.grid')
    
    if grid:
        # Obtener todos los hijos directos de la grilla (cada uno es un producto)
        containers = grid.find_all('div', recursive=False)
    else:
        # Fallback a selectores alternativos
        containers = soup.select('div[class*="h-full"]')
    
    logging.info(f"📦 Búsqueda '{search_term}' P{page_num}: {len(containers)} productos")
    
    for i, container in enumerate(containers, 1):
        try:
            # === DATOS ESENCIALES ===
            product_name = ""
            product_code = ""
            product_link = ""
            brand = ""
            
            # Link del producto
            link_elem = container.select_one('a')
            if link_elem:
                href = link_elem.get('href', '')
                if href:
                    product_link = f"https://www.paris.cl{href}" if href.startswith('/') else href
                    # Extraer código del link
                    if '.html' in href:
                        # Formato: /nombre-producto-codigo.html
                        parts = href.split('-')
                        if parts:
                            code_part = parts[-1].replace('.html', '')
                            product_code = code_part if code_part else f"PARIS_{i:04d}"
            
            # Nombre del producto - Método 1: span.ui-text-xs (selector específico París)
            name_elem = container.select_one('span.ui-text-xs')
            if name_elem:
                product_name = name_elem.get_text(strip=True)
            
            # Método 2: desde imagen
            if not product_name:
                img_elem = container.select_one('img')
                if img_elem:
                    alt_text = img_elem.get('alt', '')
                    if alt_text and alt_text != '...':
                        product_name = alt_text
            
            # Método 3: buscar en otros elementos de texto
            if not product_name:
                for selector in ['h2', 'h3', 'p[class*="text-"]', 'span[class*="text-"]']:
                    name_elems = container.select(selector)
                    for elem in name_elems:
                        text = elem.get_text(strip=True)
                        # Filtrar textos válidos para nombres
                        if (len(text) > 10 and not text.startswith('$') and 
                            not text.isdigit() and 'Vista Previa' not in text and
                            'Cupón' not in text and 'Agregar' not in text):
                            product_name = text
                            break
                    if product_name:
                        break
            
            # Método 4: desde URL si no hay nombre
            if not product_name and product_link:
                # Extraer nombre del slug de la URL
                if '/p/' in product_link:
                    slug = product_link.split('/p/')[-1].split('/')[0]
                elif '.html' in product_link:
                    slug = product_link.split('/')[-1].replace('.html', '')
                    # Limpiar el código al final
                    parts = slug.rsplit('-', 1)
                    if parts and parts[0]:
                        slug = parts[0]
                else:
                    slug = ''
                
                if slug:
                    # Convertir slug a nombre legible
                    product_name = slug.replace('-', ' ').title()
            
            # Buscar marca en el texto del producto
            text_content = container.get_text()
            common_brands = ['SAMSUNG', 'APPLE', 'XIAOMI', 'HUAWEI', 'MOTOROLA', 'LG', 'SONY', 'HONOR', 'OPPO', 'REALME', 'NOKIA', 'ALCATEL']
            for b in common_brands:
                if b in text_content.upper():
                    brand = b
                    break
            
            if not product_name:
                continue
            
            # === PRECIOS OPTIMIZADOS (3 niveles París) ===
            card_price_text = ""
            card_price_numeric = None
            normal_price_text = ""
            normal_price_numeric = None
            original_price_text = ""
            original_price_numeric = None
            
            # Buscar todos los elementos con precios
            price_pattern = re.compile(r'\$[\s]*[\d.,]+')
            price_elements = []
            
            # Buscar elementos que contienen precios
            for elem in container.find_all(string=price_pattern):
                price_text = elem.strip()
                parent = elem.parent
                if parent:
                    parent_classes = ' '.join(parent.get('class', []))
                    
                    # Clasificar el precio
                    is_strikethrough = 'line-through' in parent_classes
                    is_bold = 'font-bold' in parent_classes or 'font-semibold' in parent_classes
                    
                    # Buscar icono de tarjeta
                    has_card_icon = False
                    next_elem = parent.find_next_sibling()
                    if next_elem and next_elem.name == 'svg':
                        has_card_icon = True
                    
                    price_elements.append({
                        'text': price_text,
                        'numeric': int(re.sub(r'[^\d]', '', price_text)) if price_text else None,
                        'strikethrough': is_strikethrough,
                        'bold': is_bold,
                        'card_icon': has_card_icon
                    })
            
            # Asignar precios según su tipo
            for price in price_elements:
                if price['strikethrough'] and not original_price_text:
                    original_price_text = price['text']
                    original_price_numeric = price['numeric']
                elif price['card_icon'] and not card_price_text:
                    card_price_text = price['text']
                    card_price_numeric = price['numeric']
                elif not normal_price_text and not price['strikethrough']:
                    normal_price_text = price['text']
                    normal_price_numeric = price['numeric']
            
            # Si hay más de 2 precios sin clasificar, el primero es tarjeta
            if len(price_elements) >= 3 and not card_price_text:
                card_price_text = price_elements[0]['text']
                card_price_numeric = price_elements[0]['numeric']
                if not normal_price_text:
                    normal_price_text = price_elements[1]['text']
                    normal_price_numeric = price_elements[1]['numeric']
                if not original_price_text:
                    original_price_text = price_elements[2]['text']
                    original_price_numeric = price_elements[2]['numeric']
            
            # Buscar descuento si existe
            discount_text = ""
            for elem in container.select('span[class*="bg-"], div[class*="bg-"]'):
                text = elem.get_text(strip=True)
                if '%' in text:
                    discount_text = text
                    break
            
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
    """Scraping de una búsqueda París en modo continuo"""
    logging.info(f"🔄 CICLO {ciclo_num} - Iniciando búsqueda: {search_info['name']}")
    
    driver = None
    all_products = []
    
    try:
        driver = setup_driver_continuo()
        
        # Scrapear 5 páginas por búsqueda
        for page_num in range(1, 6):  # 5 páginas
            if stop_event.is_set():
                logging.info("🛑 Deteniendo por señal de parada")
                break
            
            # Construir URL de búsqueda París
            if page_num == 1:
                url = f"https://www.paris.cl/search/?q={search_info['term']}&commune={COMUNA_DEFAULT}"
            else:
                url = f"https://www.paris.cl/search/?q={search_info['term']}&page={page_num}&commune={COMUNA_DEFAULT}"
            
            logging.info(f"📄 {search_info['name']} - Página {page_num}/3")
            logging.info(f"🔗 URL: {url}")
            
            try:
                driver.get(url)
                time.sleep(3)
                
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
                    product['commune'] = COMUNA_DEFAULT
                
                all_products.extend(page_products)
                
                if not page_products:
                    logging.warning(f"⚠️ Sin productos en página {page_num}")
                    if page_num > 2:
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
                    "base_url": f"https://www.paris.cl/search/?q={search_info['term']}&commune={COMUNA_DEFAULT}",
                    "total_products": len(all_products),
                    "pages_scraped": len(set(p['page_scraped'] for p in all_products)),
                    "ciclo_number": ciclo_num,
                    "commune": COMUNA_DEFAULT,
                    "scraper": "París Scraper CONTINUO con BÚSQUEDAS 🔄"
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
    """Ejecutor principal del scraping continuo París con búsquedas"""
    logging.info("🔄 INICIANDO SCRAPING CONTINUO DE PARÍS CON BÚSQUEDAS")
    logging.info(f"📅 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"🔍 Total búsquedas: {len(BUSQUEDAS_CONTINUAS)}")
    logging.info(f"📋 Términos: {', '.join([b['term'] for b in BUSQUEDAS_CONTINUAS.values()])}")
    logging.info(f"📍 Comuna: {COMUNA_DEFAULT} (Las Condes)")
    logging.info("⏱️ Intervalo: 10 minutos entre categorías")
    logging.info("📄 Páginas por ejecución: 10")
    logging.info("🔄 Modo: Rotación continua entre búsquedas")
    logging.info("="*70)
    
    ciclo_num = 1
    busqueda_keys = list(BUSQUEDAS_CONTINUAS.keys())
    busqueda_index = 0
    
    try:
        # Ejecutar cada búsqueda una vez (ciclo único completo)
        for search_key in busqueda_keys:
            if stop_event.is_set():
                break
                
            search_info = BUSQUEDAS_CONTINUAS[search_key]
            
            start_time = time.time()
            
            # Ejecutar scraping de la búsqueda
            productos_extraidos = scrape_busqueda_continuo(search_key, search_info, ciclo_num)
            
            execution_time = time.time() - start_time
            
            logging.info(f"⏱️ BÚSQUEDA {search_key} completada en {execution_time:.2f}s")
            logging.info(f"📊 Productos extraídos: {productos_extraidos}")
            logging.info("-" * 50)
            
            ciclo_num += 1
            
            # Pausa entre búsquedas (solo si no es la última)
            if search_key != busqueda_keys[-1] and not stop_event.is_set():
                logging.info(f"⏸️ Pausa entre búsquedas: 30s")
                time.sleep(30)
    
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
    print("🔄 PARÍS SCRAPER CONTINUO CON BÚSQUEDAS")
    print(f"🔍 {len(BUSQUEDAS_CONTINUAS)} búsquedas configuradas:")
    for key, info in BUSQUEDAS_CONTINUAS.items():
        print(f"   • {info['name']}: '{info['term']}'")
    print(f"📍 Comuna: {COMUNA_DEFAULT} (Las Condes)")
    print("⏱️ Intervalo: 10 minutos entre categorías")
    print("📄 5 páginas por búsqueda por ciclo")
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