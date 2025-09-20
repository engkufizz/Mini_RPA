# Mini RPA Tool

A lightweight desktop automation tool built with **Python, Tkinter, PyAutoGUI, and Keyboard**.
This tool allows you to **record and replay automation sequences** (mouse clicks, keystrokes, text inputs, and delays). It’s designed as a simple RPA (Robotic Process Automation) helper for repetitive tasks.

---

## ✨ Features

* 🎥 **Record Automation Sequences**

  * Capture clicks (single, double, triple, etc.), delays, text typing, and key presses.

* ▶️ **Playback Automation**

  * Run your recorded or loaded automation sequence with an optional 5-second start delay.

* 💾 **Save & Load Sequences**

  * Save sequences as `.json` files and load them later.

* ⌨️ **Hotkey Controls**

  * **During recording**:

    * `Space` → Record click
    * `D` → Add delay
    * `T` → Add text
    * `K` → Add key press
    * `Esc` → Finish recording
  * **During playback**:

    * `Esc` → Stop automation immediately

* 🖱️ **Multi-click Grouping**

  * Rapid clicks (double/triple) are grouped into one action.

---

## 📦 Requirements

* Python 3.7+
* Install dependencies:

```bash
pip install pyautogui keyboard
```

Tkinter comes pre-installed with most Python distributions.

---

## 🚀 Usage

1. Run the program:

```bash
python mini_rpa.py
```

2. In the GUI:

   * Click **Setup Automation** → use hotkeys to record actions.
   * Save your sequence when done.
   * Or click **Load Sequence** to use a saved `.json` file.
   * Click **Start Automation** → switch to your target window before execution begins.

3. Press **Esc** anytime during playback to stop automation.

---

## 📂 File Format (JSON)

Automation sequences are stored as JSON, for example:

```json
[
    {
        "type": "multi_click",
        "x": 500,
        "y": 300,
        "count": 2,
        "description": "2 clicks at (500, 300)"
    },
    {
        "type": "wait",
        "delay": 2,
        "description": "Wait for 2 sec"
    },
    {
        "type": "text",
        "text": "Hello World",
        "description": "Type text: Hello World"
    },
    {
        "type": "key",
        "key": "enter",
        "description": "Press key: enter"
    }
]
```

---

## ⚠️ Safety Notes

* `pyautogui.FAILSAFE = True` is enabled → Move your mouse to the top-left corner of the screen to instantly abort automation.
* Always test on a safe environment before running on critical applications.

---

## 📜 License

MIT License – free to use, modify, and distribute.
