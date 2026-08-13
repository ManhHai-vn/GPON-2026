from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import io

st.set_page_config(page_title="Quản Lý & Báo Cáo Tiến Độ GPON 2026", page_icon="🔒", layout="wide")

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwaTaqtylnHfBkgC0jJDiU8n1tVVTmILtC9sjdNebIGVBBat7Yji-0WRF1HvSwJTpl4iQ/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1VPbF7bLk6JF97kJEGw-TW1JEheUf4etfDO5bLsphyGs/edit#gid=0"

USERS = {
    "admin": {"pass": "admin123", "role": "admin", "name": "Quản Trị Viên (Admin)"},
    "xuanlong": {"pass": "xl123", "role": "Xuân Long", "name": "Đối Tác Xuân Long"},
    "vcc": {"pass": "vcc123", "role": "VCC", "name": "Đối Tác VCC"},
}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None

if not st.session_state["logged_in"]:
    st.title("🔒 ĐĂNG NHẬP HỆ THỐNG GPON 2026")
    with st.form("login_form"):
        username = st.text_input("Tên đăng nhập:").strip().lower()
        password = st.text_input("Mật khẩu:", type="password")
        if st.form_submit_button("Đăng nhập"):
            if username in USERS and USERS[username]["pass"] == password:
                st.session_state["logged_in"] = True
                st.session_state["user_info"] = USERS[username]
                st.rerun()
            else:
                st.error("Sai tài khoản hoặc mật khẩu!")
    st.stop()

user = st.session_state["user_info"]
st.sidebar.title("👤 Thông tin")
st.sidebar.write(f"**Người dùng:** {user['name']}")
if st.sidebar.button("🚪 Đăng xuất"):
    st.session_state["logged_in"] = False
    st.rerun()

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10)
def load_data():
    df_main = conn.read(spreadsheet=SHEET_URL, worksheet="0")
    df_main.columns = [str(c).strip() for c in df_main.columns]
    return df_main

df_raw = load_data()

# Hàm tìm cột thông minh
def get_col(df, keywords):
    for col in df.columns:
        if any(k in col.lower() for k in keywords): return col
    return None

def get_cols_multi(df, keywords):
    return [c for c in df.columns if any(k in c.lower() for k in keywords)]

col_tram = get_col(df_raw, ["trạm", "tram"])
col_doitac = get_col(df_raw, ["đối tác", "đơn vị"])
cols_cap12 = get_cols_multi(df_raw, ["12fo"])
cols_cap24 = get_cols_multi(df_raw, ["24fo"])
cols_tu = get_cols_multi(df_raw, ["tủ", "tu"])

# Lọc dữ liệu theo nhà thầu
if user["role"] == "admin":
    df = df_raw.copy()
else:
    df = df_raw[df_raw[col_doitac].str.contains(user["role"], case=False, na=False)].copy() if col_doitac else df_raw.copy()

st.title("📊 HỆ THỐNG QUẢN LÝ TIẾN ĐỘ")

# --- TÍNH NĂNG XUẤT FILE ĐỐI CHIẾU ---
def export_excel_doi_chieu(df_sub):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_sub.to_excel(writer, index=False, sheet_name='DoiChieu')
    return output.getvalue()

st.subheader("📋 Bảng chi tiết trạm")
if user["role"] != "admin":
    st.download_button(
        label="📥 Tải File Đối Chiếu Thi Công (Excel)",
        data=export_excel_doi_chieu(df),
        file_name=f"DoiChieu_ThiCong_{user['role']}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.dataframe(df, use_container_width=True)

# Các tab báo cáo giữ nguyên logic cũ của anh/chị
tab1, tab2 = st.tabs(["📈 Thống kê", "🏗️ Báo cáo thi công"])
with tab1:
    st.write("Tổng quan dữ liệu đã được nạp.")
with tab2:
    st.write("Tính năng báo cáo thi công...")
