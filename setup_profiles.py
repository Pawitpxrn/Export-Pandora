import os
import json
from core.profile_manager import ProfileManager

def setup_sample_profiles():
    pm = ProfileManager()
    
    # 1. Profile: Full Report with Thai Headers
    pm.save_profile(
        profile_name="sales_full_thai",
        selected_columns=["No.", "Item Code", "Product Name", "Category", "Qty", "Unit Price", "Discount", "Total Amount"],
        column_mapping={
            "No.": "ลำดับ",
            "Item Code": "รหัสสินค้า",
            "Product Name": "รายการสินค้า",
            "Category": "หมวดหมู่",
            "Qty": "จำนวน",
            "Unit Price": "ราคาต่อหน่วย",
            "Discount": "ส่วนลด",
            "Total Amount": "ยอดเงินสุทธิ"
        }
    )

    # 2. Profile: Summary Only
    pm.save_profile(
        profile_name="sales_summary_only",
        selected_columns=["No.", "Product Name", "Qty", "Total Amount"],
        column_mapping={
            "No.": "ลำดับ",
            "Product Name": "ชื่อสินค้า",
            "Qty": "จำนวนที่ขายได้",
            "Total Amount": "ยอดขายรวม (บาท)"
        }
    )

    print("Sample profiles generated successfully in UTF-8!")

if __name__ == "__main__":
    setup_sample_profiles()
