import streamlit as st
import pandas as pd
import json
import base64
from io import BytesIO
from PIL import Image

# --- 頁面設定 ---
st.set_page_config(page_title="HKJC Speed Map 分析器", layout="wide")
st.title("🏇 馬會走位圖自動分類工具")

# --- 模擬數據處理函數 (你可以更換為 requests.get(url).json()) ---
def process_hkjc_data(json_input):
    try:
        # 1. 解析 Base64 走位圖
        if "RaceMapChi" in json_input:
            img_b64 = json_input["RaceMapChi"].split(",")[1]
            img_bytes = base64.b64decode(img_b64)
            speed_map_img = Image.open(BytesIO(img_bytes))
        else:
            speed_map_img = None

        # 2. 解析馬匹座標並分類 (假設數據在 SpeedPRO 的第一個項目中)
        runners = json_input["SpeedPRO"][0]["runnerrecords"]
        processed_list = []

        for r in runners:
            # 取得馬號與座標 (lbx, lby 是馬會常用的座標欄位)
            # 註：若 JSON 欄位名稱不同，請依據實際截圖修改
            no = r.get("no") or r.get("HorseNo")
            x = r.get("lbx", 0)  # 水平座標
            y = r.get("lby", 0)  # 垂直座標

            # --- 分類邏輯 ---
            # 1. 跑法 (領放/中段/後追) - X 軸通常越大越前面
            if x > 700: run_style = "領放 🟢"
            elif x > 300: run_style = "中段 🟡"
            else: run_style = "後追 🔴"

            # 2. 疊數 (近欄/二疊/外圍) - Y 軸通常越小越貼欄
            if y < 30: lane_style = "近欄 (1疊)"
            elif y < 70: lane_style = "二疊"
            else: lane_style = "外圍 (3疊+)"

            processed_list.append({
                "馬號": no,
                "跑法分類": run_style,
                "位置疊數": lane_style,
                "X座標": x,
                "Y座標": y
            })

        return speed_map_img, pd.DataFrame(processed_list)
    except Exception as e:
        st.error(f"數據解析失敗: {e}")
        return None, None

# --- Streamlit 介面 ---
st.sidebar.header("數據輸入")
json_text = st.sidebar.text_area("請貼上 race_1.json 的完整內容", height=300)

if json_text:
    data = json.loads(json_text)
    img, df = process_hkjc_data(data)

    if img:
        st.subheader("🖼️ 原始走位圖 (Base64 提取)")
        st.image(img, use_container_width=True)

    if df is not None:
        st.divider()
        st.subheader("📊 自動分類結果")
        
        # 建立過濾器
        col1, col2 = st.columns(2)
        with col1:
            f_style = st.multiselect("篩選跑法", options=df["跑法分類"].unique(), default=df["跑法分類"].unique())
        with col2:
            f_lane = st.multiselect("篩選疊數", options=df["位置疊數"].unique(), default=df["位置疊數"].unique())

        filtered_df = df[df["跑法分類"].isin(f_style) & df["位置疊數"].isin(f_lane)]
        
        # 顯示表格
        st.dataframe(
            filtered_df.sort_values(by="X座標", ascending=False), 
            column_order=("馬號", "跑法分類", "位置疊數"),
            use_container_width=True
        )

else:
    st.info("請在左側貼上從 F12 獲取的 JSON 內容來開始分析。")

# --- 頁尾說明 ---
st.caption("註：跑法分類基準值(X:300/700)可根據不同場次路程自行調整。")
