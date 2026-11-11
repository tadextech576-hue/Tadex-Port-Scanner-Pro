"""Tadex Port Scanner Pro - Android/Kivy interface."""
import csv
import json
import os
import queue
import threading
import time
from datetime import datetime
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from scanner import scan_ports

BG = (0.035, 0.055, 0.09, 1)
PANEL = (0.07, 0.10, 0.16, 1)
GREEN = (0.20, 0.85, 0.55, 1)
RED = (1, 0.30, 0.34, 1)
TEXT = (0.91, 0.95, 1, 1)
MUTED = (0.58, 0.67, 0.78, 1)

class PortScannerApp(App):
    def build(self):
        self.title = "Tadex Port Scanner Pro"
        Window.clearcolor = BG
        self.cancel_event = threading.Event()
        self.events = queue.Queue()
        self.results = []
        self.scanning = False
        self.started_at = None
        root = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(9))
        header = BoxLayout(size_hint_y=None, height=dp(60), orientation="vertical", spacing=dp(2))
        header.add_widget(Label(text="[b]TADEX[/b]  PORT SCANNER PRO", markup=True, color=GREEN, font_size="21sp", halign="left"))
        header.add_widget(Label(text="REAL TCP CONNECT SCANNER  •  ANDROID", color=MUTED, font_size="10sp", halign="left"))
        root.add_widget(header)
        form = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(270), padding=dp(10), spacing=dp(7))
        form.add_widget(self.heading("TARGET"))
        self.target = self.field("IP address or hostname (e.g. 127.0.0.1)")
        form.add_widget(self.target)
        ports = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        self.start_port = self.field("Start port", "1", input_filter="int")
        self.end_port = self.field("End port", "1024", input_filter="int")
        ports.add_widget(self.start_port)
        ports.add_widget(self.end_port)
        form.add_widget(ports)
        settings = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        self.timeout = Spinner(text="Timeout 0.8s", values=("Timeout 0.3s", "Timeout 0.8s", "Timeout 1.5s", "Timeout 3s"), background_color=PANEL, color=TEXT)
        self.workers = Spinner(text="64 workers", values=("16 workers", "32 workers", "64 workers", "100 workers"), background_color=PANEL, color=TEXT)
        settings.add_widget(self.timeout)
        settings.add_widget(self.workers)
        form.add_widget(settings)
        actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        self.start_btn = Button(text="START SCAN", background_color=GREEN, color=(0.02,0.06,0.08,1), bold=True, on_release=self.start_scan)
        self.stop_btn = Button(text="STOP", background_color=RED, color=TEXT, on_release=self.stop_scan, disabled=True)
        actions.add_widget(self.start_btn)
        actions.add_widget(self.stop_btn)
        form.add_widget(actions)
        root.add_widget(form)
        self.status = Label(text="Ready • Scan only systems you own or have permission to test.", color=MUTED, size_hint_y=None, height=dp(34), font_size="12sp")
        root.add_widget(self.status)
        self.summary = Label(text="OPEN  0       CLOSED  0       OTHER  0", color=GREEN, size_hint_y=None, height=dp(30), bold=True)
        root.add_widget(self.summary)
        export_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        export_row.add_widget(self.small_button("EXPORT CSV", self.export_csv))
        export_row.add_widget(self.small_button("EXPORT JSON", self.export_json))
        export_row.add_widget(self.small_button("CLEAR", self.clear_results))
        root.add_widget(export_row)
        self.results_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
        self.results_box.bind(minimum_height=self.results_box.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.results_box)
        root.add_widget(scroll)
        Clock.schedule_interval(self.poll_events, 0.15)
        return root

    def heading(self, text):
        return Label(text=text, color=GREEN, bold=True, size_hint_y=None, height=dp(22), halign="left")

    def field(self, hint, value="", **kwargs):
        return TextInput(hint_text=hint, text=value, multiline=False, size_hint_y=None, height=dp(44),
                         padding=(dp(10), dp(12)), background_color=PANEL, foreground_color=TEXT,
                         hint_text_color=MUTED, cursor_color=GREEN, **kwargs)

    def small_button(self, text, callback):
        return Button(text=text, on_release=callback, background_color=PANEL, color=TEXT)

    def start_scan(self, *_):
        if self.scanning:
            return
        target = self.target.text.strip()
        try:
            first, last = int(self.start_port.text), int(self.end_port.text)
            timeout = float(self.timeout.text.split()[1].rstrip("s"))
            workers = int(self.workers.text.split()[0])
            if not target or not (1 <= first <= last <= 65535):
                raise ValueError
        except (ValueError, IndexError):
            self.status.text = "Enter a target and valid port range (1–65535)."
            self.status.color = RED
            return
        self.results = []
        self.results_box.clear_widgets()
        self.cancel_event.clear()
        self.scanning = True
        self.started_at = time.time()
        self.start_btn.disabled = True
        self.stop_btn.disabled = False
        self.status.text = "Resolving target and scanning…"
        self.status.color = GREEN
        threading.Thread(target=self.worker, args=(target, first, last, timeout, workers), daemon=True).start()

    def worker(self, target, first, last, timeout, workers):
        try:
            for result in scan_ports(target, first, last, timeout, workers, self.cancel_event,
                                     on_progress=lambda done, total: self.events.put(("progress", done, total))):
                self.events.put(("result", result))
            self.events.put(("finished", self.cancel_event.is_set(), None))
        except Exception as exc:
            self.events.put(("error", str(exc), None))

    def stop_scan(self, *_):
        self.cancel_event.set()
        self.status.text = "Stopping scan…"

    def poll_events(self, _dt):
        while True:
            try:
                kind, value, extra = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == "result":
                self.results.append(value)
                color = GREEN if value.status == "open" else RED if value.status == "closed" else MUTED
                row = Label(text=f"{value.port:<6} {value.status:<24} {value.service}", color=color,
                            size_hint_y=None, height=dp(25), font_size="12sp", halign="left")
                self.results_box.add_widget(row)
                self.update_summary()
            elif kind == "progress":
                self.status.text = f"Scanning… {value}/{extra} ports checked"
            elif kind == "finished":
                self.finish_scan("Scan cancelled." if value else "Scan completed.")
            elif kind == "error":
                self.finish_scan("Error: " + value, error=True)

    def update_summary(self):
        opened = sum(r.status == "open" for r in self.results)
        closed = sum(r.status == "closed" for r in self.results)
        other = len(self.results) - opened - closed
        self.summary.text = f"OPEN  {opened}       CLOSED  {closed}       OTHER  {other}"

    def finish_scan(self, message, error=False):
        self.scanning = False
        self.start_btn.disabled = False
        self.stop_btn.disabled = True
        elapsed = time.time() - self.started_at if self.started_at else 0
        self.status.text = f"{message}  ({elapsed:.1f}s)"
        self.status.color = RED if error else GREEN

    def clear_results(self, *_):
        if self.scanning:
            self.status.text = "Stop the scan before clearing results."
            return
        self.results = []
        self.results_box.clear_widgets()
        self.update_summary()
        self.status.text = "Results cleared."

    def export_rows(self):
        if not self.results:
            self.status.text = "No results to export yet."
            return None
        folder = self.user_data_dir
        os.makedirs(folder, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return folder, stamp

    def export_csv(self, *_):
        info = self.export_rows()
        if not info:
            return
        folder, stamp = info
        path = os.path.join(folder, f"tadex_scan_{stamp}.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["host", "ip", "port", "status", "service", "response_ms"])
            for r in self.results:
                writer.writerow([r.host, r.ip, r.port, r.status, r.service, r.response_ms])
        self.status.text = "CSV saved: " + path

    def export_json(self, *_):
        info = self.export_rows()
        if not info:
            return
        folder, stamp = info
        path = os.path.join(folder, f"tadex_scan_{stamp}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump([r.__dict__ for r in self.results], f, indent=2)
        self.status.text = "JSON saved: " + path

if __name__ == "__main__":
    PortScannerApp().run()
