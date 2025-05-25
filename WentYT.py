import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import subprocess
import threading
import os
import shutil
import sys
import re

# Маппинг русской раскладки на английскую
rus = "йцукенгшщзхъфывапролджэячсмитьбю"
eng = "qwertyuiop[]asdfghjkl;'zxcvbnm,."
rus += rus.upper()
eng += eng.upper()
RU_EN_LAYOUT = str.maketrans(rus, eng)


def fix_layout(text):
    return text.translate(RU_EN_LAYOUT)


def ensure_yt_dlp():
    if shutil.which("yt-dlp") is None:
        install = messagebox.askyesno(
            "Установка yt-dlp", "yt-dlp не найден. Установить автоматически через pip?"
        )
        if not install:
            return False
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
            messagebox.showinfo("Успех", "yt-dlp успешно установлен.")
            return True
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Ошибка", f"Не удалось установить yt-dlp:\n{e}")
            return False
    return True


def download_playlist():
    raw_url = url_entry.get().strip()
    url = fix_layout(raw_url)
    out_dir = dir_entry.get().strip()
    if not url or url == "Введите URL плейлиста":
        messagebox.showerror("Ошибка", "Пожалуйста, введите URL плейлиста")
        return
    if not out_dir or out_dir == "Выберите директорию":
        messagebox.showerror("Ошибка", "Пожалуйста, выберите директорию для сохранения")
        return

    if not ensure_yt_dlp():
        return

    listbox.delete(0, tk.END)
    progress["value"] = 0
    download_button.config(state=tk.DISABLED)

    def run_download():
        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format",
            "mp3",
            "--yes-playlist",
            url,
            "-o",
            os.path.join(out_dir, "%(playlist_title)s", "%(title)s.%(ext)s"),
        ]
        download_count = 0
        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            for line in process.stdout:
                prog = re.search(r"(\d+\.?\d*)%", line)
                if prog:
                    progress["value"] = float(prog.group(1))

                dest = re.search(r"Destination: (?P<path>.+?\.mp3)", line)
                if dest:
                    full_path = dest.group("path").strip()
                    filename = os.path.basename(full_path)
                    name_only = os.path.splitext(filename)[0]
                    listbox.insert(tk.END, f'"{name_only}" скачано!')
                    download_count += 1

            process.wait()
            if process.returncode == 0:
                listbox.insert(tk.END, f"Готово! Всего скачано: {download_count}")
                messagebox.showinfo(
                    "Успех", f"Загрузка завершена! Скачано {download_count} треков."
                )
            else:
                messagebox.showerror(
                    "Ошибка",
                    f"Загрузка завершилась с ошибкой (код {process.returncode})",
                )
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
        finally:
            download_button.config(state=tk.NORMAL)

    threading.Thread(target=run_download, daemon=True).start()


def choose_directory():
    directory = filedialog.askdirectory()
    if directory:
        dir_entry.delete(0, tk.END)
        dir_entry.insert(0, directory)


# Функции для placeholder'ов
def on_entry_focus_in(event, entry, placeholder):
    if entry.get() == placeholder:
        entry.delete(0, tk.END)
        entry.config(foreground="#333")


def on_entry_focus_out(event, entry, placeholder):
    if not entry.get():
        entry.insert(0, placeholder)
        entry.config(foreground="#999")


# Основное окно
root = tk.Tk()
root.title("YouTube Music Downloader")
root.geometry("600x500")
root.configure(bg="#f5f5f5")
root.resizable(False, False)

# Стиль
style = ttk.Style()
style.theme_use("clam")

# Настройка стилей
style.configure("TLabel", font=("Arial", 14), foreground="#333", background="#f5f5f5")
style.configure("TEntry", font=("Arial", 12), padding=10, relief="flat")
style.configure(
    "TButton",
    font=("Arial", 14, "bold"),
    padding=10,
    background="#2196f3",
    foreground="#ffffff",
)
style.configure(
    "TProgressbar", thickness=20, troughcolor="#e0e0e0", background="#1e90ff"
)

# Эффекты наведения для кнопок
style.map(
    "TButton",
    background=[("active", "#1e90ff"), ("!active", "#2196f3")],
    foreground=[("active", "#ffffff"), ("!active", "#ffffff")],
)

# Панель ввода
frame_top = tk.Frame(
    root,
    bg="#ffffff",
    relief="flat",
    bd=1,
    highlightbackground="#e0e0e0",
    highlightcolor="#e0e0e0",
    highlightthickness=1,
)
frame_top.pack(pady=20, padx=20, fill=tk.X)

url_label = ttk.Label(frame_top, text="URL плейлиста")
url_label.grid(row=0, column=0, sticky="w", pady=5, padx=10)
url_entry = ttk.Entry(frame_top)
url_entry.grid(row=0, column=1, padx=10, pady=5, sticky="we")
url_entry.insert(0, "Введите URL плейлиста")
url_entry.config(foreground="#999")
url_entry.bind(
    "<FocusIn>", lambda e: on_entry_focus_in(e, url_entry, "Введите URL плейлиста")
)
url_entry.bind(
    "<FocusOut>", lambda e: on_entry_focus_out(e, url_entry, "Введите URL плейлиста")
)
frame_top.columnconfigure(1, weight=1)

dir_label = ttk.Label(frame_top, text="Папка для сохранения")
dir_label.grid(row=1, column=0, sticky="w", pady=5, padx=10)
dir_entry = ttk.Entry(frame_top)
dir_entry.grid(row=1, column=1, padx=10, pady=5, sticky="we")
dir_entry.insert(0, "Выберите директорию")
dir_entry.config(foreground="#999")
dir_entry.bind(
    "<FocusIn>", lambda e: on_entry_focus_in(e, dir_entry, "Выберите директорию")
)
dir_entry.bind(
    "<FocusOut>", lambda e: on_entry_focus_out(e, dir_entry, "Выберите директорию")
)

dir_button = ttk.Button(
    frame_top, text="📁 Выбрать", compound=tk.LEFT, command=choose_directory
)
dir_button.grid(row=1, column=2, padx=10, pady=5)

# Кнопка загрузки
download_button = ttk.Button(
    root, text="⬇️ Скачать плейлист", compound=tk.LEFT, command=download_playlist
)
download_button.pack(pady=15)

# Прогрессбар
progress = ttk.Progressbar(root, orient="horizontal", mode="determinate", length=560)
progress.pack(padx=20, pady=10)

# Мини-консоль
listbox_frame = tk.Frame(
    root,
    bg="#ffffff",
    relief="flat",
    bd=1,
    highlightbackground="#e0e0e0",
    highlightcolor="#e0e0e0",
    highlightthickness=1,
)
listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
listbox = tk.Listbox(
    listbox_frame,
    height=10,
    font=("Arial", 12),
    foreground="#333",
    background="#ffffff",
    borderwidth=0,
    highlightthickness=0,
)
listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

root.mainloop()
