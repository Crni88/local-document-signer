"""Convert ordinary DOCX files using a separate, local Microsoft Word instance."""

import importlib.util
import io
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import zipfile


def word_available():
    if os.name != "nt" or importlib.util.find_spec("win32com") is None:
        return False
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"Word.Application\CLSID"):
            return True
    except OSError:
        return False


def convert_docx(contents):
    if not word_available():
        raise ValueError("DOCX conversion requires Microsoft Word on Windows. Export the document to PDF first.")
    try:
        with zipfile.ZipFile(io.BytesIO(contents)) as archive:
            names = archive.namelist()
            if "word/document.xml" not in names or any(name.lower().endswith("vbaproject.bin") for name in names):
                raise ValueError("Upload an ordinary, macro-free DOCX document.")
            if sum(entry.file_size for entry in archive.infolist()) > 100 * 1024 * 1024:
                raise ValueError("This Word document is too large after decompression.")
    except zipfile.BadZipFile as error:
        raise ValueError("This file is not a valid DOCX document.") from error

    with tempfile.TemporaryDirectory(prefix="local-sign-", ignore_cleanup_errors=True) as temporary:
        folder = Path(temporary)
        source = folder / "document.docx"
        destination = folder / "document.pdf"
        process_file = folder / "word.pid"
        source.write_bytes(contents)
        try:
            if getattr(sys, "frozen", False):
                cmd = [sys.executable, "--convert-word", str(source), str(destination), str(process_file)]
            else:
                cmd = [sys.executable, str(Path(__file__).resolve()), str(source), str(destination), str(process_file)]
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired as error:
            if process_file.is_file():
                try:
                    os.kill(int(process_file.read_text()), signal.SIGTERM)
                except (OSError, ValueError):
                    pass
            raise ValueError("Word conversion timed out. Export the document to PDF and upload that instead.") from error
        except subprocess.CalledProcessError as error:
            raise ValueError("Word could not convert this document. Close any Word dialogs, or export the document to PDF first.") from error
        if not destination.is_file():
            raise ValueError("Word did not produce a PDF. Export the document to PDF first.")
        return destination.read_bytes()


def run_word(source, destination, process_file):
    import pythoncom
    import win32com.client
    import win32process

    pythoncom.CoInitialize()
    word = None
    document = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        word.AutomationSecurity = 3
        word.Options.UpdateLinksAtOpen = False
        word.Options.UpdateFieldsAtPrint = False
        word.Options.UpdateLinksAtPrint = False
        document = word.Documents.Add(Visible=False)
        process_id = win32process.GetWindowThreadProcessId(document.Windows.Item(1).Hwnd)[1]
        Path(process_file).write_text(str(process_id))
        document.Close(False)
        document = None
        document = word.Documents.Open(
            str(source),
            ReadOnly=True,
            AddToRecentFiles=False,
            Visible=False,
            ConfirmConversions=False,
            NoEncodingDialog=True,
            PasswordDocument="__local_signer_no_password__",
        )
        document.ExportAsFixedFormat(str(destination), 17)
    finally:
        try:
            if document is not None:
                document.Close(False)
        finally:
            try:
                if word is not None:
                    word.Quit(False)
            finally:
                pythoncom.CoUninitialize()


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--convert-word":
        args = args[1:]
    run_word(*args)