Fonts bundled with NeonPlayer
=============================

neurofont.otf              "Neuromax Cool Futuristic Gaming Logo" (c) 2025 UICreative, from fontspace.com.
                           Used for English, German, French, Spanish and Italian. Not covered by the OFL:
                           check the license on its FontSpace page before redistributing NeonPlayer publicly.
Exo2-Regular/Bold.ttf      Exo 2 (c) Natanael Gama - SIL Open Font License 1.1 (OFL-Exo2.txt).
                           Used for Polish and Russian (adds Latin Extended-A and Cyrillic). Static instances
                           generated from the original variable font.
NotoSansJP/KR/SC-*.otf     Noto Sans CJK (c) Adobe / Google - SIL Open Font License 1.1 (OFL-NotoSansCJK.txt).
                           Used for Japanese, Korean and Simplified Chinese. Trimmed with fonttools to JIS X 0208 /
                           KS X 1001 / GB 2312 plus all characters used by the translations (original files:
                           github.com/notofonts/noto-cjk). Characters outside these sets fall back to system fonts.

To swap a font without rebuilding the AppImage, put a file with the same name in NeonPlayer-data/fonts/.
Regenerate the subsets with tools/make_fonts.py.


Pygame CPU optimization
-----------------------
On native x86-64 Linux, install.sh checks whether the installed Pygame lacks
AVX2 blitters on an AVX2-capable CPU. If so, it attempts a source build with
PYGAME_DETECT_AVX2=1. Pygame's AVX2 routines are runtime-dispatched through
SDL_HasAVX2(); CPUs without AVX2 continue using the standard blitters. If the
source build cannot complete (for example, missing compiler/SDL development
packages), the installer falls back to the standard portable Pygame wheel.
Other operating systems and architectures use the standard Pygame package.
