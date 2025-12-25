import streamlit as st
import requests

st.title("HKJC 數據抓取測試")

# 設置場次
race_num = st.sidebar.number_input("場次", min_value=1, max_value=14, value=1)

# 使用你提供的最新 Header 資訊
headers = {
    "authority": "racing.hkjc.com",
    "accept": "*/*",
    "accept-language": "zh-HK,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6",
    "adrum": "isAjax:true",
    "referer": f"https://racing.hkjc.com/racing/speedpro/chinese/formguide/formguide.html?race={race_num}",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
}

url = f"https://racing.hkjc.com/racing/speedpro/assets/json/formguide/race_{race_num}.json"

if st.button("僅抓取 Data"):
    try:
        # 發起請求
        response = requests.get(url, headers=headers, timeout=10)
        
        # 顯示狀態
        st.write(f"**URL:** {url}")
        st.write(f"**HTTP 狀態碼:** {response.status_code}")
        
        if response.status_code == 200:
            st.success("成功抓取數據！")
            
            # 顯示原始的前 500 個字節，看看有沒有奇怪的符號 (例如 BOM)
            raw_data = response.content
            st.subheader("原始數據前 1000 個字節 (Binary):")
            st.code(raw_data[:1000])
            
            # 嘗試用普通 text 顯示 (不進行 JSON 轉換)
            st.subheader("原始文本內容 (Raw Text):")
            st.text(response.text[:1000]) # 僅顯示前 1000 字以防頁面崩潰
            
        else:
            st.error(f"抓取失敗，錯誤代碼：{response.status_code}")
            
    except Exception as e:
        st.error(f"連線發生異常: {e}")

st.info("這個版本不進行 Decode，僅確認伺服器是否有回傳數據。")
