#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回收站字节统计器 """

import os, sys, json, csv, struct, ctypes, weakref, threading, copy, math, random, time, webbrowser
from datetime import datetime, timedelta, date
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# -------- 可选依赖 --------
try:
    import winsound
except ImportError:
    winsound = None

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except Exception:
    HAS_TRAY = False
    pystray = None

if sys.platform != 'win32':
    print("此工具仅支持 Windows 系统"); sys.exit(1)

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try: ctypes.windll.user32.SetProcessDPIAware()
    except Exception: pass

APP_DIR = os.path.join(os.environ.get('APPDATA', '.'), 'RecycleStat')
if getattr(sys, 'frozen', False):
    # 打包后：资源文件在 PyInstaller 临时解压目录里
    SCRIPT_DIR = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
else:
    # 源码运行：资源文件在脚本旁边
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(APP_DIR, 'history.json')
SETTINGS_FILE = os.path.join(APP_DIR, 'settings.json')
GAME_FILE = os.path.join(APP_DIR, 'game.json')
FONT = "Microsoft YaHei UI"
MONO = "Cascadia Mono"
# ============================================================
# 动画缓动函数
# ============================================================
def _ease_out_cubic(t):
    return 1 - (1 - t) ** 3

def _ease_out_quad(t):
    return t * (2 - t)

def _ease_in_quad(t):
    return t * t

def _ease_out_elastic(t):
    if t == 0 or t == 1:
        return t
    return 1 + (2 ** (-10 * t)) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3))

# ============================================================
# 主题
# ============================================================
THEMES = {
    "dark": {
        "BG": "#0a0b0e", "SURFACE": "#131519", "SURFACE_2": "#181b21",
        "SURFACE_3": "#1d2129", "BORDER": "#232733", "BORDER_LIGHT": "#2e3340",
        "TEXT": "#e9ebef", "TEXT_2": "#b4b9c4", "MUTED": "#7f8792",
        "DIM": "#565c68", "ACCENT": "#7c93ff", "ACCENT_2": "#5a72e0",
        "PRIMARY_FG": "#0a0b0e", "GREEN": "#5bd6a4", "YELLOW": "#f2c96d",
        "PURPLE": "#b39eff", "RED": "#f07178",
        "ROW_ODD": "#14171d", "ROW_EVEN": "#171a21", "ROW_SEL": "#2a3556",
        "GRID": "#1c2028",
    },
    "light": {
        "BG": "#f6f7f9", "SURFACE": "#ffffff", "SURFACE_2": "#f1f3f6",
        "SURFACE_3": "#e6e9ee", "BORDER": "#e4e7ec", "BORDER_LIGHT": "#d0d5dd",
        "TEXT": "#0f1728", "TEXT_2": "#46536b", "MUTED": "#667085",
        "DIM": "#98a2b3", "ACCENT": "#5b6cff", "ACCENT_2": "#4a5be0",
        "PRIMARY_FG": "#ffffff", "GREEN": "#12b76a", "YELLOW": "#e08c00",
        "PURPLE": "#7c3aed", "RED": "#e13b3b",
        "ROW_ODD": "#ffffff", "ROW_EVEN": "#f8fafc", "ROW_SEL": "#dfe6ff",
        "GRID": "#eef0f4",
    },
        "sakura": {
        "BG": "#fdf6f9", "SURFACE": "#ffffff", "SURFACE_2": "#fce7f0",
        "SURFACE_3": "#f9d4e2", "BORDER": "#f8c8d8", "BORDER_LIGHT": "#f5b8cc",
        "TEXT": "#4a2c38", "TEXT_2": "#7a4a5c", "MUTED": "#a87f92",
        "DIM": "#c9a5b6", "ACCENT": "#e91e63", "ACCENT_2": "#c2185b",
        "PRIMARY_FG": "#ffffff", "GREEN": "#22c55e", "YELLOW": "#f59e0b",
        "PURPLE": "#a855f7", "RED": "#dc2626",
        "ROW_ODD": "#ffffff", "ROW_EVEN": "#fdf6f9", "ROW_SEL": "#fce7f0",
        "GRID": "#f5e6ed",
    },
    "cyberpunk": {
        "BG": "#0a0410", "SURFACE": "#130a1f", "SURFACE_2": "#1a0d2e",
        "SURFACE_3": "#241340", "BORDER": "#3a1f5c", "BORDER_LIGHT": "#4a2a72",
        "TEXT": "#e0d4ff", "TEXT_2": "#b8a4d9", "MUTED": "#8a6cb3",
        "DIM": "#5c4480", "ACCENT": "#00e5ff", "ACCENT_2": "#00b8cc",
        "PRIMARY_FG": "#0a0410", "GREEN": "#00ff9d", "YELLOW": "#ffe600",
        "PURPLE": "#ff00e5", "RED": "#ff2d55",
        "ROW_ODD": "#130a1f", "ROW_EVEN": "#170d26", "ROW_SEL": "#2a1a4d",
        "GRID": "#1f1233",
    },
    "forest": {
        "BG": "#1a2018", "SURFACE": "#232a21", "SURFACE_2": "#2d3628",
        "SURFACE_3": "#3a4433", "BORDER": "#475540", "BORDER_LIGHT": "#5a6b50",
        "TEXT": "#e8ede4", "TEXT_2": "#c8d0be", "MUTED": "#94a08a",
        "DIM": "#6b7a5e", "ACCENT": "#7cb342", "ACCENT_2": "#689f38",
        "PRIMARY_FG": "#1a2018", "GREEN": "#8bc34a", "YELLOW": "#ffd54f",
        "PURPLE": "#ba68c8", "RED": "#ef5350",
        "ROW_ODD": "#232a21", "ROW_EVEN": "#272f24", "ROW_SEL": "#3a4d2a",
        "GRID": "#2d3628",
    },
    "sunset": {
        "BG": "#2a1810", "SURFACE": "#3a2318", "SURFACE_2": "#4a2d1f",
        "SURFACE_3": "#5c3a28", "BORDER": "#6e4a35", "BORDER_LIGHT": "#856044",
        "TEXT": "#ffe8d6", "TEXT_2": "#e0c0a0", "MUTED": "#b89478",
        "DIM": "#8a6a52", "ACCENT": "#ff7043", "ACCENT_2": "#e64a19",
        "PRIMARY_FG": "#2a1810", "GREEN": "#ffa726", "YELLOW": "#ffd54f",
        "PURPLE": "#ff8a65", "RED": "#ff5252",
        "ROW_ODD": "#3a2318", "ROW_EVEN": "#3e261a", "ROW_SEL": "#6b3a1e",
        "GRID": "#4a2d1f",
    },
    "retro": {
        "BG": "#000000", "SURFACE": "#0a0a00", "SURFACE_2": "#151500",
        "SURFACE_3": "#1f1f00", "BORDER": "#3a3a00", "BORDER_LIGHT": "#5c5c00",
        "TEXT": "#ffcc00", "TEXT_2": "#c8a000", "MUTED": "#8a7000",
        "DIM": "#5c4a00", "ACCENT": "#00ff00", "ACCENT_2": "#00cc00",
        "PRIMARY_FG": "#000000", "GREEN": "#00ff00", "YELLOW": "#ffff00",
        "PURPLE": "#ff00ff", "RED": "#ff0000",
        "ROW_ODD": "#0a0a00", "ROW_EVEN": "#0f0f00", "ROW_SEL": "#1f1f00",
        "GRID": "#1a1a00",
    },
}
_current_theme = "dark"
_registry = []
_listeners = []

def C(role): return THEMES[_current_theme][role]

def reg(widget, **roles):
    try: ref = weakref.ref(widget)
    except TypeError: return widget
    _registry.append((ref, roles))
    try: widget.configure(**{o: C(r) for o, r in roles.items()})
    except tk.TclError: pass
    return widget

def on_theme_change(func): _listeners.append(func)

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*[max(0,min(255,int(x))) for x in rgb])

def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    r1,g1,b1 = hex_to_rgb(c1); r2,g2,b2 = hex_to_rgb(c2)
    return rgb_to_hex((r1+(r2-r1)*t, g1+(g2-g1)*t, b1+(b2-b1)*t))

def apply_theme(name, root=None):
    global _current_theme
    _current_theme = name
    alive = []
    for ref, roles in _registry:
        w = ref()
        if w is None: continue
        try:
            w.configure(**{o: C(r) for o, r in roles.items()})
            alive.append((ref, roles))
        except tk.TclError: pass
    _registry[:] = alive
    if root:
        try: root.configure(bg=C("BG"))
        except tk.TclError: pass
    setup_ttk_styles()
    for f in list(_listeners):
        try: f()
        except Exception: pass

def setup_ttk_styles():
    s = ttk.Style()
    try: s.theme_use('clam')
    except tk.TclError: pass
    s_ = load_settings()
    fs = int(s_.get("table_font_size", 12))
    hs = int(s_.get("heading_font_size", 11))
    rh = int(s_.get("table_row_height", 40))
    s.configure("Recycle.Treeview",
                background=C("SURFACE"), fieldbackground=C("SURFACE"),
                foreground=C("TEXT_2"),
                borderwidth=0, rowheight=rh, font=(FONT, fs))
    s.configure("Recycle.Treeview.Heading",
                background=C("SURFACE_2"), foreground=C("MUTED"),
                borderwidth=0, relief="flat",
                font=(FONT, hs, "bold"), padding=(10, 10))
    s.map("Recycle.Treeview",
          background=[("selected", C("ROW_SEL"))],
          foreground=[("selected", C("TEXT"))])
    s.map("Recycle.Treeview.Heading",
          background=[("active", C("SURFACE_3"))])
    # 滚动条样式（现代扁平风）
    for orient in ("Vertical", "Horizontal"):
        s.configure(f"Modern.{orient}.TScrollbar",
                    background=C("SURFACE_3"),
                    troughcolor=C("SURFACE_2"),
                    bordercolor=C("SURFACE_2"),
                    darkcolor=C("SURFACE_3"),
                    lightcolor=C("SURFACE_3"),
                    arrowcolor=C("MUTED"),
                    gripcount=0,
                    relief="flat",
                    borderwidth=0,
                    arrowsize=14,
                    width=10)
        # 鼠标悬停 / 拖动时的颜色
        s.map(f"Modern.{orient}.TScrollbar",
              background=[("pressed", C("ACCENT_2")),
                          ("active", C("ACCENT"))],
              arrowcolor=[("pressed", C("ACCENT")),
                          ("active", C("ACCENT"))],
              darkcolor=[("pressed", C("ACCENT_2")),
                         ("active", C("ACCENT"))],
              lightcolor=[("pressed", C("ACCENT_2")),
                          ("active", C("ACCENT"))])
    s.configure("Modern.TCombobox",
                fieldbackground=C("SURFACE_2"), background=C("SURFACE_2"),
                foreground=C("TEXT"), arrowcolor=C("MUTED"),
                borderwidth=0, padding=6,
                selectbackground=C("SURFACE_2"), selectforeground=C("TEXT"))
    s.map("Modern.TCombobox",
          fieldbackground=[("readonly", C("SURFACE_2")),
                           ("disabled", C("SURFACE_3")),
                           ("!disabled", C("SURFACE_2"))],
          background=[("readonly", C("SURFACE_2")),
                      ("active", C("SURFACE_3")),
                      ("!disabled", C("SURFACE_2"))],
          foreground=[("readonly", C("TEXT")),
                      ("disabled", C("DIM")),
                      ("!disabled", C("TEXT"))],
          selectbackground=[("readonly", C("SURFACE_2"))],
          selectforeground=[("readonly", C("TEXT"))],
          arrowcolor=[("active", C("ACCENT")), ("!disabled", C("MUTED"))])
    root = tk._default_root
    if root:
        root.option_add("*TCombobox*Listbox.background", C("SURFACE"))
        root.option_add("*TCombobox*Listbox.foreground", C("TEXT"))
        root.option_add("*TCombobox*Listbox.selectBackground", C("ACCENT"))
        root.option_add("*TCombobox*Listbox.selectForeground", C("PRIMARY_FG"))

# ============================================================
# 成就
# ============================================================
ACHIEVEMENTS = [
    {"id": "first",       "name": "初次告别",   "desc": "删除第一个文件", "points": 10},
    {"id": "files100",    "name": "百人斩",     "desc": "累计删除 100 个文件", "points": 50},
    {"id": "files1000",   "name": "千人斩",     "desc": "累计删除 1000 个文件", "points": 200},
    {"id": "gb1",         "name": "1GB 起步",   "desc": "累计删除 1 GB", "points": 100},
    {"id": "gb10",        "name": "十全十美",   "desc": "累计删除 10 GB", "points": 300},
    {"id": "gb100",       "name": "百 G 斩",    "desc": "累计删除 100 GB", "points": 1000},
    {"id": "tb1",         "name": "TB 俱乐部",  "desc": "累计删除 1 TB", "points": 5000},
    {"id": "dir",         "name": "清扫队长",   "desc": "删除过一个文件夹", "points": 20},
    {"id": "big100m",     "name": "大手笔",     "desc": "单次删除 100 MB 以上", "points": 50},
    {"id": "big1g",       "name": "挥金如土",   "desc": "单次删除 1 GB 以上", "points": 200},
    {"id": "combo10",     "name": "连击达人",   "desc": "达成 10 连击", "points": 150},
    {"id": "night_owl",   "name": "夜猫子",     "desc": "凌晨2点到5点之间清理文件", "points": 80},
    {"id": "early_bird",  "name": "早起的鸟儿", "desc": "清晨6点到8点之间清理文件", "points": 80},
    {"id": "weekend",     "name": "周末奋斗者", "desc": "在周末清理文件", "points": 30},
    {"id": "clean_master","name": "清理大师",   "desc": "单次扫描清理超过100个文件", "points": 300},
]

# ============================================================
# 设置 & 布局
# ============================================================
# ============================================================
# 商城商品表
# ============================================================
SHOP_THEMES = [
    {"id": "sakura",    "name": "樱花粉",   "desc": "浅色底 + 粉色强调",       "price": 300, "icon": "🌸"},
    {"id": "forest",    "name": "森林绿",   "desc": "暗绿底 + 米黄字",         "price": 400, "icon": "🌲"},
    {"id": "sunset",    "name": "落日橙",   "desc": "暖橙底 + 深棕字",         "price": 400, "icon": "🍊"},
    {"id": "cyberpunk", "name": "赛博朋克", "desc": "黑紫底 + 霓虹青",         "price": 600, "icon": "🌃"},
    {"id": "retro",     "name": "复古 DOS", "desc": "黑底 + 荧光黄绿，像老终端", "price": 800, "icon": "📼"},
]

SHOP_SFX = [
    {"id": "8bit",     "name": "8-bit 复古", "desc": "像素游戏的哔哔声",   "price": 400, "icon": "🎮"},
    {"id": "piano",    "name": "悠扬钢琴",   "desc": "柔和的和弦",         "price": 400, "icon": "🎹"},
    {"id": "robot",    "name": "机械合成",   "desc": "低沉的合成音",       "price": 400, "icon": "🤖"},
    {"id": "zen",      "name": "禅意",       "desc": "很轻的木鱼和钟声",   "price": 400, "icon": "🧘"},
    {"id": "arcade",   "name": "街机厅",     "desc": "90 年代街机音效",    "price": 500, "icon": "🕹️"},
    {"id": "crystal",  "name": "水晶音",     "desc": "清脆的玻璃声",       "price": 500, "icon": "💎"},
    {"id": "orchestra","name": "交响乐",     "desc": "低沉的弦乐与管乐",   "price": 600, "icon": "🎻"},
    {"id": "laser",    "name": "激光枪",     "desc": "科幻电影的高频能量", "price": 700, "icon": "🔫"},
    {"id": "ghost",    "name": "幽灵",       "desc": "飘忽不定的低吟",     "price": 600, "icon": "👻"},
]

SHOP_TITLES = [
    # ===== 原 5 个 =====
    {"id": "t_rookie",  "name": "见习清道夫",   "desc": "刚入行的菜鸟",
     "price": 200,  "icon": "🪣",
     "bg": "#6b7a5e", "fg": "#ffffff", "border": "#8a9a78"},
    {"id": "t_senior",  "name": "资深清道夫",   "desc": "已经清出经验了",
     "price": 500,  "icon": "🧹",
     "bg": "#2e7d32", "fg": "#ffffff", "border": "#4caf50"},
    {"id": "t_scav",    "name": "数字拾荒者",   "desc": "硬盘的拾荒专家",
     "price": 1000, "icon": "⛏️",
     "bg": "#1565c0", "fg": "#ffffff", "border": "#42a5f5"},
    {"id": "t_surgeon", "name": "硬盘外科医生", "desc": "精准切除数字肿瘤",
     "price": 2000, "icon": "🩺",
     "bg": "#6a1b9a", "fg": "#ffffff", "border": "#ab47bc"},
    {"id": "t_king",    "name": "电子垃圾之王", "desc": "所有垃圾臣服于你",
     "price": 5000, "icon": "👑",
     "bg": "#c9a961", "fg": "#2a1810", "border": "#ffd700"},
    {"id": "t_intern",  "name": "回收站实习生", "desc": "第一次接触数字垃圾",
     "price": 100,  "icon": "📎",
     "bg": "#8a8a8a", "fg": "#ffffff", "border": "#a8a8a8"},
    {"id": "t_janitor", "name": "数据保洁员",   "desc": "日复一日的清理工作",
     "price": 300,  "icon": "🧴",
     "bg": "#00897b", "fg": "#ffffff", "border": "#26a69a"},
    {"id": "t_ninja",   "name": "影之清道夫",   "desc": "无声无息地让文件消失",
     "price": 800,  "icon": "🥷",
     "bg": "#212121", "fg": "#f07178", "border": "#f07178"},
    {"id": "t_wizard",  "name": "存储巫师",     "desc": "一念之间释放上百GB",
     "price": 1500, "icon": "🧙",
     "bg": "#5c2d91", "fg": "#e0d4ff", "border": "#b39eff"},
    {"id": "t_dragon",  "name": "文件巨龙",     "desc": "吞噬一切无用数据",
     "price": 3000, "icon": "🐉",
     "bg": "#c62828", "fg": "#ffe082", "border": "#ffb300"},
    {"id": "t_phoenix", "name": "重生凤凰",     "desc": "让硬盘浴火重生",
     "price": 4000, "icon": "🔥",
     "bg": "#e64a19", "fg": "#fff3e0", "border": "#ffc107"},
    {"id": "t_ghost",   "name": "幽灵清理者",   "desc": "你甚至不确定是否见过它",
     "price": 600,  "icon": "👻",
     "bg": "#37474f", "fg": "#b0bec5", "border": "#90a4ae"},
    {"id": "t_legend",  "name": "传奇清道夫",   "desc": "被写进回收站史册",
     "price": 8000, "icon": "⚔️",
     "bg": "#1a237e", "fg": "#ffd700", "border": "#ffd700"},
    {"id": "t_god",     "name": "删除之神",     "desc": "你的鼠标就是审判之剑",
     "price": 12000,"icon": "⚡",
     "bg": "#000000", "fg": "#ffe600", "border": "#00e5ff"},
    {"id": "t_void",    "name": "虚空之主",     "desc": "万物皆空，唯你独尊",
     "price": 20000,"icon": "🌌",
     "bg": "#0a0410", "fg": "#ff00e5", "border": "#00e5ff"},
]

SHOP_ANIM = [
    {"id": "tree",      "name": "树木生长", "desc": "分形树从地面缓缓生长",   "price": 300, "icon": "🌳"},
    {"id": "fireworks", "name": "彩虹烟花", "desc": "七色烟花炸满屏幕",       "price": 300, "icon": "🎆"},
    {"id": "pixel",     "name": "像素爆炸", "desc": "8-bit 像素块四散飞溅",   "price": 300, "icon": "🌌"},
    {"id": "whale",     "name": "蓝鲸游走", "desc": "一头像素蓝鲸游过屏幕",   "price": 300, "icon": "🐳"},
    {"id": "ripple",    "name": "水波纹",   "desc": "八圈涟漪从中心荡开",     "price": 350, "icon": "💧"},
    {"id": "lightning", "name": "雷电",     "desc": "雷光从天空劈下",         "price": 400, "icon": "⚡"},
    {"id": "tornado",   "name": "龙卷风",   "desc": "粒子螺旋升腾",           "price": 450, "icon": "🌪️"},
    {"id": "blackhole", "name": "黑洞吞噬", "desc": "万物向中心坠落",         "price": 600, "icon": "🕳️"},
    {"id": "rainbow",   "name": "彩虹雨",   "desc": "彩色光柱从天而降",       "price": 400, "icon": "🌈"},
]

LUCKY_PRICE = 200   # 抽奖一次的价格

# 成就分级：铜/银/金/钻石
ACHIEVEMENT_TIER = {
    "first":       "bronze",
    "dir":         "bronze",
    "weekend":     "bronze",
    "files100":    "silver",
    "gb1":         "silver",
    "big100m":     "silver",
    "combo10":     "silver",
    "night_owl":   "silver",
    "early_bird":  "silver",
    "files1000":   "gold",
    "gb10":        "gold",
    "big1g":       "gold",
    "clean_master":"gold",
    "gb100":       "diamond",
    "tb1":         "diamond",
}

TIER_INFO = {
    "bronze":  {"name": "铜",   "color": "#cd7f32", "icon": "🥉", "mult": 1.0},
    "silver":  {"name": "银",   "color": "#a8b8c8", "icon": "🥈", "mult": 1.5},
    "gold":    {"name": "金",   "color": "#f2c96d", "icon": "🥇", "mult": 2.0},
    "diamond": {"name": "钻石", "color": "#7c93ff", "icon": "💎", "mult": 3.0},
}

DEFAULT_LAYOUT = {
    "hero":        {"relx": 0.00, "rely": 0.00, "relwidth": 1.00, "relheight": 0.28},
    "stat_cur":    {"relx": 0.00,  "rely": 0.30, "relwidth": 0.235, "relheight": 0.19},
    "stat_items":  {"relx": 0.255, "rely": 0.30, "relwidth": 0.235, "relheight": 0.19},
    "stat_files":  {"relx": 0.510, "rely": 0.30, "relwidth": 0.235, "relheight": 0.19},
    "stat_drives": {"relx": 0.765, "rely": 0.30, "relwidth": 0.235, "relheight": 0.19},
    "chart":       {"relx": 0.00, "rely": 0.51, "relwidth": 0.49, "relheight": 0.47},
    "ext":         {"relx": 0.51, "rely": 0.51, "relwidth": 0.49, "relheight": 0.47},
}
DEFAULT_SETTINGS = {
    "theme": "dark",
    "scan_interval": 60,
    "startup_scan": True,
    "table_font_size": 12,
    "heading_font_size": 11,
    "table_row_height": 40,
    "max_table_rows": 5000,
    "type_top_n": 10,
    "min_file_size": 0,
    "ignore_exts": "",
    "overview_layout": None,
    "motion_enabled": True,
    "sfx_enabled": True,
    "neon_mode": True,
    "tray_enabled": True,
    "chart_days": 7,
    "table_column_widths": None,
}
_settings_cache = None

def load_settings():
    global _settings_cache
    if _settings_cache is not None: return _settings_cache
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            d = json.load(f)
        r = dict(DEFAULT_SETTINGS); r.update(d)
    except Exception:
        r = dict(DEFAULT_SETTINGS)
    _settings_cache = r
    return r

def save_settings(d):
    global _settings_cache
    _settings_cache = d
    try:
        os.makedirs(APP_DIR, exist_ok=True)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception: pass

# ============================================================
# 账本 & 游戏数据
# ============================================================
def _normalize_ext(e):
    if e in ("（文件夹）", "(文件夹)", "文件夹"):
        return "文件夹"
    return e

def load_history():
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            h = json.load(f)
        h.setdefault("seen", {})
        h.setdefault("total_bytes", 0)
        h.setdefault("total_files", 0)
        h.setdefault("total_items", 0)
        changed = False
        for rec in h["seen"].values():
            ne = _normalize_ext(rec.get("ext", ""))
            if ne != rec.get("ext"):
                rec["ext"] = ne; changed = True
        if changed: save_history(h)
        return h
    except Exception:
        return {"seen": {}, "total_bytes": 0, "total_files": 0, "total_items": 0}

def save_history(h):
    try:
        os.makedirs(APP_DIR, exist_ok=True)
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(h, f, ensure_ascii=False, indent=2)
    except Exception: pass

DEFAULT_GAME = {
    "achievements": [],
    "max_single": 0,
    "max_combo": 0,
    "has_dir": False,
    "points": 0,
    "total_cleared_bytes": 0,
    "total_cleared_files": 0,
    # ===== 商城相关 =====
    "unlocked_themes": ["dark", "light"],
    "unlocked_sfx": ["default"],
    "unlocked_anim": [],
    "unlocked_titles": [],
    "active_theme": "dark",
    "active_sfx": "default",
    "active_anim": "none",
    "active_title": "",
    "lucky_count": 0,
}

def load_game():
    try:
        with open(GAME_FILE, 'r', encoding='utf-8') as f:
            d = json.load(f)
        r = dict(DEFAULT_GAME); r.update(d)
        return r
    except Exception:
        return dict(DEFAULT_GAME)

def save_game(g):
    try:
        os.makedirs(APP_DIR, exist_ok=True)
        with open(GAME_FILE, 'w', encoding='utf-8') as f:
            json.dump(g, f, ensure_ascii=False, indent=2)
    except Exception: pass

# ============================================================
# 工具
# ============================================================
def get_drives():
    drives = []
    bm = ctypes.windll.kernel32.GetLogicalDrives()
    for i in range(26):
        if bm & (1 << i): drives.append(f"{chr(65+i)}:\\")
    return drives

def human_size(n):
    if n is None: return "—"
    if n < 1024: return f"{n} B"
    units = ["KB", "MB", "GB", "TB", "PB", "EB"]
    v = float(n)
    for u in units:
        v /= 1024
        if v < 1024: return f"{v:.2f} {u}"
    return f"{v:.2f} ZB"

