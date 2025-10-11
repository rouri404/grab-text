<div align="center">
  <h1>GrabText</h1>
  <p>
    <img src="https://img.shields.io/badge/version-1.3.3-blue" alt="Version">
    <img src="https://img.shields.io/badge/Platform-Linux-lightgrey" alt="Platform">
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
    <img src="https://img.shields.io/badge/status-active-success" alt="Status">
    <a href="README.pt.md"><img src="https://img.shields.io/badge/Language-Português%20%F0%9F%87%A7%F0%9F%87%B7-blue" alt="Português"></a>
  </p>
    <p>
    Capture and copy text from any image or video on your screen. A simple yet powerful OCR tool for Linux-based systems. Features both GUI and CLI interfaces.
  </p>
</div>

---

## About the Project

<div align="center">
  <img src="preview.gif" width="70%" alt="Preview">
</div>

**GrabText** is a productivity tool that streamlines the process of capturing text from anywhere on your screen. Whether it's from an image, a video, a protected document, or a web page, simply select the desired area, and the text will be recognized and copied to your clipboard instantly.

It utilizes **Tesseract** for character recognition and **Flameshot** for intuitive screen selection.

---

## Features

### Core Features
*   **Multilingual OCR:** Robust support for text recognition in English (`en`) and Portuguese (`pt`).
*   **Intuitive Screen Capture:** Use the Flameshot interface to easily select the desired screen area.
*   **Instant Copy:** Recognized text is automatically copied to the clipboard.
*   **Flexible Configuration:** Switch the OCR language using configuration file or CLI commands.
*   **Activity Logging:** Detailed logs are generated to facilitate debugging.
*   **Default Behavior:** Running `grabtext` without arguments captures screen area automatically.

### CLI Features
*   **Screen Capture:** Intuitive text capture from screen areas
*   **Image Processing:** Process single images or entire directories
*   **Directory Monitoring:** Watch folders for new images to process
*   **Multiple Output Formats:** Support for text, JSON, and CSV outputs
*   **Structured Data Export:** Rich JSON and CSV formats with metadata and OCR confidence
*   **Advanced Log Management:** Filter, export, and analyze log files
*   **System Status:** Check dependencies and configuration
*   **Batch Processing:** Handle multiple images efficiently with unified data structures

## CLI Commands

The GrabText CLI is organized into main commands and utility commands for better usability:

### Main Commands

```bash
# Screen Capture (Default Behavior)
grabtext                          # Capture screen area and extract text (default)
grabtext grab                     # Same as above, explicit command
grabtext grab -l en               # Use English OCR
grabtext grab -o output.txt       # Save output to file
grabtext grab --no-clipboard      # Don't copy to clipboard
grabtext grab --dry-run           # Show what would be done

# Process Existing Files
grabtext process image.png        # Process single image
grabtext process ./images -r      # Process directory recursively
grabtext process ./images -f json # Output in structured JSON format
grabtext process ./images -f csv  # Output in structured CSV format
grabtext process ./images --batch # Process multiple images

# Monitor Directories
grabtext monitor ./images         # Monitor directory for new images
grabtext monitor ./images -r      # Monitor recursively
grabtext monitor ./images -f csv  # Output in CSV format
```

### Utility Commands

```bash
# System Information
grabtext status                   # Show system status and dependencies
grabtext config                   # Show current configuration
grabtext version                  # Display version information
grabtext help                     # Show general help

# Language Management
grabtext get-lang                 # Show current language
grabtext set-lang en              # Set language to English
grabtext set-lang pt              # Set language to Portuguese

# Log Management
grabtext logs --tail 10           # Show last 10 log entries
grabtext logs --since 2023-10-01  # Show logs since October 1st
grabtext logs --errors            # Show only errors
grabtext logs --export logs.txt   # Export logs to file
grabtext logs --clear             # Clear log file

# Debugging Options
grabtext --debug                  # Enable debug mode with verbose output
grabtext --verbose                # Show detailed progress information
grabtext --dry-run                # Show what would be done without executing
```

