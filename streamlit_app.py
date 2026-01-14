import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 設定頁面
st.set_page_config(page_title="賽馬座標偏差分析器", layout="wide")

if 'race_history' not in st.session_state:
    st.session_state.race_history = []

# 禁止拖拽 CSS
st.markdown("<style>.stPlotlyChart { pointer-events: none; }</style>", unsafe_allow_html=True)

st.title("🐎 賽馬座標分析：偏差轉向偵測版")

# --- 數據管理 ---
with st.sidebar:
    st.header("⚙️ 參數設定")
    # 讓用戶自行決定「最新場次」的影響力
    weight_factor = st.slider("最新場次權重強度 (越高則重心反應越快)", 1.1, 1.5, 1.25)
    
    if st.button("🚨 重置數據"):
        st.session_state.race_history = []
        st.rerun()
    
    st.info("💡 **解決中置誤判：**\n當重心落在中游時，請觀察點位分布。若點位散落在兩端，代表賽道可能正在變天，或是兩頭都能跑。")

# --- 數據輸入區 (簡化顯示) ---
total_rows = len(st.session_state.race_history)
current_race_num = (total_rows // 4) + 1

with st.expander(f"📝 輸入第 {current_race_num} 場數據", expanded=True):
    max_cols = st.select_slider("本場總列數", options=[3, 4, 5, 6, 7, 8], value=6)
    rank_scores = {"第一名": 4, "第二名": 3, "第三名": 2, "第四名": 1}
    current_input = []
    tabs = st.tabs(list(rank_scores.keys()))

    for i, (rank_name, score) in enumerate(rank_scores.items()):
        with tabs[i]:
            c1, c2 = st.columns(2)
            with c1:
                pos_x = st.segmented_control(f"位置 (1:後 → {max_cols}:前)", options=list(range(1, max_cols + 1)), default=max_cols, key=f"x_{current_race_num}_{i}")
            with c2:
                pos_y = st.radio(f"疊位", options=[1, 2, 3], horizontal=True, key=f"y_{current_race_num}_{i}")
            
            norm_x = ((pos_x - 1) / (max_cols - 1)) * 10 if max_cols > 1 else 10
            current_input.append({"場次": current_race_num, "名次": rank_name, "Score": score, "標準化X": norm_x, "Y": pos_y})

    if st.button("💾 儲存場次", type="primary", use_container_width=True):
        st.session_state.race_history.extend(current_input)
        st.rerun()

# --- 數據處理與分析 ---
if st.session_state.race_history:
    df = pd.DataFrame(st.session_state.race_history)
    
    # 核心：使用動態加權因子
    df['加權得分'] = df['Score'] * (weight_factor ** df['場次'])

    avg_x = (df['標準化X'] * df['加權得分']).sum() / df['加權得分'].sum()
    avg_y = (df['Y'] * df['加權得分']).sum() / df['加權得分'].sum()

    # 計算 X 軸標準差，判斷數據是否太分散
    x_std = df['標準化X'].std()

    fig = go.Figure()

    # 歷史點位
    fig.add_trace(go.Scatter(
        x=df['標準化X'], y=df['Y'],
        mode='markers+text',
        marker=dict(size=df['加權得分']*10, color=df['加權得分'], colorscale='Turbo'),
        text=df['場次'].astype(str)
    ))

    # 建議範圍
    fig.add_shape(type="rect", x0=avg_x-0.8, y0=avg_y-0.2, x1=avg_x+0.8, y1=avg_y+0.2,
                  fillcolor="rgba(255, 255, 255, 0.2)", line=dict(color="white", width=2))

    fig.update_layout(
        xaxis=dict(title="後追 (0) ←→ 領放 (10)", range=[-1, 11], tickvals=[0, 5, 10]),
        yaxis=dict(title="疊位", tickvals=[1, 2, 3], range=[0.5, 3.5]),
        dragmode=False, template="plotly_dark", height=450
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- 關鍵趨勢警示 ---
    st.subheader("🔍 趨勢分析判斷")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.metric("當前建議相對位置", f"{avg_x:.1f}")
        if x_std > 3.0:
            st.warning("⚠️ **數據極度分散！** 賽道可能正在轉變偏差，或出現了不合常理的頭馬，請謹慎對待「中置」建議。")
        else:
            st.success("✅ 偏差數據集中，建議具備參考價值。")

    with col_b:
        latest_race_x = df[df['場次'] == df['場次'].max()]['標準化X'].mean()
        if abs(latest_race_x - avg_x) > 3:
            st.error("🚨 **警告：最新一場與歷史趨勢大幅背離！** 賽道可能已經變天。")
        else:
            st.info("ℹ️ 最新賽果與整體趨勢吻合。")
