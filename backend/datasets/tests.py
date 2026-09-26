"""
InsightBoard — API Test Suite
==============================
Run with:
    python manage.py test datasets

What is a TestCase?
-------------------
Django's TestCase creates a fresh, empty test database before each test
method and destroys it after. That means every test is isolated — data
created in one test never leaks into another.

What is APIClient?
------------------
DRF's APIClient is like a fake browser/Postman built into Python.
It can make GET, POST, DELETE etc. requests directly to your Django views
without needing a real running server. This makes tests fast and reliable.
"""

import io

from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from .models import Dataset, DatasetColumn, DataRow


# ── Helper: build an in-memory CSV file ───────────────────────────────────────
def make_csv(content: str, filename: str = "test.csv"):
    """
    Returns an in-memory file object that looks exactly like a real
    uploaded CSV — no temp files on disk needed.

    io.BytesIO is just RAM pretending to be a file. Django's file-upload
    machinery is happy with it as long as it has a .name attribute.
    """
    buf = io.BytesIO(content.encode("utf-8"))
    buf.name = filename
    return buf


# ── Helper: build a Dataset with columns + rows already in the DB ─────────────
def make_dataset(name="Sales", rows=None):
    """
    Creates a Dataset, two DatasetColumns, and optional DataRows directly
    through the ORM (no HTTP). Used in tests that need pre-existing data
    without going through the upload endpoint.
    """
    ds = Dataset.objects.create(
        name=name,
        original_filename=f"{name}.csv",
        row_count=len(rows) if rows else 0,
        column_count=2,
    )
    DatasetColumn.objects.create(dataset=ds, name="product", position=0, data_type=DatasetColumn.TEXT)
    DatasetColumn.objects.create(dataset=ds, name="revenue", position=1, data_type=DatasetColumn.NUMBER)

    for i, row in enumerate(rows or []):
        DataRow.objects.create(dataset=ds, row_index=i, data=row)

    return ds


