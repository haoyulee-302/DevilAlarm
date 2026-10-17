"""惡魔鬧鐘：本機姿勢辨識與背景語音準備。"""
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
import json
import math
import queue
import random
import tempfile
import threading
import time
import tkinter as tk
from tkinter import messagebox
from display import DisplayScaling, enable_high_dpi, window_dpi
from app_paths import ASSET_DIR as BASE, SETTINGS, STATE_DIR

BG, CARD, INSET = "#0B101B", "#151D2D", "#0E1522"
TEXT, MUTED, ACCENT, GREEN = "#EDF2FA", "#8D9BB2", "#FF765E", "#B6F279"

def next_alarm(hour, minute, now=None):
    now = now or datetime.now()
    target = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
    return target if target > now else target + timedelta(days=1)

def load_settings():
    try:
        data = json.loads(SETTINGS.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        return {
            "camera": max(0, min(9, int(data.get("camera", 0)))),
            "hold": int(data.get("hold", 2)),
            "volume": max(10, min(100, float(data.get("volume", 70)))),
            "voice": data.get("voice", True) is True,
        }
    except (OSError, ValueError, TypeError, OverflowError):
        return {}

def prepare_voice(key, stop, events, session):
    """Only this worker owns temporary audio; cancellation also removes it."""
    try:
        import requests
        import edge_tts
        globals()["requests"] = requests
        lines = generate_ai_scripts(key)
        with tempfile.TemporaryDirectory(prefix="devil-alarm-") as folder:
            async def generate():
                paths = []
                for i, line in enumerate(lines):
                    if stop.is_set():
                        return []
                    path = Path(folder) / f"roast_{i}.mp3"
                    clean = "".join(c for c in line if c.isalnum() or c.isspace())[:120]
                    try:
                        speech = edge_tts.Communicate(clean, "zh-TW-HsiaoChenNeural",
                            rate=["+0%", "+25%", "+50%"][i], pitch=["+0Hz", "+5Hz", "+10Hz"][i])
                        await asyncio.wait_for(speech.save(str(path)), timeout=15)
                        paths.append(str(path))
                    except Exception:
                        cached = BASE / f"roast_{i}.mp3"
                        paths.append(str(cached) if cached.exists() else None)
                return paths
            paths = asyncio.run(generate())
            if not stop.is_set():
                events.put((session, "voice", paths))
                stop.wait()
    except Exception:
        if not stop.is_set():
            paths = [str(BASE / f"roast_{i}.mp3") if (BASE / f"roast_{i}.mp3").exists() else None for i in range(3)]
            events.put((session, "voice_fallback", paths))

def generate_ai_scripts(api_key):
    # 三個獨立的台詞庫，各自負責一個 Level（保證順序正確）
    POOL_L1 = [  # 溫柔型（假裝關心）
        "親愛的早安呢，你的枕頭有跟我說它已經膩你了喔",
        "寶貝是在做什麼夢呀，夢裡有沒有準時上班的自己呢",
        "早上好喔，我只是來看看你今天的髮型是不是叫做鳥巢",
        "你知道太陽已經出來好幾個小時了嗎，就等你一個人",
        "你繼續睡喔，反正今天的你也不屬於這個世界就是了",
        "你的被子打電話給我說他覺得你們在一起不健康",
    ]
    POOL_L2 = [  # 嘲諷型（開始酸了）
        "你睡得真香，跟你的前途一樣香消玉殞毫無動靜",
        "笑死，你是以為床是你家租來的嗎，非得住到天黑",
        "繼續躺喔，這輩子成就就這樣了，我完全理解",
        "你昨晚夢到發財了嗎，夢裡的錢不能付你今天的帳單",
        "你的鬧鐘已經叫你叫到懷疑人生，但你的人生在哪",
        "繼續睡，反正人生路那麼長，你打算繼續水平通過",
    ]
    POOL_L3 = [  # 爆炸型（完全失控）
        "你到底是要睡多久，地球都轉了幾圈你還在原地蒸發",
        "受不了了你快起來，我的耐心比你的意志力還先告終",
        "你是石頭嗎，石頭都比你有鬥志，快點給我起來",
        "再不起來我就直接把你的被子丟窗外讓風把你吹醒",
        "你有沒有搞錯，現在幾點了你自己心裡沒數嗎快起來",
        "你的懶散已超越人類極限，建議你去申請金氏世界紀錄",
    ]

    # 嘗試呼叫 Gemini（最多等 5 秒，失敗立刻走本機）
    if api_key:
        try:
            themes = ["跟床墊結婚", "夢裡中頭獎", "靈魂出竅", "世界末日", "社會底層打工仔", "超級英雄遲到"]
            chosen_theme = random.choice(themes)
            prompt = (
                f"幫我產生3句給賴床者的叫床台詞，超好笑毒舌風格，嚴禁任何標點符號跟表情符號。主題是：{chosen_theme}。"
                f"每句約20字。第1句：溫柔假裝關心但語帶威脅。第2句：嘲諷他跟床墊的關係或夢境。第3句：徹底崩潰飆罵。"
                f"【注意：絕對禁止出現任何髒話、不雅文字、或是『屎、尿、淦、屁』等字眼，要幽默且乾淨的嘴人】。"
                f"只輸出三句話，以換行分隔，不要數字前綴。"
            )
            url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"
            resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 1.2}},
                                 headers={'Content-Type': 'application/json', 'x-goog-api-key': api_key.strip()}, timeout=8)
            if resp.status_code == 200:
                lines = [l.strip().replace("*","").replace('"','').replace("'","") 
                         for l in resp.json()['candidates'][0]['content']['parts'][0]['text'].split("\n") if l.strip()]
                if len(lines) >= 3:
                    print("[系統] ✅ Gemini 台詞生成成功！")
                    return lines[:3]
        except Exception as e:
            print(f"[系統] 🎲 網路太慢，改用本機台詞庫 ({type(e).__name__})")

    # 本機庫：三個 Level 各自隨機抽一句，保證順序由溫→中→毒
    return [random.choice(POOL_L1), random.choice(POOL_L2), random.choice(POOL_L3)]


