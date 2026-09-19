import argparse
import sys
import os

# Ensure Windows terminal doesn't crash on emoji or Thai characters
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from core.extractor import PDFReportExtractor
from core.excel_builder import ExcelReportBuilder
from core.profile_manager import ProfileManager

def main():
    parser = argparse.ArgumentParser(description="Convert PDF reports to formatted Excel with selected columns")
    parser.add_argument("--input", "-i", required=True, help="Path to input PDF file")
    parser.add_argument("--output", "-o", default=None, help="Path to output Excel file (.xlsx)")
    parser.add_argument("--profile", "-p", default=None, help="Name of saved mapping profile to apply")
    parser.add_argument("--table-index", "-t", type=int, default=0, help="Index of table to extract (default: 0)")
    parser.add_argument("--mode", "-m", choices=["auto", "summary", "full", "generic"], default="auto",
                        help="Extraction mode: summary (unpivoted payments), full (detailed table), generic (standard PDF tables)")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' does not exist.")
        sys.exit(1)

    output_path = args.output
    if not output_path:
        base, _ = os.path.splitext(args.input)
        output_path = f"{base}.xlsx"

    print(f"🔍 Reading and analyzing '{args.input}'...")

    # Check if this is a cashier report
    from core.cashier_report_parser import CashierReportParser, is_cashier_report
    if (args.mode == "auto" and is_cashier_report(args.input)) or args.mode in ["summary", "full"]:
        c_parser = CashierReportParser(args.input).parse()
        if args.mode in ["auto", "summary"]:
            print("✨ Detected Cashier Report! Exporting Daily Payment Summary format...")
            df = c_parser.get_payment_summary_dataframe()
            builder = ExcelReportBuilder()
            builder.export_to_file(output_path, df, sheet_name="Sheet1")
            print(f"📊 Processed {len(df)} payment rows.")
            print(f"✅ Successfully converted to '{output_path}'!")
            return
        else:
            print("📋 Exporting full detailed table for Cashier Report...")
            df = c_parser.get_full_dataframe()
            builder = ExcelReportBuilder()
            builder.export_to_file(output_path, df, sheet_name="Sheet1")
            print(f"📊 Processed {len(df)} detailed invoice rows.")
            print(f"✅ Successfully converted to '{output_path}'!")
            return

    selected_columns = None
    column_mapping = None

    if args.profile:
        pm = ProfileManager()
        profile_data = pm.load_profile(args.profile)
        if profile_data:
            print(f"📌 Applied profile: '{args.profile}'")
            selected_columns = profile_data.get("selected_columns")
            column_mapping = profile_data.get("column_mapping")
        else:
            print(f"⚠️ Profile '{args.profile}' not found. Exporting all columns.")

    print(f"📊 Found {len(df)} rows and {len(df.columns)} columns.")
    builder = ExcelReportBuilder()
    builder.export_to_file(output_path, df, selected_columns=selected_columns, column_mapping=column_mapping)
    print(f"✅ Successfully converted to '{output_path}'!")

if __name__ == "__main__":
    main()
