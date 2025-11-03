import re
import subprocess
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class KernelEventAnalyzer:
    """Класс для анализа событий ядра Linux."""
    
    def __init__(self, log_dir: str = "monitoring_logs"):
        """
        Инициализация анализатора событий ядра.
        
        Args:
            log_dir: Директория для сохранения логов
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.kernel_events: List[Dict] = []
        
        # Паттерны для поиска событий ядра
        self.oom_patterns = [
            r'Out of memory',
            r'OOM killer',
            r'oom-killer',
            r'killed process',
            r'Memory cgroup out of memory',
            r'oom_score',
        ]
        
        self.critical_patterns = [
            r'kernel.*panic',
            r'kernel.*BUG',
            r'kernel.*WARNING',
            r'kernel.*Oops',
            r'segfault',
            r'general protection fault',
            r'page allocation failure',
            r'allocation failure',
        ]
    
    def read_kernel_logs(self, lines: int = 1000) -> List[str]:
        """
        Читает логи ядра из /var/log/kern.log или dmesg.
        
        Args:
            lines: Количество последних строк для чтения
            
        Returns:
            Список строк логов
        """
        logs = []
        
        # Пробуем разные источники логов ядра
        log_sources = [
            '/var/log/kern.log',
            '/var/log/syslog',
            '/var/log/messages',
        ]
        
        for log_source in log_sources:
            if Path(log_source).exists():
                try:
                    result = subprocess.run(
                        ['tail', '-n', str(lines), log_source],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        logs.extend(result.stdout.split('\n'))
                except Exception as e:
                    print(f"[WARNING] Не удалось прочитать {log_source}: {e}")
        
        # Также используем dmesg
        try:
            result = subprocess.run(
                ['dmesg', '-T'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logs.extend(result.stdout.split('\n'))
        except Exception as e:
            print(f"[WARNING] Не удалось выполнить dmesg: {e}")
        
        return logs
    
    def analyze_oom_events(self, logs: List[str]) -> List[Dict]:
        """
        Анализирует логи на предмет событий OOM-killer.
        
        Args:
            logs: Список строк логов
            
        Returns:
            Список найденных событий OOM
        """
        oom_events = []
        
        for line in logs:
            if not line.strip():
                continue
            
            # Проверяем все паттерны OOM
            for pattern in self.oom_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    event = self._parse_oom_event(line, pattern)
                    if event:
                        oom_events.append(event)
                    break
        
        return oom_events
    
    def _parse_oom_event(self, line: str, pattern: str) -> Optional[Dict]:
        """
        Парсит строку лога для извлечения информации об OOM событии.
        
        Args:
            line: Строка лога
            pattern: Найденный паттерн
            
        Returns:
            Словарь с информацией о событии или None
        """
        try:
            # Извлекаем временную метку
            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2})', line)
            timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().isoformat()
            
            # Извлекаем PID процесса, если есть
            pid_match = re.search(r'pid\s*[=:]?\s*(\d+)', line, re.IGNORECASE)
            pid = int(pid_match.group(1)) if pid_match else None
            
            # Извлекаем имя процесса
            process_match = re.search(r'process\s+([^\s,]+)', line, re.IGNORECASE)
            process_name = process_match.group(1) if process_match else None
            
            # Извлекаем oom_score, если есть
            oom_score_match = re.search(r'oom[_-]?score[=:]?\s*(\d+)', line, re.IGNORECASE)
            oom_score = int(oom_score_match.group(1)) if oom_score_match else None
            
            # Извлекаем информацию о памяти
            memory_match = re.search(r'(\d+)\s*(kB|MB|GB|bytes)', line, re.IGNORECASE)
            memory_info = memory_match.group(0) if memory_match else None
            
            return {
                'timestamp': timestamp,
                'type': 'OOM',
                'pattern': pattern,
                'pid': pid,
                'process_name': process_name,
                'oom_score': oom_score,
                'memory_info': memory_info,
                'raw_line': line.strip(),
            }
        except Exception as e:
            print(f"[WARNING] Ошибка парсинга OOM события: {e}")
            return None
    
    def analyze_critical_events(self, logs: List[str]) -> List[Dict]:
        """
        Анализирует логи на предмет критических событий ядра.
        
        Args:
            logs: Список строк логов
            
        Returns:
            Список найденных критических событий
        """
        critical_events = []
        
        for line in logs:
            if not line.strip():
                continue
            
            for pattern in self.critical_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    event = self._parse_critical_event(line, pattern)
                    if event:
                        critical_events.append(event)
                    break
        
        return critical_events
    
    def _parse_critical_event(self, line: str, pattern: str) -> Optional[Dict]:
        """
        Парсит строку лога для извлечения информации о критическом событии.
        
        Args:
            line: Строка лога
            pattern: Найденный паттерн
            
        Returns:
            Словарь с информацией о событии или None
        """
        try:
            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2})', line)
            timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().isoformat()
            
            # Определяем тип события
            event_type = 'UNKNOWN'
            if 'panic' in pattern.lower():
                event_type = 'KERNEL_PANIC'
            elif 'bug' in pattern.lower():
                event_type = 'KERNEL_BUG'
            elif 'warning' in pattern.lower():
                event_type = 'KERNEL_WARNING'
            elif 'oops' in pattern.lower():
                event_type = 'KERNEL_OOPS'
            elif 'segfault' in pattern.lower():
                event_type = 'SEGFAULT'
            elif 'allocation failure' in pattern.lower():
                event_type = 'MEMORY_ALLOCATION_FAILURE'
            
            return {
                'timestamp': timestamp,
                'type': event_type,
                'pattern': pattern,
                'raw_line': line.strip(),
            }
        except Exception as e:
            print(f"[WARNING] Ошибка парсинга критического события: {e}")
            return None
    
    def get_oom_score(self, pid: int) -> Optional[int]:
        """
        Получает oom_score процесса из /proc/[pid]/oom_score.
        
        Args:
            pid: PID процесса
            
        Returns:
            OOM score или None
        """
        try:
            oom_score_path = Path(f'/proc/{pid}/oom_score')
            if oom_score_path.exists():
                with open(oom_score_path, 'r') as f:
                    return int(f.read().strip())
        except Exception as e:
            print(f"[WARNING] Не удалось прочитать oom_score для PID {pid}: {e}")
        
        return None
    
    def get_oom_score_adj(self, pid: int) -> Optional[int]:
        """
        Получает oom_score_adj процесса из /proc/[pid]/oom_score_adj.
        
        Args:
            pid: PID процесса
            
        Returns:
            OOM score adj или None
        """
        try:
            oom_score_adj_path = Path(f'/proc/{pid}/oom_score_adj')
            if oom_score_adj_path.exists():
                with open(oom_score_adj_path, 'r') as f:
                    return int(f.read().strip())
        except Exception as e:
            print(f"[WARNING] Не удалось прочитать oom_score_adj для PID {pid}: {e}")
        
        return None
    
    def analyze_all_events(self) -> Dict:
        """
        Выполняет полный анализ всех событий ядра.
        
        Returns:
            Словарь с результатами анализа
        """
        logs = self.read_kernel_logs()
        oom_events = self.analyze_oom_events(logs)
        critical_events = self.analyze_critical_events(logs)
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'total_log_lines': len(logs),
            'oom_events': oom_events,
            'critical_events': critical_events,
            'oom_events_count': len(oom_events),
            'critical_events_count': len(critical_events),
        }
        
        self.kernel_events.append(analysis)
        return analysis
    
    def save_analysis(self, analysis: Dict):
        """
        Сохраняет результаты анализа в файл.
        
        Args:
            analysis: Словарь с результатами анализа
        """
        timestamp_str = analysis['timestamp'].replace(':', '-').split('.')[0]
        log_file = self.log_dir / f"kernel_analysis_{timestamp_str}.json"
        
        import json
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        print(f"[ANALYZER] Анализ ядра сохранён: {log_file}")


