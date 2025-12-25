import streamlit as st
import requests
import json

# 設定 Header 確保連線權限
headers = {
    "authority": "racing.hkjc.com",
    "accept": "*/*",
    "referer": "https://racing.hkjc.com/racing/speedpro/chinese/formguide/formguide.html",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "adrum": "isAjax:true"
}

st.title("HKJC RaceMapChi 提取測試")

race_no = st.number_input("場次", min_value=1, value=1)
url = f"https://racing.hkjc.com/racing/speedpro/assets/json/formguide/race_{race_no}.json"

if st.button("獲取原始數據"):
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # 處理 BOM 並讀取內容
        content = response.content.decode('utf-8-sig')
        data = json.loads(content)
        
        # 1. 檢查是否存在該欄位
        if "RaceMapChi" in data:
            st.success("成功找到 'RaceMapChi' 欄位！")
            
            # 2. 顯示原始 Base64 字串的前段 (避免頁面因字串過長崩潰)
            raw_b64 = data["RaceMapChi"]
            st.markdown("### 原始數據內容 (前 200 字):")
            st.code(raw_b64[:200] + "...")
            
            # 3. 提供完整數據下載
            st.download_button(
                label="下載完整 RaceMapChi Base64 字串",
                data=raw_b64,
                file_name=f"race_{race_no}_b64.txt"
            )
        else:
            st.error("JSON 中找不到 'RaceMapChi' 欄位。")
    else:
        st.error(f"連線失敗，狀態碼: {response.status_code}")
