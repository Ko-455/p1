import psutil
import time
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class ResourceMonitor:
    """Класс для мониторинга системных ресурсов."""
    
    def __init__(self, log_dir: str = "monitoring_logs"):
        """
        Инициализация монитора ресурсов.
        
        Args:
            log_dir: Директория для сохранения логов
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.monitoring_data: List[Dict] = []
        
    def get_memory_info(self) -> Dict:
        """
        Получает информацию об использовании памяти.
        
        Returns:
            Словарь с данными о памяти
        """
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'memory': {
                'total_mb': round(mem.total / (1024 * 1024), 2),
                'available_mb': round(mem.available / (1024 * 1024), 2),
                'used_mb': round(mem.used / (1024 * 1024), 2),
                'percent': mem.percent,
                'free_mb': round(mem.free / (1024 * 1024), 2),
                'cached_mb': round(getattr(mem, 'cached', 0) / (1024 * 1024), 2),
                'buffers_mb': round(getattr(mem, 'buffers', 0) / (1024 * 1024), 2),
            },
            'swap': {
                'total_mb': round(swap.total / (1024 * 1024), 2),
                'used_mb': round(swap.used / (1024 * 1024), 2),
                'free_mb': round(swap.free / (1024 * 1024), 2),
                'percent': swap.percent,
            }
        }
    
    def get_cpu_info(self) -> Dict:
        """
        Получает информацию о загрузке CPU.
        
        Returns:
            Словарь с данными о CPU
        """
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'total_percent': cpu_percent,
                'cores': cpu_count,
                'per_core_percent': cpu_per_core,
                'frequency_mhz': round(cpu_freq.current, 2) if cpu_freq else None,
            },
            'load_average': {
                '1min': round(psutil.getloadavg()[0], 2) if hasattr(psutil, 'getloadavg') else None,
                '5min': round(psutil.getloadavg()[1], 2) if hasattr(psutil, 'getloadavg') else None,
                '15min': round(psutil.getloadavg()[2], 2) if hasattr(psutil, 'getloadavg') else None,
            }
        }
    
    def get_process_info(self, pid: Optional[int] = None) -> List[Dict]:
        """
        Получает информацию о процессах, использующих много памяти.
        
        Args:
            pid: Если указан, возвращает информацию только об этом процессе
            
        Returns:
            Список словарей с информацией о процессах
        """
        processes = []
        
        if pid:
            try:
                proc = psutil.Process(pid)
                processes.append(self._get_process_dict(proc))
            except psutil.NoSuchProcess:
                pass
        else:
            # Получаем топ-10 процессов по использованию памяти
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
                try:
                    processes.append(self._get_process_dict(proc))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Сортируем по использованию памяти
            processes.sort(key=lambda x: x['memory_mb'], reverse=True)
            processes = processes[:10]
        
        return processes
    
    def _get_process_dict(self, proc) -> Dict:
        """Преобразует процесс в словарь."""
        try:
            mem_info = proc.memory_info()
            return {
                'pid': proc.pid,
                'name': proc.name(),
                'memory_mb': round(mem_info.rss / (1024 * 1024), 2),
                'memory_percent': proc.memory_percent(),
                'cpu_percent': proc.cpu_percent(interval=0.1),
                'status': proc.status(),
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {}
    
    def collect_snapshot(self, leak_process_pid: Optional[int] = None) -> Dict:
        """
        Собирает полный снимок состояния системы.
        
        Args:
            leak_process_pid: PID процесса с утечкой памяти (для отслеживания)
            
        Returns:
            Словарь с полной информацией о системе
        """
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            **self.get_memory_info(),
            **self.get_cpu_info(),
            'top_processes': self.get_process_info(),
        }
        
        if leak_process_pid:
            leak_process_info = self.get_process_info(leak_process_pid)
            if leak_process_info:
                snapshot['leak_process'] = leak_process_info[0]
        
        return snapshot
    
    def save_snapshot(self, snapshot: Dict):
        """
        Сохраняет снимок в файл и в память.
        
        Args:
            snapshot: Словарь с данными снимка
        """
        self.monitoring_data.append(snapshot)
        
        # Сохраняем в JSON файл
        timestamp_str = snapshot['timestamp'].replace(':', '-').split('.')[0]
        log_file = self.log_dir / f"snapshot_{timestamp_str}.json"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        
        print(f"[MONITOR] Снимок сохранён: {log_file}")
    
    def check_critical_conditions(self, snapshot: Dict) -> List[str]:
        """
        Проверяет критические условия в системе.
        
        Args:
            snapshot: Словарь с данными снимка
            
        Returns:
            Список критических предупреждений
        """
        warnings = []
        
        # Проверка памяти
        mem_percent = snapshot['memory']['percent']
        if mem_percent > 90:
            warnings.append(f"КРИТИЧНО: Использование памяти {mem_percent:.1f}%")
        elif mem_percent > 75:
            warnings.append(f"ПРЕДУПРЕЖДЕНИЕ: Использование памяти {mem_percent:.1f}%")
        
        # Проверка swap
        swap_percent = snapshot['swap']['percent']
        if swap_percent > 80:
            warnings.append(f"КРИТИЧНО: Использование swap {swap_percent:.1f}%")
        elif swap_percent > 50:
            warnings.append(f"ПРЕДУПРЕЖДЕНИЕ: Использование swap {swap_percent:.1f}%")
        
        # Проверка CPU
        cpu_percent = snapshot['cpu']['total_percent']
        if cpu_percent > 90:
            warnings.append(f"КРИТИЧНО: Загрузка CPU {cpu_percent:.1f}%")
        elif cpu_percent > 80:
            warnings.append(f"ПРЕДУПРЕЖДЕНИЕ: Загрузка CPU {cpu_percent:.1f}%")
        
        # Проверка доступной памяти
        available_mb = snapshot['memory']['available_mb']
        if available_mb < 100:
            warnings.append(f"КРИТИЧНО: Доступно памяти всего {available_mb:.1f} МБ")
        
        return warnings
    
    def get_all_data(self) -> List[Dict]:
        """Возвращает все собранные данные."""
        return self.monitoring_data

