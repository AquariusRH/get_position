import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import base64
from PIL import Image
from io import BytesIO

# --- 新增：抓取馬會走位圖函數 ---
def get_race_map(race_no):
    """從馬會 API 獲取特定場次的走位圖圖片"""
    api_url = f"https://racing.hkjc.com/racing/speedpro/assets/json/formguide/race_{race_no}.json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Referer": "https://racing.hkjc.com/racing/speedpro/chinese/formguide/formguide.html"
    }
    try:
        response = requests.get(api_url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            base64_img = data.get("RaceMapChi", "")
            if "," in base64_img:
                base64_data = base64_img.split(",")[1]
                img_data = base64.b64decode(base64_data)
                return Image.open(BytesIO(img_data))
    except Exception:
        return None
    return None

# 設定頁面
st.set_page_config(page_title="賽馬跑法與檔位分析器", layout="wide")
# --- 偵錯測試區 ---
st.sidebar.subheader("🔍 API 測試狀態")
test_race_no = (len(st.session_state.race_history) // 4) + 1
test_url = f"https://racing.hkjc.com/racing/speedpro/assets/json/formguide/race_{test_race_no}.json"

try:
    # 模擬更完整的瀏覽器 Header
    test_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://racing.hkjc.com/racing/speedpro/chinese/formguide/formguide.html",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    resp = requests.get(test_url, headers=test_headers, timeout=5)
    
    if resp.status_code == 200:
        st.sidebar.success(f"API 連線成功 (Race {test_race_no})")
        # 檢查 JSON 內容是否完整
        try:
            json_data = resp.json()
            if "RaceMapChi" in json_data:
                st.sidebar.info("✅ 成功解析 JSON 並找到 RaceMapChi")
            else:
                st.sidebar.warning("⚠️ JSON 格式不符 (缺少 RaceMapChi)")
        except:
            st.sidebar.error("❌ 無法解析為 JSON 格式")
    else:
        st.sidebar.error(f"連線失敗! 狀態碼: {resp.status_code}")
        st.sidebar.write("請確認比賽日當天該 JSON 是否已上傳。")

except Exception as e:
    st.sidebar.error(f"發生錯誤: {e}")
# --- 測試結束 ---
# 1. 初始化數據紀錄 (Session State)
if 'race_history' not in st.session_state:
    st.session_state.race_history = []

# 自定義 CSS 隱藏某些互動組件（可選）
st.markdown("""
    <style>
    .stPlotlyChart { pointer-events: none; } /* 全局禁止圖表鼠標事件，若需 Tooltip 則刪除此行 */
    </style>
    """, unsafe_allow_html=True)

st.title("🐎 賽馬算法：多場累積偏差分析")

# 計算目前狀態
total_rows = len(st.session_state.race_history)
current_race_num = (total_rows // 4) + 1

# --- 側邊欄：管理功能 ---
with st.sidebar:
    st.header("⚙️ 數據管理")
    st.write(f"目前已記錄場次: **{total_rows // 4}**")
    
    if st.button("🚨 重置所有數據"):
        st.session_state.race_history = []
        st.rerun()
    
    if total_rows >= 4:
        if st.button("🔙 刪除最後一場 (4行)"):
            st.session_state.race_history = st.session_state.race_history[:-4]
            st.rerun()
    
    st.divider()
    st.info("提示：下方的歷史紀錄表可以直接點擊修改數值，系統會即時重新計算。")

# --- 2. 數據輸入區 ---
st.header(f"📝 輸入第 {current_race_num} 場結果")

# --- 新增：顯示馬會走位圖 ---
with st.expander(f"查看第 {current_race_num} 場參考走位圖", expanded=True):
    speed_map = get_race_map(current_race_num)
    if speed_map:
        st.image(speed_map, use_container_width=True)
    else:
        st.warning("暫時無法從馬會獲取走位圖，請手動觀察。")

rank_scores = {"第一名": 4, "第二名": 3, "第三名": 2, "第四名": 1}

cols = st.columns(4)
current_input = []

# 建立四個輸入框
for i, (rank_name, score) in enumerate(rank_scores.items()):
    with cols[i]:
        st.subheader(rank_name)
        # 使用動態 Key 確保每場重置介面
        style = st.selectbox(f"跑法", ["領放", "中置", "後追"], key=f"style_sel_{current_race_num}_{i}")
        draw = st.selectbox(f"檔位", ["內欄", "二疊", "外檔"], key=f"draw_sel_{current_race_num}_{i}")
        current_input.append({
            "場次": current_race_num, 
            "名次": rank_name, 
            "得分": score, 
            "跑法": style, 
            "檔位": draw
        })

if st.button("💾 儲存此場結果", type="primary", use_container_width=True):
    st.session_state.race_history.extend(current_input)
    st.rerun()

st.divider()

# --- 3. 數據處理與圖表顯示 ---
if st.session_state.race_history:
    full_df = pd.DataFrame(st.session_state.race_history)

    # 分別計算統計數據
    style_stats = full_df.groupby('跑法')['得分'].sum().reset_index()
    draw_stats = full_df.groupby('檔位')['得分'].sum().reset_index()

    # 確保所有類別都出現在圖表中（即使是0分）
    style_stats = style_stats.set_index('跑法').reindex(["領放", "中置", "後追"], fill_value=0).reset_index()
    draw_stats = draw_stats.set_index('檔位').reindex(["內欄", "二疊", "外檔"], fill_value=0).reset_index()

    col_res1, col_res2 = st.columns(2)

    with col_res1:
        st.subheader("🏃 跑法累積得分 (靜態圖)")
        # 使用 Plotly 建立棒形圖
        fig_style = px.bar(style_stats, x='跑法', y='得分', color='跑法', 
                           color_discrete_map={"領放":"#FF4B4B", "中置":"#FFAA00", "後追":"#1C83E1"})
        # 禁用所有拖拽與工具列
        st.plotly_chart(fig_style, use_container_width=True, config={'staticPlot': True})
        st.dataframe(style_stats.sort_values(by='得分', ascending=False), hide_index=True)

    with col_res2:
        st.subheader("🚧 檔位累積得分 (靜態圖)")
        fig_draw = px.bar(draw_stats, x='檔位', y='得分', color='檔位',
                          color_discrete_map={"內欄":"#00C0F2", "二疊":"#F0A3FF", "外檔":"#7D7D7D"})
        # 禁用所有拖拽與工具列
        st.plotly_chart(fig_draw, use_container_width=True, config={'staticPlot': True})
        st.dataframe(draw_stats.sort_values(by='得分', ascending=False), hide_index=True)

    # --- 4. 歷史紀錄編輯區 ---
    st.subheader("📋 數據修訂表 (可直接點擊格子修改)")
    # 使用 data_editor 進行即時編輯
    edited_df = st.data_editor(
        full_df, 
        num_rows="fixed", 
        column_config={
            "得分": st.column_config.NumberColumn(disabled=True), # 禁止手動改分數，維持 4/3/2/1 邏輯
            "場次": st.column_config.NumberColumn(disabled=True)
        },
        key="main_editor"
    )
    
    # 檢查是否有變動，若有則更新 Session
    if not edited_df.equals(full_df):
        st.session_state.race_history = edited_df.to_dict('records')
        st.rerun()

    # 綜合建議顯示
    top_style = style_stats.sort_values(by='得分', ascending=False).iloc[0]['跑法']
    top_draw = draw_stats.sort_values(by='得分', ascending=False).iloc[0]['檔位']
    st.success(f"💡 **目前最優選：** 建議留意使用 **{top_style}** 跑法且排在 **{top_draw}** 的馬匹。")

else:
    st.info("👋 歡迎！請輸入第一場比賽數據後按「儲存」開始分析。")
