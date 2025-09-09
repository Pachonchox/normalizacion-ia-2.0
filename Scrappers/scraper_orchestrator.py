#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 ORQUESTADOR DE SCRAPERS INTERCALADOS
Ejecuta scrapers de forma independiente y rotativa
"""

import subprocess
import time
import threading
import json
import os
from datetime import datetime
from threading import Event
import logging
import random

# Configurar logging con codificación UTF-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('../datos/scheduler/orchestrator.log', encoding='utf-8')
    ]
)

class ScraperOrchestrator:
    """Orquestador de scrapers intercalados"""
    
    def __init__(self):
        self.stop_event = Event()
        self.scrapers = {
            'ripley': {
                'script': 'ripley_proxy_rotation.py',
                'name': '🔄 Ripley Proxy Rotation',
                'status': 'idle',
                'last_run': None,
                'process': None
            },
            'falabella': {
                'script': 'falabella_busqueda_continuo.py', 
                'name': '🏪 Falabella Continuo',
                'status': 'idle',
                'last_run': None,
                'process': None
            },
            'paris': {
                'script': 'paris_busqueda_continuo.py',
                'name': '🏬 Paris Continuo', 
                'status': 'idle',
                'last_run': None,
                'process': None
            }
        }
        
        # Crear carpetas necesarias
        os.makedirs('../datos/scheduler', exist_ok=True)
        
        # Estado del orquestador
        self.cycle_count = 0
        self.start_time = None
    
    def run_scraper(self, scraper_key: str):
        """Ejecutar un scraper específico"""
        scraper_info = self.scrapers[scraper_key]
        
        try:
            logging.info(f"🚀 Iniciando {scraper_info['name']}")
            scraper_info['status'] = 'running'
            scraper_info['last_run'] = datetime.now()
            
            # Ejecutar scraper
            process = subprocess.Popen(
                ['python', scraper_info['script']],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd='.'
            )
            
            scraper_info['process'] = process
            
            # Esperar a que termine
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                logging.info(f"✅ {scraper_info['name']} completado exitosamente")
                scraper_info['status'] = 'completed'
                
                # Ejecutar filtro automático después del scraper
                self.run_auto_filter()
            else:
                logging.error(f"❌ {scraper_info['name']} falló: {stderr}")
                scraper_info['status'] = 'failed'
                
        except Exception as e:
            logging.error(f"💥 Error ejecutando {scraper_info['name']}: {e}")
            scraper_info['status'] = 'error'
        
        finally:
            scraper_info['process'] = None
    
    def run_auto_filter(self):
        """Ejecutar filtro automático de productos ruidosos"""
        try:
            logging.info("🧹 Ejecutando filtro de productos ruidosos...")
            
            # Ejecutar auto-filtro
            filter_process = subprocess.Popen(
                ['python', 'auto_filter.py', '--mode', 'once'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd='.'
            )
            
            stdout, stderr = filter_process.communicate()
            
            if filter_process.returncode == 0:
                logging.info("✅ Filtro automático completado")
            else:
                logging.warning(f"⚠️ Filtro automático reportó issues: {stderr}")
                
        except Exception as e:
            logging.error(f"💥 Error ejecutando filtro automático: {e}")
    
    def get_next_scraper(self) -> str:
        """Obtener siguiente scraper en rotación"""
        # Buscar scrapers que no estén corriendo
        idle_scrapers = [k for k, v in self.scrapers.items() if v['status'] in ['idle', 'completed', 'failed', 'error']]
        
        if not idle_scrapers:
            return None
        
        # Rotar scrapers
        if not hasattr(self, '_last_scraper_index'):
            self._last_scraper_index = -1
        
        self._last_scraper_index = (self._last_scraper_index + 1) % len(idle_scrapers)
        return idle_scrapers[self._last_scraper_index]
    
    def run_intercalated_cycle(self):
        """Ejecutar un ciclo intercalado de todos los scrapers"""
        self.cycle_count += 1
        logging.info(f"🔄 INICIANDO CICLO {self.cycle_count}")
        
        # Lista de scrapers para este ciclo
        scrapers_order = list(self.scrapers.keys())
        random.shuffle(scrapers_order)  # Orden aleatorio cada ciclo
        
        for scraper_key in scrapers_order:
            if self.stop_event.is_set():
                logging.info("🛑 Ciclo detenido por señal de parada")
                break
            
            # Ejecutar scraper
            self.run_scraper(scraper_key)
            
            # Pausa entre scrapers (5-15 minutos)
            if not self.stop_event.is_set():
                delay = random.randint(300, 900)  # 5-15 minutos
                logging.info(f"⏳ Pausa intercalada: {delay//60} minutos")
                self.stop_event.wait(delay)
        
        logging.info(f"✅ CICLO {self.cycle_count} COMPLETADO")
    
    def run_hourly_sequence(self):
        """Ejecutar secuencia FIJA: Falabella → Ripley → Paris"""
        self.cycle_count += 1
        logging.info(f"🕐 INICIANDO SECUENCIA HORARIA #{self.cycle_count}")
        logging.info(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Orden FIJO siempre el mismo
        scrapers_order = ['falabella', 'ripley', 'paris']
        
        for scraper_key in scrapers_order:
            if self.stop_event.is_set():
                logging.info("🛑 Secuencia detenida por señal de parada")
                break
            
            # Ejecutar scraper
            self.run_scraper(scraper_key)
            
            # Pausa corta entre scrapers (solo 30 segundos)
            if scraper_key != scrapers_order[-1] and not self.stop_event.is_set():
                logging.info("⏸️ Pausa entre scrapers: 30s")
                self.stop_event.wait(30)
        
        logging.info(f"✅ SECUENCIA HORARIA #{self.cycle_count} COMPLETADA")
    
    def run_continuous(self, max_cycles: int = None):
        """Ejecutar scrapers de forma continua"""
        logging.info("🚀 INICIANDO ORQUESTADOR CONTINUO")
        logging.info("=" * 50)
        
        self.start_time = datetime.now()
        
        try:
            while not self.stop_event.is_set():
                # Ejecutar ciclo intercalado
                self.run_intercalated_cycle()
                
                # Verificar límite de ciclos
                if max_cycles and self.cycle_count >= max_cycles:
                    logging.info(f"🎯 Límite de {max_cycles} ciclos alcanzado")
                    break
                
                if not self.stop_event.is_set():
                    # Pausa larga entre ciclos completos (30-60 minutos)
                    delay = random.randint(1800, 3600)  # 30-60 minutos
                    logging.info(f"😴 Pausa entre ciclos: {delay//60} minutos")
                    self.stop_event.wait(delay)
        
        except KeyboardInterrupt:
            logging.info("⚠️ Detenido por usuario")
        
        finally:
            self.stop()
    
    def run_hourly(self):
        """Ejecutar secuencia cada hora: Falabella → Ripley → Paris"""
        logging.info("🕐 INICIANDO ORQUESTADOR HORARIO")
        logging.info("📋 Secuencia FIJA: Falabella → Ripley → Paris")
        logging.info("⏰ Frecuencia: Cada hora")
        logging.info("=" * 60)
        
        self.start_time = datetime.now()
        
        try:
            while not self.stop_event.is_set():
                # Ejecutar secuencia horaria
                self.run_hourly_sequence()
                
                if not self.stop_event.is_set():
                    # Calcular tiempo hasta próxima hora
                    now = datetime.now()
                    from datetime import timedelta
                    next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                    wait_seconds = (next_hour - now).total_seconds()
                    
                    logging.info(f"⏳ Esperando hasta próxima hora: {next_hour.strftime('%H:%M')}")
                    logging.info(f"⏰ Tiempo de espera: {wait_seconds/60:.1f} minutos")
                    
                    # Esperar en chunks para poder interrumpir
                    remaining = wait_seconds
                    while remaining > 0 and not self.stop_event.is_set():
                        chunk = min(60, remaining)  # 1 minuto chunks
                        self.stop_event.wait(chunk)
                        remaining -= chunk
        
        except KeyboardInterrupt:
            logging.info("⚠️ Detenido por usuario")
        
        finally:
            self.stop()
    
    def run_single_cycle(self):
        """Ejecutar un solo ciclo de todos los scrapers"""
        logging.info("🔄 EJECUTANDO CICLO ÚNICO")
        self.start_time = datetime.now()
        self.run_intercalated_cycle()
        self.print_summary()
    
    def stop(self):
        """Detener orquestador y procesos"""
        logging.info("🛑 DETENIENDO ORQUESTADOR")
        self.stop_event.set()
        
        # Terminar procesos activos
        for scraper_key, scraper_info in self.scrapers.items():
            if scraper_info['process']:
                try:
                    scraper_info['process'].terminate()
                    logging.info(f"🔪 Terminando proceso {scraper_info['name']}")
                except:
                    pass
        
        self.print_summary()
    
    def print_summary(self):
        """Imprimir resumen de ejecución"""
        if not self.start_time:
            return
            
        duration = datetime.now() - self.start_time
        
        logging.info("=" * 50)
        logging.info("📊 RESUMEN DE EJECUCIÓN")
        logging.info("=" * 50)
        logging.info(f"⏱️  Duración total: {duration}")
        logging.info(f"🔄 Ciclos completados: {self.cycle_count}")
        
        for scraper_key, info in self.scrapers.items():
            status_emoji = {"idle": "⚪", "running": "🟡", "completed": "✅", "failed": "❌", "error": "💥"}
            emoji = status_emoji.get(info['status'], "❓")
            last_run = info['last_run'].strftime("%H:%M:%S") if info['last_run'] else "Nunca"
            logging.info(f"{emoji} {info['name']}: {info['status']} (última: {last_run})")
        
        logging.info("=" * 50)
    
    def get_status(self) -> dict:
        """Obtener estado actual del orquestador"""
        return {
            'running': not self.stop_event.is_set(),
            'cycle_count': self.cycle_count,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'scrapers': {
                k: {
                    'name': v['name'],
                    'status': v['status'],
                    'last_run': v['last_run'].isoformat() if v['last_run'] else None
                }
                for k, v in self.scrapers.items()
            }
        }

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Orquestador de scrapers intercalados')
    parser.add_argument('--mode', choices=['continuous', 'single', 'hourly', 'status'], default='single',
                       help='Modo de ejecución (default: single)')
    parser.add_argument('--max-cycles', type=int, help='Máximo número de ciclos (solo continuous)')
    parser.add_argument('--scraper', choices=['ripley', 'falabella', 'paris'], 
                       help='Ejecutar solo un scraper específico')
    
    args = parser.parse_args()
    
    orchestrator = ScraperOrchestrator()
    
    try:
        if args.mode == 'status':
            # Mostrar estado
            status = orchestrator.get_status()
            print(json.dumps(status, indent=2))
            
        elif args.scraper:
            # Ejecutar scraper específico
            logging.info(f"🎯 Ejecutando solo {args.scraper}")
            orchestrator.run_scraper(args.scraper)
            orchestrator.print_summary()
            
        elif args.mode == 'continuous':
            # Modo continuo
            orchestrator.run_continuous(max_cycles=args.max_cycles)
            
        elif args.mode == 'hourly':
            # Modo horario
            orchestrator.run_hourly()
            
        else:
            # Ciclo único (default)
            orchestrator.run_single_cycle()
    
    except KeyboardInterrupt:
        logging.info("⚠️ Interrumpido por usuario")
    finally:
        orchestrator.stop()

if __name__ == "__main__":
    main()