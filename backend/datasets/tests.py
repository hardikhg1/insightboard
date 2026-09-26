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

from .models import DataRow, Dataset, DatasetColumn


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


# ══════════════════════════════════════════════════════════════════════════════
# 6.  Model unit tests
#     These test the ORM layer directly — no HTTP requests involved.
#     They verify that our model definitions (fields, Meta, __str__) work
#     exactly as intended.
# ══════════════════════════════════════════════════════════════════════════════
class DatasetModelTest(TestCase):

    def test_create_dataset(self):
        """We can create a Dataset row and retrieve it from the DB."""
        ds = Dataset.objects.create(
            name="Test",
            original_filename="test.csv",
            row_count=10,
            column_count=3,
        )
        # Retrieve fresh from DB to confirm it was actually saved
        fetched = Dataset.objects.get(pk=ds.pk)
        self.assertEqual(fetched.name, "Test")
        self.assertEqual(fetched.row_count, 10)
        self.assertEqual(fetched.column_count, 3)

    def test_dataset_str(self):
        """__str__ should return the dataset name."""
        ds = Dataset.objects.create(
            name="Sales 2024",
            original_filename="sales.csv",
        )
        self.assertEqual(str(ds), "Sales 2024")

    def test_dataset_default_counts_are_zero(self):
        """row_count and column_count default to 0 when not provided."""
        ds = Dataset.objects.create(name="Empty", original_filename="empty.csv")
        self.assertEqual(ds.row_count, 0)
        self.assertEqual(ds.column_count, 0)

    def test_datasets_ordered_by_uploaded_at_desc(self):
        """
        Dataset.Meta has ordering = ['-uploaded_at'].
        The most recently created dataset should appear first in a queryset.
        """
        ds1 = Dataset.objects.create(name="First", original_filename="a.csv")
        ds2 = Dataset.objects.create(name="Second", original_filename="b.csv")
        all_datasets = list(Dataset.objects.all())
        # ds2 was created after ds1, so it should be first (newest first)
        self.assertEqual(all_datasets[0].pk, ds2.pk)
        self.assertEqual(all_datasets[1].pk, ds1.pk)


class DatasetColumnModelTest(TestCase):

    def setUp(self):
        self.ds = Dataset.objects.create(name="Test", original_filename="t.csv")

    def test_create_column(self):
        """We can create a DatasetColumn linked to a Dataset."""
        col = DatasetColumn.objects.create(
            dataset=self.ds,
            name="revenue",
            position=0,
            data_type=DatasetColumn.NUMBER,
        )
        self.assertEqual(col.dataset, self.ds)
        self.assertEqual(col.data_type, "number")

    def test_column_default_type_is_text(self):
        """data_type defaults to 'text' when not specified."""
        col = DatasetColumn.objects.create(
            dataset=self.ds, name="city", position=0
        )
        self.assertEqual(col.data_type, DatasetColumn.TEXT)

    def test_column_str(self):
        """__str__ should return '<dataset name> - <column name>'."""
        col = DatasetColumn.objects.create(
            dataset=self.ds, name="price", position=1, data_type=DatasetColumn.NUMBER
        )
        self.assertEqual(str(col), "Test - price")

    def test_column_unique_together_constraint(self):
        """
        (dataset, name) must be unique — creating two columns with the same
        name on the same dataset must raise an IntegrityError.
        """
        from django.db import IntegrityError
        DatasetColumn.objects.create(dataset=self.ds, name="col_a", position=0)
        with self.assertRaises(IntegrityError):
            DatasetColumn.objects.create(dataset=self.ds, name="col_a", position=1)

    def test_column_type_choices(self):
        """All three TYPE_CHOICES constants must exist on the model."""
        self.assertEqual(DatasetColumn.TEXT,   "text")
        self.assertEqual(DatasetColumn.NUMBER, "number")
        self.assertEqual(DatasetColumn.DATE,   "date")


class DataRowModelTest(TestCase):

    def setUp(self):
        self.ds = Dataset.objects.create(name="Orders", original_filename="o.csv")

    def test_create_data_row(self):
        """We can create a DataRow with JSON data and retrieve it."""
        row = DataRow.objects.create(
            dataset=self.ds,
            row_index=0,
            data={"product": "Pen", "qty": 5}
        )
        fetched = DataRow.objects.get(pk=row.pk)
        self.assertEqual(fetched.data["product"], "Pen")
        self.assertEqual(fetched.data["qty"], 5)

    def test_data_row_str(self):
        """__str__ should return '<dataset name> - Row <row_index>'."""
        row = DataRow.objects.create(dataset=self.ds, row_index=3, data={})
        self.assertEqual(str(row), "Orders - Row 3")

    def test_data_row_null_values_stored_as_none(self):
        """JSON null maps to Python None when retrieved from the DB."""
        row = DataRow.objects.create(
            dataset=self.ds,
            row_index=0,
            data={"score": None, "name": "Alice"}
        )
        fetched = DataRow.objects.get(pk=row.pk)
        self.assertIsNone(fetched.data["score"])

    def test_cascade_delete_removes_rows(self):
        """
        Deleting a Dataset must also delete all its DataRows
        because of on_delete=models.CASCADE on the ForeignKey.
        """
        DataRow.objects.create(dataset=self.ds, row_index=0, data={"x": 1})
        DataRow.objects.create(dataset=self.ds, row_index=1, data={"x": 2})
        self.assertEqual(DataRow.objects.count(), 2)

        self.ds.delete()

        self.assertEqual(DataRow.objects.count(), 0)


