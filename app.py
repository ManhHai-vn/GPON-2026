from datetime import datetime
import pandas as pd
import requests
import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(
    page_title="Quản Lý & Báo Cáo Tiến Độ GPON 2026",
    page_icon="🔒",
    layout="wide",
)

# ⚠️ THAY ĐƯỜNG LINK WEB APP BẠN VỪA COPY Ở BƯỚC 1 VÀO ĐÂY:
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbx6LM83RsM_Yzd-vheo2ZnicwK8FHB2g1C5WboGMOt0FJHpI_2QFR4dTpLAv8G8lKz7xQ/exec"

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
        username = st.text_input("Tên đăng nhập (Username):").strip().lower()
        password = st.text_input("Mật khẩu (Password):", type="password")
        submit = st.form_submit_button("Đăng nhập")
        if submit:
            if username in USERS and USERS[username]["pass"] == password:
                st.session_state["logged_in"] = True
                st.session_state["user_info"] = USERS[username]
                st.success("Đăng nhập thành công!")
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

conn = st.connection("gsheets", type=GSheetsConnection)


@st.cache_data(ttl=10)
def load_data():
    df_main = conn.read(spreadsheet=SHEET_URL, worksheet="0")
    df_main.columns = [str(c).strip() for c in df_main.columns]
    return df_main


try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Lỗi kết nối Google Sheets: {e}")
    st.stop()


def get_col(df, possible_names):
    for name in possible_names:
        for col in df.columns:
            if name.lower() in col.lower():
                return col
    return None


col_tram = get_col(df_raw, ["trạm băng rộng", "trạm bằng chữ", "trạm", "tram"])
col_diachi = get_col(df_raw, ["địa chỉ", "dịa chỉ", "địa bàn"])
col_doitac = get_col(df_raw, ["đối tác", "đơn vị"])
col_hodan = get_col(df_raw, ["tổng hộ dân", "hộ dân"])
col_cong = get_col(df_raw, ["tổng số cổng", "số cổng"])

if user["role"] == "admin":
    df = df_raw.copy()
else:
    if col_doitac:
        df = df_raw[
            df_raw[col_doitac].str.contains(user["role"], case=False, na=False)
        ].copy()
    else:
        df = df_raw.copy()

tab1, tab2 = st.tabs(
    ["📈 Bảng Điều Khiển Tiến Độ", "📝 Đối Tác Nhập Báo Cáo"]
)

with tab1:
    st.subheader(
        f"📌 Tổng quan dữ liệu ({'Toàn bộ' if user['role']=='admin' else user['role']})"
    )

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        dia_ban_list = (
            df[col_diachi].dropna().unique().tolist() if col_diachi else []
        )
        selected_diaban = st.multiselect("Lọc theo Địa chỉ:", options=dia_ban_list)
    with col_f2:
        doitac_list = (
            df[col_doitac].dropna().unique().tolist() if col_doitac else []
        )
        selected_doitac = st.multiselect(
            "Lọc theo Đối tác:",
            options=doitac_list,
            disabled=(user["role"] != "admin"),
        )

    df_filtered = df.copy()
    if selected_diaban and col_diachi:
        df_filtered = df_filtered[df_filtered[col_diachi].isin(selected_diaban)]
    if selected_doitac and col_doitac and user["role"] == "admin":
        df_filtered = df_filtered[df_filtered[col_doitac].isin(selected_doitac)]

    c1, c2, c3 = st.columns(3)
    c1.metric("Số trạm quản lý", len(df_filtered))
    if col_hodan:
        c2.metric(
            "Tổng số hộ dân",
            f"{pd.to_numeric(df_filtered[col_hodan], errors='coerce').sum():,.0f}",
        )
    if col_cong:
        c3.metric(
            "Tổng số cổng",
            f"{pd.to_numeric(df_filtered[col_cong], errors='coerce').sum():,.0f}",
        )

    st.markdown("---")
    st.subheader("📋 Danh sách các trạm thi công")
    st.dataframe(df_filtered, use_container_width=True)

with tab2:
    st.subheader("📝 Báo cáo khối lượng hoàn thành trong ngày")

    with st.form("form_bao_cao", clear_on_submit=True):
        col_input1, col_input2 = st.columns(2)

        with col_input1:
            ngay_baocao = st.date_input("Ngày thực hiện:", datetime.now())

            tram_options = []
            if col_tram:
                tram_options = [
                    str(t)
                    for t in df[col_tram].dropna().unique().tolist()
                    if str(t).strip() != ""
                ]

            selected_tram = st.selectbox(
                "Chọn Trạm thi công:", options=tram_options
            )
            doi_tao = st.text_input(
                "Tên Đơn vị / Đối tác thi công:",
                value=user["name"],
                disabled=True,
            )

        with col_input2:
            so_luong_xong = st.number_input(
                "Số lượng / Số cổng đã hoàn thành:", min_value=0, step=1
            )
            ghi_chu = st.text_area("Ghi chú tiến độ / Khó khăn vướng mắc:")

        btn_submit = st.form_submit_button("🚀 Gửi Báo Cáo Tiến Độ")

        if btn_submit:
            if not selected_tram:
                st.warning("Vui lòng chọn Trạm thi công!")
            else:
                payload = {
                    "Ngay": str(ngay_baocao),
                    "Tram": selected_tram,
                    "Doi_Tao": user["role"],
                    "So_Luong_Xong": int(so_luong_xong),
                    "Ghi_Chu": ghi_chu,
                }
                try:
                    res = requests.post(WEB_APP_URL, json=payload)
                    if res.status_code == 200:
                        st.success(
                            "✅ Đã ghi nhận báo cáo tiến độ vào Google Sheets thành công!"
                        )
                        st.cache_data.clear()
                    else:
                        st.error(
                            f"Lỗi kết nối Web App Google Sheets (Mã lỗi: {res.status_code})"
                        )
                except Exception as ex:
                    st.error(f"Lỗi gửi dữ liệu: {ex}")
