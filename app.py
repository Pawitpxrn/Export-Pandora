import io
import os
import streamlit as st
import pandas as pd
from core.cashier_report_parser import CashierReportParser, is_cashier_report
from core.extractor import PDFReportExtractor
from core.excel_builder import ExcelReportBuilder
from core.profile_manager import ProfileManager

st.set_page_config(
    page_title="PDF to Excel Custom Converter",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished interface
st.markdown("""
<style>
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 4px;
    }
    .sub-header {
        font-size: 15px;
        color: #64748B;
        margin-bottom: 20px;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    .metric-card {
        background-color: #F8FAFC;
        padding: 14px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        text-align: center;
    }
    .badge-success {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

pm = ProfileManager()

# --- Sidebar: Profile Management ---
with st.sidebar:
    st.header("⚙️ การตั้งค่า & โพรไฟล์")
    st.caption("บันทึกและเรียกใช้การจับคู่หัวข้อที่ตั้งไว้ล่วงหน้า")

    saved_profiles = pm.list_profiles()
    selected_profile_name = st.selectbox(
        "📂 เลือก Profile ที่บันทึกไว้",
        options=["-- ไม่ใช้ Profile (กำหนดเอง) --"] + saved_profiles,
        index=0
    )

    loaded_profile_data = None
    if selected_profile_name and selected_profile_name != "-- ไม่ใช้ Profile (กำหนดเอง) --":
        loaded_profile_data = pm.load_profile(selected_profile_name)
        st.success(f"โหลดโพรไฟล์: **{selected_profile_name}** สำเร็จ")
        if st.button("🗑️ ลบ Profile นี้", type="secondary"):
            pm.delete_profile(selected_profile_name)
            st.rerun()

    st.markdown("---")
    st.subheader("💡 คำแนะนำการใช้งาน")
    st.markdown("""
    1. **อัปโหลดไฟล์ PDF** รายงาน (เช่น *รายงานตามแคชเชียร์*)
    2. ระบบตรวจจับรูปแบบรายงานให้อัตโนมัติ
    3. เลือกโหมด:
       - **สรุปรับชำระประจำวัน** (ตามตัวอย่าง Excel: `เลขที่ invoice`, `ประเภทรับชำระ`, `จำนวนเงิน`)
       - **ตารางละเอียด** (ทุกคอลัมน์จากต้นทาง)
       - **กำหนดเอง**
    4. กดปุ่ม **ดาวน์โหลด Excel** (.xlsx)
    """)

# --- Main App Header ---
st.markdown('<div class="main-header">📑 ระบบแปลงรายงาน PDF เป็น Excel ตามหัวข้อที่ต้องการ</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Custom PDF Report to Excel Converter — แปลงรายงานตามแคชเชียร์ และรายงานทั่วไปเป็น Excel</div>', unsafe_allow_html=True)

# Step 1: Upload Files
uploaded_files = st.file_uploader(
    "📤 เลือกไฟล์รายงาน PDF (รองรับไฟล์เดียวหรือหลายไฟล์พร้อมกัน)",
    type=["pdf"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("👋 กรุณาอัปโหลดไฟล์ PDF รายงานเพื่อเริ่มต้นการแปลง หรือเลือกดูตัวอย่างที่มีในระบบ")
    
    # Check if files exist in Doc or samples
    sample_files = []
    doc_dir = os.path.join(os.path.dirname(__file__), "Doc")
    if os.path.exists(doc_dir):
        sample_files.extend([os.path.join(doc_dir, f) for f in os.listdir(doc_dir) if f.endswith(".pdf")])
    samples_dir = os.path.join(os.path.dirname(__file__), "samples")
    if os.path.exists(samples_dir):
        sample_files.extend([os.path.join(samples_dir, f) for f in os.listdir(samples_dir) if f.endswith(".pdf")])

    if sample_files:
        st.markdown("### 🧪 ไฟล์ตัวอย่างสำหรับทดสอบระบบ")
        cols = st.columns(min(len(sample_files), 3))
        for i, sf in enumerate(sample_files):
            sf_name = os.path.basename(sf)
            with cols[i % 3]:
                with open(sf, "rb") as f:
                    file_bytes = f.read()
                st.download_button(
                    f"⬇️ {sf_name}",
                    data=file_bytes,
                    file_name=sf_name,
                    mime="application/pdf",
                    key=f"sample_{i}"
                )
    st.stop()

# Step 2: Analyze Uploaded PDFs
with st.spinner("⏳ กำลังอ่านและประมวลผลไฟล์ PDF..."):
    first_file_bytes = uploaded_files[0].getvalue()
    is_cashier = is_cashier_report(first_file_bytes)

# Show detection status
if is_cashier:
    st.markdown('<span class="badge-success">✨ ตรวจพบรูปแบบ: รายงานตามแคชเชียร์ (Cashier Report)</span>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Choice of export mode
    export_mode = st.radio(
        "📊 เลือกรูปแบบผลลัพธ์ Excel ที่ต้องการ:",
        options=[
            "1. รายงานสรุปรับชำระประจำวัน (ตามตัวอย่าง Excel: เลขที่ invoice, ประเภทรับชำระ, จำนวนเงิน)",
            "2. รายงานละเอียดแบบเต็ม (ทุกคอลัมน์จากต้นทาง PDF)",
            "3. กำหนดคอลัมน์และจับคู่หัวข้อเอง (Custom Mapping)"
        ],
        index=0
    )

    if "1. รายงานสรุปรับชำระประจำวัน" in export_mode:
        # Extract payment summaries from all uploaded files
        all_summaries = []
        for up_file in uploaded_files:
            c_parser = CashierReportParser(up_file.getvalue()).parse()
            df_s = c_parser.get_payment_summary_dataframe()
            if len(uploaded_files) > 1:
                df_s.insert(0, "ไฟล์ต้นทาง", up_file.name)
            all_summaries.append(df_s)

        df_final = pd.concat(all_summaries, ignore_index=True) if all_summaries else pd.DataFrame()

        # Metrics
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"<div class='metric-card'><b>📄 จำนวนไฟล์</b><h3>{len(uploaded_files)}</h3></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-card'><b>🧾 รายการรับชำระ</b><h3>{len(df_final)} รายการ</h3></div>", unsafe_allow_html=True)
        with c3:
            total_amt = df_final["จำนวนเงิน"].sum() if "จำนวนเงิน" in df_final.columns and not df_final.empty else 0
            st.markdown(f"<div class='metric-card'><b>💰 ยอดเงินรวม</b><h3>฿{total_amt:,.2f}</h3></div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 👁️ ตัวอย่างข้อมูลที่จะส่งออก (Preview)")
        preview_styled = df_final.style.format({"จำนวนเงิน": "{:,.2f}"}) if "จำนวนเงิน" in df_final.columns else df_final
        st.dataframe(preview_styled, use_container_width=True)

        st.markdown("---")
        excel_builder = ExcelReportBuilder()
        excel_bytes = excel_builder.export_to_bytes(df_final, sheet_name="Sheet1")
        out_name = f"{os.path.splitext(uploaded_files[0].name)[0]}_สรุปรับชำระ.xlsx"
        st.download_button(
            label=f"🟢 ดาวน์โหลด Excel ({out_name})",
            data=excel_bytes,
            file_name=out_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
        st.stop()

    elif "2. รายงานละเอียดแบบเต็ม" in export_mode:
        all_full = []
        for up_file in uploaded_files:
            c_parser = CashierReportParser(up_file.getvalue()).parse()
            df_f = c_parser.get_full_dataframe()
            if len(uploaded_files) > 1:
                df_f.insert(0, "ไฟล์ต้นทาง", up_file.name)
            all_full.append(df_f)

        df_final = pd.concat(all_full, ignore_index=True) if all_full else pd.DataFrame()

        st.markdown("---")
        st.markdown("### 👁️ ตัวอย่างข้อมูลละเอียดแบบเต็ม (Full Detail Preview)")
        st.dataframe(df_final, use_container_width=True)

        excel_builder = ExcelReportBuilder()
        excel_bytes = excel_builder.export_to_bytes(df_final, sheet_name="Sheet1")
        out_name = f"{os.path.splitext(uploaded_files[0].name)[0]}_ตารางเต็ม.xlsx"
        st.download_button(
            label=f"🟢 ดาวน์โหลด Excel ตารางเต็ม ({out_name})",
            data=excel_bytes,
            file_name=out_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
        st.stop()

# Fallback or Option 3: Generic / Custom Mapping Mode
extractors = []
for up_file in uploaded_files:
    ext = PDFReportExtractor(up_file.getvalue()).load_and_extract()
    extractors.append((up_file.name, ext))

first_filename, first_ext = extractors[0]

# Metrics
total_pages = sum(e.pages_count for _, e in extractors)
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"<div class='metric-card'><b>📄 จำนวนไฟล์</b><h3>{len(extractors)}</h3></div>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div class='metric-card'><b>📑 จำนวนหน้ารวม</b><h3>{total_pages}</h3></div>", unsafe_allow_html=True)
with c3:
    st.markdown(f"<div class='metric-card'><b>📊 ตารางที่พบ</b><h3>{len(first_ext.tables)}</h3></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if not first_ext.tables and not first_ext.key_values:
    st.warning("⚠️ ไม่พบตารางหรือข้อมูลที่เป็นระเบียบในไฟล์ PDF นี้")
    st.stop()

current_table_idx = 0
if len(first_ext.tables) > 1:
    table_options = [f"ตารางที่ {i+1} (ขนาด {df.shape[0]} แถว x {df.shape[1]} คอลัมน์)" for i, df in enumerate(first_ext.tables)]
    selected_table_str = st.selectbox("📋 เลือกตารางที่ต้องการแปลง:", table_options)
    current_table_idx = table_options.index(selected_table_str)

combined_rows = []
for fname, ext in extractors:
    if current_table_idx < len(ext.tables):
        file_df = ext.tables[current_table_idx].copy()
        if len(extractors) > 1:
            file_df.insert(0, "Source_File", fname)
        combined_rows.append(file_df)

if combined_rows:
    df_raw = pd.concat(combined_rows, ignore_index=True)
else:
    df_raw = pd.DataFrame([first_ext.key_values])

all_source_cols = list(df_raw.columns)
default_selection = loaded_profile_data.get("selected_columns", all_source_cols) if loaded_profile_data else all_source_cols
profile_mapping = loaded_profile_data.get("column_mapping", {}) if loaded_profile_data else {}

col_ctrl1, col_ctrl2 = st.columns([3, 1])
with col_ctrl1:
    selected_columns = st.multiselect(
        "📌 เลือกคอลัมน์จากต้นทางที่ต้องการ:",
        options=all_source_cols,
        default=[c for c in default_selection if c in all_source_cols]
    )
with col_ctrl2:
    st.write("")
    st.write("")
    if st.button("เลือกทั้งหมด"):
        selected_columns = all_source_cols

if not selected_columns:
    st.warning("กรุณาเลือกอย่างน้อย 1 คอลัมน์")
    st.stop()

st.markdown("##### ✏️ กำหนดชื่อหัวข้อใน Excel ปลายทาง:")
mapping_cols = st.columns(min(len(selected_columns), 4))
custom_mapping = {}

for idx, col in enumerate(selected_columns):
    target_container = mapping_cols[idx % 4]
    default_val = profile_mapping.get(col, col)
    with target_container:
        new_name = st.text_input(f"ต้นทาง: {col}", value=default_val, key=f"map_{col}")
        custom_mapping[col] = new_name.strip() if new_name.strip() else col

with st.expander("💾 บันทึกการตั้งค่าเป็น Profile?"):
    save_col1, save_col2 = st.columns([3, 1])
    with save_col1:
        new_profile_name = st.text_input("ตั้งชื่อ Profile:", "")
    with save_col2:
        st.write("")
        st.write("")
        if st.button("บันทึก Profile", type="primary"):
            if new_profile_name.strip():
                pm.save_profile(new_profile_name.strip(), selected_columns, custom_mapping)
                st.success(f"บันทึก Profile '{new_profile_name}' เรียบร้อยแล้ว!")
                st.rerun()

st.markdown("---")
st.markdown("### 👁️ ตรวจสอบข้อมูลก่อนส่งออก (Preview)")
preview_df = df_raw[selected_columns].copy()
preview_df.columns = [custom_mapping.get(c, c) for c in selected_columns]
st.dataframe(preview_df.head(50), use_container_width=True)

st.markdown("---")
excel_builder = ExcelReportBuilder()
excel_bytes = excel_builder.export_to_bytes(
    df_raw,
    selected_columns=selected_columns,
    column_mapping=custom_mapping,
    sheet_name="Sheet1"
)

output_filename = f"{os.path.splitext(first_filename)[0]}.xlsx"
st.download_button(
    label=f"🟢 ดาวน์โหลด Excel ({output_filename})",
    data=excel_bytes,
    file_name=output_filename,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    type="primary"
)
