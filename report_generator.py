import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict


class ReportGenerator:
    """Класс для генерации диагностических отчётов."""
    
    def __init__(self, output_dir: str = "reports"):
        """
        Инициализация генератора отчётов.
        
        Args:
            output_dir: Директория для сохранения отчётов
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_report(
        self,
        monitoring_data: List[Dict],
        kernel_events: List[Dict],
        leak_process_pid: Optional[int] = None
    ) -> Dict:
        """
        Генерирует полный диагностический отчёт.
        
        Args:
            monitoring_data: Данные мониторинга ресурсов
            kernel_events: События ядра
            leak_process_pid: PID процесса с утечкой памяти
            
        Returns:
            Словарь с отчётом
        """
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'monitoring_periods': len(monitoring_data),
                'kernel_analyses': len(kernel_events),
            },
            'executive_summary': self._generate_executive_summary(
                monitoring_data, kernel_events
            ),
            'memory_analysis': self._analyze_memory(monitoring_data),
            'cpu_analysis': self._analyze_cpu(monitoring_data),
            'swap_analysis': self._analyze_swap(monitoring_data),
            'critical_events': self._analyze_critical_events(monitoring_data, kernel_events),
            'oom_analysis': self._analyze_oom_events(kernel_events),
            'resource_exhaustion': self._analyze_resource_exhaustion(monitoring_data),
            'recommendations': self._generate_recommendations(
                monitoring_data, kernel_events
            ),
        }
        
        if leak_process_pid:
            report['leak_process_tracking'] = self._track_leak_process(
                monitoring_data, leak_process_pid
            )
        
        return report
    
    def _generate_executive_summary(
        self,
        monitoring_data: List[Dict],
        kernel_events: List[Dict]
    ) -> Dict:
        """Генерирует краткое резюме."""
        if not monitoring_data:
            return {'status': 'Нет данных для анализа'}
        
        # Анализ пиковых значений
        max_memory = max([d['memory']['percent'] for d in monitoring_data])
        max_cpu = max([d['cpu']['total_percent'] for d in monitoring_data])
        max_swap = max([d['swap']['percent'] for d in monitoring_data])
        
        # Подсчёт критических событий
        total_oom = sum([e.get('oom_events_count', 0) for e in kernel_events])
        total_critical = sum([e.get('critical_events_count', 0) for e in kernel_events])
        
        status = 'NORMAL'
        if max_memory > 90 or max_swap > 80 or total_oom > 0:
            status = 'CRITICAL'
        elif max_memory > 75 or max_swap > 50 or total_critical > 0:
            status = 'WARNING'
        
        return {
            'status': status,
            'monitoring_duration': f"{len(monitoring_data)} периодов",
            'peak_memory_usage': f"{max_memory:.1f}%",
            'peak_cpu_usage': f"{max_cpu:.1f}%",
            'peak_swap_usage': f"{max_swap:.1f}%",
            'total_oom_events': total_oom,
            'total_critical_events': total_critical,
        }
    
    def _analyze_memory(self, monitoring_data: List[Dict]) -> Dict:
        """Анализирует использование памяти."""
        if not monitoring_data:
            return {}
        
        memory_percents = [d['memory']['percent'] for d in monitoring_data]
        available_mbs = [d['memory']['available_mb'] for d in monitoring_data]
        
        return {
            'average_usage_percent': round(sum(memory_percents) / len(memory_percents), 2),
            'max_usage_percent': round(max(memory_percents), 2),
            'min_usage_percent': round(min(memory_percents), 2),
            'min_available_mb': round(min(available_mbs), 2),
            'memory_pressure_periods': len([m for m in memory_percents if m > 75]),
            'critical_periods': len([m for m in memory_percents if m > 90]),
            'trend': self._calculate_trend(memory_percents),
        }
    
    def _analyze_cpu(self, monitoring_data: List[Dict]) -> Dict:
        """Анализирует использование CPU."""
        if not monitoring_data:
            return {}
        
        cpu_percents = [d['cpu']['total_percent'] for d in monitoring_data]
        
        return {
            'average_usage_percent': round(sum(cpu_percents) / len(cpu_percents), 2),
            'max_usage_percent': round(max(cpu_percents), 2),
            'min_usage_percent': round(min(cpu_percents), 2),
            'high_load_periods': len([c for c in cpu_percents if c > 80]),
            'critical_periods': len([c for c in cpu_percents if c > 90]),
            'trend': self._calculate_trend(cpu_percents),
        }
    
    def _analyze_swap(self, monitoring_data: List[Dict]) -> Dict:
        """Анализирует использование swap."""
        if not monitoring_data:
            return {}
        
        swap_percents = [d['swap']['percent'] for d in monitoring_data]
        swap_used_mbs = [d['swap']['used_mb'] for d in monitoring_data]
        
        return {
            'average_usage_percent': round(sum(swap_percents) / len(swap_percents), 2),
            'max_usage_percent': round(max(swap_percents), 2),
            'max_used_mb': round(max(swap_used_mbs), 2),
            'swap_activity_periods': len([s for s in swap_percents if s > 50]),
            'critical_periods': len([s for s in swap_percents if s > 80]),
            'trend': self._calculate_trend(swap_percents),
        }
    
    def _analyze_critical_events(
        self,
        monitoring_data: List[Dict],
        kernel_events: List[Dict]
    ) -> Dict:
        """Анализирует критические события."""
        critical_events_list = []
        
        # Критические события из мониторинга
        for snapshot in monitoring_data:
            warnings = []
            if snapshot['memory']['percent'] > 90:
                warnings.append(f"Критическое использование памяти: {snapshot['memory']['percent']:.1f}%")
            if snapshot['swap']['percent'] > 80:
                warnings.append(f"Критическое использование swap: {snapshot['swap']['percent']:.1f}%")
            if snapshot['cpu']['total_percent'] > 90:
                warnings.append(f"Критическая загрузка CPU: {snapshot['cpu']['total_percent']:.1f}%")
            
            if warnings:
                critical_events_list.append({
                    'timestamp': snapshot['timestamp'],
                    'type': 'RESOURCE_CRITICAL',
                    'warnings': warnings,
                })
        
        # Критические события из ядра
        for kernel_analysis in kernel_events:
            for event in kernel_analysis.get('critical_events', []):
                critical_events_list.append(event)
        
        return {
            'total_critical_events': len(critical_events_list),
            'events': critical_events_list[:50],  # Ограничиваем до 50 событий
        }
    
    def _analyze_oom_events(self, kernel_events: List[Dict]) -> Dict:
        """Анализирует события OOM-killer."""
        all_oom_events = []
        
        for kernel_analysis in kernel_events:
            all_oom_events.extend(kernel_analysis.get('oom_events', []))
        
        if not all_oom_events:
            return {
                'oom_events_detected': False,
                'total_oom_events': 0,
            }
        
        # Группируем по процессам
        processes_killed = defaultdict(int)
        for event in all_oom_events:
            if event.get('process_name'):
                processes_killed[event['process_name']] += 1
        
        return {
            'oom_events_detected': True,
            'total_oom_events': len(all_oom_events),
            'processes_killed': dict(processes_killed),
            'recent_oom_events': all_oom_events[-10:],  # Последние 10 событий
        }
    
    def _analyze_resource_exhaustion(self, monitoring_data: List[Dict]) -> Dict:
        """Анализирует случаи исчерпания ресурсов."""
        if not monitoring_data:
            return {}
        
        exhaustion_events = []
        
        for snapshot in monitoring_data:
            events = []
            
            # Исчерпание памяти
            if snapshot['memory']['available_mb'] < 50:
                events.append({
                    'resource': 'MEMORY',
                    'available_mb': snapshot['memory']['available_mb'],
                    'severity': 'CRITICAL',
                })
            
            # Исчерпание swap
            if snapshot['swap']['free_mb'] < 100 and snapshot['swap']['total_mb'] > 0:
                events.append({
                    'resource': 'SWAP',
                    'free_mb': snapshot['swap']['free_mb'],
                    'severity': 'WARNING',
                })
            
            if events:
                exhaustion_events.append({
                    'timestamp': snapshot['timestamp'],
                    'events': events,
                })
        
        return {
            'exhaustion_events_count': len(exhaustion_events),
            'events': exhaustion_events,
        }
    
    def _track_leak_process(
        self,
        monitoring_data: List[Dict],
        leak_process_pid: int
    ) -> Dict:
        """Отслеживает процесс с утечкой памяти."""
        leak_history = []
        
        for snapshot in monitoring_data:
            if 'leak_process' in snapshot:
                leak_history.append({
                    'timestamp': snapshot['timestamp'],
                    'memory_mb': snapshot['leak_process'].get('memory_mb', 0),
                    'memory_percent': snapshot['leak_process'].get('memory_percent', 0),
                    'cpu_percent': snapshot['leak_process'].get('cpu_percent', 0),
                })
        
        if not leak_history:
            return {'status': 'Процесс не найден в данных мониторинга'}
        
        return {
            'pid': leak_process_pid,
            'history': leak_history,
            'max_memory_mb': max([h['memory_mb'] for h in leak_history]),
            'memory_growth': leak_history[-1]['memory_mb'] - leak_history[0]['memory_mb'],
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Вычисляет тренд значений."""
        if len(values) < 2:
            return 'INSUFFICIENT_DATA'
        
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        diff = avg_second - avg_first
        
        if abs(diff) < 1:
            return 'STABLE'
        elif diff > 5:
            return 'INCREASING'
        elif diff < -5:
            return 'DECREASING'
        else:
            return 'SLIGHTLY_INCREASING' if diff > 0 else 'SLIGHTLY_DECREASING'
    
    def _generate_recommendations(
        self,
        monitoring_data: List[Dict],
        kernel_events: List[Dict]
    ) -> List[str]:
        """Генерирует рекомендации на основе анализа."""
        recommendations = []
        
        if not monitoring_data:
            return ['Недостаточно данных для генерации рекомендаций']
        
        # Анализ памяти
        max_memory = max([d['memory']['percent'] for d in monitoring_data])
        if max_memory > 90:
            recommendations.append(
                "КРИТИЧНО: Использование памяти превышало 90%. "
                "Рассмотрите возможность увеличения объёма RAM или оптимизации приложений."
            )
        
        # Анализ swap
        max_swap = max([d['swap']['percent'] for d in monitoring_data])
        if max_swap > 80:
            recommendations.append(
                "КРИТИЧНО: Использование swap превышало 80%. "
                "Система активно использует swap, что может привести к деградации производительности."
            )
        
        # Анализ OOM событий
        total_oom = sum([e.get('oom_events_count', 0) for e in kernel_events])
        if total_oom > 0:
            recommendations.append(
                f"ОБНАРУЖЕНО: OOM-killer завершил {total_oom} процесс(ов). "
                "Это указывает на критическую нехватку памяти. "
                "Необходимо увеличить объём памяти или ограничить использование памяти приложениями."
            )
        
        # Анализ CPU
        max_cpu = max([d['cpu']['total_percent'] for d in monitoring_data])
        if max_cpu > 90:
            recommendations.append(
                "ВНИМАНИЕ: Загрузка CPU превышала 90%. "
                "Рассмотрите возможность распределения нагрузки или увеличения вычислительных ресурсов."
            )
        
        if not recommendations:
            recommendations.append("Система работала в нормальном режиме без критических проблем.")
        
        return recommendations
    
    def save_report(self, report: Dict, format: str = 'both') -> Path:
        """
        Сохраняет отчёт в файл.
        
        Args:
            report: Словарь с отчётом
            format: Формат сохранения ('json', 'txt', 'both')
            
        Returns:
            Путь к сохранённому файлу
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format in ('json', 'both'):
            json_file = self.output_dir / f"diagnostic_report_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"[REPORT] JSON отчёт сохранён: {json_file}")
        
        if format in ('txt', 'both'):
            txt_file = self.output_dir / f"diagnostic_report_{timestamp}.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(self._format_report_text(report))
            print(f"[REPORT] Текстовый отчёт сохранён: {txt_file}")
            return txt_file
        
        return json_file if format == 'json' else txt_file
    
    def _format_report_text(self, report: Dict) -> str:
        """Форматирует отчёт в текстовый вид."""
        lines = []
        lines.append("=" * 80)
        lines.append("ДИАГНОСТИЧЕСКИЙ ОТЧЁТ О СОСТОЯНИИ СИСТЕМЫ")
        lines.append("=" * 80)
        lines.append(f"Сгенерирован: {report['report_metadata']['generated_at']}")
        lines.append(f"Периодов мониторинга: {report['report_metadata']['monitoring_periods']}")
        lines.append("")
        
        # Краткое резюме
        lines.append("КРАТКОЕ РЕЗЮМЕ")
        lines.append("-" * 80)
        summary = report['executive_summary']
        lines.append(f"Статус: {summary['status']}")
        lines.append(f"Пиковое использование памяти: {summary['peak_memory_usage']}")
        lines.append(f"Пиковое использование CPU: {summary['peak_cpu_usage']}")
        lines.append(f"Пиковое использование swap: {summary['peak_swap_usage']}")
        lines.append(f"Всего OOM событий: {summary['total_oom_events']}")
        lines.append(f"Всего критических событий: {summary['total_critical_events']}")
        lines.append("")
        
        # Анализ памяти
        lines.append("АНАЛИЗ ПАМЯТИ")
        lines.append("-" * 80)
        mem = report['memory_analysis']
        lines.append(f"Среднее использование: {mem.get('average_usage_percent', 0):.1f}%")
        lines.append(f"Максимальное использование: {mem.get('max_usage_percent', 0):.1f}%")
        lines.append(f"Минимальная доступная память: {mem.get('min_available_mb', 0):.1f} МБ")
        lines.append(f"Периодов высокого давления: {mem.get('memory_pressure_periods', 0)}")
        lines.append(f"Критических периодов: {mem.get('critical_periods', 0)}")
        lines.append(f"Тренд: {mem.get('trend', 'N/A')}")
        lines.append("")
        
        # Анализ CPU
        lines.append("АНАЛИЗ CPU")
        lines.append("-" * 80)
        cpu = report['cpu_analysis']
        lines.append(f"Средняя загрузка: {cpu.get('average_usage_percent', 0):.1f}%")
        lines.append(f"Максимальная загрузка: {cpu.get('max_usage_percent', 0):.1f}%")
        lines.append(f"Периодов высокой загрузки: {cpu.get('high_load_periods', 0)}")
        lines.append(f"Критических периодов: {cpu.get('critical_periods', 0)}")
        lines.append(f"Тренд: {cpu.get('trend', 'N/A')}")
        lines.append("")
        
        # Анализ swap
        lines.append("АНАЛИЗ SWAP")
        lines.append("-" * 80)
        swap = report['swap_analysis']
        lines.append(f"Среднее использование: {swap.get('average_usage_percent', 0):.1f}%")
        lines.append(f"Максимальное использование: {swap.get('max_usage_percent', 0):.1f}%")
        lines.append(f"Максимальное использование (МБ): {swap.get('max_used_mb', 0):.1f} МБ")
        lines.append(f"Периодов активности: {swap.get('swap_activity_periods', 0)}")
        lines.append(f"Критических периодов: {swap.get('critical_periods', 0)}")
        lines.append(f"Тренд: {swap.get('trend', 'N/A')}")
        lines.append("")
        
        # Анализ OOM
        lines.append("АНАЛИЗ OOM-KILLER")
        lines.append("-" * 80)
        oom = report['oom_analysis']
        if oom.get('oom_events_detected'):
            lines.append(f"Обнаружено OOM событий: {oom.get('total_oom_events', 0)}")
            if oom.get('processes_killed'):
                lines.append("Завершённые процессы:")
                for proc, count in oom['processes_killed'].items():
                    lines.append(f"  - {proc}: {count} раз(а)")
        else:
            lines.append("OOM события не обнаружены")
        lines.append("")
        
        # Критические события
        lines.append("КРИТИЧЕСКИЕ СОБЫТИЯ")
        lines.append("-" * 80)
        critical = report['critical_events']
        lines.append(f"Всего критических событий: {critical.get('total_critical_events', 0)}")
        if critical.get('events'):
            lines.append("Последние события:")
            for event in critical['events'][:10]:
                lines.append(f"  [{event.get('timestamp', 'N/A')}] {event.get('type', 'UNKNOWN')}")
        lines.append("")
        
        # Исчерпание ресурсов
        lines.append("ИСЧЕРПАНИЕ РЕСУРСОВ")
        lines.append("-" * 80)
        exhaustion = report['resource_exhaustion']
        lines.append(f"Событий исчерпания ресурсов: {exhaustion.get('exhaustion_events_count', 0)}")
        lines.append("")
        
        # Рекомендации
        lines.append("РЕКОМЕНДАЦИИ")
        lines.append("-" * 80)
        for i, rec in enumerate(report['recommendations'], 1):
            lines.append(f"{i}. {rec}")
        lines.append("")
        
        lines.append("=" * 80)
        lines.append("Конец отчёта")
        lines.append("=" * 80)
        
        return "\n".join(lines)

