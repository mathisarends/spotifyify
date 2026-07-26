import unittest
from types import SimpleNamespace

try:
    import typer  # noqa: F401
except ModuleNotFoundError:
    raise unittest.SkipTest("typer is an optional CLI dependency") from None

from spotifyify.cli.core import BATCH_ALBUMS, BATCH_FOLLOW, BATCH_TRACKS
from tests.cli_harness import CliTestCase


class LibraryTestCase(CliTestCase):
    def library(self, *, saved=None):
        """A library namespace that records every write and read it receives."""
        self.written = []
        self.checked = []

        def writer(name):
            async def write(ids):
                self.written.append((name, list(ids)))

            return write

        def checker(name):
            async def check(ids):
                self.checked.append((name, list(ids)))
                return [saved if saved is not None else True] * len(ids)

            return check

        return {
            "library": SimpleNamespace(
                save_tracks=writer("save_tracks"),
                remove_tracks=writer("remove_tracks"),
                check_tracks=checker("check_tracks"),
                save_albums=writer("save_albums"),
                remove_albums=writer("remove_albums"),
                check_albums=checker("check_albums"),
            )
        }


class TestSaveAndRemove(LibraryTestCase):
    def test_ids_beyond_spotifys_limit_are_split_across_requests(self):
        ids = [f"t{index}" for index in range(BATCH_TRACKS + 1)]

        self.run_json(["library", "save-tracks", ",".join(ids)], self.library())

        chunks = [chunk for name, chunk in self.written if name == "save_tracks"]
        self.assertEqual([len(chunk) for chunk in chunks], [BATCH_TRACKS, 1])
        self.assertEqual([item for chunk in chunks for item in chunk], ids)

    def test_albums_use_their_own_smaller_limit(self):
        ids = [f"a{index}" for index in range(BATCH_ALBUMS + 1)]

        self.run_json(["library", "save-albums", ",".join(ids)], self.library())

        chunks = [chunk for name, chunk in self.written if name == "save_albums"]
        self.assertEqual([len(chunk) for chunk in chunks], [BATCH_ALBUMS, 1])

    def test_a_single_id_makes_a_single_request(self):
        self.run_json(["library", "save-tracks", "t1"], self.library())

        self.assertEqual(self.written, [("save_tracks", ["t1"])])

    def test_the_write_is_read_back_so_the_result_is_the_real_state(self):
        rows = self.run_json(["library", "save-tracks", "t1,t2"], self.library())

        self.assertEqual(self.checked, [("check_tracks", ["t1", "t2"])])
        self.assertEqual(
            rows, [{"id": "t1", "saved": True}, {"id": "t2", "saved": True}]
        )

    def test_removing_reports_the_resulting_state_too(self):
        rows = self.run_json(
            ["library", "remove-tracks", "t1"], self.library(saved=False)
        )

        self.assertEqual(self.written, [("remove_tracks", ["t1"])])
        self.assertEqual(rows, [{"id": "t1", "saved": False}])

    def test_checking_alone_never_writes(self):
        rows = self.run_json(["library", "check-tracks", "t1 t2"], self.library())

        self.assertEqual(self.written, [])
        self.assertEqual([row["id"] for row in rows], ["t1", "t2"])

    def test_write_and_read_scopes_are_both_requested(self):
        from spotifyify import SpotifyScope

        self.run_json(["library", "save-tracks", "t1"], self.library())

        self.assertEqual(
            set(self.requested_scopes()),
            {SpotifyScope.USER_LIBRARY_MODIFY, SpotifyScope.USER_LIBRARY_READ},
        )

    def test_a_check_alone_asks_only_for_the_read_scope(self):
        from spotifyify import SpotifyScope

        self.run_json(["library", "check-tracks", "t1"], self.library())

        self.assertEqual(self.requested_scopes(), [SpotifyScope.USER_LIBRARY_READ])


class TestSavedStatePairing(LibraryTestCase):
    def test_ids_keep_their_own_flag(self):
        async def check_tracks(ids):
            return [True, False, True]

        namespaces = self.library()
        namespaces["library"].check_tracks = check_tracks

        rows = self.run_json(["library", "check-tracks", "a,b,c"], namespaces)

        self.assertEqual(
            rows,
            [
                {"id": "a", "saved": True},
                {"id": "b", "saved": False},
                {"id": "c", "saved": True},
            ],
        )

    def test_a_short_answer_never_pairs_an_id_with_the_wrong_flag(self):
        # Better to report fewer rows than to shift flags onto the wrong ids.
        async def check_tracks(ids):
            return [True]

        namespaces = self.library()
        namespaces["library"].check_tracks = check_tracks

        rows = self.run_json(["library", "check-tracks", "a,b,c"], namespaces)

        self.assertEqual(rows, [{"id": "a", "saved": True}])


class TestFollowing(CliTestCase):
    def users(self):
        self.written = []

        def writer(name):
            async def write(type, ids):
                self.written.append((name, type, list(ids)))

            return write

        async def check_following(type, ids):
            self.checked = (type, list(ids))
            return [True] * len(ids)

        return {
            "users": SimpleNamespace(
                follow=writer("follow"),
                unfollow=writer("unfollow"),
                check_following=check_following,
            )
        }

    def test_the_type_is_forwarded_with_every_chunk(self):
        ids = [f"a{index}" for index in range(BATCH_FOLLOW + 1)]

        self.run_json(["users", "follow", "artist", ",".join(ids)], self.users())

        self.assertEqual(
            [len(chunk) for _, _, chunk in self.written], [BATCH_FOLLOW, 1]
        )
        self.assertEqual({type for _, type, _ in self.written}, {"artist"})

    def test_following_is_read_back_after_the_write(self):
        rows = self.run_json(["users", "follow", "artist", "a1"], self.users())

        self.assertEqual(self.checked, ("artist", ["a1"]))
        self.assertEqual(rows, [{"id": "a1", "following": True}])

    def test_unfollow_uses_the_unfollow_endpoint(self):
        self.run_json(["users", "unfollow", "artist", "a1"], self.users())

        self.assertEqual(self.written, [("unfollow", "artist", ["a1"])])


class TestBulkFetch(CliTestCase):
    def test_a_bulk_read_is_split_and_rejoined_in_order(self):
        requested = []

        async def get_many(ids, **kwargs):
            requested.append(list(ids))
            return [{"id": item_id, "name": item_id} for item_id in ids]

        ids = [f"t{index}" for index in range(BATCH_TRACKS + 2)]

        rows = self.run_json(
            ["tracks", "get", ",".join(ids)],
            {"tracks": SimpleNamespace(get_many=get_many)},
        )

        self.assertEqual([len(chunk) for chunk in requested], [BATCH_TRACKS, 2])
        self.assertEqual([row["id"] for row in rows], ids)

    def test_the_market_reaches_every_chunk(self):
        markets = []

        async def get_many(ids, **kwargs):
            markets.append(kwargs.get("market"))
            return [{"id": item_id} for item_id in ids]

        ids = [f"t{index}" for index in range(BATCH_TRACKS + 1)]

        self.run_json(
            ["--market", "DE", "tracks", "get", ",".join(ids)],
            {"tracks": SimpleNamespace(get_many=get_many)},
        )

        self.assertEqual(markets, ["DE", "DE"])


if __name__ == "__main__":
    unittest.main()
