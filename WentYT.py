import customtkinter as ctk
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog
import subprocess
import threading
import os
import shutil
import sys
import re
import datetime

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


RUS_TO_ENG = str.maketrans(
    "йцукенгшщзхъфывапролджэячсмитьбюЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ",
    "qwertyuiop[]asdfghjkl;'zxcvbnm,.QWERTYUIOP[]ASDFGHJKL;'ZXCVBNM,.",
)


def fix_layout(text):
    """Convert Russian keyboard input to English."""
    return text.translate(RUS_TO_ENG)


def check_yt_dlp():
    """Check if yt-dlp and ffmpeg are installed; prompt to install if missing."""
    if shutil.which("yt-dlp") is None:
        if messagebox.askyesno("Install yt-dlp", "yt-dlp not found. Install via pip?"):
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "yt-dlp"]
                )
                messagebox.showinfo("Success", "yt-dlp installed successfully.")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Failed to install yt-dlp: {e}")
                return False
        return False
    if shutil.which("ffmpeg") is None:
        messagebox.showerror(
            "Error", "ffmpeg not found. Please install ffmpeg for MP3 conversion."
        )
        return False
    return True


def download_playlist():
    """Start downloading the YouTube playlist as MP3s."""
    url = url_entry.get().strip()
    out_dir = dir_entry.get().strip()

    if not url or url == "Enter playlist URL":
        messagebox.showerror("Error", "Please enter a valid playlist URL.")
        return
    if not out_dir or out_dir == "Select directory":
        messagebox.showerror("Error", "Please select a directory to save files.")
        return
    if not os.path.isdir(out_dir):
        messagebox.showerror("Error", "Selected directory does not exist.")
        return

    url = fix_layout(url)
    if not check_yt_dlp():
        return

    output_text.configure(state="normal")
    output_text.delete("1.0", ctk.END)
    output_text.configure(state="disabled")
    progress_bar.set(0)
    status_label.configure(text="Starting download...")
    download_button.configure(state="disabled")

    def run_download():
        """Run yt-dlp in a separate thread."""
        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format",
            "mp3",
            "--yes-playlist",
            "--verbose",
            url,
            "-o",
            os.path.join(out_dir, "%(playlist_title)s/%(title)s.%(ext)s"),
        ]
        download_count = 0
        error_output = []
        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            for line in process.stdout:
                prog_match = re.search(r"(\d+\.?\d*)%", line)
                if prog_match:
                    progress_bar.set(float(prog_match.group(1)) / 100)
                    status_label.configure(text=f"Progress: {prog_match.group(1)}%")

                dest_match = re.search(r"Destination: (?P<path>.+?\.mp3)", line)
                if dest_match:
                    filename = os.path.basename(dest_match.group("path").strip())
                    name_only = os.path.splitext(filename)[0]
                    output_text.configure(state="normal")
                    output_text.insert(ctk.END, f'"{name_only}" downloaded!\n')
                    output_text.configure(state="disabled")
                    output_text.see(ctk.END)
                    download_count += 1
                    root.update_idletasks()
                else:
                    error_output.append(line.strip())

            process.wait()
            if process.returncode == 0:
                output_text.configure(state="normal")
                output_text.insert(
                    ctk.END, f"Done! Total downloaded: {download_count}\n"
                )
                output_text.configure(state="disabled")
                status_label.configure(text=f"Completed: {download_count} tracks")
                messagebox.showinfo("Success", f"Downloaded {download_count} tracks!")
            else:
                output_text.configure(state="normal")
                output_text.insert(
                    ctk.END, f"Error: Download failed (code {process.returncode})\n"
                )
                output_text.insert(ctk.END, "\n".join(error_output[-5:]) + "\n")
                output_text.configure(state="disabled")
                status_label.configure(text="Download failed")
                messagebox.showerror(
                    "Error",
                    f"Download failed (code {process.returncode}). Check output for details.",
                )
                with open("yt_dlp_error.log", "a", encoding="utf-8") as log_file:
                    log_file.write(
                        f"[{datetime.datetime.now()}] Error (code {process.returncode}):\n"
                    )
                    log_file.write("\n".join(error_output) + "\n\n")
        except Exception as e:
            output_text.configure(state="normal")
            output_text.insert(ctk.END, f"Unexpected error: {e}\n")
            output_text.configure(state="disabled")
            status_label.configure(text="Error occurred")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            with open("yt_dlp_error.log", "a", encoding="utf-8") as log_file:
                log_file.write(f"[{datetime.datetime.now()}] Unexpected error: {e}\n\n")
        finally:
            download_button.configure(state="normal")
            status_label.configure(text="Ready")

    threading.Thread(target=run_download, daemon=True).start()


