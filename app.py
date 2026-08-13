import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# -------------------------------------------------------------
# 1. CẤU HÌNH TRANG WEB
# -------------------------------------------------------------
st.set_page_config(
    page_title="Hệ Thống Quản Lý & Báo Cáo Tiến Độ GPON 2026",
    page_icon="📊",
    layout="wide"
)

# Đường link Google Sheets của bạn
SHEET_URL = "https://docs.google.com/spreadsheets/d/1VPbF7bLk6JF97kJEGw-TW1JEheUf4etfDO5bLsphyGs/edit#gid=0"

st.title("📊 HỆ THỐNG QUẢN LÝ & BÁO CÁO TIẾN ĐỘ GPON 2026")

# -------------------------------------------------------------
# 2. KẾT NỐI DỮ LIỆU GOOGLE SHEETS
# -------------------------------------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=15)  # Tự động làm mới dữ liệu sau mỗi 15 giây
def load_main_data():
    # Đọc dữ liệu từ Sheet đầu tiên (worksheet=0)
    df = conn.read(spreadsheet=SHEET_URL, worksheet="0")
    return df

try:
    df_main = load_main_data()
except Exception as e:
    st.error("⚠️ Chưa kết nối được với Google Sheets. Vui lòng kiểm tra quyền chia sẻ file 'Bất kỳ ai có liên kết - Người chỉnh sửa'.")
    st.info(f"Chi tiết lỗi: {e}")
    st.stop()

# -------------------------------------------------------------
# 3. GIAO DIỆN CHÍNH (GỒM 2 TAB)
# -------------------------------------------------------------
tab1, tab2 = st.tabs(["📈 Bảng Điều Khiển Tiến Độ", "📝 Đối Tác Nhập Báo Cáo"])

# =============================================================
# TAB 1: DÀNH CHO QUẢN LÝ & THEO DÕI
# =============================================================
with tab1:
    st.subheader("📌 Tổng quan hạ tầng & Bộ lọc tìm kiếm")
    
    # Tạo 2 cột lọc dữ liệu
    col_filter1, col_filter2 = st.columns(2)
    
    with col_filter1:
        diachi_options = df_main['Địa chỉ'].dropna().unique().tolist() if 'Địa chỉ' in df_main.columns else []
        selected_diachi = st.multiselect("Lọc theo Địa chỉ / Huyện:", options=diachi_options)
        
    with col_filter2:
        doitac_options = df_main['Đối tác'].dropna().unique().tolist() if 'Đối tác' in df_main.columns else []
        selected_doitac = st.multiselect("Lọc theo Đối tác thi công:", options=doitac_options)
        
    # Áp dụng bộ lọc
    df_filtered = df_main.copy()
    if selected_diachi:
        df_filtered = df_filtered[df_filtered['Địa chỉ'].isin(selected_diachi)]
    if selected_doitac:
        df_filtered = df_filtered[df_filtered['Đối tác'].isin(selected_doitac)]
        
    # Thống kê con số tổng hợp (Cards)
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng số trạm", len(df_filtered))
    
    if 'Tổng hộ dân' in df_filtered.columns:
        total_ho = pd.to_numeric(df_filtered['Tổng hộ dân'], errors='coerce').sum()
        c2.metric("Tổng số hộ dân", f"{total_ho:,.0f}")
        
    if 'Tổng số cổng' in df_filtered.columns:
        total_cong = pd.to_numeric(df_filtered['Tổng số cổng'], errors='coerce').sum()
        c3.metric("Tổng số cổng GPON", f"{total_cong:,.0f}")
        
    st.markdown("---")
    st.subheader("📋 Bảng chi tiết trạm & chỉ số hạ tầng")
    st.dataframe(df_filtered, use_container_width=True)

# =============================================================
# TAB 2: DÀNH CHO ĐỐI TÁC NHẬP BÁO CÁO HÀNG NGÀY
# =============================================================
with tab2:
    st.subheader("📝 Báo cáo khối lượng hoàn thành trong ngày")
    st.info("Đối tác chọn thông tin trạm và nhập số lượng công việc đã hoàn thành.")
    
    with st.form(key="form_nhap_baocao", clear_on_submit=True):
        f_col1, f_col2 = st.columns(2)
        
        with f_col1:
            ngay_baocao = st.date_input("Ngày thực hiện:", datetime.now())
            
            # Lấy danh sách Trạm
            list_tram = df_main['Trạm bằng chữ'].dropna().unique().tolist() if 'Trạm bằng chữ' in df_main.columns else []
            tram_selected = st.selectbox("Chọn Trạm thi công:", options=list_tram)
            
            doi_tac_input = st.text_input("Tên Đơn vị / Đội thi công:")
            
        with f_col2:
            so_luong = st.number_input("Số lượng / Số cổng đã hoàn thành:", min_value=0, step=1)
            ghi_chu = st.text_area("Ghi chú tiến độ / Khó khăn vướng mắc:")
            
        btn_submit = st.form_submit_button("🚀 Gửi Báo Cáo")
        
        if btn_submit:
            if not doi_tac_input:
                st.warning("⚠️ Vui lòng điền tên Đơn vị/Đội thi công!")
            else:
                try:
                    # Đọc bảng Baocao_Tiendo
                    df_baocao = conn.read(spreadsheet=SHEET_URL, worksheet="Baocao_Tiendo")
                    
                    # Tạo dữ liệu dòng mới
                    new_entry = pd.DataFrame([{
                        "Ngay": str(ngay_baocao),
                        "Tram": tram_selected,
                        "Doi_Tao": doi_tac_input,
                        "So_Luong_Xong": so_luong,
                        "Ghi_Chu": ghi_chu
                    }])
                    
                    # Cập nhật và lưu lại vào Google Sheets
                    df_updated = pd.concat([df_baocao, new_entry], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="Baocao_Tiendo", data=df_updated)
                    
                    st.success("✅ Đã gửi báo cáo thành công! Dữ liệu đã được lưu vào Google Sheets.")
                    st.cache_data.clear()
                except Exception as ex:
                    st.error(f"⚠️ Có lỗi xảy ra khi gửi báo cáo: {ex}")