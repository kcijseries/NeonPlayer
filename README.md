# <img width="334" height="73" alt="Screenshot_20261113_203121" src="https://github.com/user-attachments/assets/5e936b7c-0a23-48d3-ad33-761800277972" />


### Your music. Your world. Your frequency.

**NeonPlayer** is a futuristic, cyberpunk-inspired desktop music player for Linux & Windows x64, built with Python and PyQt6.

Designed to combine an immersive visual experience with powerful music library management, NeonPlayer brings together album artwork browsing, advanced audio playback, gamepad navigation and Linux desktop integration in one distinctive application.

Featuring a neon-soaked interface, animated audio visualization and a custom dual-player playback engine, NeonPlayer is designed for people who want more from their desktop music experience.

<sub>Linux Desktop Application · Python · PyQt6 · AppImage . Windows x64 EXE</sub>

---



## 🎬 NeonPlayer 2.0 — Video Walkthrough

[![NeonPlayer 2.0 Video Walkthrough](https://img.youtube.com/vi/dVA5soJM36w/maxresdefault.jpg)](https://www.youtube.com/watch?v=dVA5soJM36w)

*Watch NeonPlayer in action!*

## 📸 Screenshots

<img width="756" height="506" alt="Screenshot_20261113_202350" src="https://github.com/user-attachments/assets/79b90873-7ee9-4d88-bada-3561f914d9a4" />
<img width="1917" height="1080" alt="Screenshot_20261113_202339" src="https://github.com/user-attachments/assets/5274826e-8332-4ec9-b08b-d469f89006f2" />
<img width="1909" height="1077" alt="Screenshot_20261113_202327" src="https://github.com/user-attachments/assets/a77d7827-773a-4ae4-bd02-3ebbc54378f5" />

---

## ✨ Features

### 🎨 Futuristic Interface

- Cyberpunk-inspired visual design.
- Neon cyan, magenta and purple visual accents.
- Artwork-focused album browsing.
- Custom application icon and futuristic skyline background.
- Dedicated Now Playing interface.
- Compact Mini Player mode.
- Fullscreen mode.
- Custom typography and bundled fonts.

### 🎵 Music Library Management

Explore and organize your personal music collection through multiple browsing categories.

- **Albums** – Browse your collection through album artwork.
- **Artists** – Explore music organized by artist.
- **Genres** – Browse music by genre.
- **Folders** – Navigate your existing music folder structure.
- **Search** – Find music within your collection.
- **Playlists** – Create and manage custom playlists.
- **Favorites** – Keep track of your favorite music.
- **Recently Added** – Quickly find newly added tracks.
- **Library Scanning** – Scan music folders and update your library.
- **Library Cache** – Maintain a local music library index.

### 🔊 Advanced Audio Playback

NeonPlayer features a custom dual-player audio engine designed to provide smooth playback transitions.

- **Gapless Playback** – Seamless transitions between tracks.
- **Crossfade** – Blend consecutive tracks together.
- **Dual-Player Architecture** – Prepare upcoming tracks for smooth transitions.
- **Playback Queue** – Manage upcoming music.
- **Shuffle** – Randomize playback order.
- **Repeat** – Control repeat playback.
- **Seek Controls** – Navigate through individual tracks.
- **Volume Control** – Adjust playback volume.
- **Session Restoration** – Restore previous playback sessions.

Available crossfade settings:

- Off (gapless playback)
- 2 seconds
- 4 seconds
- 6 seconds
- 8 seconds
- 10 seconds

### 📊 Audio Visualization

Bring your music to life with real-time audio analysis.

- FFT-based audio spectrum analysis.
- 44 frequency bands.
- Logarithmically spaced frequency ranges.
- Animated spectrum visualization.
- Visual fallback when real-time spectrum analysis is unavailable.

The audio analysis system uses NumPy and Qt Multimedia audio buffers.

### 🎮 Gamepad Support

NeonPlayer includes optional gamepad support using pygame and SDL GameController.

Designed with Xbox-style controller layouts in mind, gamepad navigation allows you to control your music without needing a keyboard or mouse.

Features include:

- Navigate the music library.
- Browse and select albums.
- Control playback.
- Skip between tracks.
- Adjust volume.
- Seek through tracks.
- Toggle shuffle and repeat.
- Manage the playback queue.
- Switch between the main interface and Mini Player.
- Access the sleep timer.

Gamepad support is optional. NeonPlayer can also be operated using a standard keyboard and mouse.

### 🖥️ Linux Desktop Integration

NeonPlayer supports MPRIS2 media integration for Linux desktop environments.

Supported integration includes:

- KDE Plasma media controls.
- Desktop media player widgets.
- Hardware media keys.
- External playback control through compatible MPRIS clients.
- Playback status reporting.
- Track metadata.
- Playback position.
- Shuffle and repeat controls.

MPRIS integration uses D-Bus and QtDBus.

### 🌍 Multilingual Interface

NeonPlayer includes ten interface languages.

| Language | Native Name |
|---|---|
| English | English |
| German | Deutsch |
| Japanese | 日本語 |
| French | Français |
| Spanish | Español |
| Italian | Italiano |
| Korean | 한국어 |
| Russian | Русский |
| Polish | Polski |
| Simplified Chinese | 简体中文 |

The application includes bundled fonts to support international character rendering.

### ⏱️ Additional Features

- Configurable sleep timer.
- Persistent application settings.
- Playback session management.
- Album artwork extraction.
- Audio metadata reading.
- Custom skyline background.
- Portable AppImage distribution.
- Desktop launcher installation.

---

## 📥 Installation

### Recommended: AppImage (Windows x64 EXE Now available in releases!)

The easiest way to use NeonPlayer is through the prebuilt Linux AppImage.

**1. Download NeonPlayer**

Visit the [Releases](https://github.com/kcijseries/NeonPlayer/releases) page and download the latest AppImage.

**2. Make the file executable**

Open a terminal in your download directory:

```bash
chmod +x NeonPlayer-x86_64.AppImage
```

**3. Launch NeonPlayer**

```bash
./NeonPlayer-x86_64.AppImage
```

That's it! No traditional installation is required.

### Desktop Integration

NeonPlayer includes an installation script for desktop integration when installed from source.

See the source installation instructions below.

---

## 🛠️ Installation from Source

NeonPlayer can also be run directly from its Python source code.

### Requirements

- Linux operating system.
- Python 3.
- Python virtual environment support.
- PyQt6.
- Qt Multimedia.
- Mutagen.
- NumPy.
- pygame (for gamepad support).

### 1. Clone the repository

```bash
git clone https://github.com/kcijseries/NeonPlayer.git
```

### 2. Enter the project directory

```bash
cd NeonPlayer
```

### 3. Run the installation script

```bash
chmod +x install.sh
./install.sh
```

The installation script prepares the Python environment and installs the application dependencies.

### 4. Launch NeonPlayer

```bash
./run.sh
```

---

## 🔧 Building the AppImage

NeonPlayer includes a dedicated AppImage build script.

The build system is designed to package the application and its Python dependencies into a portable Linux executable.

### Build requirements

- Linux x86_64 environment.
- Bash.
- curl.
- tar.
- Internet connection for downloading build dependencies.
- Sufficient disk space for the build environment.

### Build instructions

From the project directory:

```bash
chmod +x build-appimage.sh
./build-appimage.sh
```

The build script prepares the application environment and packages NeonPlayer into an AppImage.

Expected output:

```text
NeonPlayer-x86_64.AppImage
```

The resulting AppImage can be distributed independently of the source installation.

---

## 🎧 Supported Audio Formats

NeonPlayer recognizes the following audio file extensions:

| Format | Extension |
|---|---|
| MP3 | `.mp3` |
| WAV | `.wav` |
| FLAC | `.flac` |
| OGG | `.ogg` |
| OGA | `.oga` |
| Opus | `.opus` |
| MPEG-4 Audio | `.m4a` |
| AAC | `.aac` |
| Windows Media Audio | `.wma` |
| AIFF | `.aiff`, `.aif` |
| Monkey's Audio | `.ape` |

Actual playback compatibility depends on the installed or bundled Qt Multimedia backend and available codecs.

---

## 🖼️ Album Artwork & Metadata

NeonPlayer uses audio metadata and album artwork to provide a visually rich music browsing experience.

Artwork can be obtained from supported embedded audio metadata and recognized image files in music folders.

Supported artwork image formats include:

- JPEG
- PNG
- WebP

The Mutagen library is used for audio metadata handling.

---

## 📁 Project Structure

The project is organized into separate modules for its main application functionality.

| File / Directory | Description |
|---|---|
| `neonplayer.py` | Main application and graphical interface |
| `engine.py` | Audio playback engine and visualization |
| `gamepad.py` | Gamepad and controller support |
| `i18n.py` | Internationalization and translations |
| `mpris.py` | Linux MPRIS2 integration |
| `install.sh` | Installation script |
| `run.sh` | Application launcher |
| `build-appimage.sh` | AppImage build system |
| `fonts/` | Bundled fonts and associated license files |
| `neonplayer.png` | Application icon |
| `skyline.png` | Background artwork |

---

## 🧩 Technology Stack

NeonPlayer is built using a combination of Python libraries and Linux desktop technologies.

| Technology | Purpose |
|---|---|
| Python | Core application |
| PyQt6 | Graphical interface |
| Qt Multimedia | Audio playback |
| QtDBus | Linux desktop integration |
| Mutagen | Audio metadata |
| NumPy | Audio spectrum analysis |
| pygame | Gamepad input |
| SDL2 | Controller support |
| AppImage | Portable application distribution |

---

## 🙏 Credits & Acknowledgements

NeonPlayer uses the following open-source technologies and third-party resources.

### Software

- [Python](https://www.python.org/)
- [PyQt6](https://riverbankcomputing.com/software/pyqt/)
- [Qt](https://www.qt.io/)
- [Mutagen](https://mutagen.readthedocs.io/)
- [NumPy](https://numpy.org/)
- [pygame](https://www.pygame.org/)
- [SDL](https://www.libsdl.org/)

### Fonts

The application includes bundled fonts for its interface and international language support.

- Exo 2 — Natanael Gama.
- Noto Sans CJK — Adobe / Google.
- Neuromax — UICreative.

Exo 2 and Noto Sans CJK are distributed under the SIL Open Font License 1.1.

Please refer to the accompanying font license files for licensing and attribution information.

---

## 📦 Downloads

Get the latest version of NeonPlayer:

### [⬇️ Download NeonPlayer](https://github.com/kcijseries/NeonPlayer/releases)

Prebuilt Linux AppImage releases will be published here.

---

## 🐛 Bug Reports & Feature Requests

Found a bug or have an idea for improving NeonPlayer?

Please use the GitHub Issues section to report problems, suggest features or provide feedback.

[Report an Issue](https://github.com/kcijseries/NeonPlayer/issues)

When reporting a bug, please include:

- Your Linux distribution.
- NeonPlayer version.
- Steps to reproduce the problem.
- Relevant error messages or application logs.
- Screenshots where applicable.

---

## 📜 License

The project license is currently to be determined.

Third-party libraries and bundled resources remain subject to their respective licenses. See the accompanying license files for details.

---

## 💜 About NeonPlayer

NeonPlayer was created with one goal in mind:

**Make listening to your music collection feel like an experience.**

Combining futuristic visual design, a powerful playback engine and practical Linux desktop functionality, NeonPlayer brings a distinctive cyberpunk atmosphere to everyday music listening.

Forget the ordinary.

**Enter the Neon.**
