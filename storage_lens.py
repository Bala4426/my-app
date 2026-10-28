"""StorageLens - see what is using your disk, and find / open files quickly.

Pick a drive or folder and press Scan. Tabs:
  Folders        - expandable tree, biggest first, with size / % / file count
  Largest files  - top 300 biggest files
  File types     - space used per extension
  Search         - by name, extension, minimum size, age (older than N days)
  Duplicates     - finds identical files (size + content hash), keeps the oldest, recycles the rest
Right-click any row: Open, Show in Explorer, Copy path, Move to Recycle Bin.
Sizes are logical file sizes (what Explorer shows as "Size"), not size on disk.
"""
import csv
import ctypes
import hashlib
import heapq
import os
import shutil
import stat
import subprocess
import threading
import time
import colorsys
import tkinter as tk
from ctypes import wintypes
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

try:
    import sv_ttk  # modern Windows 11 style theme (optional)
except ImportError:
    sv_ttk = None

ICON_B64 = "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"
TOP_FILES = 300
MAX_SEARCH_RESULTS = 1000
MAX_CHILDREN_SHOWN = 500
REPARSE = 0x400  # junctions / symlinks / cloud placeholders: skipped to avoid double counting and loops


# ----------------------------------------------------------------- helpers
def human(n):
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return "%d B" % n if unit == "B" else "%.1f %s" % (n, unit)
        n /= 1024


def fmt_clock(sec):
    sec = int(sec)
    return "%02d:%02d" % (sec // 60, sec % 60) if sec < 3600 else "%d:%02d:%02d" % (sec // 3600, sec % 3600 // 60, sec % 60)


def fmt_date(ts):
    try:
        return datetime.fromtimestamp(ts).strftime("%d %b %Y %H:%M")
    except (OSError, ValueError, OverflowError):
        return ""


def list_drives():
    return [c + ":\\" for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(c + ":\\")]


class _FileOp(ctypes.Structure):
    _fields_ = [("hwnd", wintypes.HWND), ("wFunc", wintypes.UINT), ("pFrom", wintypes.LPCWSTR),
                ("pTo", wintypes.LPCWSTR), ("fFlags", ctypes.c_ushort), ("aborted", wintypes.BOOL),
                ("mappings", ctypes.c_void_p), ("title", wintypes.LPCWSTR)]


def recycle(path):
    """Move a file/folder to the Recycle Bin (recoverable). Returns True on success."""
    op = _FileOp()
    op.wFunc = 3                      # FO_DELETE
    op.pFrom = os.path.abspath(path) + "\0"
    op.fFlags = 0x40 | 0x10 | 0x4 | 0x400  # ALLOWUNDO | NOCONFIRMATION | SILENT | NOERRORUI
    return ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op)) == 0 and not op.aborted


def open_path(path):
    os.startfile(path)


def show_in_explorer(path):
    subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])


# -------------------------------------------------------------------- scan
class Dir:
    __slots__ = ("path", "parent", "children", "files", "size", "count", "dead")

    def __init__(self, path, parent):
        self.path, self.parent = path, parent
        self.children, self.files = [], []   # child dir ids; (name, size, mtime)
        self.size = self.count = 0
        self.dead = False


class ScanResult:
    def __init__(self):
        self.dirs, self.types, self.largest = [], {}, []
        self.skipped, self.elapsed, self.stopped = 0, 0.0, False


def scan(root, stop, prog):
    res = ScanResult()
    t0 = time.time()
    root = os.path.normpath(root)
    res.dirs.append(Dir(root, -1))
    stack = [0]
    while stack and not stop.is_set():
        i = stack.pop()
        d = res.dirs[i]
        prog["dir"] = d.path
        try:
            it = os.scandir(d.path)
        except OSError:
            res.skipped += 1
            continue
        with it:
            for e in it:
                try:
                    st = e.stat(follow_symlinks=False)
                except OSError:
                    res.skipped += 1
                    continue
                if getattr(st, "st_file_attributes", 0) & REPARSE:
                    continue
                if stat.S_ISDIR(st.st_mode):
                    res.dirs.append(Dir(e.path, i))
                    d.children.append(len(res.dirs) - 1)
                    stack.append(len(res.dirs) - 1)
                else:
                    d.files.append((e.name, st.st_size, st.st_mtime))
                    d.size += st.st_size
                    d.count += 1
                    ext = os.path.splitext(e.name)[1].lower()
                    t = res.types.setdefault(ext, [0, 0])
                    t[0] += 1
                    t[1] += st.st_size
                    prog["files"] += 1
                    prog["bytes"] += st.st_size
    # parents are always created before their children, so a reverse pass aggregates correctly
    for i in range(len(res.dirs) - 1, 0, -1):
        d = res.dirs[i]
        p = res.dirs[d.parent]
        p.size += d.size
        p.count += d.count
    res.largest = heapq.nlargest(
        TOP_FILES,
        ((f[1], i, f[0], f[2]) for i, d in enumerate(res.dirs) for f in d.files))
    res.stopped = stop.is_set()
    res.elapsed = time.time() - t0
    return res


# ------------------------------------------------- in-place model updates
def norm_key(p):
    return os.path.normcase(os.path.normpath(p))


def subtree_ids(res, di):
    ids, stack = [], [di]
    while stack:
        i = stack.pop()
        ids.append(i)
        stack.extend(res.dirs[i].children)
    return ids


def types_adjust(res, files, sign):
    for name, size, _mt in files:
        ext = os.path.splitext(name)[1].lower()
        t = res.types.setdefault(ext, [0, 0])
        t[0] += sign
        t[1] += sign * size
        if t[0] <= 0:
            res.types.pop(ext, None)


def propagate(res, di, dsize, dcount):
    while di >= 0:
        d = res.dirs[di]
        d.size += dsize
        d.count += dcount
        di = d.parent


def kill(d):
    d.files, d.children, d.size, d.count, d.dead = [], [], 0, 0, True


def drop_dir(res, di):
    """Forget a folder (deleted on disk) and everything below it."""
    ids = subtree_ids(res, di)
    d = res.dirs[di]
    size, count, parent = d.size, d.count, d.parent
    for i in ids:
        types_adjust(res, res.dirs[i].files, -1)
    for i in ids:
        kill(res.dirs[i])
    if parent >= 0:
        res.dirs[parent].children.remove(di)
        propagate(res, parent, -size, -count)


