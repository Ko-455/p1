import sys
import time
import gc
import os
from typing import List

class MemoryLeakSimulator:
    """Класс для имитации утечки памяти."""
    
    def __init__(self, leak_rate_mb: int = 50, interval: float = 1.0):
        """
        Инициализация симулятора утечки памяти.
        
        Args:
            leak_rate_mb: Количество мегабайт для выделения за раз
            interval: Интервал между выделениями памяти в секундах
        """
        self.leak_rate_mb = leak_rate_mb
        self.interval = interval
        self.memory_chunks: List[bytearray] = []
        self.total_allocated = 0
        self.running = False
        
    def allocate_memory(self, size_mb: int) -> bytearray:
        """
        Выделяет указанное количество памяти.
        
        Args:
            size_mb: Размер в мегабайтах
            
        Returns:
            Выделенный блок памяти
        """
        try:
            # Выделяем память (1 МБ = 1024 * 1024 байт)
            chunk = bytearray(size_mb * 1024 * 1024)
            # Заполняем данными, чтобы память реально использовалась
            for i in range(0, len(chunk), 4096):
                chunk[i] = i % 256
            return chunk
        except MemoryError:
            print(f"[ERROR] Не удалось выделить {size_mb} МБ памяти!")
            return None
    
    def start_leak(self):
        """Запускает процесс утечки памяти."""
        self.running = True
        print(f"[INFO] Запуск утечки памяти: {self.leak_rate_mb} МБ каждые {self.interval} сек")
        print(f"[INFO] PID процесса: {os.getpid()}")
        
        iteration = 0
        try:
            while self.running:
                iteration += 1
                chunk = self.allocate_memory(self.leak_rate_mb)
                
                if chunk is None:
                    print(f"[ERROR] Прекращение выделения памяти на итерации {iteration}")
                    break
                
                # НЕ освобождаем память - это и есть утечка!
                self.memory_chunks.append(chunk)
                self.total_allocated += self.leak_rate_mb
                
                print(f"[INFO] Итерация {iteration}: Выделено {self.total_allocated} МБ "
                      f"(блоков в памяти: {len(self.memory_chunks)})")
                
                # Отключаем сборщик мусора для гарантированной утечки
                gc.disable()
                
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print("\n[INFO] Получен сигнал прерывания")
        except Exception as e:
            print(f"[ERROR] Произошла ошибка: {e}")
        finally:
            self.stop_leak()
    
    def stop_leak(self):
        """Останавливает утечку памяти."""
        self.running = False
        print(f"[INFO] Остановка утечки памяти. Всего выделено: {self.total_allocated} МБ")
        # Очищаем память
        self.memory_chunks.clear()
        gc.enable()
        gc.collect()


def main():
    """Главная функция для запуска симулятора."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Симулятор утечки памяти (только для виртуальных машин!)'
    )
    parser.add_argument(
        '--rate',
        type=int,
        default=50,
        help='Количество МБ для выделения за раз (по умолчанию: 50)'
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=1.0,
        help='Интервал между выделениями в секундах (по умолчанию: 1.0)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("СИМУЛЯТОР УТЕЧКИ ПАМЯТИ")
    print("=" * 60)
    print("ВНИМАНИЕ: Этот скрипт вызывает утечку памяти!")
    print("Запускайте ТОЛЬКО в виртуальной машине!")
    print("=" * 60)
    
    simulator = MemoryLeakSimulator(
        leak_rate_mb=args.rate,
        interval=args.interval
    )
    
    try:
        simulator.start_leak()
    except Exception as e:
        print(f"[FATAL] Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()


