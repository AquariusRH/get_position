import streamlit as st
import pandas as pd

st.set_page_config(page_title="賽馬多場累積分析器", layout="wide")

# 1. 初始化 Session State
if 'race_history' not in st.session_state:
    st.session_state.race_history = []

st.title("🐎 賽馬算法：多場累積偏差分析")

# 側邊欄：管理與重置
with st.sidebar:
    st.header("⚙️ 數據管理")
    if st.button("🚨 重置所有數據"):
        st.session_state.race_history = []
        st.rerun()
    
    st.divider()
    st.write(f"目前已記錄場次: {len(st.session_state.race_history)}")
    
    # 錯誤修正功能：刪除最後一筆
    if len(st.session_state.race_history) > 0:
        if st.button("🔙 刪除最後一場 (入錯資料)"):
            st.session_state.race_history.pop()
            st.rerun()

# 2. 數據輸入介面
st.header(f"📝 輸入第 {len(st.session_state.race_history) + 1} 場結果")

rank_scores = {"第一名": 4, "第二名": 3, "第三名": 2, "第四名": 1}

cols = st.columns(4)
current_input = []

for i, (rank_name, score) in enumerate(rank_scores.items()):
    with cols[i]:
        st.subheader(rank_name)
        style = st.selectbox(f"跑法", ["領放", "中段", "後追"], key=f"style_in_{i}")
        draw = st.selectbox(f"檔位", ["內欄", "二疊", "外檔"], key=f"draw_in_{i}")
        current_input.append({"場次": len(st.session_state.race_history) + 1, "名次": rank_name, "得分": score, "跑法": style, "檔位": draw})

if st.button("💾 儲存此場結果", type="primary"):
    # 將這一場的四匹馬資料存入歷史
    st.session_state.race_history.extend(current_input)
    st.rerun()

st.divider()

# 3. 數據處理與顯示
if st.session_state.race_history:
    full_df = pd.DataFrame(st.session_state.race_history)

    # 計算統計數據
    style_stats = full_df.groupby('跑法')['得分'].sum().reset_index().sort_values(by='得分', ascending=False)
    draw_stats = full_df.groupby('檔位')['得分'].sum().reset_index().sort_values(by='得分', ascending=False)

    # 顯示分析圖表
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.subheader("🏃 跑法累積得分")
        st.bar_chart(style_stats.set_index('跑法'))
        st.table(style_stats)

    with col_res2:
        st.subheader("🚧 檔位累積得分")
        st.bar_chart(draw_stats.set_index('檔位'))
        st.table(draw_stats)

    # 4. 歷史紀錄編輯區 (這是核心修改功能)
    st.subheader("📋 歷史紀錄與即時修改")
    st.write("如果你發現之前的場次入錯資料，可以直接在下表中修改，系統會自動重新計算：")
    
    # 使用 st.data_editor 讓表格可以直接點擊修改內容
    edited_df = st.data_editor(full_df, num_rows="dynamic", key="data_editor")
    
    # 如果使用者在表格中做了修改，同步回 session_state
    if not edited_df.equals(full_df):
        st.session_state.race_history = edited_df.to_dict('records')
        st.rerun()

    # 綜合建議
    top_style = style_stats.iloc[0]['跑法']
    top_draw = draw_stats.iloc[0]['檔位']
    st.success(f"💡 **當前最強偏差趨勢：** 優先考慮 **{top_style}** + **{top_draw}** 的組合。")

else:
    st.info("尚未有數據，請在上方輸入第一場比賽結果。")