def drop_file(res, di, name):
    d = res.dirs[di]
    for n, f in enumerate(d.files):
        if f[0] == name:
            del d.files[n]
            types_adjust(res, [f], -1)
            propagate(res, di, -f[1], -1)
            return True
    return False


def splice(res, di, tmp):
    """Replace the subtree under dirs[di] with a freshly scanned `tmp` (a ScanResult rooted at the same path)."""
    old = res.dirs[di]
    old_size, old_count = old.size, old.count
    ids = subtree_ids(res, di)
    for i in ids:
        types_adjust(res, res.dirs[i].files, -1)
    for i in ids[1:]:
        kill(res.dirs[i])
    base = len(res.dirs)

    def mapped(t):
        return di if t == 0 else base + t - 1

    t0 = tmp.dirs[0]
    old.files, old.children, old.size, old.count = t0.files, [mapped(c) for c in t0.children], t0.size, t0.count
    for t in tmp.dirs[1:]:
        nd = Dir(t.path, mapped(t.parent))
        nd.files, nd.children, nd.size, nd.count = t.files, [mapped(c) for c in t.children], t.size, t.count
        res.dirs.append(nd)
    for ext, (c, sz) in tmp.types.items():
        t = res.types.setdefault(ext, [0, 0])
        t[0] += c
        t[1] += sz
    res.skipped += tmp.skipped
    propagate(res, old.parent, old.size - old_size, old.count - old_count)


def compute_largest(res):
    return heapq.nlargest(TOP_FILES, ((f[1], i, f[0], f[2]) for i, d in enumerate(res.dirs) for f in d.files))


# ------------------------------------------------------------ duplicate finder
def hash_file(path, limit=None):
    h = hashlib.blake2b(digest_size=16)
    try:
        with open(path, "rb") as f:
            if limit:
                h.update(f.read(limit))
            else:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
    except OSError:
        return None
    return h.digest()


def find_dups(files, stop, prog):
    """files: [(size, path, mtime)]. Returns [(size, [(path, mtime), ...])] biggest waste first, oldest copy first."""
    by_size = {}
    for size, path, mt in files:
        by_size.setdefault(size, []).append((path, mt))
    groups = []
    prog["dup_total"] = max(sum(len(v) for v in by_size.values() if len(v) > 1) * 2, 1)   # upper bound: partial + full pass
    prog["dup_done"] = 0
    for size, items in by_size.items():
        if len(items) < 2:
            continue
        if stop.is_set():
            break
        partial = {}
        for path, mt in items:
            prog["dir"] = path
            h = hash_file(path, 65536)
            prog["dup_done"] += 1
            if h is not None:
                partial.setdefault(h, []).append((path, mt))
        for same in partial.values():
            if len(same) < 2:
                continue
            full = {}
            for path, mt in same:
                if stop.is_set():
                    break
                prog["dir"] = path
                h = hash_file(path)
                prog["dup_done"] += 1
                if h is not None:
                    full.setdefault(h, []).append((path, mt))
            groups.extend((size, sorted(v, key=lambda x: x[1])) for v in full.values() if len(v) > 1)
    groups.sort(key=lambda g: g[0] * (len(g[1]) - 1), reverse=True)
    return groups


# ----------------------------------------------------------------- treemap
def squarify(items, x, y, w, h):
    """items: [(size, payload)] sorted by size desc. Returns [(x0, y0, x1, y1, payload)] filling the rectangle."""
    items = [(sz, pl) for sz, pl in items if sz > 0]
    if not items or w <= 0 or h <= 0:
        return []
    scale = w * h / sum(sz for sz, _ in items)
    areas = [(sz * scale, pl) for sz, pl in items]
    out = []

    def worst(row, side):
        tot = sum(a for a, _ in row)
        return max(side * side * max(a for a, _ in row) / (tot * tot), tot * tot / (side * side * min(a for a, _ in row)))

    while areas:
        side = max(min(w, h), 1e-6)
        row = [areas[0]]
        i = 1
        while i < len(areas) and worst(row + [areas[i]], side) <= worst(row, side):
            row.append(areas[i])
            i += 1
        areas = areas[i:]
        tot = sum(a for a, _ in row)
        if w >= h:                       # lay the row as a column on the left
            rw = tot / h
            cy = y
            for a, pl in row:
                rh = a / rw
                out.append((x, cy, x + rw, cy + rh, pl))
                cy += rh
            x += rw
            w -= rw
        else:                            # lay the row along the top
            rh = tot / w
            cx = x
            for a, pl in row:
                rw2 = a / rh
                out.append((cx, y, cx + rw2, y + rh, pl))
                cx += rw2
            y += rh
            h -= rh
    return out


def hash_str(t):
    v = 0
    for ch in t:
        v = (v * 131 + ord(ch)) & 0xFFFFFF
    return v


def color_for(key, is_dir):
    """Stable colour: by extension for files, muted blue-grey shades for folders."""
    hv = hash_str(key)
    if is_dir:
        r, g, b = colorsys.hls_to_rgb(0.58 + (hv % 20) / 400.0, 0.36, 0.30)
    else:
        r, g, b = colorsys.hls_to_rgb((hv % 360) / 360.0, 0.42, 0.55)
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


# ------------------------------------------------------------- table widget
class Table(ttk.Frame):
    """Sortable table. rows are tuples; `cols` = (title, width, anchor, formatter); last tuple item = path."""

    def __init__(self, master, cols, app, sort_col=0, reverse=True):
        super().__init__(master)
        self.cols, self.app, self.rows = cols, app, []
        self.sort_col, self.reverse = sort_col, reverse
        ids = [str(i) for i in range(len(cols))]
        self.tree = ttk.Treeview(self, columns=ids, show="headings", selectmode="extended")
        for i, (title, width, anchor, _f) in enumerate(cols):
            self.tree.heading(str(i), text=title, command=lambda i=i: self.sort_by(i))
            self.tree.column(str(i), width=width, anchor=anchor, stretch=(i == 0))
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        app.bind_context(self.tree, self.selected_paths, self.remove_selected)
        self.tree.bind("<Double-1>", lambda _e: self.open_selected())

    def set_rows(self, rows):
        self.rows = list(rows)
        self.render()

    def render(self):
        self.rows.sort(key=lambda r: r[self.sort_col], reverse=self.reverse)
        self.tree.delete(*self.tree.get_children())
        self.tree.tag_configure("odd", background=self.app.stripe)
        for n, r in enumerate(self.rows):
            self.tree.insert("", "end", iid=str(n), values=[c[3](r[i]) for i, c in enumerate(self.cols)],
                             tags=("odd",) if n % 2 else ())

    def sort_by(self, i):
        self.reverse = not self.reverse if i == self.sort_col else (i != 0)
        self.sort_col = i
        self.render()

    def selected_paths(self):
        return [self.rows[int(i)][-1] for i in self.tree.selection()]

    def remove_selected(self):
        gone = {int(i) for i in self.tree.selection()}
        self.rows = [r for n, r in enumerate(self.rows) if n not in gone]
        self.render()

    def open_selected(self):
        for p in self.selected_paths()[:1]:
            self.app.safe(open_path, p)