def choose_directory():
    """Open a dialog to select the output directory."""
    directory = filedialog.askdirectory()
    if directory:
        dir_entry.delete(0, ctk.END)
        dir_entry.insert(0, directory)


def on_entry_focus_in(entry, placeholder):
    """Clear placeholder text when entry is focused."""
    if entry.get() == placeholder:
        entry.delete(0, ctk.END)
        entry.configure(text_color="#FFFFFF")


def on_entry_focus_out(entry, placeholder):
    """Restore placeholder text if entry is empty."""
    if not entry.get():
        entry.insert(0, placeholder)
        entry.configure(text_color="#FFFFFF")


def toggle_theme():
    """Toggle between light and dark modes."""
    current_mode = ctk.get_appearance_mode()
    new_mode = "Dark" if current_mode == "Light" else "Light"
    ctk.set_appearance_mode(new_mode)
    theme_button.configure(text=f"Switch to {current_mode} Mode")


root = ctk.CTk()
root.title("YouTube Music Downloader")
root.geometry("600x500")
root.resizable(False, False)


input_frame = ctk.CTkFrame(root, corner_radius=10)
input_frame.pack(pady=20, padx=20, fill="x")


url_label = ctk.CTkLabel(input_frame, text="Playlist URL", font=("Arial", 14))
url_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
url_entry = ctk.CTkEntry(input_frame, font=("Arial", 12), width=300)
url_entry.insert(0, "Enter playlist URL")
url_entry.configure(text_color="#FFFFFF")
url_entry.bind(
    "<FocusIn>", lambda e: on_entry_focus_in(url_entry, "Enter playlist URL")
)
url_entry.bind(
    "<FocusOut>", lambda e: on_entry_focus_out(url_entry, "Enter playlist URL")
)
url_entry.grid(row=0, column=1, padx=10, pady=5, sticky="we")

dir_label = ctk.CTkLabel(input_frame, text="Save Directory", font=("Arial", 14))
dir_label.grid(row=1, column=0, sticky="w", padx=10, pady=5)
dir_entry = ctk.CTkEntry(input_frame, font=("Arial", 12), width=300)
dir_entry.insert(0, "Select directory")
dir_entry.configure(text_color="#FFFFFF")
dir_entry.bind("<FocusIn>", lambda e: on_entry_focus_in(dir_entry, "Select directory"))
dir_entry.bind(
    "<FocusOut>", lambda e: on_entry_focus_out(dir_entry, "Select directory")
)
dir_entry.grid(row=1, column=1, padx=10, pady=5, sticky="we")
dir_button = ctk.CTkButton(
    input_frame, text="📁 Select", command=choose_directory, width=100
)
dir_button.grid(row=1, column=2, padx=10, pady=5)
input_frame.columnconfigure(1, weight=1)

download_button = ctk.CTkButton(
    root,
    text="Download Playlist",
    command=download_playlist,
    font=("Arial", 14, "bold"),
    height=40,
)
download_button.pack(pady=15)

progress_bar = ctk.CTkProgressBar(root, width=560, height=20)
progress_bar.set(0)
progress_bar.pack(padx=20, pady=10)
status_label = ctk.CTkLabel(root, text="Ready", font=("Arial", 12))
status_label.pack(pady=5)

output_frame = ctk.CTkFrame(root, corner_radius=10)
output_frame.pack(fill="both", expand=True, padx=20, pady=10)
output_text = ctk.CTkTextbox(
    output_frame, font=("Arial", 12), height=150, wrap="word", state="disabled"
)
output_text.pack(fill="both", expand=True, padx=10, pady=10)

theme_button = ctk.CTkButton(
    root,
    text="Switch to Dark Mode",
    command=toggle_theme,
    font=("Arial", 12),
    width=150,
)
theme_button.pack(pady=10)

root.mainloop()