def compact_size(n):
    """图表数值标签：2.57GB / 123.4MB / 512B"""
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "—"
    if n <= 0:
        return "0B"
    if n < 1024:
        return f"{int(n)}B"
    units = ["KB", "MB", "GB", "TB", "PB"]
    for u in units:
        n /= 1024
        if n < 1024:
            if n < 10:
                return f"{n:.2f}{u}"    # 2.57GB
            if n < 100:
                return f"{n:.1f}{u}"    # 23.4MB
            return f"{n:.0f}{u}"        # 123MB
    return f"{n:.1f}EB"

def fmt_int(n):
    try: return f"{int(n):,}"
    except Exception: return "—"

def filetime_to_dt(ft):
    if not ft: return None
    try: return datetime(1601,1,1) + timedelta(microseconds=ft/10)
    except Exception: return None

def parse_i_file(path):
    try:
        with open(path,'rb') as f: data = f.read()
    except OSError: return None, None
    if len(data) < 24: return None, None
    try:
        ft = struct.unpack('<Q', data[16:24])[0]
        dt = filetime_to_dt(ft)
        if len(data) >= 28:
            plen = struct.unpack('<I', data[24:28])[0]
            raw = data[28:28+plen*2]
            orig = raw.decode('utf-16-le', errors='ignore').rstrip('\x00')
            return orig or None, dt
    except Exception: pass
    return None, None

def measure(path):
    if os.path.isfile(path):
        try: return os.path.getsize(path), 1
        except OSError: return 0, 0
    total, count = 0, 0
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f)); count += 1
            except OSError: pass
    return total, count

def extract_ext(path, is_dir):
    if is_dir: return "文件夹"
    _, ext = os.path.splitext(path or "")
    return ext.lower() if ext else "(无扩展名)"

def extract_name(path, fallback):
    if not path: return fallback or "—"
    p = path.replace("/", "\\").rstrip("\\")
    if not p: return path
    return p.split("\\")[-1] or p

def parse_ignored_exts(s):
    if not s: return set()
    parts = [x.strip().lower() for x in s.replace(";", ",").split(",")]
    return {p if p.startswith(".") else "." + p for p in parts if p}

def calc_level(total_bytes):
    gb = total_bytes / (1024**3)
    return int(gb) + 1, gb

# ============================================================
# 扫描
# ============================================================
def scan():
    st = load_settings()
    min_size = int(st.get("min_file_size", 0))
    ignored_exts = parse_ignored_exts(st.get("ignore_exts", ""))

    per_drive = {}
    items = []
    for drive in get_drives():
        rb = os.path.join(drive, '$Recycle.Bin')
        if not os.path.isdir(rb): continue
        try: sids = os.listdir(rb)
        except OSError: continue
        for sid in sids:
            sid_path = os.path.join(rb, sid)
            if not os.path.isdir(sid_path): continue
            try: entries = os.listdir(sid_path)
            except OSError: continue
            for name in entries:
                if not name.startswith('$R'): continue
                full = os.path.join(sid_path, name)
                i_path = os.path.join(sid_path, '$I' + name[2:])
                orig, dt = parse_i_file(i_path)
                size, cnt = measure(full)
                is_dir = os.path.isdir(full)
                orig_safe = orig or name
                ext = extract_ext(orig_safe, is_dir)
                if size < min_size: continue
                if ext in ignored_exts: continue
                key = f"{drive}|{sid}|{name}"
                items.append({
                    "key": key, "size": size, "files": cnt,
                    "orig": orig_safe,
                    "filename": extract_name(orig_safe, name),
                    "time": dt.strftime('%Y-%m-%d %H:%M:%S') if dt else None,
                    "is_dir": is_dir, "drive": drive, "ext": ext,
                })
                d = per_drive.setdefault(drive, [0,0,0])
                d[0] += size; d[1] += cnt; d[2] += 1
    return per_drive, items

# ============================================================
# 音效
# ============================================================
def _find_windows_sound(filename):
    """在 Windows\Media 目录中查找系统音效文件，返回完整路径或 None。"""
    try:
        windir = os.environ.get("WINDIR", r"C:\Windows")
        path = os.path.join(windir, "Media", filename)
        if os.path.isfile(path):
            return path
    except Exception:
        pass
    return None

class Sfx:
    def __init__(self):
        self.enabled = True
        self.pack = "default"
        self._lock = threading.Lock()

    def _play_wav(self, path):
        try:
            winsound.PlaySound(
                path,
                winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
            )
        except Exception:
            pass

    def _play_beep_seq(self, seq):
        for freq, ms, gap in seq:
            try:
                winsound.Beep(freq, ms)
                if gap:
                    time.sleep(gap / 1000.0)
            except Exception:
                pass

    # 音效包定义：
    #   值 = ("wav", "文件名")  或  ("beep", [(freq, ms, gap), ...])
    _PACKS = {
        # 默认：经典系统提示音
        "default": {
            "delete":      ("wav", "Windows Ding.wav"),
            "levelup":     ("wav", "chimes.wav"),
            "achievement": ("wav", "tada.wav"),
            "combo":       ("wav", "Windows Pop-up Blocked.wav"),
            "purchase":    ("wav", "Windows Notify System Generic.wav"),
            "error":       ("wav", "Windows Error.wav"),
        },
        # 8-bit 复古：短促、数字化
        "8bit": {
            "delete":      ("wav", "Windows Navigation Start.wav"),
            "levelup":     ("wav", "Windows Feed Discovered.wav"),
            "achievement": ("wav", "chimes.wav"),
            "combo":       ("wav", "Windows Menu Command.wav"),
            "purchase":    ("wav", "Windows Pop-up Blocked.wav"),
            "error":       ("wav", "Windows Hardware Fail.wav"),
        },
        # 钢琴：和弦 + 清脆铃音
        "piano": {
            "delete":      ("wav", "chord.wav"),
            "levelup":     ("wav", "chimes.wav"),
            "achievement": ("wav", "Windows Notify.wav"),
            "combo":       ("wav", "ding.wav"),
            "purchase":    ("wav", "Windows Notify System Generic.wav"),
            "error":       ("wav", "Windows Exclamation.wav"),
        },
        # 机械合成：硬件相关音效
        "robot": {
            "delete":      ("wav", "Windows Hardware Remove.wav"),
            "levelup":     ("wav", "Windows Hardware Insert.wav"),
            "achievement": ("wav", "Windows Feed Discovered.wav"),
            "combo":       ("wav", "Windows Menu Command.wav"),
            "purchase":    ("wav", "Windows Notify System Generic.wav"),
            "error":       ("wav", "Windows Hardware Fail.wav"),
        },
        # 禅意：温和、低沉的氛围音
        "zen": {
            "delete":      ("wav", "Windows Balloon.wav"),
            "levelup":     ("wav", "Windows Foreground.wav"),
            "achievement": ("wav", "Windows Background.wav"),
            "combo":       ("wav", "Windows Minimize.wav"),
            "purchase":    ("wav", "Windows Notify Messaging.wav"),
            "error":       ("wav", "Windows Information Bar.wav"),
        },
        # 街机厅：轻快短促，像老游戏机
        "arcade": {
            "delete":      ("wav", "Windows Navigation Start.wav"),
            "levelup":     ("wav", "Windows Feed Discovered.wav"),
            "achievement": ("wav", "tada.wav"),
            "combo":       ("wav", "Windows Pop-up Blocked.wav"),
            "purchase":    ("wav", "Windows Notify Calendar.wav"),
            "error":       ("wav", "Windows Exclamation.wav"),
        },
        # 水晶音：清脆的玻璃/铃声
        "crystal": {
            "delete":      ("wav", "ding.wav"),
            "levelup":     ("wav", "Windows Notify Calendar.wav"),
            "achievement": ("wav", "Windows Print complete.wav"),
            "combo":       ("wav", "Windows Pop-up Blocked.wav"),
            "purchase":    ("wav", "Windows Notify Email.wav"),
            "error":       ("wav", "Windows Critical Stop.wav"),
        },
        # 交响乐：长音、层叠和声
        "orchestra": {
            "delete":      ("wav", "chord.wav"),
            "levelup":     ("wav", "chimes.wav"),
            "achievement": ("wav", "tada.wav"),
            "combo":       ("wav", "Windows Notify.wav"),
            "purchase":    ("wav", "Windows Notify System Generic.wav"),
            "error":       ("wav", "Windows Critical Stop.wav"),
        },
        # 激光枪：高频、能量感
        "laser": {
            "delete":      ("wav", "Windows Navigation Start.wav"),
            "levelup":     ("wav", "Windows Feed Discovered.wav"),
            "achievement": ("wav", "Windows Notify Calendar.wav"),
            "combo":       ("wav", "Windows Message Nudge.wav"),
            "purchase":    ("wav", "Windows Notify Email.wav"),
            "error":       ("wav", "Windows Hardware Fail.wav"),
        },
        # 幽灵：飘忽、低沉的氛围
        "ghost": {
            "delete":      ("wav", "Windows Balloon.wav"),
            "levelup":     ("wav", "Windows Foreground.wav"),
            "achievement": ("wav", "Windows Background.wav"),
            "combo":       ("wav", "Windows Proximity Notification.wav"),
            "purchase":    ("wav", "Windows Notify Messaging.wav"),
            "error":       ("wav", "Windows Critical Stop.wav"),
        },
    }
    
    def play(self, kind):
        if not self.enabled or not winsound:
            return
        pack = self.pack
        entry = self._PACKS.get(pack, {}).get(kind)
        if not entry:
            return
        mode, data = entry

        def _do():
            try:
                with self._lock:
                    if mode == "wav":
                        path = _find_windows_sound(data)
                        if path:
                            self._play_wav(path)
                            return
                        # 找不到首选音效时，按顺序尝试备选
                        # 这些都是 Windows 各版本普遍存在的音效
                        fallbacks = [
                            "Windows Ding.wav",
                            "Windows Notify System Generic.wav",
                            "ding.wav",
                            "notify.wav",
                        ]
                        for fb in fallbacks:
                            fb_path = _find_windows_sound(fb)
                            if fb_path:
                                self._play_wav(fb_path)
                                return
                        # 全部找不到 → 静默（不再用 Beep 蜂鸣器兜底）
                    else:
                        # 兼容旧数据：万一 game.json 里还留着老的 beep 定义
                        # 也统一改成播放系统音效，避免蜂鸣器声音
                        fallbacks = [
                            "Windows Ding.wav",
                            "Windows Notify System Generic.wav",
                        ]
                        for fb in fallbacks:
                            fb_path = _find_windows_sound(fb)
                            if fb_path:
                                self._play_wav(fb_path)
                                return
            except Exception:
                pass

        threading.Thread(target=_do, daemon=True).start()

# ============================================================
# 组件
# ============================================================
def make_card(parent, padx=20, pady=16, accent=None):
    outer = tk.Frame(parent, bg=C("SURFACE"),
                     highlightbackground=C("BORDER"),
                     highlightthickness=1, bd=0)
    reg(outer, bg="SURFACE", highlightbackground="BORDER")
    inner = tk.Frame(outer, bg=C("SURFACE"))
    reg(inner, bg="SURFACE")
    inner.pack(fill="both", expand=True, padx=padx, pady=pady)
    return outer, inner
    
def make_scrollbar(parent, orient="vertical", command=None):
    """原生滚动条，无 grip 纹理，扁平配色。"""
    sb = tk.Scrollbar(parent,
                      orient=orient,
                      command=command,
                      bg=C("SURFACE_3"),
                      troughcolor=C("SURFACE_2"),
                      activebackground=C("ACCENT"),
                      highlightthickness=0,
                      bd=0,
                      elementborderwidth=0,
                      width=10 if orient == "vertical" else 14,
                      relief="flat")
    reg(sb, bg="SURFACE_3", troughcolor="SURFACE_2",
        activebackground="ACCENT")
    return sb

class Toggle(tk.Canvas):
    def __init__(self, parent, variable, bg_role="SURFACE", command=None):
        super().__init__(parent, width=40, height=22,
                         bd=0, highlightthickness=0, cursor="hand2")
        self.var = variable; self.bg_role = bg_role; self.command = command
        reg(self, bg=bg_role)
        self.bind("<Button-1>", self._on_click)
        self.var.trace_add("write", lambda *a: self._redraw())
        on_theme_change(self._redraw); self._redraw()
    def _on_click(self, e):
        self.var.set(not self.var.get())
        if self.command: self.command()
    def _redraw(self):
        try: self.configure(bg=C(self.bg_role))
        except tk.TclError: return
        self.delete("all"); w, h = 40, 22
        if self.var.get():
            self._rr(1,1,w-1,h-1,11, fill=C("ACCENT"))
            self.create_oval(w-h+2,3,w-2,h-2, fill="#ffffff", outline="")
        else:
            self._rr(1,1,w-1,h-1,11, fill=C("SURFACE_3"))
            self.create_oval(3,3,h-2,h-2, fill="#ffffff", outline="")
    def _rr(self, x1, y1, x2, y2, r, **kw):
        pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
               x2,y2-r, x2,y2, x2-r,y2, x1+r,y2,
               x1,y2, x1,y2-r, x1,y1+r, x1,y1]
        return self.create_polygon(pts, smooth=True, **kw)

class Pill(tk.Label):
    def __init__(self, parent, text, command=None):
        super().__init__(parent, text=text, font=(FONT, 10, "bold"),
                         bg=C("SURFACE_2"), fg=C("MUTED"),
                         padx=18, pady=8, cursor="hand2",
                         bd=0, highlightthickness=0)
        reg(self, bg="SURFACE_2", fg="MUTED")
        self.command = command; self.active = False
        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
    def set_active(self, active):
        self.active = active
        try:
            if active: self.config(bg=C("ACCENT"), fg=C("PRIMARY_FG"))
            else: self.config(bg=C("SURFACE_2"), fg=C("MUTED"))
        except tk.TclError: pass
    def _click(self, _):
        if self.command: self.command()
    def _enter(self, _):
        if not self.active:
            try: self.config(bg=C("SURFACE_3"), fg=C("TEXT_2"))
            except tk.TclError: pass
    def _leave(self, _):
        if not self.active:
            try: self.config(bg=C("SURFACE_2"), fg=C("MUTED"))
            except tk.TclError: pass

# ============================================================
# 伤害数字
# ============================================================
class DamagePopup:
    def __init__(self, canvas, x, y, text, color, life=40):
        self.canvas = canvas
        self.x = x; self.y = y
        self.vy = -2.2
        self.life = life
        self.life_max = life
        self.base_color = color
        self.bg_color = C("BG")
        self.item = canvas.create_text(
            x, y, text=text, fill=color,
            font=(MONO, 11, "bold"), anchor="w")
        self._tick()

    def _tick(self):
        if self.life <= 0:
            try: self.canvas.delete(self.item)
            except Exception: pass
            return
        self.y += self.vy
        self.life -= 1
        t = 1 - self.life / self.life_max
        col = lerp_color(self.base_color, self.bg_color, t)
        try:
            self.canvas.coords(self.item, self.x, self.y)
            self.canvas.itemconfig(self.item, fill=col)
        except Exception:
            return
        self.canvas.after(30, self._tick)

