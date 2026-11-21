"""NeonPlayer translations.

English strings are the keys. Columns: de, ja, fr, es, it, ko, ru, pl, zh (Simplified Chinese).
Placeholders like {n} are filled by tr(key, n=...). Plural-free phrasing is used on purpose.
"""

ORDER = ["de", "ja", "fr", "es", "it", "ko", "ru", "pl", "zh"]

# (native name shown in the language menu)
LANGS = [("en", "English"), ("de", "Deutsch"), ("ja", "日本語"), ("fr", "Français"),
         ("es", "Español"), ("it", "Italiano"), ("ko", "한국어"), ("ru", "Русский"),
         ("pl", "Polski"), ("zh", "中文（简体）")]

# Which bundled font(s) each language uses (logical names, see FONT_FILES in neonplayer.py).
# Neuromax (the user's font) covers English + Latin-1 (de, fr, es, it); it lacks Polish
# letters, Cyrillic and CJK, which are served by Exo 2 and the Noto Sans CJK subsets.
FONT_CHAIN = {"en": ["neuro"], "de": ["neuro"], "fr": ["neuro"], "es": ["neuro"], "it": ["neuro"],
              "pl": ["exo2"], "ru": ["exo2"],
              "ja": ["jp", "exo2"], "ko": ["kr", "exo2"], "zh": ["sc", "exo2"]}

# Neuromax has no "…" glyph, so these languages use three dots instead.
ELLIPSIS_FIX = {"en", "de", "fr", "es", "it"}