def check_standing_waving_posture(landmarks, mp_pose):
    try:
        l_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        r_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        l_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        r_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
        l_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value]
        r_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value]

        # --- 基本可見度檢查 ---
        core_visibilities = [
            l_shoulder.visibility, r_shoulder.visibility,
            l_hip.visibility, r_hip.visibility,
            l_knee.visibility, r_knee.visibility,
        ]
        if any(v < 0.5 for v in core_visibilities):
            return False, "Move Back! (Shoulders to Knees must be visible)"

        # --- 檢查 1：垂直順序（肩膀在臀部上方，臀部在膝蓋上方）---
        left_order = (l_shoulder.y < l_hip.y) and (l_hip.y < l_knee.y)
        right_order = (r_shoulder.y < r_hip.y) and (r_hip.y < r_knee.y)
        if not (left_order or right_order):
            return False, "Not standing straight! (Don't cheat!)"

        # --- 計算骨架中點 ---
        mid_shoulder_x = (l_shoulder.x + r_shoulder.x) / 2
        mid_shoulder_y = (l_shoulder.y + r_shoulder.y) / 2
        mid_hip_y = (l_hip.y + r_hip.y) / 2
        mid_knee_x = (l_knee.x + r_knee.x) / 2
        mid_knee_y = (l_knee.y + r_knee.y) / 2

        # --- 檢查 2：身體方向（垂直 vs 水平）防止躺著通過 ---
        body_vertical_span = abs(mid_knee_y - mid_shoulder_y)
        body_horizontal_span = abs(mid_knee_x - mid_shoulder_x)

        # 身體垂直跨度必須佔畫面至少 15%（躺平時 Y 軸幾乎沒有差距）
        if body_vertical_span < 0.15:
            return False, "Stand up! (Body not vertical enough)"

        # 水平跨度不應超過垂直跨度的 80%（躺著時水平 > 垂直）
        if body_horizontal_span > body_vertical_span * 0.8:
            return False, "Stand up! (You seem to be lying down)"

        # --- 檢查 3：坐姿偵測（大腿長度 vs 軀幹長度）---
        torso_len = mid_hip_y - mid_shoulder_y
        thigh_len = mid_knee_y - mid_hip_y

        if torso_len > 0 and thigh_len < torso_len * 0.3:
            return False, "Please stand up! (You seem to be sitting)"

        # --- 檢查 4：肩膀水平度（防止側躺）---
        shoulder_y_diff = abs(l_shoulder.y - r_shoulder.y)
        if shoulder_y_diff > 0.15:
            return False, "Stand straight! (Shoulders not level)"

        return True, "Perfect! You're standing!"

    except Exception as e:
        return False, f"Error: {e}"

