#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕐 ORQUESTADOR HORARIO DE SCRAPERS
Ejecuta secuencialmente: Falabella → Ripley → Paris cada hora
Intervención mínima sin modificar lógica de extracción
"""

import os
import sys
import time
import subprocess
import logging
from datetime import datetime, timedelta
import signal
import threading

# Configurar logging
log_dir = r"D:\Normalizacion IA 2.0\datos\scheduler"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'hourly_scheduler.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

class HourlyScrapingScheduler:
    """Orquestador que ejecuta scrapers secuencialmente cada hora"""
    
    def __init__(self):
        self.running = True
        self.current_cycle = 1
        self.scrapers_dir = os.path.dirname(__file__)
        
        # Configuración de scrapers (orden de ejecución)
        self.scrapers = [
            {
                "name": "Falabella",
                "script": "falabella_busqueda_continuo.py", 
                "timeout": 1200  # 20 minutos máximo
            },
            {
                "name": "Ripley",
                "script": "ripley_ultra_stealth_v3.py",
                "timeout": 1200  # 20 minutos máximo  
            },
            {
                "name": "Paris", 
                "script": "paris_busqueda_continuo.py",
                "timeout": 1200  # 20 minutos máximo
            }
        ]
        
        # Handler para Ctrl+C
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Manejo de señal de interrupción"""
        logging.info("⚠️ Recibida señal de interrupción")
        self.running = False
    
    def execute_scraper(self, scraper_config):
        """Ejecutar un scraper individual"""
        script_path = os.path.join(self.scrapers_dir, scraper_config["script"])
        scraper_name = scraper_config["name"]
        timeout = scraper_config["timeout"]
        
        logging.info(f"🚀 Iniciando {scraper_name}...")
        start_time = time.time()
        
        try:
            # Ejecutar scraper como subproceso
            result = subprocess.run(
                [sys.executable, script_path],
                cwd=self.scrapers_dir,
                timeout=timeout,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                logging.info(f"✅ {scraper_name} completado exitosamente ({execution_time:.1f}s)")
                return True
            else:
                logging.error(f"❌ {scraper_name} falló (código {result.returncode})")
                if result.stderr:
                    logging.error(f"Error: {result.stderr[:500]}")
                return False
                
        except subprocess.TimeoutExpired:
            logging.error(f"⏰ {scraper_name} excedió timeout ({timeout}s)")
            return False
        except Exception as e:
            execution_time = time.time() - start_time
            logging.error(f"💥 Error ejecutando {scraper_name}: {e} ({execution_time:.1f}s)")
            return False
    
    def execute_cycle(self):
        """Ejecutar un ciclo completo: Falabella → Ripley → Paris"""
        cycle_start = time.time()
        logging.info(f"🔄 INICIANDO CICLO #{self.current_cycle}")
        logging.info(f"📅 Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("=" * 60)
        
        results = {}
        
        for scraper_config in self.scrapers:
            scraper_name = scraper_config["name"]
            success = self.execute_scraper(scraper_config)
            results[scraper_name] = success
            
            # Pausa entre scrapers (para no sobrecargar)
            if scraper_name != self.scrapers[-1]["name"]:  # No pausar después del último
                logging.info("⏸️ Pausa entre scrapers: 30s")
                time.sleep(30)
        
        cycle_time = time.time() - cycle_start
        
        # Resumen del ciclo
        logging.info("=" * 60)
        logging.info(f"📊 RESUMEN CICLO #{self.current_cycle}")
        
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        for scraper_name, success in results.items():
            status = "✅ ÉXITO" if success else "❌ FALLO"
            logging.info(f"  {scraper_name}: {status}")
        
        logging.info(f"⏱️ Tiempo total ciclo: {cycle_time:.1f}s ({cycle_time/60:.1f} min)")
        logging.info(f"🎯 Scrapers exitosos: {successful}/{total}")
        
        self.current_cycle += 1
        return successful == total
    
    def calculate_next_hour(self):
        """Calcular cuánto tiempo falta para la próxima hora en punto"""
        now = datetime.now()
        next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        wait_seconds = (next_hour - now).total_seconds()
        return wait_seconds, next_hour
    
    def run(self):
        """Bucle principal del scheduler"""
        logging.info("🕐 INICIANDO ORQUESTADOR HORARIO DE SCRAPERS")
        logging.info("📋 Secuencia: Falabella → Ripley → Paris")
        logging.info("⏰ Frecuencia: Cada hora en punto")
        logging.info("🛑 Detener con Ctrl+C")
        logging.info("=" * 60)
        
        while self.running:
            try:
                # Ejecutar ciclo completo
                cycle_success = self.execute_cycle()
                
                if not self.running:
                    break
                
                # Calcular espera hasta próxima hora
                wait_seconds, next_execution = self.calculate_next_hour()
                
                if wait_seconds > 0:
                    logging.info(f"⏳ Esperando hasta próxima ejecución: {next_execution.strftime('%H:%M:%S')}")
                    logging.info(f"⏰ Tiempo de espera: {wait_seconds/60:.1f} minutos")
                    
                    # Esperar en chunks de 60 segundos para poder interrumpir
                    remaining = wait_seconds
                    while remaining > 0 and self.running:
                        chunk = min(60, remaining)
                        time.sleep(chunk)
                        remaining -= chunk
                        
                        if remaining > 0:
                            logging.info(f"⏳ Esperando... {remaining/60:.1f} min restantes")
                else:
                    logging.info("⚡ Ejecutando inmediatamente (ya es hora de ejecutar)")
                
            except KeyboardInterrupt:
                logging.info("⚠️ Interrupción recibida")
                self.running = False
            except Exception as e:
                logging.error(f"💥 Error crítico en scheduler: {e}")
                logging.info("⏸️ Esperando 5 minutos antes de reintentar...")
                time.sleep(300)  # 5 minutos
        
        logging.info("🏁 ORQUESTADOR HORARIO FINALIZADO")
        logging.info(f"📊 Total ciclos ejecutados: {self.current_cycle - 1}")

def main():
    """Función principal"""
    try:
        scheduler = HourlyScrapingScheduler()
        scheduler.run()
    except Exception as e:
        logging.error(f"💥 Error crítico: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())