---

## Export Formats

GrabText supports three output formats, each optimized for different use cases:

### Text Format (Default)
Simple text output - just the extracted text content.

### JSON Format
Rich structured data with comprehensive metadata and OCR information:

```bash
# Single image JSON output
grabtext process image.png -f json

# Batch processing JSON output
grabtext process ./images -f json -o results.json
```

**JSON Structure:**
```json
{
  "metadata": {
    "filename": "document.png",
    "filepath": "/path/to/document.png",
    "file_size_bytes": 245760,
    "file_modified": "2025-10-11T16:30:00.000000",
    "image_width": 1920,
    "image_height": 1080,
    "image_format": "PNG",
    "image_mode": "RGB"
  },
  "ocr": {
    "text": "Extracted text content...",
    "word_count": 25,
    "char_count": 150,
    "avg_confidence": 87.5,
    "language_used": "eng",
    "has_text": true,
    "processing_timestamp": "2025-10-11T16:35:00.000000"
  },
  "processing_info": {
    "grabtext_version": "1.3.2",
    "processed_at": "2025-10-11T16:35:00.000000"
  }
}
```

**Batch JSON Structure:**
```json
{
  "batch_info": {
    "total_files": 5,
    "processed_at": "2025-10-11T16:35:00.000000",
    "directory": "/path/to/images",
    "recursive": false,
    "grabtext_version": "1.3.2",
    "successfully_processed": 5
  },
  "results": [
    { /* Individual file data as above */ }
  ]
}
```

### CSV Format
Tabular data perfect for spreadsheet applications and data analysis:

```bash
# Single image CSV output
grabtext process image.png -f csv

# Batch processing CSV output
grabtext process ./images -f csv -o results.csv
```

**CSV Columns:**
- `filename`: Image file name
- `filepath`: Full path to the image
- `file_size_bytes`: File size in bytes
- `file_modified`: Last modification timestamp
- `image_width`: Image width in pixels
- `image_height`: Image height in pixels
- `image_format`: Image format (PNG, JPEG, etc.)
- `image_mode`: Color mode (RGB, RGBA, etc.)
- `text`: Extracted text content
- `word_count`: Number of words detected
- `char_count`: Number of characters detected
- `avg_confidence`: Average OCR confidence (0-100)
- `language_used`: OCR language used
- `has_text`: Whether text was detected (true/false)
- `processing_timestamp`: When processing occurred

### Use Cases

**JSON Format is ideal for:**
- API integrations and web applications
- Data analysis with programming languages
- Automated processing pipelines
- Detailed audit trails

**CSV Format is ideal for:**
- Spreadsheet analysis (Excel, LibreOffice Calc)
- Database imports
- Statistical analysis tools
- Quick data review and comparison

---

## Environment Variables

The following environment variables can be used to configure GrabText:

*   `GRABTEXT_LANG`: Set the default OCR language (`en` or `pt`)
*   `GRABTEXT_LOG`: Set custom log file location (default: `~/.local/share/grabtext/grabtext.log`)
*   `GRABTEXT_NO_NOTIFY`: Disable desktop notifications when set to `1`

---

## Compatibility

This project was developed and tested to work on major Linux desktop environments. Shortcut automation is most effective in the following environments:

*   **Ideal Support Environments:** GNOME, XFCE
*   **Guided Support Environments:** KDE Plasma
*   **Supported Distributions:** Any `apt`-based (Debian, Ubuntu), `pacman`-based (Arch Linux), `dnf`-based (Fedora), or `zypper`-based (openSUSE) distribution.

---

## Installation

1.  **Clone this repository:**
    ```bash
    git clone https://github.com/rouri404/GrabText.git
    cd GrabText
    ```

2.  **Make the installation script executable:**
    ```bash
    chmod +x install.sh
    ```

3.  **Run the installer:**
    ```bash
    ./install.sh
    ```
    The script will ask for your password to install system packages (if not already installed) and configure the rest of the environment.

---

## How to Use

