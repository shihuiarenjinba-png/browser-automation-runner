from __future__ import annotations

import contextlib
import io
import json
import threading
import urllib.parse
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from browser_runner import BrowserRunner, BrowserRunnerError
from ui_language import load_language, save_language

APP_ID = "browser-automation-runner"


class BrowserAutomationDesktop:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.lang = load_language(APP_ID)
        self.root.geometry("1020x740")
        self.root.minsize(880, 640)
        self.config_path = tk.StringVar()
        self.status = tk.StringVar(value="")
        self.config: dict | None = None
        self._live_running = False
        self._build()
        default = Path(__file__).resolve().parent / "workflow.example.json"
        if default.is_file():
            self.config_path.set(str(default))
            self._load_config(False)
        else:
            self.status.set(self.t("APIが無い場合の最終手段", "Advanced fallback only"))

    def t(self, ja: str, en: str) -> str:
        return en if self.lang == "en" else ja

    def _build(self) -> None:
        for child in self.root.winfo_children():
            child.destroy()
        self.root.title(self.t("ブラウザ自動化 — 上級", "Browser Automation Runner — Advanced"))

        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)

        language = ttk.Frame(outer)
        language.pack(fill="x", pady=(0, 8))
        ttk.Label(language, text="言語 / Language", font=("Segoe UI", 9, "bold")).pack(side="right", padx=(0, 6))
        self.language_var = tk.StringVar(value="日本語" if self.lang == "ja" else "English")
        combo = ttk.Combobox(language, textvariable=self.language_var, values=("日本語", "English"), state="readonly", width=10)
        combo.pack(side="right")
        combo.bind("<<ComboboxSelected>>", self._language_changed)

        ttk.Label(outer, text=self.t("ブラウザ自動化ランナー", "Browser Automation Runner"), font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(
            outer,
            text=self.t(
                "上級機能 — APIやローカル処理で実現できない場合だけ使用してください。Web画面変更で壊れる可能性があります。",
                "Advanced feature — use only when API/local processing cannot do the job. Website UI changes can break browser automation.",
            ),
            wraplength=900,
        ).pack(anchor="w", pady=(0, 14))

        cfg = ttk.LabelFrame(outer, text=self.t("設定", "Configuration"), padding=10)
        cfg.pack(fill="x", pady=(0, 10))
        ttk.Entry(cfg, textvariable=self.config_path).pack(side="left", fill="x", expand=True)
        ttk.Button(cfg, text=self.t("選択", "Browse"), command=self._browse).pack(side="left", padx=(8, 0))
        ttk.Button(cfg, text=self.t("検証", "Validate"), command=lambda: self._load_config(True)).pack(side="left", padx=(6, 0))

        summary = ttk.LabelFrame(outer, text=self.t("通信境界", "Network boundary"), padding=8)
        summary.pack(fill="x", pady=(0, 10))
        self.summary = ttk.Treeview(summary, columns=("item", "value"), show="headings", height=5)
        self.summary.heading("item", text=self.t("項目", "Item"))
        self.summary.heading("value", text=self.t("内容", "Value"))
        self.summary.column("item", width=220, anchor="w")
        self.summary.column("value", width=720, anchor="w")
        self.summary.pack(fill="x")

        stepbox = ttk.LabelFrame(outer, text=self.t("操作手順", "Steps"), padding=8)
        stepbox.pack(fill="both", expand=True, pady=(0, 10))
        self.steps = tk.Listbox(stepbox, height=10)
        self.steps.pack(fill="both", expand=True)

        actions = ttk.LabelFrame(outer, text=self.t("実行", "Execution"), padding=10)
        actions.pack(fill="x", pady=(0, 10))
        self.dry_btn = ttk.Button(actions, text=self.t("設定確認（Dry Run）", "Dry Run / Validate"), command=self._dry_run)
        self.dry_btn.pack(side="left")
        self.run_btn = ttk.Button(actions, text=self.t("ブラウザ実行", "Run Browser"), command=self._run_live)
        self.run_btn.pack(side="left", padx=6)
        ttk.Label(
            actions,
            text=self.t(
                "実ブラウザ実行はクリック・入力・ダウンロード等の副作用を起こし得ます。",
                "Live browser execution may click, type, download, or otherwise cause side effects.",
            ),
            wraplength=520,
        ).pack(side="right")

        logbox = ttk.LabelFrame(outer, text=self.t("結果", "Result"), padding=8)
        logbox.pack(fill="both", expand=True)
        self.log = tk.Text(logbox, wrap="word", height=10, state="disabled", font=("Consolas", 9))
        self.log.pack(fill="both", expand=True)
        ttk.Label(outer, textvariable=self.status).pack(fill="x", pady=(8, 0))
        if self._live_running:
            self.dry_btn.configure(state="disabled")
            self.run_btn.configure(state="disabled")

    def _language_changed(self, _event=None) -> None:
        self.lang = "en" if self.language_var.get() == "English" else "ja"
        save_language(APP_ID, self.lang)
        self._build()
        if self.config is not None:
            try:
                runner = BrowserRunner(self.config, dry_run=True)
                runner.run()
                self._render(runner)
            except Exception:
                pass
        self.status.set(self.t("ブラウザ実行中…", "Browser running…") if self._live_running else self.t("APIが無い場合の最終手段", "Advanced fallback only"))

    def _browse(self) -> None:
        path = filedialog.askopenfilename(
            title=self.t("ブラウザ自動化JSONを選択", "Choose Browser Automation JSON"),
            filetypes=[("JSON", "*.json"), (self.t("すべてのファイル", "All files"), "*.*")],
        )
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
            self.status.set(self.t("設定OK — 上級フォールバック", "Configuration valid — Advanced fallback"))
            return True
        except Exception as exc:
            self.config = None
            self.status.set(self.t(f"設定エラー: {type(exc).__name__}", f"Configuration error: {type(exc).__name__}"))
            if show_error:
                messagebox.showerror(self.t("設定エラー", "Configuration error"), str(exc), parent=self.root)
            return False

    @staticmethod
    def _safe_url_preview(raw_url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(raw_url)
            host = parsed.hostname or ""
            port = f":{parsed.port}" if parsed.port else ""
            path = parsed.path or "/"
            return f"{parsed.scheme}://{host}{port}{path}"
        except Exception:
            return "(URL hidden)"

    def _render(self, runner: BrowserRunner) -> None:
        for item in self.summary.get_children():
            self.summary.delete(item)
        rows = [
            (self.t("画面遷移許可ホスト", "Allowed navigation hosts"), ", ".join(sorted(runner.allowed_hosts))),
            (self.t("素材通信ホスト", "Resource-only hosts"), ", ".join(sorted(runner.resource_hosts)) or "-"),
            ("Headless", str(runner.headless)),
            ("Timeout", f"{runner.timeout_ms} ms"),
            ("Service workers", self.t("無効化", "blocked")),
        ]
        for row in rows:
            self.summary.insert("", "end", values=row)
        self.steps.delete(0, "end")
        for index, step in enumerate(runner.steps, start=1):
            if isinstance(step, dict):
                action = step.get("action", "?")
                if action == "goto":
                    detail = self._safe_url_preview(str(step.get("url", "")))
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
        if self._live_running or not self._load_config(True):
            return
        self._append(self.t(
            "Dry Run OK — 設定と通信境界のみ検証しました。ブラウザ操作は実行していません。",
            "Dry Run OK — configuration/network boundary validated. No browser actions executed.",
        ))

    def _run_live(self) -> None:
        if self._live_running or not self._load_config(True):
            return
        warning = self.t(
            "ブラウザを実際に操作します。クリック、入力、ダウンロード等が実行され、Webサービス側に副作用が発生する可能性があります。\n\nAPIで代替できないこと、Dry Run、対象アカウントを確認済みの場合だけ続行してください。",
            "This will control a real browser. Clicks, typing, downloads, or other actions may cause side effects on the website.\n\nContinue only after confirming that no API/local alternative is appropriate, Dry Run passed, and the target account is correct.",
        )
        if not messagebox.askyesno(self.t("上級ブラウザ実行", "Advanced browser execution"), warning, parent=self.root):
            return
        assert self.config is not None
        raw = self.config
        self._live_running = True
        self.dry_btn.configure(state="disabled")
        self.run_btn.configure(state="disabled")
        self.status.set(self.t("ブラウザ実行中…", "Browser running…"))

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
        self._live_running = False
        self._append(text)
        self.dry_btn.configure(state="normal")
        self.run_btn.configure(state="normal")
        self.status.set(self.t("実行完了", "Run complete") if ok else self.t("実行失敗", "Run failed"))
        if not ok:
            messagebox.showerror(self.t("ブラウザ自動化", "Browser Runner"), text[-1500:], parent=self.root)


def main() -> None:
    root = tk.Tk()
    BrowserAutomationDesktop(root)
    root.mainloop()


if __name__ == "__main__":
    main()
