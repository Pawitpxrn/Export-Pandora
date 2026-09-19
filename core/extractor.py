import io
import re
from typing import List, Dict, Any, Union, Optional
import pdfplumber
import pandas as pd
from core.normalizer import clean_cell_text, parse_data_value

class PDFReportExtractor:
    """
    Extracts tables, headers, and key-value fields from PDF reports.
    Supports both file paths and byte streams (for Streamlit uploads).
    """

    def __init__(self, pdf_source: Union[str, io.BytesIO, bytes]):
        self.pdf_source = pdf_source
        self.pages_count = 0
        self.tables: List[pd.DataFrame] = []
        self.key_values: Dict[str, str] = {}
        self.raw_text_by_page: List[str] = []

    def load_and_extract(self) -> "PDFReportExtractor":
        """Executes full analysis on the PDF."""
        # Handle bytes vs path vs BytesIO
        if isinstance(self.pdf_source, bytes):
            stream = io.BytesIO(self.pdf_source)
        elif isinstance(self.pdf_source, io.BytesIO):
            stream = self.pdf_source
        else:
            stream = open(self.pdf_source, "rb")

        with pdfplumber.open(stream) as pdf:
            self.pages_count = len(pdf.pages)
            all_page_tables = []
            
            for page_idx, page in enumerate(pdf.pages):
                # 1. Extract text for key-value analysis
                page_text = page.extract_text() or ""
                self.raw_text_by_page.append(page_text)
                self._extract_key_values_from_text(page_text)

                # 2. Extract tables (try lattice first, then text stream)
                tables = page.extract_tables()
                if not tables or all(len(t) <= 1 for t in tables):
                    # Fallback to stream / text-based alignment
                    tables = page.extract_tables({
                        "vertical_strategy": "text",
                        "horizontal_strategy": "text",
                        "snap_tolerance": 3,
                        "join_tolerance": 3,
                    })

                for raw_table in tables:
                    cleaned_rows = self._clean_raw_table(raw_table)
                    if cleaned_rows and len(cleaned_rows) >= 2: # At least header + 1 data row
                        all_page_tables.append(cleaned_rows)

            # 3. Combine multi-page tables if headers match
            self.tables = self._assemble_dataframes(all_page_tables)

        if not isinstance(self.pdf_source, (bytes, io.BytesIO)):
            stream.close()

        return self

    def _clean_raw_table(self, raw_table: List[List[Any]]) -> List[List[str]]:
        """Cleans empty rows and whitespace in table cells."""
        cleaned = []
        for row in raw_table:
            if not row:
                continue
            cleaned_row = [clean_cell_text(cell) for cell in row]
            # Skip completely empty rows
            if any(cell != "" for cell in cleaned_row):
                cleaned.append(cleaned_row)
        return cleaned

    def _assemble_dataframes(self, raw_tables: List[List[List[str]]]) -> List[pd.DataFrame]:
        """Converts raw table rows into clean DataFrames, merging multi-page tables."""
        if not raw_tables:
            return []

        dataframes: List[pd.DataFrame] = []
        current_df: Optional[pd.DataFrame] = None
        current_header: Optional[List[str]] = None

        for table in raw_tables:
            if not table or len(table) < 2:
                continue

            header = [h if h else f"Column_{i+1}" for i, h in enumerate(table[0])]
            # Ensure unique header names
            header = self._make_unique_headers(header)
            data_rows = table[1:]

            # Check if this table is a continuation of the previous table (same header count & names)
            if current_df is not None and current_header == header:
                continuation_df = pd.DataFrame(data_rows, columns=header)
                current_df = pd.concat([current_df, continuation_df], ignore_index=True)
            else:
                if current_df is not None:
                    dataframes.append(current_df)
                current_header = header
                current_df = pd.DataFrame(data_rows, columns=header)

        if current_df is not None:
            dataframes.append(current_df)

        # Post-process: strip trailing summary rows or repeated headers inside table
        cleaned_dfs = []
        for df in dataframes:
            # Drop rows where every cell is identical to header
            mask = ~df.apply(lambda row: list(row) == list(df.columns), axis=1)
            cleaned_dfs.append(df[mask].reset_index(drop=True))

        return cleaned_dfs

    def _make_unique_headers(self, headers: List[str]) -> List[str]:
        """Ensure column headers are unique and non-empty."""
        seen: Dict[str, int] = {}
        unique = []
        for i, h in enumerate(headers):
            h_clean = h.strip().replace("\n", " ")
            if not h_clean:
                h_clean = f"Column_{i+1}"
            if h_clean in seen:
                seen[h_clean] += 1
                unique.append(f"{h_clean}_{seen[h_clean]}")
            else:
                seen[h_clean] = 0
                unique.append(h_clean)
        return unique

    def _extract_key_values_from_text(self, text: str):
        """Finds key-value pairs like 'Invoice No.: 12345' or 'วันที่: 19/09/2569'."""
        patterns = [
            r"([ก-๙a-zA-Z0-9\s_\-\.]{2,35})\s*[:：]\s*([^\n\r]+)",
        ]
        for line in text.splitlines():
            line_str = line.strip()
            for pat in patterns:
                m = re.match(pat, line_str)
                if m:
                    key = m.group(1).strip()
                    val = m.group(2).strip()
                    # Filter out noise
                    if len(key) >= 2 and len(val) >= 1 and key not in self.key_values:
                        self.key_values[key] = val

    def get_summary(self) -> Dict[str, Any]:
        """Returns structured summary of extraction results."""
        return {
            "pages": self.pages_count,
            "num_tables": len(self.tables),
            "table_shapes": [df.shape for df in self.tables],
            "table_headers": [list(df.columns) for df in self.tables],
            "key_values": self.key_values,
        }