# ══════════════════════════════════════════════════════════════════════════════
# 1.  GET /api/datasets/  — list all datasets
# ══════════════════════════════════════════════════════════════════════════════
class DatasetListTest(TestCase):

    def setUp(self):
        # setUp() runs before EVERY test method in this class.
        # APIClient() is our fake HTTP client.
        self.client = APIClient()
        self.url = reverse("dataset-list-create")  # looks up the URL by its name

    def test_empty_list_returns_200(self):
        """When no datasets exist, the list endpoint returns 200 with an empty array."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_returns_existing_datasets(self):
        """After creating two datasets, the list endpoint returns both."""
        make_dataset("Alpha")
        make_dataset("Beta")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_contains_expected_fields(self):
        """Each item in the list must have the right fields."""
        make_dataset("Gamma")
        response = self.client.get(self.url)
        item = response.data[0]
        for field in ["id", "name", "original_filename", "uploaded_at", "row_count", "column_count"]:
            self.assertIn(field, item)


# ══════════════════════════════════════════════════════════════════════════════
# 2.  POST /api/datasets/upload/  — CSV upload
# ══════════════════════════════════════════════════════════════════════════════
class CSVUploadTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("dataset-upload")

    # ── Happy path ────────────────────────────────────────────────────────────

    def test_valid_csv_returns_201(self):
        """Uploading a well-formed CSV must return 201 Created."""
        csv_data = "name,age,joined\nAlice,30,2020-01-01\nBob,25,2021-06-15\n"
        response = self.client.post(
            self.url,
            data={"file": make_csv(csv_data)},
            format="multipart",  # tells APIClient to send multipart/form-data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_upload_creates_dataset_record(self):
        """After upload, exactly one Dataset row must exist in the DB."""
        csv_data = "product,price\nApple,1.5\nBanana,0.75\n"
        self.client.post(self.url, data={"file": make_csv(csv_data)}, format="multipart")
        self.assertEqual(Dataset.objects.count(), 1)

    def test_upload_sets_correct_row_and_column_counts(self):
        """row_count and column_count on the new Dataset must match the CSV."""
        csv_data = "a,b,c\n1,2,3\n4,5,6\n7,8,9\n"
        self.client.post(self.url, data={"file": make_csv(csv_data)}, format="multipart")
        ds = Dataset.objects.first()
        self.assertEqual(ds.row_count, 3)     # 3 data rows (header not counted)
        self.assertEqual(ds.column_count, 3)  # columns: a, b, c

    def test_upload_creates_columns_with_correct_types(self):
        """DatasetColumn rows must be created with correct inferred data types."""
        csv_data = "city,population\nMumbai,20000000\nDelhi,32000000\n"
        self.client.post(self.url, data={"file": make_csv(csv_data)}, format="multipart")
        ds = Dataset.objects.first()

        # Two columns should have been created
        self.assertEqual(ds.columns.count(), 2)

        city_col = ds.columns.get(name="city")
        pop_col = ds.columns.get(name="population")
        self.assertEqual(city_col.data_type, DatasetColumn.TEXT)
        self.assertEqual(pop_col.data_type, DatasetColumn.NUMBER)

    def test_upload_creates_data_rows(self):
        """One DataRow must be created for each CSV data row."""
        csv_data = "x,y\n10,20\n30,40\n50,60\n"
        self.client.post(self.url, data={"file": make_csv(csv_data)}, format="multipart")
        ds = Dataset.objects.first()
        self.assertEqual(ds.rows.count(), 3)

    def test_uploaded_row_data_is_correct(self):
        """The JSON stored in DataRow.data must exactly match the CSV values."""
        csv_data = "item,qty\nPen,5\nBook,2\n"
        self.client.post(self.url, data={"file": make_csv(csv_data)}, format="multipart")
        ds = Dataset.objects.first()

        first_row = ds.rows.get(row_index=0)
        self.assertEqual(first_row.data["item"], "Pen")
        self.assertEqual(first_row.data["qty"], 5)

    def test_response_body_contains_dataset_fields(self):
        """The 201 response body must include the Dataset's id, name, etc."""
        csv_data = "col1\nvalue1\n"
        response = self.client.post(
            self.url, data={"file": make_csv(csv_data, "mydata.csv")}, format="multipart"
        )
        self.assertIn("id", response.data)
        self.assertEqual(response.data["original_filename"], "mydata.csv")

    # ── Edge cases ────────────────────────────────────────────────────────────

    def test_missing_file_returns_400(self):
        """Sending no file must return 400 Bad Request."""
        response = self.client.post(self.url, data={}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_non_csv_file_returns_400(self):
        """Uploading a .txt file must be rejected with 400."""
        buf = io.BytesIO(b"hello world")
        buf.name = "notes.txt"
        response = self.client.post(self.url, data={"file": buf}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_empty_csv_returns_400(self):
        """An empty CSV (no rows, no columns) must return 400."""
        response = self.client.post(
            self.url, data={"file": make_csv("")}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_csv_with_missing_values_uploads_ok(self):
        """A CSV with blank/NaN cells must upload without error (stored as null)."""
        csv_data = "name,score\nAlice,\nBob,90\n"
        response = self.client.post(
            self.url, data={"file": make_csv(csv_data)}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        ds = Dataset.objects.first()
        alice_row = ds.rows.get(row_index=0)
        # Blank cell → stored as None (JSON null), not the string "nan"
        self.assertIsNone(alice_row.data["score"])


# ══════════════════════════════════════════════════════════════════════════════
# 3.  GET /api/datasets/<pk>/  — dataset detail (with nested columns + rows)
# ══════════════════════════════════════════════════════════════════════════════
class DatasetDetailTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.ds = make_dataset(
            "Orders",
            rows=[
                {"product": "Pen",  "revenue": 100},
                {"product": "Book", "revenue": 250},
            ]
        )
        self.url = reverse("dataset-detail", kwargs={"pk": self.ds.pk})

    def test_detail_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_contains_nested_columns(self):
        """The detail response must include a 'columns' list."""
        response = self.client.get(self.url)
        self.assertIn("columns", response.data)
        self.assertEqual(len(response.data["columns"]), 2)

    def test_detail_contains_nested_rows(self):
        """The detail response must include a 'rows' list."""
        response = self.client.get(self.url)
        self.assertIn("rows", response.data)
        self.assertEqual(len(response.data["rows"]), 2)

    def test_nonexistent_dataset_returns_404(self):
        """Requesting a pk that doesn't exist must return 404."""
        url = reverse("dataset-detail", kwargs={"pk": 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ══════════════════════════════════════════════════════════════════════════════
# 4.  DELETE /api/datasets/<pk>/  — delete a dataset
# ══════════════════════════════════════════════════════════════════════════════
class DatasetDeleteTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.ds = make_dataset("ToDelete", rows=[{"product": "X", "revenue": 10}])
        self.url = reverse("dataset-detail", kwargs={"pk": self.ds.pk})

    def test_delete_returns_204(self):
        """DELETE must return 204 No Content on success."""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_removes_dataset_from_db(self):
        """After DELETE, the Dataset must no longer exist in the DB."""
        self.client.delete(self.url)
        self.assertFalse(Dataset.objects.filter(pk=self.ds.pk).exists())

    def test_delete_cascades_to_columns_and_rows(self):
        """
        Deleting a Dataset must also delete its DatasetColumn and DataRow
        records (CASCADE behaviour defined in the model ForeignKey).
        """
        self.client.delete(self.url)
        self.assertEqual(DatasetColumn.objects.filter(dataset=self.ds).count(), 0)
        self.assertEqual(DataRow.objects.filter(dataset=self.ds).count(), 0)


# ══════════════════════════════════════════════════════════════════════════════
# 5.  GET /api/datasets/<pk>/rows/?column=X&value=Y  — row filter endpoint
# ══════════════════════════════════════════════════════════════════════════════
class RowFilterTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.ds = make_dataset(
            "Products",
            rows=[
                {"product": "Pen",    "revenue": 100},
                {"product": "Book",   "revenue": 250},
                {"product": "Pen",    "revenue": 300},
                {"product": "Eraser", "revenue": 50},
            ]
        )
        self.url = reverse("dataset-row-filter", kwargs={"pk": self.ds.pk})

    def test_filter_returns_matching_rows(self):
        """?column=product&value=Pen must return only the 2 Pen rows."""
        response = self.client.get(self.url, {"column": "product", "value": "Pen"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_no_match_returns_empty_list(self):
        """A filter that matches nothing must return an empty array (not 404)."""
        response = self.client.get(self.url, {"column": "product", "value": "Pencil"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_no_filter_params_returns_all_rows(self):
        """Without query params, all rows must be returned."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_nonexistent_dataset_returns_404(self):
        """Row filter on a missing dataset pk must return 404."""
        url = reverse("dataset-row-filter", kwargs={"pk": 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
