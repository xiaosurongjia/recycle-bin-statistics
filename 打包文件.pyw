#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用 Python 打包工具"""

import os
import sys
import glob
import shutil
import queue
import weakref
import threading
import subprocess
import ctypes
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


# ═══════════════════════════════════════════════════════════
#  主题
# ═══════════════════════════════════════════════════════════

FONT = "Microsoft YaHei UI"
MONO = "Cascadia Mono"

THEMES = {
    "dark": {
        "BG": "#0a0b0e", "SURFACE": "#131519", "SURFACE_2": "#181b21",
        "SURFACE_3": "#1d2129", "BORDER": "#232733", "BORDER_LIGHT": "#2e3340",
        "TEXT": "#e9ebef", "TEXT_2": "#b4b9c4", "MUTED": "#7f8792",
        "DIM": "#565c68", "ACCENT": "#7c93ff", "ACCENT_2": "#5a72e0",
        "PRIMARY_FG": "#0a0b0e", "GREEN": "#5bd6a4", "YELLOW": "#f2c96d",
        "PURPLE": "#b39eff", "RED": "#f07178",
        "LOG_BG": "#05060a", "LOG_FG": "#c8ccd4",
    },
    "light": {
        "BG": "#f6f7f9", "SURFACE": "#ffffff", "SURFACE_2": "#f1f3f6",
        "SURFACE_3": "#e6e9ee", "BORDER": "#e4e7ec", "BORDER_LIGHT": "#d0d5dd",
        "TEXT": "#0f1728", "TEXT_2": "#46536b", "MUTED": "#667085",
        "DIM": "#98a2b3", "ACCENT": "#5b6cff", "ACCENT_2": "#4a5be0",
        "PRIMARY_FG": "#ffffff", "GREEN": "#12b76a", "YELLOW": "#e08c00",
        "PURPLE": "#7c3aed", "RED": "#e13b3b",
        "LOG_BG": "#eaecef", "LOG_FG": "#0f1728",
    },
}

_current_theme = "light"
_registry = []
_listeners = []


def C(role):
    return THEMES[_current_theme][role]


def reg(widget, **roles):
    try:
        ref = weakref.ref(widget)
    except TypeError:
        return widget
    _registry.append((ref, roles))
    try:
        widget.configure(**{o: C(r) for o, r in roles.items()})
    except (tk.TclError, KeyError):
        pass
    return widget


def on_theme_change(func):
    _listeners.append(func)


def setup_styles():
    s = ttk.Style()
    try:
        s.theme_use("clam")
    except tk.TclError:
        pass

    s.configure("Dark.TCombobox",
                fieldbackground=C("SURFACE_2"),
                background=C("SURFACE_2"),
                foreground=C("TEXT"),
                arrowcolor=C("MUTED"),
                borderwidth=0, padding=6,
                selectbackground=C("SURFACE_2"),
                selectforeground=C("TEXT"))
    s.map("Dark.TCombobox",
          fieldbackground=[("readonly", C("SURFACE_2")),
                           ("!disabled", C("SURFACE_2"))],
          background=[("readonly", C("SURFACE_2")),
                      ("active", C("SURFACE_3")),
                      ("!disabled", C("SURFACE_2"))],
          foreground=[("readonly", C("TEXT")),
                      ("!disabled", C("TEXT"))],
          arrowcolor=[("active", C("ACCENT")),
                      ("!disabled", C("MUTED"))])

    for orient in ("Vertical", "Horizontal"):
        s.configure(f"Modern.{orient}.TScrollbar",
                    background=C("SURFACE_3"),
                    troughcolor=C("SURFACE_2"),
                    bordercolor=C("SURFACE_2"),
                    darkcolor=C("SURFACE_3"),
                    lightcolor=C("SURFACE_3"),
                    arrowcolor=C("MUTED"),
                    gripcount=0, relief="flat",
                    borderwidth=0, arrowsize=14, width=14)
        s.map(f"Modern.{orient}.TScrollbar",
              background=[("pressed", C("ACCENT_2")),
                          ("active", C("ACCENT"))],
              arrowcolor=[("pressed", C("ACCENT")),
                          ("active", C("ACCENT"))])

    root = tk._default_root
    if root:
        root.option_add("*TCombobox*Listbox.background", C("SURFACE"))
        root.option_add("*TCombobox*Listbox.foreground", C("TEXT"))
        root.option_add("*TCombobox*Listbox.font", (FONT, 13))
        root.option_add("*TCombobox*Listbox.selectBackground", C("ACCENT"))
        root.option_add("*TCombobox*Listbox.selectForeground", C("PRIMARY_FG"))


def apply_theme(name, root=None):
    global _current_theme
    _current_theme = name
    alive = []
    for ref, roles in _registry:
        w = ref()
        if w is None:
            continue
        try:
            w.configure(**{o: C(r) for o, r in roles.items()})
            alive.append((ref, roles))
        except (tk.TclError, KeyError):
            pass
    _registry[:] = alive
    if root:
        try:
            root.configure(bg=C("BG"))
        except tk.TclError:
            pass
    setup_styles()
    for f in list(_listeners):
        try:
            f()
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
#  基础组件
# ═══════════════════════════════════════════════════════════

def make_card(parent, padx=22, pady=18):
    outer = tk.Frame(parent, bg=C("SURFACE"),
                     highlightbackground=C("BORDER"),
                     highlightthickness=1, bd=0)
    reg(outer, bg="SURFACE", highlightbackground="BORDER")
    inner = tk.Frame(outer, bg=C("SURFACE"))
    reg(inner, bg="SURFACE")
    inner.pack(fill="both", expand=True, padx=padx, pady=pady)
    return outer, inner


def card_title(parent, title, hint=""):
    row = tk.Frame(parent, bg=C("SURFACE"))
    reg(row, bg="SURFACE")
    row.pack(fill="x", pady=(0, 14))
    reg(tk.Label(row, text=title, font=(FONT, 18, "bold")),
        bg="SURFACE", fg="TEXT").pack(side="left")
    if hint:
        reg(tk.Label(row, text="  · " + hint, font=(FONT, 12)),
            bg="SURFACE", fg="DIM").pack(side="left", pady=(4, 0))


def hint_label(parent, text, wrap=900):
    lb = tk.Label(parent, text=text, font=(FONT, 11),
                  anchor="w", justify="left", wraplength=wrap)
    reg(lb, bg="SURFACE", fg="DIM")
    lb.pack(fill="x", pady=(2, 8))
    return lb


