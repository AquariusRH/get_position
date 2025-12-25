import streamlit as st
import pandas as pd
import requests
import base64
import json
from io import BytesIO
from PIL import Image

# 頁面基本配置
st.set_page_config(page_title="HKJC SpeedPro 自動分析", layout="wide")
st.title("🏇 香港賽馬會 SpeedPRO 走位全自動分析")

# --- 1. 定義數據抓取函數 ---
def get_race_data(race_no):
    # 使用你提供的精確路徑
    url = f"https://racing.hkjc.com/racing/speedpro/assets/json/formguide/race_{race_no}.json"
    
    # 整合所有截圖中的 Headers
    headers = {
        "authority": "racing.hkjc.com",
        "method": "GET",
        "path": f"/racing/speedpro/assets/json/formguide/race_{race_no}.json",
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "zh-HK,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6",
        "adrum": "isAjax:true",
        "referer": f"https://racing.hkjc.com/racing/speedpro/chinese/formguide/formguide.html?race={race_no}",
        "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 關鍵修正：解決 Unexpected UTF-8 BOM 報錯
        # 使用 utf-8-sig 進行解碼，自動過濾檔案開頭的 BOM 字符
        content = response.content.decode('utf-8-sig')
        return json.loads(content)
        
    except Exception as e:
        st.error(f"數據讀取失敗: {e}")
        return None

# --- 2. 介面控制 ---
st.sidebar.header("控制台")
race_num = st.sidebar.number_input("輸入場次", min_value=1, max_value=14, value=1)

if st.sidebar.button("獲取並分析數據"):
    data = get_race_data(race_num)
    
    if data:
        st.success(f"成功連線並取得第 {race_num} 場數據")
        
        # 顯示賽事基本資訊
        info = data.get("RaceInfoChi", {})
        st.subheader(f"第 {race_num} 場 - {info.get('RaceName')} ({info.get('Distance')})")
        
        col1, col2 = st.columns([1, 1])
        
        # --- 3. 處理圖片 (Base64) ---
        with col1:
            st.markdown("### 🖼️ 原始走位圖")
            if "RaceMapChi" in data:
                img_data = data["RaceMapChi"].split(",")[1]
                img_bytes = base64.b64decode(img_data)
                st.image(Image.open(BytesIO(img_bytes)), use_container_width=True)

        # --- 4. 解析座標並進行分類 ---
        with col2:
            st.markdown("### 📊 自動位置紀錄")
            try:
                # 進入 SpeedPRO 數據結構獲取馬匹紀錄
                runners = data["SpeedPRO"][0].get("runnerrecords", [])
                results = []

                for r in runners:
                    no = r.get("no")
                    x = r.get("lbx", 0) # 橫向位置
                    y = r.get("lby", 0) # 縱向位置 (疊數)

                    # 分類 1：跑法 (X 座標)
                    if x > 750: run_type = "領放"
                    elif x > 350: run_type = "中段"
                    else: run_type = "後追"

                    # 分類 2：疊數 (Y 座標)
                    if y < 35: lane_type = "近欄"
                    elif y < 75: lane_type = "二疊"
                    else: lane_type = "外圍"

                    results.append({
                        "馬號": no,
                        "跑法": run_type,
                        "疊數位置": lane_type,
                        "精確座標": f"X:{x}, Y:{y}"
                    })

                df = pd.DataFrame(results)
                st.dataframe(df.sort_values("馬號"), hide_index=True, use_container_width=True)

            except Exception as e:
                st.warning("數據結構解析異常，可能該場次資料尚未完整。")

# 頁尾資訊
st.divider()
st.caption("技術說明：本程式自動處理 UTF-8 BOM 編碼並模擬瀏覽器 Header 以確保連線穩定性。")
