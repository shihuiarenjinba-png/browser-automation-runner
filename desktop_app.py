from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import sys
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
            self.status.set(self.t("準備完了", "Ready"))

    def t(self, ja: str, en: str) -> str:
        return en if self.lang == "en" else ja

    def _build(self) -> None:
        if getattr(self, 'step_builder', None) is not None:
            self.builder_steps = [dict(x) for x in self.step_builder.steps]
        for child in self.root.winfo_children():
            child.destroy()
        self.root.title(self.t("ブラウザ操作の自動化", "Browser Automation Runner"))

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)
        self.guide_tab = ttk.Frame(self.notebook)
        self.step_tab = ttk.Frame(self.notebook)
        self.advanced_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.guide_tab, text=self.t("① かんたん設定", "1. Quick setup"))
        self.notebook.add(self.step_tab, text=self.t("② 操作手順", "2. Build steps"))
        self.notebook.add(self.advanced_tab, text=self.t("③ 確認・実行", "3. Preview & run"))
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
                "使い方：①保存した操作を選ぶ → ②ブラウザを開かずに試運転 → ③手順を確認してブラウザ実行します。",
                "Start here: 1. Choose a saved workflow → 2. Preview without opening the browser → 3. Review the steps, then run the browser.",
            ),
            wraplength=900,
        ).pack(anchor="w", pady=(0, 14))

        cfg = ttk.LabelFrame(outer, text=self.t("保存した操作", "Saved workflow"), padding=10)
        cfg.pack(fill="x", pady=(0, 10))
        ttk.Entry(cfg, textvariable=self.config_path).pack(side="left", fill="x", expand=True)
        ttk.Button(cfg, text=self.t("操作を選ぶ", "Choose workflow"), command=self._browse).pack(side="left", padx=(8, 0))
        ttk.Button(cfg, text=self.t("内容を確認", "Check workflow"), command=lambda: self._load_config(True)).pack(side="left", padx=(6, 0))

        summary = ttk.LabelFrame(outer, text=self.t("アクセス先の確認", "Allowed websites"), padding=8)
        summary.pack(fill="x", pady=(0, 10))
        self.summary = ttk.Treeview(summary, columns=("item", "value"), show="headings", height=5)
        self.summary.heading("item", text=self.t("項目", "Item"))
        self.summary.heading("value", text=self.t("内容", "Value"))
        self.summary.column("item", width=220, anchor="w")
        self.summary.column("value", width=720, anchor="w")
        self.summary.pack(fill="x")

        stepbox = ttk.LabelFrame(outer, text=self.t("実行する操作", "Actions to run"), padding=8)
        stepbox.pack(fill="both", expand=True, pady=(0, 10))
        self.steps = tk.Listbox(stepbox, height=10)
        self.steps.pack(fill="both", expand=True)

        actions = ttk.LabelFrame(outer, text=self.t("試運転してから実行", "Preview before running"), padding=10)
        actions.pack(fill="x", pady=(0, 10))
        self.dry_btn = ttk.Button(actions, text=self.t("ブラウザを開かず確認", "Preview without browser"), command=self._dry_run)
        self.dry_btn.pack(side="left")
        self.run_btn = ttk.Button(actions, text=self.t("確認してブラウザ実行", "Confirm and run browser"), command=self._run_live)
        self.run_btn.pack(side="left", padx=6)
        ttk.Label(
            actions,
            text=self.t(
                "本実行では設定したクリック・入力・保存などを実際のWebページで実行します。",
                "A real run performs the configured clicks, typing, downloads, and saves on the website.",
            ),
            wraplength=520,
        ).pack(side="right")

        logbox = ttk.LabelFrame(outer, text=self.t("結果", "Result"), padding=8)
        logbox.pack(fill="both", expand=True)
        self.log = tk.Text(logbox, wrap="word", height=10, state="disabled", font=("Consolas", 9))
        self.log.pack(fill="both", expand=True)
        ttk.Label(outer, textvariable=self.status).pack(fill="x", pady=(8, 0))
        self._refresh_action_state()

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
            "Webページを開き、クリック・入力・画像保存・ダウンロードなど、決めた操作を順番に自動実行します。\n"
            "まずはページ画像の保存から始め、必要に応じて「操作手順」でクリックや入力を追加できます。",
            "Automate a sequence of website actions such as navigation, clicking, form entry, screenshots, and downloads.\n"
            "Start with a page capture, then add clicks or form input in Build steps when needed.",
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
            "「操作手順」では、実行する内容を上から順に確認できます。実行前には必ず試運転を行います。",
            "Review the actions in order under Build steps. A preview is required before a real browser run.",
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
            if getattr(sys, "frozen", False):
                bundled = Path(sys.executable).resolve().parent / "pw-browsers"
                if not bundled.is_dir():
                    messagebox.showwarning(
                        self.t("Chromiumが見つかりません", "Chromium is missing"),
                        self.t("同梱Chromiumがありません。Windows用パッケージを確認してください。",
                               "Bundled Chromium is missing; check the installed package."),
                        parent=self.root)
                    return
                os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(bundled)
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
        self.status.set(self.t("ブラウザ実行中…", "Browser running…") if self._live_running else self.t("準備完了", "Ready"))
        self._refresh_action_state()

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
            self.status.set(self.t("設定を読み込みました。次に「ブラウザを開かず確認」を実行してください。",
                                   "Workflow loaded. Next, use Preview without browser."))
            self._refresh_action_state()
            return True
        except Exception as exc:
            self.config = None
            self.preview_revision = None
            self.status.set(self.t(f"設定エラー: {type(exc).__name__}", f"Configuration error: {type(exc).__name__}"))
            self._refresh_action_state()
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

    def _preview_matches_current(self) -> bool:
        if self.preview_revision is None or self.config is None:
            return False
        try:
            return self.preview_revision == self._revision(self.config)
        except (OSError, ValueError):
            return False

    def _refresh_action_state(self) -> None:
        if not hasattr(self, "dry_btn"):
            return
        if self._live_running:
            self.dry_btn.configure(state="disabled")
            self.run_btn.configure(state="disabled")
            return
        self.dry_btn.configure(state="normal")
        self.run_btn.configure(state="normal" if self._preview_matches_current() else "disabled")

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
            "試運転OK — 操作手順とアクセス先を確認しました。ブラウザ操作はまだ実行していません。",
            "Preview OK — actions and allowed websites validated. No browser actions were executed.",
        ))
        self.status.set(self.t("試運転完了。内容を確認してから実行できます。",
                               "Preview complete. Review the steps before running."))
        self._refresh_action_state()

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
            "ブラウザを実際に操作します。表示されている手順どおりにクリック・入力・ダウンロード等を実行します。\n\n対象ページと試運転結果を確認済みの場合だけ続行してください。",
            "This will control a real browser and perform the listed clicks, typing, downloads, or other actions.\n\nContinue only after reviewing the target site and preview result.",
        )
        if not messagebox.askyesno(self.t("ブラウザを実行", "Run browser workflow"), warning, parent=self.root):
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
        self.status.set(self.t("実行完了", "Run complete") if ok else self.t("実行失敗", "Run failed"))
        self._refresh_action_state()
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

def browser_smoke() -> int:
    """Offline real Chromium launch for isolated Windows packaging acceptance."""
    import tempfile
    with tempfile.TemporaryDirectory(prefix="browser-chromium-smoke-") as path:
        config = {
            "root_dir": path, "allow_hosts": ["example.com"],
            "steps": [{"action": "goto", "url": "about:blank"}],
            "headless": True,
        }
        with contextlib.redirect_stdout(io.StringIO()):
            BrowserRunner(config, dry_run=False).run()
    return 0


def main() -> None:
    root = tk.Tk()
    BrowserAutomationDesktop(root)
    root.mainloop()


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--self-test"]:
        raise SystemExit(self_test())
    if sys.argv[1:] == ["--browser-smoke"]:
        raise SystemExit(browser_smoke())
    main()
