import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import subprocess
import sys

class ChatFrontend:
    def __init__(self, master):
        self.master = master
        master.title("Ollama NLP Chat")
        master.geometry("600x500")
        master.minsize(400, 300)

        self.chat_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, state='disabled', font=("Consolas", 12))
        self.chat_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.entry = tk.Entry(master, font=("Consolas", 12))
        self.entry.pack(fill=tk.X, padx=5, pady=(0,5))
        self.entry.bind('<Return>', self.send_message)

        self.send_button = tk.Button(master, text="Send", command=self.send_message)
        self.send_button.pack(pady=(0,5))

        self.response_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self.worker, daemon=True)
        self.worker_thread.start()

    def send_message(self, event=None):
        user_input = self.entry.get().strip()
        if not user_input:
            return
        self.append_chat(f"You: {user_input}\n")
        self.entry.delete(0, tk.END)
        self.response_queue.put(user_input)

    def append_chat(self, text):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, text)
        self.chat_area.see(tk.END)
        self.chat_area.config(state='disabled')

    def worker(self):
        while True:
            user_input = self.response_queue.get()
            # Call the backend (shell.py) as a subprocess
            try:
                result = subprocess.run([sys.executable, 'shell.py'], input=user_input.encode('utf-8'), capture_output=True, timeout=30)
                output = result.stdout.decode('utf-8').strip()
            except Exception as e:
                output = f"[Error] {e}"
            self.master.after(0, self.append_chat, f"Ollama: {output}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatFrontend(root)
    root.mainloop()
