from PIL import Image, ImageDraw, ImageFont
from datetime import date, datetime, timedelta
import calendar
import ctypes
import os
import sys
import tkinter as tk
from tkinter import messagebox

# ===================== CONFIG =====================

YEAR = 2026
MAX_CHECKPOINTS = 10

SCREEN_WIDTH  = 1920
SCREEN_HEIGHT = 1080
TASKBAR_SAFE  = 120

MONTH_COLS = 4
MONTH_ROWS = 3

BOX = 26
GAP = 6

TOP_MARGIN  = 200
SIDE_MARGIN = 80
MONTH_GAP_X = 40
MONTH_GAP_Y = 70

# Files
CHECKPOINT_FILE = "checkpoints.txt"
PRODUCTIVE_FILE = "productive_days.txt"

# Colors
BG_COLOR         = "#020617"
PAST_COLOR       = "#4ade80"
FUTURE_COLOR     = "#0b1220"
EMPTY_COLOR      = "#020617"
CHECKPOINT_COLOR = "#fbbf24"
PRODUCTIVE_COLOR = "#38bdf8"
TODAY_OUTLINE    = "#22c55e"

TEXT_MAIN        = "#e5e7eb"
TEXT_MUTED       = "#94a3b8"

YEAR_NOTE = "CONSISTENCY > INTENSITY"

# =================================================

calendar.setfirstweekday(calendar.MONDAY)
today = date.today()
yesterday = today - timedelta(days=1)

# ===================== STORAGE =====================

def load_productive_days():
    days = set()
    if os.path.exists(PRODUCTIVE_FILE):
        with open(PRODUCTIVE_FILE, "r") as f:
            for line in f:
                try:
                    days.add(datetime.strptime(line.strip(), "%Y-%m-%d").date())
                except:
                    pass
    return days

def save_productive_day(d):
    with open(PRODUCTIVE_FILE, "a") as f:
        f.write(d.strftime("%Y-%m-%d") + "\n")

def load_checkpoints():
    cps = []
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    d, name = line.strip().split("|", 1)
                    cps.append({"date": datetime.strptime(d, "%Y-%m-%d").date(), "name": name})
                except:
                    pass
    return cps

def save_checkpoints(cps):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        for cp in cps:
            f.write(f"{cp['date']}|{cp['name']}\n")

# ===================== CHECKPOINT GUI =====================

def edit_checkpoints():
    checkpoints = []

    def submit():
        checkpoints.clear()
        for n, d in rows:
            name = n.get().strip()
            date_str = d.get().strip()
            if not name or not date_str:
                continue
            try:
                cp_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                checkpoints.append({"name": name, "date": cp_date})
            except:
                messagebox.showerror("Error", f"Invalid date: {date_str}")
                return
        save_checkpoints(checkpoints)
        root.destroy()

    root = tk.Tk()
    root.title("Edit Checkpoints")
    root.geometry("640x520")
    root.resizable(False, False)

    tk.Label(root, text="Checkpoint Name", font=("Arial", 11, "bold")).grid(row=0, column=0, padx=20, pady=15, sticky="w")
    tk.Label(root, text="Date (YYYY-MM-DD)", font=("Arial", 11, "bold")).grid(row=0, column=1, padx=20, pady=15, sticky="w")

    rows = []
    existing = load_checkpoints()

    for i in range(MAX_CHECKPOINTS):
        n = tk.Entry(root, width=34)
        d = tk.Entry(root, width=20)
        if i < len(existing):
            n.insert(0, existing[i]["name"])
            d.insert(0, existing[i]["date"].strftime("%Y-%m-%d"))
        n.grid(row=i+1, column=0, padx=20, pady=6, sticky="w")
        d.grid(row=i+1, column=1, padx=20, pady=6, sticky="w")
        rows.append((n, d))

    tk.Button(root, text="Save", font=("Arial", 12, "bold"), command=submit).grid(
        row=MAX_CHECKPOINTS+1, column=0, columnspan=2, pady=30
    )

    root.mainloop()

# ===================== MODE =====================

if "--edit-checkpoints" in sys.argv or not os.path.exists(CHECKPOINT_FILE):
    edit_checkpoints()

checkpoints = load_checkpoints()
productive_days = load_productive_days()

# ===================== DAILY PRODUCTIVITY PROMPT =====================

if yesterday not in productive_days:
    root = tk.Tk()
    root.withdraw()
    ans = messagebox.askyesno("Daily Reflection", "Was yesterday productive?")
    root.destroy()
    if ans:
        productive_days.add(yesterday)
        save_productive_day(yesterday)

