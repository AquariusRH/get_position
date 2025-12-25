import streamlit as st
import pandas as pd
import requests
import base64
import json
from io import BytesIO
from PIL import Image

# --- 配置 ---
headers = {
    "authority": "racing.hkjc.com",
    "referer": "https://racing.hkjc.com/racing/speedpro/chinese/formguide/formguide.html",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "adrum": "isAjax:true"
}

st.title("🏇 SpeedPRO 走位圖解析器")

# --- 1. 取得數據 ---
race_no = st.sidebar.number_input("場次", min_value=1, value=1)
url = f"https://racing.hkjc.com/racing/speedpro/assets/json/formguide/race_{race_no}.json"

if st.sidebar.button("獲取並轉換圖片"):
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # 處理馬會 JSON 特有的 BOM 編碼問題
        content = response.content.decode('utf-8-sig')
        data = json.loads(content)
        
        if "RaceMapChi" in data:
            # --- 2. 轉換圖片關鍵步驟 ---
            # 取得原始字串，例如 "data:image/jpeg;base64,/9j/4AAQ..."
            b64_string = data["RaceMapChi"]
            
            # 去除前綴 "data:image/jpeg;base64," 取得純編碼部分
            header, encoded = b64_string.split(",", 1)
            
            # Base64 解碼為二進制字節
            img_data = base64.b64decode(encoded)
            
            # 使用 PIL 打開圖片
            img = Image.open(BytesIO(img_bytes))
            
            # --- 3. 顯示圖片 ---
            st.subheader(f"第 {race_no} 場走位圖")
            st.image(img, use_container_width=True)
            
            # --- 4. 同步分析數據 (按類紀錄) ---
            st.divider()
            st.subheader("📋 走位紀錄分析")
            
            try:
                # 抓取馬匹紀錄
                runners = data["SpeedPRO"][0]["runnerrecords"]
                res = []
                for r in runners:
                    x, y = r.get("lbx", 0), r.get("lby", 0)
                    
                    # 你的分類邏輯
                    run_style = "領放" if x > 750 else ("中段" if x > 350 else "後追")
                    lane_pos = "近欄" if y < 35 else ("二疊" if y < 75 else "外圍")
                    
                    res.append({
                        "馬號": r.get("no"),
                        "跑法": run_style,
                        "位置": lane_pos
                    })
                
                st.table(pd.DataFrame(res).sort_values("馬號"))
            except:
                st.warning("無法從 JSON 中提取詳細座標數據。")
        else:
            st.error("JSON 中找不到 RaceMapChi 欄位。")
