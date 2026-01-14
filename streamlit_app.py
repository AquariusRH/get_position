import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 設定頁面
st.set_page_config(page_title="賽馬座標偏差分析器", layout="wide")

# 1. 初始化數據紀錄
if 'race_history' not in st.session_state:
    st.session_state.race_history = []

st.title("🐎 賽馬座標偏差分析 (固定疊位版)")

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
    st.info("💡 **座標映射說明：**\n- **X 軸 (水平):** 0 (後追) → 10 (領放)\n- **Y 軸 (垂直):** 1:內欄, 2:二疊, 3:三疊/外")

# --- 2. 數據輸入區 ---
st.header(f"📝 輸入第 {current_race_num} 場結果")

st.markdown(f"🔗 [點此開啟馬會走位圖網頁 (第 {current_race_num} 場參考)](https://racing.hkjc.com/racing/speedpro/chinese/formguide/formguide.html)")

rank_scores = {"第一名": 4, "第二名": 3, "第三名": 2, "第四名": 1}
current_input = []

# 輸入介面
tabs = st.tabs(list(rank_scores.keys()))

for i, (rank_name, score) in enumerate(rank_scores.items()):
    with tabs[i]:
        st.write(f"請標記 **{rank_name}** 的位置：")
        col_x, col_y = st.columns(2)
        with col_x:
            # 水平位置保持 Slider (0-10)
            pos_x = st.slider(f"水平位置 (0:後追 ←→ 10:領放)", 0.0, 10.0, 5.0, step=0.5, key=f"x_{current_race_num}_{i}")
        with col_y:
            # 垂直位置改為固定三個選擇
            pos_y = st.radio(f"垂直疊位", options=[1, 2, 3], format_func=lambda x: {1: "1 (內欄)", 2: "2 (二疊)", 3: "3 (三疊或外)"}[x], horizontal=True, key=f"y_{current_race_num}_{i}")
        
        current_input.append({
            "場次": current_race_num,
            "名次": rank_name,
            "原始分數": score,
            "X": pos_x,
            "Y": pos_y
        })

if st.button("💾 儲存此場結果", type="primary", use_container_width=True):
    st.session_state.race_history.extend(current_input)
    st.rerun()

st.divider()

# --- 3. 數據視覺化 ---
if st.session_state.race_history:
    df = pd.DataFrame(st.session_state.race_history)
    
    # 指數加權計算
    df['加權得分'] = df['原始分數'] * (1.1 ** df['場次'])

    # 繪製圖表
    fig = go.Figure()

    # 歷史數據點
    fig.add_trace(go.Scatter(
        x=df['X'], y=df['Y'],
        mode='markers+text',
        marker=dict(
            size=df['加權得分'] * 12,
            color=df['加權得分'],
            colorscale='Hot',
            showscale=True,
            line=dict(width=1, color='white')
        ),
        text=df['場次'].astype(str),
        textposition="middle center",
        name="獲獎位置"
    ))

    # 計算加權中心
    avg_x = (df['X'] * df['加權得分']).sum() / df['加權得分'].sum()
    avg_y = (df['Y'] * df['加權得分']).sum() / df['加權得分'].sum()

    # 繪製建議範圍（最佳區域）
    fig.add_shape(type="rect", # 使用矩形在固定軌道上更直觀
        xref="x", yref="y",
        x0=avg_x-1.5, y0=avg_y-0.4, x1=avg_x+1.5, y1=avg_y+0.4,
        fillcolor="rgba(0, 255, 0, 0.2)",
        line=dict(color="Lime", width=2),
    )

    fig.update_layout(
        title="🏃 賽道偏差熱力圖 (1-3 軌道分布)",
        xaxis=dict(
            title="後追 (0) ←──────→ 領放 (10)", 
            range=[-0.5, 10.5],
            gridcolor='rgba(255,255,255,0.1)'
        ),
        yaxis=dict(
            title="疊位 (1:內 / 2:中 / 3:外)", 
            tickvals=[1, 2, 3],
            ticktext=["1 (內欄)", "2 (二疊)", "3 (外疊)"],
            range=[0.5, 3.5], 
            gridcolor='rgba(255,255,255,0.1)'
        ),
        height=500,
        template="plotly_dark",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- 4. 分析結果 ---
    res_l, res_r = st.columns([1, 2])
    with res_l:
        st.subheader("🎯 重心預測")
        h_desc = "大後方衝刺" if avg_x < 3.5 else ("中游推進" if avg_x < 7 else "前方領放")
        v_desc = "貼欄省腳程" if avg_y < 1.5 else ("二疊望空" if avg_y < 2.5 else "外疊包抄")
        
        st.success(f"**最佳跑法：** {h_desc}")
        st.success(f"**最佳取線：** {v_desc}")
        st.info(f"建議座標：X={avg_x:.1f}, Y={avg_y:.1f}")

    with res_r:
        st.subheader("📋 歷史紀錄")
        st.dataframe(df[['場次', '名次', 'X', 'Y', '加權得分']].sort_values(by=['場次'], ascending=False), hide_index=True)

else:
    st.info("👋 請開始標記前四名位置。垂直位置已固定為 1 (內), 2 (二疊), 3 (外)。")