T = {
    # --- sidebar / modes ---
    "Folders": ("Ordner", "フォルダー", "Dossiers", "Carpetas", "Cartelle", "폴더", "Папки", "Foldery", "文件夹"),
    "Artists": ("Künstler", "アーティスト", "Artistes", "Artistas", "Artisti", "아티스트", "Исполнители", "Wykonawcy", "艺术家"),
    "Albums": ("Alben", "アルバム", "Albums", "Álbumes", "Album", "앨범", "Альбомы", "Albumy", "专辑"),
    "Genres": ("Genres", "ジャンル", "Genres", "Géneros", "Generi", "장르", "Жанры", "Gatunki", "流派"),
    "Playlists": ("Playlists", "プレイリスト", "Playlists", "Listas", "Playlist", "재생목록", "Плейлисты", "Playlisty", "播放列表"),
    "Favorites": ("Favoriten", "お気に入り", "Favoris", "Favoritos", "Preferiti", "즐겨찾기", "Избранное", "Ulubione", "收藏"),
    "Recently Added": ("Neu hinzugefügt", "最近追加", "Ajouts récents", "Recientes", "Recenti", "최근 추가", "Недавние", "Ostatnio dodane", "最近添加"),
    "Now Playing": ("Aktuelle Wiedergabe", "再生中", "En lecture", "Reproduciendo", "In riproduzione", "재생 중", "Сейчас играет", "Teraz gra", "正在播放"),
    "Queue": ("Warteschlange", "キュー", "File d'attente", "Cola", "Coda", "대기열", "Очередь", "Kolejka", "队列"),
    "Mini Player": ("Mini-Player", "ミニプレーヤー", "Mini-lecteur", "Mini reproductor", "Mini player", "미니 플레이어", "Мини-плеер", "Mini odtwarzacz", "迷你播放器"),
    "Settings": ("Einstellungen", "設定", "Paramètres", "Ajustes", "Impostazioni", "설정", "Настройки", "Ustawienia", "设置"),
    "Gamepad": ("Gamepad", "ゲームパッド", "Manette", "Mando", "Gamepad", "게임패드", "Геймпад", "Pad", "手柄"),
    "Search albums, artists, tracks…": (
        "Alben, Künstler, Titel suchen…", "アルバム・アーティスト・曲を検索…",
        "Rechercher albums, artistes, titres…", "Buscar álbumes, artistas, pistas…",
        "Cerca album, artisti, brani…", "앨범, 아티스트, 트랙 검색…",
        "Поиск по библиотеке…", "Szukaj w bibliotece…", "搜索专辑、艺术家、曲目…"),
    # --- player screen ---
    "Library": ("Bibliothek", "ライブラリ", "Bibliothèque", "Biblioteca", "Libreria", "라이브러리", "Библиотека", "Biblioteka", "音乐库"),
    "Stop": ("Stopp", "停止", "Arrêt", "Parar", "Stop", "정지", "Стоп", "Stop", "停止"),
    "Mini": ("Mini", "ミニ", "Mini", "Mini", "Mini", "미니", "Мини", "Mini", "迷你"),
    "Back to the library — music keeps playing": (
        "Zurück zur Bibliothek – die Musik läuft weiter", "ライブラリに戻る — 音楽は再生し続けます",
        "Retour à la bibliothèque — la musique continue", "Volver a la biblioteca: la música sigue sonando",
        "Torna alla libreria — la musica continua", "라이브러리로 돌아가기 — 음악은 계속 재생됩니다",
        "Назад в библиотеку — музыка продолжает играть", "Powrót do biblioteki — muzyka gra dalej",
        "返回音乐库——音乐继续播放"),
    "Stop playback and close the player": (
        "Wiedergabe stoppen und Player schließen", "再生を停止してプレーヤーを閉じる",
        "Arrêter la lecture et fermer le lecteur", "Detener la reproducción y cerrar el reproductor",
        "Ferma la riproduzione e chiudi il player", "재생을 멈추고 플레이어 닫기",
        "Остановить воспроизведение и закрыть плеер", "Zatrzymaj odtwarzanie i zamknij odtwarzacz",
        "停止播放并关闭播放器"),
    "Switch to the small always-on-top player": (
        "Zum kleinen Player im Vordergrund wechseln", "常に手前に表示される小型プレーヤーに切り替え",
        "Passer au petit lecteur toujours au premier plan", "Cambiar al reproductor pequeño siempre visible",
        "Passa al piccolo player sempre in primo piano", "항상 위에 표시되는 작은 플레이어로 전환",
        "Переключиться на мини-плеер поверх окон", "Przełącz na mały odtwarzacz zawsze na wierzchu",
        "切换到始终置顶的小播放器"),
    "Sleep timer": ("Schlaf-Timer", "スリープタイマー", "Minuterie de veille", "Temporizador de sueño", "Timer di spegnimento", "취침 타이머", "Таймер сна", "Wyłącznik czasowy", "睡眠定时器"),
    "Album": ("Album", "アルバム", "Album", "Álbum", "Album", "앨범", "Альбом", "Album", "专辑"),
    "Queue all": ("Alle einreihen", "すべて追加", "Tout ajouter", "Añadir todo", "Accoda tutto", "모두 추가", "Все в очередь", "Dodaj wszystko", "全部加入队列"),
    "Clear": ("Leeren", "クリア", "Vider", "Vaciar", "Svuota", "비우기", "Очистить", "Wyczyść", "清空"),
    "Save…": ("Speichern…", "保存…", "Enregistrer…", "Guardar…", "Salva…", "저장…", "Сохранить…", "Zapisz…", "保存…"),
    "VOL": ("LAUT", "音量", "VOL", "VOL", "VOL", "음량", "ГРОМК.", "GŁOŚ.", "音量"),
    "From queue": ("Aus der Warteschlange", "キューから", "Depuis la file", "Desde la cola", "Dalla coda", "대기열에서", "Из очереди", "Z kolejki", "来自队列"),
    "Nothing playing": ("Keine Wiedergabe", "再生していません", "Aucune lecture", "Nada en reproducción", "Nessuna riproduzione", "재생 중인 항목 없음", "Ничего не играет", "Nic nie jest odtwarzane", "未在播放"),
    "Open": ("Öffnen", "開く", "Ouvrir", "Abrir", "Apri", "열기", "Открыть", "Otwórz", "打开"),
    "end of track": ("Titelende", "トラック終了時", "fin du morceau", "fin de la pista", "fine del brano", "트랙 종료 시", "конец трека", "koniec utworu", "曲目结束"),
    # --- settings menu ---
    "Language": ("Sprache", "言語", "Langue", "Idioma", "Lingua", "언어", "Язык", "Język", "语言"),
    "Change library…": ("Bibliothek ändern…", "ライブラリを変更…", "Changer de bibliothèque…", "Cambiar biblioteca…", "Cambia libreria…", "라이브러리 변경…", "Сменить библиотеку…", "Zmień bibliotekę…", "更改音乐库…"),
    "Rescan library (changes only)": (
        "Bibliothek neu scannen (nur Änderungen)", "ライブラリを再スキャン（変更分のみ）",
        "Réanalyser la bibliothèque (changements uniquement)", "Volver a explorar la biblioteca (solo cambios)",
        "Riscansiona la libreria (solo modifiche)", "라이브러리 다시 검색(변경 사항만)",
        "Пересканировать библиотеку (только изменения)", "Przeskanuj bibliotekę (tylko zmiany)",
        "重新扫描音乐库（仅更改）"),
    "Rebuild cache (full rescan)": (
        "Cache neu aufbauen (vollständiger Scan)", "キャッシュを再構築（完全スキャン）",
        "Reconstruire le cache (analyse complète)", "Reconstruir caché (exploración completa)",
        "Ricostruisci la cache (scansione completa)", "캐시 다시 만들기(전체 검색)",
        "Пересоздать кэш (полное сканирование)", "Odbuduj pamięć podręczną (pełne skanowanie)",
        "重建缓存（完整扫描）"),
    "Crossfade": ("Überblendung", "クロスフェード", "Fondu enchaîné", "Fundido cruzado", "Dissolvenza incrociata", "크로스페이드", "Плавный переход", "Płynne przejście", "淡入淡出"),
    "Off (gapless)": ("Aus (lückenlos)", "オフ（ギャップレス）", "Désactivé (sans coupure)", "Desactivado (sin pausas)", "Disattivato (gapless)", "끄기(갭리스)", "Выкл. (без пауз)", "Wyłączone (bez przerw)", "关闭（无缝播放）"),
    "{n} s": ("{n} s", "{n}秒", "{n} s", "{n} s", "{n} s", "{n}초", "{n} с", "{n} s", "{n}秒"),
    "Off": ("Aus", "オフ", "Désactivé", "Desactivado", "Disattivato", "끄기", "Выкл.", "Wyłączone", "关闭"),
    "{n} min": ("{n} Min.", "{n}分", "{n} min", "{n} min", "{n} min", "{n}분", "{n} мин", "{n} min", "{n}分钟"),
    "End of this track": ("Ende dieses Titels", "このトラックの終わり", "Fin de ce morceau", "Al final de esta pista", "Fine di questo brano", "이 트랙이 끝나면", "В конце этого трека", "Na końcu tego utworu", "本曲结束时"),
    "Resume last session on launch": (
        "Letzte Sitzung beim Start fortsetzen", "起動時に前回のセッションを再開",
        "Reprendre la dernière session au lancement", "Reanudar la última sesión al iniciar",
        "Riprendi l'ultima sessione all'avvio", "시작할 때 마지막 세션 이어서 재생",
        "Продолжить прошлый сеанс при запуске", "Wznów ostatnią sesję przy uruchomieniu",
        "启动时恢复上次会话"),
    "Mini player (Ctrl+M)": ("Mini-Player (Strg+M)", "ミニプレーヤー (Ctrl+M)", "Mini-lecteur (Ctrl+M)", "Mini reproductor (Ctrl+M)", "Mini player (Ctrl+M)", "미니 플레이어 (Ctrl+M)", "Мини-плеер (Ctrl+M)", "Mini odtwarzacz (Ctrl+M)", "迷你播放器 (Ctrl+M)"),
    "Toggle fullscreen (F11)": ("Vollbild umschalten (F11)", "全画面表示の切り替え (F11)", "Basculer en plein écran (F11)", "Alternar pantalla completa (F11)", "Attiva/disattiva schermo intero (F11)", "전체 화면 전환 (F11)", "Полноэкранный режим (F11)", "Przełącz pełny ekran (F11)", "切换全屏 (F11)"),
    "Cache folder: {path}": ("Cache-Ordner: {path}", "キャッシュフォルダー: {path}", "Dossier du cache : {path}", "Carpeta de caché: {path}", "Cartella della cache: {path}", "캐시 폴더: {path}", "Папка кэша: {path}", "Folder pamięci podręcznej: {path}", "缓存文件夹：{path}"),
    "Media keys (MPRIS): {state}": ("Medientasten (MPRIS): {state}", "メディアキー (MPRIS): {state}", "Touches multimédia (MPRIS) : {state}", "Teclas multimedia (MPRIS): {state}", "Tasti multimediali (MPRIS): {state}", "미디어 키(MPRIS): {state}", "Мультимедийные клавиши (MPRIS): {state}", "Klawisze multimedialne (MPRIS): {state}", "媒体键 (MPRIS)：{state}"),
    "active": ("aktiv", "有効", "actif", "activo", "attivo", "활성", "активно", "aktywne", "已启用"),
    "unavailable": ("nicht verfügbar", "利用不可", "indisponible", "no disponible", "non disponibile", "사용 불가", "недоступно", "niedostępne", "不可用"),
    "Spectrum: {state}": ("Spektrum: {state}", "スペクトラム: {state}", "Spectre : {state}", "Espectro: {state}", "Spettro: {state}", "스펙트럼: {state}", "Спектр: {state}", "Widmo: {state}", "频谱：{state}"),
    "real-time FFT": ("Echtzeit-FFT", "リアルタイムFFT", "FFT en temps réel", "FFT en tiempo real", "FFT in tempo reale", "실시간 FFT", "FFT в реальном времени", "FFT w czasie rzeczywistym", "实时 FFT"),
    "animated (needs numpy)": ("animiert (benötigt numpy)", "アニメーション（numpyが必要）", "animé (nécessite numpy)", "animado (requiere numpy)", "animato (richiede numpy)", "애니메이션(numpy 필요)", "анимация (нужен numpy)", "animowane (wymaga numpy)", "动画（需要 numpy）"),
    "Controller: {state}": ("Controller: {state}", "コントローラー: {state}", "Manette : {state}", "Mando: {state}", "Controller: {state}", "컨트롤러: {state}", "Контроллер: {state}", "Kontroler: {state}", "手柄：{state}"),
    "none detected": ("keiner erkannt", "検出なし", "aucune détectée", "ninguno detectado", "nessuno rilevato", "감지되지 않음", "не обнаружен", "nie wykryto", "未检测到"),
    "needs pygame": ("benötigt pygame", "pygameが必要", "nécessite pygame", "requiere pygame", "richiede pygame", "pygame 필요", "нужен pygame", "wymaga pygame", "需要 pygame"),
    "⚠ Cache save failed: {err}": ("⚠ Cache konnte nicht gespeichert werden: {err}", "⚠ キャッシュを保存できませんでした: {err}", "⚠ Échec de l'enregistrement du cache : {err}", "⚠ No se pudo guardar la caché: {err}", "⚠ Salvataggio della cache non riuscito: {err}", "⚠ 캐시 저장 실패: {err}", "⚠ Не удалось сохранить кэш: {err}", "⚠ Nie udało się zapisać pamięci podręcznej: {err}", "⚠ 缓存保存失败：{err}"),
    # --- library / status ---
    "Where do you keep your music library?": ("Wo befindet sich Ihre Musikbibliothek?", "音楽ライブラリはどこにありますか？", "Où se trouve votre bibliothèque musicale ?", "¿Dónde guarda su biblioteca de música?", "Dove si trova la tua libreria musicale?", "음악 라이브러리는 어디에 있나요?", "Где находится ваша музыкальная библиотека?", "Gdzie znajduje się Twoja biblioteka muzyczna?", "您的音乐库在哪里？"),
    "Loading…": ("Lädt…", "読み込み中…", "Chargement…", "Cargando…", "Caricamento…", "불러오는 중…", "Загрузка…", "Wczytywanie…", "加载中…"),
    "Scanning…": ("Scannen…", "スキャン中…", "Analyse…", "Explorando…", "Scansione…", "검색 중…", "Сканирование…", "Skanowanie…", "扫描中…"),
    "Scanning… (folders: {n})": ("Scannen… (Ordner: {n})", "スキャン中…（フォルダー: {n}）", "Analyse… (dossiers : {n})", "Explorando… (carpetas: {n})", "Scansione… (cartelle: {n})", "검색 중… (폴더: {n})", "Сканирование… (папок: {n})", "Skanowanie… (folderów: {n})", "扫描中…（文件夹：{n}）"),
    "{name} (loose tracks)": ("{name} (einzelne Titel)", "{name}（単独トラック）", "{name} (pistes isolées)", "{name} (pistas sueltas)", "{name} (brani singoli)", "{name} (개별 트랙)", "{name} (отдельные треки)", "{name} (luźne utwory)", "{name}（零散曲目）"),
    "No playlists yet — add tracks to the queue and press Save…": (
        "Noch keine Playlists – Titel zur Warteschlange hinzufügen und „Speichern…“ drücken",
        "プレイリストはまだありません — キューに曲を追加して「保存…」を押してください",
        "Aucune playlist — ajoutez des pistes à la file et appuyez sur « Enregistrer… »",
        "Aún no hay listas — añada pistas a la cola y pulse «Guardar…»",
        "Nessuna playlist — aggiungi brani alla coda e premi «Salva…»",
        "재생목록이 없습니다 — 대기열에 트랙을 추가하고 ‘저장…’을 누르세요",
        "Плейлистов пока нет — добавьте треки в очередь и нажмите «Сохранить…»",
        "Brak playlist — dodaj utwory do kolejki i naciśnij „Zapisz…”",
        "还没有播放列表——将曲目加入队列并点击“保存…”"),
    "No music found in that folder": ("In diesem Ordner wurde keine Musik gefunden", "このフォルダーに音楽が見つかりません", "Aucune musique trouvée dans ce dossier", "No se encontró música en esa carpeta", "Nessuna musica trovata in questa cartella", "이 폴더에서 음악을 찾을 수 없습니다", "В этой папке музыка не найдена", "Nie znaleziono muzyki w tym folderze", "在该文件夹中未找到音乐"),
    "No favorites yet — press ♡ in the player": ("Noch keine Favoriten – im Player ♡ drücken", "お気に入りはまだありません — プレーヤーで ♡ を押してください", "Aucun favori — appuyez sur ♡ dans le lecteur", "Aún no hay favoritos: pulse ♡ en el reproductor", "Nessun preferito — premi ♡ nel player", "즐겨찾기가 없습니다 — 플레이어에서 ♡를 누르세요", "Избранного пока нет — нажмите ♡ в плеере", "Brak ulubionych — naciśnij ♡ w odtwarzaczu", "还没有收藏——在播放器中点击 ♡"),
    "No results": ("Keine Ergebnisse", "結果なし", "Aucun résultat", "Sin resultados", "Nessun risultato", "결과 없음", "Ничего не найдено", "Brak wyników", "无结果"),
    "Nothing here": ("Hier ist nichts", "ここには何もありません", "Rien ici", "No hay nada aquí", "Niente qui", "항목이 없습니다", "Здесь пусто", "Nic tu nie ma", "这里空空如也"),
    "Search": ("Suche", "検索", "Recherche", "Búsqueda", "Ricerca", "검색", "Поиск", "Wyszukiwanie", "搜索"),
    "Items: {n}": ("Elemente: {n}", "項目: {n}", "Éléments : {n}", "Elementos: {n}", "Elementi: {n}", "항목: {n}", "Элементов: {n}", "Elementów: {n}", "项目：{n}"),
    "Unknown Artist": ("Unbekannter Künstler", "不明なアーティスト", "Artiste inconnu", "Artista desconocido", "Artista sconosciuto", "알 수 없는 아티스트", "Неизвестный исполнитель", "Nieznany wykonawca", "未知艺术家"),
    "Unknown Genre": ("Unbekanntes Genre", "不明なジャンル", "Genre inconnu", "Género desconocido", "Genere sconosciuto", "알 수 없는 장르", "Неизвестный жанр", "Nieznany gatunek", "未知流派"),
    # --- menus / tooltips / dialogs ---
    "Add to queue": ("Zur Warteschlange hinzufügen", "キューに追加", "Ajouter à la file", "Añadir a la cola", "Aggiungi alla coda", "대기열에 추가", "Добавить в очередь", "Dodaj do kolejki", "加入队列"),
    "Play next": ("Als Nächstes abspielen", "次に再生", "Lire ensuite", "Reproducir a continuación", "Riproduci come prossimo", "다음에 재생", "Играть следующим", "Odtwórz jako następny", "下一首播放"),
    "Delete playlist": ("Playlist löschen", "プレイリストを削除", "Supprimer la playlist", "Eliminar lista", "Elimina playlist", "재생목록 삭제", "Удалить плейлист", "Usuń playlistę", "删除播放列表"),
    "Play now": ("Jetzt abspielen", "今すぐ再生", "Lire maintenant", "Reproducir ahora", "Riproduci ora", "지금 재생", "Играть сейчас", "Odtwórz teraz", "立即播放"),
    "Move to top": ("Nach oben verschieben", "先頭に移動", "Placer en tête", "Mover al principio", "Sposta in cima", "맨 위로 이동", "Переместить наверх", "Przenieś na początek", "移到顶部"),
    "Remove": ("Entfernen", "削除", "Retirer", "Quitar", "Rimuovi", "제거", "Удалить", "Usuń", "移除"),
    "Tracks added to the queue: {n}": ("Titel zur Warteschlange hinzugefügt: {n}", "キューに追加した曲数: {n}", "Pistes ajoutées à la file : {n}", "Pistas añadidas a la cola: {n}", "Brani aggiunti alla coda: {n}", "대기열에 추가된 트랙: {n}", "Добавлено в очередь: {n}", "Dodano do kolejki: {n}", "已加入队列的曲目：{n}"),
    "The queue is empty": ("Die Warteschlange ist leer", "キューは空です", "La file est vide", "La cola está vacía", "La coda è vuota", "대기열이 비어 있습니다", "Очередь пуста", "Kolejka jest pusta", "队列为空"),
    "Saved playlist “{name}”": ("Playlist „{name}“ gespeichert", "プレイリスト「{name}」を保存しました", "Playlist « {name} » enregistrée", "Lista «{name}» guardada", "Playlist «{name}» salvata", "재생목록 ‘{name}’을(를) 저장했습니다", "Плейлист «{name}» сохранён", "Zapisano playlistę „{name}”", "已保存播放列表“{name}”"),
    "Nothing playing — right-click an album to queue it": ("Keine Wiedergabe – Rechtsklick auf ein Album, um es einzureihen", "再生中のものはありません — アルバムを右クリックしてキューに追加できます", "Aucune lecture — clic droit sur un album pour l'ajouter à la file", "Nada en reproducción: haga clic derecho en un álbum para añadirlo a la cola", "Nessuna riproduzione — clic destro su un album per accodarlo", "재생 중인 항목이 없습니다 — 앨범을 오른쪽 클릭하여 대기열에 추가하세요", "Ничего не играет — щёлкните альбом правой кнопкой, чтобы добавить в очередь", "Nic nie jest odtwarzane — kliknij album prawym przyciskiem, aby dodać do kolejki", "未在播放——右键点击专辑即可加入队列"),
    "Volume {v}%": ("Lautstärke {v} %", "音量 {v}%", "Volume {v} %", "Volumen {v} %", "Volume {v}%", "음량 {v}%", "Громкость {v}%", "Głośność {v}%", "音量 {v}%"),
    "Controller connected: {name}": ("Controller verbunden: {name}", "コントローラーを接続しました: {name}", "Manette connectée : {name}", "Mando conectado: {name}", "Controller collegato: {name}", "컨트롤러 연결됨: {name}", "Контроллер подключён: {name}", "Podłączono kontroler: {name}", "手柄已连接：{name}"),
    "Save playlist": ("Playlist speichern", "プレイリストを保存", "Enregistrer la playlist", "Guardar lista", "Salva playlist", "재생목록 저장", "Сохранить плейлист", "Zapisz playlistę", "保存播放列表"),
    "Playlist name:": ("Name der Playlist:", "プレイリスト名:", "Nom de la playlist :", "Nombre de la lista:", "Nome della playlist:", "재생목록 이름:", "Название плейлиста:", "Nazwa playlisty:", "播放列表名称："),
}

TR = {code: {} for code in ORDER}
for _key, _vals in T.items():
    assert len(_vals) == len(ORDER), (_key, len(_vals))
    for _code, _val in zip(ORDER, _vals):
        TR[_code][_key] = _val

_cur = "en"


def set_lang(code):
    global _cur
    _cur = code if (code == "en" or code in TR) else "en"


def lang():
    return _cur


def tr(key, **kw):
    s = TR.get(_cur, {}).get(key, key)
    if kw:
        s = s.format(**kw)
    if _cur in ELLIPSIS_FIX:
        s = s.replace("…", "...")
    return s
