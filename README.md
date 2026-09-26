# PlexTales

PlexTales is an unofficial Omarchy bar widget for audiobooks stored on a Plex Media Server. It is based on [Tunarchy](https://github.com/flathack/omarchy-tunarchy) and uses the same native Quickshell player layout. PlexTales is not affiliated with Plex, Inc.

## Audiobook model

Create a **Music** library in Plex for audiobooks. PlexTales treats an artist as an author, an album as a book, and its tracks as chapters. Name and order chapters in Plex as you want them played. A book can consist of one long file or many chapter files. Plex libraries of type Movie, Show, or Photo are not supported.

- **Resume** lists unfinished books with saved progress. Continuing a book rewinds 15 seconds for context, including across chapter boundaries. Finished books remain under **Books** and can be marked unfinished.
- Book progress is saved per book and chapter on status polls (about every 3 seconds while the panel is open and every 10 seconds during background playback), and immediately on pause, seek, chapter change, or shutdown.
- Progress is stored in `${XDG_CONFIG_HOME:-~/.config}/plextales/progress.json`, outside the disposable artwork and library cache. It survives app restarts, cache cleanup, and Plex token refreshes. Progress and favorites are separated by Plex account, server, and library. They are local to this computer and are not synchronized to other Plex clients.
- The player has 30-second back/forward controls, a chapter seek bar with hour display, and selectable 1×, 1.25×, 1.5×, 1.75×, and 2× speed. Speed is remembered locally.
- The player shows the current chapter length and, underneath it, the total length of the audiobook across its chapters.
- Every book in the library and at the top of its chapter list shows a progress bar, percent complete, time reached in the story, and time remaining. Unstarted books show 0%; started books also appear in **Resume**. The full and mini players show the current book progress. This is the current point in the book, so rewinding moves the marker back; it does not count repeated listening time.
- A sleep timer offers 15, 30, or 45 minutes, or the end of the current chapter. Its background watcher continues when the popup closes and stops playback after saving the position.
- A book can have local bookmarks with optional notes. Each bookmark opens its exact chapter and position. Books with many chapters initially show the current chapter and nearby chapters; **Show all chapters** expands the full list. The **Books** and **Authors** lists can load additional pages.
- Plex browser sign-in, cover art, search, queue, mini player, hardware media keys through `mpv-mpris`, system volume, and dark/light Omarchy themes are inherited from Tunarchy. **Favs** now stores whole books locally.

## Requirements and installation

- Omarchy 4.0 or newer with the plugin-based shell
- Python 3.10 or newer
- `mpv` (`omarchy pkg add mpv`)
- Optional: `mpv-mpris` for media keys
- Reachable Plex Media Server and account with access to a Music library containing audiobooks

```bash
omarchy plugin add https://github.com/flathack/Omarchy-PlexTales.git --enable
```

Click the bar item, choose **Connect with Plex**, enter the server URL, and approve the sign-in in your browser. If more than one Music library exists, choose the audiobook library. Right-click the bar item for manual token setup if browser sign-in is unavailable. Never pass a Plex token on the command line.

An HTTPS server URL is recommended. With HTTP, devices on the network path can observe the Plex token; use it only on a trusted private network or inside an encrypted tunnel.

## Controls

- Left-click the bar item to open the player; middle-click to play or pause.
- Scroll over the bar item to jump 30 seconds; use the buttons in the player for back/forward 30 seconds.
- Select **Resume** to continue a saved book. Opening a book and pressing **Continue book** starts from its bookmark.
- In a book's chapter list, select **Reset book progress** beside **Continue book** and confirm with a second click to forget that book's bookmark. If that book is playing, playback stops; the next **Continue book** starts at chapter 1. Other books keep their progress.
- Choose a chapter to play it directly. Selecting an earlier chapter moves the saved book position there.
- Click the speed button to cycle through the available speeds.
- Click the clock button to cycle the sleep timer. In a book, use the heart to add it to **Favs**, the check button to mark it finished, or the bookmark field to save a note at the current position.
- Open **Help and settings** to select a full or mini player and system or local player volume.
- The Plex power button disconnects playback while keeping the account and local book progress.

Useful CLI commands:

```bash
PLAYER="${XDG_CONFIG_HOME:-$HOME/.config}/omarchy/plugins/io.github.flathack.plextales/bin/plextales"
"$PLAYER" doctor
"$PLAYER" status
"$PLAYER" library continue
"$PLAYER" library albums
"$PLAYER" library albums --limit 100 --offset 100
"$PLAYER" sleep-timer 30
"$PLAYER" sleep-timer chapter
"$PLAYER" bookmark list BOOK_KEY
"$PLAYER" control seek 1800
"$PLAYER" control speed 1.25
"$PLAYER" shutdown
```

The private data paths are `${XDG_CONFIG_HOME:-~/.config}/plextales/` for the account and progress, and `${XDG_CACHE_HOME:-~/.cache}/plextales/` for player state, artwork, and cached library views. `logout` removes the saved account token; it does not delete progress.

## Development

```bash
python3 -m unittest discover -s tests -v
node --test tests/test_model.js
omarchy plugin validate .
```

Demo mode presents fictional audiobooks without Plex or mpv:

```bash
omarchy bar set io.github.flathack.plextales demoMode true --json
```

A live Plex account and mpv are needed to validate streaming and library metadata against a real server. See [SECURITY.md](SECURITY.md) for credential handling.
