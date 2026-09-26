import pandas as pd

from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Dataset, DatasetColumn, DataRow
from .serializers import DatasetSerializer, DatasetDetailSerializer, DataRowSerializer



class DatasetListCreateView(generics.ListCreateAPIView):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer


class DatasetDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Dataset.objects.all()
    serializer_class = DatasetDetailSerializer


def _infer_type(series):
    """
    Look at a single pandas Series (one CSV column) and return
    'date', 'number', or 'text' based on its dtype.

    Why a helper function?  Because we'll call this once per column
    and it keeps the upload view clean and readable.
    """
    # pandas already parsed this as a date during read_csv
    if pd.api.types.is_datetime64_any_dtype(series):
        return DatasetColumn.DATE

    # int64, float64, etc. — any numeric dtype
    if pd.api.types.is_numeric_dtype(series):
        return DatasetColumn.NUMBER

    # Everything else (object/string columns) → text
    return DatasetColumn.TEXT


class CSVUploadView(APIView):
    """
    POST /api/datasets/upload/

    Accepts a multipart form upload with a single field called 'file'.
    Parses the CSV with pandas, infers column data types, then creates:
      - one Dataset row
      - one DatasetColumn row per CSV column   (bulk_create)
      - one DataRow row per CSV data row       (bulk_create)

    Returns the new Dataset's metadata (id, name, row_count, …).
    """

    # These two parsers tell DRF to accept multipart/form-data
    # (the encoding used when you upload a file via an HTML form or Postman).
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        # ── 1. Validate that a file was actually sent ──────────────────────
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response(
                {'error': 'No file provided. Send a CSV as field name "file".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not uploaded_file.name.endswith('.csv'):
            return Response(
                {'error': 'Only .csv files are supported.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ── 2. Parse the CSV with pandas ───────────────────────────────────
        # parse_dates=True tells pandas to try to detect date columns.
        # keep_default_na=True means blank cells become NaN (which we
        # convert to None below so JSON can serialise them).
        try:
            df = pd.read_csv(uploaded_file, parse_dates=True, keep_default_na=True)
        except Exception as exc:
            return Response(
                {'error': f'Could not parse CSV: {exc}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if df.empty or len(df.columns) == 0:
            return Response(
                {'error': 'The CSV file is empty or has no columns.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ── 3. Create the parent Dataset record ────────────────────────────
        dataset = Dataset.objects.create(
            name=uploaded_file.name.rsplit('.', 1)[0],   # filename without extension
            original_filename=uploaded_file.name,
            row_count=len(df),
            column_count=len(df.columns),
        )

        # ── 4. Bulk-create DatasetColumn rows ──────────────────────────────
        # bulk_create() inserts all rows in a single SQL INSERT → much faster
        # than calling .create() inside a loop.
        columns_to_create = [
            DatasetColumn(
                dataset=dataset,
                name=col_name,
                position=pos,
                data_type=_infer_type(df[col_name]),
            )
            for pos, col_name in enumerate(df.columns)
        ]
        DatasetColumn.objects.bulk_create(columns_to_create)

        # ── 5. Bulk-create DataRow rows ────────────────────────────────────
        # df.itertuples() is faster than df.iterrows() for large CSVs.
        # We convert each row to a plain dict so it's JSON-serialisable.
        # NaN → None because JSON has no NaN; None becomes null in JSON.
        rows_to_create = []
        for row_index, row in enumerate(df.itertuples(index=False)):
            row_dict = {}
            for col_name in df.columns:
                value = getattr(row, col_name)
                # pandas uses float('nan') for missing numeric values;
                # JSON can't represent NaN, so we turn it into None (→ null).
                if pd.isna(value):
                    value = None
                # Convert numpy int/float to plain Python types so that
                # Django's JSONField (backed by json.dumps) can serialise them.
                elif hasattr(value, 'item'):
                    value = value.item()
                row_dict[col_name] = value
            rows_to_create.append(
                DataRow(dataset=dataset, row_index=row_index, data=row_dict)
            )

        DataRow.objects.bulk_create(rows_to_create)

        # ── 6. Return the new Dataset's metadata ───────────────────────────
        serializer = DatasetSerializer(dataset)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RowFilterView(APIView):
    """
    GET /api/datasets/<pk>/rows/
    GET /api/datasets/<pk>/rows/?column=product&value=Pen

    Returns DataRow records for the given dataset.
    If query params `column` and `value` are both provided, only rows
    whose JSON data contains that column:value pair are returned.

    Why filter in Python (not SQL)?
    --------------------------------
    DataRow.data is a JSONField — a blob of JSON stored in one column.
    Filtering on keys *inside* JSON would require database-specific JSON
    operators (e.g. PostgreSQL's @> operator). Filtering in Python is
    simpler to understand and good enough for small-to-medium CSVs.
    For very large datasets a proper JSON query or a dedicated column
    index would be the next step.
    """

    def get(self, request, pk, *args, **kwargs):
        # get_object_or_404: fetches the Dataset or returns HTTP 404 automatically.
        dataset = get_object_or_404(Dataset, pk=pk)

        # Start with ALL rows for this dataset, ordered by row_index.
        rows = dataset.rows.order_by('row_index')

        # Read optional query parameters from the URL
        # e.g. ?column=product&value=Pen
        column = request.query_params.get('column')
        value  = request.query_params.get('value')

        if column and value:
            # Filter in Python: keep only rows where data[column] == value.
            # str(v) comparison makes it work whether value was stored as
            # int/float or string (e.g. "100" matches 100).
            rows = [
                row for row in rows
                if str(row.data.get(column, "")).lower() == value.lower()
            ]

        serializer = DataRowSerializer(rows, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
