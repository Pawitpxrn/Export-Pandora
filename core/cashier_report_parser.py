import io
import re
from typing import List, Dict, Any, Union
import pdfplumber
import pandas as pd

# Column x-ranges based on standard MMS / MGC Cashier Report layout
COL_RANGES = [
    ('แคชเชียร์', 0, 50),
    ('เวลา', 50, 80),
    ('เลขที่ invoice', 80, 150),
    ('อ้างถึง', 150, 220),
    ('เงินสด', 220, 280),
    ('เครดิตการ์ด', 280, 350),
    ('โอน', 350, 400),
    ('คูปอง', 400, 460),
    ('อื่นๆ', 460, 510),
    ('ขายเชื่อ', 510, 570),
    ('รวมเงิน', 570, 635),
    ('ส่วนลดเงินสด', 635, 750),
]

PAYMENT_TYPES = ['ขายเชื่อ', 'โอน', 'เงินสด', 'เครดิตการ์ด', 'คูปอง', 'อื่นๆ']

class CashierReportParser:
    """
    Dedicated parser for 'รายงานตามแคชเชียร์' (Cashier Transaction Reports)
    Extracts invoice rows and can transform into Daily Payment Summary format:
    [เลขที่ invoice, ประเภทรับชำระ, จำนวนเงิน]
    """

    def __init__(self, pdf_source: Union[str, io.BytesIO, bytes]):
        self.pdf_source = pdf_source
        self.raw_rows: List[Dict[str, Any]] = []
        self.header_info: Dict[str, str] = {}

    def parse(self) -> "CashierReportParser":
        if isinstance(self.pdf_source, bytes):
            stream = io.BytesIO(self.pdf_source)
        elif isinstance(self.pdf_source, io.BytesIO):
            stream = self.pdf_source
        else:
            stream = open(self.pdf_source, "rb")

        with pdfplumber.open(stream) as pdf:
            current_cashier = ""
            for page_idx, page in enumerate(pdf.pages):
                words = page.extract_words()
                if not words:
                    continue

                # Sort words by top (y), then x0
                words.sort(key=lambda w: (round(w['top'], 1), w['x0']))

                # Group words into horizontal lines
                lines = []
                curr_line = []
                curr_top = None
                for w in words:
                    if curr_top is None or abs(w['top'] - curr_top) <= 3.5:
                        curr_line.append(w)
                        curr_top = w['top']
                    else:
                        lines.append(curr_line)
                        curr_line = [w]
                        curr_top = w['top']
                if curr_line:
                    lines.append(curr_line)

                # Extract lines
                for line in lines:
                    top = line[0]['top']
                    line_text = ' '.join(w['text'] for w in line)

                    # Extract header info if present
                    if "001" in line_text and "สาขา" not in self.header_info:
                        self.header_info["สาขา"] = "001"
                    date_match = re.search(r'Date\s*:\s*(\d{2}/\d{2}/\d{4})', line_text)
                    if date_match:
                        self.header_info["วันที่พิมพ์"] = date_match.group(1)

                    # Skip header area (top < 115) and summary/total lines
                    if top < 115:
                        continue
                    if 'ยอดรวม' in line_text or '(cid:22)(cid:13)(cid:27)' in line_text or 'รวมทั้งสิ้น' in line_text:
                        continue

                    # Map words to columns by x position
                    row_dict = {col[0]: '' for col in COL_RANGES}
                    for w in line:
                        x = (w['x0'] + w['x1']) / 2.0
                        for col_name, x_min, x_max in COL_RANGES:
                            if x_min <= x < x_max:
                                row_dict[col_name] = w['text']
                                break

                    # Track cashier name across rows
                    if row_dict['แคชเชียร์']:
                        # e.g. "LADAWAN.12:09:10" -> cashier name is LADAWAN
                        cashier_clean = row_dict['แคชเชียร์'].split('.')[0]
                        if cashier_clean:
                            current_cashier = cashier_clean
                    row_dict['แคชเชียร์'] = current_cashier

                    # Validate if row is an actual invoice row
                    inv = row_dict['เลขที่ invoice'].strip()
                    # An invoice typically has digits (e.g. CH00126090001, CR0012609027, etc.)
                    if inv and re.search(r'\d', inv):
                        self.raw_rows.append(row_dict)

        if not isinstance(self.pdf_source, (bytes, io.BytesIO)):
            stream.close()

        return self

    def get_full_dataframe(self) -> pd.DataFrame:
        """Returns the full tabular DataFrame with all columns."""
        if not self.raw_rows:
            return pd.DataFrame()
        return pd.DataFrame(self.raw_rows)

    def get_payment_summary_dataframe(self) -> pd.DataFrame:
        """
        Unpivots payment columns into the target format:
        [เลขที่ invoice, ประเภทรับชำระ, จำนวนเงิน]
        """
        summary_rows = []
        for r in self.raw_rows:
            inv = r['เลขที่ invoice']
            for ptype in PAYMENT_TYPES:
                val_str = r.get(ptype, '').replace(',', '').strip()
                if val_str:
                    try:
                        amt = float(val_str)
                        if amt > 0:
                            summary_rows.append({
                                'เลขที่ invoice': inv,
                                'ประเภทรับชำระ': ptype,
                                'จำนวนเงิน': float(amt)
                            })
                    except ValueError:
                        pass

        if not summary_rows:
            return pd.DataFrame(columns=['เลขที่ invoice', 'ประเภทรับชำระ', 'จำนวนเงิน'])
        return pd.DataFrame(summary_rows)

def is_cashier_report(pdf_source: Union[str, io.BytesIO, bytes]) -> bool:
    """Detects whether the PDF matches the Cashier Report format."""
    try:
        if isinstance(pdf_source, bytes):
            stream = io.BytesIO(pdf_source)
        elif isinstance(pdf_source, io.BytesIO):
            stream = pdf_source
        else:
            stream = open(pdf_source, "rb")

        with pdfplumber.open(stream) as pdf:
            if not pdf.pages:
                return False
            first_page_text = pdf.pages[0].extract_text() or ""
            # Check for signatures of cashier reports (e.g. CH, J, Page :, Date :, Cashier)
            markers = ["Page :", "Date :", "012", "CH", "J", "LADAWAN", "แคชเชียร์"]
            match_count = sum(1 for m in markers if m in first_page_text)
            return match_count >= 3
    except Exception:
        return False
    finally:
        if not isinstance(pdf_source, (bytes, io.BytesIO)):
            try:
                stream.close()
            except Exception:
                pass
