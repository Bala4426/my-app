# StorageLens

A Windows desktop tool that shows what is using your disk, and helps you find, open and clean up files.

## Features
- Scan a drive or folder (progress bar with percentage, Stop button)
- **Folders**: expandable tree with size, % of parent and file count
- **Treemap**: coloured blocks sized by space used; click to select, double-click to drill down
- **Largest files** and **File types**
- **Search** by name, extension, minimum size and age (older than N days)
- **Duplicates**: finds identical files (size + content hash), keeps the oldest copy
- Right-click: Open, Show in Explorer, Copy path, Move to Recycle Bin (recoverable)
- **Refresh selected (F5)** rescans only the selected folder; deletes made in the tool update sizes immediately
- Dark / light mode, export to CSV

## Run
```
pip install sv-ttk pillow
python storage_lens.py
```
`sv-ttk` gives the modern theme (optional, the app falls back to the default theme without it).
`pillow` is only needed to regenerate the icon (`python create_icon.py`).

## Build a single .exe
```
pip install pyinstaller
python -m PyInstaller --onefile --noconsole --name StorageLens --icon storage_lens.ico --collect-all sv_ttk storage_lens.py
```

## Notes
- Sizes are logical file sizes (what Explorer shows as "Size"), not size on disk.
- Junctions, symlinks and cloud-only placeholders are skipped to avoid double counting.
- Run as administrator to read system folders that are otherwise skipped.
