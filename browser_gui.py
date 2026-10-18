"""Desktop action editor. Runs only after explicit confirmation."""
import json
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from browser_editor import EditorError, make_config, make_step
from browser_runner import BrowserRunner


class BrowserWindow(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.pack(fill="both", expand=True)
        self.root_dir = tk.StringVar(value=str(Path.home() / "BrowserAutomation"))
        self.hosts = tk.StringVar(value="example.com")
        self.resources = tk.StringVar()
        self.action = tk.StringVar(value="goto")
        self.target = tk.StringVar(value="https://example.com")
        self.value = tk.StringVar()
        self.status = tk.StringVar(value="Add steps, then preview before running.")
        self.steps = []
        self.columnconfigure(1, weight=1)
        for row, (label, var) in enumerate(
            (("Working directory", self.root_dir),
             ("Allowed hosts (comma separated)", self.hosts),
             ("Additional resource hosts", self.resources))
        ):
            ttk.Label(self, text=label).grid(row=row, column=0, sticky="w")
            ttk.Entry(self, textvariable=var).grid(row=row, column=1, sticky="ew", pady=4)
        ttk.Button(self, text="Browse", command=self.browse).grid(row=0, column=2)
        ttk.Combobox(self, textvariable=self.action, state="readonly",
                     values=("goto", "fill", "click", "wait_for", "select_option",
                             "check", "uncheck", "screenshot", "download")).grid(row=3, column=0)
        ttk.Entry(self, textvariable=self.target).grid(row=3, column=1, sticky="ew")
        ttk.Entry(self, textvariable=self.value, width=24).grid(row=3, column=2)
        ttk.Label(self, text="URL / selector / screenshot path       Value / download path",
                  wraplength=800).grid(row=4, column=0, columnspan=3, sticky="w")
        ttk.Button(self, text="Add action", command=self.add).grid(row=5, column=0)
        ttk.Button(self, text="Delete selected", command=self.delete).grid(row=5, column=1, sticky="w")
        self.items = tk.Listbox(self, height=10, exportselection=False)
        self.items.grid(row=6, column=0, columnspan=3, sticky="nsew")
        self.rowconfigure(6, weight=1)
        controls = ttk.Frame(self)
        controls.grid(row=7, column=0, columnspan=3, sticky="w", pady=8)
        for title, fn in (("Load", self.load), ("Save", self.save),
                          ("Preview", self.preview), ("Run once", self.run_once)):
            ttk.Button(controls, text=title, command=fn).pack(side="left", padx=4)
        ttk.Label(self, textvariable=self.status).grid(row=8, column=0, columnspan=3, sticky="w")

    def browse(self):
        folder = filedialog.askdirectory()
        if folder:
            self.root_dir.set(folder)

    def refresh(self):
        self.items.delete(0, "end")
        for step in self.steps:
            self.items.insert("end", json.dumps(step, ensure_ascii=False))

    def add(self):
        try:
            self.steps.append(make_step(self.action.get(), self.target.get(), self.value.get()))
            self.refresh()
        except EditorError as exc:
            messagebox.showerror("Invalid step", str(exc))

    def delete(self):
        selected = self.items.curselection()
        if selected:
            self.steps.pop(selected[0])
            self.refresh()

    def config(self):
        cfg = make_config(self.root_dir.get(), self.hosts.get(), self.steps, self.resources.get())
        BrowserRunner(cfg, dry_run=True).run()
        return cfg

    def preview(self):
        try:
            cfg = self.config()
            self.status.set(f"Validated {len(cfg['steps'])} steps without accessing the network.")
        except Exception as exc:
            messagebox.showerror("Validation failed", str(exc))

    def save(self):
        try:
            cfg = self.config()
            path = filedialog.asksaveasfilename(defaultextension=".json")
            if path:
                with Path(path).open("x", encoding="utf-8") as handle:
                    json.dump(cfg, handle, ensure_ascii=False, indent=2)
                self.status.set("Saved " + path)
        except Exception as exc:
            messagebox.showerror("Not saved", str(exc))

    def load(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            supported = {"root_dir", "allow_hosts", "resource_hosts",
                         "headless", "timeout_ms", "steps"}
            if set(data) - supported or data.get("headless", True) is not True or data.get("timeout_ms", 30000) != 30000:
                raise ValueError("This settings file has advanced options this editor cannot preserve")
            cfg = make_config(data["root_dir"], ",".join(data["allow_hosts"]),
                              data["steps"], ",".join(data.get("resource_hosts", [])))
            BrowserRunner(cfg, dry_run=True).run()
            self.root_dir.set(cfg["root_dir"])
            self.hosts.set(",".join(cfg["allow_hosts"]))
            self.resources.set(",".join(cfg["resource_hosts"]))
            self.steps = list(cfg["steps"])
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Cannot load", str(exc))

    def run_once(self):
        try:
            cfg = self.config()
        except Exception as exc:
            messagebox.showerror("Invalid workflow", str(exc))
            return
        if not messagebox.askyesno("Run once", "Execute the selected browser steps?"):
            return
        self.status.set("Running...")
        def work():
            try:
                BrowserRunner(cfg).run()
                self.after(0, self.status.set, "Completed.")
            except Exception as exc:
                self.after(0, self.status.set, "Failed: " + type(exc).__name__)
        threading.Thread(target=work, daemon=True).start()


def main():
    root = tk.Tk()
    root.title("Browser Automation Runner")
    root.minsize(850, 480)
    BrowserWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