# ══════════════════════════════════════════════════════════════════════════════
# 7.  Serializer unit tests
#     These test the serializer layer in isolation — no HTTP, no DB calls.
#     They verify that our serializers produce the right JSON shape and
#     enforce the right read/write rules.
# ══════════════════════════════════════════════════════════════════════════════
class DatasetSerializerTest(TestCase):

    def _make_dataset(self):
        return Dataset.objects.create(
            name="Revenue",
            original_filename="revenue.csv",
            row_count=100,
            column_count=4,
        )

    def test_serializer_contains_expected_fields(self):
        """DatasetSerializer output must have exactly the fields we defined."""
        from .serializers import DatasetSerializer
        ds = self._make_dataset()
        data = DatasetSerializer(ds).data
        expected_fields = {"id", "name", "original_filename", "uploaded_at",
                           "row_count", "column_count"}
        self.assertEqual(set(data.keys()), expected_fields)

    def test_serializer_name_matches_model(self):
        """The serialized name must equal the model's name field."""
        from .serializers import DatasetSerializer
        ds = self._make_dataset()
        data = DatasetSerializer(ds).data
        self.assertEqual(data["name"], "Revenue")

    def test_serializer_row_count_is_integer(self):
        """row_count must be serialized as an integer, not a string."""
        from .serializers import DatasetSerializer
        ds = self._make_dataset()
        data = DatasetSerializer(ds).data
        self.assertIsInstance(data["row_count"], int)


class DatasetDetailSerializerTest(TestCase):

    def setUp(self):
        self.ds = Dataset.objects.create(
            name="Products", original_filename="products.csv",
            row_count=2, column_count=2,
        )
        DatasetColumn.objects.create(
            dataset=self.ds, name="item", position=0, data_type=DatasetColumn.TEXT
        )
        DatasetColumn.objects.create(
            dataset=self.ds, name="price", position=1, data_type=DatasetColumn.NUMBER
        )
        DataRow.objects.create(dataset=self.ds, row_index=0, data={"item": "Pen",  "price": 10})
        DataRow.objects.create(dataset=self.ds, row_index=1, data={"item": "Book", "price": 50})

    def test_detail_serializer_nests_columns(self):
        """DatasetDetailSerializer must include a nested 'columns' list."""
        from .serializers import DatasetDetailSerializer
        data = DatasetDetailSerializer(self.ds).data
        self.assertIn("columns", data)
        self.assertEqual(len(data["columns"]), 2)

    def test_detail_serializer_nests_rows(self):
        """DatasetDetailSerializer must include a nested 'rows' list."""
        from .serializers import DatasetDetailSerializer
        data = DatasetDetailSerializer(self.ds).data
        self.assertIn("rows", data)
        self.assertEqual(len(data["rows"]), 2)

    def test_nested_column_has_data_type(self):
        """Each nested column entry must include a 'data_type' field."""
        from .serializers import DatasetDetailSerializer
        data = DatasetDetailSerializer(self.ds).data
        price_col = next(c for c in data["columns"] if c["name"] == "price")
        self.assertEqual(price_col["data_type"], "number")

    def test_nested_row_has_data_dict(self):
        """Each nested row entry must include a 'data' dict."""
        from .serializers import DatasetDetailSerializer
        data = DatasetDetailSerializer(self.ds).data
        first_row = data["rows"][0]
        self.assertIn("data", first_row)
        self.assertIsInstance(first_row["data"], dict)

    def test_columns_are_read_only(self):
        """
        DatasetDetailSerializer.columns is read_only=True.
        POSTing with a 'columns' key must not create new column records.
        """
        from .serializers import DatasetDetailSerializer
        payload = {
            "name": "Hacked",
            "original_filename": "hacked.csv",
            "columns": [{"name": "injected", "position": 0, "data_type": "text"}]
        }
        serializer = DatasetDetailSerializer(data=payload)
        serializer.is_valid()
        # read_only fields are simply ignored — columns count stays the same
        self.assertEqual(DatasetColumn.objects.count(), 2)


class DataRowSerializerTest(TestCase):

    def setUp(self):
        self.ds = Dataset.objects.create(name="D", original_filename="d.csv")

    def test_row_serializer_fields(self):
        """DataRowSerializer must output id, row_index, and data."""
        from .serializers import DataRowSerializer
        row = DataRow.objects.create(
            dataset=self.ds, row_index=7, data={"col": "val"}
        )
        data = DataRowSerializer(row).data
        self.assertIn("id", data)
        self.assertIn("row_index", data)
        self.assertIn("data", data)
        self.assertEqual(data["row_index"], 7)
        self.assertEqual(data["data"]["col"], "val")
