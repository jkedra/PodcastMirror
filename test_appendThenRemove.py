from unittest import TestCase


class TestAppendThenRemove(TestCase):
    def setUp(self):
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as src:
            src.write(b"AAA")
            self.srcname = src.name
        with tempfile.NamedTemporaryFile(delete=False) as dst:
            self.dstname = dst.name

    @staticmethod
    def remove(fname):
        import os
        try:
            os.remove(fname)
        except FileNotFoundError:
            pass

    def test_appendThenRemove_unlink(self):
        from Podcast import append_then_remove
        import os
        append_then_remove(self.srcname, self.dstname)
        if os.path.isfile(self.srcname):
            self.fail('File exists but should be removed.')

    def tearDown(self):
        self.remove(self.srcname)
        self.remove(self.dstname)
