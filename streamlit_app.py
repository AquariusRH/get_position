import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# 設定頁面
st.set_page_config(page_title="賽馬空間偏差分析器", layout="wide")

if 'race_history' not in st.session_state:
    st.session_state.race_history = []

st.title("🐎 賽馬空間偏差：座標點選分析")

# --- 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 數據管理")
    if st.button("🚨 重置數據"):
        st.session_state.race_history = []
        st.rerun()
    st.info("💡 **操作指南：** 在座標圖中點擊前四名的位置。X軸越左代表越前放，Y軸越下代表越內欄。")

# --- 1. 座標輸入區 ---
st.header("📍 標記第 {} 場前四名位置".format(len(st.session_state.race_history)//4 + 1))

# 建立一個座標選取器 (這裡模擬一個可視化輸入介面)
# X: 0(領放) -> 10(後追) | Y: 0(內欄) -> 10(外檔)
col1, col2 = st.columns([1, 1])

with col1:
    st.write("請滑動下方拉條來標定位置（或未來整合點擊事件）")
    
    current_race_data = []
    ranks = ["第一名", "第二名", "第三名", "第四名"]
    scores = [4, 3, 2, 1]
    
    tabs = st.tabs(ranks)
    for i, tab in enumerate(tabs):
        with tab:
            c1, c2 = st.columns(2)
            with c1:
                pos_x = st.slider(f"{ranks[i]} 跑法 (0領放-10後追)", 0.0, 10.0, 5.0, key=f"x_{i}")
            with c2:
                pos_y = st.slider(f"{ranks[i]} 檔位 (0內欄-10外檔)", 0.0, 10.0, 2.0, key=f"y_{i}")
            current_race_data.append({
                "場次": len(st.session_state.race_history)//4 + 1,
                "名次": ranks[i],
                "Score": scores[i],
                "X": pos_x,
                "Y": pos_y
            })

    if st.button("💾 儲存此場位置紀錄", type="primary", use_container_width=True):
        st.session_state.race_history.extend(current_race_data)
        st.rerun()

# --- 2. 數據分析與視覺化 ---
if st.session_state.race_history:
    df = pd.DataFrame(st.session_state.race_history)
    
    # 計算指數加權 (最新場次權重最高)
    df['Weight'] = df['Score'] * (1.1 ** df['場次'])

    # 繪製偏差熱力圖
    fig = go.Figure()

    # 1. 繪製所有歷史點位
    fig.add_trace(go.Scatter(
        x=df['X'], y=df['Y'],
        mode='markers',
        marker=dict(
            size=df['Weight'] * 5,
            color=df['Weight'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="影響力指數")
        ),
        text=df['名次'],
        name="歷史頭馬位置"
    ))

    # 2. 模擬生成「最佳位置範圍」 (使用簡易密度估計)
    # 這裡我們用加權中心點來繪製一個推薦區域
    avg_x = (df['X'] * df['Weight']).sum() / df['Weight'].sum()
    avg_y = (df['Y'] * df['Weight']).sum() / df['Weight'].sum()

    fig.add_shape(type="circle",
        xref="x", yref="y",
        x0=avg_x-1.5, y0=avg_y-1.5, x1=avg_x+1.5, y1=avg_y+1.5,
        fillcolor="rgba(255, 75, 75, 0.3)",
        line_color="Red",
    )

    fig.update_layout(
        title="賽道偏差熱力圖 (紅色圈內為預測黃金地帶)",
        xaxis=dict(title="跑法 (左:領放 <---> 右:後追)", range=[-1, 11]),
        yaxis=dict(title="檔位 (下:內欄 <---> 上:外檔)", range=[11, -1]), # 倒置 Y 軸符合馬場直觀
        height=600,
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- 3. 輸出分析結果 ---
    with col2:
        st.subheader("🎯 戰略建議")
        
        def get_desc_x(x):
            if x < 3: return "極速領放"
            if x < 6: return "好位中置"
            return "大外後追"
        
        def get_desc_y(y):
            if y < 3: return "貼欄省腳程"
            if y < 6: return "二三疊望空"
            return "外疊衝刺"

        st.metric("建議跑法重心", get_desc_x(avg_x))
        st.metric("建議檔位取向", get_desc_y(avg_y))
        
        st.write("---")
        st.write("**加權點位分布數據：**")
        st.dataframe(df[['場次', '名次', 'X', 'Y', 'Weight']].sort_values('Weight', ascending=False), hide_index=True)