class DarkEntry(tk.Frame):
    def __init__(self, parent, textvariable, width=40):
        super().__init__(parent, bg=C("SURFACE_2"),
                         highlightbackground=C("BORDER_LIGHT"),
                         highlightthickness=1)
        reg(self, bg="SURFACE_2", highlightbackground="BORDER_LIGHT")
        self.entry = tk.Entry(self, textvariable=textvariable, width=width,
                              font=(FONT, 13), bg=C("SURFACE_2"), fg=C("TEXT"),
                              insertbackground=C("ACCENT"), bd=0, relief="flat")
        reg(self.entry, bg="SURFACE_2", fg="TEXT",
            insertbackground="ACCENT")
        self.entry.pack(padx=10, pady=7, fill="x")
        self.bind("<Button-1>", lambda e: self.entry.focus_set())

    def set_state(self, enabled):
        try:
            self.entry.configure(state="normal" if enabled else "disabled")
        except tk.TclError:
            pass


class Toggle(tk.Canvas):
    def __init__(self, parent, variable, command=None):
        super().__init__(parent, width=46, height=24, bd=0,
                         highlightthickness=0, cursor="hand2")
        reg(self, bg="SURFACE")
        self.var = variable
        self.command = command
        self.bind("<Button-1>", self._on_click)
        self.var.trace_add("write", lambda *a: self._redraw())
        on_theme_change(self._redraw)
        self._redraw()

    def _on_click(self, e):
        self.var.set(not self.var.get())
        if self.command:
            self.command()

    def _redraw(self):
        try:
            self.configure(bg=C("SURFACE"))
        except tk.TclError:
            return
        self.delete("all")
        w, h = 46, 24
        if self.var.get():
            self._rr(1, 1, w-1, h-1, 12, fill=C("ACCENT"))
            self.create_oval(w-h+2, 3, w-3, h-3, fill="#ffffff", outline="")
        else:
            self._rr(1, 1, w-1, h-1, 12, fill=C("SURFACE_3"))
            self.create_oval(3, 3, h-3, h-3, fill="#ffffff", outline="")

    def _rr(self, x1, y1, x2, y2, r, **kw):
        pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
               x2,y2-r, x2,y2, x2-r,y2, x1+r,y2,
               x1,y2, x1,y2-r, x1,y1+r, x1,y1]
        return self.create_polygon(pts, smooth=True, **kw)


class RadioPill(tk.Label):
    def __init__(self, parent, text, variable, value):
        super().__init__(parent, text=text, font=(FONT, 13, "bold"),
                         padx=16, pady=8, cursor="hand2",
                         bd=0, highlightthickness=0)
        self.var = variable
        self.value = value
        self.bind("<Button-1>", lambda e: self.var.set(self.value))
        self.var.trace_add("write", lambda *a: self._refresh())
        on_theme_change(self._refresh)
        self._refresh()

    def _refresh(self):
        try:
            if self.var.get() == self.value:
                self.configure(bg=C("ACCENT"), fg=C("PRIMARY_FG"))
            else:
                self.configure(bg=C("SURFACE_2"), fg=C("MUTED"))
        except tk.TclError:
            pass


class StepPill(tk.Label):
    SYMBOLS = ["①", "②", "③", "④"]

    def __init__(self, parent, index, title, command):
        super().__init__(parent,
                         text=f"{self.SYMBOLS[index]}  {title}",
                         font=(FONT, 13, "bold"),
                         padx=18, pady=10,
                         cursor="hand2",
                         bd=0, highlightthickness=0)
        self.index = index
        self.command = command
        self.state = "pending"
        self.bind("<Button-1>", lambda e: self.command(self.index))
        on_theme_change(self._refresh)
        self._refresh()

    def set_state(self, state):
        if self.state != state:
            self.state = state
            self._refresh()

    def _refresh(self):
        try:
            if self.state == "current":
                self.configure(bg=C("ACCENT"), fg=C("PRIMARY_FG"))
            elif self.state == "done":
                self.configure(bg=C("SURFACE_2"), fg=C("GREEN"))
            else:
                self.configure(bg=C("SURFACE_3"), fg=C("MUTED"))
        except tk.TclError:
            pass


def ghost_btn(parent, text, command, big=False):
    fnt = (FONT, 13, "bold") if big else (FONT, 12)
    b = tk.Label(parent, text=text, font=fnt,
                 padx=18, pady=10,
                 cursor="hand2",
                 bd=0, highlightthickness=0)
    reg(b, bg="SURFACE_2", fg="TEXT_2")
    b.bind("<Button-1>", lambda e: command())

    def _en(e):
        try:
            b.configure(bg=C("SURFACE_3"), fg=C("TEXT"))
        except tk.TclError:
            pass

    def _lv(e):
        try:
            b.configure(bg=C("SURFACE_2"), fg=C("TEXT_2"))
        except tk.TclError:
            pass

    b.bind("<Enter>", _en)
    b.bind("<Leave>", _lv)
    on_theme_change(lambda: _lv(None))
    return b


# ═══════════════════════════════════════════════════════════
#  新增：问号图标 + 帮助弹窗
# ═══════════════════════════════════════════════════════════

class HelpIcon(tk.Canvas):
    """小问号图标，点击弹出帮助弹窗"""

    def __init__(self, parent, help_title, help_content):
        super().__init__(parent, width=22, height=22, bd=0,
                         highlightthickness=0, cursor="hand2")
        reg(self, bg="SURFACE")
        self.help_title = help_title
        self.help_content = help_content
        self.bind("<Button-1>", self._show_help)
        self.bind("<Enter>", lambda e: self._redraw(hover=True))
        self.bind("<Leave>", lambda e: self._redraw(hover=False))
        on_theme_change(self._redraw)
        self._redraw()

    def _redraw(self, hover=False, event=None):
        try:
            self.configure(bg=C("SURFACE"))
        except tk.TclError:
            return
        self.delete("all")
        bg = C("ACCENT") if hover else C("SURFACE_3")
        fg = C("PRIMARY_FG") if hover else C("ACCENT")
        self.create_oval(1, 1, 21, 21, fill=bg, outline="")
        self.create_text(11, 11, text="?", fill=fg,
                         font=(FONT, 12, "bold"))

    def _show_help(self, event=None):
        HelpDialog(self.winfo_toplevel(),
                   self.help_title,
                   self.help_content)


