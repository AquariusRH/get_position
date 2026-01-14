import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 設定頁面
st.set_page_config(page_title="公平座標分析器", layout="wide")

if 'race_history' not in st.session_state:
    st.session_state.race_history = []

st.title("🐎 賽馬公平分析：動態列數標準化")

# --- 數據輸入區 ---
total_rows = len(st.session_state.race_history)
current_race_num = (total_rows // 4) + 1

with st.expander(f"📝 輸入第 {current_race_num} 場數據", expanded=True):
    col_config, _ = st.columns([1, 1])
    with col_config:
        # 關鍵：讓用戶定義這一場「最長」到第幾列
        max_cols = st.select_slider("這場走位圖總共有多少列水平位置？", options=[3, 4, 5, 6, 7, 8], value=6)
    
    st.markdown(f"🔗 [馬會走位圖參考](https://racing.hkjc.com/racing/speedpro/chinese/formguide/formguide.html)")
    
    rank_scores = {"第一名": 4, "第二名": 3, "第三名": 2, "第四名": 1}
    current_input = []
    tabs = st.tabs(list(rank_scores.keys()))

    for i, (rank_name, score) in enumerate(rank_scores.items()):
        with tabs[i]:
            c1, c2 = st.columns(2)
            with c1:
                # 動態調整選項範圍
                pos_x = st.segmented_control(f"水平位置 (1:最後 → {max_cols}:最前)", 
                                           options=list(range(1, max_cols + 1)), 
                                           default=max_cols, key=f"x_{current_race_num}_{i}")
            with c2:
                pos_y = st.radio(f"垂直疊位", options=[1, 2, 3], horizontal=True, key=f"y_{current_race_num}_{i}")
            
            # 標準化計算：(位置 - 1) / (總列數 - 1) -> 縮放至 0~1
            # 例如：5列中的第5列 = (5-1)/(5-1) = 1.0; 6列中的第6列 = (6-1)/(6-1) = 1.0 (公平！)
            norm_x = (pos_x - 1) / (max_cols - 1) if max_cols > 1 else 1.0
            
            current_input.append({
                "場次": current_race_num,
                "名次": rank_name,
                "Score": score,
                "原始X": pos_x,
                "總列數": max_cols,
                "標準化X": norm_x * 10, # 放大回 0-10 方便繪圖
                "Y": pos_y
            })

    if st.button("💾 儲存並公平計算", type="primary", use_container_width=True):
        st.session_state.race_history.extend(current_input)
        st.rerun()

# --- 數據處理與繪圖 ---
if st.session_state.race_history:
    df = pd.DataFrame(st.session_state.race_history)
    df['加權得分'] = df['Score'] * (1.1 ** df['場次'])

    fig = go.Figure()

    # 使用「標準化X」繪圖，確保不同列數的場次在圖中位置一致
    fig.add_trace(go.Scatter(
        x=df['標準化X'], y=df['Y'],
        mode='markers+text',
        marker=dict(size=df['加權得分']*15, color=df['加權得分'], colorscale='Plasma', showscale=True),
        text=df['場次'].astype(str),
        textposition="middle center"
    ))

    # 計算加權中心
    avg_x = (df['標準化X'] * df['加權得分']).sum() / df['加權得分'].sum()
    avg_y = (df['Y'] * df['加權得分']).sum() / df['加權得分'].sum()

    # 繪製最佳範圍
    fig.add_shape(type="rect", x0=avg_x-1, y0=avg_y-0.3, x1=avg_x+1, y1=avg_y+0.3,
                  fillcolor="rgba(0, 255, 0, 0.2)", line=dict(color="Lime"))

    fig.update_layout(
        title="🏃 公平分析熱力圖 (標準化比例)",
        xaxis=dict(title="相對位置 (0:極後追 ←→ 10:極領放)", range=[-0.5, 10.5], tickvals=[0, 5, 10], ticktext=["末尾", "中游", "領先"]),
        yaxis=dict(title="疊位", tickvals=[1, 2, 3], range=[0.5, 3.5]),
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

    # 戰略建議
    st.subheader("🎯 公平趨勢結論")
    h_bias = "領放馬佔優" if avg_x > 7 else ("後追馬強勢" if avg_x < 3 else "均勢/看形勢")
    st.success(f"跨場次綜合分析顯示：今天 **{h_bias}**，建議關注相對位置在 **{avg_x:.1f}** 附近的馬匹。")