# ===================== WALLPAPER =====================

img = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), BG_COLOR)
draw = ImageDraw.Draw(img)

try:
    font_big   = ImageFont.truetype("arial.ttf", 72)
    font_mid   = ImageFont.truetype("arial.ttf", 28)
    font_small = ImageFont.truetype("arial.ttf", 22)
    font_month = ImageFont.truetype("arial.ttf", 24)
except:
    font_big = font_mid = font_small = font_month = ImageFont.load_default()

# -------- STATS --------

start_date = date(YEAR, 1, 1)
passed = max(0, min((today - start_date).days + 1, 365))
remaining = 365 - passed

num_width = draw.textbbox((0, 0), str(passed), font=font_big)[2]
draw.text((SIDE_MARGIN, 40), str(passed), fill=TEXT_MAIN, font=font_big)
draw.text((SIDE_MARGIN + num_width + 12, 58), "days passed", fill=TEXT_MUTED, font=font_mid)
draw.text((SIDE_MARGIN, 120), f"{remaining} days remaining", fill=TEXT_MUTED, font=font_mid)
draw.text((SIDE_MARGIN, 155), f"Ends on 31 Dec {YEAR}", fill=TEXT_MUTED, font=font_mid)

weekday_str = today.strftime("%A")
date_str    = today.strftime("%d %B %Y")

base_y = 155

draw.text((SIDE_MARGIN, base_y + 40), weekday_str, fill=TEXT_MAIN, font=font_mid)
draw.text((SIDE_MARGIN, base_y + 70), date_str, fill=TEXT_MUTED, font=font_small)


# -------- CALENDAR --------

month_w = 7 * BOX + 6 * GAP
month_h = 6 * BOX + 5 * GAP
total_w = MONTH_COLS * month_w + (MONTH_COLS - 1) * MONTH_GAP_X

start_x = (SCREEN_WIDTH - total_w) // 2
start_y = TOP_MARGIN

cp_dates = {c["date"]: c for c in checkpoints}

for m in range(1, 13):
    r = (m-1)//MONTH_COLS
    c = (m-1)%MONTH_COLS
    x0 = start_x + c*(month_w+MONTH_GAP_X)
    y0 = start_y + r*(month_h+MONTH_GAP_Y)

    draw.text((x0, y0-30), calendar.month_name[m], fill=TEXT_MAIN, font=font_month)

    for w, week in enumerate(calendar.monthcalendar(YEAR, m)):
        for d, day in enumerate(week):
            if day == 0: continue
            cur = date(YEAR, m, day)

            x1 = x0 + d*(BOX+GAP)
            y1 = y0 + w*(BOX+GAP)
            x2 = x1 + BOX
            y2 = y1 + BOX

            if cur in productive_days:
                color = PRODUCTIVE_COLOR
            elif cur in cp_dates:
                color = CHECKPOINT_COLOR
            elif cur <= today:
                color = PAST_COLOR
            else:
                color = FUTURE_COLOR

            draw.rounded_rectangle([x1,y1,x2,y2], radius=6, fill=color)

            if cur == today:
                draw.rounded_rectangle([x1-2,y1-2,x2+2,y2+2], radius=8, outline=TODAY_OUTLINE, width=2)

# -------- CHECKPOINT PANEL --------

right_x = start_x + total_w + 80
right_y = TOP_MARGIN + 10

future = [c for c in checkpoints if (c["date"] - today).days >= 0]
nearest = min(future, key=lambda c:(c["date"]-today).days, default=None)

if checkpoints:
    draw.text((right_x, right_y-48), "Checkpoints", fill=TEXT_MAIN, font=font_mid)
    off = 0
    for cp in sorted(checkpoints, key=lambda c:c["date"]):
        delta = (cp["date"] - today).days
        if delta < 0: continue
        label = "Today" if delta==0 else "Tomorrow" if delta==1 else f"{delta} days left"
        draw.text((right_x, right_y+off), cp["name"], fill=TEXT_MAIN, font=font_mid)
        draw.text((right_x, right_y+off+30), label, fill=TEXT_MUTED, font=font_small)
        off += 78

# -------- FOOTER NOTE --------

draw.text((SIDE_MARGIN, SCREEN_HEIGHT - TASKBAR_SAFE - 60), YEAR_NOTE, fill=TEXT_MUTED, font=font_mid)

# -------- SAVE --------

path = os.path.join(os.getcwd(), "calendar_wallpaper.png")
img.save(path)
ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)

print("Wallpaper updated successfully.")
