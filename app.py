from datetime import datetime
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# 1. Cấu hình giao diện ứng dụng
st.set_page_config(
    page_title="Quản Lý & Báo Cáo Tiến Độ GPON 2026",
    page_icon="📊",
    layout="wide",
)

st.title("📊 HỆ THỐNG QUẢN LÝ & BÁO CÁO TIẾN ĐỘ GPON 2026")

# Link Google Sheet của bạn
SHEET_URL = "https://docs.google.com/spreadsheets/d/1VPbF7bLk6JF97kJEGw-TW1JEheUf4etfDO5bLsphyGs/edit#gid=0"

# 2. Kết nối tới Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)


@st.cache_data(ttl=10)  # Tự động làm mới dữ liệu sau 10s
def load_data():
    df_main = conn.read(spreadsheet=SHEET_URL, worksheet="0")
    # Xóa khoảng trắng thừa ở đầu/cuối tên cột
    df_main.columns = [str(c).strip() for c in df_main.columns]
    return df_main


try:
    df = load_data()
except Exception as e:
    st.error(f"Chưa kết nối được Google Sheet! Lỗi: {e}")
    st.stop()


# Hàm tìm cột linh hoạt theo từ khóa
def get_col(df, possible_names):
    for name in possible_names:
        for col in df.columns:
            if name.lower() in col.lower():
                return col
    return None


# Nhận diện chính xác tên các cột từ Google Sheet của bạn
col_tram = get_col(df, ["trạm băng rộng", "trạm bằng chữ", "trạm", "tram"])
col_diachi = get_col(df, ["địa chỉ", "dịa chỉ", "địa bàn"])
col_doitac = get_col(df, ["đối tác", "đơn vị"])
col_hodan = get_col(df, ["tổng hộ dân", "hộ dân"])
col_cong = get_col(df, ["tổng số cổng", "số cổng"])

# 3. Tạo các TAB chức năng
tab1, tab2 = st.tabs(
    ["📈 Bảng Điều Khiển Tiến Độ", "📝 Đối Tác Nhập Báo Cáo"]
)

# ==========================================
# TAB 1: XEM TỔNG QUAN & TIẾN ĐỘ (QUẢN LÝ)
# ==========================================
with tab1:
    st.subheader("📌 Tổng quan dữ liệu hạ tầng GPON")

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
        selected_doitac = st.multiselect("Lọc theo Đối tác:", options=doitac_list)

    # Lọc dữ liệu
    df_filtered = df.copy()
    if selected_diaban and col_diachi:
        df_filtered = df_filtered[df_filtered[col_diachi].isin(selected_diaban)]
    if selected_doitac and col_doitac:
        df_filtered = df_filtered[df_filtered[col_doitac].isin(selected_doitac)]

    # Các thẻ chỉ số
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng số trạm", len(df_filtered))

    if col_hodan:
        val_hodan = pd.to_numeric(
            df_filtered[col_hodan], errors="coerce"
        ).sum()
        c2.metric("Tổng số hộ dân", f"{val_hodan:,.0f}")

    if col_cong:
        val_cong = pd.to_numeric(df_filtered[col_cong], errors="coerce").sum()
        c3.metric("Tổng số cổng", f"{val_cong:,.0f}")

    st.markdown("---")
    st.subheader("📋 Bảng chi tiết danh mục các trạm")
    st.dataframe(df_filtered, use_container_width=True)

# ==========================================
# TAB 2: ĐỐI TÁC NHẬP BÁO CÁO HÀNG NGÀY
# ==========================================
with tab2:
    st.subheader("📝 Báo cáo khối lượng hoàn thành trong ngày")
    st.info("Đối tác chọn thông tin trạm và nhập số lượng công việc đã hoàn thành.")

    with st.form("form_bao_cao", clear_on_submit=True):
        col_input1, col_input2 = st.columns(2)

        with col_input1:
            ngay_baocao = st.date_input("Ngày thực hiện:", datetime.now())

            # Lấy danh sách trạm từ cột "Trạm băng rộng"
            tram_options = []
            if col_tram:
                tram_options = [
                    str(t)
                    for t in df[col_tram].dropna().unique().tolist()
                    if str(t).strip() != ""
                ]

            selected_tram = st.selectbox(
                "Chọn Trạm thi công:",
                options=tram_options,
                help="Chọn mã trạm cần báo cáo tiến độ",
            )
            doi_tao = st.text_input("Tên Đơn vị / Đối tác thi công:")

        with col_input2:
            so_luong_xong = st.number_input(
                "Số lượng / Số cổng đã hoàn thành:", min_value=0, step=1
            )
            ghi_chu = st.text_area("Ghi chú tiến độ / Khó khăn vướng mắc:")

        btn_submit = st.form_submit_button("🚀 Gửi Báo Cáo Tiến Độ")

        if btn_submit:
            if not doi_tao:
                st.warning("Vui lòng nhập Tên Đơn vị / Đối tác thi công!")
            elif not selected_tram:
                st.warning("Vui lòng chọn Trạm thi công!")
            else:
                try:
                    df_baocao = conn.read(
                        spreadsheet=SHEET_URL, worksheet="Baocao_Tiendo"
                    )

                    new_row = pd.DataFrame([
                        {
                            "Ngay": str(ngay_baocao),
                            "Tram": selected_tram,
                            "Doi_Tao": doi_tao,
                            "So_Luong_Xong": so_luong_xong,
                            "Ghi_Chu": ghi_chu,
                        }
                    ])

                    df_updated = pd.concat(
                        [df_baocao, new_row], ignore_index=True
                    )
                    conn.update(
                        spreadsheet=SHEET_URL,
                        worksheet="Baocao_Tiendo",
                        data=df_updated,
                    )

                    st.success("✅ Đã ghi nhận báo cáo tiến độ thành công!")
                    st.cache_data.clear()
                except Exception as ex:
                    st.error(
                        f"Lỗi lưu dữ liệu: Vui lòng đảm bảo đã tạo tab 'Baocao_Tiendo' trên Google Sheet! Chi tiết: {ex}"
                    )
