from __future__ import annotations

import contextlib
import io
import json
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from browser_runner import BrowserRunner, BrowserRunnerError, PlaywrightError


class BrowserAutomationDesktop:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Browser Automation Runner — Advanced / ブラウザ自動化 — 上級")
        self.root.geometry("1020x720")
        self.root.minsize(880, 620)
        self.config_path = tk.StringVar()
        self.status = tk.StringVar(value="Advanced fallback only / APIが無い場合の最終手段")
        self.config: dict | None = None
        self._build()
        default = Path(__file__).resolve().parent / "browser.example.json"
        if default.is_file():
            self.config_path.set(str(default))
            self._load_config(False)

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Browser Automation Runner", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(outer, text="Advanced / 上級機能 — APIやローカル処理で実現できない場合だけ使用してください。Web画面変更で壊れる可能性があります。", wraplength=900).pack(anchor="w", pady=(0, 14))

        cfg = ttk.LabelFrame(outer, text="Configuration / 設定", padding=10)
        cfg.pack(fill="x", pady=(0, 10))
        ttk.Entry(cfg, textvariable=self.config_path).pack(side="left", fill="x", expand=True)
        ttk.Button(cfg, text="Browse / 選択", command=self._browse).pack(side="left", padx=(8, 0))
        ttk.Button(cfg, text="Validate / 検証", command=lambda: self._load_config(True)).pack(side="left", padx=(6, 0))

        summary = ttk.LabelFrame(outer, text="Network boundary / 通信境界", padding=8)
        summary.pack(fill="x", pady=(0, 10))
        self.summary = ttk.Treeview(summary, columns=("item", "value"), show="headings", height=5)
        self.summary.heading("item", text="Item / 項目")
        self.summary.heading("value", text="Value / 内容")
        self.summary.column("item", width=220, anchor="w")
        self.summary.column("value", width=720, anchor="w")
        self.summary.pack(fill="x")

        stepbox = ttk.LabelFrame(outer, text="Steps / 操作手順", padding=8)
        stepbox.pack(fill="both", expand=True, pady=(0, 10))
        self.steps = tk.Listbox(stepbox, height=10)
        self.steps.pack(fill="both", expand=True)

        actions = ttk.LabelFrame(outer, text="Execution / 実行", padding=10)
        actions.pack(fill="x", pady=(0, 10))
        self.dry_btn = ttk.Button(actions, text="Dry Run / 設定確認", command=self._dry_run)
        self.dry_btn.pack(side="left")
        self.run_btn = ttk.Button(actions, text="Run Browser / ブラウザ実行", command=self._run_live)
        self.run_btn.pack(side="left", padx=6)
        ttk.Label(actions, text="Live実行はクリック・入力・ダウンロード等の副作用を起こし得ます。", wraplength=520).pack(side="right")

        logbox = ttk.LabelFrame(outer, text="Result / 結果", padding=8)
        logbox.pack(fill="both", expand=True)
        self.log = tk.Text(logbox, wrap="word", height=10, state="disabled", font=("Consolas", 9))
        self.log.pack(fill="both", expand=True)
        ttk.Label(outer, textvariable=self.status).pack(fill="x", pady=(8, 0))

    def _browse(self) -> None:
        path = filedialog.askopenfilename(title="Browser Automation JSON", filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if path:
            self.config_path.set(path)
            self._load_config(True)

    def _read(self) -> dict:
        path = Path(self.config_path.get()).expanduser().resolve()
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise BrowserRunnerError("config root must be an object")
        return raw

    def _load_config(self, show_error: bool) -> bool:
        try:
            raw = self._read()
            runner = BrowserRunner(raw, dry_run=True)
            runner.run()
            self.config = raw
            self._render(runner)
            self.status.set("Configuration valid / 設定OK — Advanced fallback")
            return True
        except Exception as exc:
            self.config = None
            self.status.set(f"Configuration error / 設定エラー: {type(exc).__name__}")
            if show_error:
                messagebox.showerror("Configuration", str(exc))
            return False

    def _render(self, runner: BrowserRunner) -> None:
        for item in self.summary.get_children():
            self.summary.delete(item)
        rows = [
            ("Allow hosts / 画面遷移許可", ", ".join(sorted(runner.allowed_hosts))),
            ("Resource hosts / 素材通信のみ", ", ".join(sorted(runner.resource_hosts)) or "-"),
            ("Headless", str(runner.headless)),
            ("Timeout", f"{runner.timeout_ms} ms"),
            ("Service workers", "blocked / 無効化"),
        ]
        for row in rows:
            self.summary.insert("", "end", values=row)
        self.steps.delete(0, "end")
        for index, step in enumerate(runner.steps, start=1):
            if isinstance(step, dict):
                action = step.get("action", "?")
                # Do not show fill values or other potentially sensitive payloads.
                if action == "goto":
                    detail = str(step.get("url", ""))
                elif action in {"screenshot", "download"}:
                    detail = str(step.get("path") or step.get("save_as") or "")
                else:
                    detail = str(step.get("selector", ""))
                self.steps.insert("end", f"{index}. {action} — {detail}")

    def _append(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _dry_run(self) -> None:
        if not self._load_config(True):
            return
        self._append("Dry Run OK — configuration/network boundary validated. No browser actions executed. / 設定検証のみ。ブラウザ操作なし。")

    def _run_live(self) -> None:
        if not self._load_config(True):
            return
        if not messagebox.askyesno("Advanced browser execution / 上級ブラウザ実行", "ブラウザを実際に操作します。クリック、入力、ダウンロード等が実行され、Webサービス側に副作用が発生する可能性があります。\n\nAPIで代替できないこと、Dry Run、対象アカウントを確認済みの場合だけ続行してください。"):
            return
        assert self.config is not None
        raw = self.config
        self.dry_btn.configure(state="disabled")
        self.run_btn.configure(state="disabled")
        self.status.set("Browser running… / ブラウザ実行中…")
        def worker() -> None:
            buffer = io.StringIO()
            try:
                with contextlib.redirect_stdout(buffer):
                    BrowserRunner(raw, dry_run=False).run()
                self.root.after(0, lambda: self._finish(True, buffer.getvalue() or "Run OK"))
            except Exception as exc:
                text = buffer.getvalue() + f"ERROR: {type(exc).__name__}: {exc}"
                self.root.after(0, lambda: self._finish(False, text))
        threading.Thread(target=worker, daemon=True).start()

    def _finish(self, ok: bool, text: str) -> None:
        self._append(text)
        self.dry_btn.configure(state="normal")
        self.run_btn.configure(state="normal")
        self.status.set("Run complete / 実行完了" if ok else "Run failed / 実行失敗")
        if not ok:
            messagebox.showerror("Browser Runner", text[-1500:])


def main() -> None:
    root = tk.Tk()
    BrowserAutomationDesktop(root)
    root.mainloop()


if __name__ == "__main__":
    main()
