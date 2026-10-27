from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from .models import Brand, Industry, Review, Reviewer

MODELS = (Industry, Brand, Reviewer, Review)


def counts():
    return {m.__name__: m.objects.count() for m in MODELS}


class ImportWpIdempotencyTests(TestCase):
    """Runs import_wp against the compose WP MariaDB (read-only) into the test database."""

    def run_import(self):
        out = StringIO()
        call_command("import_wp", stdout=out, stderr=StringIO())
        return out.getvalue()

    def test_second_run_creates_nothing_and_row_counts_are_equal(self):
        first = self.run_import()
        after_first = counts()
        self.assertGreater(after_first["Brand"], 0)
        self.assertGreater(after_first["Review"], 0)
        self.assertGreater(after_first["Industry"], 0)
        self.assertGreater(after_first["Reviewer"], 0)
        self.assertIn("created=", first)

        second = self.run_import()
        self.assertEqual(counts(), after_first)
        for line in second.splitlines():
            if "created=" in line:
                self.assertIn("created=0 updated=0", line)
        # counts are reported for every model
        for name in ("Industry", "Brand", "Reviewer", "Review"):
            self.assertIn(name, second)

    def test_rerun_restores_a_drifted_row_without_duplicating(self):
        self.run_import()
        before = counts()
        brand = Brand.objects.first()
        original = brand.name
        Brand.objects.filter(pk=brand.pk).update(name="drifted")
        out = self.run_import()
        self.assertEqual(counts(), before)
        self.assertEqual(Brand.objects.get(pk=brand.pk).name, original)
        self.assertIn("updated=1", out)
