from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st
import io

# Cấu hình trang
st.set_page_config(page_title="Quản Lý & Báo Cáo Tiến Độ GPON 2026", layout="wide")

# CẤU HÌNH ĐƯỜNG DẪN ĐÚNG
SHEET_ID = "1wUSpmt-4SyB-yyXmOn5Yox6nCRq7NuLHRpklvisJIuw"
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwCeCROZKl1_t4iRB9aDdgXJW-43X-N8KUVWvsZiMA5j8bNRwhu5Okx4yavGG1FvydM2Q/exec"

USERS = {
    "admin": {"pass": "admin123", "role": "admin", "name": "Quản Trị Viên (Admin)"},
    "xuanlong": {"pass": "xl123", "role": "Xuân Long", "name": "Đối Tác Xuân Long"},
    "vcc": {"pass": "vcc123", "role": "VCC", "name": "Đối Tác VCC"},
}

# --- Logic Đăng nhập ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("🔒 ĐĂNG NHẬP HỆ THỐNG")
    with st.form("login"):
        user_input = st.text_input("Username").strip().lower()
        pass_input = st.text_input("Password", type="password")
        if st.form_submit_button("Đăng nhập"):
            if user_input in USERS and USERS[user_input]["pass"] == pass_input:
                st.session_state["logged_in"] = True
                st.session_state["user_info"] = USERS[user_input]
                st.rerun()
            else:
                st.error("Sai tài khoản!")
    st.stop()

# --- Load dữ liệu ---
@st.cache_data(ttl=60)
def load_data():
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    response = requests.get(csv_url)
    if response.status_code != 200:
        return pd.DataFrame()
    return pd.read_csv(io.StringIO(response.text))

df_raw = load_data()
user = st.session_state["user_info"]

# --- Giao diện chính ---
st.sidebar.write(f"👤 **{user['name']}**")
if st.sidebar.button("Đăng xuất"):
    st.session_state["logged_in"] = False
    st.rerun()

st.title("📊 HỆ THỐNG QUẢN LÝ GPON 2026")
if st.button("🔄 Làm mới dữ liệu"):
    st.cache_data.clear()
    st.rerun()

tab1, tab2, tab3 = st.tabs(["📈 Thống kê", "🏗️ Báo cáo thi công", "📅 Kế hoạch"])

with tab1:
    st.subheader("Danh sách chi tiết")
    st.dataframe(df_raw, use_container_width=True)

with tab2:
    st.subheader("Báo cáo thi công")
    with st.form("bao_cao"):
        tram = st.selectbox("Chọn trạm", df_raw.iloc[:, 1].unique() if df_raw.shape[1] > 1 else [])
        keo_cap = st.number_input("Mét cáp", 0)
        if st.form_submit_button("Gửi"):
            payload = {"action": "bao_cao", "Tram": tram, "Met": keo_cap, "Doi": user["name"]}
            requests.post(WEB_APP_URL, json=payload)
            st.success("Đã gửi báo cáo!")

with tab3:
    st.subheader("Kế hoạch thi công")
    st.write("Tính năng kế hoạch đang hoạt động...")

# Lưu ý: Các logic lọc dữ liệu (VCC, Xuân Long) nếu bạn muốn dùng lại 
# thì có thể copy từ bản cũ vào đây, tôi đã để cấu trúc sẵn để bạn dễ phát triển.
