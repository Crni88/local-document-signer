# AI Agent Instructions for Local Document Signer

Welcome! This workspace contains **Local Document Signer**, a local-first, privacy-focused document signing desktop application built with Python, Flask, PyMuPDF, and Vanilla HTML/CSS/JS.

---

## 1. UI / UX Design System (Strict Apple Design Guidelines)

All UI/UX changes **must strictly follow the Apple Design guidelines** documented in [.agents/rules/ui-ux-design.md](file:///c:/Users/TarikKA/Desktop/sign/.agents/rules/ui-ux-design.md).

### Non-Negotiable Rules:
1. **NO PURPLE / NEON GRADIENTS**:
   - Never use purple gradients, rainbow bars, or artificial AI-style glowing backgrounds.
   - The workspace background must remain a calm, clean Apple Studio solid neutral (`#f5f5f7` in light mode, `#121214` in dark mode).
2. **Apple Translucent Materials**:
   - Use subtle frosted glass headers and toolbars with `backdrop-filter: blur(20px) saturate(180%)`.
   - Sidebars use heavier frosted glass (`blur(24px)`).
3. **Apple System Palette**:
   - Accent Blue: `#0071e3` (light) / `#0a84ff` (dark).
   - System Green: `#34c759` / `#30d158`.
   - Alert Red: `#ff3b30` / `#ff453a`.
4. **Direct Manipulation & Physical Feedback**:
   - Instant response on pointer-down: all buttons scale to `0.96` on `:active`.
   - Signature dragging uses physical lift: scale `1.025x` and enlarged shadow (`drop-shadow(0 10px 20px rgba(0,0,0,0.2))`).
   - Squircles and rounded corners (`border-radius: 8px` to `10px`).
5. **System Typography**:
   - Use `-apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", Inter, system-ui, sans-serif`.
   - Optical tracking: tight headings (`-0.015em` to `-0.02em`), neutral body (`0`), relaxed microcopy (`+0.01em`).
   - Tabular numerals (`font-variant-numeric: tabular-nums`) on all numeric counters and percentages.

---

## 2. Desktop Packaging & Executable Rules

The application is distributed as a standalone Windows executable (`dist/LocalDocumentSigner.exe` and `dist/LocalDocumentSigner-Windows.zip`).

When modifying backend code, routes, or assets:
1. **Resource Path Resolution**:
   - Always resolve static and template paths using `get_bundle_dir()` in `app.py` to support PyInstaller's `sys._MEIPASS`.
2. **Word COM Subprocess Isolation**:
   - `word_conversion.py` runs Word in an isolated child process. In frozen mode, it must pass `--convert-word` so the executable calls `run_word` without re-spawning the GUI launcher.
3. **Rebuilding the Executable**:
   - Whenever you make changes to `static/`, `templates/`, `app.py`, or `launcher.py`, rebuild and package the distribution:
     ```powershell
     python -m PyInstaller LocalDocumentSigner.spec
     python package_release.py
     ```
4. **Verification**:
   - Run tests:
     ```powershell
     python -m unittest discover -v
     python verify_executable.py
     ```
