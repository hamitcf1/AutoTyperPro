import customtkinter as ctk
import keyboard
import pyperclip
import threading
import time
import random
import winsound
import os

class AutoTyper:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Auto Typer Pro")
        self.root.geometry("800x600")
        ctk.set_appearance_mode("dark")
        
        # Variables
        self.is_typing = False
        self.typing_thread = None
        self.text_to_type = ""
        self.current_delay = 100  # Default delay in ms
        
        # Create the GUI
        self.setup_gui()
        
        # Bind ESC key for emergency stop
        keyboard.on_press_key("esc", self.emergency_stop)

    def setup_gui(self):
        # Text input frame
        text_frame = ctk.CTkFrame(self.root)
        text_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Text input label
        text_label = ctk.CTkLabel(text_frame, text="Text to Type:")
        text_label.pack(pady=5)
        
        # Text input box
        self.text_input = ctk.CTkTextbox(text_frame, height=200)
        self.text_input.pack(pady=5, padx=10, fill="both", expand=True)
        
        # Bind text changes to update stats
        self.text_input.bind("<<Modified>>", self._on_text_modified)
        
        # Button frame
        button_frame = ctk.CTkFrame(self.root)
        button_frame.pack(pady=10, padx=10, fill="x")
        
        # Copy, Paste, Clear buttons
        copy_btn = ctk.CTkButton(button_frame, text="Copy", command=self.copy_text)
        copy_btn.pack(side="left", padx=5)
        
        paste_btn = ctk.CTkButton(button_frame, text="Paste", command=self.paste_text)
        paste_btn.pack(side="left", padx=5)
        
        clear_btn = ctk.CTkButton(button_frame, text="Clear", command=self.clear_text)
        clear_btn.pack(side="left", padx=5)
        
        # Speed selection frame
        speed_frame = ctk.CTkFrame(self.root)
        speed_frame.pack(pady=10, padx=10, fill="x")
        
        # Speed mode buttons
        self.speed_var = ctk.StringVar(value="normal")
        speeds = [
            ("Super Fast", 30),
            ("Fast", 60),
            ("Normal", 100),
            ("Slow", 150),
            ("Super Slow", 250),
            ("Kaotic Random", -1)  # -1 indicates random mode
        ]
        
        for speed_name, delay in speeds:
            btn = ctk.CTkRadioButton(
                speed_frame,
                text=speed_name,
                value=str(delay),
                variable=self.speed_var
            )
            btn.pack(side="left", padx=10)
        
        # Options Frame
        options_frame = ctk.CTkFrame(self.root)
        options_frame.pack(pady=10, padx=10, fill="x")

        # Start Delay
        delay_frame = ctk.CTkFrame(options_frame)
        delay_frame.pack(pady=5, padx=5, fill="x")
        ctk.CTkLabel(delay_frame, text="Start Delay (seconds):").pack(side="left", padx=5)
        self.start_delay = ctk.CTkEntry(delay_frame, width=70)
        self.start_delay.insert(0, "3")
        self.start_delay.pack(side="left", padx=5)

        # Sound Toggle
        self.sound_enabled = ctk.BooleanVar(value=True)
        sound_check = ctk.CTkCheckBox(options_frame, text="Enable Sounds", 
                                    variable=self.sound_enabled)
        sound_check.pack(pady=5, padx=5, side="left")

        # Natural Typing
        self.natural_typing = ctk.BooleanVar(value=False)
        natural_check = ctk.CTkCheckBox(options_frame, text="Natural Typing", 
                                      variable=self.natural_typing)
        natural_check.pack(pady=5, padx=5, side="left")

        # Word Pauses
        self.word_pauses = ctk.BooleanVar(value=False)
        word_pause_check = ctk.CTkCheckBox(options_frame, text="Pause Between Words", 
                                         variable=self.word_pauses)
        word_pause_check.pack(pady=5, padx=5, side="left")

        # Newline Handling
        newline_frame = ctk.CTkFrame(self.root)
        newline_frame.pack(pady=5, padx=10, fill="x")
        ctk.CTkLabel(newline_frame, text="Newline Handling:").pack(side="left", padx=5)
        self.newline_var = ctk.StringVar(value="space")
        newline_options = [
            ("Space", "space"),
            ("Shift+Enter", "shift_enter"),
            ("Ignore", "ignore")
        ]
        for text, value in newline_options:
            ctk.CTkRadioButton(newline_frame, text=text, value=value,
                             variable=self.newline_var).pack(side="left", padx=5)

        # Custom delay frame for Kaotic Random mode
        self.random_frame = ctk.CTkFrame(self.root)
        self.random_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(self.random_frame, text="Random Delay Range (ms):").pack(side="left", padx=5)
        self.min_delay = ctk.CTkEntry(self.random_frame, width=70)
        self.min_delay.insert(0, "10")
        self.min_delay.pack(side="left", padx=5)
        
        ctk.CTkLabel(self.random_frame, text="to").pack(side="left", padx=5)
        
        self.max_delay = ctk.CTkEntry(self.random_frame, width=70)
        self.max_delay.insert(0, "5000")
        self.max_delay.pack(side="left", padx=5)
        
        # Control buttons frame
        control_frame = ctk.CTkFrame(self.root)
        control_frame.pack(pady=10, padx=10, fill="x")
        
        # Start and Stop buttons
        self.start_btn = ctk.CTkButton(
            control_frame,
            text="Start Typing",
            command=self.start_typing
        )
        self.start_btn.pack(side="left", padx=5, expand=True)
        
        self.stop_btn = ctk.CTkButton(
            control_frame,
            text="Stop",
            command=self.stop_typing,
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5, expand=True)
        
        # Stats Frame
        stats_frame = ctk.CTkFrame(self.root)
        stats_frame.pack(pady=5, padx=10, fill="x")
        
        self.char_count_label = ctk.CTkLabel(stats_frame, text="Characters: 0")
        self.char_count_label.pack(side="left", padx=5)
        
        self.word_count_label = ctk.CTkLabel(stats_frame, text="Words: 0")
        self.word_count_label.pack(side="left", padx=5)

        # Time estimation labels
        time_frame = ctk.CTkFrame(stats_frame)
        time_frame.pack(side="right", padx=5)
        
        self.time_estimate_label = ctk.CTkLabel(time_frame, text="Est. Time: 0:00")
        self.time_estimate_label.pack(side="right", padx=5)
        
        self.progress_label = ctk.CTkLabel(stats_frame, text="Progress: 0%")
        self.progress_label.pack(side="right", padx=5)

        # Status bar
        status_frame = ctk.CTkFrame(self.root)
        status_frame.pack(pady=5, padx=10, fill="x", side="bottom")
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Press ESC for Emergency Stop",
            text_color="red"
        )
        self.status_label.pack(pady=5, side="left")
        
        self.status_text = ctk.CTkLabel(
            status_frame,
            text="Ready",
            text_color="yellow"
        )
        self.status_text.pack(pady=5, side="right")

    def copy_text(self):
        text = self.text_input.get("1.0", "end-1c")
        pyperclip.copy(text)
        self.status_text.configure(text="Text copied!", text_color="green")
        self.root.after(1000, lambda: self.status_text.configure(text="Ready", text_color="yellow"))

    def paste_text(self):
        text = pyperclip.paste()
        self.text_input.delete("1.0", "end")
        self.text_input.insert("1.0", text)
        self.update_text_stats()
        self.status_text.configure(text="Text pasted!", text_color="green")
        self.root.after(1000, lambda: self.status_text.configure(text="Ready", text_color="yellow"))

    def clear_text(self):
        self.text_input.delete("1.0", "end")
        self.update_text_stats()
        self.status_text.configure(text="Text cleared!", text_color="green")
        self.root.after(1000, lambda: self.status_text.configure(text="Ready", text_color="yellow"))

    def get_delay(self):
        delay = int(self.speed_var.get())
        if delay == -1:  # Kaotic Random mode
            min_d = int(self.min_delay.get())
            max_d = int(self.max_delay.get())
            return random.randint(min_d, max_d) / 1000.0
        return delay / 1000.0

    def format_time(self, seconds):
        """Convert seconds to MM:SS format"""
        if seconds < 60:
            return f"0:{seconds:02.0f}"
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def calculate_typing_time(self, text_length=None):
        """Calculate estimated typing time based on current settings"""
        if text_length is None:
            text = self.text_input.get("1.0", "end-1c")
            text_length = len(text)

        if text_length == 0:
            return 0

        # Get base delay
        if self.speed_var.get() == "-1":  # Kaotic Random mode
            try:
                min_d = int(self.min_delay.get())
                max_d = int(self.max_delay.get())
                avg_delay = (min_d + max_d) / 2 / 1000.0
            except ValueError:
                avg_delay = 0.1
        else:
            avg_delay = int(self.speed_var.get()) / 1000.0

        # Account for natural typing variation
        if self.natural_typing.get():
            avg_delay *= 1.15  # Add 15% to account for variations

        # Calculate word pause impact
        if self.word_pauses.get():
            space_count = text.count(' ') if 'text' in locals() else text_length // 5
            total_pause_time = space_count * (avg_delay * 2)  # Double delay for word pauses
        else:
            total_pause_time = 0

        # Calculate total time
        try:
            start_delay = float(self.start_delay.get())
        except ValueError:
            start_delay = 3

        total_time = (text_length * avg_delay) + total_pause_time + start_delay
        return total_time

    def update_time_estimate(self, chars_typed=0, total_chars=None):
        """Update the time estimation label"""
        if total_chars is None:
            total_chars = len(self.text_input.get("1.0", "end-1c"))
        
        if total_chars == 0:
            self.time_estimate_label.configure(text="Est. Time: 0:00")
            return

        if chars_typed == 0:
            # Before starting, show total estimated time
            total_time = self.calculate_typing_time(total_chars)
            self.time_estimate_label.configure(text=f"Est. Time: {self.format_time(total_time)}")
        else:
            # During typing, show remaining time
            chars_remaining = total_chars - chars_typed
            remaining_time = self.calculate_typing_time(chars_remaining)
            self.time_estimate_label.configure(text=f"Time Left: {self.format_time(remaining_time)}")

    def update_text_stats(self):
        text = self.text_input.get("1.0", "end-1c")
        char_count = len(text)
        word_count = len(text.split())
        self.char_count_label.configure(text=f"Characters: {char_count}")
        self.word_count_label.configure(text=f"Words: {word_count}")
        self.update_time_estimate()  # Update time estimate when text changes

    def _on_text_modified(self, event=None):
        self.update_text_stats()
        self.text_input.edit_modified(False)  # Reset modified flag

    def play_sound(self, sound_name):
        if not self.sound_enabled.get():
            return
            
        try:
            sound_path = os.path.join(os.path.dirname(__file__), "sounds", f"{sound_name}.wav")
            if os.path.exists(sound_path):
                winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as e:
            print(f"Sound error: {e}")

    def natural_delay(self):
        if self.natural_typing.get():
            # Add some natural variation (±30% of base delay)
            base_delay = self.get_delay()
            variation = base_delay * 0.3
            return base_delay + random.uniform(-variation, variation)
        return self.get_delay()

    def type_text(self):
        self.text_to_type = self.text_input.get("1.0", "end-1c")
        total_chars = len(self.text_to_type)
        chars_typed = 0
        
        # Start delay
        try:
            start_delay = float(self.start_delay.get())
        except ValueError:
            start_delay = 3
        
        self.status_text.configure(text=f"Starting in {start_delay} seconds...", text_color="yellow")
        time.sleep(start_delay)
        
        self.play_sound("start")
        self.status_text.configure(text="Typing...", text_color="green")

        last_char = ' '
        for char in self.text_to_type:
            if not self.is_typing:
                break

            # Handle newlines more carefully
            if char == '\n':
                if self.newline_var.get() == "space":
                    keyboard.write(' ')
                elif self.newline_var.get() == "shift_enter":
                    keyboard.press('shift')
                    keyboard.press('enter')
                    time.sleep(0.05)  # Small delay to ensure keys are registered
                    keyboard.release('enter')
                    keyboard.release('shift')
                # Even if ignore is selected, we still count the character
            else:
                # Type the character
                keyboard.write(char)
            
            chars_typed += 1
            progress = (chars_typed / total_chars) * 100
            self.progress_label.configure(text=f"Progress: {progress:.1f}%")
            self.update_time_estimate(chars_typed, total_chars)

            # Word pause
            if self.word_pauses.get() and last_char != ' ' and char == ' ':
                time.sleep(self.natural_delay() * 2)  # Longer pause between words
            else:
                time.sleep(self.natural_delay())
            
            last_char = char

        self.is_typing = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_text.configure(text="Ready", text_color="yellow")
        
        if chars_typed >= total_chars:
            self.play_sound("finish")
            self.progress_label.configure(text="Progress: 100%")

    def start_typing(self):
        if not self.is_typing:
            self.is_typing = True
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.typing_thread = threading.Thread(target=self.type_text)
            self.typing_thread.start()

    def stop_typing(self):
        self.is_typing = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_text.configure(text="Stopped", text_color="yellow")
        self.play_sound("stop")

    def emergency_stop(self, e):
        if self.is_typing:
            self.is_typing = False
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.status_text.configure(text="Emergency Stop!", text_color="red")
            self.play_sound("emergency")
            # Reset after 2 seconds
            self.root.after(2000, lambda: self.status_text.configure(text="Ready", text_color="yellow"))

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AutoTyper()
    app.run()
