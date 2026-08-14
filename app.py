from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st
import io

st.set_page_config(
    page_title="Quản Lý & Báo Cáo Tiến Độ GPON 2026",
    page_icon="🔒",
    layout="wide",
)

# Cấu hình URL
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwCeCROZKl1_t4iRB9aDdgXJW-43X-N8KUVWvsZiMA5j8bNRwhu5Okx4yavGG1FvydM2Q/exec"
# URL bạn vừa cung cấp
SHEET_ID = "1wUSpmt-4SyB-yyXmOn5Yox6nCRq7NuLHRpklvisJIuw" 

USERS = {
    "admin": {"pass": "admin123", "role": "admin", "name": "Quản Trị Viên (Admin)"},
    "xuanlong": {"pass": "xl123", "role": "Xuân Long", "name": "Đối Tác Xuân Long"},
    "vcc": {"pass": "vcc123", "role": "VCC", "name": "Đối Tác VCC"},
}

# --- Xử lý đăng nhập ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("🔒 ĐĂNG NHẬP HỆ THỐNG")
    with st.form("login_form"):
        username = st.text_input("Username:").strip().lower()
        password = st.text_input("Password:", type="password")
        if st.form_submit_button("Đăng nhập"):
            if username in USERS and USERS[username]["pass"] == password:
                st.session_state["logged_in"] = True
                st.session_state["user_info"] = USERS[username]
                st.rerun()
            else:
                st.error("Sai tài khoản hoặc mật khẩu!")
    st.stop()

user = st.session_state["user_info"]
st.sidebar.write(f"👤 **{user['name']}**")
if st.sidebar.button("Đăng xuất"):
    st.session_state["logged_in"] = False
    st.rerun()

# --- Hàm load dữ liệu (đã sửa lỗi 404) ---
@st.cache_data(ttl=60)
def load_data():
    # Sử dụng format export chuẩn của Google Sheets
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    
    response = requests.get(csv_url)
    if response.status_code != 200:
        st.error(f"Lỗi tải dữ liệu (Mã {response.status_code}). Hãy đảm bảo file đã được 'Chia sẻ cho bất kỳ ai có đường liên kết'.")
        return pd.DataFrame()
        
    df = pd.read_csv(io.StringIO(response.text))
    df.columns = [str(c).strip() for c in df.columns]
    return df

st.title("📊 HỆ THỐNG QUẢN LÝ GPON 2026")
df_raw = load_data()

if not df_raw.empty:
    st.success("Đã tải dữ liệu thành công!")
    st.dataframe(df_raw.head())
else:
    st.warning("Không có dữ liệu hoặc lỗi kết nối.")
