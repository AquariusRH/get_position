import streamlit as st
import pandas as pd
import plotly.express as px

# 設定頁面
st.set_page_config(page_title="賽馬跑法與檔位分析器", layout="wide")

# 1. 初始化數據紀錄 (Session State)
if 'race_history' not in st.session_state:
    st.session_state.race_history = []

# 自定義 CSS
st.markdown("""
    <style>
    .stPlotlyChart { pointer-events: none; } 
    </style>
    """, unsafe_allow_html=True)

st.title("🐎 賽馬算法：加權累積偏差分析")

# 計算目前狀態
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
        if st.button("🔙 刪除最後一場 (4行)"):
            st.session_state.race_history = st.session_state.race_history[:-4]
            st.rerun()
    
    st.divider()
    st.info("💡 **權重邏輯：** 最新一場的權重最高，分數會乘以其場次編號。")

# --- 2. 數據輸入區 ---
st.header(f"📝 輸入第 {current_race_num} 場結果")

st.markdown(f"🔗 [點此開啟馬會走位圖網頁 (第 {current_race_num} 場)](https://racing.hkjc.com/racing/speedpro/chinese/formguide/formguide.html)")

rank_scores = {"第一名": 4, "第二名": 3, "第三名": 2, "第四名": 1}

cols = st.columns(4)
current_input = []

for i, (rank_name, score) in enumerate(rank_scores.items()):
    with cols[i]:
        st.subheader(rank_name)
        style = st.selectbox(f"跑法", ["領放", "中置", "後追"], key=f"style_sel_{current_race_num}_{i}")
        draw = st.selectbox(f"檔位", ["內欄", "二疊", "外檔"], key=f"draw_sel_{current_race_num}_{i}")
        current_input.append({
            "場次": current_race_num, 
            "名次": rank_name, 
            "原始分數": score, 
            "跑法": style, 
            "檔位": draw
        })

if st.button("💾 儲存此場結果", type="primary", use_container_width=True):
    st.session_state.race_history.extend(current_input)
    st.rerun()

st.divider()

# --- 3. 數據處理 (加上加權邏輯) ---
if st.session_state.race_history:
    full_df = pd.DataFrame(st.session_state.race_history)
    
    # 計算加權分數：原始分數 * 場次
    # 這樣第1場權重為1，第5場權重為5，實現「最新佔比最大」
    full_df['加權得分'] = full_df['原始分數'] * full_df['場次']

    # 聚合加權得分
    style_stats = full_df.groupby('跑法')['加權得分'].sum().reset_index()
    draw_stats = full_df.groupby('檔位')['加權得分'].sum().reset_index()

    # 確保所有類別都存在
    style_stats = style_stats.set_index('跑法').reindex(["領放", "中置", "後追"], fill_value=0).reset_index()
    draw_stats = draw_stats.set_index('檔位').reindex(["內欄", "二疊", "外檔"], fill_value=0).reset_index()

    col_res1, col_res2 = st.columns(2)

    with col_res1:
        st.subheader("🏃 跑法加權累積 (趨勢圖)")
        fig_style = px.line(style_stats, x='跑法', y='加權得分', markers=True,
                            color_discrete_sequence=["#FF4B4B"])
        fig_style.update_traces(line=dict(width=4), marker=dict(size=12))
        st.plotly_chart(fig_style, use_container_width=True, config={'staticPlot': True})
        st.dataframe(style_stats.sort_values(by='加權得分', ascending=False), hide_index=True)

    with col_res2:
        st.subheader("🚧 檔位加權累積 (趨勢圖)")
        fig_draw = px.line(draw_stats, x='檔位', y='加權得分', markers=True,
                           color_discrete_sequence=["#00C0F2"])
        fig_draw.update_traces(line=dict(width=4), marker=dict(size=12))
        st.plotly_chart(fig_draw, use_container_width=True, config={'staticPlot': True})
        st.dataframe(draw_stats.sort_values(by='加權得分', ascending=False), hide_index=True)

    # --- 4. 歷史紀錄編輯區 ---
    st.subheader("📋 數據修訂表")
    edited_df = st.data_editor(
        full_df, 
        num_rows="fixed", 
        column_config={
            "原始分數": st.column_config.NumberColumn(disabled=True),
            "加權得分": st.column_config.NumberColumn(disabled=True),
            "場次": st.column_config.NumberColumn(disabled=True)
        },
        key="main_editor"
    )
    
    if not edited_df.equals(full_df):
        # 排除加權得分這類計算出來的欄位，只存原始數據
        st.session_state.race_history = edited_df.drop(columns=['加權得分']).to_dict('records')
        st.rerun()

    # 綜合建議
    top_style = style_stats.sort_values(by='加權得分', ascending=False).iloc[0]['跑法']
    top_draw = draw_stats.sort_values(by='加權得分', ascending=False).iloc[0]['檔位']
    st.success(f"💡 **目前最優選 (加權後)：** 建議留意使用 **{top_style}** 跑法且排在 **{top_draw}** 的馬匹。")

else:
    st.info("👋 歡迎！請輸入第一場比賽數據後按「儲存」開始分析。")
