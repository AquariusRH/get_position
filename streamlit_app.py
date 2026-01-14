import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 設定頁面
st.set_page_config(page_title="賽馬座標偏差分析器", layout="wide")

# 初始化數據紀錄
if 'race_history' not in st.session_state:
    st.session_state.race_history = []

# 禁止圖表拖拽的 CSS
st.markdown("""
    <style>
    .stPlotlyChart { pointer-events: none; } 
    </style>
    """, unsafe_allow_html=True)

st.title("🐎 賽馬座標偏差分析 (完整功能版)")

# --- 側邊欄：數據管理 (包含刪除按鈕) ---
with st.sidebar:
    st.header("⚙️ 數據管理")
    total_data_points = len(st.session_state.race_history)
    st.write(f"目前已記錄場次: **{total_data_points // 4}**")
    
    # 重置按鈕
    if st.button("🚨 重置所有數據"):
        st.session_state.race_history = []
        st.rerun()
    
    # 重新找回的刪除最後一場按鈕
    if total_data_points >= 4:
        if st.button("🔙 刪除最後一場 (4行)"):
            st.session_state.race_history = st.session_state.race_history[:-4]
            st.rerun()
    
    st.divider()
    weight_factor = st.slider("最新場次權重強度", 1.1, 1.5, 1.2, help="越高代表越看重最近一場的結果")

# --- 2. 數據輸入區 ---
total_rows = len(st.session_state.race_history)
current_race_num = (total_rows // 4) + 1

st.header(f"📝 輸入第 {current_race_num} 場結果")
st.markdown(f"🔗 [點此開啟馬會走位圖網頁 (第 {current_race_num} 場參考)](https://racing.hkjc.com/racing/speedpro/chinese/formguide/formguide.html)")

# 設定本場列數 (用來標準化公平分析)
max_cols_current = st.select_slider(
    "根據走位圖，這場水平分布共幾列？", 
    options=[3, 4, 5, 6, 7, 8], 
    value=6,
    key=f"max_col_slider_{current_race_num}"
)

rank_scores = {"第一名": 4, "第二名": 3, "第三名": 2, "第四名": 1}
current_input = []

tabs = st.tabs(list(rank_scores.keys()))

for i, (rank_name, score) in enumerate(rank_scores.items()):
    with tabs[i]:
        col_x, col_y = st.columns(2)
        with col_x:
            pos_x = st.segmented_control(
                f"水平位置 (1:後追 ←→ {max_cols_current}:領放)", 
                options=list(range(1, max_cols_current + 1)), 
                default=max_cols_current,
                key=f"x_{current_race_num}_{i}"
            )
        with col_y:
            pos_y = st.radio(
                f"垂直疊位", options=[1, 2, 3], 
                format_func=lambda x: {1: "1 (內)", 2: "2 (二疊)", 3: "3 (外)"}[x], 
                horizontal=True, key=f"y_{current_race_num}_{i}"
            )
        
        # 公平標準化 X 座標至 0-10 區間
        norm_x = ((pos_x - 1) / (max_cols_current - 1)) * 10 if max_cols_current > 1 else 10
        
        current_input.append({
            "場次": current_race_num,
            "名次": rank_name,
            "Score": score,
            "標準化X": norm_x,
            "Y": pos_y
        })

if st.button("💾 儲存此場結果", type="primary", use_container_width=True):
    st.session_state.race_history.extend(current_input)
    st.rerun()

st.divider()

# --- 3. 數據視覺化與分析 ---
if st.session_state.race_history:
    df = pd.DataFrame(st.session_state.race_history)
    df['加權得分'] = df['Score'] * (weight_factor ** df['場次'])

    # 計算加權中心
    avg_x = (df['標準化X'] * df['加權得分']).sum() / df['加權得分'].sum()
    avg_y = (df['Y'] * df['加權得分']).sum() / df['加權得分'].sum()
    
    # 趨勢警示邏輯
    x_std = df['標準化X'].std()
    latest_x = df[df['場次'] == df['場次'].max()]['標準化X'].mean()

    fig = go.Figure()

    # 數據點
    fig.add_trace(go.Scatter(
        x=df['標準化X'], y=df['Y'],
        mode='markers+text',
        marker=dict(size=df['加權得分']*12, color=df['加權得分'], colorscale='Viridis', showscale=True),
        text=df['場次'].astype(str),
        textposition="middle center"
    ))

    # 建議重心區 (紅框)
    fig.add_shape(type="rect",
        x0=avg_x-1, y0=avg_y-0.2, x1=avg_x+1, y1=avg_y+0.2,
        fillcolor="rgba(255, 0, 0, 0.2)", line=dict(color="Red", width=2)
    )

    fig.update_layout(
        title="🏃 賽道偏差標準化分佈圖 (0:末尾 | 10:領先)",
        xaxis=dict(title="水平相對位置", range=[-0.5, 10.5], tickvals=[0, 5, 10]),
        yaxis=dict(title="疊位", tickvals=[1, 2, 3], range=[0.5, 3.5]),
        dragmode=False, height=500, template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

    # 結論提示
    c1, c2 = st.columns(2)
    with c1:
        st.metric("建議重心 X 座標", f"{avg_x:.1f}")
        if x_std > 3:
            st.warning("⚠️ 警告：數據極為分散，可能存在多重偏差或變天中。")
    with c2:
        if abs(latest_x - avg_x) > 3.5:
            st.error("🚨 偵測到轉變：最新場次與先前趨勢嚴重不符！")
        else:
            st.success("✅ 目前趨勢穩定。")

else:
    st.info("👋 歡迎！請開始輸入數據。側邊欄可以隨時刪除最後一場或重置。")
