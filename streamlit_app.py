import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 設定頁面
st.set_page_config(page_title="賽馬座標偏差分析器", layout="wide")

# 1. 初始化數據紀錄
if 'race_history' not in st.session_state:
    st.session_state.race_history = []

# 自定義 CSS：確保圖表區域不響應滑鼠拖拽事件
st.markdown("""
    <style>
    .stPlotlyChart { pointer-events: none; } 
    </style>
    """, unsafe_allow_html=True)

st.title("🐎 賽馬座標分析 (公平標準化 + 固定顯示)")

# 計算目前場次
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
        if st.button("🔙 刪除最後一場"):
            st.session_state.race_history = st.session_state.race_history[:-4]
            st.rerun()
    
    st.divider()
    st.info("💡 **公平分析邏輯：**\n系統會將不同列數的場次縮放至 0-10 的標準尺碼。例如：5列中的第5列與6列中的第6列，都會被視為 10 (極領放)。")

# --- 2. 數據輸入區 ---
st.header(f"📝 輸入第 {current_race_num} 場結果")

# 設定本場列數 (3-8列)
max_cols_current = st.select_slider(
    "根據走位圖，這場比賽馬群水平分布共分為幾列？", 
    options=[3, 4, 5, 6, 7, 8], 
    value=6,
    key=f"max_col_slider_{current_race_num}"
)

st.markdown(f"🔗 [點此開啟馬會走位圖網頁 (第 {current_race_num} 場參考)](https://racing.hkjc.com/racing/speedpro/chinese/formguide/formguide.html)")

rank_scores = {"第一名": 4, "第二名": 3, "第三名": 2, "第四名": 1}
current_input = []

tabs = st.tabs(list(rank_scores.keys()))

for i, (rank_name, score) in enumerate(rank_scores.items()):
    with tabs[i]:
        col_x, col_y = st.columns(2)
        with col_x:
            # 水平：根據設定的 max_cols 動態生成按鈕
            pos_x = st.segmented_control(
                f"水平位置 (1:後追 ←→ {max_cols_current}:領放)", 
                options=list(range(1, max_cols_current + 1)), 
                default=max_cols_current,
                key=f"x_{current_race_num}_{i}"
            )
        with col_y:
            # 垂直：固定 1, 2, 3
            pos_y = st.radio(
                f"垂直疊位", 
                options=[1, 2, 3], 
                format_func=lambda x: {1: "1 (內)", 2: "2 (二疊)", 3: "3 (外)"}[x], 
                horizontal=True, 
                key=f"y_{current_race_num}_{i}"
            )
        
        # 標準化邏輯：將 X 縮放至 0-10 區間
        # 公式: ((當前列 - 1) / (總列數 - 1)) * 10
        norm_x = ((pos_x - 1) / (max_cols_current - 1)) * 10 if max_cols_current > 1 else 10
        
        current_input.append({
            "場次": current_race_num,
            "名次": rank_name,
            "原始分數": score,
            "原始X": pos_x,
            "總列數": max_cols_current,
            "標準化X": norm_x,
            "Y": pos_y
        })

if st.button("💾 儲存此場結果", type="primary", use_container_width=True):
    st.session_state.race_history.extend(current_input)
    st.rerun()

st.divider()

# --- 3. 數據視覺化 ---
if st.session_state.race_history:
    df = pd.DataFrame(st.session_state.race_history)
    
    # 指數權重
    df['加權得分'] = df['原始分數'] * (1.1 ** df['場次'])

    fig = go.Figure()

    # 歷史數據點 (使用標準化後的 X)
    fig.add_trace(go.Scatter(
        x=df['標準化X'], y=df['Y'],
        mode='markers+text',
        marker=dict(
            size=df['加權得分'] * 15,
            color=df['加權得分'],
            colorscale='Viridis',
            line=dict(width=1, color='white')
        ),
        text=df['場次'].astype(str),
        textposition="middle center",
        name="獲獎位置"
    ))

    # 計算加權中心
    avg_x = (df['標準化X'] * df['加權得分']).sum() / df['加權得分'].sum()
    avg_y = (df['Y'] * df['加權得分']).sum() / df['加權得分'].sum()

    # 繪製最佳範圍
    fig.add_shape(type="rect",
        xref="x", yref="y",
        x0=avg_x-1, y0=avg_y-0.3, x1=avg_x+1, y1=avg_y+0.3,
        fillcolor="rgba(255, 75, 75, 0.2)",
        line=dict(color="Red", width=2),
    )

    fig.update_layout(
        title="🏃 跨場次偏差分佈 (已標準化列數)",
        xaxis=dict(
            title="← 後追 (0) | 領放 (10) →", 
            range=[-0.5, 10.5],
            tickvals=[0, 2.5, 5, 7.5, 10],
            ticktext=["末尾", "後中", "中游", "前中", "領先"]
        ),
        yaxis=dict(
            title="內欄 (1) ↑ 外疊 (3)", 
            tickvals=[1, 2, 3],
            range=[0.5, 3.5]
        ),
        dragmode=False, # 禁用拖拽
        height=500,
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- 4. 分析總結 ---
    res_l, res_r = st.columns([1, 2])
    with res_l:
        st.subheader("🎯 綜合重心")
        h_desc = "極端後追" if avg_x < 2.5 else ("中游/跟前" if avg_x < 7.5 else "領放/跟前")
        v_desc = "貼欄" if avg_y < 1.5 else ("二疊" if avg_y < 2.5 else "外疊")
        st.success(f"目前優勢位置：**{h_desc}** + **{v_desc}**")
        st.info(f"建議鎖定相對位置 **{avg_x:.1f}** 的馬匹。")

    with res_r:
        st.subheader("📋 數據紀錄")
        st.dataframe(df[['場次', '名次', '原始X', '總列數', 'Y', '標準化X']].sort_values(by=['場次'], ascending=False), hide_index=True)

else:
    st.info("💡 歡迎！請標記比賽數據以觀察賽道偏差。")
