"""Constrained Tk step editor. No browser actions before separate live approval."""
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, ttk
from guided_config import GuidedConfigError
from guided_steps import build_extra_step, build_nocode_workflow

_ACTIONS = ("click", "fill", "wait_for", "select_option", "check", "uncheck", "download")


class BrowserStepBuilder(ttk.Frame):
    def __init__(self, master, *, translate, root_var, url_var, output_var,
                 save_callback, initial_steps=None):
        super().__init__(master, padding=14)
        self.t = translate
        self.root_var = root_var
        self.url_var = url_var
        self.output_var = output_var
        self.save_callback = save_callback
        self.steps = [dict(step) for step in (initial_steps or [])]
        self.action_labels = {
            "wait_for": self.t("表示されるまで待つ", "Wait for element"),
            "click": self.t("ボタン・リンクをクリック", "Click element"),
            "fill": self.t("入力欄へ文字を入力", "Fill text input"),
            "select_option": self.t("選択リストから選ぶ", "Select an option"),
            "check": self.t("チェックを入れる", "Check a box"),
            "uncheck": self.t("チェックを外す", "Uncheck a box"),
            "download": self.t("クリックしてファイル保存", "Click and download file"),
        }
        self.action = tk.StringVar(value=self.action_labels["wait_for"])
        self.selector = tk.StringVar(value="")
        self.value = tk.StringVar(value="")
        self.filename = tk.StringVar(value="download.csv")
        self._build()
        self.refresh()

    def _build(self):
        ttk.Label(self, text=self.t(
            "操作手順を組む（JSON編集なし）", "Build browser steps without editing JSON"),
            font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 5))
        ttk.Label(self, text=self.t(
            "「はじめに」で保存先・URL・画像ファイル名を入力後、ここで操作を追加します。"
            "すべての操作は指定したHTTPSページから順番に実行されます。",
            "Set folder, URL and screenshot name in Start Here, then add actions below. "
            "All actions run sequentially on the explicitly chosen HTTPS page."),
            wraplength=890).pack(anchor="w", pady=(0, 7))
        frame = ttk.LabelFrame(self, text=self.t("追加する操作", "Add an action"), padding=10)
        frame.pack(fill="x")
        frame.columnconfigure(1, weight=1)
        values = [
            (self.t("操作", "Action"), self.action),
            (self.t("要素の指定 (CSS selector)", "Element (CSS selector)"), self.selector),
            (self.t("入力値 (fill/select_option)", "Value (fill/select_option)"), self.value),
            (self.t("保存名 (download)", "Filename (download)"), self.filename),
        ]
        for row, (label, variable) in enumerate(values):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=3, padx=(0, 10))
            if row == 0:
                widget = ttk.Combobox(
                    frame, textvariable=variable, values=tuple(self.action_labels.values()),
                    state="readonly")
                widget.bind("<<ComboboxSelected>>", self._update_action_inputs)
            else:
                widget = ttk.Entry(frame, textvariable=variable)
            widget.grid(row=row, column=1, sticky="ew", pady=3)
            if row == 2:
                self.value_entry = widget
            elif row == 3:
                self.filename_entry = widget
        self.help_text = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.help_text, wraplength=650).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=3)
        ttk.Button(frame, text=self.t("手順に追加", "Add step"),
                   command=self.add_step).grid(row=5, column=1, sticky="w", pady=5)
        self._update_action_inputs()
        ttk.Label(self, text=self.t(
            "CSS selector例: #submit / input[name='keyword'] / button.search。"
            "認証情報などは直接入力しないでください（環境変数参照を使用）。",
            "Example selectors: #submit / input[name='keyword'] / button.search. "
            "Never paste passwords or API tokens; reference an environment variable."),
            wraplength=890).pack(anchor="w", pady=5)
        group = ttk.LabelFrame(self, text=self.t("実行順（前から順に実行）", "Run order"), padding=6)
        group.pack(fill="both", expand=True, pady=4)
        self.tree = ttk.Treeview(group, columns=("action", "target"), show="headings", height=7)
        self.tree.heading("action", text=self.t("操作", "Action"))
        self.tree.heading("target", text=self.t("対象・出力", "Selector / output"))
        self.tree.column("action", width=135, stretch=False)
        self.tree.column("target", width=650)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self._load_selected_step)
        btns = ttk.Frame(group)
        btns.pack(fill="x", pady=(4, 0))
        ttk.Button(btns, text=self.t("削除", "Remove"), command=self.remove).pack(side="left")
        ttk.Button(btns, text="↑", command=lambda: self.move(-1)).pack(side="left", padx=5)
        ttk.Button(btns, text="↓", command=lambda: self.move(1)).pack(side="left", padx=5)
        ttk.Label(self, text=self.t(
            "保存するJSONには通常の入力文字列が含まれます。実行前のDry Runはブラウザ操作をしません。"
            "クリックやフォーム送信は相手サイトのデータを変更する可能性があります。",
            "Normal input text is saved inside the JSON file. Offline Dry Run does not browse. "
            "Clicks or form submissions can change remote data."),
            wraplength=890).pack(anchor="w", pady=(6, 3))
        ttk.Button(self, text=self.t("手順を新規JSONに保存し確認画面へ →",
                                    "Save steps to new JSON and preview →"),
                   command=self.save).pack(anchor="w", pady=6)

    def _selected_action(self) -> str:
        label = self.action.get()
        for action, text in self.action_labels.items():
            if text == label:
                return action
        raise GuidedConfigError("Choose a known browser action")

    def _update_action_inputs(self, _event=None) -> None:
        try:
            selected = self._selected_action()
        except GuidedConfigError:
            selected = "wait_for"
        self.value_entry.configure(
            state="normal" if selected in {"fill", "select_option"} else "disabled")
        self.filename_entry.configure(
            state="normal" if selected == "download" else "disabled")
        prompts = {
            "click": self.t("クリック後に次の操作へ進みます。フォームの送信に注意。",
                            "Clicking can submit forms or change account data."),
            "fill": self.t("入力内容を指定。パスワードは環境変数参照を使用。",
                           "Enter text; use an environment variable for passwords."),
            "wait_for": self.t("要素が表示されるまで待ちます。","Wait until the element is visible."),
            "select_option": self.t("プルダウンの値を入力します。","Specify the option value."),
            "check": self.t("チェックボックスをオンにします。", "Select a checkbox."),
            "uncheck": self.t("チェックボックスをオフにします。", "Clear a checkbox."),
            "download": self.t("ファイル名だけ指定。既存ファイルは上書きしません。",
                               "Provide a filename only; existing files are preserved."),
        }
        self.help_text.set(prompts[selected])

    def _load_selected_step(self, _event=None) -> None:
        """Double-click a step to edit the form, without executing it."""
        selected = self.tree.selection()
        if not selected:
            return
        step = self.steps[int(selected[0])]
        self.action.set(self.action_labels[step["action"]])
        self.selector.set(step["selector"])
        self.value.set(step.get("value", ""))
        self.filename.set(step.get("save_as", "download.csv").split("/")[-1])
        self._update_action_inputs()

    def refresh(self):
        selected = self.tree.selection()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, step in enumerate(self.steps):
            target = step.get("save_as", step.get("selector", ""))
            self.tree.insert("", "end", iid=str(i), values=(step["action"], target))
        if selected and selected[0] in self.tree.get_children():
            self.tree.selection_set(selected[0])

    def add_step(self):
        try:
            if len(self.steps) >= 20:
                raise GuidedConfigError("Maximum 20 intermediate actions")
            step = build_extra_step(
                action=self._selected_action(), selector=self.selector.get(),
                value=self.value.get(), filename=self.filename.get())
        except GuidedConfigError as exc:
            messagebox.showerror(self.t("設定エラー", "Invalid step"), str(exc), parent=self)
            return
        self.steps.append(step)
        self.value.set("")
        self.refresh()
        self.tree.selection_set(str(len(self.steps)-1))

    def remove(self):
        selected = self.tree.selection()
        if selected:
            self.steps.pop(int(selected[0]))
            self.refresh()

    def move(self, difference: int):
        selected = self.tree.selection()
        if not selected:
            return
        index = int(selected[0])
        other = index + difference
        if not 0 <= other < len(self.steps):
            return
        self.steps[index], self.steps[other] = self.steps[other], self.steps[index]
        self.refresh()
        self.tree.selection_set(str(other))

    def save(self):
        try:
            cfg = build_nocode_workflow(
                root_dir=self.root_var.get(), url=self.url_var.get(),
                screenshot=self.output_var.get(), additional_steps=self.steps)
        except (GuidedConfigError, OSError) as exc:
            messagebox.showerror(self.t("設定内容を確認", "Check your setup"),
                                 str(exc), parent=self)
            return
        self.save_callback(cfg)
