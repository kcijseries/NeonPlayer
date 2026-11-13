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