class HelpDialog(tk.Toplevel):
    """自定义样式的帮助弹窗"""

    def __init__(self, parent, title, content):
        super().__init__(parent)
        self.title("帮助")
        self.configure(bg=C("BG"))
        self.resizable(False, False)
        self.transient(parent)

        card = tk.Frame(self, bg=C("SURFACE"),
                        highlightbackground=C("BORDER"),
                        highlightthickness=1)
        reg(card, bg="SURFACE", highlightbackground="BORDER")
        card.pack(fill="both", expand=True, padx=14, pady=14)

        # 标题
        reg(tk.Label(card, text=title, font=(FONT, 16, "bold")),
            bg="SURFACE", fg="TEXT").pack(anchor="w", padx=22,
                                           pady=(20, 10))

        # 内容
        reg(tk.Label(card, text=content, font=(FONT, 12),
                     justify="left", anchor="w", wraplength=520),
            bg="SURFACE", fg="TEXT_2").pack(anchor="w", padx=22,
                                             pady=(0, 20))

        # 关闭按钮
        btn = tk.Label(card, text="知道了",
                       font=(FONT, 13, "bold"),
                       bg=C("ACCENT"), fg=C("PRIMARY_FG"),
                       padx=26, pady=10, cursor="hand2")
        reg(btn, bg="ACCENT", fg="PRIMARY_FG")
        btn.pack(pady=(0, 20))
        btn.bind("<Button-1>", lambda e: self.destroy())

        # 居中到父窗口
        self.update_idletasks()
        w = max(560, self.winfo_reqwidth())
        h = self.winfo_reqheight()
        px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(0, px)}+{max(0, py)}")

        self.bind("<Escape>", lambda e: self.destroy())
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
#  主应用
# ═══════════════════════════════════════════════════════════

