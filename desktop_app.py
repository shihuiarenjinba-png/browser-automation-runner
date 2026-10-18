from __future__ import annotations

import contextlib
import hashlib
import io
import json
import threading
import urllib.parse
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from browser_runner import BrowserRunner, BrowserRunnerError
from guided_config import GuidedConfigError, make_screenshot_workflow, save_new_config
from step_builder_panel import BrowserStepBuilder
from ui_language import load_language, save_language

APP_ID = "browser-automation-runner"


class BrowserAutomationDesktop:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.lang = load_language(APP_ID)
        self.root.geometry("1020x740")
        self.root.minsize(880, 640)
        self.config_path = tk.StringVar()
        self.guide_root = tk.StringVar()
        self.guide_url = tk.StringVar(value="https://example.com")
        self.guide_output = tk.StringVar(value="page.png")
        self.status = tk.StringVar(value="")
        self.config: dict | None = None
        self._live_running = False
        self.preview_revision: str | None = None
        self.builder_steps: list[dict] = []
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
        if getattr(self, 'step_builder', None) is not None:
            self.builder_steps = [dict(x) for x in self.step_builder.steps]
        for child in self.root.winfo_children():
            child.destroy()
        self.root.title(self.t("ブラウザ自動化 — 上級", "Browser Automation Runner — Advanced"))

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)
        self.guide_tab = ttk.Frame(self.notebook)
        self.step_tab = ttk.Frame(self.notebook)
        self.advanced_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.guide_tab, text=self.t("はじめに・新規設定", "Start here / New setup"))
        self.notebook.add(self.step_tab, text=self.t("操作手順を作る", "Build steps"))
        self.notebook.add(self.advanced_tab, text=self.t("詳細・試運転・実行", "Advanced / Preview / Run"))
        self._build_guide()
        self.step_builder = BrowserStepBuilder(
            self.step_tab, translate=self.t, root_var=self.guide_root,
            url_var=self.guide_url, output_var=self.guide_output,
            save_callback=self._save_builder_config, initial_steps=self.builder_steps)
        self.step_builder.pack(fill='both', expand=True)
        outer = ttk.Frame(self.advanced_tab, padding=18)
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
                "使い方：①操作JSONを選択 → ②Dry Runで設定・許可ホストを確認（ブラウザ操作なし）→ ③内容を確認して実行。APIで代替できないときだけ利用してください。",
                "Start here: 1. Choose workflow JSON → 2. Dry Run validates steps and host restrictions (no browser actions) → 3. Review and execute. Use only when an API cannot do the job.",
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

    def _build_guide(self) -> None:
        pane = ttk.Frame(self.guide_tab, padding=20)
        pane.pack(fill="both", expand=True)
        banner = ttk.Frame(pane)
        banner.pack(fill="x", pady=(0, 10))
        ttk.Label(banner, text=self.t("ブラウザ自動化とは？", "What does Browser Automation Runner do?"),
                  font=("Segoe UI", 18, "bold")).pack(side="left")
        self.guide_language = ttk.Combobox(
            banner, values=("日本語", "English"), state="readonly", width=10,
        )
        self.guide_language.set("English" if self.lang == "en" else "日本語")
        self.guide_language.pack(side="right")
        self.guide_language.bind("<<ComboboxSelected>>", self._guide_language_changed)
        ttk.Label(pane, text=self.t(
            "決めたWebページを開き、クリック・入力・画像保存などの手順を自動実行する上級者向けのWindowsアプリです。\n"
            "まずは安全な「指定ページを開いてスクリーンショットを保存」の2手順だけを作れます。\n"
            "Webサイトの操作画面が変わると失敗する場合があります。APIが利用できる場合はAPIを優先してください。",
            "Automate predefined website steps such as navigation, clicking, form entry, and screenshots.\n"
            "This guided setup creates only two steps: visit one URL and save a screenshot.\n"
            "Website UI changes can break workflows. Prefer official APIs whenever available.",
        ), wraplength=870, justify="left").pack(anchor="w", pady=(0, 14))
        fields = ttk.LabelFrame(pane, text=self.t("① 作成する操作を指定", "1. Set up a page capture"), padding=12)
        fields.pack(fill="x", pady=(0, 12))
        fields.columnconfigure(1, weight=1)
        for i, (label, var) in enumerate([
            (self.t("画像の保存用フォルダー", "Local output folder"), self.guide_root),
            (self.t("開くページのHTTPS URL", "HTTPS page to visit"), self.guide_url),
            (self.t("画像ファイル名（.png）", "Screenshot filename (.png)"), self.guide_output),
        ]):
            ttk.Label(fields, text=label).grid(row=i, column=0, sticky="w", padx=(0, 10), pady=7)
            ttk.Entry(fields, textvariable=var).grid(row=i, column=1, sticky="ew", pady=7)
        ttk.Button(fields, text=self.t("選択…", "Browse…"), command=self._choose_guide_root
                   ).grid(row=0, column=2, padx=(8, 0))
        ttk.Label(pane, text=self.t(
            "② JSONとして新規保存（この操作ではブラウザを開きません）。\n"
            "③ 次の画面でDry Runで設定を確認 → 実ブラウザ起動を承認するとページを開いて画像を保存します。\n"
            "画像が既にあるときは上書きしません。",
            "2. Save as a new JSON file (this does not open the browser).\n"
            "3. On the next screen, Dry Run validates settings. Confirm a real browser run to capture the page.\n"
            "Existing screenshots are never overwritten.",
        ), wraplength=870, justify="left").pack(anchor="w", pady=(4, 12))
        ttk.Button(pane, text=self.t("新規設定を保存して次へ →", "Save new workflow and continue →"),
                   command=self._create_guided_config).pack(anchor="w", pady=(0, 10))
        ttk.Button(pane, text=self.t("クリック・入力・保存の手順を画面で追加 →", "Build click/fill/download steps →"),
                   command=lambda: self.notebook.select(self.step_tab)).pack(anchor="w", pady=(0, 10))
        ttk.Button(pane, text=self.t("既存JSONを使う（詳細画面へ）", "Use existing JSON (advanced)"),
                   command=lambda: self.notebook.select(self.advanced_tab)).pack(anchor="w")
        ttk.Button(
            pane, text=self.t("ブラウザ実行環境を確認（通信なし）", "Check Chromium availability (offline)"),
            command=self._check_browser_runtime,
        ).pack(anchor="w", pady=(9, 0))
        ttk.Label(pane, text=self.t(
            "注意：この簡単設定ではクリックやログインは自動化しません。\n"
            "高度な操作は詳細JSONで設定します。外部サイトの利用規約と権限を守ってください。",
            "This starter workflow never clicks forms or logs in. Advanced actions require editing JSON.\n"
            "Use only sites and accounts you are authorized to automate.",
        ), wraplength=870, justify="left").pack(anchor="w", pady=(16, 0))

    def _guide_language_changed(self, _event=None) -> None:
        if self._live_running:
            self.guide_language.set("English" if self.lang == "en" else "日本語")
            return
        self.lang = "en" if self.guide_language.get() == "English" else "ja"
        save_language(APP_ID, self.lang)
        self._build()
        if self.config is not None:
            try:
                runner = BrowserRunner(self.config, dry_run=True)
                runner.run()
                self._render(runner)
            except (OSError, ValueError, BrowserRunnerError):
                pass

    def _check_browser_runtime(self) -> None:
        if self._live_running:
            return
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as client:
                installed = Path(client.chromium.executable_path).is_file()
            if installed:
                messagebox.showinfo(
                    self.t("ブラウザ環境", "Browser runtime"),
                    self.t("Chromium実行ファイルを確認しました。実際の起動確認は別途必要です。",
                           "Chromium executable found. Actual browser startup has not yet been tested."),
                    parent=self.root,
                )
            else:
                messagebox.showwarning(
                    self.t("Chromiumが見つかりません", "Chromium is missing"),
                    self.t("ブラウザ実行ファイルが見つかりません。製品パッケージを確認してください。",
                           "Chromium executable is missing. Verify the product package."),
                    parent=self.root,
                )
        except Exception as exc:
            messagebox.showerror(
                self.t("環境確認失敗", "Runtime check failed"),
                f"{type(exc).__name__}: {exc}", parent=self.root,
            )

    def _choose_guide_root(self) -> None:
        if self._live_running:
            return
        name = filedialog.askdirectory(parent=self.root)
        if name:
            self.guide_root.set(name)

    def _create_guided_config(self) -> None:
        if self._live_running:
            return
        try:
            config = make_screenshot_workflow(
                root_dir=self.guide_root.get(),
                url=self.guide_url.get(),
                filename=self.guide_output.get(),
            )
        except (GuidedConfigError, OSError) as exc:
            messagebox.showerror(self.t("設定内容を確認", "Check your settings"), str(exc), parent=self.root)
            return
        filename = filedialog.asksaveasfilename(
            parent=self.root, defaultextension=".json",
            filetypes=[("JSON", "*.json")], initialfile="page-capture.json",
        )
        if not filename:
            return
        try:
            save_new_config(filename, config)
        except OSError as exc:
            messagebox.showerror(self.t("保存できませんでした", "Could not save"), str(exc), parent=self.root)
            return
        self.preview_revision = None
        self.config_path.set(str(filename))
        self.notebook.select(self.advanced_tab)
        self._load_config(True)
        self.status.set(self.t("保存完了。次はDry Runです（ブラウザはまだ開いていません）。",
                               "Saved. Next: Dry Run (no browser was opened)."))

    def _save_builder_config(self, config: dict) -> None:
        if self._live_running:
            return
        try:
            BrowserRunner(config, dry_run=True).run()
        except (OSError, ValueError, BrowserRunnerError) as exc:
            messagebox.showerror(self.t("設定エラー", "Validation error"),
                                 str(exc), parent=self.root)
            return
        path = filedialog.asksaveasfilename(
            parent=self.root, defaultextension=".json",
            initialfile="browser-steps.json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            save_new_config(path, config)
        except OSError as exc:
            messagebox.showerror(self.t("保存失敗", "Save failed"), str(exc),
                                 parent=self.root)
            return
        self.preview_revision = None
        self.config_path.set(str(path))
        self.notebook.select(self.advanced_tab)
        self._load_config(True)
        self.status.set(self.t("保存完了。Dry Runで検証してください（ブラウザ未実行）。",
                               "Saved. Run Dry Run (browser not launched)."))

    def _language_changed(self, _event=None) -> None:
        if self._live_running:
            self.language_var.set("English" if self.lang == "en" else "日本語")
            return
        was_advanced = self.notebook.select() == str(self.advanced_tab)
        self.lang = "en" if self.language_var.get() == "English" else "ja"
        save_language(APP_ID, self.lang)
        self._build()
        if was_advanced:
            self.notebook.select(self.advanced_tab)
        if self.config is not None:
            try:
                runner = BrowserRunner(self.config, dry_run=True)
                runner.run()
                self._render(runner)
            except Exception:
                pass
        self.status.set(self.t("ブラウザ実行中…", "Browser running…") if self._live_running else self.t("APIが無い場合の最終手段", "Advanced fallback only"))

    def _browse(self) -> None:
        if self._live_running:
            return
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

    def _revision(self, raw: dict) -> str:
        canonical = json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        payload = str(Path(self.config_path.get()).expanduser().resolve()) + "\\n" + canonical
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _dry_run(self) -> None:
        if self._live_running or not self._load_config(True):
            return
        assert self.config is not None
        self.preview_revision = self._revision(self.config)
        self._append(self.t(
            "Dry Run OK — 設定と通信境界のみ検証しました。ブラウザ操作は実行していません。",
            "Dry Run OK — configuration/network boundary validated. No browser actions executed.",
        ))

    def _run_live(self) -> None:
        if self._live_running or not self._load_config(True):
            return
        assert self.config is not None
        if self.preview_revision != self._revision(self.config):
            messagebox.showwarning(
                self.t("試運転が必要", "Dry Run required"),
                self.t("現在の設定でDry Runを成功させてから実行してください。",
                       "Run Dry Run successfully with the current configuration first."),
                parent=self.root,
            )
            return
        warning = self.t(
            "ブラウザを実際に操作します。クリック、入力、ダウンロード等が実行され、Webサービス側に副作用が発生する可能性があります。\n\nAPIで代替できないこと、Dry Run、対象アカウントを確認済みの場合だけ続行してください。",
            "This will control a real browser. Clicks, typing, downloads, or other actions may cause side effects on the website.\n\nContinue only after confirming that no API/local alternative is appropriate, Dry Run passed, and the target account is correct.",
        )
        if not messagebox.askyesno(self.t("上級ブラウザ実行", "Advanced browser execution"), warning, parent=self.root):
            return
        assert self.config is not None
        raw = self.config
        # Revoke authorization before side effects, including lost responses.
        self.preview_revision = None
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


def self_test() -> int:
    """Validate packaged browser automation code without starting Chromium."""
    import tempfile
    with tempfile.TemporaryDirectory(prefix="browser-runner-self-test-") as d:
        config = make_screenshot_workflow(
            root_dir=d, url="https://example.com", filename="self-test.png",
        )
        with contextlib.redirect_stdout(io.StringIO()):
            BrowserRunner(config, dry_run=True).run()
        if (Path(d) / "screenshots").exists():
            raise RuntimeError("Dry Run unexpectedly wrote an image")
    return 0

def main() -> None:
    root = tk.Tk()
    BrowserAutomationDesktop(root)
    root.mainloop()


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--self-test"]:
        raise SystemExit(self_test())
    main()
