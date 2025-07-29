# Auto Typer Pro

A modern, customizable, and user-friendly auto-typing application featuring natural typing simulation, real-time progress tracking, and various control options.

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
- **Natural Typing**: Simulates human-like typing with random variations (±30% delay)
- **Word Pauses**: Extra pauses between words for more natural appearance
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

### Control Features
- **Emergency Stop**: Press ESC at any time to stop typing
- **Sound Effects**: Toggle-able notifications for:
  - Start typing
  - Finish typing
  - Stop typing
  - Emergency stop

## Installation

### Method 1: Running from Source
1. Download Python 3.x from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation
2. Clone this repository:
   ```bash
   git clone https://github.com/username/AutoTyperPro.git
   cd AutoTyperPro
   ```
3. Run `make_executable.bat`
   - This script will automatically:
     - Create virtual environment
     - Install required packages
     - Create executable file

### Method 2: Using Pre-built Executable
1. Download the latest release from [Releases](../../releases)
2. Extract the ZIP file
3. Run `AutoTyperPro.exe`

## Sound Files
Place these .wav files in the 'sounds' folder:
- start.wav
- finish.wav
- stop.wav
- emergency.wav

## Development

### Requirements
- Python 3.x
- Packages:
  ```bash
  keyboard==0.13.5
  customtkinter==5.2.0
  pyperclip==1.8.2
  ```

### Development Setup
1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```
3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

### Building Executable
On Windows:
```bash
make_executable.bat
```

On Linux/Mac:
```bash
python -m PyInstaller --name="AutoTyperPro" --onefile --windowed --add-data "sounds:sounds" --clean auto_typer.py
```

## Usage

1. Start the program
2. Enter or paste your text
3. Configure typing settings:
   - Select typing speed
   - Adjust start delay
   - Enable natural typing and word pauses if desired
   - Choose newline behavior
4. Check estimated completion time
5. Click "Start Typing" and switch to target application

## Important Notes

- May require administrator privileges for keyboard simulation
- Test before using with important text
- ESC key always available for emergency stop
- Time estimates consider:
  - Selected typing speed
  - Natural typing variations
  - Word pauses
  - Start delay
  - Text length

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