# ============================================================
# 主应用
# ============================================================
class RecycleApp:
    def __init__(self, root):
        self.root = root
        root.title("回收站统计")
        root.geometry("1140x950")
        root.minsize(1000, 720)

        self.settings = load_settings()
        self.game = load_game()
        # 老版本升级：旧版曾错误地把当前回收站大小当作"已清空"写入，
        # 这里做一次性修正——如果 retro_v2_done 标记不存在，就重置为 0
        if not self.game.get("retro_v2_done", False):
            self.game["total_cleared_bytes"] = 0
            self.game["total_cleared_files"] = 0
            self.game["retro_v2_done"] = True
            save_game(self.game)
        # 兜底：确保字段存在
        self.game.setdefault("total_cleared_bytes", 0)
        self.game.setdefault("total_cleared_files", 0)
        self.sfx = Sfx()
        self.sfx.enabled = bool(self.settings.get("sfx_enabled", True))
        self.sfx.pack = self.game.get("active_sfx", "default")
        self.auto_var = tk.BooleanVar(value=True)
        self.auto_after_id = None
        self.history = load_history()
        self.sort_key = tk.StringVar(value="按时间倒序")
        self.filter_var = tk.StringVar()
        self.heading_sort = {"column": None, "dir": None}

        # 布局容器（保留 _block_widgets 用于布局）
        self._block_widgets = {}

        self.layout = copy.deepcopy(DEFAULT_LAYOUT)
        saved = self.settings.get("overview_layout")
        if isinstance(saved, dict):
            for k, v in saved.items():
                if k in self.layout and isinstance(v, dict):
                    self.layout[k] = dict(v)

        self._spinner_angle = 0
        self._spinner_id = None

        # 连击
        self._combo = 0
        self._combo_last_time = 0
        self._combo_reset_id = None

        # 伤害数字统计（避免频繁刷）
        self._damage_cooldown = 0

        # 托盘
        self.tray_icon = None

        # 成就 Toast 队列
        self._toast_queue = []
        self._toast_busy = False

        root.configure(bg=C("BG"))
        self._build_header()
        self._build_tabs()
        self._build_content()
        self._build_status()
                # 伤害数字画布：放在重新扫描按钮下方
        self.damage_canvas = tk.Canvas(self.root, bg=C("BG"), bd=0,
                                         highlightthickness=0,
                                         width=320, height=56)
        reg(self.damage_canvas, bg="BG")
        self.damage_canvas.place(relx=1.0, rely=0.0, anchor="ne",
                                   x=-28, y=100)

        apply_theme(self.settings.get("theme", "dark"), root)

        # 修复：启动时把概览页提到最前
        self.page_ov.tkraise()

        # 关闭到托盘
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 启动托盘
        if HAS_TRAY and self.settings.get("tray_enabled", True):
            self._setup_tray()

        if self.settings.get("startup_scan", True):
            root.after(150, self.refresh)

    # ---------- 托盘 ----------
    def _make_tray_image(self):
        try:
            img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            # 垃圾桶盖
            d.rectangle([12, 12, 52, 20], fill=(124, 147, 255, 255))
            # 提手
            d.rectangle([26, 6, 38, 12], fill=(124, 147, 255, 255))
            # 桶身
            d.polygon([(16, 20), (48, 20), (44, 58), (20, 58)],
                       fill=(124, 147, 255, 255))
            # 三条竖线
            for x in (24, 31, 38):
                d.rectangle([x, 26, x+2, 52], fill=(10, 11, 14, 255))
            return img
        except Exception:
            return None

    def _setup_tray(self):
        if not HAS_TRAY: return
        img = self._make_tray_image()
        if img is None: return

        def on_show(icon, item):
            self.root.after(0, self._show_window)
        def on_scan(icon, item):
            self.root.after(0, self.refresh)
        def on_quit(icon, item):
            self.root.after(0, self._really_quit)

        menu = pystray.Menu(
            pystray.MenuItem("显示主界面", on_show, default=True),
            pystray.MenuItem("立即扫描", on_scan),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", on_quit),
        )
        try:
            self.tray_icon = pystray.Icon("recycle_stat", img, "回收站统计", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception:
            self.tray_icon = None

    def _on_close(self):
        # 托盘不可用 → 只能直接关闭
        if not HAS_TRAY or not self.settings.get("tray_enabled", True):
            self._really_quit()
            return
        if self.tray_icon is None:
            self._really_quit()
            return
        self._show_close_dialog()

    def _show_window(self):
        try:
            self.root.deiconify()
            self.root.state("normal")     # 保持顺序，deiconify 之后设置更稳
            try:
                self.root.attributes("-topmost", True)
                self.root.after(200, lambda: self.root.attributes("-topmost", False))
            except Exception:
                pass
            self.root.lift()
            self.root.focus_force()
            self.root.after(50, self._apply_layout)
            self.root.after(150, self._apply_layout)
            self.root.after(300, self._apply_layout)
            self.root.after(100, self._repaint_after_restore)
        except Exception:
            pass

    def _repaint_after_restore(self):
        try:
            # 先让 _content 内的页面重新应用布局
            self._apply_layout()
        except Exception:
            pass
        try:
            self._draw_chart()
        except Exception:
            pass
        try:
            if hasattr(self, "_last_hist"):
                self._refresh_ext_chart(self._last_hist)
        except Exception:
            pass
        try:
            self._reload_table()
        except Exception:
            pass
        # 关键：把所有卡片按当前页面尺寸重新 place 一遍
        try:
            p = self.page_ov
            pw = p.winfo_width()
            ph = p.winfo_height()
            if pw > 50 and ph > 50:
                for name, w in self._block_widgets.items():
                    info = self.layout.get(name)
                    if not info:
                        continue
                    try:
                        w.place(in_=p,
                                relx=info["relx"], rely=info["rely"],
                                relwidth=info["relwidth"],
                                relheight=info["relheight"])
                    except tk.TclError:
                        pass
            self.root.update_idletasks()
        except Exception:
            pass

    def _show_close_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.withdraw()
        dlg.title("关闭")
        dlg.configure(bg=C("BG"))
        dlg.resizable(False, False)

        card = tk.Frame(dlg, bg=C("SURFACE"),
                        highlightbackground=C("BORDER"),
                        highlightthickness=1)
        reg(card, bg="SURFACE", highlightbackground="BORDER")
        card.pack(fill="both", expand=True, padx=14, pady=14)

        reg(tk.Label(card, text="要关闭程序吗？", font=(FONT, 14, "bold")),
            bg="SURFACE", fg="TEXT").pack(padx=32, pady=(24, 4))
        reg(tk.Label(card,
                      text="最小化到后台会继续监测回收站，\n"
                           "右键任务栏托盘图标可以恢复或退出",
                      font=(FONT, 10), justify="center"),
            bg="SURFACE", fg="MUTED").pack(padx=32, pady=(0, 18))

        btns = tk.Frame(card, bg=C("SURFACE")); reg(btns, bg="SURFACE")
        btns.pack(padx=32, pady=(0, 24))

        def _do_min():
            # 没有托盘时只能最小化到任务栏，否则窗口会彻底"消失"找不回来
            if not HAS_TRAY or self.tray_icon is None:
                try:
                    self.root.iconify()
                    self.status.config(text="已最小化（托盘不可用）")
                except Exception:
                    pass
                return
            try:
                self._saved_geometry = self.root.winfo_geometry()
            except Exception:
                self._saved_geometry = None
            try:
                self.root.withdraw()
                self.status.config(text="已隐藏到托盘，右键托盘图标可恢复或退出")
            except Exception:
                pass

        def _do_close():
            self._really_quit()

        def _cancel():
            try:
                dlg.destroy()
            except Exception:
                pass

        min_btn = tk.Label(btns, text="最小化到后台", font=(FONT, 11, "bold"),
                           bg=C("ACCENT"), fg=C("PRIMARY_FG"),
                           padx=20, pady=10, cursor="hand2")
        reg(min_btn, bg="ACCENT", fg="PRIMARY_FG")
        min_btn.pack(side="left", padx=(0, 10))

        def _on_min(event=None):
            dlg.destroy()
            _do_min()

        def _on_close(event=None):
            dlg.destroy()
            _do_close()

        min_btn.bind("<Button-1>", _on_min)

        close_btn = tk.Label(btns, text="直接关闭", font=(FONT, 11),
                             bg=C("SURFACE_2"), fg=C("TEXT_2"),
                             padx=20, pady=10, cursor="hand2")
        reg(close_btn, bg="SURFACE_2", fg="TEXT_2")
        close_btn.pack(side="left")
        close_btn.bind("<Button-1>", _on_close)

        # 标题栏 X 或 Esc = 取消
        dlg.protocol("WM_DELETE_WINDOW", _cancel)
        dlg.bind("<Escape>", lambda e: _cancel())

        # 算好尺寸和位置后再显示
        dlg.update_idletasks()
        W = max(400, dlg.winfo_reqwidth())
        H = max(220, dlg.winfo_reqheight())

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()

        cx = cy = None
        try:
            self.root.update_idletasks()
            rw = self.root.winfo_width()
            rh = self.root.winfo_height()
            rx = self.root.winfo_rootx()
            ry = self.root.winfo_rooty()
            if rw > 200 and rh > 200 and 0 <= rx < sw and 0 <= ry < sh:
                cx = rx + (rw - W) // 2
                cy = ry + (rh - H) // 2
        except Exception:
            pass
        if cx is None or cy is None:
            cx = (sw - W) // 2
            cy = (sh - H) // 2
        cx = max(0, min(cx, sw - W))
        cy = max(0, min(cy, sh - H))
        dlg.geometry(f"{W}x{H}+{cx}+{cy}")
        dlg.deiconify()
        dlg.lift()
        try:
            dlg.attributes("-topmost", True)
            dlg.after(300, lambda: dlg.attributes("-topmost", False))
        except Exception:
            pass
        try:
            dlg.grab_set()
            dlg.focus_force()
        except Exception:
            pass


    def _really_quit(self):
        try:
            if self.tray_icon is not None:
                self.tray_icon.stop()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

    # ---------- Header ----------
    def _build_header(self):
        h = tk.Frame(self.root, bg=C("BG"), height=72); reg(h, bg="BG")
        h.pack(fill="x", padx=32, pady=(24, 0)); h.pack_propagate(False)

        left = tk.Frame(h, bg=C("BG")); reg(left, bg="BG")
        left.pack(side="left", fill="y")
        reg(tk.Label(left, text="🗑", font=(FONT, 24)),
            bg="BG", fg="ACCENT").pack(side="left", pady=(0,4))

        tb = tk.Frame(left, bg=C("BG")); reg(tb, bg="BG")
        tb.pack(side="left", padx=(14,0), pady=(8,0))

        title_row = tk.Frame(tb, bg=C("BG")); reg(title_row, bg="BG")
        title_row.pack(anchor="w")
        reg(tk.Label(title_row, text="回收站统计", font=(FONT, 15, "bold")),
            bg="BG", fg="TEXT").pack(side="left")

        # 等级徽章
        self.level_badge = tk.Label(title_row, text="Lv.1",
            font=(MONO, 11, "bold"),
            bg=C("ACCENT"), fg=C("PRIMARY_FG"),
            padx=8, pady=1)
        reg(self.level_badge, bg="ACCENT", fg="PRIMARY_FG")
        self.level_badge.pack(side="left", padx=(8, 0))
        # 称号徽章
        self.title_badge = tk.Label(title_row, text="",
                                     font=(FONT, 10, "bold"),
                                     bg=C("SURFACE_3"), fg=C("PURPLE"),
                                     padx=8, pady=1)
        reg(self.title_badge, bg="SURFACE_3", fg="PURPLE")
        self.title_badge.pack(side="left", padx=(6, 0))
        self._refresh_title_badge()
        # 成就点数
        self.points_badge = tk.Label(title_row, text="⭐ 0", font=(MONO, 11, "bold"),
                                     bg=C("SURFACE_3"), fg=C("YELLOW"),
                                     padx=8, pady=1)
        reg(self.points_badge, bg="SURFACE_3", fg="YELLOW")
        self.points_badge.pack(side="left", padx=(8, 0))
        on_theme_change(self._refresh_points_badge)
        self._refresh_points_badge()

        reg(tk.Label(tb, text="Recycle Bin Statistics", font=(FONT, 9)),
            bg="BG", fg="DIM").pack(anchor="w")

        right = tk.Frame(h, bg=C("BG")); reg(right, bg="BG")
        right.pack(side="right", fill="y", pady=(14, 0))

        self.refresh_btn = self._primary_btn(right, "重新扫描", self.refresh)
        self.refresh_btn.pack(side="right")

        self._build_nuke_button(right)

        self.theme_quick = tk.Label(right, text="",
            font=(FONT, 14), bg=C("SURFACE_2"), fg=C("TEXT"),
            padx=10, pady=5, cursor="hand2")
        reg(self.theme_quick, bg="SURFACE_2", fg="TEXT")
        self.theme_quick.pack(side="right", padx=(0, 8))
        self.theme_quick.bind("<Button-1>", lambda e: self._toggle_theme())
        self.theme_quick.bind("<Enter>", lambda e: self._hover_bg(
            self.theme_quick, "SURFACE_2", "SURFACE_3"))
        self.theme_quick.bind("<Leave>", lambda e: self._hover_bg(
            self.theme_quick, "SURFACE_3", "SURFACE_2"))
        on_theme_change(self._refresh_theme_quick)
        self._refresh_theme_quick()

    def _refresh_theme_quick(self):
        try:
            cur = self.settings.get("theme", "dark")
            self.theme_quick.config(text="☀" if cur == "dark" else "☾")
        except tk.TclError: pass

    def _refresh_level_badge(self):
        try:
            lvl, gb = calc_level(self.history.get("total_bytes", 0))
            self.level_badge.config(text=f"Lv.{lvl}")
        except Exception: pass

    def _refresh_points_badge(self):
        try:
            pts = self.game.get("points", 0)
            self.points_badge.config(text=f"⭐ {pts}")
        except Exception: pass
    def _refresh_title_badge(self):
        try:
            tid = self.game.get("active_title", "")
            if not tid:
                self.title_badge.config(
                    text="", bg=C("SURFACE_3"), fg=C("PURPLE"))
                return
            for t in SHOP_TITLES:
                if t["id"] == tid:
                    # 用固定颜色值，不走主题系统
                    self.title_badge.config(
                        text=f"{t['icon']} {t['name']}",
                        bg=t.get("bg", C("SURFACE_3")),
                        fg=t.get("fg", "#ffffff"),
                    )
                    return
            self.title_badge.config(text="")
        except Exception:
            pass

    def _hover_bg(self, widget, from_role, to_role):
        if not self.settings.get("motion_enabled", True):
            try: widget.config(bg=C(to_role))
            except tk.TclError: pass
            return
        try: c1 = C(from_role); c2 = C(to_role)
        except KeyError: return
        steps = 8
        for i in range(steps + 1):
            col = lerp_color(c1, c2, i / steps)
            self.root.after(int(18 * i), lambda c=col, w=widget: self._safe_bg(w, c))

    def _safe_bg(self, w, color):
        try: w.config(bg=color)
        except tk.TclError: pass

    def _toggle_theme(self):
        new = "light" if self.settings.get("theme") == "dark" else "dark"
        self.settings["theme"] = new
        self.game["active_theme"] = new
        save_settings(self.settings)
        save_game(self.game)
        apply_theme(new, self.root)
        if hasattr(self, "theme_var"):
            self.theme_var.set(new)
        self._refresh_theme_btns()
    # ---------- 核弹式清空回收站按钮 ----------
    def _build_nuke_button(self, parent):
        try:
            self.root.update_idletasks()
        except Exception:
            pass
        try:
            rw = self.refresh_btn.winfo_width()
            if rw <= 1:
                rw = self.refresh_btn.winfo_reqwidth()
            rh = self.refresh_btn.winfo_height()
            if rh <= 1:
                rh = self.refresh_btn.winfo_reqheight()
        except Exception:
            rw, rh = 120, 38
        rw = max(rw, 100)
        rh = max(rh, 36)

        wrap = tk.Frame(parent, bg=C("BG"), width=rw, height=rh)
        reg(wrap, bg="BG")
        wrap.pack(side="right", padx=(0, 8))
        wrap.pack_propagate(False)
        wrap.grid_propagate(False)
        wrap.grid_rowconfigure(0, weight=1)
        wrap.grid_columnconfigure(0, weight=1)
        self._nuke_wrap = wrap

        # 底层按钮
        self.nuke_btn = tk.Label(
            wrap, text="💥 清空",
            font=(FONT, 10, "bold"),
            bg="#3a1212", fg="#ff9c9c",
            cursor="hand2", bd=0, highlightthickness=0)
        self.nuke_btn.grid(row=0, column=0, sticky="nsew")

        # 红色盖子
        self.nuke_cover = tk.Frame(wrap, bg="#c0392b", cursor="hand2")
        self.nuke_cover.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.nuke_cover_label = tk.Label(
            self.nuke_cover, text="⚠ 清空",
            font=(FONT, 10, "bold"),
            bg="#c0392b", fg="#ffffff", cursor="hand2")
        self.nuke_cover_label.place(relx=0.5, rely=0.5, anchor="center")

        # 状态
        self._nuke_armed = False
        self._nuke_timer_id = None
        self._nuke_leave_id = None

        # 事件绑定
        self.nuke_cover.bind("<Button-1>", self._nuke_arm)
        self.nuke_cover_label.bind("<Button-1>", self._nuke_arm)
        self.nuke_btn.bind("<Button-1>", self._nuke_fire)
        self.nuke_btn.bind("<Leave>", self._nuke_maybe_disarm)

    def _hide_cover(self):
        try:
            if self.nuke_cover.winfo_exists():
                self.nuke_cover.place_forget()
        except Exception:
            pass

    def _show_cover(self):
        try:
            if self.nuke_cover.winfo_exists():
                self.nuke_cover.place(relx=0, rely=0, relwidth=1, relheight=1)
        except Exception:
            pass

    def _animate_slide(self, from_y, to_y, steps=5, on_done=None):
        def step(i):
            if i > steps:
                if on_done:
                    try: on_done()
                    except Exception: pass
                return
            t = i / steps
            y = from_y + (to_y - from_y) * t
            try:
                self.nuke_cover.place_configure(rely=y)
            except Exception:
                if on_done:
                    try: on_done()
                    except Exception: pass
                return
            self.root.after(15, lambda: step(i + 1))
        step(0)

    def _nuke_arm(self, event=None):
        if self._nuke_armed: return
        self._nuke_armed = True
        try:
            self.nuke_cover.place(relx=0, rely=0, relwidth=1, relheight=1)
        except Exception:
            pass
        self._animate_slide(0.0, -1.0, on_done=self._hide_cover)
        if self._nuke_timer_id:
            try: self.root.after_cancel(self._nuke_timer_id)
            except Exception: pass
        self._nuke_timer_id = self.root.after(3000, self._nuke_disarm)
        try:
            self.status.config(text="⚠ 核弹已解锁：再次点击将清空回收站（鼠标移开可取消）")
        except Exception:
            pass

    def _nuke_disarm(self):
        if not self._nuke_armed:
            return
        self._nuke_armed = False
        if self._nuke_timer_id:
            try: self.root.after_cancel(self._nuke_timer_id)
            except Exception: pass
            self._nuke_timer_id = None
        if self._nuke_leave_id:
            try: self.root.after_cancel(self._nuke_leave_id)
            except Exception: pass
            self._nuke_leave_id = None
        try:
            self.nuke_cover.place(relx=0, rely=-1.0, relwidth=1, relheight=1)
        except Exception:
            pass
        self._animate_slide(-1.0, 0.0)
        try:
            self.status.config(text="已取消清空")
        except Exception:
            pass

    def _nuke_fire(self, event=None):
        if not self._nuke_armed:
            return
        self._nuke_disarm()
        self.root.after(180, self._do_empty_recycle_bin)

    def _nuke_maybe_disarm(self, event=None):
        if not self._nuke_armed:
            return
        if self._nuke_leave_id:
            try: self.root.after_cancel(self._nuke_leave_id)
            except Exception: pass
        self._nuke_leave_id = self.root.after(300, self._nuke_check_disarm)

    def _nuke_check_disarm(self):
        self._nuke_leave_id = None
        if not self._nuke_armed:
            return
        try:
            x, y = self.root.winfo_pointerxy()
            bx = self.nuke_btn.winfo_rootx()
            by = self.nuke_btn.winfo_rooty()
            bw = self.nuke_btn.winfo_width()
            bh = self.nuke_btn.winfo_height()
            if bx <= x <= bx + bw and by <= y <= by + bh:
                return
        except Exception:
            pass
        self._nuke_disarm()

    def _measure_disk_recycle_size(self):
        total, cnt = 0, 0
        for drive in get_drives():
            rb = os.path.join(drive, '$Recycle.Bin')
            if not os.path.isdir(rb): continue
            try: sids = os.listdir(rb)
            except OSError: continue
            for sid in sids:
                sid_path = os.path.join(rb, sid)
                if not os.path.isdir(sid_path): continue
                try: entries = os.listdir(sid_path)
                except OSError: continue
                for name in entries:
                    if not name.startswith('$R'): continue
                    full = os.path.join(sid_path, name)
                    size, c = measure(full)
                    total += size
                    cnt += c
        return total, cnt

    def _do_empty_recycle_bin(self):
        try:
            self.status.config(text="📏 正在测量垃圾体积…")
            self.root.update_idletasks()
        except Exception:
            pass

        before_bytes, before_files = self._measure_disk_recycle_size()

        if before_bytes <= 0:
            try:
                self.status.config(text="回收站已经是空的")
                messagebox.showinfo("无事发生",
                    "回收站本来就是空的，\n你已经很干净了，别再按了 😴")
            except Exception:
                pass
            return

        try:
            ok = messagebox.askyesno(
                "确认清空回收站",
                f"确定要清空所有分区的回收站吗？\n\n"
                f"待清理：{human_size(before_bytes)} · {before_files} 文件\n"
                f"清空后无法恢复",
                icon="warning", default="no",
            )
        except Exception:
            ok = True
        if not ok:
            try: self.status.config(text="已取消清空")
            except Exception: pass
            return

        try:
            self.status.config(text="⏳ 正在清空回收站…")
            self.root.update_idletasks()
        except Exception:
            pass
        # 记录即将清空的所有 key，用于下次扫描时区分"清空"和"还原"
        try:
            _h = load_history()
            self.game["pending_cleared_keys"] = list(_h["seen"].keys())
            save_game(self.game)
        except Exception:
            pass

        try:
            flags = 0x00000001 | 0x00000002 | 0x00000004
            result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
            if result == 0:
                gb = before_bytes / (1024 ** 3)
                pts = max(1, int(gb * 10))
                self.game["points"] = self.game.get("points", 0) + pts
                save_game(self.game)

                self._refresh_points_badge()
                self.status.config(text="✅ 回收站已清空")
                if self.settings.get("motion_enabled", True):
                    self.root.after(80, self._play_clear_animation)
                    self.root.after(400, self.refresh)
                    self.root.after(1400, lambda: self._show_clear_report(
                        before_bytes, before_files, pts))
                else:
                    self.root.after(400, self.refresh)
                    self.root.after(600, lambda: self._show_clear_report(
                        before_bytes, before_files, pts))
            else:
                self.status.config(text=f"清空结束（代码 {result}）")
                self.root.after(400, self.refresh)
        except Exception as e:
            try: self.status.config(text=f"清空失败：{e}")
            except Exception: pass
            messagebox.showerror("清空回收站失败", str(e))

    def _primary_btn(self, parent, text, cmd):
        b = tk.Label(parent, text=text, font=(FONT, 10, "bold"),
                     bg=C("ACCENT"), fg=C("PRIMARY_FG"),
                     padx=20, pady=9, cursor="hand2", bd=0, highlightthickness=0)
        reg(b, bg="ACCENT", fg="PRIMARY_FG")
        b.bind("<Button-1>", lambda e: cmd())
        b.bind("<Enter>", lambda e: self._hover_bg(b, "ACCENT", "ACCENT_2"))
        b.bind("<Leave>", lambda e: self._hover_bg(b, "ACCENT_2", "ACCENT"))
        return b

    def _make_emoji_badge(self, emoji_char, size=140):
        try:
            from PIL import Image, ImageDraw, ImageFont, ImageTk
        except ImportError:
            return None
        try:
            accent = C("ACCENT")
            h = accent.lstrip("#")
            r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            cx = cy = size // 2

            # 外发光圈
            for i in range(size // 2, size // 2 - 14, -1):
                alpha = int(70 * (1 - (size // 2 - i) / 14))
                if alpha <= 0: continue
                draw.ellipse([cx - i, cy - i, cx + i, cy + i],
                             fill=(r, g, b, alpha))

            # 纯色圆底
            radius = size // 2 - 12
            draw.ellipse(
                [cx - radius, cy - radius, cx + radius, cy + radius],
                fill=(r, g, b, 255))

            # 中心彩色 emoji
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/seguiemj.ttf",
                                           int(size * 0.55))
                draw.text((cx, cy), emoji_char, font=font,
                          embedded_color=True, anchor="mm")
            except Exception:
                try:
                    font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf",
                                                int(size * 0.55))
                    draw.text((cx, cy), emoji_char, font=font,
                              fill=(255, 255, 255, 255), anchor="mm")
                except Exception:
                    return None
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def _pick_clear_quip(self, cleared_bytes):
        mb = cleared_bytes / (1024 * 1024)
        gb = cleared_bytes / (1024 ** 3)
        size = human_size(cleared_bytes)
        photos = max(1, int(mb / 3))
        minutes = max(1, int(gb * 60))
        songs = max(1, int(mb / 5))
        bins = max(1, int(mb / 100))
        fmt = {"size": size, "photos": photos, "minutes": minutes,
               "songs": songs, "bins": bins}

        # 段位文案（按清空量分级）
        if cleared_bytes >= 1024 ** 4:
            tier = "🌌 清空 {size} 这不是清理，这是宇宙大爆炸的反向操作"
        elif gb >= 100:
            tier = "🐋 清空 {size} 恭喜，你放生了一头蓝鲸"
        elif gb >= 10:
            tier = "🐘 清空 {size} 大象从你的硬盘上走开了"
        elif gb >= 1:
            tier = "🐻 清空 {size} 熊从你的硬盘里捞走了一整条鱼"
        elif mb >= 100:
            tier = "🐹 清空 {size} 仓鼠终于吐出了一点腮帮子里的东西"
        else:
            tier = "🐜 清空 {size} 蚂蚁搬家，聊胜于无"

        # 幽默文案池
        pool = [
            "🎉 你为地球清理了 {size} 数字垃圾，相当于 {photos} 张高清照片",
            "📸 又删掉了 {size}，够你拍 {photos} 张自拍，并永远不看第二眼",
            "🎬 你清空的 {size}，够你录 {minutes} 分钟「不知道拍什么」的素材",
            "☁️ {size} 从你的硬盘消失了，云盘服务商松了一口气",
            "🗑️ 你扔掉了 {size} 的数字垃圾，相当于把 {bins} 个垃圾桶的「万一有用」倒进了赛博焚化炉",
            "🧹 清理了 {size}，你的电脑终于能呼吸了，它刚才差点窒息",
            "🏠 {size} 被清空，相当于给你的硬盘做了一次「数字大扫除」，灰尘都能炒一盘菜了",
            "🍜 你删掉的 {size}，如果打印出来，能绕地球半圈——好吧，气势到位了",
            "💾 你删了 {size}，这些文件你存的时候觉得「以后肯定用得上」，结果一次都没打开过",
            "🐹 {size} 没了，你的「数字仓鼠症」得到了片刻缓解，但明天还会继续囤",
            "📁 {size} 被清理，其中一些文件叫「新建文件夹」「未命名文档」「最终版_v3_真的最终版」",
            "🎊 恭喜！你成功把 {size} 的「电子垃圾」变成了「电子不存在」",
            "🏆 成就解锁：【数字清道夫】— 一次性清理 {size} 数字垃圾",
            "🥇 {size} 清空完毕，你的电脑刚才给你发了一条内部消息：「谢谢，但我还是卡」",
            "🌟 恭喜你战胜了「万一以后用得上」的幻觉，{size} 归零",
            "🚀 清理 {size} 完成，硬盘空间 +{size}，人生烦恼 -0",
            "💻 {size} 已清空，程序员说：「能跑就别动」你说：「我偏要删」",
            "🐛 你删掉了 {size}，其中一些可能是你三年前写的 bug，现在它们终于安息了",
            "📦 回收站已清空，你的电脑现在有 {size} 的空间来装新的、同样永远不打开的文件",
            "🔥 {size} 被焚毁，数字焚化炉温度正常，排放的只有你的一点点愧疚",
            "🎉 你清理了 {size}，你的数字生活整洁了一点点，但你的桌面图标还是乱的",
            "📉 删了 {size}，你的硬盘空了一点，你的心还是满的",
            "🗑️ {size} 清空了，但这些文件如果在回收站里再待一会儿，说不定你就真的会去看了呢？——不会的",
            "⏰ {size} 没了，你省下了无数次「等一下我再整理」的机会",
            "😶 {size} 被删除，你终于做了那个决定，但「待处理」文件夹还在等着你",
        ]

        # 30% 概率用段位文案，70% 用幽默池
        if random.random() < 0.3:
            return tier.format(**fmt)
        return random.choice(pool).format(**fmt)

    def _show_clear_report(self, cleared_bytes, cleared_files, points):
        try:
            emoji = random.choice(["🎉", "💚", "🧹", "🚀", "⚡", "🍃", "🔥", "🌟", "🗑️", "🕶️"])
            quip_text = self._pick_clear_quip(cleared_bytes)

            top = tk.Toplevel(self.root)
            top.withdraw()
            top.title("清空成功")
            top.configure(bg=C("BG"))
            top.resizable(False, False)

            card = tk.Frame(top, bg=C("SURFACE"),
                            highlightbackground=C("ACCENT"),
                            highlightthickness=2)
            reg(card, bg="SURFACE", highlightbackground="ACCENT")
            card.pack(fill="both", expand=True, padx=14, pady=14)

            emoji_canvas = tk.Canvas(card, width=150, height=150,
                                      bg=C("SURFACE"), bd=0,
                                      highlightthickness=0)
            reg(emoji_canvas, bg="SURFACE")
            emoji_canvas.pack(pady=(20, 8))
            badge = self._make_emoji_badge(emoji, size=140)
            if badge is not None:
                top._emoji_photo = badge
                emoji_canvas.create_image(75, 75, image=badge)
            else:
                emoji_canvas.create_oval(10, 10, 140, 140,
                                          fill=C("ACCENT"), outline="")
                emoji_canvas.create_text(75, 75, text=emoji,
                                          font=("Segoe UI Emoji", 56),
                                          fill="#ffffff")


            reg(tk.Label(card, text=" 回收站已清空！",
                          font=(FONT, 18, "bold")),
                bg="SURFACE", fg="TEXT").pack()
            reg(tk.Label(card, text=quip_text, font=(FONT, 12, "bold"),
                          wraplength=520, justify="center"),
                bg="SURFACE", fg="TEXT").pack(pady=(8, 16))

            data = tk.Frame(card, bg=C("SURFACE_2"))
            reg(data, bg="SURFACE_2")
            data.pack(fill="x", padx=24, pady=(0, 12))

            def _datarow(label, value, color_role):
                row = tk.Frame(data, bg=C("SURFACE_2"))
                reg(row, bg="SURFACE_2")
                row.pack(fill="x", padx=16, pady=4)
                reg(tk.Label(row, text=label, font=(FONT, 10)),
                    bg="SURFACE_2", fg="MUTED").pack(side="left")
                reg(tk.Label(row, text=value, font=(MONO, 11, "bold")),
                    bg="SURFACE_2", fg=color_role).pack(side="right")

            _datarow("本次清空",
                     f"{human_size(cleared_bytes)} · {cleared_files} 文件",
                     "GREEN")
            _datarow("累计清空",
                     human_size(self.game.get("total_cleared_bytes", 0)),
                     "ACCENT")
            _datarow("获得成就点", f"+{points} ⭐", "YELLOW")

            btn = tk.Label(card, text="我知道啦！", font=(FONT, 11, "bold"),
                           bg=C("ACCENT"), fg=C("PRIMARY_FG"),
                           padx=32, pady=10, cursor="hand2")
            reg(btn, bg="ACCENT", fg="PRIMARY_FG")
            btn.pack(pady=(0, 20))
            btn.bind("<Button-1>", lambda e: top.destroy())

            # 所有内容 pack 完后，再计算尺寸
            top.update_idletasks()
            W = max(520, top.winfo_reqwidth())
            H = max(500, top.winfo_reqheight())

            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()

            cx = cy = None
            try:
                self.root.update_idletasks()
                rw = self.root.winfo_width()
                rh = self.root.winfo_height()
                rx = self.root.winfo_rootx()
                ry = self.root.winfo_rooty()
                # 仅当主窗口可见且在屏内时，以它为中心
                if (rw > 200 and rh > 200
                        and 0 <= rx < sw and 0 <= ry < sh):
                    cx = rx + (rw - W) // 2
                    cy = ry + (rh - H) // 2
            except Exception:
                pass

            # 回退：屏幕正中
            if cx is None or cy is None:
                cx = (sw - W) // 2
                cy = (sh - H) // 2

            # 保证不越界
            cx = max(0, min(cx, sw - W))
            cy = max(0, min(cy, sh - H))
            top.geometry(f"{W}x{H}+{cx}+{cy}")
            top.deiconify()   # 显示（此时坐标已设置好）
            top.lift()
            top.attributes("-alpha", 1.0)

            try:
                top.attributes("-topmost", True)
                def fade(i=0):
                    if i > 20 or not top.winfo_exists():
                        return
                    try:
                        top.attributes("-alpha", i / 20)
                    except Exception:
                        return
                    top.after(15, lambda: fade(i + 1))
                fade()
                top.after(400, lambda: top.attributes("-topmost", False))
            except Exception:
                pass
        except Exception:
            pass

    def _play_sfx_demo(self, pack_id):
        """临时切到指定音效包，连播三个代表性音效，播完恢复。"""
        old_pack = self.sfx.pack
        self.sfx.pack = pack_id
        try:
            self.sfx.play("delete")
        except Exception:
            pass
        self.root.after(400, lambda: self.sfx.play("levelup"))
        self.root.after(1400, lambda: self.sfx.play("achievement"))
        # 等三段都播完再恢复
        self.root.after(2800, lambda: setattr(self.sfx, "pack", old_pack))
    def _play_clear_animation(self, anim_id=None):
        if anim_id is None:
            anim = self.game.get("active_anim", "")
        else:
            anim = anim_id
        if not anim or anim == "none":
            return

        self._safe_destroy_anim()

        try:
            self.root.update_idletasks()
            rw = self.root.winfo_width()
            rh = self.root.winfo_height()
            if rw < 200 or rh < 200:
                W, H = 900, 700
                cx0 = cy0 = None
            else:
                W, H = rw, rh
                cx0 = self.root.winfo_rootx()
                cy0 = self.root.winfo_rooty()

            TRANSPARENT = C("BG")   # 用主题背景色，不再做色键抠图
            win = tk.Toplevel(self.root)
            win.withdraw()
            win.overrideredirect(True)
            win.configure(bg=TRANSPARENT)
            try:
                win.attributes("-topmost", True)
                win.attributes("-alpha", 0.92)
            except Exception:
                pass

            cv = tk.Canvas(win, bg=TRANSPARENT, bd=0,
                            highlightthickness=0, width=W, height=H)
            cv.pack(fill="both", expand=True)
                        # 点击任意处 = 关闭特效
            # 点击任意处 = 关闭特效
            def _close_anim(event=None):
                self._safe_destroy_anim()
            win.bind("<Button-1>", _close_anim)
            cv.bind("<Button-1>", _close_anim)
            win.bind("<Escape>", _close_anim)

            if cx0 is None:
                sw = win.winfo_screenwidth()
                sh = win.winfo_screenheight()
                cx = (sw - W) // 2
                cy = (sh - H) // 2
            else:
                cx = max(0, cx0)
                cy = max(0, cy0)

            win.geometry(f"{W}x{H}+{cx}+{cy}")
            win.deiconify()
            win.lift()
            self._anim_window = win
            self._anim_transparent = TRANSPARENT

            gid = self.root.after(20000, self._safe_destroy_anim)
            win._guard_id = gid

            if anim == "tree":
                self._anim_tree(cv, W, H)
            elif anim == "fireworks":
                self._anim_fireworks(cv, W, H)
            elif anim == "pixel":
                self._anim_pixel(cv, W, H)
            elif anim == "whale":
                self._anim_whale(cv, W, H)
            elif anim == "ripple":
                self._anim_ripple(cv, W, H)
            elif anim == "lightning":
                self._anim_lightning(cv, W, H)
            elif anim == "tornado":
                self._anim_tornado(cv, W, H)
            elif anim == "blackhole":
                self._anim_blackhole(cv, W, H)
            elif anim == "rainbow":
                self._anim_rainbow(cv, W, H)
            else:
                self._safe_destroy_anim()
        except Exception:
            pass

    def _safe_destroy_anim(self):
        win = getattr(self, "_anim_window", None)
        if win is None:
            return
        try:
            gid = getattr(win, "_guard_id", None)
            if gid:
                self.root.after_cancel(gid)
        except Exception:
            pass
        try:
            win.destroy()
        except Exception:
            pass
        if getattr(self, "_anim_window", None) is win:
            self._anim_window = None

    # ---------- 动画：颜色工具 ----------
    def _hsv_to_rgb(self, h, s, v):
        """h:0-360, s:0-1, v:0-1 -> '#rrggbb'"""
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        if   h < 60:  r, g, b = c, x, 0
        elif h < 120: r, g, b = x, c, 0
        elif h < 180: r, g, b = 0, c, x
        elif h < 240: r, g, b = 0, x, c
        elif h < 300: r, g, b = x, 0, c
        else:         r, g, b = c, 0, x
        return "#{:02x}{:02x}{:02x}".format(
            int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))

    def _lerp_hex(self, c1, c2, t):
        """在两个十六进制颜色之间插值"""
        t = max(0.0, min(1.0, t))
        h1 = c1.lstrip("#"); h2 = c2.lstrip("#")
        r1, g1, b1 = (int(h1[i:i+2], 16) for i in (0, 2, 4))
        r2, g2, b2 = (int(h2[i:i+2], 16) for i in (0, 2, 4))
        return "#{:02x}{:02x}{:02x}".format(
            int(r1 + (r2 - r1) * t),
            int(g1 + (g2 - g1) * t),
            int(b1 + (b2 - b1) * t))

    def _anim_tree(self, cv, w, h):
        """分形树：随机分形 + 所有末端长叶 + 懒创建（无残留点）"""
        T = self._anim_transparent

        # ── 配色 ──
        BRANCH_COLOR_START = "#4a2e14"
        BRANCH_COLOR_END   = "#9b6a30"
        LEAF_COLORS        = ["#2e8b57", "#3cb371",
                              "#228b22", "#32cd32", "#4caf50"]

        # ── 树的参数 ──
        TRUNK_LEN   = h * 0.22
        MAX_DEPTH   = 10
        START_WIDTH = 16

        branch_meta = []
        leaf_meta   = []

        def build(x, y, angle_deg, length, width, depth, spawn_frame):
            # 太小的枝不画
            if length < 3 or width < 0.6:
                return

            bend = random.uniform(-0.12, 0.12)
            rad = math.radians(angle_deg + bend * 30)
            x2 = x + math.sin(rad) * length
            y2 = y - math.cos(rad) * length

            grow_frames = 6
            branch_meta.append({
                "x1": x, "y1": y, "x2": x2, "y2": y2,
                "width": max(1, int(round(width))),
                "depth": depth,
                "spawn": spawn_frame, "life": grow_frames,
                "color": self._lerp_hex(BRANCH_COLOR_START,
                                         BRANCH_COLOR_END,
                                         depth / max(1, MAX_DEPTH)),
                "id": None,
            })

            # ── 先算子枝的期望尺寸，用于判断是否末端 ──
            len_ratio = random.uniform(0.68, 0.82)
            w_ratio   = random.uniform(0.62, 0.75)
            next_len   = length * len_ratio
            next_width = width * w_ratio

            is_terminal = (depth >= MAX_DEPTH or
                           next_len < 5 or
                           next_width < 0.65)

            child_delay = spawn_frame + grow_frames + random.randint(0, 2)

            if is_terminal:
                # ── 末端：长 2~4 片叶子（带散布）──
                n_leaves = random.choices([2, 3, 4], weights=[30, 50, 20])[0]
                for _ in range(n_leaves):
                    # 叶子位置：沿枝末端散布
                    lx = x2 + random.uniform(-8, 8)
                    ly = y2 + random.uniform(-8, 8)
                    leaf_meta.append({
                        "x": lx, "y": ly,
                        "spawn": spawn_frame + grow_frames
                                  + random.randint(0, 4),
                        "r": random.uniform(2.5, 5.0),
                        "color": random.choice(LEAF_COLORS),
                        "id": None, "birth": None,
                    })
                return

            # ── 分叉 ──
            n_children = random.choices([1, 2, 3],
                                         weights=[15, 65, 20])[0]
            base_spread = random.uniform(22, 42)

            def grow(a, length_scale):
                build(x2, y2, a,
                      next_len * length_scale,
                      next_width,
                      depth + 1, child_delay)

            if n_children == 1:
                a = angle_deg + random.uniform(-base_spread, base_spread)
                grow(a, random.uniform(1.0, 1.15))
            elif n_children == 2:
                la = angle_deg - base_spread + random.uniform(-8, 8)
                ra = angle_deg + base_spread + random.uniform(-8, 8)
                grow(la, random.uniform(0.88, 1.05))
                grow(ra, random.uniform(0.88, 1.05))
            else:
                la = angle_deg - base_spread + random.uniform(-6, 6)
                ma = angle_deg + random.uniform(-10, 10)
                ra = angle_deg + base_spread + random.uniform(-6, 6)
                grow(la, random.uniform(0.82, 0.98))
                grow(ma, random.uniform(0.90, 1.10))
                grow(ra, random.uniform(0.82, 0.98))

        # ── 起手 ──
        root_x = w // 2 + random.randint(-40, 40)
        root_y = h - 20
        build(root_x, root_y, random.uniform(-3, 3),
              TRUNK_LEN, START_WIDTH, 0, 0)

        # ── 动画总长 ──
        max_spawn = max(
            [b["spawn"] + b["life"] for b in branch_meta] +
            [l["spawn"] + 12 for l in leaf_meta] +
            [60]
        )
        TOTAL_FRAMES = max_spawn + 70

        def step(frame):
            if frame > TOTAL_FRAMES:
                self._safe_destroy_anim()
                return

            # 枝条：到达 spawn 帧才创建
            for br in branch_meta:
                if frame < br["spawn"]:
                    continue
                if br["id"] is None:
                    try:
                        br["id"] = cv.create_line(
                            br["x1"] + 0.5, br["y1"] + 0.5,
                            br["x1"], br["y1"],
                            fill=br["color"], width=br["width"],
                            capstyle="round")
                    except Exception:
                        br["id"] = -1
                        continue
                prog = min(1.0, (frame - br["spawn"]) / br["life"])
                e = _ease_out_cubic(prog)
                cx2 = br["x1"] + (br["x2"] - br["x1"]) * e
                cy2 = br["y1"] + (br["y2"] - br["y1"]) * e
                try:
                    cv.coords(br["id"], br["x1"], br["y1"], cx2, cy2)
                except Exception:
                    pass

            # 叶子：到达 spawn 帧才创建
            for lf in leaf_meta:
                if frame < lf["spawn"]:
                    continue
                if lf["id"] is None:
                    try:
                        lf["id"] = cv.create_oval(
                            lf["x"], lf["y"], lf["x"] + 0.5, lf["y"] + 0.5,
                            fill=lf["color"], outline="")
                        lf["birth"] = frame
                    except Exception:
                        lf["id"] = -1
                        continue
                else:
                    p = min(1.0, (frame - lf["birth"]) / 12.0)
                    r = lf["r"] * _ease_out_cubic(p)
                    try:
                        cv.coords(lf["id"],
                                  lf["x"] - r, lf["y"] - r,
                                  lf["x"] + r, lf["y"] + r)
                    except Exception:
                        pass

            # 最后 60 帧整体淡出
            if frame > TOTAL_FRAMES - 60:
                fade = min(1.0, (frame - (TOTAL_FRAMES - 60)) / 60)
                for br in branch_meta:
                    if br["id"] not in (None, -1):
                        try:
                            c = cv.itemcget(br["id"], "fill")
                            cv.itemconfig(br["id"],
                                           fill=self._lerp_hex(c, T, fade))
                        except Exception:
                            pass
                for lf in leaf_meta:
                    if lf["id"] not in (None, -1):
                        try:
                            c = cv.itemcget(lf["id"], "fill")
                            cv.itemconfig(lf["id"],
                                           fill=self._lerp_hex(c, T, fade))
                        except Exception:
                            pass

            cv.after(35, lambda: step(frame + 1))

        step(0)

    def _anim_fireworks(self, cv, w, h):
        """彩虹烟花：5 朵错时绽放 + 重力 + 拖尾 + 亮度衰减"""
        particles = []
        explosions = []   # 待爆发的烟花

        # 排布爆点
        scale = max(1.0, ((w * h) / (640 * 420)) ** 0.55)
        for i in range(int(5 * min(2.0, scale))):
            ex = random.randint(w // 6, w * 5 // 6)
            ey = random.randint(h // 5, h * 3 // 5)
            hue = (i * 72 + random.randint(-20, 20)) % 360
            explosions.append({"x": ex, "y": ey, "hue": hue,
                                "delay": i * 8})

        def boom(x, y, hue):
            n = random.randint(int(40 * scale), int(60 * scale))
            for _ in range(n):
                ang = random.uniform(0, 2 * math.pi)
                spd = random.uniform(2, 7) * _ease_out_quad(random.random())
                vx = math.cos(ang) * spd
                vy = math.sin(ang) * spd
                # 拖尾：每个粒子多画 1 个暗色影子
                it = cv.create_oval(-10, -10, -10, -10,
                                     fill=self._hsv_to_rgb(hue, 1.0, 1.0),
                                     outline="")
                life = random.randint(45, 80)
                particles.append({
                    "id": it, "x": x, "y": y,
                    "vx": vx, "vy": vy,
                    "life": life, "life_max": life,
                    "size": random.uniform(1.5, 3.5),
                    "hue": hue + random.uniform(-25, 25),
                })
            # 加中心白色闪光
            flash = cv.create_oval(x - 12, y - 12, x + 12, y + 12,
                                    fill="#ffffff", outline="")
            particles.append({
                "id": flash, "x": x, "y": y, "vx": 0, "vy": 0,
                "life": 10, "life_max": 10,
                "size": 12, "hue": 0, "is_flash": True,
            })

        def step(frame):
            if frame > 160:
                self._safe_destroy_anim()
                return

            # 触发爆炸
            for ex in explosions:
                if ex["delay"] == 0:
                    boom(ex["x"], ex["y"], ex["hue"])
                    ex["delay"] = -1
                elif ex["delay"] > 0:
                    ex["delay"] -= 1

            # 更新粒子
            for p in particles:
                if p["life"] <= 0:
                    try: cv.delete(p["id"])
                    except Exception: pass
                    continue
                p["life"] -= 1
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vy"] += 0.15         # 重力
                p["vx"] *= 0.97         # 阻力
                p["vy"] *= 0.99
                t = 1 - p["life"] / p["life_max"]
                if p.get("is_flash"):
                    sz = p["size"] * (1 - t)
                    col = "#ffffff"
                else:
                    # 亮度从 1.0 衰减到 0.15
                    v = 1.0 - 0.85 * t
                    col = self._hsv_to_rgb(p["hue"] % 360, 0.9, v)
                    sz = p["size"] * (1 - t * 0.7)
                try:
                    cv.coords(p["id"], p["x"] - sz, p["y"] - sz,
                              p["x"] + sz, p["y"] + sz)
                    cv.itemconfig(p["id"], fill=col)
                except Exception:
                    pass

            cv.after(26, lambda: step(frame + 1))
        step(0)

    def _anim_pixel(self, cv, w, h):
        """像素爆炸：8-bit 方块 + 缓动向外飞散 + 重力下落 + 旋转色相"""
        blocks = []
        palette = ["#00ff00", "#00ffff", "#ff00ff", "#ffff00",
                   "#ff0000", "#ff9800", "#7c93ff"]

        scale = max(1.0, ((w * h) / (640 * 420)) ** 0.55)
        for _ in range(int(55 * scale)):
            size = random.choice([6, 8, 10, 12, 14, 16])
            x = random.randint(0, w)
            y = random.randint(0, h)
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(1.5, 5.5)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd - 2   # 稍微往上
            col = random.choice(palette)
            it = cv.create_rectangle(x, y, x + size, y + size,
                                      fill=col, outline="")
            life = random.randint(40, 70)
            blocks.append({
                "id": it, "x": x, "y": y,
                "vx": vx, "vy": vy, "size": size,
                "life": life, "life_max": life,
                "col": col, "hue": random.uniform(0, 360),
            })

        def step(frame):
            if frame > 140:
                self._safe_destroy_anim()
                return
            for b in blocks:
                if b["life"] <= 0:
                    try: cv.delete(b["id"])
                    except Exception: pass
                    continue
                b["life"] -= 1
                b["x"] += b["vx"]
                b["y"] += b["vy"]
                b["vy"] += 0.22            # 重力
                b["vx"] *= 0.96            # 阻力
                t = 1 - b["life"] / b["life_max"]
                # 颜色向暗色渐隐
                col = self._lerp_hex(b["col"], C("SURFACE"), t * t)
                sz = b["size"] * (1 - t * 0.55)
                try:
                    cv.coords(b["id"], b["x"], b["y"],
                              b["x"] + sz, b["y"] + sz)
                    cv.itemconfig(b["id"], fill=col)
                except Exception:
                    pass
            cv.after(28, lambda: step(frame + 1))
        step(0)

    def _anim_whale(self, cv, w, h):
        """蓝鲸从右往左游，鲸鱼本体染为蓝色（轮廓不变）"""
        scale = max(1.0, (w * h) / (640 * 420))
        base_y = h // 2
        whale_size = int(100 * min(2.0, scale))

        # ── 尝试用 PIL 把 emoji 染成蓝色 ──
        photo = None
        try:
            from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageOps

            WHALE_DARK  = (30, 90, 180)      # 深蓝（暗部）
            WHALE_LIGHT = (150, 210, 255)    # 亮蓝（高光）

            font_size = whale_size * 2
            embedded = True
            try:
                font = ImageFont.truetype(
                    "C:/Windows/Fonts/seguiemj.ttf", font_size)
            except Exception:
                font = ImageFont.truetype(
                    "C:/Windows/Fonts/segoeuib.ttf", font_size)
                embedded = False

            # 渲染 emoji 到一张透明画布
            big = Image.new("RGBA",
                            (font_size * 2, font_size * 2),
                            (0, 0, 0, 0))
            d = ImageDraw.Draw(big)
            if embedded:
                d.text((font_size, font_size), "🐳", font=font,
                       embedded_color=True, anchor="mm")
            else:
                d.text((font_size, font_size), "🐳", font=font,
                       fill=(255, 255, 255, 255), anchor="mm")

            # 裁到内容边界
            bbox = big.getbbox()
            if bbox:
                big = big.crop(bbox)

            # 灰度 → 蓝色渐变，保留 alpha（形状不变）
            alpha = big.split()[3]
            gray  = big.convert("L")
            blue  = ImageOps.colorize(gray,
                                       black=WHALE_DARK,
                                       white=WHALE_LIGHT)
            blue.putalpha(alpha)

            # 缩放到目标尺寸
            target = int(whale_size * 1.3)
            blue = blue.resize((target, target), Image.LANCZOS)
            photo = ImageTk.PhotoImage(blue)
            self._whale_photo = photo      # 防被 GC
        except Exception:
            photo = None

        # ── 创建鲸鱼（优先用染色图，失败退回 emoji）──
        start_x = w + whale_size
        if photo is not None:
            whale = cv.create_image(start_x, base_y,
                                     image=photo, anchor="center")
        else:
            whale = cv.create_text(start_x, base_y, text="🐳",
                                    font=("Segoe UI Emoji", whale_size),
                                    anchor="center")

        step_delta = -8
        bubbles = []
        trail = []

        def spawn_bubble(x, y):
            b_size = random.uniform(2, 6) * min(2.0, scale)
            it = cv.create_oval(x - b_size, y - b_size,
                                 x + b_size, y + b_size,
                                 fill=self._hsv_to_rgb(
                                     random.uniform(180, 220), 0.7, 0.9),
                                 outline="")
            bubbles.append({
                "id": it, "x": x, "y": y,
                "vy": random.uniform(-1.2, -0.4),
                "vx": random.uniform(-0.5, 0.5),
                "life": random.randint(30, 55),
                "life_max": 55,
                "size": b_size,
            })

        def spawn_trail(x, y):
            sz = random.uniform(2, 4) * min(2.0, scale)
            it = cv.create_oval(x - sz, y - sz, x + sz, y + sz,
                                 fill="#7c93ff", outline="")
            trail.append({
                "id": it, "x": x, "y": y, "size": sz,
                "life": 20, "life_max": 20,
            })

        def step(x):
            if x < -whale_size - 50:
                self._safe_destroy_anim()
                return

            y = base_y + int(30 * math.sin(x / 55))
            try:
                cv.coords(whale, x, y)
            except Exception:
                return

            if random.random() < 0.6:
                spawn_bubble(x + whale_size * 0.6 + random.randint(-15, 15),
                              y + random.randint(-10, 25))
            if random.random() < 0.8:
                spawn_trail(x + whale_size * 0.8 + random.randint(-8, 8),
                             y + random.randint(-5, 15))

            for b in bubbles[:]:
                b["life"] -= 1
                if b["life"] <= 0:
                    try: cv.delete(b["id"])
                    except Exception: pass
                    bubbles.remove(b)
                    continue
                b["y"] += b["vy"]
                b["x"] += b["vx"]
                t = 1 - b["life"] / b["life_max"]
                sz = b["size"] * (1 - t * 0.5)
                col = self._lerp_hex(
                    self._hsv_to_rgb(200, 0.7, 0.9),
                    self._anim_transparent, t)
                try:
                    cv.coords(b["id"], b["x"] - sz, b["y"] - sz,
                              b["x"] + sz, b["y"] + sz)
                    cv.itemconfig(b["id"], fill=col)
                except Exception:
                    pass

            for tr in trail[:]:
                tr["life"] -= 1
                if tr["life"] <= 0:
                    try: cv.delete(tr["id"])
                    except Exception: pass
                    trail.remove(tr)
                    continue
                t = 1 - tr["life"] / tr["life_max"]
                col = self._lerp_hex("#7c93ff", self._anim_transparent, t)
                sz = tr["size"] * (1 - t * 0.5)
                try:
                    cv.coords(tr["id"], tr["x"] - sz, tr["y"] - sz,
                              tr["x"] + sz, tr["y"] + sz)
                    cv.itemconfig(tr["id"], fill=col)
                except Exception:
                    pass

            cv.after(22, lambda: step(x + step_delta))
        step(start_x)

    def _anim_ripple(self, cv, w, h):
        """水波纹：八圈错时涟漪 + 中心闪光"""
        T = self._anim_transparent
        cx, cy = w // 2, h // 2
        scale = max(1.0, ((w * h) / (640 * 420)) ** 0.55)
        max_r = 260 * scale
        ripples = []
        for i in range(8):
            it = cv.create_oval(-1, -1, -1, -1,
                                 outline="#00bcd4", width=3)
            ripples.append({
                "id": it, "delay": i * 5,
                "r": 5, "life": 55, "life_max": 55,
                "hue": 180 + i * 8,
            })
        center = cv.create_oval(cx - 12, cy - 12, cx + 12, cy + 12,
                                 fill="#ffffff", outline="")

        def step(frame):
            if frame > 150:
                self._safe_destroy_anim()
                return
            t_c = min(1.0, frame / 12)
            r_c = 12 * (1 - t_c)
            try:
                cv.coords(center, cx - r_c, cy - r_c, cx + r_c, cy + r_c)
                if frame > 12:
                    cv.delete(center)
            except Exception:
                pass
            for rp in ripples:
                if rp["delay"] > 0:
                    rp["delay"] -= 1
                    continue
                if rp["life"] <= 0:
                    try: cv.delete(rp["id"])
                    except Exception: pass
                    continue
                rp["life"] -= 1
                t = 1 - rp["life"] / rp["life_max"]
                rp["r"] = _ease_out_quad(t) * max_r
                wd = max(1, int(4 * (1 - t)))
                col = self._lerp_hex(
                    self._hsv_to_rgb(rp["hue"], 1.0, 1.0), T, t * t)
                try:
                    cv.coords(rp["id"], cx - rp["r"], cy - rp["r"],
                              cx + rp["r"], cy + rp["r"])
                    cv.itemconfig(rp["id"], outline=col, width=wd)
                except Exception:
                    pass
            cv.after(28, lambda: step(frame + 1))
        step(0)

    def _anim_lightning(self, cv, w, h):
        """雷电：单色黄色折线 + 尖角转折 + 多次闪烁"""
        T = self._anim_transparent

        # ── 单色黄 ──
        LIGHTNING = "#ffdd00"    # 闪电的唯一颜色

        line_items = []
        flashes = []

        # ── 生成一条折线（不用 smooth，走尖角）──
        def make_polyline(start_x, end_y, segments=16, jitter=42):
            pts = [(start_x + random.randint(-10, 10), -10)]
            x, y = pts[0]
            step_y = (end_y + 10) / segments
            for i in range(1, segments + 1):
                if i == segments:
                    # 最后一点：垂直方向必须拉开，避免出现短棍
                    pts.append((x + random.randint(-jitter, jitter), end_y))
                    break
                x += random.randint(-jitter, jitter)
                y += step_y + random.randint(-4, 4)
                x = max(30, min(w - 30, x))
                pts.append((x, y))
            return pts

        # ── 分支折线（也是尖角，从主干某点斜向下）──
        def make_branch(start_pt, length):
            x0, y0 = start_pt
            side = random.choice([-1, 1])
            pts = [(x0, y0)]
            n = random.randint(5, 7)
            for i in range(1, n + 1):
                t = i / n
                nx = x0 + side * length * t + random.randint(-12, 12)
                ny = y0 + length * t * 0.75 + random.randint(-6, 6)
                pts.append((nx, ny))
            return pts

        # ── 画一条折线：单色、单层、尖角 ──
        def draw(pts, width):
            flat = []
            for (x, y) in pts:
                flat.extend([x, y])
            try:
                it = cv.create_line(*flat,
                                     fill=LIGHTNING,
                                     width=width,
                                     capstyle="round",
                                     joinstyle="miter")   # 尖角，不用圆角
                line_items.append(it)
            except Exception:
                pass

        # ── 一次劈落 ──
        def strike():
            sx = random.randint(w // 5, w * 4 // 5)
            main_pts = make_polyline(sx, int(h * 0.9))
            draw(main_pts, 4)                # 主干宽度 4
            # 分支：从主干中段开始，不要首尾两端
            for i in range(3, len(main_pts) - 3):
                if random.random() < 0.5:
                    br = make_branch(main_pts[i],
                                      length=random.randint(90, 180))
                    draw(br, 3)              # 分支宽度 3

            # 全屏泛白（暖白，配黄色闪电）
            fl = cv.create_rectangle(0, 0, w, h,
                                      fill="#fff5c0", outline="",
                                      stipple="gray50")
            flashes.append({"id": fl, "life": 6})

        def clear_lines():
            for it in line_items:
                try: cv.delete(it)
                except Exception: pass
            line_items.clear()

        # ── 时间轴 ──
        HOLD = 8
        strike_frames = [0, 22, 60, 115, 175]
        total_frames = 240

        strike()

        def step(frame):
            if frame > total_frames:
                self._safe_destroy_anim()
                return
            if frame in strike_frames and frame != 0:
                clear_lines()
                strike()
            for sf in strike_frames:
                if frame == sf + HOLD:
                    clear_lines()
            for fl in flashes[:]:
                fl["life"] -= 1
                if fl["life"] <= 0:
                    try: cv.delete(fl["id"])
                    except Exception: pass
                    flashes.remove(fl)
            cv.after(26, lambda: step(frame + 1))
        step(0)

    def _anim_tornado(self, cv, w, h):
        """龙卷风：从屏幕一侧移动到另一侧，带锥形漏斗 + 旋转粒子 + 地面碎屑"""
        T = self._anim_transparent
        scale = max(1.0, ((w * h) / (640 * 420)) ** 0.55)

        # ---- 几何参数 ----
        base_y   = h * 0.90              # 地面
        top_y    = h * 0.08              # 顶端
        top_r    = max(60, h * 0.28)     # 顶端半径（大口）
        bottom_r = max(8,  h * 0.022)    # 地面半径（漏斗尖端）

        # ---- 移动路径：加速（200 帧走完全程）----
        margin  = top_r + 40
        start_x = -margin
        end_x   = w + margin
        total_frames = 260
        move_frames  = 200

        parts  = []   # 漏斗旋转粒子
        debris = []   # 地面碎屑

        def funnel_r(y_t):
            """y_t: 0=地面, 1=顶端 -> 该高度的最大半径"""
            return bottom_r + (top_r - bottom_r) * (y_t ** 1.4)

        def spawn_vortex(cx_now):
            y_t = random.random() ** 1.6
            y   = base_y - (base_y - top_y) * y_t
            r_max = funnel_r(y_t)
            r = r_max * random.uniform(0.35, 1.0)
            angle = random.uniform(0, 2 * math.pi)
            x = cx_now + math.cos(angle) * r
            sz = random.uniform(1.6, 4.2) * (1 - y_t * 0.45)
            hue = random.uniform(195, 235)
            sat = 0.20 + random.uniform(0, 0.30)
            val = 0.50 + random.uniform(0, 0.40)
            it = cv.create_oval(x - sz, y - sz, x + sz, y + sz,
                                 fill=self._hsv_to_rgb(hue, sat, val),
                                 outline="")
            spin = (0.35 + 0.55 * (bottom_r / max(r, 4))) * random.uniform(0.7, 1.3)
            parts.append({
                "id": it, "x": x, "y": y,
                "angle": angle,
                "size": sz, "hue": hue, "sat": sat, "val": val,
                "spin": spin,
                "life": random.randint(35, 75),
                "life_max": 75,
                "vy": random.uniform(-3.8, -1.8) * (1 + y_t * 0.6),
            })

        def spawn_debris(cx_now):
            angle = random.uniform(0, 2 * math.pi)
            r = bottom_r * random.uniform(0.4, 1.8)
            x = cx_now + math.cos(angle) * r
            y = base_y - random.uniform(-8, 25)
            sz = random.uniform(1.5, 4.5)
            hue = random.uniform(15, 48)      # 土黄
            it = cv.create_rectangle(x - sz, y - sz, x + sz, y + sz,
                                       fill=self._hsv_to_rgb(hue, 0.45, 0.70),
                                       outline="")
            tang = angle + math.pi / 2
            spd = random.uniform(2.5, 7.0)
            debris.append({
                "id": it, "x": x, "y": y,
                "vx": math.cos(tang) * spd,
                "vy": -random.uniform(2.0, 5.0),
                "size": sz, "hue": hue,
                "life": random.randint(22, 48),
                "life_max": 48,
            })

        def step(frame):
            if frame > total_frames:
                self._safe_destroy_anim()
                return

            # --- 位置：ease-in-out 横穿屏幕 ---
            if frame <= move_frames:
                t = frame / move_frames
                if t < 0.5:
                    te = 2 * t * t
                else:
                    te = 1 - ((-2 * t + 2) ** 2) / 2
            else:
                te = 1.0
            cx_now = start_x + (end_x - start_x) * te

            # 离屏时降低生成率
            if cx_now < -top_r * 0.5 or cx_now > w + top_r * 0.5:
                gen = 0.15
            elif cx_now < 0 or cx_now > w:
                gen = 0.5
            else:
                gen = 1.0

            # --- 生成粒子 ---
            for _ in range(int(random.uniform(3, 6) * scale * gen)):
                spawn_vortex(cx_now)
            if random.random() < 0.5 * gen:
                spawn_debris(cx_now)

            # --- 更新漏斗粒子 ---
            for p in parts[:]:
                p["life"] -= 1
                if p["life"] <= 0:
                    try: cv.delete(p["id"])
                    except Exception: pass
                    parts.remove(p)
                    continue
                p["y"] += p["vy"]
                y_t = max(0.0, min(1.0, (base_y - p["y"]) / (base_y - top_y)))
                r_max = funnel_r(y_t)
                p["angle"] += p["spin"] * 0.18
                life_t = 1 - p["life"] / p["life_max"]
                r_now = r_max * (0.35 + 0.65 * life_t)
                p["x"] = cx_now + math.cos(p["angle"]) * r_now

                sz  = p["size"] * (1 - life_t * 0.45)
                val = p["val"] * (1 - life_t * 0.75)
                col = self._hsv_to_rgb(p["hue"], p["sat"], val)
                try:
                    cv.coords(p["id"], p["x"] - sz, p["y"] - sz,
                              p["x"] + sz, p["y"] + sz)
                    cv.itemconfig(p["id"], fill=col)
                except Exception:
                    pass

            # --- 更新地面碎屑 ---
            for d in debris[:]:
                d["life"] -= 1
                if d["life"] <= 0:
                    try: cv.delete(d["id"])
                    except Exception: pass
                    debris.remove(d)
                    continue
                d["x"] += d["vx"]
                d["y"] += d["vy"]
                d["vy"] += 0.18          # 重力
                d["vx"] *= 0.97
                t = 1 - d["life"] / d["life_max"]
                sz = d["size"] * (1 - t * 0.5)
                col = self._lerp_hex(
                    self._hsv_to_rgb(d["hue"], 0.45, 0.70), T, t)
                try:
                    cv.coords(d["id"], d["x"] - sz, d["y"] - sz,
                              d["x"] + sz, d["y"] + sz)
                    cv.itemconfig(d["id"], fill=col)
                except Exception:
                    pass

            cv.after(28, lambda: step(frame + 1))

        step(0)
    def _anim_blackhole(self, cv, w, h):
        """黑洞吞噬：前半段螺旋吸入，后半段黑洞扩张吞掉所有粒子。"""
        T = self._anim_transparent
        cx, cy = w // 2, h // 2
        parts = []

        scale = max(1.0, ((w * h) / (640 * 420)) ** 0.55)
        max_dist = 320 * scale
        for _ in range(int(95 * scale)):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(max_dist * 0.7, max_dist)
            x = cx + math.cos(angle) * dist
            y = cy + math.sin(angle) * dist
            tang = angle + math.pi / 2
            spd = random.uniform(1.4, 3.0)
            vx = math.cos(tang) * spd
            vy = math.sin(tang) * spd
            sz = random.uniform(1.5, 4)
            hue = random.uniform(255, 320)
            it = cv.create_oval(x - sz, y - sz, x + sz, y + sz,
                                 fill=self._hsv_to_rgb(hue, 0.8, 0.9),
                                 outline="")
            parts.append({
                "id": it, "x": x, "y": y, "vx": vx, "vy": vy,
                "size": sz, "hue": hue, "alive": True,
            })

        hole = cv.create_oval(cx - 5, cy - 5, cx + 5, cy + 5,
                               fill="#000000",
                               outline="#a855f7", width=2)
        # 光环（外圈紫色描边，随黑洞扩大）
        halo = cv.create_oval(cx - 8, cy - 8, cx + 8, cy + 8,
                               outline="#e0c4ff", width=1)
        state = {"r": 5}
        PHASE1_END = 80     # 前半段结束帧
        PHASE2_END = 200    # 后半段结束帧

        def step(frame):
            if frame > PHASE2_END:
                self._safe_destroy_anim()
                return

            # === 黑洞半径分两段 ===
            if frame <= PHASE1_END:
                # 前半段：缓慢从 5 扩到 52
                state["r"] = 5 + (52 - 5) * (frame / PHASE1_END)
            else:
                # 后半段：快速扩到 ~155（约 3 倍），然后保持
                t = (frame - PHASE1_END) / (PHASE2_END - PHASE1_END)
                t_expand = min(1.0, t / 0.45)   # 前 45% 时间内扩到最大
                state["r"] = 52 + (155 - 52) * _ease_out_cubic(t_expand)

            try:
                cv.coords(hole, cx - state["r"], cy - state["r"],
                          cx + state["r"], cy + state["r"])
                halo_r = state["r"] + 6
                cv.coords(halo, cx - halo_r, cy - halo_r,
                          cx + halo_r, cy + halo_r)
            except Exception:
                pass

            is_phase2 = frame > PHASE1_END
            for p in parts[:]:
                if not p["alive"]:
                    continue
                dx = cx - p["x"]
                dy = cy - p["y"]
                dist = math.sqrt(dx * dx + dy * dy) + 0.001

                if not is_phase2:
                    # 前半段：螺旋吸入
                    force = 45.0 / (dist + 60)
                    p["vx"] += dx / dist * force
                    p["vy"] += dy / dist * force
                    tx = -dy / dist
                    ty = dx / dist
                    p["vx"] += tx * 0.32
                    p["vy"] += ty * 0.32
                    p["x"] += p["vx"] * 0.5
                    p["y"] += p["vy"] * 0.5
                else:
                    # 后半段：直接被吸入，速度飞快
                    p["vx"] += dx / dist * 2.2
                    p["vy"] += dy / dist * 2.2
                    spd = math.sqrt(p["vx"] ** 2 + p["vy"] ** 2)
                    if spd > 25:
                        p["vx"] *= 25 / spd
                        p["vy"] *= 25 / spd
                    p["x"] += p["vx"]
                    p["y"] += p["vy"]

                if dist < state["r"] + 3:
                    p["alive"] = False
                    try: cv.delete(p["id"])
                    except Exception: pass
                    parts.remove(p)
                    continue

                near = max(0.0, 1 - dist / 200)
                hue = (p["hue"] - near * 110) % 360
                col = self._hsv_to_rgb(hue, 0.9, 0.9)
                sz = p["size"] * (1 - near * 0.5)
                try:
                    cv.coords(p["id"], p["x"] - sz, p["y"] - sz,
                              p["x"] + sz, p["y"] + sz)
                    cv.itemconfig(p["id"], fill=col)
                except Exception:
                    pass

            cv.after(38, lambda: step(frame + 1))
        step(0)

    def _anim_rainbow(self, cv, w, h):
        """彩虹雨：彩色光点从天而降，色相流动"""
        T = self._anim_transparent
        scale = max(1.0, ((w * h) / (640 * 420)) ** 0.55)
        drops = []

        def spawn():
            x = random.randint(0, w)
            y = -10
            size = random.uniform(2, 5)
            hue = random.uniform(0, 360)
            it = cv.create_oval(x - size, y - size, x + size, y + size,
                                 fill=self._hsv_to_rgb(hue, 0.85, 1.0),
                                 outline="")
            vy = random.uniform(4, 9)
            drops.append({
                "id": it, "x": x, "y": y,
                "vy": vy, "size": size, "hue": hue,
            })

        def step(frame):
            if frame > 200:
                self._safe_destroy_anim()
                return
            for _ in range(random.randint(int(2 * scale), int(4 * scale))):
                spawn()
            for d in drops[:]:
                d["y"] += d["vy"]
                if d["y"] > h + 12:
                    try: cv.delete(d["id"])
                    except Exception: pass
                    drops.remove(d)
                    continue
                hue = (d["hue"] + frame * 2.5) % 360
                col = self._hsv_to_rgb(hue, 0.9, 1.0)
                sz = d["size"]
                try:
                    cv.coords(d["id"], d["x"] - sz, d["y"] - sz,
                              d["x"] + sz, d["y"] + sz)
                    cv.itemconfig(d["id"], fill=col)
                except Exception:
                    pass
            cv.after(28, lambda: step(frame + 1))
        step(0)

    # ---------- Tabs ----------
    def _build_tabs(self):
        bar = tk.Frame(self.root, bg=C("BG")); reg(bar, bg="BG")
        bar.pack(fill="x", padx=32, pady=(20, 0))
        self.tab_ov = Pill(bar, "  概览  ", command=lambda: self._switch("ov"))
        self.tab_ov.pack(side="left")
        self.tab_dt = Pill(bar, "  历史明细  ", command=lambda: self._switch("dt"))
        self.tab_dt.pack(side="left", padx=(8, 0))
        self.tab_shop = Pill(bar, "  🎁 商城  ", command=lambda: self._switch("shop"))
        self.tab_shop.pack(side="left", padx=(8, 0))
        self.tab_st = Pill(bar, "  ⚙  设置  ", command=lambda: self._switch("st"))
        self.tab_st.pack(side="left", padx=(8, 0))
        self.tab_about = Pill(bar, "  ℹ  关于  ", command=lambda: self._switch("about"))
        self.tab_about.pack(side="left", padx=(8, 0))
        self.tab_ov.set_active(True)

    def _switch(self, which):
        for k, tab in [("ov", self.tab_ov), ("dt", self.tab_dt),
                        ("st", self.tab_st),
                        ("shop", self.tab_shop), ("about", self.tab_about)]:
            tab.set_active(k == which)
        target = {"ov": self.page_ov, "dt": self.page_dt,
                  "st": self.page_st,
                  "shop": self.page_shop, "about": self.page_about}[which]
        if which == "dt": self._reload_table()
        if which == "shop": self._build_shop_list()
        self._slide_in(target)

    def _slide_in(self, target_page):
        target_page.tkraise()

    def _place_page(self, page, x_off):
        try:
            page.place(in_=self._content, x=x_off, rely=0,
                       relwidth=1, relheight=1)
        except tk.TclError: pass

    # ---------- 内容 ----------
    def _build_content(self):
        self._content = tk.Frame(self.root, bg=C("BG")); reg(self._content, bg="BG")
        self._content.pack(fill="both", expand=True, padx=32, pady=(16, 0))
        self._content.bind("<Configure>", lambda e: self._apply_layout())
        self.page_ov = tk.Frame(self._content, bg=C("BG")); reg(self.page_ov, bg="BG")
        self.page_dt = tk.Frame(self._content, bg=C("BG")); reg(self.page_dt, bg="BG")
        self.page_st = tk.Frame(self._content, bg=C("BG")); reg(self.page_st, bg="BG")
        self.page_shop = tk.Frame(self._content, bg=C("BG")); reg(self.page_shop, bg="BG")
        self.page_about = tk.Frame(self._content, bg=C("BG")); reg(self.page_about, bg="BG")
        for p in (self.page_ov, self.page_dt, self.page_st, self.page_shop, self.page_about):
            p.place(in_=self._content, x=0, rely=0, relwidth=1, relheight=1)
        self._build_overview()
        self._build_detail()
        self._build_shop_page()
        self._build_settings()
        self._build_about_page()


    # ===== 概览 =====
    def _build_overview(self):
        p = self.page_ov

        hero_outer, hero = make_card(p, padx=32, pady=24)
        self._block_widgets["hero"] = hero_outer

        top = tk.Frame(hero, bg=C("SURFACE")); reg(top, bg="SURFACE")
        top.pack(fill="x")
        reg(tk.Label(top, text="累计删除", font=(FONT, 11, "bold")),
            bg="SURFACE", fg="MUTED").pack(side="left")

        self.combo_label = tk.Label(top, text="", font=(MONO, 13, "bold"),
                                     bg=C("SURFACE"), fg=C("RED"))
        reg(self.combo_label, bg="SURFACE", fg="RED")
        self.combo_label.pack(side="left", padx=(12, 0))

        self.new_label = tk.Label(top, text="", font=(FONT, 10),
                                   bg=C("SURFACE"), fg=C("YELLOW"))
        reg(self.new_label, bg="SURFACE", fg="YELLOW")
        self.new_label.pack(side="right")

        nr = tk.Frame(hero, bg=C("SURFACE")); reg(nr, bg="SURFACE")
        nr.pack(fill="x", pady=(12, 0))
        self.bytes_label = tk.Label(nr, text="—", font=(MONO, 50, "bold"),
                                     bg=C("SURFACE"), fg=C("TEXT"))
        reg(self.bytes_label, bg="SURFACE", fg="TEXT")
        self.bytes_label.pack(side="left")
        self.unit_label = tk.Label(nr, text="字节", font=(FONT, 13),
                                    bg=C("SURFACE"), fg=C("DIM"))
        reg(self.unit_label, bg="SURFACE", fg="DIM")
        self.unit_label.pack(side="left", padx=(10, 0), pady=(14, 0))

        self.human_label = tk.Label(nr, text="", font=(FONT, 12),
                                     bg=C("SURFACE"), fg=C("ACCENT"))
        reg(self.human_label, bg="SURFACE", fg="ACCENT")
        self.human_label.pack(side="left", padx=(18, 0), pady=(14, 0))

        self.card_cur,    _ = self._stat_card(p, "当前回收站", "—", "GREEN")
        self.card_items,  _ = self._stat_card_dual(
            p, "历史累计删除", "历史删除项数", "—", "删除文件总数", "—",
            "PURPLE", "YELLOW")
        self.card_cleared, _ = self._stat_card(p, "为你的电脑减负", "—", "YELLOW")
        self._block_widgets["stat_cur"]    = self.card_cur
        self._block_widgets["stat_items"]  = self.card_items
        self._block_widgets["stat_files"]  = self.card_cleared

        # ===== 分区统计卡片（内嵌分区列表 + 垂直滚动条） =====
        self.card_drives, drives_inner = self._stat_card(p, "分区统计", "—", "ACCENT")
        self._block_widgets["stat_drives"] = self.card_drives

        drives_wrap = tk.Frame(drives_inner, bg=C("SURFACE"))
        reg(drives_wrap, bg="SURFACE")
        drives_wrap.pack(fill="both", expand=True, pady=(8, 0))
        drives_canvas = tk.Canvas(drives_wrap, bg=C("SURFACE"), bd=0,
                                    highlightthickness=0)
        reg(drives_canvas, bg="SURFACE")
        drives_vsb = ttk.Scrollbar(drives_wrap, orient="vertical",
                                     command=drives_canvas.yview,
                                     style="Modern.Vertical.TScrollbar")
        drives_canvas.configure(yscrollcommand=drives_vsb.set)
        drives_canvas.pack(side="left", fill="both", expand=True)
        drives_vsb.pack(side="right", fill="y")
        self.drives_box = tk.Frame(drives_canvas, bg=C("SURFACE"))
        reg(self.drives_box, bg="SURFACE")
        drives_win = drives_canvas.create_window((0, 0), window=self.drives_box,
                                                   anchor="nw")
        def _sync_drives_scroll(e=None):
            try:
                drives_canvas.update_idletasks()
                bb = drives_canvas.bbox("all")
                if not bb: return
                x1, y1, x2, y2 = bb
                ch = drives_canvas.winfo_height()
                drives_canvas.configure(
                    scrollregion=(0, 0, x2, max(y2, ch)))
            except Exception:
                pass
        drives_canvas.bind("<Configure>",
            lambda e: (drives_canvas.itemconfigure(drives_win,
                       width=max(1, e.width - 12)),
                       _sync_drives_scroll()))
        self.drives_box.bind("<Configure>", _sync_drives_scroll)
        self._drives_canvas = drives_canvas
        def _dw(e):
            drives_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        drives_canvas.bind("<MouseWheel>", _dw)
        self.drives_box.bind("<MouseWheel>", _dw)

        # ===== 左下：趋势图（带水平滚动条） =====
        co, ci = make_card(p, padx=18, pady=12)
        self._block_widgets["chart"] = co

        chart_head = tk.Frame(ci, bg=C("SURFACE")); reg(chart_head, bg="SURFACE")
        chart_head.pack(fill="x")
        self.chart_title = tk.Label(chart_head, text="最近 7 天删除趋势",
                                      font=(FONT, 10, "bold"),
                                      bg=C("SURFACE"), fg=C("MUTED"))
        reg(self.chart_title, bg="SURFACE", fg="MUTED")
        self.chart_title.pack(side="left")
        self.chart_peak = tk.Label(chart_head, text="", font=(FONT, 9),
                                     bg=C("SURFACE"), fg=C("DIM"))
        reg(self.chart_peak, bg="SURFACE", fg="DIM")
        self.chart_peak.pack(side="right")

        chart_wrap = tk.Frame(ci, bg=C("SURFACE")); reg(chart_wrap, bg="SURFACE")
        chart_wrap.pack(fill="both", expand=True, pady=(6, 0))
        self.chart_canvas = tk.Canvas(chart_wrap, bg=C("SURFACE"), bd=0,
                                        highlightthickness=0, height=90)
        reg(self.chart_canvas, bg="SURFACE")
        chart_hsb = ttk.Scrollbar(chart_wrap, orient="horizontal",
                                    command=self.chart_canvas.xview,
                                    style="Modern.Horizontal.TScrollbar")
        self.chart_canvas.configure(xscrollcommand=chart_hsb.set)
        self.chart_canvas.pack(fill="both", expand=True)
        chart_hsb.pack(fill="x")
        self.chart_canvas.bind("<Configure>", lambda e: self._draw_chart())

        # ===== 右下：类型分布（带垂直滚动条） =====
        eo, ei = make_card(p, padx=22, pady=18)
        self._block_widgets["ext"] = eo
        reg(tk.Label(ei, text="历史累计 · 类型分布", font=(FONT, 10, "bold")),
            bg="SURFACE", fg="MUTED").pack(anchor="w")

        ext_wrap = tk.Frame(ei, bg=C("SURFACE")); reg(ext_wrap, bg="SURFACE")
        ext_wrap.pack(fill="both", expand=True, pady=(10, 0))
        ext_canvas = tk.Canvas(ext_wrap, bg=C("SURFACE"), bd=0,
                                 highlightthickness=0)
        reg(ext_canvas, bg="SURFACE")
        ext_vsb = ttk.Scrollbar(ext_wrap, orient="vertical",
                                  command=ext_canvas.yview,
                                  style="Modern.Vertical.TScrollbar")
        ext_canvas.configure(yscrollcommand=ext_vsb.set)
        ext_canvas.pack(side="left", fill="both", expand=True)
        ext_vsb.pack(side="right", fill="y")
        self.ext_box = tk.Frame(ext_canvas, bg=C("SURFACE"))
        reg(self.ext_box, bg="SURFACE")
        ext_win = ext_canvas.create_window((0, 0), window=self.ext_box, anchor="nw")
        def _sync_ext_scroll(e=None):
            try:
                ext_canvas.update_idletasks()
                bb = ext_canvas.bbox("all")
                if not bb: return
                x1, y1, x2, y2 = bb
                ch = ext_canvas.winfo_height()
                ext_canvas.configure(scrollregion=(0, 0, x2, max(y2, ch)))
            except Exception:
                pass
        ext_canvas.bind("<Configure>",
            lambda e: (ext_canvas.itemconfigure(ext_win,
                       width=max(1, e.width - 12)),
                       _sync_ext_scroll()))
        self.ext_box.bind("<Configure>", _sync_ext_scroll)
        self._ext_canvas = ext_canvas
        def _ew(e):
            ext_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        ext_canvas.bind("<MouseWheel>", _ew)
        self.ext_box.bind("<MouseWheel>", _ew)

        self._apply_layout()
        p.bind("<Configure>", lambda e: self._apply_layout())
        self._toast_frame = None

    def _stat_card(self, parent, label, value, accent):
        o, i = make_card(parent, padx=20, pady=16)
        reg(tk.Label(i, text=label, font=(FONT, 10)),
            bg="SURFACE", fg="MUTED").pack(anchor="w")
        v = tk.Label(i, text=value, font=(MONO, 18, "bold"),
                     bg=C("SURFACE"), fg=C(accent))
        reg(v, bg="SURFACE", fg=accent)
        v.pack(anchor="w", pady=(6, 0))
        s = tk.Label(i, text="", font=(FONT, 9), bg=C("SURFACE"), fg=C("DIM"))
        reg(s, bg="SURFACE", fg="DIM")
        s.pack(anchor="w", pady=(2, 0))
        o._v = v; o._s = s
        return o, i

    def _stat_card_dual(self, parent, title, left_label, left_value,
                        right_label, right_value, accent_l, accent_r):
        o, i = make_card(parent, padx=20, pady=16)
        reg(tk.Label(i, text=title, font=(FONT, 10)),
            bg="SURFACE", fg="MUTED").pack(anchor="w")
        row = tk.Frame(i, bg=C("SURFACE")); reg(row, bg="SURFACE")
        row.pack(fill="x", pady=(6, 0))

        left = tk.Frame(row, bg=C("SURFACE")); reg(left, bg="SURFACE")
        left.pack(side="left", fill="x", expand=True)
        lv = tk.Label(left, text=left_value, font=(MONO, 15, "bold"),
                      bg=C("SURFACE"), fg=C(accent_l))
        reg(lv, bg="SURFACE", fg=accent_l)
        lv.pack(anchor="w")
        ls = tk.Label(left, text=left_label, font=(FONT, 9),
                      bg=C("SURFACE"), fg=C("DIM"))
        reg(ls, bg="SURFACE", fg="DIM")
        ls.pack(anchor="w", pady=(2, 0))

        sep = tk.Frame(row, bg=C("BORDER"), width=1)
        reg(sep, bg="BORDER")
        sep.pack(side="left", fill="y", padx=12, pady=6)

        right = tk.Frame(row, bg=C("SURFACE")); reg(right, bg="SURFACE")
        right.pack(side="left", fill="x", expand=True)
        rv = tk.Label(right, text=right_value, font=(MONO, 15, "bold"),
                      bg=C("SURFACE"), fg=C(accent_r))
        reg(rv, bg="SURFACE", fg=accent_r)
        rv.pack(anchor="w")
        rs = tk.Label(right, text=right_label, font=(FONT, 9),
                      bg=C("SURFACE"), fg=C("DIM"))
        reg(rs, bg="SURFACE", fg="DIM")
        rs.pack(anchor="w", pady=(2, 0))

        o._lv = lv; o._ls = ls
        o._rv = rv; o._rs = rs
        return o, i

    def _apply_layout(self):
        p = self.page_ov
        for name, w in self._block_widgets.items():
            info = self.layout.get(name)
            if not info: continue
            try:
                w.place(in_=p,
                        relx=info["relx"], rely=info["rely"],
                        relwidth=info["relwidth"], relheight=info["relheight"])
            except tk.TclError:
                pass

    def _bind_wheel_recursive(self, widget, callback):
        try: widget.bind("<MouseWheel>", callback)
        except Exception: pass
        for c in widget.winfo_children():
            self._bind_wheel_recursive(c, callback)

    # ---------- 伤害数字弹出 ----------
    def _spawn_damage(self, filename, size, drive=""):
        if not hasattr(self, "damage_canvas"): return
        if not self.settings.get("motion_enabled", True):
            return
        try:
            text = f"{filename[:18]}  +{human_size(size)}"
            # 随机纵向偏移，避免完全重叠
            y = random.randint(10, 45)
            colors = ["#f2c96d", "#5bd6a4", "#b39eff", "#7c93ff", "#f07178"]
            col = random.choice(colors)
            DamagePopup(self.damage_canvas, 5, y, text, col, life=36)
        except Exception:
            pass

    # ---------- 连击 ----------
    def _bump_combo(self, count):
        now = time.time()
        if now - self._combo_last_time < 10:
            self._combo += count
        else:
            self._combo = count
        self._combo_last_time = now
        if self._combo > self.game.get("max_combo", 0):
            self.game["max_combo"] = self._combo
            save_game(self.game)
        self._update_combo_label()

        # 重置计时器
        if self._combo_reset_id:
            try: self.root.after_cancel(self._combo_reset_id)
            except Exception: pass
        self._combo_reset_id = self.root.after(10000, self._reset_combo)

    def _reset_combo(self):
        self._combo = 0
        self._combo_reset_id = None
        self._update_combo_label()

    def _update_combo_label(self):
        try:
            if self._combo >= 2:
                self.combo_label.config(text=f"COMBO x{self._combo}")
                self.sfx.play("combo")
            else:
                self.combo_label.config(text="")
        except tk.TclError:
            pass

    # ---------- 成就 ----------
    def _check_achievements(self):
        hist = self.history
        g = self.game
        unlocked = set(g.get("achievements", []))
        new_ones = []
        total_bytes = hist.get("total_bytes", 0)
        total_files = hist.get("total_files", 0)

        checks = {
            "first":      total_bytes > 0,
            "files100":   total_files >= 100,
            "files1000":  total_files >= 1000,
            "gb1":        total_bytes >= 1024**3,
            "gb10":       total_bytes >= 10 * 1024**3,
            "gb100":      total_bytes >= 100 * 1024**3,
            "tb1":        total_bytes >= 1024**4,
            "dir":        bool(g.get("has_dir", False)),
            "big100m":    g.get("max_single", 0) >= 100 * 1024**2,
            "big1g":      g.get("max_single", 0) >= 1024**3,
            "combo10":    g.get("max_combo", 0) >= 10,
            "night_owl":  g.get("night_owl_trigger", False),
            "early_bird": g.get("early_bird_trigger", False),
            "weekend":    g.get("weekend_trigger", False),
            "clean_master": g.get("clean_master_trigger", False),
        }

        for aid, ok in checks.items():
            if ok and aid not in unlocked:
                unlocked.add(aid)
                new_ones.append(aid)
        if new_ones:
            g["achievements"] = sorted(unlocked)
            new_points = 0
            for aid in new_ones:
                a = self._get_ach(aid)
                new_points += a.get("points", 10) if a else 10
                self._queue_toast(aid)
            g["points"] = g.get("points", 0) + new_points
            save_game(g)
            self._refresh_points_badge()

    def _get_ach(self, aid):
        for a in ACHIEVEMENTS:
            if a["id"] == aid: return a
        return None

    def _queue_toast(self, ach_id):
        a = self._get_ach(ach_id)
        if not a: return
        self._toast_queue.append(a)
        if not self._toast_busy:
            self._show_next_toast()

    def _show_next_toast(self):
        if not self._toast_queue:
            self._toast_busy = False
            return
        self._toast_busy = True
        a = self._toast_queue.pop(0)

        try:
            toast = tk.Frame(self.root, bg=C("SURFACE_3"),
                             highlightbackground=C("ACCENT"),
                             highlightthickness=1)
            toast.place(relx=0.99, rely=0.05, anchor="ne", x=-8)

            reg(tk.Label(toast, text="🏆 成就解锁",
                          font=(FONT, 11, "bold")),
                bg="SURFACE_3", fg="ACCENT").pack(anchor="w", padx=16, pady=(10, 0))
            reg(tk.Label(toast, text=a["name"], font=(FONT, 12, "bold")),
                bg="SURFACE_3", fg="TEXT").pack(anchor="w", padx=16, pady=(4, 0))
            reg(tk.Label(toast, text=a["desc"], font=(FONT, 9)),
                bg="SURFACE_3", fg="MUTED").pack(anchor="w", padx=16, pady=(0, 4))
            pts = a.get("points", 10)
            reg(tk.Label(toast, text=f"⭐ 成就点数 +{pts}", font=(FONT, 10, "bold")),
                bg="SURFACE_3", fg="YELLOW").pack(anchor="w", padx=16, pady=(0, 10))


            self.sfx.play("achievement")
            self.root.after(2400, lambda: self._destroy_toast(toast))
        except Exception:
            self._toast_busy = False

    def _destroy_toast(self, toast):
        try: toast.destroy()
        except Exception: pass
        self.root.after(150, self._show_next_toast)

    def _build_achievements_list(self):
        if not hasattr(self, "shop_content"):
            return
        for w in self.shop_content.winfo_children():
            w.destroy()

        unlocked = set(self.game.get("achievements", []))

        # 标题
        reg(tk.Label(self.shop_content, text="🏆 成就徽章",
                      font=(FONT, 15, "bold")),
            bg="SURFACE", fg="TEXT").pack(anchor="w", padx=32, pady=(24, 4))
        reg(tk.Label(self.shop_content,
                      text=f"已解锁 {len(unlocked)} / {len(ACHIEVEMENTS)}",
                      font=(FONT, 10)),
            bg="SURFACE", fg="MUTED").pack(anchor="w", padx=32, pady=(0, 16))

        # 网格
        grid = tk.Frame(self.shop_content, bg=C("SURFACE"))
        reg(grid, bg="SURFACE")
        grid.pack(fill="x", padx=32, pady=(0, 24))
        cols = 3
        for c in range(cols):
            grid.grid_columnconfigure(c, weight=1, uniform="ach")

        # 逐个卡片
        for idx, a in enumerate(ACHIEVEMENTS):
            got = a["id"] in unlocked

            card = tk.Frame(grid,
                            bg=C("SURFACE_2") if got else C("SURFACE"),
                            highlightbackground=C("ACCENT") if got else C("BORDER"),
                            highlightthickness=1, bd=0)
            reg(card, bg="SURFACE_2" if got else "SURFACE")
            card.grid(row=idx // cols, column=idx % cols,
                      padx=6, pady=6, sticky="nsew")

            inner = tk.Frame(card, bg=C("SURFACE_2") if got else C("SURFACE"))
            reg(inner, bg="SURFACE_2" if got else "SURFACE")
            inner.pack(fill="both", expand=True, padx=16, pady=14)

            tier = ACHIEVEMENT_TIER.get(a["id"], "bronze")
            tier_info = TIER_INFO.get(tier, TIER_INFO["bronze"])
            icon = tier_info["icon"] if got else "🔒"

            head = tk.Frame(inner, bg=C("SURFACE_2") if got else C("SURFACE"))
            reg(head, bg="SURFACE_2" if got else "SURFACE")
            head.pack(anchor="w", fill="x")

            reg(tk.Label(head, text=icon, font=(FONT, 20)),
                bg="SURFACE_2" if got else "SURFACE").pack(side="left")

            name_col = tk.Frame(head, bg=C("SURFACE_2") if got else C("SURFACE"))
            reg(name_col, bg="SURFACE_2" if got else "SURFACE")
            name_col.pack(side="left", padx=(8, 0))

            reg(tk.Label(name_col, text=a["name"],
                          font=(FONT, 11, "bold")),
                bg="SURFACE_2" if got else "SURFACE",
                fg="TEXT" if got else "MUTED").pack(anchor="w")

            tl = tk.Label(name_col, text=f"{tier_info['name']}级",
                           font=(FONT, 8),
                           bg=C("SURFACE_2") if got else C("SURFACE"),
                           fg=tier_info["color"] if got else C("DIM"))
            tl.pack(anchor="w")

            reg(tk.Label(inner, text=a["desc"],
                          font=(FONT, 9), wraplength=200, justify="left"),
                bg="SURFACE_2" if got else "SURFACE",
                fg="TEXT_2" if got else "DIM").pack(anchor="w")

        # 让滚轮也能滚
        try:
            if hasattr(self, "_shop_wheel_cb"):
                self._bind_wheel_recursive(
                    self.shop_content, self._shop_wheel_cb)
        except Exception:
            pass

    def _build_shop_list(self):
        if not hasattr(self, "shop_content"): return
        for w in self.shop_content.winfo_children():
            w.destroy()

        # 更新点数显示
        try:
            pts = self.game.get("points", 0)
            self.shop_points_label.config(text=f"⭐ {pts}")
        except Exception:
            pass

        cat = self.shop_cat

        # ===== 成就：单独渲染 =====
        if cat == "ach":
            self._build_achievements_list()
            return

        # 每个分类的"免费默认项"，永远可切换回来
        FREE_THEMES = [
            {"id": "dark",  "name": "深色（原版）", "desc": "默认深色主题",
             "price": 0, "icon": "🌙", "is_default": True},
            {"id": "light", "name": "浅色（原版）", "desc": "默认浅色主题",
             "price": 0, "icon": "☀️", "is_default": True},
        ]
        FREE_SFX = [
            {"id": "default", "name": "默认音效", "desc": "系统默认提示音",
             "price": 0, "icon": "🔔", "is_default": True},
        ]
        FREE_TITLES = [
            {"id": "", "name": "无称号", "desc": "不显示称号徽章",
             "price": 0, "icon": "❌", "is_default": True},
        ]
        FREE_ANIM = [
            {"id": "none", "name": "无动画", "desc": "清空时不播放特效",
             "price": 0, "icon": "🚫", "is_default": True},
        ]

        if cat == "theme":
            items = FREE_THEMES + SHOP_THEMES
            owned_key = "unlocked_themes"
            active_key = "active_theme"
        elif cat == "sfx":
            items = FREE_SFX + SHOP_SFX
            owned_key = "unlocked_sfx"
            active_key = "active_sfx"
        elif cat == "title":
            items = FREE_TITLES + SHOP_TITLES
            owned_key = "unlocked_titles"
            active_key = "active_title"
        elif cat == "anim":
            items = FREE_ANIM + SHOP_ANIM
            owned_key = "unlocked_anim"
            active_key = "active_anim"
        else:
            return

        owned = set(self.game.get(owned_key, []))
        active = self.game.get(active_key, "")

        # 免费默认项：主题和音效有默认
        if cat == "theme":
            owned.update(["dark", "light"])
        elif cat == "sfx":
            owned.update(["default"])

        # 网格
        grid = tk.Frame(self.shop_content, bg=C("SURFACE"))
        reg(grid, bg="SURFACE")
        grid.pack(fill="x", padx=24, pady=(20, 12))
        cols = 3
        for c in range(cols):
            grid.grid_columnconfigure(c, weight=1, uniform="shop")

        for idx, item in enumerate(items):
            iid = item["id"]
            is_default = item.get("is_default", False)
            is_owned = is_default or (iid in owned)
            is_active = (iid == active)
            self._shop_item_card(grid, item, idx, cols,
                                 is_owned, is_active, cat,
                                 owned_key, active_key)

        # 抽奖宝箱（只在主题分类下显示，避免重复）
        if cat == "theme":
            self._build_lucky_box()
            
        # 递归绑定鼠标滚轮到所有子控件
        try:
            if hasattr(self, "_shop_wheel_cb"):
                self._bind_wheel_recursive(
                    self.shop_content, self._shop_wheel_cb)
        except Exception:
            pass
    def _shop_item_card(self, grid, item, idx, cols,
                        is_owned, is_active, cat,
                        owned_key, active_key):
        iid = item["id"]
        card = tk.Frame(grid, bg=C("SURFACE_2") if is_owned else C("SURFACE"),
                        highlightbackground=C("ACCENT") if is_active
                                              else (C("BORDER_LIGHT") if is_owned
                                                    else C("BORDER")),
                        highlightthickness=1 if not is_active else 2)
        reg(card, bg="SURFACE_2" if is_owned else "SURFACE")
        card.grid(row=idx // cols, column=idx % cols,
                  padx=8, pady=8, sticky="nsew")

        inner = tk.Frame(card, bg=C("SURFACE_2") if is_owned else C("SURFACE"))
        reg(inner, bg="SURFACE_2" if is_owned else "SURFACE")
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        # 图标
        reg(tk.Label(inner, text=item.get("icon", "🎁"),
                      font=(FONT, 28)),
            bg="SURFACE_2" if is_owned else "SURFACE").pack(anchor="w")

        # 名字
        reg(tk.Label(inner, text=item["name"], font=(FONT, 11, "bold")),
            bg="SURFACE_2" if is_owned else "SURFACE",
            fg="TEXT" if is_owned else "TEXT_2").pack(anchor="w", pady=(6, 2))

        # 描述
        reg(tk.Label(inner, text=item["desc"], font=(FONT, 9),
                      wraplength=180, justify="left"),
            bg="SURFACE_2" if is_owned else "SURFACE",
            fg="MUTED").pack(anchor="w")

        # 按钮区域
        btn_area = tk.Frame(inner, bg=C("SURFACE_2") if is_owned else C("SURFACE"))
        reg(btn_area, bg="SURFACE_2" if is_owned else "SURFACE")
        btn_area.pack(fill="x", pady=(10, 0))

        # 音效 / 动画分类：多一个"演示"按钮
        if cat in ("anim", "sfx"):
            demo_btn = tk.Label(btn_area, text="▶ 演示",
                                font=(FONT, 9, "bold"),
                                bg=C("SURFACE_3"), fg=C("TEXT"),
                                padx=10, pady=6, cursor="hand2")
            reg(demo_btn, bg="SURFACE_3", fg="TEXT")
            demo_btn.pack(side="left", padx=(0, 6))
            if cat == "anim":
                demo_btn.bind("<Button-1>",
                              lambda e, a=iid: self._play_clear_animation(a))
            else:
                demo_btn.bind("<Button-1>",
                              lambda e, p=iid: self._play_sfx_demo(p))

        side = "left" if cat in ("anim", "sfx") else None

        if is_active:
            btn = tk.Label(btn_area, text="✓ 使用中",
                           font=(FONT, 10, "bold"),
                           bg=C("GREEN"), fg=C("PRIMARY_FG"),
                           padx=14, pady=6)
            reg(btn, bg="GREEN", fg="PRIMARY_FG")
            btn.pack(side=side) if side else btn.pack()
        elif is_owned:
            btn = tk.Label(btn_area, text="启用",
                           font=(FONT, 10, "bold"),
                           bg=C("SURFACE_3"), fg=C("TEXT"),
                           padx=14, pady=6, cursor="hand2")
            reg(btn, bg="SURFACE_3", fg="TEXT")
            btn.pack(side=side) if side else btn.pack()
            btn.bind("<Button-1>", lambda e, i=iid, k=active_key:
                     self._activate_shop_item(i, k))
        else:
            price = item["price"]
            btn = tk.Label(btn_area, text=f"⭐ {price}",
                           font=(FONT, 10, "bold"),
                           bg=C("ACCENT"), fg=C("PRIMARY_FG"),
                           padx=14, pady=6, cursor="hand2")
            reg(btn, bg="ACCENT", fg="PRIMARY_FG")
            btn.pack(side=side) if side else btn.pack()
            btn.bind("<Button-1>", lambda e, i=item, k=owned_key, a=active_key:
                     self._buy_shop_item(i, k, a))

    def _buy_shop_item(self, item, owned_key, active_key):
        iid = item["id"]
        price = item["price"]
        pts = self.game.get("points", 0)
        if pts < price:
            self.sfx.play("error")
            try:
                messagebox.showwarning("积分不足",
                    f"购买「{item['name']}」需要 {price} 点。\n"
                    f"你当前只有 {pts} 点。\n\n"
                    f"继续清理文件可以获得更多成就点数。")
            except Exception:
                pass
            return
        try:
            ok = messagebox.askyesno("确认购买",
                f"购买「{item['name']}」？\n\n"
                f"花费：⭐ {price}\n"
                f"余额：⭐ {pts}  →  ⭐ {pts - price}")
        except Exception:
            ok = True
        if not ok:
            return

        self.game["points"] = pts - price
        lst = self.game.get(owned_key, [])
        if iid not in lst:
            lst.append(iid)
        self.game[owned_key] = lst
        self.game[active_key] = iid
        save_game(self.game)

        self.sfx.play("purchase")
        self._refresh_points_badge()
        self._apply_shop_activation(active_key, iid)
        self._build_shop_list()
        try:
            self.status.config(text=f"✅ 已购买并启用「{item['name']}」")
        except Exception:
            pass

    def _activate_shop_item(self, iid, active_key):
        self.game[active_key] = iid
        save_game(self.game)
        self._apply_shop_activation(active_key, iid)
        self._build_shop_list()
        try:
            self.status.config(text=f"已启用：{iid}")
        except Exception:
            pass

    def _apply_shop_activation(self, active_key, iid):
        """根据激活项类型，切换主题 / 音效 / 称号 / 动画。"""
        if active_key == "active_theme":
            self.settings["theme"] = iid
            save_settings(self.settings)
            apply_theme(iid, self.root)
            try:
                if hasattr(self, "theme_var"):
                    self.theme_var.set(iid)
                self._refresh_theme_btns()
                self._refresh_theme_quick()
            except Exception:
                pass
        elif active_key == "active_sfx":
            self.sfx.pack = iid
        elif active_key == "active_title":
            self._refresh_title_badge()
        # 称号和动画只在 UI 更新时读取，不需要立即做什么

    def _build_lucky_box(self):
        wrap = tk.Frame(self.shop_content, bg=C("SURFACE"))
        reg(wrap, bg="SURFACE")
        wrap.pack(fill="x", padx=24, pady=(0, 24))

        box = tk.Frame(wrap, bg=C("SURFACE_2"),
                       highlightbackground=C("YELLOW"),
                       highlightthickness=1)
        reg(box, bg="SURFACE_2", highlightbackground="YELLOW")
        box.pack(fill="x")

        inner = tk.Frame(box, bg=C("SURFACE_2"))
        reg(inner, bg="SURFACE_2")
        inner.pack(fill="x", padx=20, pady=18)

        left = tk.Frame(inner, bg=C("SURFACE_2")); reg(left, bg="SURFACE_2")
        left.pack(side="left", fill="x", expand=True)
        reg(tk.Label(left, text="🎲 抽奖宝箱", font=(FONT, 13, "bold")),
            bg="SURFACE_2", fg="YELLOW").pack(anchor="w")
        reg(tk.Label(left,
                      text=f"每次 {LUCKY_PRICE} 点，随机获得主题 / 音效 / 称号 / 动画 / 双倍积分卡",
                      font=(FONT, 9), wraplength=460, justify="left"),
            bg="SURFACE_2", fg="MUTED").pack(anchor="w", pady=(4, 0))
        cnt = self.game.get("lucky_count", 0)
        if cnt:
            reg(tk.Label(left, text=f"已抽过 {cnt} 次",
                          font=(FONT, 9)),
                bg="SURFACE_2", fg="DIM").pack(anchor="w", pady=(2, 0))

        btn = tk.Label(inner, text=f"🎲 抽一次  ⭐ {LUCKY_PRICE}",
                       font=(FONT, 11, "bold"),
                       bg=C("YELLOW"), fg=C("PRIMARY_FG"),
                       padx=22, pady=12, cursor="hand2")
        reg(btn, bg="YELLOW", fg="PRIMARY_FG")
        btn.pack(side="right")
        btn.bind("<Button-1>", lambda e: self._lucky_draw())

    def _lucky_draw(self):
        pts = self.game.get("points", 0)
        if pts < LUCKY_PRICE:
            self.sfx.play("error")
            try:
                messagebox.showwarning("积分不足",
                    f"抽奖需要 {LUCKY_PRICE} 点，你只有 {pts} 点。")
            except Exception:
                pass
            return

        self.game["points"] = pts - LUCKY_PRICE
        self.game["lucky_count"] = self.game.get("lucky_count", 0) + 1

        # 奖池
        pool = []
        for t in SHOP_THEMES:
            if t["id"] not in self.game.get("unlocked_themes", []):
                pool.append(("theme", t))
        for s in SHOP_SFX:
            if s["id"] not in self.game.get("unlocked_sfx", []):
                pool.append(("sfx", s))
        for ti in SHOP_TITLES:
            if ti["id"] not in self.game.get("unlocked_titles", []):
                pool.append(("title", ti))
        for a in SHOP_ANIM:
            if a["id"] not in self.game.get("unlocked_anim", []):
                pool.append(("anim", a))

        # 如果全解锁了，奖池加积分返还
        if not pool:
            bonus = random.randint(50, 300)
            self.game["points"] = self.game["points"] + bonus
            save_game(self.game)
            self._refresh_points_badge()
            self._build_shop_list()
            self.sfx.play("purchase")
            messagebox.showinfo("满仓抽奖",
                f"你已经拥有全部商品啦！\n\n"
                f"作为奖励，返还 ⭐ {bonus} 积分。")
            return

        # 抽：60% 拿东西，40% 拿积分
        r = random.random()
        if r < 0.6:
            cat, item = random.choice(pool)
            if cat == "theme":
                lst = self.game.get("unlocked_themes", [])
                if item["id"] not in lst: lst.append(item["id"])
                self.game["unlocked_themes"] = lst
            elif cat == "sfx":
                lst = self.game.get("unlocked_sfx", [])
                if item["id"] not in lst: lst.append(item["id"])
                self.game["unlocked_sfx"] = lst
            elif cat == "title":
                lst = self.game.get("unlocked_titles", [])
                if item["id"] not in lst: lst.append(item["id"])
                self.game["unlocked_titles"] = lst
            elif cat == "anim":
                lst = self.game.get("unlocked_anim", [])
                if item["id"] not in lst: lst.append(item["id"])
                self.game["unlocked_anim"] = lst

            save_game(self.game)
            self._refresh_points_badge()
            self._build_shop_list()
            self.sfx.play("purchase")
            messagebox.showinfo("🎉 恭喜中奖",
                f"你抽到了：{item['icon']} {item['name']}\n\n"
                f"{item['desc']}\n\n"
                f"已自动加入你的收藏，可在对应分类下启用。")
        else:
            bonus = random.choice([100, 150, 200, 300, 500])
            self.game["points"] = self.game["points"] + bonus
            save_game(self.game)
            self._refresh_points_badge()
            self._build_shop_list()
            self.sfx.play("purchase")
            messagebox.showinfo("再抽一次",
                f"这次没抽到商品，但返还了 ⭐ {bonus} 积分。\n"
                f"再来一次吧！")

    # ===== 明细 =====
    def _build_detail(self):
        p = self.page_dt
        to, ti = make_card(p, padx=18, pady=12)
        to.pack(fill="x")
        reg(tk.Label(ti, text="排序", font=(FONT, 10)),
            bg="SURFACE", fg="MUTED").pack(side="left")
        combo = ttk.Combobox(ti, textvariable=self.sort_key, state="readonly",
                              width=12,
                              values=["按时间倒序","按大小倒序","按名称","按类型"],
                              style="Modern.TCombobox", font=(FONT, 10))
        combo.pack(side="left", padx=(8, 20))
        combo.bind("<<ComboboxSelected>>", lambda e: self._reload_table())
        reg(tk.Label(ti, text="筛选", font=(FONT, 10)),
            bg="SURFACE", fg="MUTED").pack(side="left")
        ew = tk.Frame(ti, bg=C("SURFACE_2"),
                      highlightbackground=C("BORDER_LIGHT"),
                      highlightthickness=1)
        reg(ew, bg="SURFACE_2", highlightbackground="BORDER_LIGHT")
        ew.pack(side="left", padx=(8, 0))
        e = tk.Entry(ew, textvariable=self.filter_var, width=32,
                     font=(FONT, 10), bg=C("SURFACE_2"), fg=C("TEXT"),
                     insertbackground=C("ACCENT"), bd=0, relief="flat")
        reg(e, bg="SURFACE_2", fg="TEXT", insertbackground="ACCENT")
        e.pack(padx=10, pady=6)
        e.bind("<KeyRelease>", lambda ev: self._reload_table())
        self.table_info = tk.Label(ti, text="", font=(FONT, 9),
                                     bg=C("SURFACE"), fg=C("DIM"))
        reg(self.table_info, bg="SURFACE", fg="DIM")
        self.table_info.pack(side="right")

        tbo, tbi = make_card(p, padx=1, pady=1)
        tbo.pack(fill="both", expand=True, pady=(16, 0))
        cols = ("filename","ext","size","time","orig")
        self.tree = ttk.Treeview(tbi, columns=cols, show="headings",
                                   style="Recycle.Treeview")
        self.tree.heading("filename", text="文件名", anchor="w",
                          command=lambda: self._sort_by("filename"))
        self.tree.heading("ext", text="类型", anchor="w",
                          command=lambda: self._sort_by("ext"))
        self.tree.heading("size", text="大小", anchor="e",
                          command=lambda: self._sort_by("size"))
        self.tree.heading("time", text="删除时间", anchor="w",
                          command=lambda: self._sort_by("time"))
        self.tree.heading("orig", text="原始路径", anchor="w",
                          command=lambda: self._sort_by("orig"))
        # 默认列宽
        default_widths = {
            "filename": 260, "ext": 110, "size": 210,
            "time": 170, "orig": 380,
        }
        saved_widths = self.settings.get("table_column_widths") or {}
        def _w(col):
            try:
                return int(saved_widths.get(col, default_widths[col]))
            except (TypeError, ValueError):
                return default_widths[col]
        self.tree.column("filename", width=_w("filename"), anchor="w", stretch=False)
        self.tree.column("ext",      width=_w("ext"),      anchor="w", stretch=False)
        self.tree.column("size",     width=_w("size"),     anchor="e", stretch=False)
        self.tree.column("time",     width=_w("time"),     anchor="w", stretch=False)
        self.tree.column("orig",     width=_w("orig"),     anchor="w", stretch=True)

        # 监听列宽拖动，松手后延迟保存
        self.tree.bind("<ButtonRelease-1>", self._on_column_resize)
        vsb = ttk.Scrollbar(tbi, orient="vertical", command=self.tree.yview,
                             style="Modern.Vertical.TScrollbar")
        hsb = ttk.Scrollbar(tbi, orient="horizontal", command=self.tree.xview,
                             style="Modern.Horizontal.TScrollbar")
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tbi.grid_rowconfigure(0, weight=1)
        tbi.grid_columnconfigure(0, weight=1)
        self._refresh_tree_tags()
        on_theme_change(self._refresh_tree_tags)
    def _on_column_resize(self, event=None):
        if getattr(self, "_col_save_id", None):
            try: self.root.after_cancel(self._col_save_id)
            except Exception: pass
        self._col_save_id = self.root.after(400, self._save_column_widths)

    def _save_column_widths(self):
        self._col_save_id = None
        if not hasattr(self, "tree"): return
        try:
            widths = {}
            for col in ("filename", "ext", "size", "time", "orig"):
                widths[col] = int(self.tree.column(col, "width"))
            self.settings["table_column_widths"] = widths
            save_settings(self.settings)
        except Exception:
            pass

    def _refresh_tree_tags(self):
        if not hasattr(self, "tree"): return
        try:
            self.tree.tag_configure("odd", background=C("ROW_ODD"))
            self.tree.tag_configure("even", background=C("ROW_EVEN"))
        except tk.TclError: pass

    def _sort_by(self, col):
        cur_col = self.heading_sort["column"]
        cur_dir = self.heading_sort["dir"]
        if cur_col == col:
            new_dir = "desc" if cur_dir == "asc" else "asc"
        else:
            new_dir = "desc"
        self.heading_sort["column"] = col
        self.heading_sort["dir"] = new_dir
        self._update_heading_arrows()
        self._reload_table()

    def _update_heading_arrows(self):
        base = {"filename": "文件名", "ext": "类型", "size": "大小",
                "time": "删除时间", "orig": "原始路径"}
        anchors = {"filename": "w", "ext": "w", "size": "e",
                   "time": "w", "orig": "w"}
        cur_col = self.heading_sort["column"]; cur_dir = self.heading_sort["dir"]
        for col, txt in base.items():
            if col == cur_col:
                arrow = " ↑" if cur_dir == "asc" else " ↓"
                self.tree.heading(col, text=txt + arrow, anchor=anchors[col])
            else:
                self.tree.heading(col, text=txt, anchor=anchors[col])
    # ===== 商城 =====
    def _build_shop_page(self):
        p = self.page_shop

        # 顶部：标题 + 点数
        head_outer, head_inner = make_card(p, padx=24, pady=16)
        head_outer.pack(fill="x")

        head_row = tk.Frame(head_inner, bg=C("SURFACE")); reg(head_row, bg="SURFACE")
        head_row.pack(fill="x")
        reg(tk.Label(head_row, text="🎁 积分商城", font=(FONT, 16, "bold")),
            bg="SURFACE", fg="TEXT").pack(side="left")
        self.shop_points_label = tk.Label(head_row, text="⭐ 0",
                                            font=(MONO, 14, "bold"),
                                            bg=C("SURFACE"), fg=C("YELLOW"))
        reg(self.shop_points_label, bg="SURFACE", fg="YELLOW")
        self.shop_points_label.pack(side="right")
        reg(tk.Label(head_row, text="当前积分：", font=(FONT, 10)),
            bg="SURFACE", fg="MUTED").pack(side="right", padx=(0, 4))

        # 分类 tab
        tab_row = tk.Frame(head_inner, bg=C("SURFACE")); reg(tab_row, bg="SURFACE")
        tab_row.pack(fill="x", pady=(14, 0))
        self.shop_cat = "theme"
        self._shop_cat_btns = {}
        for key, label in [("theme", "🎨 主题"),
                           ("sfx",   "🔊 音效包"),
                           ("title", "🏅 称号"),
                           ("anim",  "✨ 清空动画"),
                           ("ach",   "🏆 成就")]:
            b = tk.Label(tab_row, text=label, font=(FONT, 10, "bold"),
                         bg=C("SURFACE_2"), fg=C("MUTED"),
                         padx=16, pady=8, cursor="hand2")
            reg(b, bg="SURFACE_2", fg="MUTED")
            b.pack(side="left", padx=(0, 8))
            b.bind("<Button-1>", lambda e, k=key: self._switch_shop_cat(k))
            self._shop_cat_btns[key] = b
        self._refresh_shop_cat_btns()

        # 内容区（可滚动）
        body_outer, body_inner = make_card(p, padx=0, pady=0)
        body_outer.pack(fill="both", expand=True, pady=(16, 0))

        canvas = tk.Canvas(body_inner, bg=C("SURFACE"), bd=0, highlightthickness=0)
        reg(canvas, bg="SURFACE")
        vsb = make_scrollbar(body_inner, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.shop_content = tk.Frame(canvas, bg=C("SURFACE"))
        reg(self.shop_content, bg="SURFACE")
        win = canvas.create_window((0, 0), window=self.shop_content, anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfigure(win, width=e.width))
        self.shop_content.bind("<Configure>",
                               lambda e: canvas.configure(
                                   scrollregion=canvas.bbox("all")))
        self._shop_canvas = canvas

        # 滚轮
        def _wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _wheel)
        self.shop_content.bind("<MouseWheel>", _wheel)
        self._shop_wheel_cb = _wheel

    def _switch_shop_cat(self, key):
        self.shop_cat = key
        self._refresh_shop_cat_btns()
        self._build_shop_list()

    def _refresh_shop_cat_btns(self):
        if not hasattr(self, "_shop_cat_btns"): return
        for k, b in self._shop_cat_btns.items():
            try:
                if k == self.shop_cat:
                    b.config(bg=C("ACCENT"), fg=C("PRIMARY_FG"))
                else:
                    b.config(bg=C("SURFACE_2"), fg=C("MUTED"))
            except tk.TclError:
                pass
    # ===== 关于 =====
    def _build_about_page(self):
        p = self.page_about

        # 主卡片
        outer, inner = make_card(p, padx=40, pady=32)
        outer.pack(fill="both", expand=True)

        # 顶部：图标 + 软件名 + 版本号
        head = tk.Frame(inner, bg=C("SURFACE")); reg(head, bg="SURFACE")
        head.pack(fill="x")

        reg(tk.Label(head, text="🗑", font=(FONT, 48)),
            bg="SURFACE", fg="ACCENT").pack(side="left", pady=(0, 8))

        tb = tk.Frame(head, bg=C("SURFACE")); reg(tb, bg="SURFACE")
        tb.pack(side="left", padx=(20, 0), pady=(10, 0))

        reg(tk.Label(tb, text="回收站统计", font=(FONT, 22, "bold")),
            bg="SURFACE", fg="TEXT").pack(anchor="w")

        ver_row = tk.Frame(tb, bg=C("SURFACE")); reg(ver_row, bg="SURFACE")
        ver_row.pack(anchor="w", pady=(4, 0))
        reg(tk.Label(ver_row, text="版本", font=(FONT, 10)),
            bg="SURFACE", fg="MUTED").pack(side="left")
        ver_badge = tk.Label(ver_row, text="0.1.1",
                              font=(MONO, 11, "bold"),
                              bg=C("ACCENT"), fg=C("PRIMARY_FG"),
                              padx=10, pady=1)
        reg(ver_badge, bg="ACCENT", fg="PRIMARY_FG")
        ver_badge.pack(side="left", padx=(8, 0))
        reg(tk.Label(ver_row, text="  Recycle Bin Statistics",
                      font=(FONT, 9)),
            bg="SURFACE", fg="DIM").pack(side="left")

        # 分隔线
        self._sep(inner)

        # 软件简介
        reg(tk.Label(inner, text="📖 软件简介", font=(FONT, 12, "bold")),
            bg="SURFACE", fg="TEXT").pack(anchor="w", pady=(16, 6))
        reg(tk.Label(inner,
                      text="这是一款为 Windows 回收站打造的字节统计工具\n"
                           "它可以实时监控回收站的大小、文件数量和类型分布\n"
                           "让你清空回收站变成一种享受",
                      font=(FONT, 10), justify="left", wraplength=700),
            bg="SURFACE", fg="TEXT_2").pack(anchor="w", pady=(0, 12))

        # 分隔线
        self._sep(inner)

        # 链接区域
        link_row = tk.Frame(inner, bg=C("SURFACE")); reg(link_row, bg="SURFACE")
        link_row.pack(anchor="w", pady=(16, 12))

        # B站
        self._about_link_btn(link_row, "哔哩哔哩",
                              "https://space.bilibili.com/3493129137163081",
                              "点击跳转到 B 站主页",
                              icon_keyword="bilibili")
        # GitHub
        self._about_link_btn(link_row, "GitHub",
                              "https://github.com/xiaosurongjia/recycle-bin-statistics",
                              "点击跳转到 GitHub 仓库",
                              icon_keyword="github")

        # 分隔线
        self._sep(inner)

        # 底部版权
        reg(tk.Label(inner,
                      text="\n© 2026 回收站统计 · 使用Python制作\n"
                           "本项目仅供学习交流使用",
                      font=(FONT, 9), justify="center"),
            bg="SURFACE", fg="DIM").pack(anchor="center", pady=(20, 0))

    def _about_link_btn(self, parent, text, url, tip, icon_keyword=None):
        """在关于页创建一个可点击的链接按钮（带图标）"""
        wrap = tk.Frame(parent, bg=C("SURFACE_2"),
                        highlightbackground=C("BORDER_LIGHT"),
                        highlightthickness=1)
        reg(wrap, bg="SURFACE_2", highlightbackground="BORDER_LIGHT")
        wrap.pack(side="left", padx=(0, 24))

        # 图标
        if icon_keyword:
            img = self._load_icon(icon_keyword, size=(64, 64))
            if img is not None:
                icon_lbl = tk.Label(wrap, image=img, bg=C("SURFACE_2"),
                                    cursor="hand2")
                reg(icon_lbl, bg="SURFACE_2")
                icon_lbl.image = img
                if not hasattr(self, "_about_icon_photos"):
                    self._about_icon_photos = []
                self._about_icon_photos.append(img)
                icon_lbl.pack(pady=(24, 8))
                icon_lbl.bind("<Button-1>", lambda e: webbrowser.open_new_tab(url))

        btn = tk.Label(wrap, text=text, font=(FONT, 14, "bold"),
                        bg=C("SURFACE_2"), fg=C("ACCENT"),
                        padx=48, pady=18, cursor="hand2")
        reg(btn, bg="SURFACE_2", fg="ACCENT")
        btn.pack()

        tip_lbl = tk.Label(wrap, text=tip, font=(FONT, 9),
                            bg=C("SURFACE_2"), fg=C("DIM"))
        reg(tip_lbl, bg="SURFACE_2", fg="DIM")
        tip_lbl.pack(pady=(0, 14))

        def _open(event=None):
            try:
                webbrowser.open_new_tab(url)
            except Exception:
                pass

        def _enter(e):
            btn.config(fg=C("TEXT"))
        def _leave(e):
            btn.config(fg=C("ACCENT"))

        btn.bind("<Button-1>", _open)
        btn.bind("<Enter>", _enter)
        btn.bind("<Leave>", _leave)

    # ===== 设置 =====
    def _build_settings(self):
        p = self.page_st
        o, i = make_card(p, padx=0, pady=0)
        o.pack(fill="both", expand=True)
        canvas = tk.Canvas(i, bg=C("SURFACE"), bd=0, highlightthickness=0)
        reg(canvas, bg="SURFACE")
        vsb = ttk.Scrollbar(i, orient="vertical", command=canvas.yview,
                             style="Modern.Vertical.TScrollbar")
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.settings_content = tk.Frame(canvas, bg=C("SURFACE"))
        reg(self.settings_content, bg="SURFACE")
        win = canvas.create_window((0, 0), window=self.settings_content, anchor="nw")
        def _cfg(e): canvas.configure(scrollregion=canvas.bbox("all"))
        def _cw(e): canvas.itemconfigure(win, width=e.width)
        self.settings_content.bind("<Configure>", _cfg)
        canvas.bind("<Configure>", _cw)
        def _wheel(e): canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        def bind_wheel(w):
            w.bind("<MouseWheel>", _wheel)
            for c in w.winfo_children(): bind_wheel(c)

        # 外观
        g = self._group("外观")
        self._row(g, "主题模式", "深色 / 浅色切换",
                  lambda p: self._theme_selector(p))
        self._row(g, "明细字号", "文件列表字体大小",
                  lambda p: self._dropdown(p,
                      ["10","11","12","13","14","15","16"],
                      self.settings.get("table_font_size", 12),
                      lambda v: self._change("table_font_size", v)))
        self._row(g, "表头字号", "表格顶部标题字体大小",
                  lambda p: self._dropdown(p,
                      ["9","10","11","12","13","14"],
                      self.settings.get("heading_font_size", 11),
                      lambda v: self._change("heading_font_size", v)))
        self._row(g, "明细行高", "每行的高度，字大要调大",
                  lambda p: self._dropdown(p,
                      ["28","32","36","40","44","48","52","56"],
                      self.settings.get("table_row_height", 40),
                      lambda v: self._change("table_row_height", v)))
        self._row(g, "界面动效", "按钮渐变、页面滑入、数字滚动、伤害数字",
                  lambda p: self._toggle(p, "motion_enabled"))
        self._sep(g)

        # 游戏
        g = self._group("游戏化", "等级、成就、连击、音效")
        self._row(g, "音效开关", "删除 / 升级 / 成就时播放提示音",
                  lambda p: self._toggle(p, "sfx_enabled"))
        self._row(g, "系统托盘", "关闭窗口时缩到右下角继续运行",
                  lambda p: self._toggle(p, "tray_enabled"))
        self._sep(g)

        # 扫描
        g = self._group("扫描")
        interval_map = {
            "关闭": 0, "30 秒": 30, "1 分钟": 60, "2 分钟": 120,
            "5 分钟": 300, "10 分钟": 600, "30 分钟": 1800,
        }
        cur_int = self.settings.get("scan_interval", 60)
        cur_label = "1 分钟"
        for k, v in interval_map.items():
            if v == cur_int: cur_label = k; break
        self._row(g, "自动刷新", "多久扫描一次回收站",
                  lambda p: self._dropdown(p, list(interval_map.keys()),
                      cur_label,
                      lambda v: self._change("scan_interval", interval_map[v])))
        self._row(g, "启动时自动扫描", "打开程序后立即扫一次",
                  lambda p: self._toggle(p, "startup_scan"))
        self._row(g, "明细最多显示", "表格最多渲染的条数",
                  lambda p: self._dropdown(p,
                      ["500","1000","3000","5000","10000","全部"],
                      str(self.settings.get("max_table_rows", 5000)),
                      lambda v: self._change("max_table_rows",
                          0 if v == "全部" else int(v))))
        self._sep(g)

        # 展示
        g = self._group("展示")
        self._row(g, "类型 Top N", "概览页类型分布显示多少项",
                  lambda p: self._dropdown(p,
                      ["5","10","15","20"],
                      str(self.settings.get("type_top_n", 10)),
                      lambda v: self._change("type_top_n", int(v))))
        self._row(g, "趋势图天数", "最近多少天的删除趋势",
                  lambda p: self._dropdown(p,
                      ["3","5","7","14","30"],
                      str(self.settings.get("chart_days", 7)),
                      lambda v: self._change("chart_days", int(v))))
        self._sep(g)

        # 过滤
        g = self._group("过滤", "过滤掉你不关心的记录，节省账本空间")
        self._row(g, "忽略小于（字节）", "例如 1024 表示不记录 1KB 以下的小文件",
                  lambda p: self._entry(p, "min_file_size", 14))
        self._row(g, "忽略扩展名", "逗号分隔，例如 .tmp, .log, .bak",
                  lambda p: self._entry(p, "ignore_exts", 24))
        self._sep(g)
        # 调试
        g = self._group("调试", "非正常操作，会影响游戏平衡")
        debug_row = tk.Frame(g, bg=C("SURFACE")); reg(debug_row, bg="SURFACE")
        debug_row.pack(fill="x", pady=(8, 4))

        b_add = tk.Label(debug_row, text="＋1000 积分",
                         font=(FONT, 10, "bold"),
                         bg=C("GREEN"), fg=C("PRIMARY_FG"),
                         padx=16, pady=8, cursor="hand2")
        reg(b_add, bg="GREEN", fg="PRIMARY_FG")
        b_add.pack(side="left")
        b_add.bind("<Button-1>", lambda e: self._cheat_add_points())

        b_clr = tk.Label(debug_row, text="积分清零",
                         font=(FONT, 10, "bold"),
                         bg=C("SURFACE_2"), fg=C("RED"),
                         padx=16, pady=8, cursor="hand2")
        reg(b_clr, bg="SURFACE_2", fg="RED")
        b_clr.pack(side="left", padx=(8, 0))
        b_clr.bind("<Button-1>", lambda e: self._cheat_clear_points())
        b_purge = tk.Label(debug_row, text="清空已购",
                           font=(FONT, 10, "bold"),
                           bg=C("SURFACE_2"), fg=C("RED"),
                           padx=16, pady=8, cursor="hand2")
        reg(b_purge, bg="SURFACE_2", fg="RED")
        b_purge.pack(side="left", padx=(8, 0))
        b_purge.bind("<Button-1>", lambda e: self._cheat_clear_purchases())
        self._sep(g)

        # 数据
        g = self._group("数据")
        path_row = tk.Frame(g, bg=C("SURFACE")); reg(path_row, bg="SURFACE")
        path_row.pack(fill="x", pady=6)
        reg(tk.Label(path_row, text="账本位置", font=(FONT, 10, "bold")),
            bg="SURFACE", fg="TEXT").pack(anchor="w")
        pl = tk.Label(path_row, text=HISTORY_FILE, font=(MONO, 9),
                      bg=C("SURFACE"), fg=C("MUTED"), anchor="w",
                      wraplength=760, justify="left")
        reg(pl, bg="SURFACE", fg="MUTED")
        pl.pack(anchor="w")

        btns = tk.Frame(g, bg=C("SURFACE")); reg(btns, bg="SURFACE")
        btns.pack(fill="x", pady=(8, 4))
        self._text_btn(btns, "打开账本文件夹", self.open_ledger_folder).pack(side="left")
        self._text_btn(btns, "导出为 CSV", self.export_csv).pack(side="left", padx=(8, 0))
        self._text_btn(btns, "重置历史", self.reset_history, danger=True).pack(side="left", padx=(8, 0))
        self._text_btn(btns, "重置成就", self.reset_game, danger=True).pack(side="left", padx=(8, 0))

        self.settings_content.update_idletasks()
        bind_wheel(self.settings_content)

    def _group(self, title, hint=""):
        g = tk.Frame(self.settings_content, bg=C("SURFACE")); reg(g, bg="SURFACE")
        g.pack(fill="x", padx=32, pady=(22, 0))
        head = tk.Frame(g, bg=C("SURFACE")); reg(head, bg="SURFACE")
        head.pack(fill="x", pady=(0, 4))
        reg(tk.Label(head, text=title, font=(FONT, 12, "bold")),
            bg="SURFACE", fg="TEXT").pack(side="left")
        if hint:
            reg(tk.Label(head, text="  · " + hint, font=(FONT, 9)),
                bg="SURFACE", fg="DIM").pack(side="left", pady=(2, 0))
        body = tk.Frame(g, bg=C("SURFACE")); reg(body, bg="SURFACE")
        body.pack(fill="x", pady=(4, 0))
        return body

    def _sep(self, parent):
        f = tk.Frame(parent, bg=C("BORDER"), height=1); reg(f, bg="BORDER")
        f.pack(fill="x", pady=(16, 0))

    def _row(self, parent, title, subtitle, builder):
        r = tk.Frame(parent, bg=C("SURFACE")); reg(r, bg="SURFACE")
        r.pack(fill="x", pady=8)
        l = tk.Frame(r, bg=C("SURFACE")); reg(l, bg="SURFACE")
        l.pack(side="left", fill="x", expand=True)
        reg(tk.Label(l, text=title, font=(FONT, 10, "bold"), anchor="w"),
            bg="SURFACE", fg="TEXT").pack(anchor="w")
        if subtitle:
            reg(tk.Label(l, text=subtitle, font=(FONT, 9), anchor="w"),
                bg="SURFACE", fg="MUTED").pack(anchor="w", pady=(1, 0))
        rt = tk.Frame(r, bg=C("SURFACE")); reg(rt, bg="SURFACE")
        rt.pack(side="right")
        builder(rt)

    def _theme_selector(self, parent):
        wrap = tk.Frame(parent, bg=C("SURFACE_2"),
                        highlightbackground=C("BORDER_LIGHT"),
                        highlightthickness=1)
        reg(wrap, bg="SURFACE_2", highlightbackground="BORDER_LIGHT")
        wrap.pack()
        self.theme_var = tk.StringVar(value=self.settings.get("theme", "dark"))
        self._theme_btns = {}
        for key, label in [("dark", "☾ 深色"), ("light", "☀ 浅色")]:
            b = tk.Label(wrap, text=label, font=(FONT, 10, "bold"),
                         padx=14, pady=7, cursor="hand2")
            b.pack(side="left", padx=2, pady=2)
            b.bind("<Button-1>", lambda e, k=key: self._set_theme(k))
            self._theme_btns[key] = b
        self._refresh_theme_btns()
        on_theme_change(self._refresh_theme_btns)

    def _refresh_theme_btns(self):
        if not hasattr(self, "_theme_btns"): return
        cur = self.settings.get("theme", "dark")
        for k, b in self._theme_btns.items():
            try:
                if k == cur: b.config(bg=C("ACCENT"), fg=C("PRIMARY_FG"))
                else: b.config(bg=C("SURFACE_2"), fg=C("MUTED"))
            except tk.TclError: pass

    def _set_theme(self, name):
        self.settings["theme"] = name
        self.game["active_theme"] = name
        save_settings(self.settings)
        save_game(self.game)
        apply_theme(name, self.root)
        self._refresh_theme_quick()
        self._refresh_theme_btns()

    def _dropdown(self, parent, values, current, on_change):
        var = tk.StringVar(value=str(current))
        cb = ttk.Combobox(parent, textvariable=var, values=values,
                          state="readonly", width=12,
                          style="Modern.TCombobox", font=(FONT, 10))
        cb.pack()
        cb.bind("<<ComboboxSelected>>", lambda e: on_change(var.get()))

    def _toggle(self, parent, key):
        v = tk.BooleanVar(value=bool(self.settings.get(key, False)))
        Toggle(parent, v, bg_role="SURFACE",
               command=lambda: self._change(key, v.get())).pack()

    def _entry(self, parent, key, width):
        wrap = tk.Frame(parent, bg=C("SURFACE_2"),
                        highlightbackground=C("BORDER_LIGHT"),
                        highlightthickness=1)
        reg(wrap, bg="SURFACE_2", highlightbackground="BORDER_LIGHT")
        wrap.pack()
        var = tk.StringVar(value=str(self.settings.get(key, "")))
        e = tk.Entry(wrap, textvariable=var, width=width,
                     font=(FONT, 10), bg=C("SURFACE_2"), fg=C("TEXT"),
                     insertbackground=C("ACCENT"), bd=0, relief="flat")
        reg(e, bg="SURFACE_2", fg="TEXT", insertbackground="ACCENT")
        e.pack(padx=10, pady=6)
        def _commit(ev=None): self._change(key, var.get())
        e.bind("<Return>", _commit); e.bind("<FocusOut>", _commit)

    def _text_btn(self, parent, text, cmd, danger=False):
        fg_role = "RED" if danger else "TEXT_2"
        b = tk.Label(parent, text=text, font=(FONT, 10),
                     bg=C("SURFACE_2"), fg=C(fg_role),
                     padx=16, pady=8, cursor="hand2", bd=0, highlightthickness=0)
        reg(b, bg="SURFACE_2", fg=fg_role)
        b.bind("<Button-1>", lambda e: cmd())
        def _en(e):
            b.config(bg=C("SURFACE_3"),
                     fg=C("RED") if danger else C("TEXT"))
        def _lv(e):
            b.config(bg=C("SURFACE_2"), fg=C(fg_role))
        b.bind("<Enter>", _en); b.bind("<Leave>", _lv)
        return b

    def _change(self, key, value):
        if key in ("table_font_size","heading_font_size","table_row_height",
                   "type_top_n","scan_interval","max_table_rows",
                   "min_file_size","chart_days"):
            try: value = int(value)
            except (TypeError, ValueError): return
        elif key in ("startup_scan","motion_enabled","sfx_enabled",
                      "neon_mode","tray_enabled"):
            value = bool(value)
        elif key == "ignore_exts":
            value = str(value).strip()

        self.settings[key] = value
        save_settings(self.settings)

        if key in ("table_font_size","heading_font_size","table_row_height"):
            setup_ttk_styles(); self._reload_table()
        elif key == "scan_interval":
            if self.auto_var.get(): self._schedule_auto()
        elif key in ("min_file_size","ignore_exts"):
            self.refresh()
        elif key == "type_top_n":
            if hasattr(self, "_last_hist"):
                self._refresh_ext_chart(self._last_hist)
        elif key == "chart_days":
            self._draw_chart()
        elif key == "sfx_enabled":
            self.sfx.enabled = value
        elif key == "tray_enabled":
            if value and HAS_TRAY and self.tray_icon is None:
                self._setup_tray()
            elif not value and self.tray_icon is not None:
                try: self.tray_icon.stop()
                except Exception: pass
                self.tray_icon = None

        self.status.config(text=f"已保存设置：{key}")

    # ---------- 状态栏 ----------
    def _build_status(self):
        bar = tk.Frame(self.root, bg=C("BG"), height=28); reg(bar, bg="BG")
        bar.pack(fill="x", padx=32, pady=(4, 12)); bar.pack_propagate(False)
        self.spinner = tk.Canvas(bar, width=14, height=14,
                                   bg=C("BG"), bd=0, highlightthickness=0)
        reg(self.spinner, bg="BG")
        self.spinner.pack(side="left", pady=(4, 0))
        self._draw_spinner(0)
        self.status = tk.Label(bar, text="准备就绪", font=(FONT, 9),
                                bg=C("BG"), fg=C("DIM"))
        reg(self.status, bg="BG", fg="DIM")
        self.status.pack(side="left", padx=(6, 0), pady=(4, 0))
        self.auto_btn = tk.Label(bar, text="● 自动刷新",
            font=(FONT, 9), bg=C("BG"), fg=C("GREEN"), cursor="hand2")
        reg(self.auto_btn, bg="BG", fg="GREEN")
        self.auto_btn.pack(side="right", pady=(4, 0))
        self.auto_btn.bind("<Button-1>", lambda e: self._toggle_auto_ui())

    def _build_social_icons(self, parent):
        """把 bilibili / github 图标放到状态栏右侧（不区分大小写）。"""
        # 改成你自己的链接
        links = [
            ("github",   "https://github.com/xiaosurongjia/recycle-bin-statistics"),
            ("bilibili", "https://space.bilibili.com/3493129137163081"),
        ]
        for keyword, url in links:
            img = self._load_icon(keyword, size=(20, 20))
            if img is None:
                # 找不到就退化成文字
                lbl = tk.Label(parent, text=keyword,
                               font=(FONT, 9), bg=C("BG"), fg=C("MUTED"),
                               cursor="hand2")
                reg(lbl, bg="BG", fg="MUTED")
            else:
                lbl = tk.Label(parent, image=img, bg=C("BG"),
                               cursor="hand2", bd=0, highlightthickness=0)
                reg(lbl, bg="BG")
                lbl.image = img
                self._icon_photos.append(img)

            lbl.pack(side="right", padx=(6, 0), pady=(2, 0))
            lbl.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
            lbl.bind("<Enter>", lambda e, w=lbl: self._safe_bg(w, C("SURFACE_3")))
            lbl.bind("<Leave>", lambda e, w=lbl: self._safe_bg(w, C("BG")))

    def _load_icon(self, keyword, size=(20, 20)):
        """在脚本所在目录里找名字含 keyword 的 png（不区分大小写）。"""
        path = None
        try:
            for fname in os.listdir(SCRIPT_DIR):
                low = fname.lower()
                if low.endswith(".png") and keyword in low:
                    path = os.path.join(SCRIPT_DIR, fname)
                    break
        except Exception:
            pass
        if not path or not os.path.exists(path):
            print(f"[图标] 没找到含 '{keyword}' 的 png，目录：{SCRIPT_DIR}")
            return None
        # 优先用 PIL
        try:
            from PIL import Image, ImageTk
            img = Image.open(path).convert("RGBA")
            img = img.resize(size, Image.LANCZOS)
            print(f"[图标] 已加载：{path}")
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"[图标] PIL 加载失败：{e}")
        # 退化到 tk
        try:
            return tk.PhotoImage(file=path)
        except Exception as e:
            print(f"[图标] tk 加载失败：{e}")
            return None

    def _draw_spinner(self, angle):
        try:
            self.spinner.delete("all")
            w, h = 14, 14
            if self._spinner_id is None:
                self.spinner.create_oval(5, 5, 9, 9, fill=C("GREEN"), outline="")
            else:
                self.spinner.create_arc(1, 1, w-1, h-1,
                    start=angle, extent=270, style="arc",
                    outline=C("ACCENT"), width=2)
        except tk.TclError: pass

    def _start_spinner(self):
        if self._spinner_id: return
        def tick():
            if not self._spinner_id: return
            self._spinner_angle = (self._spinner_angle + 30) % 360
            self._draw_spinner(self._spinner_angle)
            self._spinner_id = self.root.after(50, tick)
        self._spinner_id = self.root.after(1, tick)

    def _stop_spinner(self):
        if self._spinner_id:
            self.root.after_cancel(self._spinner_id)
            self._spinner_id = None
        self._draw_spinner(0)

    def _toggle_auto_ui(self):
        self.auto_var.set(not self.auto_var.get())
        if self.auto_var.get():
            self.auto_btn.config(text="● 自动刷新", fg=C("GREEN"))
            self._schedule_auto()
        else:
            self.auto_btn.config(text="○ 自动刷新", fg=C("DIM"))
            self._cancel_auto()
    def _cheat_add_points(self):
        self.game["points"] = self.game.get("points", 0) + 1000
        save_game(self.game)
        self._refresh_points_badge()
        try:
            if hasattr(self, "shop_points_label"):
                self.shop_points_label.config(text=f"⭐ {self.game['points']}")
        except Exception:
            pass
        try:
            self.status.config(text=f"已 +1000 积分，当前 {self.game['points']}")
        except Exception:
            pass

    def _cheat_clear_points(self):
        try:
            ok = messagebox.askyesno("确认清零",
                "确定要把积分清零吗？\n\n已购买的商品不会被收回。")
        except Exception:
            ok = True
        if not ok:
            return
        self.game["points"] = 0
        save_game(self.game)
        self._refresh_points_badge()
        try:
            if hasattr(self, "shop_points_label"):
                self.shop_points_label.config(text="⭐ 0")
        except Exception:
            pass
        try:
            self.status.config(text="积分已清零")
        except Exception:
            pass
    def _cheat_clear_purchases(self):
        try:
            ok = messagebox.askyesno("确认清空已购",
                "确定要清空所有已购买的内容吗？\n\n"
                "包括：主题 / 音效包 / 称号 / 清空动画\n"
                "全部恢复为初始状态，积分不变。")
        except Exception:
            ok = True
        if not ok:
            return

        # 重置为默认
        self.game["unlocked_themes"] = ["dark", "light"]
        self.game["unlocked_sfx"] = ["default"]
        self.game["unlocked_anim"] = []
        self.game["unlocked_titles"] = []
        self.game["active_theme"] = "dark"
        self.game["active_sfx"] = "default"
        self.game["active_anim"] = "none"
        self.game["active_title"] = ""
        self.game["lucky_count"] = 0
        save_game(self.game)

        # 切回深色主题
        self.settings["theme"] = "dark"
        save_settings(self.settings)
        apply_theme("dark", self.root)

        # 音效恢复默认
        self.sfx.pack = "default"

        # 刷新 UI
        try:
            self._refresh_title_badge()
            self._refresh_points_badge()
            self._refresh_theme_quick()
            if hasattr(self, "theme_var"):
                self.theme_var.set("dark")
            self._refresh_theme_btns()
        except Exception:
            pass
        try:
            if hasattr(self, "shop_content"):
                self._build_shop_list()
        except Exception:
            pass
        try:
            self.status.config(text="已清空所有购买的内容")
        except Exception:
            pass
    # ---------- 动作 ----------
    def open_ledger_folder(self):
        try:
            os.makedirs(APP_DIR, exist_ok=True)
            os.startfile(APP_DIR)
        except Exception as e:
            messagebox.showerror("无法打开", str(e))

    def export_csv(self):
        if not self.history["seen"]:
            messagebox.showinfo("提示", "暂无数据可导出"); return
        path = filedialog.asksaveasfilename(
            title="导出为 CSV", defaultextension=".csv",
            filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")],
            initialfile=f"recycle_history_{datetime.now():%Y%m%d_%H%M%S}.csv")
        if not path: return
        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f)
                w.writerow(["文件名","类型","大小(字节)","大小(可读)",
                            "删除时间","首次发现","原始路径","是否文件夹"])
                for rec in self.history["seen"].values():
                    w.writerow([
                        rec.get("filename",""), rec.get("ext",""),
                        rec.get("size",0), human_size(rec.get("size",0)),
                        rec.get("time",""), rec.get("first_seen",""),
                        rec.get("orig",""),
                        "是" if rec.get("is_dir") else "否",
                    ])
            if messagebox.askyesno("导出成功", f"已导出到：\n{path}\n\n是否打开所在文件夹？"):
                os.startfile(os.path.dirname(path))
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def reset_history(self):
        if messagebox.askyesno("确认重置",
                "确定要清空历史累计记录吗？\n\n账本文件将被删除，累计数字从头开始\n（成就不会清除）"):
            try:
                if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)
            except OSError: pass
            self.history = {"seen":{}, "total_bytes":0, "total_files":0, "total_items":0}
            self.status.config(text="历史记录已清空")
            self.refresh()

    def reset_game(self):
        if messagebox.askyesno("确认重置", "确定要清空所有成就和等级记录吗？"):
            try:
                if os.path.exists(GAME_FILE): os.remove(GAME_FILE)
            except OSError: pass
            self.game = dict(DEFAULT_GAME)
            self._refresh_level_badge()
            # 只有当前在商城-成就分类时才重绘
            if getattr(self, "shop_cat", "") == "ach":
                self._build_achievements_list()
            self.status.config(text="游戏记录已清空")

    # ---------- 定时 ----------
    def _schedule_auto(self):
        self._cancel_auto()
        sec = int(self.settings.get("scan_interval", 60))
        if sec <= 0: return
        self.auto_after_id = self.root.after(sec * 1000, self._auto_tick)

    def _cancel_auto(self):
        if self.auto_after_id:
            self.root.after_cancel(self.auto_after_id)
            self.auto_after_id = None

    def _auto_tick(self):
        self.auto_after_id = None
        self.refresh(auto=True)

    def refresh(self, auto=False):
        self._cancel_auto()
        self.status.config(text="自动刷新中…" if auto else "扫描中…")
        self._start_spinner()
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        try:
            per_drive, items = scan()
            hist = load_history()
            seen = hist["seen"]

            # ═══════════════════════════════════════════════════
            #  处理"消失的条目"：区分【清空】和【还原】
            # ═══════════════════════════════════════════════════
            current_keys = {it["key"] for it in items}
            pending = set(self.game.get("pending_cleared_keys", []) or [])

            # 判断是否属于"整体清空"：
            #   ① 软件里点的清空 → pending 里有记录
            #   ② 资源管理器里右键清空 → 整个回收站空了（seen 原来有内容，现在 current_keys 为空）
            seen_had_content = len(seen) > 0
            whole_wiped = seen_had_content and len(current_keys) == 0
            is_clear_all = bool(pending) or whole_wiped

            if is_clear_all:
                # ── 清空：seen 保留（用于趋势图/类型分布/明细），
                #          但给每条打 _cleared 标记，累计只加一次 ──
                cleared_b = 0
                cleared_f = 0
                for k, rec in seen.items():
                    if k in current_keys:
                        continue
                    if rec.get("_cleared"):
                        continue        # 已统计过，跳过
                    rec["_cleared"] = True
                    cleared_b += rec.get("size", 0)
                    cleared_f += rec.get("files", 0)

                if cleared_b or cleared_f:
                    self.game["total_cleared_bytes"] = \
                        self.game.get("total_cleared_bytes", 0) + cleared_b
                    self.game["total_cleared_files"] = \
                        self.game.get("total_cleared_files", 0) + cleared_f

                # 清空标记用完清掉
                self.game["pending_cleared_keys"] = []
                save_game(self.game)

            else:
                # ── 部分消失：判定为"还原"，从 seen 和累计里都扣掉 ──
                removed_bytes = 0
                removed_files = 0
                removed_items = 0
                for k in list(seen.keys()):
                    if k in current_keys:
                        continue
                    rec = seen.get(k)
                    if rec and rec.get("_cleared"):
                        # 这条早就被清空过了，不属于"还原"
                        continue
                    rec = seen.pop(k, None)
                    if rec:
                        removed_bytes += rec.get("size", 0)
                        removed_files += rec.get("files", 0)
                        removed_items += 1

                if removed_bytes or removed_files or removed_items:
                    hist["total_bytes"] = max(0, hist["total_bytes"] - removed_bytes)
                    hist["total_files"] = max(0, hist["total_files"] - removed_files)
                    hist["total_items"] = max(0, hist["total_items"] - removed_items)

            # ═══════════════════════════════════════════════════
            #  处理"新增条目"
            # ═══════════════════════════════════════════════════
            nb = nf = ni = 0
            new_items_list = []
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for it in items:
                if it["key"] not in seen:
                    seen[it["key"]] = {
                        "size": it["size"], "files": it["files"],
                        "orig": it["orig"], "filename": it["filename"],
                        "time": it["time"], "first_seen": now_str,
                        "is_dir": it["is_dir"], "ext": it["ext"],
                        "drive": it["drive"],
                    }
                    hist["total_bytes"] += it["size"]
                    hist["total_files"] += it["files"]
                    hist["total_items"] += 1
                    nb += it["size"]; nf += it["files"]; ni += 1
                    new_items_list.append(it)

            hist["seen"] = seen
            save_history(hist)
            self.history = hist
            self.root.after(0, lambda: self._update_ui(
                per_drive, hist, nb, nf, ni, new_items_list))
        except Exception as e:
            self.root.after(0, lambda: self._show_error(str(e)))

    def _animate_number(self, label, from_val, to_val, duration=600):
        if not self.settings.get("motion_enabled", True) or from_val == to_val:
            label.config(text=fmt_int(to_val)); return
        steps = 20
        def tick(i):
            if i > steps:
                label.config(text=fmt_int(to_val)); return
            t = i / steps
            v = int(from_val + (to_val - from_val) * t)
            label.config(text=fmt_int(v))
            self.root.after(max(1, duration // steps), lambda: tick(i+1))
        tick(0)

    # ---------- 主 UI 更新 ----------
    def _update_ui(self, per_drive, hist, nb, nf, ni, new_items_list):
        cur_bytes = sum(v[0] for v in per_drive.values())
        cur_files = sum(v[1] for v in per_drive.values())

        # 等级变化检测
        old_level, _ = calc_level(self._old_total_bytes if hasattr(self, "_old_total_bytes") else 0)
        new_level, _ = calc_level(hist['total_bytes'])

        try:
            old = int(self.bytes_label.cget("text").replace(",", ""))
        except Exception:
            old = 0
        if old == 0:
            self.bytes_label.config(text=fmt_int(hist['total_bytes']))
        else:
            self._animate_number(self.bytes_label, old, hist['total_bytes'])
        self.human_label.config(text=f"≈ {human_size(hist['total_bytes'])}")

        # 伤害数字
        if new_items_list and self.settings.get("motion_enabled", True):
            for it in new_items_list[:5]:
                self._spawn_damage(it["filename"], it["size"], it.get("drive",""))

        if ni:
            self.new_label.config(text=f"✨ 本次新增 {ni} 项 · +{fmt_int(nb)} 字节")
        else:
            self.new_label.config(text="")

        # 更新游戏数据
        max_single_old = self.game.get("max_single", 0)
        for it in new_items_list:
            if it["size"] > self.game.get("max_single", 0):
                self.game["max_single"] = it["size"]
            if it.get("is_dir"):
                self.game["has_dir"] = True
        if new_items_list:
            save_game(self.game)

        if ni > 0:
            self._bump_combo(ni)
            self.sfx.play("delete")

        # 卡片
        self.card_cur._v.config(text=human_size(cur_bytes))
        self.card_cur._s.config(text=f"{fmt_int(cur_bytes)} 字节 · {cur_files} 文件")
        self.card_items._lv.config(text=fmt_int(hist['total_items']))
        self.card_items._ls.config(text="历史项数")
        self.card_items._rv.config(text=fmt_int(hist['total_files']))
        self.card_items._rs.config(text="文件总数")

        cleared_b = self.game.get("total_cleared_bytes", 0)
        cleared_f = self.game.get("total_cleared_files", 0)
        self.card_cleared._v.config(
            text=human_size(cleared_b) if cleared_b else "0 B")
        self.card_cleared._s.config(
            text=f"{fmt_int(cleared_f)} 个文件已离你而去")
        n_drives = len(per_drive)
        self.card_drives._v.config(text=f"{n_drives} 个")
        self.card_drives._s.config(text=f"共 {human_size(cur_bytes)}")

        # 分区明细（B 方案）
        for w in self.drives_box.winfo_children(): w.destroy()
        if not per_drive:
            reg(tk.Label(self.drives_box, text="回收站是空的 ✨",
                          font=(FONT, 10)),
                bg="SURFACE", fg="DIM").pack(anchor="w", pady=8)
        else:
            mx = max(v[0] for v in per_drive.values()) or 1
            for drive in sorted(per_drive):
                size, cnt, icnt = per_drive[drive]
                self._bar(self.drives_box, drive, size, mx,
                          f"{human_size(size)} · {icnt} 项", "ACCENT")
        try:
            self.root.after(30, lambda: (
                self._drives_canvas.update_idletasks(),
                self._drives_canvas.configure(scrollregion=(
                    0, 0,
                    self._drives_canvas.bbox("all")[2],
                    max(self._drives_canvas.bbox("all")[3],
                        self._drives_canvas.winfo_height())))))
        except Exception:
            pass
        try:
            self._bind_wheel_recursive(
                self.drives_box,
                lambda e: self._drives_canvas.yview_scroll(
                    int(-1 * (e.delta / 120)), "units"))
        except Exception:
            pass

        self._last_hist = hist
        self._refresh_ext_chart(hist)
        self._draw_chart()
        self._reload_table()
        self._refresh_level_badge()

                # 时间类成就判定
        now_hour = datetime.now().hour
        now_weekday = datetime.now().weekday()
        if 2 <= now_hour < 5: self.game["night_owl_trigger"] = True
        if 6 <= now_hour < 8: self.game["early_bird_trigger"] = True
        if now_weekday >= 5: self.game["weekend_trigger"] = True
        if ni > 100: self.game["clean_master_trigger"] = True
        self._check_achievements()

        # 等级提升音
        if new_level > old_level and hasattr(self, "_old_total_bytes"):
            self.sfx.play("levelup")
            self._queue_levelup_toast(new_level)

        self._old_total_bytes = hist['total_bytes']

        now = datetime.now().strftime("%H:%M:%S")
        self.status.config(text=f"上次更新 {now}")
        self._stop_spinner()
        if self.auto_var.get(): self._schedule_auto()

    def _queue_levelup_toast(self, lvl):
        try:
            toast = tk.Frame(self.root, bg=C("ACCENT"),
                             highlightbackground=C("ACCENT_2"),
                             highlightthickness=1)
            toast.place(relx=0.5, rely=0.15, anchor="n")
            reg(tk.Label(toast, text=f"⭐ 升级到 Lv.{lvl}",
                          font=(FONT, 13, "bold")),
                bg="ACCENT", fg="PRIMARY_FG").pack(padx=24, pady=12)
            self.root.after(1800, lambda: self._destroy_toast(toast))
        except Exception:
            pass

    def _refresh_ext_chart(self, hist):
        if not hasattr(self, "ext_box"): return
        for w in self.ext_box.winfo_children(): w.destroy()
        top_n = int(self.settings.get("type_top_n", 10))
        ext_stats = defaultdict(lambda: [0,0])
        for rec in hist["seen"].values():
            e = rec.get("ext") or "(未知)"
            ext_stats[e][0] += rec.get("size", 0)
            ext_stats[e][1] += 1
        top = sorted(ext_stats.items(), key=lambda x: -x[1][0])[:top_n]
        if not top:
            reg(tk.Label(self.ext_box, text="暂无记录", font=(FONT, 10)),
                bg="SURFACE", fg="DIM").pack(anchor="w", pady=8)
        else:
            mx = max(v[0] for _, v in top) or 1
            for ext, (sz, cnt) in top:
                self._bar(self.ext_box, ext, sz, mx,
                          f"{human_size(sz)} · {cnt}", "PURPLE")
        try:
            self._bind_wheel_recursive(
                self.ext_box,
                lambda e: self._ext_canvas.yview_scroll(
                    int(-1 * (e.delta / 120)), "units"))
        except Exception:
            pass
        try:
            self.root.after(30, lambda: (
                self._ext_canvas.update_idletasks(),
                self._ext_canvas.configure(scrollregion=(
                    0, 0,
                    self._ext_canvas.bbox("all")[2],
                    max(self._ext_canvas.bbox("all")[3],
                        self._ext_canvas.winfo_height())))))
        except Exception:
            pass
    def _draw_chart(self):
        c = getattr(self, "chart_canvas", None)
        if c is None: return
        try: c.delete("all")
        except tk.TclError: return
        w = c.winfo_width(); h = c.winfo_height()
        if w < 20 or h < 20: return

        days_n = int(self.settings.get("chart_days", 7))
        try:
            self.chart_title.config(text=f"最近 {days_n} 天删除趋势")
        except Exception:
            pass

        daily = defaultdict(int)
        for rec in self.history["seen"].values():
            t = rec.get("time") or ""
            if not t: continue
            try:
                d = datetime.strptime(t[:10], "%Y-%m-%d").date()
                daily[d] += rec.get("size", 0)
            except Exception:
                pass

        today = date.today()
        days = [today - timedelta(days=i) for i in range(days_n - 1, -1, -1)]
        values = [daily.get(d, 0) for d in days]
        max_v = max(values) if values else 0

        try:
            self.chart_peak.config(
                text=f"峰值 {human_size(max_v)}" if max_v > 0 else "")
        except Exception:
            pass

        # 柱子加宽：给大字号标签留空间
        min_bar_w = 64
        inner_w = max(w, days_n * min_bar_w + 30)
        pad_l = 14; pad_r = 14; pad_b = 26
        pad_t = 26                     # 顶部留空间给柱上方标签
        bw = (inner_w - pad_l - pad_r) / max(1, len(days))

        if max_v > 0:
            avail_h = h - pad_t - pad_b
            for i, v in enumerate(values):
                bh = (v / max_v) * avail_h
                x0 = pad_l + i * bw + 3
                x1 = pad_l + (i + 1) * bw - 3
                y0 = h - pad_b
                y1 = y0 - bh
                col = C("ACCENT") if i == len(values) - 1 else C("ACCENT_2")
                c.create_rectangle(x0, y1, x1, y0, fill=col, outline="")

                if v <= 0:
                    continue

                xc = (x0 + x1) / 2
                txt = compact_size(v)

                if bh >= 34:
                    # 柱子够高：数字放在柱子内部靠上的位置
                    c.create_text(xc, y1 + 10, text=txt,
                                  fill=C("PRIMARY_FG"),
                                  font=(MONO, 11, "bold"),
                                  anchor="n")
                else:
                    # 柱子太短：数字写在柱子上方
                    c.create_text(xc, y1 - 4, text=txt,
                                  fill=C("TEXT_2"),
                                  font=(MONO, 11, "bold"),
                                  anchor="s")
        else:
            c.create_text(w // 2, h // 2, text="暂无删除记录",
                          fill=C("DIM"), font=(FONT, 9))

        for i, d in enumerate(days):
            if days_n <= 7 or i == 0 or i == len(days) - 1 \
               or i % max(1, days_n // 7) == 0:
                x = pad_l + i * bw + bw / 2
                c.create_text(x, h - 4, text=d.strftime("%m-%d"),
                              fill=C("DIM"), font=(FONT, 8), anchor="s")

        c.configure(scrollregion=(0, 0, inner_w, h))

    def _bar(self, parent, label, value, max_value, sub_text, accent):
        row = tk.Frame(parent, bg=C("SURFACE")); reg(row, bg="SURFACE")
        row.pack(fill="x", pady=3)
        top = tk.Frame(row, bg=C("SURFACE")); reg(top, bg="SURFACE")
        top.pack(fill="x")
        reg(tk.Label(top, text=label, font=(MONO, 10, "bold")),
            bg="SURFACE", fg="TEXT_2").pack(side="left")
        reg(tk.Label(top, text=sub_text, font=(FONT, 9)),
            bg="SURFACE", fg="DIM").pack(side="right")
        bg = tk.Frame(row, bg=C("SURFACE_2"), height=4)
        reg(bg, bg="SURFACE_2")
        bg.pack(fill="x", pady=(4, 0)); bg.pack_propagate(False)
        ratio = value / max_value if max_value else 0
        ratio = max(0.02, min(1.0, ratio))
        fill = tk.Frame(bg, bg=C(accent)); reg(fill, bg=accent)
        fill.place(relx=0, rely=0, relwidth=ratio, relheight=1)

    def _reload_table(self):
        if not hasattr(self, "tree"): return
        for r in self.tree.get_children(): self.tree.delete(r)
        records = list(self.history["seen"].values())
        kw = self.filter_var.get().strip().lower()
        if kw:
            records = [r for r in records
                       if kw in (r.get("orig") or "").lower()
                       or kw in (r.get("filename") or "").lower()]
        if self.heading_sort["column"]:
            col = self.heading_sort["column"]
            asc = self.heading_sort["dir"] == "asc"
            def key_func(r):
                if col == "size": return r.get("size", 0)
                if col == "filename": return (r.get("filename") or "").lower()
                if col == "ext": return (r.get("ext") or "").lower()
                if col == "time": return r.get("time") or ""
                if col == "orig": return (r.get("orig") or "").lower()
                return ""
            records.sort(key=key_func, reverse=not asc)
        else:
            mode = self.sort_key.get()
            if mode == "按时间倒序":
                records.sort(key=lambda r: r.get("time") or "", reverse=True)
            elif mode == "按大小倒序":
                records.sort(key=lambda r: r.get("size", 0), reverse=True)
            elif mode == "按名称":
                records.sort(key=lambda r: (r.get("filename") or "").lower())
            elif mode == "按类型":
                records.sort(key=lambda r: (r.get("ext") or "",
                                            -(r.get("size") or 0)))
        cap = int(self.settings.get("max_table_rows", 5000))
        shown = records if cap <= 0 else records[:cap]
        for i, rec in enumerate(shown):
            size = rec.get("size", 0)
            fn = rec.get("filename") or extract_name(rec.get("orig"), "—")
            self.tree.insert("", "end",
                values=(fn, rec.get("ext") or "—",
                        f"{human_size(size)}  ({fmt_int(size)})",
                        rec.get("time") or "—",
                        rec.get("orig") or "—"),
                tags=("odd" if i % 2 else "even",))
        total = len(records)
        if cap > 0 and total > cap:
            self.table_info.config(text=f"共 {total:,} 条 · 显示前 {cap:,} 条")
        else:
            self.table_info.config(text=f"共 {total:,} 条")

    def _show_error(self, msg):
        self.status.config(text=f"错误：{msg}")
        self._stop_spinner()


def main():
    import traceback
    root = tk.Tk()

    def _tk_error(exc, val, tb):
        try:
            os.makedirs(APP_DIR, exist_ok=True)
            with open(os.path.join(APP_DIR, "error.log"), "a", encoding="utf-8") as f:
                f.write("=== Tk callback error ===\n")
                traceback.print_exception(exc, val, tb, file=f)
                f.write("\n")
        except Exception:
            pass

    root.report_callback_exception = _tk_error

    try:
        app = RecycleApp(root)
        root.mainloop()
    except Exception:
        try:
            os.makedirs(APP_DIR, exist_ok=True)
            with open(os.path.join(APP_DIR, "error.log"), "a", encoding="utf-8") as f:
                f.write("=== Startup error ===\n")
                traceback.print_exc(file=f)
                f.write("\n")
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()