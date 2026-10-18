import unittest
from browser_editor import EditorError, make_config, make_step, hosts_from_text


class EditorTests(unittest.TestCase):
    def test_make_steps(self):
        self.assertEqual(make_step("goto", "https://example.com")["url"], "https://example.com")
        self.assertEqual(make_step("screenshot", "result.png")["path"], "result.png")
        self.assertEqual(make_step("download", "a", "out/file.csv")["save_as"], "out/file.csv")

    def test_restrict_hosts(self):
        for invalid in ("*", "https://example.com", "example.com:443"):
            with self.assertRaises(EditorError):
                hosts_from_text(invalid)
        with self.assertRaises(EditorError):
            make_config(".", "example.com",
                        [make_step("goto", "https://other.example/")])

    def test_missing_action_info(self):
        with self.assertRaises(EditorError):
            make_step("download", "a")
        with self.assertRaises(EditorError):
            make_step("goto", "http://example.com")
        with self.assertRaises(EditorError):
            make_config(".", "example.com", [])


if __name__ == "__main__":
    unittest.main()
