# Portfolio Showcase Guide: Local Document Signer

This guide provides technical summaries, copy snippets, hosting strategies, and UI embed components to help you showcase **Local Document Signer** on your developer portfolio.

---

## 1. Project Overview & Elevator Pitch

### Headline
> **Local Document Signer** — High-Performance, Privacy-First PDF Signing Desktop Application

### Elevator Pitch
> A local-first document signing tool built with Python, Flask, and PyMuPDF, packaged as a standalone Windows executable. It allows users to sign PDFs, Word documents, and scans entirely offline with customizable electronic signatures. Originals are preserved, and documents are processed in-memory without ever leaving the user's computer.

---

## 2. Technical Highlights (For Portfolio & Resume)

| Metric / Dimension | Specification |
| :--- | :--- |
| **Architecture** | Local-first client-server desktop hybrid (Flask backend + native GUI companion + browser frontend) |
| **Key Technologies** | Python 3.14, Flask 3.1, PyMuPDF (Fitz) 1.28, PyWin32 (COM Automation), PyInstaller, Vanilla ES6 JS, CSS3 |
| **Packaging** | Standalone zero-dependency Windows executable (`LocalDocumentSigner.exe`, PE 64-bit binary) |
| **Privacy Model** | 100% offline, `127.0.0.1` binding only, strictly in-memory PDF manipulation, zero telemetry |
| **Document Formats** | PDF (including multi-page & rotated), Word DOCX (isolated COM engine), PNG, JPG, TIFF, BMP, WEBP |
| **Security Controls** | Custom request origin validation (`X-Requested-With`), strict Content Security Policy, decompression-bomb protection |

---

## 3. Engineering Highlights (Great for Interviews)

When talking about this project to recruiters, engineering managers, or interviewers, emphasize these problems you solved:

1. **Subprocess Isolation for Word COM Automation**:
   - Problem: Automating Microsoft Word via `win32com` can hang or leak processes if a dialog opens or Word crashes. In a frozen PyInstaller `.exe`, spawning `sys.executable` re-launches the entire GUI app recursively.
   - Solution: Implemented a process-isolated worker mode with `--convert-word` argument routing. Word runs in an isolated child process with timeout guards and PID tracking, terminating cleanly if execution exceeds limits.

2. **Accurate Vector Font Rasterization & Derotation**:
   - Problem: PDFs often have mixed rotations (e.g., page 1 at 0°, page 2 at 90° landscape). A naive overlay places signatures upside-down or misaligned.
   - Solution: Created a dynamic signature engine with PyMuPDF that renders vector signatures from Windows font collections, crops exact ink bounding boxes, and calculates placement using page derotation matrices (`rectangle * page.derotation_matrix`).

3. **Zero-Configuration Desktop Experience**:
   - Problem: Most Python web apps require users to install Python, pip, open a terminal, run commands, and manually type `http://localhost:5050`.
   - Solution: Designed a Tkinter desktop companion that automatically detects an available port, launches the local server daemon, opens the user's default browser, and offers a clean GUI for copying URLs, reopening tabs, and graceful termination.

4. **Resource Resolution in Frozen Binaries**:
   - Handled PyInstaller's `sys._MEIPASS` dynamic unpacking directory to reliably locate Jinja2 templates, static CSS, JavaScript, and variable WOFF2 fonts without broken assets.

---

## 4. Distribution & Download Hosting Options

For your portfolio page, you can host the downloadable file using one of the following methods:

### Option A: GitHub Releases (Recommended — Free & Reliable)
1. Push the repository to GitHub.
2. Go to **Releases** -> **Create a new release** (e.g., `v1.0.0`).
3. Drag and drop `dist/LocalDocumentSigner.exe` or `dist/LocalDocumentSigner-Windows.zip`.
4. Use the direct release asset download URL on your portfolio button:
   ```html
   <a href="https://github.com/<your-username>/<repo>/releases/download/v1.0.0/LocalDocumentSigner-Windows.zip" class="btn-download">
     Download for Windows (.zip)
   </a>
   ```

### Option B: Cloudflare R2 / AWS S3 / Supabase Storage
- Upload `LocalDocumentSigner-Windows.zip` or `LocalDocumentSigner.exe` to an S3/R2 bucket with public read access.
- Benefits: Fast global CDN download speeds and custom domains (e.g., `download.yourportfolio.com/LocalDocumentSigner.exe`).

---

## 5. Ready-to-Use Portfolio Component (HTML/CSS)

You can drop this modern card into your portfolio website:

```html
<div class="project-card">
  <div class="project-badge">Desktop App &bull; Windows</div>
  <h3 class="project-title">Local Document Signer</h3>
  <p class="project-description">
    A privacy-centric desktop application for signing PDFs, Word documents, and images locally.
    Features real-time signature generation, interactive drag-and-drop placement, rotation handling,
    and 100% in-memory processing with zero cloud dependency.
  </p>

  <div class="tech-stack">
    <span class="pill">Python</span>
    <span class="pill">Flask</span>
    <span class="pill">PyMuPDF</span>
    <span class="pill">Vanilla JS</span>
    <span class="pill">PyInstaller</span>
  </div>

  <div class="project-actions">
    <a href="YOUR_DOWNLOAD_LINK" class="btn btn-primary" download>
      <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/><path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/></svg>
      Download Executable (Windows)
    </a>
    <a href="YOUR_GITHUB_REPO_URL" class="btn btn-secondary" target="_blank" rel="noopener">
      View Source
    </a>
  </div>
</div>
```

---

## 6. Verification Artifacts Summary

The following production artifacts have been built and verified:
- **Executable**: `dist/LocalDocumentSigner.exe` (Standalone Windows 64-bit executable)
- **Release Archive**: `dist/LocalDocumentSigner-Windows.zip` (Contains `.exe` and `README.txt`)
- **QuickStart Guide**: `dist/README.txt`
- **Branding Assets**: `app_icon.ico`, `app_icon.png`
- **Automated Verification**: `verify_executable.py` (Tests server start, static asset delivery, capabilities API, signature rendering API, and clean shutdown)
