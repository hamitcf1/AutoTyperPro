# Auto Typer Pro

Modern, özelleştirilebilir ve kullanıcı dostu bir otomatik yazma uygulaması. Doğal yazma simulasyonu, gerçek zamanlı ilerleme takibi ve çeşitli kontrol seçenekleri sunar.

[English README](#english)

## Features

### Typing Modes
- **Super Fast** (30ms delay)
- **Fast** (60ms delay)
- **Normal** (100ms delay)
- **Slow** (150ms delay)
- **Super Slow** (250ms delay)
- **Kaotic Random** (customizable delay range: 10-5000ms)

### Advanced Options
- **Start Delay**: Customizable delay before typing begins (default: 3 seconds)
- **Natural Typing**: Simulates human-like typing with random variations (±30% of base delay)
- **Word Pauses**: Extra pauses between words for more natural typing
- **Newline Handling**:
  - Space: Convert newlines to spaces
  - Shift+Enter: Type actual newlines
  - Ignore: Skip newlines

### Smart Progress Tracking
- Real-time character and word count
- Progress percentage display
- Estimated completion time calculation
- Remaining time display during typing
- Time estimates update with setting changes

### Text Management
- **Copy/Paste/Clear** functions with instant feedback
- Real-time character and word count updates
- Progress tracking during typing
- Live status updates

### Control Features
- **Emergency Stop**: Press ESC at any time to stop typing
- **Sound Effects**: Toggle-able sound notifications for:
  - Start typing
  - Finish typing
  - Stop typing
  - Emergency stop

### User Interface
- Modern dark theme
- Real-time statistics display
- Status bar with color-coded messages
- Progress and time tracking

## Installation

### Method 1: Running from Source
1. Install Python 3.x from [python.org](https://www.python.org/downloads/)
2. Install required packages:
   ```bash
   pip install keyboard customtkinter pyperclip
   ```
3. Download the source code
4. Place sound files in the 'sounds' folder

### Method 2: Using the Executable
1. Download the latest release
2. Extract the zip file
3. Run `AutoTyperPro.exe`

## Sound Effects Setup
Place these .wav files in the 'sounds' folder:
- start.wav
- finish.wav
- stop.wav
- emergency.wav

## Usage

1. Launch AutoTyper Pro
2. Paste or type your text in the input box
3. Configure typing settings:
   - Select typing speed
   - Adjust start delay (default: 3 seconds)
   - Enable/disable natural typing
   - Choose newline handling method
   - Toggle sound effects
   - Enable word pauses if desired
4. Review the estimated completion time
5. Click "Start Typing" and switch to your target application

## Important Notes

- Requires administrative privileges for keyboard simulation
- Test the typing speed and options before using with important text
- Use ESC key for emergency stop at any time
- Time estimates consider:
  - Selected typing speed
  - Natural typing variations
  - Word pauses
  - Start delay
  - Text length

## Tips for Best Results

- Use "Natural Typing" and "Word Pauses" for human-like typing
- For chat applications, use "Shift+Enter" newline mode
- Adjust start delay based on your needs
- Monitor the estimated completion time when changing settings
- Keep sound effects enabled for better feedback
- Use emergency stop (ESC) if needed

## Building from Source

To create your own executable:
1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Create the executable:
   ```bash
   pyinstaller --onefile --windowed --icon=icon.ico --add-data "sounds;sounds" auto_typer.py
   ```
3. The executable will be created in the `dist` folder

## Troubleshooting

- If sounds don't play, ensure .wav files are in the sounds folder
- If keyboard simulation doesn't work, run as administrator
- For any issues, check the console output for error messages
