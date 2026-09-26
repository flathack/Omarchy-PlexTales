import importlib.machinery
import importlib.util
import pathlib
import stat
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
LOADER = importlib.machinery.SourceFileLoader("plextales_audiobooks", str(ROOT / "bin" / "plextales"))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
player = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(player)


class AudiobookProgressTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        base = pathlib.Path(self.folder.name)
        self.patches = [
            mock.patch.object(player, "PROGRESS_FILE", base / "config" / "progress.json"),
            mock.patch.object(player, "STATE_FILE", base / "cache" / "state.json"),
            mock.patch.object(player, "DATA_CACHE_DIR", base / "cache" / "data"),
        ]
        for patch in self.patches:
            patch.start()
            self.addCleanup(patch.stop)
        self.config = {"server": "https://plex.example", "section": "7", "clientIdentifier": "client",
                       "token": "first-token", "connectionEnabled": False}
        self.track = {"key": "chapter-2", "albumKey": "book-1", "title": "Chapter two",
                      "album": "A Long Story", "artist": "Jane Author", "duration": 7200}

    def test_bookmark_survives_token_change_and_cache_cleanup(self):
        player.checkpoint_progress(self.config, self.track, 3661.5, 7200, True)
        self.assertEqual(stat.S_IMODE(player.PROGRESS_FILE.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(player.PROGRESS_FILE.parent.stat().st_mode), 0o700)
        new_token = {**self.config, "token": "refreshed-token"}
        self.assertEqual(player.book_progress(new_token, "book-1")["position"], 3661.5)
        self.assertEqual(player.continue_books(new_token, 10)[0]["progressChapter"], "Chapter two")
        player.cleanup_cache(max_age_days=1)
        self.assertEqual(player.book_progress(new_token, "book-1")["position"], 3661.5)
        self.assertEqual(player.book_progress({**new_token, "section": "8"}, "book-1"), {})

    def test_multiple_books_have_independent_positions(self):
        player.checkpoint_progress(self.config, self.track, 240, 7200, True)
        other = {**self.track, "key": "chapter-9", "albumKey": "book-2", "album": "Another Story"}
        player.checkpoint_progress(self.config, other, 100, 7200, True)
        self.assertEqual(player.book_progress(self.config, "book-1")["trackKey"], "chapter-2")
        self.assertEqual(player.book_progress(self.config, "book-2")["position"], 100)
        self.assertEqual(len(player.continue_books(self.config, 10)), 2)

    def test_reset_removes_only_selected_book_and_next_continue_starts_at_first_chapter(self):
        player.checkpoint_progress(self.config, self.track, 240, 7200, True, 10000, 3840)
        other = {**self.track, "key": "other-chapter", "albumKey": "book-2"}
        player.checkpoint_progress(self.config, other, 100, 7200, True)
        with mock.patch.object(player, "mpv_properties", return_value=None), \
             mock.patch.object(player, "status", return_value={"playing": False}):
            result = player.reset_book_progress(self.config, "book-1")
        self.assertEqual(player.book_progress(self.config, "book-1"), {})
        self.assertEqual(player.book_progress(self.config, "book-2")["position"], 100)
        self.assertEqual([book["key"] for book in player.continue_books(self.config, 10)], ["book-2"])
        self.assertEqual((result["book"]["progressTotal"], result["book"]["progressElapsed"],
                          result["book"]["progressPercent"]), (10000, 0, 0))
        queue = [{"key": "chapter-1", "albumKey": "book-1"}, self.track]
        with mock.patch.object(player, "mpv_running", return_value=False), \
             mock.patch.object(player, "prepare_collection", return_value=(queue, ["a", "b"])), \
             mock.patch.object(player, "activate_queue", return_value={"playing": True}) as activate:
            player.play_collection(self.config, "album", "book-1")
        self.assertEqual(activate.call_args.kwargs["start_index"], 0)
        self.assertEqual(activate.call_args.kwargs["start_position"], 0)

    def test_reset_stops_only_the_selected_book_before_removing_its_bookmark(self):
        player.checkpoint_progress(self.config, self.track, 240, 7200, True, 10000, 3840)
        snapshot = {"playlist": [], "playlist-pos": 0, "idle-active": False}
        state = {"queue": [self.track]}
        with mock.patch.object(player, "mpv_properties", return_value=snapshot), \
             mock.patch.object(player, "sync_queue_from_mpv", return_value=state), \
             mock.patch.object(player, "shutdown_player") as shutdown, \
             mock.patch.object(player, "status", return_value={"playing": False}):
            player.reset_book_progress(self.config, "book-1")
        shutdown.assert_called_once_with(self.config)
        self.assertEqual(player.book_progress(self.config, "book-1"), {})

        player.checkpoint_progress(self.config, self.track, 240, 7200, True, 10000, 3840)
        other = {**self.track, "albumKey": "book-2"}
        with mock.patch.object(player, "mpv_properties", return_value=snapshot), \
             mock.patch.object(player, "sync_queue_from_mpv", return_value={"queue": [other]}), \
             mock.patch.object(player, "shutdown_player") as shutdown, \
             mock.patch.object(player, "status", return_value={"playing": True}):
            player.reset_book_progress(self.config, "book-1")
        shutdown.assert_not_called()

    def test_collection_play_uses_saved_chapter_and_position(self):
        player.checkpoint_progress(self.config, self.track, 3661.5, 7200, True)
        with mock.patch.object(player, "prepare_collection", return_value=([self.track], ["url"])) as prepare, \
             mock.patch.object(player, "activate_queue", return_value={"playing": True}) as activate:
            player.play_collection(self.config, "album", "book-1")
        self.assertEqual(prepare.call_args.args[3], "chapter-2")
        self.assertEqual(activate.call_args.kwargs["start_position"], 3661.5)

    def test_status_checkpoints_current_chapter(self):
        queue = [self.track]
        snapshot = {"playlist": [], "playlist-pos": 0, "pause": False, "idle-active": False,
                    "time-pos": 1234.5, "duration": 7200, "volume": 100}
        with mock.patch.object(player, "mpv_properties", return_value=snapshot), \
             mock.patch.object(player, "sync_queue_from_mpv", return_value={"queue": queue, "shuffle": False,
                                                                             "repeat": "off", "speed": 1.25}), \
             mock.patch.object(player, "update_timeline"):
            status = player.status(self.config)
        self.assertEqual(status["speed"], 1.25)
        self.assertEqual(player.book_progress(self.config, "book-1")["position"], 1234.5)

    def test_stopped_status_shows_bookmarked_chapter(self):
        player.checkpoint_progress(self.config, self.track, 3661.5, 7200, True)
        first = {**self.track, "key": "chapter-1", "title": "Chapter one"}
        state = {"queue": [first, self.track], "speed": 1.0, "queueNamespace": player.cache_namespace(self.config)}
        with mock.patch.object(player, "mpv_properties", return_value=None), \
             mock.patch.object(player, "sync_queue_from_mpv", return_value=state), \
             mock.patch.object(player, "update_timeline"):
            status = player.status(self.config)
        self.assertEqual(status["track"]["key"], "chapter-2")
        self.assertEqual(status["position"], 3661.5)

    def test_book_total_includes_chapters_before_selected_chapter(self):
        rows = [{"ratingKey": str(index), "type": "track", "duration": duration}
                for index, duration in enumerate((60000, 120000, 180000), 1)]
        queue = [{"key": str(index), "albumKey": "book-1", "duration": duration / 1000}
                 for index, duration in ((1, 60000), (2, 120000), (3, 180000))]
        with mock.patch.object(player, "album_track_rows", return_value=rows), \
             mock.patch.object(player, "prepare_rows", return_value=(queue, ["a", "b", "c"])):
            prepared, _ = player.prepare_collection(self.config, "album", "book-1", "2")
        self.assertEqual(prepared[0]["_bookDuration"], 360)
        self.assertEqual([item["_bookOffset"] for item in prepared], [0, 60, 180])
        self.assertEqual(player.book_total_duration(prepared, prepared[0]), 360)
        legacy = [{key: value for key, value in item.items() if key != "_bookDuration"} for item in queue]
        self.assertEqual(player.book_total_duration(legacy, legacy[0]), 360)
        self.assertEqual(player.book_total_duration([{**legacy[0], "albumKey": "other"}, legacy[1]], legacy[1]), 0)

    def test_resuming_middle_chapter_keeps_previous_chapters_in_order(self):
        player.checkpoint_progress(self.config, self.track, 30, 7200, True, 10000, 3630)
        queue = [{"key": "chapter-1", "albumKey": "book-1"}, self.track,
                 {"key": "chapter-3", "albumKey": "book-1"}]
        with mock.patch.object(player, "mpv_running", return_value=False), \
             mock.patch.object(player, "prepare_collection", return_value=(queue, ["a", "b", "c"])), \
             mock.patch.object(player, "activate_queue", return_value={"playing": True}) as activate:
            player.play_collection(self.config, "album", "book-1")
        self.assertEqual([item["key"] for item in activate.call_args.args[1]],
                         ["chapter-1", "chapter-2", "chapter-3"])
        self.assertEqual(activate.call_args.kwargs["start_index"], 1)
        self.assertEqual(activate.call_args.kwargs["start_position"], 30)

    def test_playing_chapter_from_search_loads_its_whole_book(self):
        with mock.patch.object(player, "mpv_running", return_value=False), \
             mock.patch.object(player, "raw_track", return_value=(self.track, "/part")), \
             mock.patch.object(player, "prepare_collection", return_value=([self.track], ["url"])) as prepare, \
             mock.patch.object(player, "activate_queue", return_value={"playing": True}):
            player.play(self.config, "chapter-2", None)
        self.assertEqual(prepare.call_args.args[1:4], ("album", "book-1", "chapter-2"))

    def test_book_progress_crosses_chapter_boundaries_and_rewinds(self):
        second = {**self.track, "_bookDuration": 10000, "_bookOffset": 3600}
        at_ten_minutes = player.book_progress_position([second], second, 600)
        self.assertEqual(at_ten_minutes["bookElapsed"], 4200)
        self.assertEqual(at_ten_minutes["bookRemaining"], 5800)
        self.assertEqual(at_ten_minutes["bookPercent"], 42)
        self.assertEqual(player.book_progress_position([second], second, 100)["bookPercent"], 37)

    def test_resume_and_book_list_expose_persisted_whole_book_progress(self):
        player.checkpoint_progress(self.config, self.track, 600, 7200, True, 10000, 4200)
        resumed = player.continue_books(self.config, 10)[0]
        self.assertEqual((resumed["progressElapsed"], resumed["progressRemaining"], resumed["progressPercent"]),
                         (4200, 5800, 42))
        book = {"type": "album", "key": "book-1", "title": "A Long Story"}
        self.config["connectionEnabled"] = True
        with mock.patch.object(player, "album_track_rows", return_value=[{"ratingKey": "one", "duration": 180000}]):
            decorated = player.decorate_book_items(self.config, [book, {"type": "album", "key": "unstarted"}])
        self.assertEqual(decorated[0]["progressPercent"], 42)
        self.assertEqual(decorated[1]["progressPercent"], 0)
        self.assertEqual(decorated[1]["progressRemaining"], 180)

    def test_older_chapter_bookmark_is_hydrated_once(self):
        player.checkpoint_progress(self.config, self.track, 30, 7200, True)
        self.config["connectionEnabled"] = True
        rows = [{"ratingKey": "chapter-1", "duration": 60000},
                {"ratingKey": "chapter-2", "duration": 120000}]
        with mock.patch.object(player, "album_track_rows", return_value=rows) as fetch:
            first = player.continue_books(self.config, 10)[0]
            second = player.continue_books(self.config, 10)[0]
        fetch.assert_called_once_with(self.config, "book-1")
        self.assertEqual(first["progressTotal"], 180)
        self.assertEqual(first["progressElapsed"], 90)
        self.assertEqual(first["progressRemaining"], 90)
        self.assertEqual(second["progressPercent"], 50)

    def test_book_outline_is_cached_after_first_fetch(self):
        self.config["connectionEnabled"] = True
        rows = [{"ratingKey": "chapter-1", "duration": 60000}]
        with mock.patch.object(player, "album_track_rows", return_value=rows) as fetch:
            first = player.cached_book_outline(self.config, "book-1")
            self.config["connectionEnabled"] = False
            second = player.cached_book_outline(self.config, "book-1")
        fetch.assert_called_once_with(self.config, "book-1")
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
