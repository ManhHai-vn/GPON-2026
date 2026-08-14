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

# ĐÃ CẬP NHẬT ĐÚNG ĐƯỜNG DẪN TỪ ẢNH CỦA BẠN
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwCeCROZKl1_t4iRB9aDdgXJW-43X-N8KUVWvsZiMA5j8bNRwhu5Okx4yavGG1FvydM2Q/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1wUSpmt-4SyB-yyXmOn5Yox6nCRq7NuLHRpkIvisJluw/edit#gid=0"

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
        username = st.text_input("Tên đăng nhập (Username):").strip().lower()
        password = st.text_input("Mật khẩu (Password):", type="password")
        submit = st.form_submit_button("Đăng nhập")
        if submit:
            if username in USERS and USERS[username]["pass"] == password:
                st.session_state["logged_in"] = True
                st.session_state["user_info"] = USERS[username]
                st.rerun()
            else:
                st.error("Tài khoản hoặc mật khẩu không chính xác!")
    st.stop()

user = st.session_state["user_info"]
st.sidebar.title("👤 Thông tin tài khoản")
st.sidebar.write(f"**Người dùng:** {user['name']}")
st.sidebar.write(f"**Quyền hạn:** `{user['role']}`")
if st.sidebar.button("🚪 Đăng xuất"):
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None
    st.rerun()

st.title("📊 HỆ THỐNG QUẢN LÝ & BÁO CÁO TIẾN ĐỘ GPON 2026")

@st.cache_data(ttl=10)
def load_data():
    sheet_id = SHEET_URL.split("/d/")[1].split("/")[0]
    # Xuất bản sang CSV để tránh lỗi phân quyền phức tạp
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(csv_url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Không thể tải dữ liệu (Mã lỗi: {response.status_code}). Hãy kiểm tra xem file đã được chia sẻ công khai chưa.")
        
    df_main = pd.read_csv(io.StringIO(response.text))
    df_main.columns = [str(c).strip() for c in df_main.columns]
    return df_main

try:
    df_raw = load_data()
    # Hiển thị thông báo nếu file rỗng
    if df_raw.empty:
        st.warning("File Google Sheets hiện tại đang trống dữ liệu.")
except Exception as e:
    st.error(f"Lỗi kết nối: {e}")
    st.stop()

# --- Phần xử lý logic hiển thị giữ nguyên như cũ ---
def get_col(df, possible_names):
    for name in possible_names:
        for col in df.columns:
            if name.lower() in col.lower(): return col
    return None

col_tram = get_col(df_raw, ["trạm", "tram"])
col_doitac = get_col(df_raw, ["đối tác", "đơn vị"])
# ... (Giữ nguyên các hàm xử lý dữ liệu còn lại của bạn) ...

# (Lưu ý: Bạn hãy giữ lại các đoạn code xử lý tab1, tab2, tab3 bên dưới như bản cũ, 
# chỉ cần thay phần SHEET_URL và load_data ở trên là được)