### GUI Mode (Default)
1.  Press the `INSERT` key.
2.  The capture interface will appear. Select the desired area of the screen with the text.
3.  Press `Enter` or click the `✓` (Confirm) icon.
4.  The extracted text will be in your clipboard, ready to be pasted with `Ctrl+V`.

### CLI Mode Examples

**Basic Text Extraction:**
```bash
# Extract text from screen area
grabtext

# Extract text from a specific image
grabtext process document.png

# Extract text and save to file
grabtext process document.png -o extracted_text.txt
```

**Batch Processing:**
```bash
# Process all images in a directory
grabtext process ./images -r

# Export results in structured JSON format
grabtext process ./images -f json -o batch_results.json

# Export results in CSV format for spreadsheet analysis
grabtext process ./images -f csv -o batch_results.csv
```

**Advanced Usage:**
```bash
# Process with specific language
grabtext process document.png -l pt

# Monitor directory for new images
grabtext monitor ./incoming_images -f json

# Process without copying to clipboard
grabtext process document.png --no-clipboard -o output.txt

# Show what would be processed (dry run)
grabtext process ./images --dry-run
```

### Forcing OCR Language

You can force the OCR language (between English `en` and Portuguese `pt`) using the `GRABTEXT_LANG` environment variable.

*   **For a single execution:**
    ```bash
    GRABTEXT_LANG=en ./launch.sh
    ```
    or
    ```bash
    GRABTEXT_LANG=pt ./launch.sh
    ```

*   **To set permanently (e.g., in .bashrc or .zshrc):**
    Add the line below to the end of your shell configuration file (e.g., `~/.bashrc`):
    ```bash
    export GRABTEXT_LANG=en
    ```
    After editing the file, run `source ~/.bashrc` (or the corresponding file) to apply the change immediately.

---

## Troubleshooting

Common issues and solutions:

<details>
  <summary><strong>OCR not working properly</strong></summary>
  
  *   Ensure the image has good contrast and is not blurry.
  *   Try changing the OCR language with the `-l` flag.
  *   Check if Tesseract is installed correctly.
</details>

<details>
  <summary><strong>Command not found</strong></summary>
  
  *   Make sure `~/.local/bin` is in your PATH.
  *   Try running `source ~/.bashrc` or restarting your terminal.
  *   Re-run the installation script.
</details>

<details>
  <summary><strong>GUI capture not working</strong></summary>
  
  *   Check if Flameshot is installed and running.
  *   Ensure you're in a graphical environment.
  *   Try restarting the Flameshot service.
</details>

<details>
  <summary><strong>Logs not appearing</strong></summary>
  
  *   Check the log file at `~/.local/share/grabtext/grabtext.log`.
  *   Ensure you have write permissions in the log directory.
  *   Try using `grabtext logs --errors` to see error messages.
</details>

<details>
  <summary><strong>The shortcut was not created automatically. How do I configure it manually?</strong></summary>
  
  If automation failed or was skipped, you can configure the shortcut manually in a few steps. The command you'll need to use is the absolute path to the `launch.sh` script, which the installer created for you.
  
  **Example Command:** `/home/$USER/GrabText/launch.sh grab`

  Follow the guide corresponding to your desktop environment:

  #### For GNOME (Ubuntu, Fedora)
  1.  Open **Settings** > **Keyboard** > **Keyboard Shortcuts**.
  2.  Scroll to **Custom Shortcuts** and click the `+`.
  3.  Fill in the fields:
      * **Name:** `GrabText`
      * **Command:** Enter the full path to the `launch.sh` file, followed by `grab`. For example, `/home/$USER/GrabText/launch.sh grab`.
      * **Shortcut:** Press the `INSERT` key.
  4.  Click "Add".

  #### For KDE Plasma
  1.  Open **System Settings** > **Shortcuts** > **Custom Shortcuts**.
  2.  Go to `Edit` > `New` > `Global Shortcut` > `Command/URL`.
  3.  Fill in the fields:
      * **Name:** `GrabText`
      * **Trigger** tab: Press the `INSERT` key.
      * **Action** tab: In the "Command/URL" field, enter the full path to the `launch.sh` file, followed by `grab`. For example, `/home/$USER/GrabText/launch.sh grab`.
  4.  Click "Apply".

  #### For XFCE
  1.  Go to **Settings** > **Keyboard** > **Application Shortcuts**.
  2.  Click **"Add"**.
  3.  In the "Command" field, enter the full path to the `launch.sh` file, followed by `grab`. For example, `/home/$USER/GrabText/launch.sh grab`.
  4.  When the system asks for the key, press `INSERT`.
