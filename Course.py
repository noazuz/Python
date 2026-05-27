import tkinter as tk
from tkinter import ttk, messagebox
import random
import time

# Клас для представлення мережевого пакета
class Packet:
    def __init__(self, p_type, size_mb, priority):
        self.type = p_type       # Тип трафіку (VoIP, Video, Data)
        self.size_mb = size_mb   # Розмір пакета в Мегабайтах
        self.priority = priority # Пріоритет (чим менше число, тим вищий пріоритет)
        self.timestamp = time.time()

class NetworkSimGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Аналізатор пропускної здатності мережі")
        self.root.geometry("600x650") 
        
        # Початкові параметри
        self.bandwidth_mbps = 144
        self.total_data_sent_mb = 0
        self.packet_count = 0
        self.start_time = time.time()
        self.queue = []
        self.is_running = False # Симуляція не почнеться, поки не натиснуть кнопку

        self.setup_ui()

    def setup_ui(self):
        """Створення графічного інтерфейсу"""
        
        # Блок введення параметрів
        input_frame = ttk.LabelFrame(self.root, text=" Налаштування мережі ")
        input_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(input_frame, text="Пропускна здатність (Мбіт/с):").grid(row=0, column=0, padx=5, pady=5)
        self.entry_speed = ttk.Entry(input_frame)
        self.entry_speed.insert(0, "144") # Значення за замовчуванням
        self.entry_speed.grid(row=0, column=1, padx=5, pady=5)

        self.btn_start = ttk.Button(input_frame, text="Запустити", command=self.start_simulation)
        self.btn_start.grid(row=0, column=2, padx=5, pady=5)

        # Панель статистики
        stats_frame = ttk.LabelFrame(self.root, text=" Статистика в реальному часі ")
        stats_frame.pack(fill="x", padx=10, pady=5)

        self.lbl_time = ttk.Label(stats_frame, text="Час: 0.00с")
        self.lbl_time.grid(row=0, column=0, padx=10, pady=5)
        
        self.lbl_data = ttk.Label(stats_frame, text="Передано: 0.00 ГБ")
        self.lbl_data.grid(row=0, column=1, padx=10, pady=5)

        self.lbl_speed = ttk.Label(stats_frame, text="Швидкість: 0 Мбіт/с")
        self.lbl_speed.grid(row=0, column=2, padx=10, pady=5)

        # Стан каналу (візуалізація активності)
        status_frame = ttk.LabelFrame(self.root, text=" Поточна активність ")
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.lbl_status = ttk.Label(status_frame, text="Симуляцію не запущено", foreground="gray", font=('Arial', 10, 'bold'))
        self.lbl_status.pack(pady=10)

        self.progress = ttk.Progressbar(status_frame, length=500, mode='determinate')
        self.progress.pack(padx=10, pady=10)

        # Візуалізація черги пакетів
        queue_frame = ttk.LabelFrame(self.root, text=" Пріоритетна черга (Buffer) ")
        queue_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.queue_listbox = tk.Listbox(queue_frame, height=8, font=('Courier', 9))
        self.queue_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Кнопка завершення
        self.btn_finish = ttk.Button(self.root, text="Завершити", command=self.finish_simulation, state="disabled")
        self.btn_finish.pack(pady=10)

    def start_simulation(self):
        """Валідація вводу та початок роботи"""
        try:
            # Спроба зчитати число з поля вводу
            speed = float(self.entry_speed.get())
            if speed <= 0:
                raise ValueError("Швидкість повинна бути більше нуля")
            
            self.bandwidth_mbps = speed
            self.is_running = True
            self.start_time = time.time()
            
            # Оновлення UI
            self.btn_start.config(state="disabled")
            self.entry_speed.config(state="disabled")
            self.btn_finish.config(state="normal")
            self.lbl_status.config(text="Канал вільний", foreground="green")
            
            # Запуск циклів
            self.simulate_network()
            
        except ValueError as e:
            # Обробка помилок вводу (букви замість цифр або некоректні числа)
            messagebox.showerror("Помилка вводу", f"Будь ласка, введіть коректне числове значення!\nДеталі: {e}")

    def add_packet(self):
        """Генерація випадкових пакетів з різними пріоритетами"""
        if not self.is_running: return
        rand_val = random.random()
        
        # Розподіл трафіку: Data (40%), Video (40%), Voice (20%)
        if rand_val < 0.4:
            p = Packet("Best-Effort Data", random.randint(15, 60), 3)
        elif rand_val < 0.8:
            p = Packet("VBR Video (4K)", random.randint(20, 45), 2)
        else:
            p = Packet("RT Voice (VoIP)", 0.5, 1) # Голос завжди маленький, але пріоритетний
        
        self.queue.append(p)
        # Сортування черги за пріоритетом (QoS)
        self.queue.sort(key=lambda x: x.priority)
        self.update_queue_display()

    def update_queue_display(self):
        """Відображення вмісту буфера в інтерфейсі"""
        self.queue_listbox.delete(0, tk.END)
        for p in self.queue:
            self.queue_listbox.insert(tk.END, f"[P{p.priority}] {p.type: <20} | {p.size_mb} MB")

    def process_transmission(self):
        """Логіка передачі даних з черги в канал"""
        if not self.is_running: return
        
        try:
            if self.queue:
                pkt = self.queue.pop(0) # Беремо перший пакет (найвищий пріоритет)
                self.update_queue_display()
                
                # Розрахунок часу передачі (Формула: (Size_Mb * 8) / Speed_Mbps)
                t_time = (pkt.size_mb * 8) / self.bandwidth_mbps
                ms_time = int(t_time * 1000)
                
                self.lbl_status.config(text=f"ПЕРЕДАЧА: {pkt.type} ({pkt.size_mb} MB)", foreground="blue")
                self.animate_progress(ms_time, pkt)
            else:
                self.lbl_status.config(text="Очікування трафіку...", foreground="gray")
                self.root.after(500, self.process_transmission)
        except Exception as e:
            print(f"Помилка при передачі: {e}")

    def animate_progress(self, duration_ms, pkt):
        """Анімація смуги прогресу для передачі пакета"""
        if not self.is_running: return
        steps = 20
        step_time = max(1, duration_ms // steps)
        
        def run_step(current_step):
            if not self.is_running: return
            if current_step <= steps:
                self.progress['value'] = (current_step / steps) * 100
                self.root.after(step_time, lambda: run_step(current_step + 1))
            else:
                # Оновлення статистики після завершення передачі
                self.total_data_sent_mb += pkt.size_mb
                self.packet_count += 1
                self.update_stats()
                self.progress['value'] = 0
                self.process_transmission()
        run_step(0)

    def update_stats(self):
        """Оновлення лічильників у реальному часі"""
        try:
            duration = time.time() - self.start_time
            total_gb = self.total_data_sent_mb / 1024
            avg_speed = (self.total_data_sent_mb * 8) / duration if duration > 0 else 0
            
            self.lbl_time.config(text=f"Час: {duration:.1f}с")
            self.lbl_data.config(text=f"Передано: {total_gb:.2f} ГБ")
            self.lbl_speed.config(text=f"Сер. швидкість: {avg_speed:.1f} Мбіт/с")
        except ZeroDivisionError:
            pass

    def simulate_network(self):
        """Головний цикл генерації навантаження"""
        if not self.is_running: return
        
        # З шансом 70% додаємо новий пакет кожні 650 мс
        if random.random() < 0.7:
            self.add_packet()
            
        if self.lbl_status.cget("text") == "Канал вільний":
            self.process_transmission()
            
        self.root.after(650, self.simulate_network)

    def finish_simulation(self):
        """Зупинка, підведення підсумків та закриття"""
        self.is_running = False
        duration = time.time() - self.start_time
        total_gb = self.total_data_sent_mb / 1024
        avg_speed = (self.total_data_sent_mb * 8) / duration if duration > 0 else 0

        report = (
            f"Встановлена швидкість:     {self.bandwidth_mbps} Мбіт/с\n"
            f"Час роботи симуляції:     {duration:.2f} сек\n"
            f"Всього передано даних:    {total_gb:.2f} ГБ\n"
            f"Опрацьовано пакетів:      {self.packet_count}\n"
            f"Середня пропускна здатність: {avg_speed:.2f} Мбіт/с\n"
        )
        
        messagebox.showinfo("Підсумкова статистика", report)
        self.root.destroy() 

if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkSimGUI(root)
    root.mainloop()