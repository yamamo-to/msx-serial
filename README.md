# MSX Serial Terminal

[![CI](https://github.com/yamamo-to/msx-serial/actions/workflows/ci.yml/badge.svg)](https://github.com/yamamo-to/msx-serial/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/msx-serial.svg)](https://badge.fury.io/py/msx-serial)

A high-performance terminal program for MSX communication via serial connection or telnet. Features instant character display, automatic mode detection, and Japanese text support.

## Features

✨ **Instant Communication**: Optimized for real-time character-by-character MSX interaction  
🔍 **Automatic Mode Detection**: Detects BASIC and MSX-DOS modes automatically  
🌐 **Multiple Connection Types**: Serial, Telnet, and Dummy connections  
📝 **Japanese Text Support**: Full MSX character encoding support  
📁 **File Transfer**: BASIC program upload and text file paste functionality  
🎯 **Smart Completion**: Context-aware command completion  
🎨 **Color Display**: Beautiful colored terminal output  

## Installation

```bash
pip install msx-serial
```

## Usage

### Basic Connection

```bash
# Serial connections
msx-serial COM1                                    # Windows
msx-serial /dev/ttyUSB0                           # Linux
msx-serial /dev/tty.usbserial-12345678901         # macOS

# Serial with parameters
msx-serial 'serial:///dev/ttyUSB0?baudrate=115200&bytesize=8&parity=N&stopbits=1'

# Telnet connections
msx-serial 192.168.1.100:2223
msx-serial telnet://192.168.1.100:2223

# Dummy connection (for testing)
msx-serial dummy://
```

### Command Line Options

```
usage: msx-serial [-h] [--encoding ENCODING] [--debug] connection

MSX Serial Terminal

positional arguments:
  connection           Connection string (e.g. COM4, /dev/ttyUSB0, 192.168.1.100:2223, dummy://)

options:
  -h, --help           Show help message and exit
  --encoding ENCODING  Text encoding (default: msx-jp)
  --debug              Enable debug mode
```

### Special Commands

| Command | Description | Available In |
|---------|-------------|--------------|
| `@paste` | Paste text file content | BASIC mode only |
| `@upload` | Upload file as BASIC program | BASIC mode only |
| `@cd` | Change current directory | All modes |
| `@encode` | Set text encoding | All modes |
| `@help` | Show command help | All modes |
| `@mode` | Display/force MSX mode | All modes |
| `@exit` | Exit program | All modes |

Use `@help` for detailed command usage information.

### MSX Mode Detection

The terminal automatically detects and adapts to MSX operating modes:

- **BASIC Mode**: Detected by `Ok` prompt - enables file upload/paste commands
- **MSX-DOS Mode**: Detected by `A:>`, `B:>`, `C:>` etc. prompts  
- **Unknown Mode**: Default state until mode is detected

### Mode Commands

```bash
@mode          # Display current MSX mode
@mode basic    # Force BASIC mode
@mode dos      # Force MSX-DOS mode  
@mode unknown  # Reset to unknown mode
```

## Connection URI Format

### Serial Connections

```bash
# Basic format
serial:///dev/ttyUSB0

# With parameters
serial:///dev/ttyUSB0?baudrate=115200&bytesize=8&parity=N&stopbits=1&timeout=1
```

**Supported Parameters:**
- `baudrate`: Baud rate (default: 9600)
- `bytesize`: Data bits (5, 6, 7, 8 - default: 8) 
- `parity`: Parity (N, E, O, M, S - default: N)
- `stopbits`: Stop bits (1, 1.5, 2 - default: 1)
- `timeout`: Read timeout in seconds
- `xonxoff`: Software flow control (true/false)
- `rtscts`: Hardware flow control (true/false)
- `dsrdtr`: DSR/DTR flow control (true/false)

### Telnet Connections

```bash
# Basic format
telnet://hostname:port

# Examples
telnet://192.168.1.100:2223
telnet://msx.local:2223
```

## Text Encoding Support

Supported encodings for MSX text:
- `msx-jp`: Japanese MSX encoding (default)
- `msx-intl`: International MSX encoding
- `msx-br`: Brazilian MSX encoding  
- `shift-jis`: Shift-JIS encoding
- `utf-8`: UTF-8 encoding

Change encoding with: `@encode msx-jp`

## Architecture

### Core Components

- **OptimizedTerminalSession**: Main terminal session with instant response
- **ConnectionManager**: Unified connection handling (Serial/Telnet/Dummy)
- **MSXProtocolDetector**: Automatic mode detection from prompts
- **DataProcessor**: Real-time data processing with instant display
- **CommandCompleter**: Context-aware command completion
- **FileTransferManager**: File upload and paste operations

### Project Structure

```
msx_serial/
├── core/              # Core terminal session and data processing
├── connection/        # Connection implementations (Serial/Telnet/Dummy)
├── protocol/          # MSX protocol detection and mode management
├── display/           # Terminal display handlers
├── completion/        # Command completion system
├── commands/          # Special command handlers
├── io/                # Input/output coordination
├── transfer/          # File transfer functionality
├── common/            # Shared utilities and color output
└── data/              # Static data (command lists, keywords)
```

### Key Design Principles

1. **Instant Response**: Character-by-character processing for real-time MSX interaction
2. **Automatic Adaptation**: Mode detection adapts terminal behavior to MSX state
3. **Unified Connection**: Single interface for multiple connection types
4. **Context Awareness**: Commands and completion adapt to current MSX mode
5. **Robust Error Handling**: Graceful handling of connection and encoding issues

## Development

### Requirements

- Python 3.9+
- Dependencies listed in `pyproject.toml`

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yamamo-to/msx-serial
cd msx-serial

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate   # Windows

# Install in development mode
pip install -e . --use-pep517
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=msx_serial

# Run specific test file
python -m pytest tests/test_protocol.py -v
```

### Key Dependencies

- **pyserial**: Serial communication
- **prompt-toolkit**: Interactive command line interface
- **colorama**: Terminal color support
- **msx-charset**: MSX character encoding conversion
- **chardet**: Character encoding detection
- **PyYAML**: YAML configuration file support
- **tqdm**: Progress bars for file transfers

## Performance Optimizations

The terminal is optimized for MSX communication with several key improvements:

- **Instant Mode**: Character-by-character processing eliminates buffering delays
- **Adaptive Delays**: Smart timing based on data activity patterns
- **Efficient Display**: Direct ANSI escape sequence output
- **Single Character Reads**: Optimal for MSX's character-based interaction
- **Echo Suppression**: Intelligent command echo handling

## Acknowledgments

Base64 upload functionality inspired by:
https://qiita.com/enu7/items/23cab122141fb8d07c6d

MSX-BASIC command reference converted from:
https://github.com/fu-sen/MSX-BASIC

## License

MIT License
