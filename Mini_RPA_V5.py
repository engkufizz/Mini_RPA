#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import pyautogui
import threading
import time
import json
import sys
import keyboard

class MiniRPA_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini RPA Tool v3.2")
        self.root.geometry("600x500")
        
        # Default settings and flags
        self.delay_between_actions = 0.3
        self.automation_sequence = []  # Recorded (or loaded) automation steps
        self.stop_automation = False
        self.automation_esc_hotkey = None  # Hotkey used to cancel automation during playback
        self.is_dialog_open = False         # Prevent multiple input dialogs at once
        self.in_setup_mode = False          # True when recording a sequence
        
        # Variables for grouping rapid clicks (for single, double, triple clicks, etc.)
        self.click_buffer_count = 0
        self.last_click_time = 0
        self.click_buffer_after_id = None
        
        self.create_gui()
        self.setup_error_handling()
    
    def create_gui(self):
        # Main frame—with padding around the main contents.
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(expand=True, fill="both")
        
        # Title label.
        title_label = tk.Label(main_frame, text="Mini RPA Tool", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Progress/Status label. This tells the user the current mode.
        self.progress_label = tk.Label(main_frame, text="Ready", font=("Arial", 12))
        self.progress_label.pack(pady=(0, 10))
        
        # --- Buttons arranged vertically ---
        # Big colored button for Setup Automation.
        self.setup_button = tk.Button(main_frame, text="Setup Automation", command=self.setup_automation,
                                      font=("Arial", 12), bg="#3498db", fg="white", width=20, height=2)
        self.setup_button.pack(pady=5)
        
        # Big colored button for Start Automation.
        self.start_button = tk.Button(main_frame, text="Start Automation", command=self.start_automation,
                                      font=("Arial", 12), bg="#2ecc71", fg="white", width=20, height=2)
        self.start_button.pack(pady=5)
        
        # Colorless (default themed) button for Load Sequence.
        self.load_button = ttk.Button(main_frame, text="Load Sequence", command=self.load_automation_sequence)
        self.load_button.pack(pady=5)
        
        # Listbox to display the recorded/loaded automation sequence.
        listbox_label = tk.Label(main_frame, text="Recorded/Loaded Automation Sequence:", font=("Arial", 12))
        listbox_label.pack(pady=(15, 5))
        self.sequence_listbox = tk.Listbox(main_frame, width=70, height=10)
        self.sequence_listbox.pack(fill="both", expand=True)
        
        # A status bar at the very bottom.
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor="w")
        status_bar.pack(side="bottom", fill="x")
    
    def setup_error_handling(self):
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = self.delay_between_actions
    
    def handle_error(self, error, action=None):
        error_msg = f"Error during automation: {str(error)}"
        self.status_var.set(error_msg)
        messagebox.showerror("Automation Error", error_msg, parent=self.root)
    
    # ───────────── Setup Automation (Recording) ─────────────
    def setup_automation(self):
        # Activate setup mode and clear any previous sequence.
        self.in_setup_mode = True
        self.automation_sequence = []
        self.sequence_listbox.delete(0, tk.END)
        self.progress_label.config(text="Setup mode active.")
        self.register_setup_hotkeys()
    
    def register_setup_hotkeys(self):
        # Global hotkeys (active even when application is unfocused) used during setup.
        self.hotkeys = {
            'space': keyboard.add_hotkey('space', lambda: self.handle_setup_key('space')),
            'd':     keyboard.add_hotkey('d',     lambda: self.handle_setup_key('d')),
            't':     keyboard.add_hotkey('t',     lambda: self.handle_setup_key('t')),
            'k':     keyboard.add_hotkey('k',     lambda: self.handle_setup_key('k')),
            'esc':   keyboard.add_hotkey('esc',   lambda: self.handle_setup_key('esc'))
        }
    
    def remove_setup_hotkeys(self):
        if hasattr(self, 'hotkeys'):
            for hotkey in self.hotkeys.values():
                try:
                    hotkey()  # Calling the removal function unregisters the hotkey.
                except Exception:
                    pass
            self.hotkeys.clear()
    
    def handle_setup_key(self, key):
        # For keys D, T, and K, ignore if an input dialog is already open.
        if key in ['d', 't', 'k'] and self.is_dialog_open:
            return
        self.root.after(0, self.process_setup_key, key)
    
    def process_setup_key(self, key):
        if key == 'esc':
            self.finish_setup()
        elif key == 'space':
            self.record_click_action()
        elif key == 'd':
            self.record_delay_action()
        elif key == 't':
            self.record_text_action()
        elif key == 'k':
            self.record_key_action()
    
    def record_click_action(self):
        now = time.time()
        threshold = 0.3  # Seconds to group rapid clicks.
        pos = pyautogui.position()
        if self.click_buffer_count > 0 and (now - self.last_click_time < threshold):
            self.click_buffer_count += 1
            if self.automation_sequence:
                self.automation_sequence.pop()
            if self.sequence_listbox.size() > 0:
                self.sequence_listbox.delete(tk.END)
            action = {
                "type": "multi_click",
                "x": pos[0],
                "y": pos[1],
                "count": self.click_buffer_count,
                "description": f"{self.click_buffer_count} clicks at ({pos[0]}, {pos[1]})"
            }
            self.automation_sequence.append(action)
            self.sequence_listbox.insert(tk.END, action["description"])
            self.last_click_time = now
            if self.click_buffer_after_id:
                self.root.after_cancel(self.click_buffer_after_id)
            self.click_buffer_after_id = self.root.after(int(threshold * 1000), self.finalize_click_buffer)
        else:
            self.click_buffer_count = 1
            self.last_click_time = now
            action = {
                "type": "multi_click",
                "x": pos[0],
                "y": pos[1],
                "count": self.click_buffer_count,
                "description": f"{self.click_buffer_count} click at ({pos[0]}, {pos[1]})"
            }
            self.automation_sequence.append(action)
            self.sequence_listbox.insert(tk.END, action["description"])
            if self.click_buffer_after_id:
                self.root.after_cancel(self.click_buffer_after_id)
            self.click_buffer_after_id = self.root.after(int(threshold * 1000), self.finalize_click_buffer)
    
    def finalize_click_buffer(self):
        self.click_buffer_count = 0
        self.click_buffer_after_id = None
    
    def record_delay_action(self):
        if self.is_dialog_open:
            return
        try:
            self.is_dialog_open = True
            delay = simpledialog.askfloat("Delay Action", "Enter delay in seconds:", parent=self.root)
            if delay is not None:
                action = {"type": "wait", "delay": delay, "description": f"Wait for {delay} sec"}
                self.automation_sequence.append(action)
                self.sequence_listbox.insert(tk.END, action["description"])
        finally:
            self.is_dialog_open = False
    
    def record_text_action(self):
        if self.is_dialog_open:
            return
        try:
            self.is_dialog_open = True
            text = simpledialog.askstring("Text Action", "Enter text to type:", parent=self.root)
            if text is not None:
                action = {"type": "text", "text": text, "description": f"Type text: {text}"}
                self.automation_sequence.append(action)
                self.sequence_listbox.insert(tk.END, action["description"])
        finally:
            self.is_dialog_open = False
    
    def record_key_action(self):
        if self.is_dialog_open:
            return
        try:
            self.is_dialog_open = True
            key_value = simpledialog.askstring("Key Press Action",
                                               "Enter key to press (e.g., 'a', 'enter', 'space'):",
                                               parent=self.root)
            if key_value is not None:
                action = {"type": "key", "key": key_value, "description": f"Press key: {key_value}"}
                self.automation_sequence.append(action)
                self.sequence_listbox.insert(tk.END, action["description"])
        finally:
            self.is_dialog_open = False
    
    def finish_setup(self):
        if not self.in_setup_mode:
            return
        self.in_setup_mode = False
        self.remove_setup_hotkeys()
        self.progress_label.config(text="Setup Complete! You can now start automation.")
        self.status_var.set("Setup complete.")
        # Prompt user to save the recorded sequence.
        self.save_automation_sequence()
    
    def save_automation_sequence(self):
        save_path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save Automation Sequence",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if save_path:
            try:
                with open(save_path, "w") as fp:
                    json.dump(self.automation_sequence, fp, indent=4)
                messagebox.showinfo("Success", f"Automation sequence saved to:\n{save_path}", parent=self.root)
            except Exception as e:
                self.handle_error(e)
    
    # ───────────── Loading & Starting Automation ─────────────
    def load_automation_sequence(self):
        # Allow the user to load a predefined sequence from a JSON file.
        sequence_path = filedialog.askopenfilename(
            title="Select Automation Sequence",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if sequence_path:
            try:
                with open(sequence_path, "r") as fp:
                    self.automation_sequence = json.load(fp)
                self.sequence_listbox.delete(0, tk.END)
                for action in self.automation_sequence:
                    self.sequence_listbox.insert(tk.END, action.get("description", "No description"))
                self.progress_label.config(text="Sequence loaded. Ready to start automation.")
                self.status_var.set("Sequence loaded.")
            except Exception as e:
                self.handle_error(e)
    
    def start_automation(self):
        if not self.automation_sequence:
            messagebox.showerror("Error", "No automation sequence found.\nPlease use Setup or Load a sequence.", parent=self.root)
            return
        self.stop_automation = False
        self.progress_label.config(text="Automation will start in 5 seconds.\nSwitch to target window. (Press ESC to cancel)")
        self.status_var.set("Automation starting in 5 seconds...")
        self.automation_esc_hotkey = keyboard.add_hotkey('esc', self.request_stop_automation)
        threading.Thread(target=self.run_automation, args=(self.automation_sequence,), daemon=True).start()
    
    def request_stop_automation(self):
        self.stop_automation = True
    
    def run_automation(self, sequence):
        try:
            time.sleep(5)  # Delay to allow switching to the target window.
            for index, action in enumerate(sequence, start=1):
                if self.stop_automation:
                    break
                self.execute_action(action, index)
        finally:
            self.cleanup_automation()
    
    def execute_action(self, action, index):
        try:
            if action["type"] == "multi_click":
                if action["count"] == 1:
                    pyautogui.click(x=action["x"], y=action["y"])
                else:
                    pyautogui.click(x=action["x"], y=action["y"], clicks=action["count"], interval=0.1)
            elif action["type"] == "wait":
                time.sleep(action["delay"])
            elif action["type"] == "text":
                pyautogui.write(action["text"])
            elif action["type"] == "key":
                pyautogui.press(action["key"])
        except Exception as e:
            self.handle_error(e, action)
    
    def cleanup_automation(self):
        if self.automation_esc_hotkey:
            try:
                self.automation_esc_hotkey()  # Unregister the global ESC hotkey.
            except Exception:
                pass
            self.automation_esc_hotkey = None
        if not self.stop_automation:
            messagebox.showinfo("Success", "Automation completed successfully", parent=self.root)
            self.status_var.set("Automation completed successfully")
        else:
            messagebox.showinfo("Stopped", "Automation was stopped by user", parent=self.root)
            self.status_var.set("Automation was stopped")
        self.progress_label.config(text="Ready")
        self.stop_automation = False

def main():
    root = tk.Tk()
    app = MiniRPA_GUI(root)
    root.mainloop()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