def camera_worker(index, stop, frames, events, session, alarm=False, hold=2, volume=.7, voices=None):
    cap = pose = mixer = None
    try:
        import cv2
        if alarm:
            import pygame
            import mediapipe as mp
            if not hasattr(mp, "solutions"):
                raise RuntimeError("MediaPipe 版本不相容，請執行 setup.ps1 安裝指定版本。")
            mixer = pygame.mixer
            mixer.init()
            if not (BASE / "alarm.wav").exists():
                from generate_alarm import generate_beep
                generate_beep(str(BASE / "alarm.wav"))
            sound = mixer.Sound(str(BASE / "alarm.wav"))
            sound.set_volume(volume)
            mixer.music.set_volume(volume)
            sound.play(-1)
            pose_api = mp.solutions.pose
            pose = pose_api.Pose(min_detection_confidence=.6, min_tracking_confidence=.6)
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            raise RuntimeError(f"無法開啟攝影機 {index}。請確認 iVCam 已連線，或改選其他編號。")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        valid_since, audio_since, spoken, speaking = None, time.monotonic(), 0, False
        while not stop.is_set():
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError("攝影機影像中斷，請確認連線後重新啟動。")
            frame = cv2.flip(frame, 1)
            progress, message = 0, "預覽中 · 請讓肩膀到膝蓋進入畫面"
            if alarm:
                result = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                valid = False
                if result.pose_landmarks:
                    mp.solutions.drawing_utils.draw_landmarks(frame, result.pose_landmarks, pose_api.POSE_CONNECTIONS)
                    valid, _ = check_standing_waving_posture(result.pose_landmarks.landmark, pose_api)
                now = time.monotonic()
                valid_since = (valid_since if valid_since is not None else now) if valid else None
                progress = min(1, (now - valid_since) / hold) if valid_since is not None else 0
                message = f"保持站直 · 還有 {max(0, hold - (now - valid_since)):.1f} 秒" if valid else "請站直，讓肩膀、臀部與膝蓋完整入鏡"
                if progress >= 1:
                    events.put((session, "success", None))
                    break
                if speaking and not mixer.music.get_busy():
                    sound.play(-1)
                    speaking, audio_since = False, now
                if not speaking and now - audio_since >= 10 and spoken < len(voices):
                    path = voices[spoken]
                    spoken += 1
                    audio_since = now
                    if path:
                        try:
                            mixer.music.load(path)
                            sound.stop()
                            mixer.music.play()
                            speaking = True
                        except Exception:
                            sound.play(-1)
            height, width = frame.shape[:2]
            ratio = min(1, 1280 / width, 720 / height)
            if ratio < 1:
                frame = cv2.resize(frame, (round(width * ratio), round(height * ratio)), interpolation=cv2.INTER_AREA)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width = rgb.shape[:2]
            payload = f"P6\n{width} {height}\n255\n".encode("ascii") + rgb.tobytes()
            try:
                frames.put_nowait((session, payload, progress, message))
            except queue.Full:
                pass
            stop.wait(.035)
    except Exception as exc:
        events.put((session, "error", str(exc)))
    finally:
        if cap is not None:
            cap.release()
        if pose is not None:
            pose.close()
        if mixer is not None:
            mixer.quit()
        events.put((session, "camera_done", None))