</details>

<details>
  <summary><strong>OCR does not extract any text or the result is incorrect.</strong></summary>
  
  OCR quality depends 99% on image quality. Remember best practices:
  * **High Contrast:** Dark text on a light, solid background works best.
  * **Standard Fonts:** Very artistic or small fonts are difficult to read.
  * **Good Resolution:** If the text on the screen is small, use zoom (`Ctrl` + `+`) in the application before capturing the screen.
</details>

<details>
  <summary><strong>How can I customize the appearance of the capture interface?</strong></summary>
  
  The interface appearance is controlled by Flameshot. To customize colors, buttons, and opacity, run the following command in the terminal:
  ```bash
  flameshot config
  ```
  The `install.sh` already applies a minimalist initial configuration, but you can adjust it as you prefer through this panel. If the appearance doesn't change after editing, try completely closing Flameshot with `killall flameshot` and triggering the shortcut again.
</details>

<details>
  <summary><strong>Where can I find logs for debugging?</strong></summary>
  
  GrabText generates a log file named `grabtext.log` in the project directory. This log is always in English and has a clean, structured format, which facilitates the identification and debugging of any issues that may arise during the tool's execution. You can consult it for detailed information about the OCR process and other operations.
</details>

<details>
  <summary><strong>JSON/CSV export not working properly</strong></summary>
  
  *   Ensure you have write permissions in the output directory.
  *   Check if the output file path is valid and accessible.
  *   For large batches, the process might take time - check the logs for progress.
  *   Verify that the images contain readable text for meaningful OCR results.
  *   Use `grabtext --debug` to see detailed processing information.
</details>

<details>
  <summary><strong>CSV file appears corrupted or has formatting issues</strong></summary>
  
  *   CSV files use proper escaping for text content with commas or quotes.
  *   Open the CSV file with a text editor first to verify the structure.
  *   Import into Excel/LibreOffice Calc using "Text to Columns" if needed.
  *   Check that the text content doesn't contain problematic characters.
</details>

For more help, run `grabtext help` or check the specific command help with `grabtext <command> --help`. When reporting issues, you can use `grabtext --debug` to get more detailed output that will help diagnose the problem.

---

### Manual Installation and Prerequisites

If the `install.sh` script encounters any errors, you can manually install the dependencies with the following commands:

#### For Arch Linux and derivatives (Manjaro, EndeavourOS)
```bash
sudo pacman -S flameshot tesseract tesseract-data-por tesseract-data-eng xclip python-pip libnotify
```

#### For Debian, Ubuntu, and derivatives (Mint, Pop!_OS)
```bash
sudo apt install flameshot tesseract-ocr tesseract-ocr-por tesseract-ocr-eng xclip python3-pip libnotify-bin
```

#### For Fedora
```bash
sudo dnf install flameshot tesseract tesseract-langpack-por langpacks-eng xclip python3-pip libnotify
```

#### For openSUSE
```bash
sudo zypper install flameshot tesseract-ocr tesseract-ocr-data-por tesseract-ocr-eng xclip python3-pip libnotify-tools
```
After manual installation, continue with step 2 in the **Installation** section above.

---

## Uninstallation

To remove GrabText and its components:

1.  Navigate to the project folder.
2.  Make the uninstaller executable:
    ```bash
    chmod +x uninstall.sh
    ```
3.  Run the script and follow the instructions:
    ```bash
    ./uninstall.sh
    ```