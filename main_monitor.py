import sys
import time
import signal
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

from resource_monitor import ResourceMonitor
from kernel_event_analyzer import KernelEventAnalyzer
from report_generator import ReportGenerator


class SystemMonitor:
    """Главный класс для мониторинга системы."""
    
    def __init__(
        self,
        interval_minutes: int = 5,
        leak_process_pid: int = None,
        log_dir: str = "monitoring_logs",
        report_dir: str = "reports"
    ):
        """
        Инициализация монитора системы.
        
        Args:
            interval_minutes: Интервал мониторинга в минутах
            leak_process_pid: PID процесса с утечкой памяти (опционально)
            log_dir: Директория для логов
            report_dir: Директория для отчётов
        """
        self.interval_seconds = interval_minutes * 60
        self.leak_process_pid = leak_process_pid
        self.running = False
        
        self.resource_monitor = ResourceMonitor(log_dir)
        self.kernel_analyzer = KernelEventAnalyzer(log_dir)
        self.report_generator = ReportGenerator(report_dir)
        
        # Регистрируем обработчик сигналов
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения."""
        print(f"\n[INFO] Получен сигнал {signum}. Завершение работы...")
        self.running = False
    
    def start_monitoring(self):
        """Запускает автоматический мониторинг."""
        self.running = True
        iteration = 0
        
        print("=" * 80)
        print("СИСТЕМА МОНИТОРИНГА РЕСУРСОВ ОС")
        print("=" * 80)
        print(f"Интервал мониторинга: {self.interval_seconds / 60} минут")
        print(f"PID процесса с утечкой: {self.leak_process_pid or 'не указан'}")
        print("Нажмите Ctrl+C для остановки")
        print("=" * 80)
        
        try:
            while self.running:
                iteration += 1
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                      f"Итерация мониторинга #{iteration}")
                print("-" * 80)
                
                # Сбор данных о ресурсах
                print("[MONITOR] Сбор данных о ресурсах системы...")
                snapshot = self.resource_monitor.collect_snapshot(self.leak_process_pid)
                self.resource_monitor.save_snapshot(snapshot)
                
                # Проверка критических условий
                warnings = self.resource_monitor.check_critical_conditions(snapshot)
                if warnings:
                    print("[WARNING] Обнаружены критические условия:")
                    for warning in warnings:
                        print(f"  - {warning}")
                
                # Анализ событий ядра
                print("[ANALYZER] Анализ событий ядра...")
                kernel_analysis = self.kernel_analyzer.analyze_all_events()
                self.kernel_analyzer.save_analysis(kernel_analysis)
                
                if kernel_analysis['oom_events_count'] > 0:
                    print(f"[CRITICAL] Обнаружено {kernel_analysis['oom_events_count']} OOM событий!")
                
                if kernel_analysis['critical_events_count'] > 0:
                    print(f"[CRITICAL] Обнаружено {kernel_analysis['critical_events_count']} критических событий!")
                
                # Генерация промежуточного отчёта каждые 5 итераций
                if iteration % 5 == 0:
                    print("[REPORT] Генерация промежуточного отчёта...")
                    self._generate_report()
                
                # Ожидание следующего цикла
                if self.running:
                    print(f"[INFO] Ожидание {self.interval_seconds / 60} минут до следующего цикла...")
                    for _ in range(self.interval_seconds):
                        if not self.running:
                            break
                        time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n[INFO] Прерывание по запросу пользователя")
        except Exception as e:
            print(f"\n[ERROR] Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Останавливает мониторинг и генерирует финальный отчёт."""
        self.running = False
        print("\n" + "=" * 80)
        print("ОСТАНОВКА МОНИТОРИНГА")
        print("=" * 80)
        
        print("[REPORT] Генерация финального диагностического отчёта...")
        self._generate_report()
        
        print("[INFO] Мониторинг завершён")
    
    def _generate_report(self):
        """Генерирует диагностический отчёт."""
        monitoring_data = self.resource_monitor.get_all_data()
        kernel_events = self.kernel_analyzer.kernel_events
        
        if not monitoring_data:
            print("[WARNING] Нет данных для генерации отчёта")
            return
        
        report = self.report_generator.generate_report(
            monitoring_data,
            kernel_events,
            self.leak_process_pid
        )
        
        report_path = self.report_generator.save_report(report, format='both')
        print(f"[REPORT] Отчёт сохранён: {report_path}")


def start_leak_process(rate: int = 50, interval: float = 1.0) -> int:
    """
    Запускает процесс с утечкой памяти в фоновом режиме.
    
    Args:
        rate: Количество МБ для выделения за раз
        interval: Интервал между выделениями в секундах
        
    Returns:
        PID запущенного процесса
    """
    script_path = Path(__file__).parent / "memory_leak_simulator.py"
    
    process = subprocess.Popen(
        [sys.executable, str(script_path), '--rate', str(rate), '--interval', str(interval)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    return process.pid


def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(
        description='Система мониторинга ресурсов ОС (только для виртуальных машин!)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Интервал мониторинга в минутах (по умолчанию: 5)'
    )
    parser.add_argument(
        '--leak-pid',
        type=int,
        default=None,
        help='PID процесса с утечкой памяти (если уже запущен)'
    )
    parser.add_argument(
        '--start-leak',
        action='store_true',
        help='Запустить процесс с утечкой памяти автоматически'
    )
    parser.add_argument(
        '--leak-rate',
        type=int,
        default=50,
        help='Количество МБ для выделения за раз при автоматическом запуске (по умолчанию: 50)'
    )
    parser.add_argument(
        '--leak-interval',
        type=float,
        default=1.0,
        help='Интервал между выделениями памяти в секундах (по умолчанию: 1.0)'
    )
    parser.add_argument(
        '--log-dir',
        type=str,
        default='monitoring_logs',
        help='Директория для логов (по умолчанию: monitoring_logs)'
    )
    parser.add_argument(
        '--report-dir',
        type=str,
        default='reports',
        help='Директория для отчётов (по умолчанию: reports)'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("СИСТЕМА МОНИТОРИНГА РЕСУРСОВ ОС")
    print("=" * 80)
    print("ВНИМАНИЕ: Этот скрипт предназначен для работы в виртуальной машине!")
    print("Работа OOM-killer может привести к нестабильности системы!")
    print("=" * 80)
    
    leak_pid = args.leak_pid
    
    # Запуск процесса с утечкой памяти, если требуется
    if args.start_leak:
        print("[INFO] Запуск процесса с утечкой памяти...")
        leak_pid = start_leak_process(args.leak_rate, args.leak_interval)
        print(f"[INFO] Процесс с утечкой памяти запущен: PID {leak_pid}")
        time.sleep(2)  # Даём процессу время на запуск
    
    # Запуск мониторинга
    monitor = SystemMonitor(
        interval_minutes=args.interval,
        leak_process_pid=leak_pid,
        log_dir=args.log_dir,
        report_dir=args.report_dir
    )
    
    try:
        monitor.start_monitoring()
    except Exception as e:
        print(f"[FATAL] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