# --------------------------------------------------------------------- app
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("StorageLens")
        try:
            self._icon = tk.PhotoImage(data=ICON_B64)
            self.iconphoto(True, self._icon)
        except tk.TclError:
            pass
        self.geometry("1240x800")
        self.minsize(1000, 620)
        self.report_callback_exception = lambda *a: messagebox.showerror("Error", "%s: %s" % (a[0].__name__, a[1]))
        self.res = None
        self.stop_evt = threading.Event()
        self.prog = {"files": 0, "bytes": 0, "dir": ""}
        self.scanning = False
        self.pending = None
        self._pmap = None
        self.dup_groups, self.dup_pending, self.dup_running = [], None, False
        self.dark = True
        self.canvas_bg = self.hl_color = self.stripe = ""
        if sv_ttk:
            sv_ttk.set_theme("dark")
        self.style_colors()

        # header
        head = ttk.Frame(self, padding=(20, 16, 20, 4))
        head.pack(fill="x")
        titles = ttk.Frame(head)
        titles.pack(side="left")
        ttk.Label(titles, text="StorageLens", style="Title.TLabel").pack(anchor="w")
        ttk.Label(titles, text="See what is using your disk, then find, open and clean up files", style="Muted.TLabel").pack(anchor="w")
        self.dark_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(head, text="Dark mode", style="Switch.TCheckbutton", variable=self.dark_var,
                        command=self.toggle_theme).pack(side="right")

        # controls
        top = ttk.Frame(self, padding=(20, 8))
        top.pack(fill="x")
        self.path_var = tk.StringVar(value=(list_drives() or ["C:\\"])[-1])
        self.combo = ttk.Combobox(top, textvariable=self.path_var, values=list_drives(), width=46)
        self.combo.pack(side="left")
        self.combo.bind("<<ComboboxSelected>>", lambda _e: self.update_disk_info())
        ttk.Button(top, text="\u22ef  Browse", command=self.browse).pack(side="left", padx=(8, 0))
        self.scan_btn = ttk.Button(top, text="\u25b6  Scan", style="Accent.TButton", command=self.start_scan)
        self.scan_btn.pack(side="left", padx=(8, 0))
        self.refresh_btn = ttk.Button(top, text="\u21bb  Refresh selected (F5)", command=self.refresh_selected)
        self.refresh_btn.pack(side="left", padx=(8, 0))
        self.stop_btn = ttk.Button(top, text="\u25a0  Stop", command=self.stop_evt.set, state="disabled")
        self.stop_btn.pack(side="left", padx=(8, 0))
        ttk.Button(top, text="\u2193  Export CSV", command=self.export_csv).pack(side="right")
        self.bind("<F5>", lambda _e: self.refresh_selected())

        # summary cards
        cards = ttk.Frame(self, padding=(20, 4, 20, 8))
        cards.pack(fill="x")
        for i in range(4):
            cards.columnconfigure(i, weight=1, uniform="card")
        self.cv = {k: tk.StringVar(value="-") for k in ("disk", "free", "size", "files", "folders")}

        def card(col, caption):
            f = ttk.LabelFrame(cards, text=caption, padding=(14, 8))
            f.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 10, 0))
            return f

        c = card(0, "Disk")
        ttk.Label(c, textvariable=self.cv["disk"], style="CardBig.TLabel").pack(anchor="w")
        self.disk_bar = ttk.Progressbar(c, maximum=100)
        self.disk_bar.pack(fill="x", pady=(6, 2))
        ttk.Label(c, textvariable=self.cv["free"], style="Muted.TLabel").pack(anchor="w")
        for col, key, cap in ((1, "size", "Scanned size"), (2, "files", "Files"), (3, "folders", "Folders")):
            c = card(col, cap)
            ttk.Label(c, textvariable=self.cv[key], style="CardBig.TLabel").pack(anchor="w", pady=(6, 14))

        # tabs
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=20, pady=(0, 6))

        self.folder_tab = ttk.Frame(self.nb)
        self.build_folder_tab(self.folder_tab)
        self.nb.add(self.folder_tab, text="  \u25a4  Folders  ")

        self.map_tab = ttk.Frame(self.nb)
        self.build_map_tab(self.map_tab)
        self.nb.add(self.map_tab, text="  \u25a6  Treemap  ")
        self.nb.bind("<<NotebookTabChanged>>", lambda _e: self.draw_map())

        self.largest = Table(self.nb, [
            ("Name", 260, "w", str), ("Size", 100, "e", human), ("Modified", 140, "center", fmt_date),
            ("Folder", 500, "w", str), ("", 0, "w", str)], self, sort_col=1)
        self.nb.add(self.largest, text="  \u21e9  Largest files  ")

        self.types = Table(self.nb, [
            ("Type", 200, "w", lambda x: x or "(no extension)"), ("Files", 100, "e", lambda n: "{:,}".format(n)),
            ("Size", 120, "e", human), ("% of scanned", 110, "e", lambda p: "%.1f%%" % p), ("", 0, "w", str)], self, sort_col=2)
        self.nb.add(self.types, text="  \u25d4  File types  ")

        self.search_tab = ttk.Frame(self.nb)
        self.build_search_tab(self.search_tab)
        self.nb.add(self.search_tab, text="  \u2315  Search  ")

        self.dup_tab = ttk.Frame(self.nb)
        self.build_dup_tab(self.dup_tab)
        self.nb.add(self.dup_tab, text="  \u29c9  Duplicates  ")

        self.status = tk.StringVar(value="Choose a drive or folder and press Scan.")
        ttk.Label(self, textvariable=self.status, style="Muted.TLabel", padding=(20, 6)).pack(fill="x", side="bottom")
        self.busy = ttk.Frame(self, padding=(20, 4, 20, 0))      # shown only while scanning / comparing
        self.pbar = ttk.Progressbar(self.busy, mode="determinate", maximum=100)
        self.pbar.pack(side="left", fill="x", expand=True)
        self.pct_var = tk.StringVar()
        ttk.Label(self.busy, textvariable=self.pct_var, width=6, anchor="e").pack(side="left", padx=(10, 0))
        self.busy_t0, self.busy_total, self.busy_label = 0.0, None, ""
        self.update_disk_info()

    # ---- theme
    def style_colors(self):
        dark = self.dark
        self.canvas_bg, self.hl_color = ("#1c1c1c", "#ffffff") if dark else ("#f3f3f3", "#111111")
        self.stripe = "#272727" if dark else "#f4f6f8"
        st = ttk.Style(self)
        st.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        st.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        st.configure("Muted.TLabel", foreground="#9aa0a6" if dark else "#5f6368")
        st.configure("CardBig.TLabel", font=("Segoe UI", 18, "bold"))
        st.configure("Title.TLabel", font=("Segoe UI", 22, "bold"))

    def toggle_theme(self):
        self.dark = self.dark_var.get()
        if sv_ttk:
            sv_ttk.set_theme("dark" if self.dark else "light")
        self.style_colors()
        self.canvas.configure(background=self.canvas_bg)
        for t in (self.largest, self.types, self.results):
            t.render()
        self.draw_map()

    # ---- shared helpers
    def safe(self, fn, *a):
        try:
            fn(*a)
        except Exception as ex:
            messagebox.showerror("Error", "%s: %s" % (type(ex).__name__, ex))

    def bind_context(self, tree, get_paths, on_removed):
        menu = tk.Menu(tree, tearoff=0)

        def paths():
            return [p for p in get_paths() if p]

        def do_open():
            for p in paths()[:1]:
                self.safe(open_path, p)

        def do_show():
            for p in paths()[:1]:
                self.safe(show_in_explorer, p)

        def do_copy():
            self.clipboard_clear()
            self.clipboard_append("\n".join(paths()))

        def do_delete():
            ps = paths()
            if not ps:
                return
            msg = "Move %d item(s) to the Recycle Bin?\n\n%s" % (len(ps), "\n".join(ps[:8]) + ("\n..." if len(ps) > 8 else ""))
            if not messagebox.askyesno("Recycle", msg, icon="warning"):
                return
            ok = [p for p in ps if recycle(p)]
            if len(ok) != len(ps):
                messagebox.showwarning("Recycle", "%d item(s) could not be deleted (in use or no permission)." % (len(ps) - len(ok)))
            if ok:
                self.forget_paths(ok)
                self.status.set("%d item(s) moved to Recycle Bin. Sizes updated." % len(ok))

        menu.add_command(label="Open", command=do_open)
        menu.add_command(label="Show in Explorer", command=do_show)
        menu.add_command(label="Copy path", command=do_copy)
        menu.add_separator()
        menu.add_command(label="Move to Recycle Bin", command=do_delete)

        def popup(ev):
            row = tree.identify_row(ev.y)
            if row and row not in tree.selection():
                tree.selection_set(row)
            if tree.selection():
                menu.tk_popup(ev.x_root, ev.y_root)

        tree.bind("<Button-3>", popup)

    def browse(self):
        p = filedialog.askdirectory(initialdir=self.path_var.get())
        if p:
            self.path_var.set(os.path.normpath(p))
            self.update_disk_info()

    def update_disk_info(self):
        try:
            u = shutil.disk_usage(self.path_var.get())
            self.cv["disk"].set("%s used" % human(u.used))
            self.cv["free"].set("%s free of %s  (%.0f%%)" % (human(u.free), human(u.total), u.used / u.total * 100))
            self.disk_bar["value"] = u.used / u.total * 100
        except OSError:
            self.cv["disk"].set("-")
            self.cv["free"].set("")
            self.disk_bar["value"] = 0

    def update_cards(self):
        if self.res:
            root = self.res.dirs[0]
            self.cv["size"].set(human(root.size))
            self.cv["files"].set("{:,}".format(root.count))
            self.cv["folders"].set("{:,}".format(len(self.path_map())))

    # ---- progress bar
    def begin_busy(self, label, total=None):
        """total = expected bytes (determinate bar with %); None = animated bar without a percentage."""
        self.busy_t0, self.busy_total, self.busy_label = time.time(), total, label
        self.pbar.stop()
        if total:
            self.pbar.config(mode="determinate", maximum=100, value=0)
        else:
            self.pbar.config(mode="indeterminate")
            self.pbar.start(12)
        self.pct_var.set("")
        self.busy.pack(fill="x", side="bottom")

    def end_busy(self):
        self.pbar.stop()
        self.busy.pack_forget()

    # ---- scanning
    def start_scan(self, root=None):
        root = root or self.path_var.get().strip()
        if self.scanning:
            return
        if not os.path.isdir(root):
            messagebox.showwarning("Scan", "Folder not found: %s" % root)
            return
        self.stop_evt.clear()
        self.prog.update(files=0, bytes=0, dir="")
        self.scanning = True
        self.pending = None
        self.scan_btn.config(state="disabled")
        self.refresh_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.update_disk_info()
        total = None
        if os.path.splitdrive(root)[1] in ("\\", "/"):              # whole drive: estimate progress from used space
            try:
                total = shutil.disk_usage(root).used
            except OSError:
                pass
        self.begin_busy("Scanning", total)
        self.poll()

        def work():
            try:
                self.pending = scan(root, self.stop_evt, self.prog)
            except Exception as ex:  # never leave the UI stuck in "Scanning..."
                self.pending = ex

        threading.Thread(target=work, daemon=True).start()

    def poll(self):
        if not self.scanning:
            return
        if self.pending is not None:
            res, self.pending = self.pending, None
            if isinstance(res, tuple):
                self.refresh_done(*res)
            elif isinstance(res, Exception):
                self.scanning = False
                self.scan_btn.config(state="normal")
                self.refresh_btn.config(state="normal")
                self.stop_btn.config(state="disabled")
                self.end_busy()
                messagebox.showerror("Scan failed", "%s: %s" % (type(res).__name__, res))
            else:
                self.scan_done(res)
            return
        pct = ""
        if self.busy_total:
            frac = min(self.prog["bytes"] / self.busy_total, 0.99)
            self.pbar["value"] = frac * 100
            pct = "%d%%" % (frac * 100)
        self.pct_var.set(pct)
        self.status.set("%s %s   %s files   %s   %s   |   %s" % (
            self.busy_label, pct, "{:,}".format(self.prog["files"]), human(self.prog["bytes"]),
            fmt_clock(time.time() - self.busy_t0), self.prog["dir"][-80:]))
        self.after(250, self.poll)

    def scan_done(self, res):
        self.scanning = False
        self.scan_btn.config(state="normal")
        self.refresh_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.end_busy()
        self.res = res
        root = res.dirs[0]
        self._pmap = None
        self.map_dir, self.map_sel = 0, None
        self.refresh_views(recompute_largest=False, keep_tree=False)
        self.status.set("%s%s: %s in %s files, %s folders. %.1f sec%s" % (
            "Stopped early. " if res.stopped else "", root.path, human(root.size), "{:,}".format(root.count),
            "{:,}".format(len(res.dirs)), res.elapsed,
            ("  (%d folders not accessible)" % res.skipped) if res.skipped else ""))

    # ---- keeping the view in sync with the disk
    def path_map(self):
        if getattr(self, "_pmap", None) is None:
            self._pmap = {norm_key(d.path): i for i, d in enumerate(self.res.dirs) if not d.dead}
        return self._pmap

    def refresh_views(self, recompute_largest=True, keep_tree=True):
        res = self.res
        if recompute_largest:
            res.largest = compute_largest(res)
        total = max(res.dirs[0].size, 1)
        self.largest.set_rows([(name, size, mt, res.dirs[di].path, os.path.join(res.dirs[di].path, name))
                               for size, di, name, mt in res.largest])
        self.types.set_rows([(ext, c, s, s / total * 100, "") for ext, (c, s) in res.types.items()])
        opened, y = [], 0.0
        if keep_tree:
            opened = sorted(int(i[1:]) for i in self.fmap if i[0] == "d" and self.ftree.exists(i) and self.ftree.item(i, "open"))
            y = self.ftree.yview()[0]
        self.fill_folder_root()
        for di in opened:
            iid = "d%d" % di
            if self.ftree.exists(iid) and not res.dirs[di].dead:
                self.ftree.item(iid, open=True)
                self.expand(iid)
        if keep_tree:
            self.update_idletasks()
            self.ftree.yview_moveto(y)
        while res.dirs[self.map_dir].dead:       # the folder shown in the treemap was removed
            self.map_dir = res.dirs[self.map_dir].parent if res.dirs[self.map_dir].parent >= 0 else 0
            self.map_sel = None
        self.map_sel = None
        self.draw_map()
        if self.results.rows:
            self.run_search()
        self.update_disk_info()
        self.update_cards()

    def forget_paths(self, paths):
        """Items were deleted: update sizes in memory instead of requiring a rescan."""
        if not self.res:
            return
        pmap = self.path_map()
        for p in paths:
            k = norm_key(p)
            di = pmap.get(k)
            if di is not None and di != 0:
                drop_dir(self.res, di)
            else:
                pi = pmap.get(norm_key(os.path.dirname(p)))
                if pi is not None:
                    drop_file(self.res, pi, os.path.basename(p))
        self._pmap = None
        keys = [norm_key(p) for p in paths]
        self.results.rows = [r for r in self.results.rows
                             if not any(norm_key(r[-1]) == k or norm_key(r[-1]).startswith(k + os.sep) for k in keys)]
        self.results.render()
        self.dup_prune(keys)
        self.refresh_views()

    def refresh_target(self):
        sel = self.nb.nametowidget(self.nb.select())
        if sel is self.map_tab:
            return self.map_dir
        if sel is self.folder_tab:
            for iid in self.ftree.selection():
                if iid in self.fmap:
                    return self.fmap[iid][1] if self.fmap[iid][0] == "d" else int(iid[1:].split("_")[0])
        return 0

    def refresh_selected(self):
        if not self.res:
            messagebox.showinfo("Refresh", "Scan a drive or folder first.")
            return
        if self.scanning:
            return
        di = self.refresh_target()
        if di == 0:
            self.start_scan(self.res.dirs[0].path)
            return
        path = self.res.dirs[di].path
        if not os.path.isdir(path):              # folder no longer exists
            drop_dir(self.res, di)
            self._pmap = None
            self.refresh_views()
            self.status.set("%s no longer exists. Removed from the view." % path)
            return
        self.stop_evt.clear()
        self.prog.update(files=0, bytes=0, dir="")
        self.scanning = True
        self.pending = None
        self.scan_btn.config(state="disabled")
        self.refresh_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.begin_busy("Refreshing")
        self.poll()

        def work():
            try:
                self.pending = ("refresh", di, scan(path, self.stop_evt, self.prog))
            except Exception as ex:
                self.pending = ex

        threading.Thread(target=work, daemon=True).start()

    def refresh_done(self, _tag, di, tmp):
        self.scanning = False
        self.scan_btn.config(state="normal")
        self.refresh_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.end_busy()
        if tmp.stopped:
            self.status.set("Refresh stopped. Nothing was changed.")
            return
        old = self.res.dirs[di].size
        splice(self.res, di, tmp)
        self._pmap = None
        self.refresh_views()
        self.status.set("Refreshed %s: %s -> %s (%.1f sec)" % (self.res.dirs[di].path, human(old), human(self.res.dirs[di].size), tmp.elapsed))

    # ---- folders tab
    def build_folder_tab(self, tab):
        cols = ("size", "pct", "files", "bar", "modified")
        self.ftree = ttk.Treeview(tab, columns=cols, selectmode="extended")
        self.ftree.heading("#0", text="Name")
        self.ftree.column("#0", width=430)
        for c, t, w, a in (("size", "Size", 100, "e"), ("pct", "% of parent", 120, "e"), ("files", "Files", 90, "e"),
                           ("bar", "", 170, "w"), ("modified", "Modified", 140, "center")):
            self.ftree.heading(c, text=t)
            self.ftree.column(c, width=w, anchor=a, stretch=False)
        sb = ttk.Scrollbar(tab, orient="vertical", command=self.ftree.yview)
        self.ftree.configure(yscrollcommand=sb.set)
        self.ftree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.fmap = {}  # iid -> (kind, dir_id or None, full path)
        self.ftree.bind("<<TreeviewOpen>>", self.on_expand)
        self.ftree.bind("<Double-1>", self.on_fdouble)
        self.ftree.tag_configure("dir", font=("Segoe UI", 9, "bold"))
        self.bind_context(self.ftree, lambda: [self.fmap[i][2] for i in self.ftree.selection() if i in self.fmap],
                          lambda: [self.ftree.delete(i) for i in self.ftree.selection()])

    def fill_folder_root(self):
        self.ftree.delete(*self.ftree.get_children())
        self.fmap.clear()
        self.add_dir_row("", 0, 1)
        self.ftree.item("d0", open=True)
        self.expand("d0")

    def add_dir_row(self, parent_iid, di, parent_size):
        d = self.res.dirs[di]
        iid = "d%d" % di
        pct = 100.0 if di == 0 else (d.size / parent_size * 100 if parent_size else 0)
        name = d.path if di == 0 else os.path.basename(d.path)
        self.ftree.insert(parent_iid, "end", iid=iid, text=name, open=False, tags=("dir",),
                          values=(human(d.size), "%.1f%%" % pct, "{:,}".format(d.count), "\u2588" * int(min(pct, 100) / 6), ""))
        self.fmap[iid] = ("d", di, d.path)
        if d.children or d.files:
            self.ftree.insert(iid, "end", iid=iid + "_stub", text="")  # makes the expander arrow appear

    def on_expand(self, _event):
        focus = self.ftree.focus()
        if focus:
            self.expand(focus)

    def expand(self, iid):
        if iid not in self.fmap or self.fmap[iid][0] != "d" or not self.ftree.exists(iid + "_stub"):
            return
        self.ftree.delete(iid + "_stub")
        di = self.fmap[iid][1]
        d = self.res.dirs[di]
        kids = sorted(d.children, key=lambda c: self.res.dirs[c].size, reverse=True)
        for c in kids[:MAX_CHILDREN_SHOWN]:
            self.add_dir_row(iid, c, d.size)
        files = sorted(d.files, key=lambda f: f[1], reverse=True)
        for n, (name, size, mt) in enumerate(files[:MAX_CHILDREN_SHOWN]):
            fid = "f%d_%d" % (di, n)
            pct = size / d.size * 100 if d.size else 0
            self.ftree.insert(iid, "end", iid=fid, text=name,
                              values=(human(size), "%.1f%%" % pct, "", "\u2591" * int(min(pct, 100) / 6), fmt_date(mt)))
            self.fmap[fid] = ("f", None, os.path.join(d.path, name))
        hidden = max(0, len(kids) - MAX_CHILDREN_SHOWN) + max(0, len(files) - MAX_CHILDREN_SHOWN)
        if hidden:
            self.ftree.insert(iid, "end", text="... %d more (smaller) items not shown" % hidden)

    def on_fdouble(self, ev):
        iid = self.ftree.identify_row(ev.y)
        if iid in self.fmap and self.fmap[iid][0] == "f":
            self.safe(open_path, self.fmap[iid][2])

    # ---- treemap tab
    def build_map_tab(self, tab):
        self.map_dir, self.map_tiles, self.map_sel, self._map_job = 0, [], None, None
        bar = ttk.Frame(tab, padding=(6, 6, 6, 0))
        bar.pack(fill="x")
        ttk.Button(bar, text="\u2191 Up", command=self.map_up).pack(side="left")
        ttk.Button(bar, text="Top", command=lambda: self.map_goto(0)).pack(side="left", padx=4)
        self.map_path = ttk.Label(bar, text="Scan first. Click a block to select it, double-click a folder to open it.")
        self.map_path.pack(side="left", padx=10)
        self.legend = ttk.Frame(tab, padding=(8, 6, 8, 0))
        self.legend.pack(fill="x")
        self.canvas = tk.Canvas(tab, background=self.canvas_bg, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=6, pady=6)
        self.canvas.bind("<Configure>", lambda _e: self.schedule_map())
        self.canvas.bind("<Button-1>", self.map_click)
        self.canvas.bind("<Double-1>", self.map_double)
        self.canvas.bind("<Motion>", self.map_hover)
        self.canvas.bind("<Button-3>", self.map_menu)

    def map_menu(self, ev):
        self.map_click(ev)
        tile = self.map_sel
        if not tile or not tile["path"]:
            return
        path = tile["path"]
        m = tk.Menu(self.canvas, tearoff=0)
        m.add_command(label="Open", command=lambda: self.safe(open_path, path))
        m.add_command(label="Show in Explorer", command=lambda: self.safe(show_in_explorer, path))
        m.add_command(label="Copy path", command=lambda: (self.clipboard_clear(), self.clipboard_append(path)))
        m.add_separator()
        m.add_command(label="Move to Recycle Bin", command=lambda: self.map_recycle(tile))
        m.tk_popup(ev.x_root, ev.y_root)

    def map_recycle(self, tile):
        if not messagebox.askyesno("Recycle", "Move to the Recycle Bin?\n\n%s" % tile["path"], icon="warning"):
            return
        if recycle(tile["path"]):
            self.forget_paths([tile["path"]])
            self.status.set("Moved to Recycle Bin. Sizes updated.")
        else:
            messagebox.showwarning("Recycle", "Could not delete (in use or no permission).")

    def schedule_map(self):
        if self._map_job:
            self.after_cancel(self._map_job)
        self._map_job = self.after(120, self.draw_map)

    def map_goto(self, di):
        self.map_dir, self.map_sel = di, None
        self.draw_map()

    def map_up(self):
        if self.res and self.res.dirs[self.map_dir].parent >= 0:
            self.map_goto(self.res.dirs[self.map_dir].parent)

    def draw_map(self, relayout=True):
        if not self.res or self.nb.select() != str(self.map_tab):
            return
        c = self.canvas
        w, h = c.winfo_width(), c.winfo_height()
        if w < 20 or h < 20:
            return
        d = self.res.dirs[self.map_dir]
        if relayout:
            items = [(self.res.dirs[k].size, {"kind": "d", "label": os.path.basename(self.res.dirs[k].path) or self.res.dirs[k].path,
                                              "size": self.res.dirs[k].size, "path": self.res.dirs[k].path, "di": k}) for k in d.children]
            items += [(sz, {"kind": "f", "label": name, "size": sz, "path": os.path.join(d.path, name), "di": None})
                      for name, sz, _mt in d.files]
            items.sort(key=lambda t: t[0], reverse=True)
            if len(items) > 400:
                rest = items[400:]
                rest_size = sum(i[0] for i in rest)
                items = items[:400] + [(rest_size, {"kind": "o", "label": "%d smaller items" % len(rest), "size": rest_size, "path": "", "di": None})]
            self.map_tiles = squarify(items, 0, 0, w - 1, h - 1)
            self.update_legend(d)
        c.delete("all")
        total = max(d.size, 1)
        self.map_path.config(text="%s   %s" % (d.path, human(d.size)))
        for x0, y0, x1, y1, tile in self.map_tiles:
            kind = tile["kind"]
            if kind == "o":
                fill = "#555a60"
            elif kind == "d":
                fill = color_for(tile["label"], True)
            else:
                fill = color_for(os.path.splitext(tile["label"])[1].lower() or "none", False)
            sel = self.map_sel is tile
            c.create_rectangle(x0, y0, x1, y1, fill=fill, outline=self.hl_color if sel else self.canvas_bg, width=2 if sel else 1)
            if x1 - x0 > 60 and y1 - y0 > 30:
                c.create_text(x0 + 5, y0 + 4, anchor="nw", fill="white", width=x1 - x0 - 8,
                              font=("Segoe UI", 8, "bold" if kind == "d" else "normal"),
                              text="%s\n%s  %.1f%%" % (tile["label"], human(tile["size"]), tile["size"] / total * 100))

    def tile_at(self, ev):
        for x0, y0, x1, y1, tile in self.map_tiles:
            if x0 <= ev.x <= x1 and y0 <= ev.y <= y1:
                return tile
        return None

    def map_click(self, ev):
        tile = self.tile_at(ev)
        if tile is not self.map_sel:
            self.map_sel = tile
            self.draw_map(relayout=False)

    def map_double(self, ev):
        tile = self.tile_at(ev)
        if not tile:
            return
        if tile["kind"] == "d":
            self.map_goto(tile["di"])
        elif tile["kind"] == "f":
            self.safe(open_path, tile["path"])

    def map_hover(self, ev):
        tile = self.tile_at(ev)
        self.canvas.delete("hover")
        if not tile:
            return
        for x0, y0, x1, y1, t in self.map_tiles:
            if t is tile:
                self.canvas.create_rectangle(x0 + 1, y0 + 1, x1 - 1, y1 - 1, outline=self.hl_color, width=2, tags="hover")
                break
        if not self.scanning:
            self.status.set("%s   %s" % (tile["path"] or tile["label"], human(tile["size"])))

    def update_legend(self, d):
        for w in self.legend.winfo_children():
            w.destroy()
        by_ext = {}
        for name, size, _mt in d.files:
            ext = os.path.splitext(name)[1].lower() or "none"
            by_ext[ext] = by_ext.get(ext, 0) + size
        chips = [("Folder", color_for("x", True))] + [(e, color_for(e, False)) for e, _ in
                                                       sorted(by_ext.items(), key=lambda kv: kv[1], reverse=True)[:8]]
        for label, col in chips:
            tk.Frame(self.legend, bg=col, width=14, height=14).pack(side="left")
            ttk.Label(self.legend, text=label, style="Muted.TLabel").pack(side="left", padx=(4, 14))

    # ---- duplicates tab
    def build_dup_tab(self, tab):
        bar = ttk.Frame(tab, padding=(6, 8))
        bar.pack(fill="x")
        ttk.Label(bar, text="Min file size (MB)").pack(side="left")
        self.dup_min = tk.StringVar(value="1")
        ttk.Entry(bar, textvariable=self.dup_min, width=6).pack(side="left", padx=(6, 12))
        self.dup_btn = ttk.Button(bar, text="\u2315  Find duplicates", style="Accent.TButton", command=self.find_duplicates)
        self.dup_btn.pack(side="left")
        ttk.Button(bar, text="\u2611  Select all but oldest", command=self.dup_select_extra).pack(side="left", padx=8)
        ttk.Button(bar, text="\u2716  Move selected to Recycle Bin", command=self.dup_recycle).pack(side="left")
        self.dup_info = ttk.Label(bar, style="Muted.TLabel")
        self.dup_info.pack(side="left", padx=12)
        frame = ttk.Frame(tab)
        frame.pack(fill="both", expand=True)
        self.dtree = ttk.Treeview(frame, columns=("size", "modified", "folder"), selectmode="extended")
        self.dtree.heading("#0", text="Group / file")
        self.dtree.column("#0", width=380)
        for c, t, w, a in (("size", "Size", 100, "e"), ("modified", "Modified", 140, "center"), ("folder", "Folder", 420, "w")):
            self.dtree.heading(c, text=t)
            self.dtree.column(c, width=w, anchor=a, stretch=(c == "folder"))
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.dtree.yview)
        self.dtree.configure(yscrollcommand=sb.set)
        self.dtree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.dtree.tag_configure("group", font=("Segoe UI", 9, "bold"))
        self.dmap = {}
        self.bind_context(self.dtree, lambda: [self.dmap[i] for i in self.dtree.selection() if i in self.dmap], lambda: None)
        self.dtree.bind("<Double-1>", lambda ev: [self.safe(open_path, self.dmap[i]) for i in [self.dtree.identify_row(ev.y)] if i in self.dmap])

    def find_duplicates(self):
        if not self.res:
            messagebox.showinfo("Duplicates", "Scan a drive or folder first.")
            return
        if self.dup_running or self.scanning:
            return
        try:
            min_size = max(float(self.dup_min.get() or 0) * 1024 * 1024, 1)
        except ValueError:
            messagebox.showwarning("Duplicates", "Min file size must be a number (MB).")
            return
        files = [(sz, os.path.join(d.path, name), mt) for d in self.res.dirs for name, sz, mt in d.files if sz >= min_size]
        self.dup_running, self.dup_pending = True, None
        self.stop_evt.clear()
        self.dup_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.prog.update(dup_total=1, dup_done=0)
        self.begin_busy("Comparing files", 1)
        self.poll_dups()

        def work():
            try:
                self.dup_pending = find_dups(files, self.stop_evt, self.prog)
            except Exception as ex:
                self.dup_pending = ex

        threading.Thread(target=work, daemon=True).start()

    def poll_dups(self):
        if not self.dup_running:
            return
        if self.dup_pending is not None:
            res, self.dup_pending = self.dup_pending, None
            self.dup_running = False
            self.dup_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.end_busy()
            if isinstance(res, Exception):
                messagebox.showerror("Duplicates", "%s: %s" % (type(res).__name__, res))
            else:
                self.dup_groups = res
                self.render_dups()
            return
        frac = min(self.prog["dup_done"] / max(self.prog["dup_total"], 1), 0.99)
        self.pbar["value"] = frac * 100
        self.pct_var.set("%d%%" % (frac * 100))
        self.status.set("Comparing files %d%%   %s   |   %s" % (frac * 100, fmt_clock(time.time() - self.busy_t0), self.prog["dir"][-80:]))
        self.after(250, self.poll_dups)

    def render_dups(self):
        self.dtree.delete(*self.dtree.get_children())
        self.dmap.clear()
        wasted = 0
        for gi, (size, items) in enumerate(self.dup_groups):
            wasted += size * (len(items) - 1)
            if gi >= 500:
                continue
            gid = "g%d" % gi
            self.dtree.insert("", "end", iid=gid, tags=("group",), text="%d copies x %s   (can free %s)" % (
                len(items), human(size), human(size * (len(items) - 1))), values=(human(size), "", ""))
            for n, (path, mt) in enumerate(items):
                iid = "%s_%d" % (gid, n)
                self.dtree.insert(gid, "end", iid=iid, text=os.path.basename(path) + ("   (oldest, keep)" if n == 0 else ""),
                                  values=(human(size), fmt_date(mt), os.path.dirname(path)))
                self.dmap[iid] = path
        n = len(self.dup_groups)
        self.dup_info.config(text="%d duplicate group(s), %s can be freed%s" % (
            n, human(wasted), "  (showing the top 500)" if n > 500 else ""))
        self.status.set("Duplicates: %d group(s), %s can be freed." % (n, human(wasted)))

    def dup_prune(self, keys):
        """After deletions: drop removed files from the duplicate groups and redraw."""
        if not self.dup_groups:
            return
        def gone(path):
            k = norm_key(path)
            return any(k == x or k.startswith(x + os.sep) for x in keys)
        groups = []
        for size, items in self.dup_groups:
            items = [i for i in items if not gone(i[0])]
            if len(items) > 1:
                groups.append((size, items))
        self.dup_groups = groups
        self.render_dups()

    def dup_select_extra(self):
        pick = []
        for gid in self.dtree.get_children():
            self.dtree.item(gid, open=True)
            pick.extend(self.dtree.get_children(gid)[1:])
        self.dtree.selection_set(pick)
        self.status.set("%d duplicate file(s) selected (the oldest copy of each is kept)." % len(pick))

    def dup_recycle(self):
        sel = [i for i in self.dtree.selection() if i in self.dmap]
        if not sel:
            messagebox.showinfo("Duplicates", "Select files first (or use \"Select all but oldest\").")
            return
        whole = [g for g in self.dtree.get_children() if self.dtree.get_children(g) and
                 all(k in sel for k in self.dtree.get_children(g))]
        if whole and not messagebox.askyesno("Every copy selected", "You selected EVERY copy in %d group(s). "
                                             "Those files would be gone completely.\n\nContinue?" % len(whole), icon="warning"):
            return
        paths = [self.dmap[i] for i in sel]
        if not messagebox.askyesno("Recycle", "Move %d file(s) to the Recycle Bin?" % len(paths), icon="warning"):
            return
        ok = [p for p in paths if recycle(p)]
        if len(ok) != len(paths):
            messagebox.showwarning("Recycle", "%d file(s) could not be deleted (in use or no permission)." % (len(paths) - len(ok)))
        if ok:
            self.forget_paths(ok)
            self.status.set("%d duplicate file(s) moved to Recycle Bin. Sizes updated." % len(ok))

    # ---- search tab
    def build_search_tab(self, tab):
        bar = ttk.Frame(tab, padding=6)
        bar.pack(fill="x")
        self.q_name, self.q_ext, self.q_min, self.q_days = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()
        for label, var, w in (("Name contains", self.q_name, 22), ("Extension (e.g. pdf)", self.q_ext, 9),
                              ("Min size (MB)", self.q_min, 7), ("Older than (days)", self.q_days, 7)):
            ttk.Label(bar, text=label).pack(side="left")
            e = ttk.Entry(bar, textvariable=var, width=w)
            e.pack(side="left", padx=(4, 12))
            e.bind("<Return>", lambda _e: self.run_search())
        ttk.Button(bar, text="Search", style="Accent.TButton", command=self.run_search).pack(side="left")
        self.search_info = ttk.Label(bar)
        self.search_info.pack(side="left", padx=12)
        self.results = Table(tab, [
            ("Name", 260, "w", str), ("Size", 100, "e", human), ("Modified", 140, "center", fmt_date),
            ("Folder", 500, "w", str), ("", 0, "w", str)], self, sort_col=1)
        self.results.pack(fill="both", expand=True)

    def run_search(self):
        if not self.res:
            messagebox.showinfo("Search", "Scan a drive or folder first.")
            return
        name = self.q_name.get().strip().lower()
        ext = self.q_ext.get().strip().lower().lstrip(".")
        try:
            min_size = float(self.q_min.get() or 0) * 1024 * 1024
            days = float(self.q_days.get() or 0)
        except ValueError:
            messagebox.showwarning("Search", "Min size (MB) and age (days) must be numbers.")
            return
        cutoff = time.time() - days * 86400 if days else None
        hits = []
        for d in self.res.dirs:
            for fname, size, mt in d.files:
                if size < min_size or (cutoff is not None and mt > cutoff):
                    continue
                low = fname.lower()
                if name and name not in low:
                    continue
                if ext and not low.endswith("." + ext):
                    continue
                hits.append((fname, size, mt, d.path, os.path.join(d.path, fname)))
        total = len(hits)
        hits = heapq.nlargest(MAX_SEARCH_RESULTS, hits, key=lambda r: r[1])
        self.results.set_rows(hits)
        self.search_info.config(text="%s match(es)%s" % ("{:,}".format(total), ", showing the biggest %d" % MAX_SEARCH_RESULTS if total > MAX_SEARCH_RESULTS else ""))

    # ---- export
    def export_csv(self):
        if not self.res:
            messagebox.showinfo("Export", "Scan first.")
            return
        sel = self.nb.nametowidget(self.nb.select())
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], initialfile="storage_lens.csv")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            if sel in (self.folder_tab, self.map_tab):
                w.writerow(["Folder", "Size (bytes)", "Size", "Files"])
                for d in sorted(self.res.dirs, key=lambda d: d.size, reverse=True):
                    w.writerow([d.path, d.size, human(d.size), d.count])
            else:
                table = self.results if sel is self.search_tab else sel
                is_types = table is self.types
                w.writerow([c[0] for c in table.cols[:-1]] + ([] if is_types else ["Size (bytes)"]))
                for r in table.rows:
                    w.writerow([table.cols[i][3](r[i]) for i in range(len(table.cols) - 1)] + ([] if is_types else [r[1]]))
        self.status.set("Exported to %s" % path)


def enable_dpi():
    """Sharp text and correct sizes on high-DPI screens."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass


if __name__ == "__main__":
    enable_dpi()
    App().mainloop()
