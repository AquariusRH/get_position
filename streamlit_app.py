import streamlit as st
import pandas as pd

st.set_page_config(page_title="賽馬多場累積分析器", layout="wide")

# 初始化 Session State (如果不存在)
if 'race_history' not in st.session_state:
    st.session_state.race_history = []

st.title("🐎 賽馬算法：多場累積偏差分析")
st.write("輸入每場頭四名的資料，系統將自動累計當天整體的跑法與檔位趨勢。")

# 側邊欄控制
with st.sidebar:
    st.header("數據管理")
    if st.button("重置所有數據"):
        st.session_state.race_history = []
        st.rerun()
    
    st.write(f"目前已記錄場次: {len(st.session_state.race_history)}")

# 1. 數據輸入介面
st.header(f"輸入第 {len(st.session_state.race_history) + 1} 場結果")

rank_scores = {"第一名": 4, "第二名": 3, "第三名": 2, "第四名": 1}
current_race_data = []

cols = st.columns(4)
for i, (rank_name, score) in enumerate(rank_scores.items()):
    with cols[i]:
        st.subheader(rank_name)
        style = st.selectbox(f"跑法", ["領放", "中段", "後追"], key=f"style_{i}")
        draw = st.selectbox(f"檔位", ["內欄", "二疊", "外檔"], key=f"draw_{i}")
        current_race_data.append({"rank": rank_name, "score": score, "style": style, "draw": draw})

if st.button("儲存此場結果並計算下一場", type="primary"):
    st.session_state.race_history.append(current_race_data)
    st.success(f"第 {len(st.session_state.race_history)} 場數據已儲存！")
    st.rerun()

st.divider()

# 2. 累計數據計算
if st.session_state.race_history:
    total_styles = {"領放": 0, "中段": 0, "後追": 0}
    total_draws = {"內欄": 0, "二疊": 0, "外檔": 0}

    # 遍歷歷史場次計算總分
    for race in st.session_state.race_history:
        for entry in race:
            total_styles[entry['style']] += entry['score']
            total_draws[entry['draw']] += entry['score']

    # 轉為 DataFrame 方便顯示
    df_style = pd.DataFrame(list(total_styles.items()), columns=['跑法', '累積得分']).sort_values(by='累積得分', ascending=False)
    df_draw = pd.DataFrame(list(total_draws.items()), columns=['檔位', '累積得分']).sort_values(by='累積得分', ascending=False)

    # 3. 顯示結果圖表
    col_res1, col_res2 = st.columns(2)

    with col_res1:
        st.subheader("🏃 累積跑法趨勢")
        st.bar_chart(df_style.set_index('跑法'))
        st.table(df_style)

    with col_res2:
        st.subheader("🚧 累積檔位趨勢")
        st.bar_chart(df_draw.set_index('檔位'))
        st.table(df_draw)

    # 4. 綜合建議
    top_style = df_style.iloc[0]['跑法']
    top_draw = df_draw.iloc[0]['檔位']
    
    st.info(f"💡 **根據 {len(st.session_state.race_history)} 場數據分析：**")
    st.markdown(f"目前賽道對 **{top_style}** 跑法與 **{top_draw}** 檔位的馬匹最為有利。")

    # 顯示原始數據紀錄（選用）
    with st.expander("查看原始數據紀錄"):
        st.write(st.session_state.race_history)
else:
    st.info("請輸入第一場比賽數據並點擊儲存，開始分析趨勢。")