class AlarmUI(tk.Tk):
    def __init__(self):
        enable_high_dpi()
        super().__init__()
        self.withdraw()
        self.title("惡魔鬧鐘 · DEVIL ALARM")
        if (BASE / "app.ico").exists():
            try:
                self.iconbitmap(str(BASE / "app.ico"))
            except tk.TclError:
                pass
        self.geometry("1080x780")
        self.minsize(1000, 760)
        self.configure(bg=BG)
        self.option_add("*Font", ("Microsoft JhengHei UI", 10))
        self.events, self.frames = queue.Queue(), queue.Queue(maxsize=2)
        self.session, self.target, self.active, self.previewing = 0, None, False, False
        self.camera_thread = None
        self.stop_camera, self.stop_voice = threading.Event(), threading.Event()
        self.voices = []
        self.closing = False
        settings = load_settings()
        default = datetime.now() + timedelta(minutes=1)
        self.hour = tk.StringVar(value=f"{default.hour:02d}")
        self.minute = tk.StringVar(value=f"{default.minute:02d}")
        self.camera = tk.StringVar(value=str(settings.get("camera", 0)))
        self.hold = tk.IntVar(value=settings.get("hold", 2) if settings.get("hold") in (2, 3, 5) else 2)
        self.volume = tk.DoubleVar(value=settings.get("volume", 70))
        self.voice = tk.BooleanVar(value=settings.get("voice", True))
        self.key, self.reveal = tk.StringVar(), False
        self.controls = []
        self.build_ui()
        self.display_scaling = DisplayScaling(self)
        self.last_dpi = None
        self.refresh_dpi()
        self.deiconify()
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("q", lambda event: self.cancel() if self.active else None)
        self.after(100, self.tick)

    def refresh_dpi(self):
        dpi = window_dpi(self)
        if dpi != self.last_dpi:
            self.last_dpi = dpi
            scale = min(dpi / 96, self.winfo_screenwidth() / 1120, self.winfo_screenheight() / 840)
            self.display_scaling.apply(scale)
            self.geometry(f"{round(1080 * scale)}x{round(780 * scale)}")
            self.minsize(round(1000 * scale), round(760 * scale))
        if not self.closing:
            self.after(750, self.refresh_dpi)

    def label(self, parent, text, size=11, color=TEXT, bold=False, **kw):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                        font=("Microsoft JhengHei UI", size, "bold" if bold else "normal"), **kw)

    def button(self, parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=command, bg=ACCENT if primary else "#253249",
            fg=BG if primary else TEXT, activebackground="#FF957F" if primary else "#35465F",
            activeforeground=BG if primary else TEXT, relief="flat", bd=0, cursor="hand2",
            font=("Microsoft JhengHei UI", 11, "bold"), padx=16, pady=10,
            disabledforeground=MUTED)

    def card(self, parent):
        return tk.Frame(parent, bg=CARD, highlightbackground="#243046", highlightthickness=1, padx=22, pady=18)

    def build_ui(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=32, pady=(25, 20))
        self.label(header, "◈", 30, ACCENT, True).pack(side="left", padx=(0, 12))
        brand = tk.Frame(header, bg=BG)
        brand.pack(side="left")
        self.label(brand, "惡魔鬧鐘", 23, bold=True).pack(anchor="w")
        self.label(brand, "DEVIL ALARM  /  把清醒變成一個動作", 10, MUTED).pack(anchor="w", pady=(3, 0))
        self.clock = self.label(header, "", 12, MUTED)
        self.clock.pack(side="right")
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=32)
        body.columnconfigure(0, weight=1, uniform="body")
        body.columnconfigure(1, weight=1, uniform="body")
        body.rowconfigure(0, weight=1)
        left, right = self.card(body), self.card(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.label(left, "01  /  設定你的清醒時刻", 12, bold=True).pack(anchor="w")
        self.label(left, "時間一到就響起，站直後才能完成挑戰。", 10, MUTED).pack(anchor="w", pady=(6, 22))
        timebox = tk.Frame(left, bg=INSET, pady=12)
        timebox.pack(fill="x")
        for var, limit in ((self.hour, 23), (self.minute, 59)):
            spin = tk.Spinbox(timebox, from_=0, to=limit, format="%02.0f", wrap=True, textvariable=var,
                width=3, font=("Consolas", 42, "bold"), bg=INSET, fg=TEXT, buttonbackground="#253249",
                insertbackground=ACCENT, relief="flat", justify="center", highlightthickness=0,
                disabledbackground=INSET, disabledforeground=MUTED)
            spin.pack(side="left", expand=True)
            self.controls.append(spin)
            if var is self.hour:
                self.label(timebox, ":", 36, ACCENT).pack(side="left")
        self.schedule_hint = self.label(left, "24 小時制 · 已過的時間會排到明天", 10, MUTED)
        self.schedule_hint.pack(anchor="w", pady=(9, 16))
        row = tk.Frame(left, bg=CARD)
        row.pack(fill="x")
        self.label(row, "攝影機編號", 10, MUTED).pack(side="left")
        camera = tk.Spinbox(row, from_=0, to=9, width=3, textvariable=self.camera,
            bg=INSET, fg=TEXT, buttonbackground="#253249", relief="flat", font=("Consolas", 13),
            disabledbackground=INSET, disabledforeground=MUTED)
        camera.pack(side="right")
        self.controls.append(camera)
        self.preview_btn = self.button(left, "◎  測試攝影機", self.preview)
        self.preview_btn.pack(fill="x", pady=(10, 15))
        row = tk.Frame(left, bg=CARD)
        row.pack(fill="x")
        self.label(row, "站直解鎖", 10, MUTED).pack(side="left", padx=(0, 12))
        for seconds in (2, 3, 5):
            radio = tk.Radiobutton(row, text=f"{seconds} 秒", variable=self.hold, value=seconds,
                bg=CARD, fg=TEXT, selectcolor=INSET, activebackground=CARD, activeforeground=GREEN,
                disabledforeground=MUTED)
            radio.pack(side="left")
            self.controls.append(radio)
        volume_row = tk.Frame(left, bg=CARD)
        volume_row.pack(fill="x", pady=(12, 4))
        self.label(volume_row, "鬧鐘音量", 10, MUTED).pack(side="left")
        scale = tk.Scale(volume_row, from_=10, to=100, orient="horizontal", variable=self.volume,
            bg=CARD, fg=MUTED, troughcolor=INSET, highlightthickness=0, bd=0,
            activebackground=ACCENT, length=235, sliderrelief="flat")
        scale.pack(side="right")
        self.controls.append(scale)
        check = tk.Checkbutton(left, text="啟用 AI 吐槽語音", variable=self.voice, bg=CARD, fg=TEXT,
            selectcolor=INSET, activebackground=CARD, activeforeground=TEXT, disabledforeground=MUTED)
        check.pack(anchor="w", pady=(12, 5))
        self.controls.append(check)
        keyrow = tk.Frame(left, bg=CARD)
        keyrow.pack(fill="x")
        entry = tk.Entry(keyrow, textvariable=self.key, show="●", bg=INSET, fg=TEXT,
            insertbackground=ACCENT, relief="flat", font=("Consolas", 11),
            disabledbackground=INSET, disabledforeground=MUTED)
        entry.pack(side="left", fill="x", expand=True, ipady=8)
        self.controls.append(entry)
        def reveal():
            self.reveal = not self.reveal
            entry.configure(show="" if self.reveal else "●")
        self.button(keyrow, "顯示", reveal).pack(side="right", padx=(6, 0))
        self.label(left, "Gemini Key 選填 · 留白使用本機台詞 · 金鑰不儲存", 9, MUTED).pack(anchor="w", pady=(7, 0))
        self.label(right, "02  /  清醒任務", 12, bold=True).pack(anchor="w")
        self.badge = self.label(right, "●  尚未排程", 10, GREEN)
        self.badge.pack(anchor="w", pady=(9, 12))
        self.preview_label = tk.Label(right, bg=INSET, fg=MUTED, text="◎\n\n站起來，迎接新的一天\n\n點擊「測試攝影機」確認取景",
            font=("Microsoft JhengHei UI", 12), width=44, height=15)
        self.preview_label.pack(fill="both", expand=True)
        self.progress_canvas = tk.Canvas(right, height=5, bg=INSET, highlightthickness=0)
        self.progress_canvas.pack(fill="x", pady=(16, 10))
        self.progress_rect = self.progress_canvas.create_rectangle(0, 0, 0, 5, fill=GREEN, outline="")
        self.pose_label = self.label(right, "肩膀 → 臀部 → 膝蓋，請完整入鏡", 10, MUTED, wraplength=420)
        self.pose_label.pack(anchor="w")
        self.countdown = self.label(right, "等待設定", 28, bold=True)
        self.countdown.pack(anchor="w", pady=(16, 3))
        self.status = self.label(right, "先測試取景，再啟動你的起床挑戰。", 10, MUTED, wraplength=420, justify="left")
        self.status.pack(anchor="w")
        footer = tk.Frame(self, bg=BG)
        footer.pack(fill="x", padx=32, pady=20)
        self.label(footer, "影像僅在本機辨識\n程式需保持開啟，電腦需保持喚醒", 9, MUTED, justify="left").pack(side="left")
        self.cancel_btn = self.button(footer, "取消排程", self.cancel)
        self.cancel_btn.pack(side="right", padx=(10, 0))
        self.cancel_btn.configure(state="disabled")
        self.start_btn = self.button(footer, "啟動鬧鐘  →", self.arm, True)
        self.start_btn.pack(side="right")

    def camera_busy(self):
        return self.camera_thread is not None and self.camera_thread.is_alive()

    def validate(self):
        try:
            hour, minute, camera = int(self.hour.get()), int(self.minute.get()), int(self.camera.get())
            if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= camera <= 9):
                raise ValueError
            return hour, minute, camera
        except ValueError:
            messagebox.showerror("設定不完整", "時間需為 00:00–23:59，攝影機編號需為 0–9。", parent=self)

    def preview(self):
        if self.previewing:
            self.stop_camera.set()
            self.preview_btn.configure(text="正在關閉…", state="disabled")
            return
        values = self.validate()
        if not values or self.camera_busy():
            return
        self.session += 1
        self.previewing = True
        self.stop_camera = threading.Event()
        self.camera_thread = threading.Thread(target=camera_worker,
            args=(values[2], self.stop_camera, self.frames, self.events, self.session), daemon=True)
        self.camera_thread.start()
        self.preview_btn.configure(text="停止預覽")
        self.start_btn.configure(state="disabled")
        self.status.configure(text="正在連接攝影機…")

    def arm(self):
        values = self.validate()
        if not values or self.camera_busy():
            return
        self.session += 1
        self.target = next_alarm(*values[:2])
        self.active = False
        self.voices = []
        self.stop_voice = threading.Event()
        for control in self.controls:
            control.configure(state="disabled")
        self.start_btn.configure(state="disabled")
        self.preview_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal", text="取消排程")
        self.badge.configure(text="●  排程已啟動", fg=GREEN)
        self.schedule_hint.configure(text=self.target.strftime("預定響鈴  %m/%d  %H:%M"))
        self.status.configure(text="排程已生效，語音在背景準備中…" if self.voice.get() else "排程已生效，到時播放鬧鐘提示音。")
        settings = dict(camera=values[2], hold=self.hold.get(), volume=self.volume.get(), voice=self.voice.get())
        try:
            SETTINGS.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            self.status.configure(text="排程已生效；偏好設定無法寫入。")
        if self.voice.get():
            threading.Thread(target=prepare_voice, args=(self.key.get().strip(), self.stop_voice,
                             self.events, self.session), daemon=True).start()

    def ring(self):
        self.active = True
        self.stop_camera = threading.Event()
        self.badge.configure(text="●  鬧鐘響起 · 站直解鎖", fg=ACCENT)
        self.cancel_btn.configure(text="停止鬧鐘")
        self.countdown.configure(text="起床時間到了", fg=ACCENT)
        self.lift()
        self.bell()
        self.camera_thread = threading.Thread(target=camera_worker, args=(int(self.camera.get()),
            self.stop_camera, self.frames, self.events, self.session, True, self.hold.get(),
            self.volume.get() / 100, self.voices), daemon=True)
        self.camera_thread.start()

    def cancel(self, success=False):
        self.target = None
        self.active = False
        self.stop_camera.set()
        self.stop_voice.set()
        self.cancel_btn.configure(state="disabled", text="取消排程")
        self.badge.configure(text="●  挑戰完成" if success else "●  已取消", fg=GREEN if success else MUTED)
        self.countdown.configure(text="早安，挑戰成功！" if success else "等待設定", fg=GREEN if success else TEXT)
        self.status.configure(text="你已完成站姿挑戰，開始新的一天吧。" if success else "可重新設定下一個鬧鐘。")
        if not self.camera_busy():
            self.unlock_controls()

    def unlock_controls(self):
        for control in self.controls:
            control.configure(state="normal")
        self.start_btn.configure(state="normal")
        self.preview_btn.configure(state="normal", text="◎  測試攝影機")

    def tick(self):
        if self.closing:
            return
        now = datetime.now()
        self.clock.configure(text=now.strftime("%Y.%m.%d  /  %H:%M:%S"))
        if self.target and not self.active:
            remaining = max(0, math.ceil((self.target - now).total_seconds()))
            self.countdown.configure(text=f"{remaining//3600:02d} : {remaining//60%60:02d} : {remaining%60:02d}", fg=TEXT)
            if now >= self.target:
                self.ring()
        for _ in range(20):
            try:
                session, kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if session != self.session:
                continue
            if kind in ("voice", "voice_fallback") and self.target:
                self.voices[:] = value
                self.status.configure(text="語音已備妥，等待起床挑戰。" if kind == "voice" and all(value) else "語音部分或全部使用快取；提示音會照常響起。")
            elif kind == "success" and self.active:
                self.cancel(success=True)
            elif kind == "error":
                self.cancel()
                self.badge.configure(text="●  裝置尚未就緒", fg=ACCENT)
                self.status.configure(text=value)
                messagebox.showerror("無法啟動攝影機或音效", value, parent=self)
            elif kind == "camera_done":
                self.previewing = False
                self.after(80, self.camera_finished)
        latest = None
        for _ in range(3):
            try:
                candidate = self.frames.get_nowait()
                if candidate[0] == self.session and not self.stop_camera.is_set():
                    latest = candidate
            except queue.Empty:
                break
        if latest:
            _, pixels, progress, message = latest
            from io import BytesIO
            from PIL import Image, ImageOps, ImageTk
            source = Image.open(BytesIO(pixels))
            available = (max(1, self.preview_label.winfo_width()), max(1, self.preview_label.winfo_height()))
            fitted = ImageOps.contain(source, available, Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(fitted, master=self)
            self.preview_label.configure(image=self.photo, text="", width=1, height=1)
            self.pose_label.configure(text=message, fg=GREEN if progress else MUTED)
            self.progress_canvas.coords(self.progress_rect, 0, 0,
                self.progress_canvas.winfo_width() * progress, self.progress_canvas.winfo_height())
        self.after(100, self.tick)

    def camera_finished(self):
        if self.closing:
            return
        if self.camera_busy():
            self.after(100, self.camera_finished)
            return
        if self.target is None:
            self.unlock_controls()
        self.preview_label.configure(image="", text="◎\n\n攝影機已關閉\n\n點擊「測試攝影機」確認取景", width=44, height=15)
        self.pose_label.configure(text="肩膀 → 臀部 → 膝蓋，請完整入鏡", fg=MUTED)
        self.progress_canvas.coords(self.progress_rect, 0, 0, 0, 5)

    def close(self):
        self.closing = True
        self.stop_camera.set()
        self.stop_voice.set()
        for callback in self.tk.splitlist(self.tk.call('after', 'info')):
            self.after_cancel(callback)
        self.destroy()


def main():
    AlarmUI().mainloop()


if __name__ == "__main__":
    main()
