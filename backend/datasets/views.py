import os

from google import genai as google_genai
import pandas as pd
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DataRow, Dataset, DatasetColumn
from .serializers import DataRowSerializer, DatasetDetailSerializer, DatasetSerializer


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


class ChatView(APIView):
    """
    POST /api/datasets/<pk>/chat/

    Body: { "question": "What is the average revenue?" }

    How it works:
    1. Fetch the dataset metadata (column names, types, row count).
    2. Pull a sample of up to 30 rows.
    3. Compute quick statistics (mean, min, max for number columns;
       top values for text columns) — this gives Gemini real numbers
       to work with rather than making it guess.
    4. Build a detailed system prompt that describes the dataset.
    5. Send the user's question to Google Gemini (gemini-1.5-flash).
    6. Return the response text.

    The GEMINI_API_KEY must be set in the environment:
        Windows:  $env:GEMINI_API_KEY = "your-key-here"
        macOS/Linux: export GEMINI_API_KEY=your-key-here
    """

    def post(self, request, pk, *args, **kwargs):
        # ── 0. Check API key ──────────────────────────────────────────────
        api_key = (
            os.environ.get("GOOGLE_API_KEY")
            or os.environ.get("GEMINI_API_KEY", "")
        )
        if not api_key:
            return Response(
                {"error": "GOOGLE_API_KEY environment variable is not set. "
                          "Get a free key at https://aistudio.google.com/app/apikey"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # ── 1. Validate request body ──────────────────────────────────────
        question = (request.data.get("question") or "").strip()
        if not question:
            return Response(
                {"error": "Please provide a non-empty 'question' field."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 2. Fetch dataset + columns + rows ─────────────────────────────
        dataset = get_object_or_404(Dataset, pk=pk)
        columns = list(dataset.columns.order_by("position"))
        rows    = list(dataset.rows.order_by("row_index")[:500])  # cap at 500 for speed

        # ── 3. Build quick stats so Gemini has real numbers ───────────────
        stats_lines = []
        for col in columns:
            values = [r.data.get(col.name) for r in rows if r.data.get(col.name) is not None]
            if col.data_type == DatasetColumn.NUMBER and values:
                nums = [v for v in values if isinstance(v, (int, float))]
                if nums:
                    stats_lines.append(
                        f"  - {col.name} (number): "
                        f"min={min(nums):.4g}, max={max(nums):.4g}, "
                        f"mean={sum(nums)/len(nums):.4g}, "
                        f"non-null={len(nums)}/{len(rows)}"
                    )
            elif col.data_type == DatasetColumn.TEXT and values:
                from collections import Counter
                top = Counter(str(v) for v in values).most_common(5)
                top_str = ", ".join(f'"{v}"({c})' for v, c in top)
                stats_lines.append(
                    f"  - {col.name} (text): {len(set(str(v) for v in values))} unique values; "
                    f"top: {top_str}"
                )
            elif col.data_type == DatasetColumn.DATE and values:
                stats_lines.append(f"  - {col.name} (date): {len(values)} non-null values")

        # ── 4. Build sample rows (first 10) as a mini CSV ─────────────────
        col_names = [c.name for c in columns]
        sample_header = " | ".join(col_names)
        sample_rows = []
        for r in rows[:10]:
            sample_rows.append(" | ".join(str(r.data.get(c, "")) for c in col_names))
        sample_table = "\n".join([sample_header] + sample_rows)

        # ── 5. Build the system prompt ────────────────────────────────────
        system_prompt = f"""You are InsightBot, an expert data analyst assistant embedded inside InsightBoard — a CSV exploration tool.

The user has uploaded a dataset. Here is everything you know about it:

DATASET NAME: {dataset.name}
FILE: {dataset.original_filename}
TOTAL ROWS: {dataset.row_count}
TOTAL COLUMNS: {dataset.column_count}

COLUMNS & TYPES:
{chr(10).join(f'  - {c.name} ({c.data_type})' for c in columns)}

COLUMN STATISTICS (based on up to 500 rows):
{chr(10).join(stats_lines) if stats_lines else '  (no stats available)'}

SAMPLE DATA (first 10 rows):
{sample_table}

INSTRUCTIONS:
- Answer the user's question based on the dataset information above.
- Be concise but accurate. Use specific numbers from the statistics.
- If the user asks something you cannot determine from the data provided, say so clearly.
- Format numbers nicely (e.g. 1,234.56 instead of 1234.5600000001).
- Use markdown formatting (bold, bullet points) where it helps readability.
- Do NOT make up data that isn't in the statistics above.
"""

        # ── 6. Call Gemini API ────────────────────────────────────────────
        try:
            client = google_genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=system_prompt + "\n\nUSER QUESTION: " + question,
            )
            answer = response.text
        except Exception as exc:
            return Response(
                {"error": f"Gemini API error: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"answer": answer}, status=status.HTTP_200_OK)