class PackerApp:
    LOG_H = 200

    def __init__(self, root):
        self.root = root
        root.title("Python 打包工具")
        root.configure(bg=C("BG"))
        root.minsize(960, 700)

        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        try:
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
        except Exception:
            pass

        self.log_queue = queue.Queue()
        self.is_packing = False
        self.current_step = 0
        self._prev_enabled = False

        # ── 变量（精简版）──
        self.source_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.onefile_var = tk.BooleanVar(value=True)
        self.gui_var = tk.BooleanVar(value=True)
        self.icon_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()  

        # 高级选项（只保留 5 个）
        self.adv_enabled_var = tk.BooleanVar(value=False)
        self.hidden_var = tk.StringVar()
        self.collect_all_var = tk.StringVar()
        self.data_var = tk.StringVar()
        self.exclude_var = tk.StringVar()
        self.splash_var = tk.StringVar()

        setup_styles()
        self._build_layout()
        self._scan_files()
        self._pump_log()
        self._center(1000, 760)
        self._goto_step(0)

        apply_theme("light", root)

    # ───────────────────────────────────────────
    def _center(self, w, h):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = min(w, sw - 40)
        h = min(h, sh - 80)
        x = (sw - w) // 2
        y = max(10, (sh - h) // 2 - 20)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ═══════════════════════════════════════════
    def _build_layout(self):
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_rowconfigure(3, weight=0)
        self.root.grid_rowconfigure(4, weight=0)
        self.root.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_tabs()
        self._build_content()
        self._build_footer()
        self._build_log_panel()

    # ───────────────────────────────────────────
    def _build_header(self):
        h = tk.Frame(self.root, bg=C("BG"), height=76)
        reg(h, bg="BG")
        h.grid(row=0, column=0, sticky="ew", padx=26, pady=(16, 0))
        h.grid_propagate(False)

        left = tk.Frame(h, bg=C("BG"))
        reg(left, bg="BG")
        left.pack(side="left", fill="y")
        reg(tk.Label(left, text="🐍", font=(FONT, 26)),
            bg="BG", fg="ACCENT").pack(side="left", pady=(0, 6))

        tb = tk.Frame(left, bg=C("BG"))
        reg(tb, bg="BG")
        tb.pack(side="left", padx=(12, 0), pady=(6, 0))

        title_row = tk.Frame(tb, bg=C("BG"))
        reg(title_row, bg="BG")
        title_row.pack(anchor="w")
        reg(tk.Label(title_row, text="Python 打包工具",
                     font=(FONT, 20, "bold")),
            bg="BG", fg="TEXT").pack(side="left")
        reg(tk.Label(title_row, text="PyInstaller",
                     font=(MONO, 12, "bold"),
                     padx=9, pady=2),
            bg="ACCENT", fg="PRIMARY_FG").pack(side="left", padx=(10, 0))

        right = tk.Frame(h, bg=C("BG"))
        reg(right, bg="BG")
        right.pack(side="right", fill="y", pady=(8, 0))

        self.theme_btn = tk.Label(right, text="☾",
                                   font=(FONT, 18),
                                   padx=12, pady=7,
                                   cursor="hand2",
                                   bd=0, highlightthickness=0)
        reg(self.theme_btn, bg="SURFACE_2", fg="TEXT")
        self.theme_btn.pack(side="right")
        self.theme_btn.bind("<Button-1>", lambda e: self._toggle_theme())
        self.theme_btn.bind(
            "<Enter>",
            lambda e: self.theme_btn.configure(bg=C("SURFACE_3")))
        self.theme_btn.bind(
            "<Leave>",
            lambda e: self.theme_btn.configure(bg=C("SURFACE_2")))
        on_theme_change(self._refresh_theme_btn)
        self._refresh_theme_btn()

    def _refresh_theme_btn(self):
        try:
            self.theme_btn.configure(
                text="☀" if _current_theme == "dark" else "☾")
        except tk.TclError:
            pass

    def _toggle_theme(self):
        new = "light" if _current_theme == "dark" else "dark"
        apply_theme(new, self.root)

    # ───────────────────────────────────────────
    def _build_tabs(self):
        bar = tk.Frame(self.root, bg=C("BG"))
        reg(bar, bg="BG")
        bar.grid(row=1, column=0, sticky="ew", padx=26, pady=(8, 4))

        self.step_pills = []
        titles = ["源文件", "输出设置", "图标", "高级选项"]
        for i, title in enumerate(titles):
            p = StepPill(bar, i, title, self._goto_step)
            p.pack(side="left", padx=(0, 6))
            self.step_pills.append(p)

    # ───────────────────────────────────────────
    def _build_content(self):
        self.content_wrap = tk.Frame(self.root, bg=C("BG"))
        reg(self.content_wrap, bg="BG")
        self.content_wrap.grid(row=2, column=0, sticky="nsew",
                                padx=26, pady=(8, 0))

        self.step_frames = []
        for _ in range(4):
            f = tk.Frame(self.content_wrap, bg=C("BG"))
            reg(f, bg="BG")
            f.place(in_=self.content_wrap, x=0, y=0,
                    relwidth=1, relheight=1)
            self.step_frames.append(f)

        self._build_step1(self.step_frames[0])
        self._build_step2(self.step_frames[1])
        self._build_step3(self.step_frames[2])
        self._build_step4(self.step_frames[3])

    # ── 第 1 步 ──
    def _build_step1(self, parent):
        outer, inner = make_card(parent)
        outer.pack(fill="both", expand=True)
        card_title(inner, "①  源文件", "选择要打包的 .py / .pyw")

        row = tk.Frame(inner, bg=C("SURFACE"))
        reg(row, bg="SURFACE")
        row.pack(fill="x", pady=(0, 8))

        self.src_combo = ttk.Combobox(row,
                                       textvariable=self.source_var,
                                       state="readonly",
                                       font=(FONT, 13),
                                       style="Dark.TCombobox")
        self.src_combo.pack(side="left", fill="x", expand=True, ipady=4)
        self.src_combo.bind("<<ComboboxSelected>>", self._on_src_change)

        ghost_btn(row, "刷新", self._scan_files).pack(
            side="left", padx=(8, 0))
        ghost_btn(row, "浏览…", self._browse_source).pack(
            side="left", padx=(6, 0))

        hint_label(inner,
                   "从当前目录自动列出所有 .py / .pyw 文件；\n"
                   "也可以点「浏览…」选择其他文件夹里的文件。")

    # ── 第 2 步 ──
    def _build_step2(self, parent):
        outer, inner = make_card(parent)
        outer.pack(fill="both", expand=True)
        card_title(inner, "②  输出设置")

        # ── exe 名称 ──
        r = tk.Frame(inner, bg=C("SURFACE"))
        reg(r, bg="SURFACE")
        r.pack(fill="x", pady=(0, 14))
        reg(tk.Label(r, text="exe 名称", font=(FONT, 13, "bold"),
                     width=10, anchor="w"),
            bg="SURFACE", fg="TEXT").pack(side="left")
        DarkEntry(r, self.name_var, width=40).pack(
            side="left", fill="x", expand=True)

        # ── 打包模式（提示移到右侧）──
        r = tk.Frame(inner, bg=C("SURFACE"))
        reg(r, bg="SURFACE")
        r.pack(fill="x", pady=(0, 10))
        reg(tk.Label(r, text="打包模式", font=(FONT, 13, "bold"),
                     width=10, anchor="w"),
            bg="SURFACE", fg="TEXT").pack(side="left")
        RadioPill(r, "单文件", self.onefile_var, True).pack(side="left")
        RadioPill(r, "文件夹", self.onefile_var, False).pack(
            side="left", padx=(6, 0))
        reg(tk.Label(r,
                     text="单文件：启动稍慢，方便分发　·　"
                          "文件夹：启动快，文件多",
                     font=(FONT, 11), anchor="e", justify="right"),
            bg="SURFACE", fg="DIM").pack(side="right", padx=(12, 0))

        # ── 程序类型（提示移到右侧）──
        r = tk.Frame(inner, bg=C("SURFACE"))
        reg(r, bg="SURFACE")
        r.pack(fill="x", pady=(0, 10))
        reg(tk.Label(r, text="程序类型", font=(FONT, 13, "bold"),
                     width=10, anchor="w"),
            bg="SURFACE", fg="TEXT").pack(side="left")
        RadioPill(r, "GUI 程序", self.gui_var, True).pack(side="left")
        RadioPill(r, "命令行", self.gui_var, False).pack(
            side="left", padx=(6, 0))
        reg(tk.Label(r,
                     text="GUI：隐藏黑窗口　·　命令行：保留黑窗口",
                     font=(FONT, 11), anchor="e", justify="right"),
            bg="SURFACE", fg="DIM").pack(side="right", padx=(12, 0))

        # ── 输出地址 ──
        r = tk.Frame(inner, bg=C("SURFACE"))
        reg(r, bg="SURFACE")
        r.pack(fill="x", pady=(0, 8))
        reg(tk.Label(r, text="输出地址", font=(FONT, 13, "bold"),
                     width=10, anchor="w"),
            bg="SURFACE", fg="TEXT").pack(side="left")
        DarkEntry(r, self.output_dir_var, width=40).pack(
            side="left", fill="x", expand=True)
        ghost_btn(r, "浏览…", self._browse_output).pack(
            side="left", padx=(6, 0))
        reg(tk.Label(r, text="留空则输出到 dist/",
                     font=(FONT, 11), anchor="e"),
            bg="SURFACE", fg="DIM").pack(side="right", padx=(12, 0))

    # ── 第 3 步 ──
    def _build_step3(self, parent):
        outer, inner = make_card(parent)
        outer.pack(fill="both", expand=True)
        card_title(inner, "③  图标", "可选，必须为 .ico 格式")

        row = tk.Frame(inner, bg=C("SURFACE"))
        reg(row, bg="SURFACE")
        row.pack(fill="x", pady=(0, 8))

        self.ico_combo = ttk.Combobox(row,
                                       textvariable=self.icon_var,
                                       state="readonly",
                                       font=(FONT, 13),
                                       style="Dark.TCombobox")
        self.ico_combo.pack(side="left", fill="x", expand=True, ipady=4)
        ghost_btn(row, "浏览…", self._browse_icon).pack(
            side="left", padx=(6, 0))

        # ═══════════════════════════════════════════
        # 新增：图片转 ICO 按钮
        # ═══════════════════════════════════════════
        convert_row = tk.Frame(inner, bg=C("SURFACE"))
        reg(convert_row, bg="SURFACE")
        convert_row.pack(fill="x", pady=(4, 0))
        ghost_btn(convert_row, "🖼️ 将图片转换为 .ico", 
                  self._convert_image_to_ico).pack(side="left")
        # ═══════════════════════════════════════════

        hint_label(inner,
                   "图标必须是 .ico 格式（不能直接用 png/jpg）。\n"
                   "可以到 cloudconvert.com 把 PNG 转成 ico。\n"
                   "留空则用系统默认图标。")
    # ═══════════════════════════════════════════
    #  第 4 步：精简 + 双栏 + 问号
    # ═══════════════════════════════════════════
    def _build_step4(self, parent):
        outer = tk.Frame(parent, bg=C("SURFACE"),
                         highlightbackground=C("BORDER"),
                         highlightthickness=1, bd=0)
        reg(outer, bg="SURFACE", highlightbackground="BORDER")
        outer.pack(fill="both", expand=True)

        # 标题
        head = tk.Frame(outer, bg=C("SURFACE"))
        reg(head, bg="SURFACE")
        head.pack(fill="x", padx=22, pady=(16, 8))

        reg(tk.Label(head, text="④  高级选项",
                     font=(FONT, 18, "bold")),
            bg="SURFACE", fg="TEXT").pack(side="left")
        reg(tk.Label(head, text="  ·  只有少数程序需要填写",
                     font=(FONT, 12)),
            bg="SURFACE", fg="DIM").pack(side="left", pady=(4, 0))

        # 启用开关
        sw_row = tk.Frame(outer, bg=C("SURFACE"))
        reg(sw_row, bg="SURFACE")
        sw_row.pack(fill="x", padx=22, pady=(4, 10))

        Toggle(sw_row, self.adv_enabled_var,
               command=self._toggle_adv_state).pack(side="left", padx=(0, 10))
        reg(tk.Label(sw_row, text="启用高级选项",
                     font=(FONT, 14, "bold")),
            bg="SURFACE", fg="TEXT").pack(side="left")
        reg(tk.Label(sw_row,
                     text="   打开后可以填写下面的参数",
                     font=(FONT, 11)),
            bg="SURFACE", fg="DIM").pack(side="left", pady=(4, 0))

        # 内容区
        body = tk.Frame(outer, bg=C("SURFACE"))
        reg(body, bg="SURFACE")
        body.pack(fill="both", expand=True, padx=(14, 6), pady=(4, 14))

        self.adv_canvas = tk.Canvas(body, bg=C("SURFACE"),
                                     bd=0, highlightthickness=0)
        reg(self.adv_canvas, bg="SURFACE")
        self.adv_vsb = ttk.Scrollbar(body, orient="vertical",
                                      command=self.adv_canvas.yview,
                                      style="Modern.Vertical.TScrollbar")
        self.adv_canvas.configure(yscrollcommand=self.adv_vsb.set)
        self.adv_canvas.pack(side="left", fill="both", expand=True)
        self._adv_vsb_packed = False

        self.adv_inner = tk.Frame(self.adv_canvas, bg=C("SURFACE"))
        reg(self.adv_inner, bg=C("SURFACE"))
        self._adv_win = self.adv_canvas.create_window(
            (0, 0), window=self.adv_inner, anchor="nw")

        self.adv_canvas.bind(
            "<Configure>",
            lambda e: self.adv_canvas.itemconfigure(
                self._adv_win, width=e.width))
        self.adv_inner.bind("<Configure>",
                             self._on_adv_inner_configure)

        def _wheel(e):
            self.adv_canvas.yview_scroll(int(-e.delta / 120), "units")

        def bind_wheel_rec(w):
            w.bind("<MouseWheel>", _wheel)
            for c in w.winfo_children():
                bind_wheel_rec(c)

        # 双栏
        col_left = tk.Frame(self.adv_inner, bg=C("SURFACE"))
        reg(col_left, bg="SURFACE")
        col_left.pack(side="left", fill="both", expand=True,
                       padx=(8, 10))
        col_right = tk.Frame(self.adv_inner, bg=C("SURFACE"))
        reg(col_right, bg="SURFACE")
        col_right.pack(side="left", fill="both", expand=True,
                        padx=(10, 8))

        self._adv_entries = []

        def field(parent, label, var, hint, help_title, help_text):
            # 标题行 + 问号
            row = tk.Frame(parent, bg=C("SURFACE"))
            reg(row, bg="SURFACE")
            row.pack(fill="x", pady=(10, 4))
            reg(tk.Label(row, text=label, font=(FONT, 13, "bold")),
                bg="SURFACE", fg="TEXT").pack(side="left")
            HelpIcon(row, help_title, help_text).pack(
                side="left", padx=(8, 0))

            # 输入框
            de = DarkEntry(parent, var, width=30)
            de.pack(fill="x")
            self._adv_entries.append(de)

            # 提示
            reg(tk.Label(parent, text=hint, font=(FONT, 10),
                         anchor="w", justify="left", wraplength=380),
                bg="SURFACE", fg="DIM").pack(anchor="w", pady=(2, 2))

        # ── 左栏 ──
        field(col_left,
              "隐藏导入",
              self.hidden_var,
              "一般不用填。打不开 exe 时才看这里。",
              "隐藏导入",
              "【这一栏是干什么的？】\n"
              "告诉打包工具：有些代码文件别忘了打进去。\n\n"
              "【什么时候需要填？】\n"
              "打包成功，但双击 exe 打不开，或者托盘图标不显示。\n"
              "如果程序能正常打开，这一栏就留空，不用管。\n\n"
              "【怎么填？】\n"
              "每一项写一个名字，用逗号隔开。\n"
              "名字就是你 import 的那个东西。\n\n"
              "【例子】\n"
              "如果你的程序里写了：\n"
              "    import pystray\n"
              "    from PIL import Image\n"
              "那你就填：\n"
              "    pystray,PIL,PIL.Image\n\n"
              "【千万别填】\n"
              "不要填文件名（比如 图片.png）！\n"
              "图片、图标这类文件要填到「额外数据」那一栏。\n")

        field(col_left,
              "收集全部",
              self.collect_all_var,
              "一般不用填。和上面那个差不多，二选一。",
              "收集全部",
              "【这一栏是干什么的？】\n"
              "和上一栏「隐藏导入」差不多，都是别忘打包某些东西。\n"
              "区别是：这里写一个大名字，它会把那一整包东西全打包。\n\n"
              "【该填哪个？】\n"
              "两个选一个就行，别都填。\n"
              "· 想省心 → 用这一栏，写大名字就行\n"
              "· 想 exe 小一点 → 用「隐藏导入」手动写具体名字\n\n"
              "【怎么填？】\n"
              "写包的英文名，用逗号隔开。\n\n"
              "【例子】\n"
              "    pystray,PIL\n"
              "（等于把 pystray 和 PIL 这两个包里的东西全打进去）\n")

        field(col_left,
              "额外数据",
              self.data_var,
              "把图片、配置文件一起打包进去。多个用逗号隔开，只写文件名就行。",
              "额外数据",
              "【这一栏是干什么的？】\n"
              "把图片、配置文件这类“程序要用到的小文件”\n"
              "一起打包进 exe，这样别人拿到 exe 就能直接用。\n\n"
              "【什么时候需要填？】\n"
              "你的程序要显示图标、读配置文件、放音效等，\n"
              "只要用到外部文件，就要填这里。\n\n"
              "【怎么填？超简单】\n"
              "直接把文件名写上去就行，多个文件用逗号隔开。\n\n"
              "【例子】\n"
              "情况1：只有两个图标\n"
              "    图片.png,图标.ico\n\n"
              "情况2：还有配置文件\n"
              "    图片.png,图标.ico,config.json\n\n"
              "情况3：图标在子文件夹里\n"
              "    图标/logo.ico,配置/settings.json\n"
              "（这样程序运行时会自动放到 exe 旁边的对应文件夹）\n\n"
              "【不用管什么分号】\n"
              "程序会自动帮你加好，你只写文件名即可。\n")

        # ── 右栏 ──
        field(col_right,
              "排除模块",
              self.exclude_var,
              "一般不用填。exe 超过 100MB 时才用。",
              "排除模块",
              "【这一栏是干什么的？】\n"
              "告诉打包工具：这些东西不要打包进去。\n\n"
              "【什么时候需要填？】\n"
              "打出来的 exe 文件大得离谱（比如超过 100MB）\n"
              "才需要填。正常情况下留空就行。\n\n"
              "【为什么会变大？】\n"
              "打包工具有时候会想太多，把一些你没用到的大库\n"
              "（比如画图用的 matplotlib）也塞进去了。\n"
              "排除掉能让 exe 瘦下来。\n\n"
              "【怎么填？】\n"
              "写库的英文名，用逗号隔开。\n\n"
              "【例子】\n"
              "    matplotlib,numpy,pandas\n\n"
              "【注意】\n"
              "你的程序代码里 import 过的东西，千万别填在这里，\n"
              "否则程序运行时会报错打不开。\n"
              "不确定的话，就留空，别填。\n")

        field(col_right,
              "启动画面",
              self.splash_var,
              "程序启动时先显示一张图。单文件启动太慢时才用。",
              "启动画面",
              "【这一栏是干什么的？】\n"
              "双击 exe 后，先弹出一张图片，等程序准备好\n"
              "再进入主界面。\n\n"
              "【什么时候需要填？】\n"
              "你选了「单文件」模式，双击后要等好几秒才\n"
              "出现界面，用户以为程序没反应。\n"
              "这时候加一张启动画面，用户就知道在加载。\n\n"
              "【怎么填？】\n"
              "把一张 PNG 图片放到和 py 文件同一个文件夹，\n"
              "然后在这里填图片的文件名。\n\n"
              "【例子】\n"
              "    loading.png\n"
              "    splash.png\n\n"
              "【注意】\n"
              "· 必须是 PNG 格式，jpg、bmp 不行\n"
              "· 加这张图会让程序启动慢 0.5 秒左右\n"
              "· 程序能正常启动的话，这一栏不用填\n")

        self.root.after(250, lambda: bind_wheel_rec(self.adv_inner))
        self._toggle_adv_state()

    def _on_adv_inner_configure(self, event=None):
        try:
            self.adv_canvas.update_idletasks()
            bbox = self.adv_canvas.bbox("all")
            if not bbox:
                return
            x1, y1, x2, y2 = bbox
            self.adv_canvas.configure(scrollregion=(0, 0, x2, y2))
            canvas_h = self.adv_canvas.winfo_height()
            need = y2 > canvas_h + 4
            if need and not self._adv_vsb_packed:
                self.adv_vsb.pack(side="right", fill="y")
                self._adv_vsb_packed = True
            elif not need and self._adv_vsb_packed:
                self.adv_vsb.pack_forget()
                self._adv_vsb_packed = False
        except Exception:
            pass

    def _toggle_adv_state(self):
        enabled = self.adv_enabled_var.get()
        for de in self._adv_entries:
            de.set_state(enabled)

    # ───────────────────────────────────────────
    def _build_footer(self):
        bar = tk.Frame(self.root, bg=C("BG"))
        reg(bar, bg="BG")
        bar.grid(row=3, column=0, sticky="ew", padx=26, pady=(10, 8))

        self.prev_btn = tk.Label(bar, text="←  上一步",
                                 font=(FONT, 13, "bold"),
                                 padx=22, pady=11,
                                 cursor="hand2",
                                 bd=0, highlightthickness=0)
        reg(self.prev_btn, bg="SURFACE_2", fg="TEXT_2")
        self.prev_btn.pack(side="left")
        self.prev_btn.bind("<Button-1>", lambda e: self._on_prev())
        self.prev_btn.bind("<Enter>", lambda e: self._prev_hover(True))
        self.prev_btn.bind("<Leave>", lambda e: self._prev_hover(False))

        self.next_btn = tk.Label(bar, text="下一步  →",
                                 font=(FONT, 14, "bold"),
                                 padx=28, pady=11,
                                 cursor="hand2",
                                 bd=0, highlightthickness=0)
        reg(self.next_btn, bg="ACCENT", fg="PRIMARY_FG")
        self.next_btn.pack(side="right")
        self.next_btn.bind("<Button-1>", lambda e: self._on_next())
        self.next_btn.bind("<Enter>", lambda e: self._next_hover(True))
        self.next_btn.bind("<Leave>", lambda e: self._next_hover(False))

    def _prev_hover(self, entering):
        if not self._prev_enabled or self.is_packing:
            return
        try:
            if entering:
                self.prev_btn.configure(bg=C("SURFACE_3"), fg=C("TEXT"))
            else:
                self.prev_btn.configure(bg=C("SURFACE_2"), fg=C("TEXT_2"))
        except tk.TclError:
            pass

    def _next_hover(self, entering):
        if self.is_packing:
            return
        try:
            self.next_btn.configure(
                bg=C("ACCENT_2") if entering else C("ACCENT"))
        except tk.TclError:
            pass

    # ───────────────────────────────────────────
    def _build_log_panel(self):
        outer = tk.Frame(self.root, bg=C("SURFACE"),
                         highlightbackground=C("BORDER"),
                         highlightthickness=1)
        reg(outer, bg="SURFACE", highlightbackground="BORDER")
        outer.grid(row=4, column=0, sticky="ew", padx=26, pady=(0, 18))
        outer.configure(height=self.LOG_H)
        outer.grid_propagate(False)

        head = tk.Frame(outer, bg=C("SURFACE"), height=36)
        reg(head, bg="SURFACE")
        head.pack(fill="x", padx=14, pady=(10, 4))
        head.pack_propagate(False)

        reg(tk.Label(head, text="📜  打包日志",
                     font=(FONT, 14, "bold")),
            bg="SURFACE", fg="TEXT").pack(side="left")

        self.log_status = tk.Label(head, text="就绪", font=(FONT, 12))
        reg(self.log_status, bg="SURFACE", fg="DIM")
        self.log_status.pack(side="right")

        body = tk.Frame(outer, bg=C("SURFACE"))
        reg(body, bg="SURFACE")
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.log_text = tk.Text(body, font=(MONO, 12),
                                 bg=C("LOG_BG"), fg=C("LOG_FG"),
                                 insertbackground=C("LOG_FG"),
                                 relief="flat", wrap="word",
                                 bd=0, highlightthickness=0,
                                 padx=12, pady=8,
                                 height=6)
        reg(self.log_text, bg="LOG_BG", fg="LOG_FG",
            insertbackground="LOG_FG")
        log_vsb = ttk.Scrollbar(body, orient="vertical",
                                command=self.log_text.yview,
                                style="Modern.Vertical.TScrollbar")
        self.log_text.configure(yscrollcommand=log_vsb.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        log_vsb.pack(side="right", fill="y")

        self._append("就绪。选好文件后点「开始打包」。\n")

    # ───────────────────────────────────────────
    def _goto_step(self, n):
        if n < 0 or n > 3:
            return
        self.current_step = n

        try:
            self.step_frames[n].tkraise()
            if n == 3:
                self.root.after(80, self._on_adv_inner_configure)
        except tk.TclError:
            pass

        for i, pill in enumerate(self.step_pills):
            if i == n:
                pill.set_state("current")
            elif i < n:
                pill.set_state("done")
            else:
                pill.set_state("pending")

        try:
            if n == 0:
                self.prev_btn.configure(fg=C("DIM"), cursor="arrow")
                self._prev_enabled = False
            else:
                self.prev_btn.configure(fg=C("TEXT_2"), cursor="hand2")
                self._prev_enabled = True

            if n == 3:
                self.next_btn.configure(text="🚀  开始打包")
            else:
                self.next_btn.configure(text="下一步  →")
        except tk.TclError:
            pass

    def _on_prev(self):
        if self.current_step > 0:
            self._goto_step(self.current_step - 1)

    def _on_next(self):
        if self.current_step < 3:
            self._goto_step(self.current_step + 1)
        else:
            self._start()

    # ───────────────────────────────────────────
    def _scan_files(self):
        my_name = os.path.basename(__file__)
        py_files = sorted(
            f for f in glob.glob("*.py") + glob.glob("*.pyw")
            if os.path.basename(f) != my_name
            and "打包" not in os.path.basename(f)
        )
        self.src_combo["values"] = py_files
        if py_files and not self.source_var.get():
            self.source_var.set(py_files[0])
            self.name_var.set(os.path.splitext(py_files[0])[0])

        ico_files = [""] + sorted(glob.glob("*.ico"))
        self.ico_combo["values"] = ico_files

    def _on_src_change(self, event=None):
        src = self.source_var.get()
        if src and not self.name_var.get():
            self.name_var.set(os.path.splitext(src)[0])

    def _browse_source(self):
        path = filedialog.askopenfilename(
            title="选择源文件",
            filetypes=[("Python 文件", "*.py *.pyw"),
                       ("所有文件", "*.*")])
        if path:
            self.source_var.set(path)
            if not self.name_var.get():
                self.name_var.set(
                    os.path.splitext(os.path.basename(path))[0])

    def _browse_icon(self):
        path = filedialog.askopenfilename(
            title="选择图标文件",
            filetypes=[("ICO 图标", "*.ico"),
                       ("所有文件", "*.*")])
        if path:
            self.icon_var.set(path)
    def _browse_output(self):
        path = filedialog.askdirectory(title="选择输出文件夹")
        if path:
            self.output_dir_var.set(path)

    def _convert_image_to_ico(self):
        """将用户选择的图片转换为多尺寸 ICO 文件"""
        # 1. 选择源图片
        src_path = filedialog.askopenfilename(
            title="选择要转换的图片",
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
                ("所有文件", "*.*")
            ])
        if not src_path:
            return

        # 2. 选择保存位置
        default_name = os.path.splitext(os.path.basename(src_path))[0] + ".ico"
        dst_path = filedialog.asksaveasfilename(
            title="保存为 .ico 文件",
            defaultextension=".ico",
            filetypes=[("ICO 图标", "*.ico")],
            initialfile=default_name)
        if not dst_path:
            return

        # 3. 执行转换
        try:
            from PIL import Image

            # 打开图片并转换为 RGBA（支持透明度）
            img = Image.open(src_path).convert("RGBA")

            # 定义要嵌入 ICO 的多个尺寸（Windows 图标常用尺寸）
            icon_sizes = [(16, 16), (24, 24), (32, 32),
                          (48, 48), (64, 64), (128, 128), (256, 256)]

            # 保存为 ICO（Pillow 会自动处理多尺寸和透明通道）
            img.save(dst_path, format="ICO", sizes=icon_sizes)

            # 4. 更新界面，自动选中刚生成的图标
            self.icon_var.set(dst_path)
            # 刷新 ICO 下拉列表（可选）
            ico_files = [""] + sorted(glob.glob("*.ico"))
            self.ico_combo["values"] = ico_files

            messagebox.showinfo("转换成功",
                                f"已生成 ICO 文件：\n{dst_path}")

        except ImportError:
            messagebox.showerror("缺少依赖",
                                 "需要 Pillow 库才能转换图片。\n"
                                 "请运行：pip install pillow")
        except Exception as e:
            messagebox.showerror("转换失败", f"错误信息：\n{e}")

    def _open_dist(self):
        if os.path.isdir("dist"):
            try:
                os.startfile("dist")
            except Exception as e:
                messagebox.showerror("打开失败", str(e))
        else:
            messagebox.showinfo("提示", "还没有 dist 文件夹，请先打包。")

    # ───────────────────────────────────────────
    def _set_log_status(self, text, color_role="DIM"):
        if self.log_status and self.log_status.winfo_exists():
            try:
                self.log_status.configure(text=text, fg=C(color_role))
            except tk.TclError:
                pass

    def _append(self, text):
        if self.log_text and self.log_text.winfo_exists():
            self.log_text.insert("end", text)
            self.log_text.see("end")

    def _put(self, text):
        self.log_queue.put(text)

    def _pump_log(self):
        try:
            while True:
                self._append(self.log_queue.get_nowait())
        except queue.Empty:
            pass
        self.root.after(80, self._pump_log)

    # ───────────────────────────────────────────
    def _start(self):
        if self.is_packing:
            return

        source = self.source_var.get().strip()
        if not source:
            messagebox.showwarning("缺少文件", "请先选择要打包的源文件。")
            self._goto_step(0)
            return
        if not os.path.isfile(source):
            messagebox.showerror("文件不存在", f"找不到：{source}")
            self._goto_step(0)
            return

        name = self.name_var.get().strip() or os.path.splitext(source)[0]
        icon = self.icon_var.get().strip()
        if icon and not os.path.isfile(icon):
            messagebox.showwarning("图标无效", f"找不到图标：{icon}")
            self._goto_step(2)
            return

        mode = "单文件" if self.onefile_var.get() else "文件夹"
        ptype = "GUI（无控制台）" if self.gui_var.get() else "命令行"
        summary = (
            f"源文件：{source}\n"
            f"输出名：{name}.exe\n"
            f"模式  ：{mode} · {ptype}\n"
            f"图标  ：{icon or '（无）'}\n"
            f"高级选项：{'启用' if self.adv_enabled_var.get() else '未启用'}\n"
        )
        if not messagebox.askyesno("确认打包",
                                    summary + "\n开始打包吗？"):
            return

        self.is_packing = True
        try:
            self.next_btn.configure(
                text="⏳  打包中…",
                bg=C("SURFACE_3"), fg=C("MUTED"),
                cursor="arrow")
            self.prev_btn.configure(cursor="arrow")
        except tk.TclError:
            pass

        self._set_log_status("打包中…", "YELLOW")
        if self.log_text and self.log_text.winfo_exists():
            self.log_text.delete("1.0", "end")
        self._append("═══ 开始打包 ═══\n")

        threading.Thread(target=self._worker,
                         args=(source, name, icon),
                         daemon=True).start()

    # ───────────────────────────────────────────
    #  打包核心：组装命令（硬编码 noconfirm / clean / noupx）
    # ───────────────────────────────────────────
    def _worker(self, source, name, icon):
        try:
            self._put("【1/4】检查 PyInstaller…\n")
            try:
                import PyInstaller  # noqa
                self._put("  ✅ 已安装\n\n")
            except ImportError:
                self._put("  ⚠ 未安装，正在安装…\n")
                r = subprocess.run(
                    [sys.executable, "-m", "pip", "install",
                     "pyinstaller", "pillow", "pystray"],
                    shell=False, capture_output=True, text=True)
                if r.returncode != 0:
                    self._put("  ❌ 安装失败：\n"
                              + (r.stderr or "") + "\n")
                    self._finish(False)
                    return
                self._put("  ✅ 安装完成\n\n")

            self._put("【2/4】清理旧构建…\n")
            for d in ("build", "dist"):
                if os.path.isdir(d):
                    try:
                        shutil.rmtree(d)
                        self._put(f"  已删除 {d}/\n")
                    except Exception as e:
                        self._put(f"  ⚠ 无法删除 {d}/：{e}\n")
            for spec in glob.glob("*.spec"):
                try:
                    os.remove(spec)
                    self._put(f"  已删除 {spec}\n")
                except Exception:
                    pass
            self._put("\n")

            self._put("【3/4】组装命令…\n")
            cmd = [sys.executable, "-m", "PyInstaller",
                   "--clean",
                   "--noconfirm",
                   "--noupx"]
            cmd += ["--onefile"] if self.onefile_var.get() else ["--onedir"]
            cmd += ["--noconsole"] if self.gui_var.get() else ["--console"]
            cmd += ["--name", name]
            if icon:
                cmd += ["--icon", icon]

            # 输出目录：用户填了就用，没填就用默认 dist/
            out_dir = self.output_dir_var.get().strip()
            if out_dir and os.path.isdir(out_dir):
                cmd += ["--distpath", out_dir]
            else:
                out_dir = os.path.abspath("dist")

            # 高级选项：只有启用时才加
            if self.adv_enabled_var.get():
                for h in self._split(self.hidden_var.get()):
                    cmd += ["--hidden-import", h]
                for s in self._split(self.collect_all_var.get()):
                    cmd += ["--collect-all", s]
                for d in self._split_add_data(self.data_var.get()):
                    cmd += ["--add-data", d]
                for e in self._split(self.exclude_var.get()):
                    cmd += ["--exclude-module", e]
                if self.splash_var.get().strip():
                    cmd += ["--splash", self.splash_var.get().strip()]

            cmd.append(source)
            self._put("  $ " + " ".join(self._q(c) for c in cmd) + "\n\n")

            self._put("【4/4】打包中，请稍候…\n")
            self._put("─" * 60 + "\n")

            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"

            proc = subprocess.Popen(
                cmd, shell=False,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                bufsize=1, env=env)

            for line in proc.stdout:
                self._put(line)
            proc.wait()

            self._put("─" * 60 + "\n\n")

            if proc.returncode != 0:
                self._put(f"❌ 打包失败（退出码 {proc.returncode}）\n")
                self._put("常见原因：\n")
                self._put("  · 隐藏导入缺失 → 第 ④ 步启用高级选项后补齐\n")
                self._put("  · 图标格式错 → 用在线工具把 PNG 转 ico\n")
                self._put("  · Python 版本过新 → 换 Python 3.12 再试\n")
                self._finish(False)
                return

            # 检查结果
            if self.onefile_var.get():
                exe = os.path.join(out_dir, f"{name}.exe")
            else:
                exe = os.path.join(out_dir, name, f"{name}.exe")

            if os.path.isfile(exe):
                size_mb = os.path.getsize(exe) / (1024 * 1024)
                self._put("✅ 打包成功！\n")
                self._put(f"   位置：{os.path.abspath(exe)}\n")
                self._put(f"   大小：{size_mb:.1f} MB\n")
            else:
                self._put("⚠ 打包结束，但没找到 exe，请查看输出目录\n")

            # ── 打包成功后：清理 build/ 和 .spec ──
            if self.onefile_var.get():
                try:
                    # 删除 build/
                    if os.path.isdir("build"):
                        shutil.rmtree("build")
                        self._put("🧹 已清理 build/\n")
                    # 删除 .spec
                    for spec in glob.glob("*.spec"):
                        try:
                            os.remove(spec)
                            self._put(f"🧹 已清理 {spec}\n")
                        except Exception:
                            pass
                except Exception as e:
                    self._put(f"⚠ 清理中间产物失败：{e}\n")

            self._finish(True)

        except Exception:
            import traceback
            self._put("\n❌ 出现异常：\n")
            self._put(traceback.format_exc())
            self._finish(False)

    def _finish(self, ok):
        def _do():
            self.is_packing = False
            try:
                if ok:
                    self.next_btn.configure(
                        text="🚀  开始打包",
                        bg=C("ACCENT"), fg=C("PRIMARY_FG"),
                        cursor="hand2")
                    self._set_log_status("✅ 打包成功", "GREEN")
                    if messagebox.askyesno("打包完成",
                                            "打包成功！\n\n打开 dist 文件夹？"):
                        self._open_dist()
                else:
                    self.next_btn.configure(
                        text="🚀  重试",
                        bg=C("RED"), fg="#ffffff",
                        cursor="hand2")
                    self._set_log_status("❌ 打包失败", "RED")
            except tk.TclError:
                pass
            self._goto_step(self.current_step)
        self.root.after(0, _do)

    @staticmethod
    def _split(s, sep=","):
        if not s:
            return []
        s = s.replace("，", ",").replace("；", ";")
        if sep == ",":
            s = s.replace(";", ",")
        return [p.strip() for p in s.split(sep) if p.strip()]
    @staticmethod
    def _split_add_data(s):
        """解析 --add-data 输入。支持格式：
           - 逗号分隔多项（中文逗号也行）
           - 每项可以是 "源;目标" 或 "源:目标"
           - 只写 "源" 时自动补成 "源;."
        """
        if not s:
            return []
        s = s.replace("，", ",")
        result = []
        for item in s.split(","):
            item = item.strip()
            if not item:
                continue
            # 没有写目标路径，自动补 ";."
            if ";" not in item and ":" not in item:
                item = item + ";."
            result.append(item)
        return result
    @staticmethod
    def _q(s):
        return f'"{s}"' if " " in s else s


# ═══════════════════════════════════════════════════════════
#  入口
# ═══════════════════════════════════════════════════════════

def main():
    root = tk.Tk()
    PackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()