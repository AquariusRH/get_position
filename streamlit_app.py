import streamlit as st
import pandas as pd
import requests
import base64
from io import BytesIO
from PIL import Image

# 頁面配置
st.set_page_config(page_title="HKJC SpeedPro 自動分析", layout="wide")
st.title("🏇 香港賽馬會 SpeedPRO 走位全自動分析")

# --- 1. 定義數據抓取函數 ---
def get_race_data(race_no):
    # 根據你提供的路徑拼接 URL
    url = f"https://racing.hkjc.com/racing/speedpro/assets/json/formguide/race_{race_no}.json"
    
    # 根據你截圖中的 Request Headers 設定
    headers = {
        "authority": "racing.hkjc.com",
        "accept": "*/*",
        "accept-language": "zh-HK,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6",
        "referer": "https://racing.hkjc.com/racing/speedpro/chinese/formguide/formguide.html",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "adrum": "isAjax:true"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"獲取數據失敗: {e}")
        return None

# --- 2. 側邊欄控制 ---
st.sidebar.header("設定")
race_num = st.sidebar.selectbox("選擇場次", range(1, 13), index=0)

if st.sidebar.button("開始自動分析"):
    data = get_race_data(race_num)
    
    if data:
        # 顯示賽事資訊
        info = data.get("RaceInfoChi", {})
        st.subheader(f"第 {race_num} 場 - {info.get('RaceName', '')} ({info.get('Distance', '')})")
        st.write(f"日期: {info.get('Date', '')} | 場地: {info.get('Racecourse', '')} {info.get('Track', '')}")

        # --- 3. 處理並顯示走位圖 ---
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 🖼️ 原始走位圖")
            if "RaceMapChi" in data:
                img_b64 = data["RaceMapChi"].split(",")[1]
                img_bytes = base64.b64decode(img_b64)
                st.image(Image.open(BytesIO(img_bytes)), use_container_width=True)

        # --- 4. 解析數據並進行分類 ---
        with col2:
            st.markdown("### 📊 自動分類紀錄")
            try:
                # 取得 SpeedPRO 內馬匹紀錄 (對應截圖中的 runnerrecords)
                runners = data["SpeedPRO"][0].get("runnerrecords", [])
                analysis_results = []

                for r in runners:
                    no = r.get("no")
                    # 抓取座標 lbx (橫向) 與 lby (縱向)
                    x = r.get("lbx", 0)
                    y = r.get("lby", 0)

                    # --- 分類邏輯 ---
                    # 1. 跑法分類 (X 軸) - 數值越大代表越靠前
                    if x > 750: run_style = "領放"
                    elif x > 350: run_style = "中段"
                    else: run_style = "後追"

                    # 2. 疊數分類 (Y 軸) - 數值越小代表越近欄
                    if y < 35: lane_pos = "近欄"
                    elif y < 75: lane_pos = "二疊"
                    else: lane_pos = "外圍"

                    analysis_results.append({
                        "馬號": no,
                        "跑法紀錄": run_style,
                        "位置紀錄": lane_pos,
                        "座標(X,Y)": f"({x}, {y})"
                    })

                # 顯示結果表格
                df = pd.DataFrame(analysis_results)
                st.dataframe(df.sort_values("馬號"), use_container_width=True, hide_index=True)
                
                # 下載按鈕
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("下載分析報表 (CSV)", csv, f
