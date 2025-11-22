#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import pyautogui
import threading
import time
import json
import sys
import keyboard

# ───────────── ToolTip Class for Hover Help ─────────────
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 25
        
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tip_window, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("Consolas", 10, "normal"))
        label.pack(ipadx=5, ipady=5)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

# ───────────── Main Application ─────────────
class MiniRPA_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini RPA Tool v3.6") 
        self.root.geometry("600x600")
        
        # Default settings and flags
        self.delay_between_actions = 0.3
        self.automation_sequence = []  
        self.stop_automation = False
        self.automation_esc_hotkey = None  
        self.is_dialog_open = False         
        self.in_setup_mode = False          
        
        # Variables for grouping rapid clicks
        self.click_buffer_count = 0
        self.last_click_time = 0
        self.click_buffer_after_id = None
        
        self.create_gui()
        self.setup_error_handling()
    
    def create_gui(self):
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(expand=True, fill="both")
        
        # Title
        title_label = tk.Label(main_frame, text="Mini RPA Tool", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 5))

        # --- Help Button [?] ---
        help_btn = tk.Button(main_frame, text="[?]", font=("Arial", 10, "bold"), bg="#ecf0f1", width=4)
        help_btn.pack(pady=(0, 10))
        
        help_text = (
            "SETUP MODE HOTKEYS:\n"
            "-------------------\n"
            "SPACE  : Record Mouse Click (at current position)\n"
            "D      : Add Delay (Wait time)\n"
            "T      : Type Text (Input string)\n"
            "K      : Press Specific Key (e.g., tab, shift)\n"
            "INSERT : Press ENTER Key (Quick record)\n"
            "ARROWS : Record Up/Down/Left/Right keys\n"
            "ESC    : Finish Setup / Stop Automation"
        )
        ToolTip(help_btn, help_text)
        # -----------------------
        
        self.progress_label = tk.Label(main_frame, text="Ready", font=("Arial", 12))
        self.progress_label.pack(pady=(0, 10))
        
        # Setup Button
        self.setup_button = tk.Button(main_frame, text="Setup Automation", command=self.setup_automation,
                                      font=("Arial", 12), bg="#3498db", fg="white", width=20, height=2)
        self.setup_button.pack(pady=5)
        
        # Loop Controls
        loop_frame = tk.Frame(main_frame)
        loop_frame.pack(pady=5)
        tk.Label(loop_frame, text="Loop Count:", font=("Arial", 11)).pack(side="left", padx=5)
        self.loop_entry = tk.Entry(loop_frame, width=5, justify="center", font=("Arial", 11))
        self.loop_entry.insert(0, "1") 
        self.loop_entry.pack(side="left")
        
        # Start Button
        self.start_button = tk.Button(main_frame, text="Start Automation", command=self.start_automation,
                                      font=("Arial", 12), bg="#2ecc71", fg="white", width=20, height=2)
        self.start_button.pack(pady=5)
        
        self.load_button = ttk.Button(main_frame, text="Load Sequence", command=self.load_automation_sequence)
        self.load_button.pack(pady=5)
        
        listbox_label = tk.Label(main_frame, text="Recorded/Loaded Automation Sequence:", font=("Arial", 12))
        listbox_label.pack(pady=(15, 5))
        self.sequence_listbox = tk.Listbox(main_frame, width=70, height=10)
        self.sequence_listbox.pack(fill="both", expand=True)
        
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
    
    # ───────────── Setup Automation ─────────────
    def setup_automation(self):
        self.in_setup_mode = True
        self.automation_sequence = []
        self.sequence_listbox.delete(0, tk.END)
        self.progress_label.config(text="Setup Active. Hover over [?] for keys.")
        self.register_setup_hotkeys()
    
    def register_setup_hotkeys(self):
        self.hotkeys = {
            'space': keyboard.add_hotkey('space', lambda: self.handle_setup_key('space')),
            'd':     keyboard.add_hotkey('d',     lambda: self.handle_setup_key('d')),
            't':     keyboard.add_hotkey('t',     lambda: self.handle_setup_key('t')),
            'k':     keyboard.add_hotkey('k',     lambda: self.handle_setup_key('k')),
            'esc':   keyboard.add_hotkey('esc',   lambda: self.handle_setup_key('esc')),
            'up':    keyboard.add_hotkey('up',    lambda: self.handle_setup_key('up')),
            'down':  keyboard.add_hotkey('down',  lambda: self.handle_setup_key('down')),
            'left':  keyboard.add_hotkey('left',  lambda: self.handle_setup_key('left')),
            'right': keyboard.add_hotkey('right', lambda: self.handle_setup_key('right')),
            'insert': keyboard.add_hotkey('insert', lambda: self.handle_setup_key('enter')) 
        }
    
    def remove_setup_hotkeys(self):
        if hasattr(self, 'hotkeys'):
            for hotkey_name in self.hotkeys:
                try:
                    keyboard.remove_hotkey(hotkey_name)
                except Exception:
                    pass
            self.hotkeys.clear()
    
    def handle_setup_key(self, key):
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
        elif key in ['up', 'down', 'left', 'right', 'enter']:
            self.record_specific_key_press(key)
    
    def record_click_action(self):
        now = time.time()
        threshold = 0.3
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
        if self.is_dialog_open: return
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
        if self.is_dialog_open: return
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
        if self.is_dialog_open: return
        try:
            self.is_dialog_open = True
            key_value = simpledialog.askstring("Key Press Action", "Enter key (e.g., 'enter', 'tab'):", parent=self.root)
            if key_value is not None:
                clean_key = key_value.lower().strip()
                action = {"type": "key", "key": clean_key, "description": f"Press key: {clean_key}"}
                self.automation_sequence.append(action)
                self.sequence_listbox.insert(tk.END, action["description"])
        finally:
            self.is_dialog_open = False

    def record_specific_key_press(self, key_value):
        if self.is_dialog_open: return
        clean_key = key_value.lower().strip()
        action = {"type": "key", "key": clean_key, "description": f"Press key: {clean_key}"}
        self.automation_sequence.append(action)
        self.sequence_listbox.insert(tk.END, action["description"])
        self.status_var.set(f"Recorded key press: {clean_key}")

    def finish_setup(self):
        if not self.in_setup_mode: return
        self.in_setup_mode = False
        self.remove_setup_hotkeys()
        self.progress_label.config(text="Setup Complete! You can now start automation.")
        self.status_var.set("Setup complete.")
        if self.automation_sequence:
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
    
    # ───────────── Loading & Starting ─────────────
    def load_automation_sequence(self):
        sequence_path = filedialog.askopenfilename(
            title="Select Automation Sequence",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if sequence_path:
            try:
                with open(sequence_path, "r") as fp:
                    data = json.load(fp)
                
                if not isinstance(data, list):
                    raise ValueError("JSON file must contain a list of actions.")
                
                valid_sequence = []
                for item in data:
                    if "type" not in item or "description" not in item:
                        continue 
                    valid_sequence.append(item)
                
                if not valid_sequence:
                    raise ValueError("No valid actions found in file.")

                self.automation_sequence = valid_sequence
                self.sequence_listbox.delete(0, tk.END)
                for action in self.automation_sequence:
                    self.sequence_listbox.insert(tk.END, action.get("description", "No description"))
                self.progress_label.config(text="Sequence loaded. Ready to start.")
                self.status_var.set("Sequence loaded.")
            except Exception as e:
                self.handle_error(e)
    
    def start_automation(self):
        if not self.automation_sequence:
            messagebox.showerror("Error", "No automation sequence found.", parent=self.root)
            return
        
        try:
            loops = int(self.loop_entry.get())
            if loops < 1: loops = 1
        except ValueError:
            messagebox.showerror("Input Error", "Loop count must be a number.")
            return

        self.stop_automation = False
        self.progress_label.config(text=f"Starting {loops} loop(s) in 5 seconds.\nSwitch to target window. (Press ESC to cancel)")
        self.status_var.set("Automation starting in 5 seconds...")
        self.automation_esc_hotkey = keyboard.add_hotkey('esc', self.request_stop_automation)
        
        threading.Thread(target=self.run_automation, args=(self.automation_sequence, loops), daemon=True).start()
    
    def request_stop_automation(self):
        self.stop_automation = True
    
    def run_automation(self, sequence, loops):
        try:
            time.sleep(5)
            for current_loop in range(loops):
                if self.stop_automation: break
                
                loop_msg = f"Loop {current_loop + 1}/{loops}"
                self.root.after(0, self.progress_label.config, {"text": f"Running... {loop_msg} (Press ESC to stop)"})
                
                for index, action in enumerate(sequence, start=1):
                    if self.stop_automation:
                        self.root.after(0, self.status_var.set, f"Stopping at step {index}...")
                        break
                    
                    self.root.after(0, self.status_var.set, f"[{loop_msg}] Step {index}/{len(sequence)}: {action['description']}")
                    self.execute_action(action, index)
                    time.sleep(self.delay_between_actions)
                
                if current_loop < loops - 1:
                    time.sleep(1) 

        finally:
            self.root.after(0, self.cleanup_automation)
    
    def execute_action(self, action, index):
        try:
            action_type = action.get("type")
            if action_type == "multi_click":
                pyautogui.click(x=action["x"], y=action["y"], clicks=action["count"], interval=0.1)
            elif action_type == "wait":
                time.sleep(action["delay"])
            elif action_type == "text":
                pyautogui.write(action["text"])
            elif action_type == "key":
                key_to_press = str(action["key"]).lower().strip()
                pyautogui.press(key_to_press)
        except Exception as e:
            self.root.after(0, self.handle_error, e, action)
            self.stop_automation = True
    
    def cleanup_automation(self):
        if self.automation_esc_hotkey:
            try:
                keyboard.remove_hotkey('esc')
            except Exception:
                pass
            self.automation_esc_hotkey = None
        
        if self.stop_automation:
            messagebox.showinfo("Stopped", "Automation was stopped.", parent=self.root)
            self.status_var.set("Automation stopped.")
        else:
            messagebox.showinfo("Success", "All loops completed successfully.", parent=self.root)
            self.status_var.set("Automation completed.")
            
        self.progress_label.config(text="Ready")
        self.stop_automation = False

def main():
    root = tk.Tk()
    app = MiniRPA_GUI(root)
    
    def on_closing():
        app.remove_setup_hotkeys()
        if app.automation_esc_hotkey:
            try:
                keyboard.remove_hotkey('esc')
            except:
                pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
