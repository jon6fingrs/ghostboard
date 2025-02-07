# Ghostboard iOS Shortcuts Integration

Welcome to the iOS Shortcuts integration for Ghostboard! This directory includes two shortcuts designed to help you interact with your Ghostboard instance seamlessly on your Apple devices.

## Shortcuts Overview

### 1. **Copy Text Shortcut**
   - **File:** `Copy_text.shortcut`
   - **Function:** This shortcut copies the contents of your clipboard to a Ghostboard board.
   - **Steps:**
     1. Prompt to enter a board name (defaults to the root board if not specified).
     2. Retrieve the current contents of your clipboard.
     3. Send the clipboard contents to the Ghostboard server.

### 2. **Paste Text Shortcut**
   - **File:** `Paste_text.shortcut`
   - **Function:** This shortcut retrieves text from a Ghostboard board and gives you the option to save it as a file.
   - **Steps:**
     1. Prompt to enter a board name (defaults to the root board if not specified).
     2. Retrieve the current text from the specified board.
     3. If the board is empty, a message will notify you, and the shortcut ends.
     4. If text is found:
        - Copy the text to the clipboard.
        - Ask if you want to save the text as a file.
        - If you choose to save, you can specify the file name and location (or it defaults to ghostboard.txt).
        - If you choose not to save, the shortcut ends, allowing you to paste the text elsewhere.

## How to Use

1. **Download the Shortcuts:** Clone or download this repository and navigate to the `ios_shortcuts` directory.
2. **Import the Shortcuts:** Open each `.shortcut` file on your iOS device to import them into the Shortcuts app.
3. **Set Your Server Address:** When you import a shortcut, you will be prompted to enter your Ghostboard server hostname or IP address.
4. **Start Using:** Use the shortcuts to copy and paste text across your Ghostboard boards effortlessly!

## Example Use Case

- You want to share a snippet of text between your phone and computer. Use the **Copy Text Shortcut** to send it to Ghostboard. On your computer, open the board in your browser to view or further edit the text.
- Later, you can use the **Paste Text Shortcut** on your phone to retrieve the same text, save it as a file, or paste it into another app.

## Feedback & Contributions

We welcome feedback and suggestions! If you encounter any issues or have ideas for improvements, feel free to open an issue or submit a pull request.

Happy syncing!
"""

