import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# 設定頁面
st.set_page_config(page_title="賽馬空間偏差分析器", layout="wide")

# 1. 初始化數據紀錄
if 'race_history' not in st.session_state:
    st.session_state.race_history = []

st.title("🐎 賽馬座標偏差分析 (空間加權法)")

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
        if st.button("🔙 刪除最後一場 (4行)"):
            st.session_state.race_history = st.session_state.race_history[:-4]
            st.rerun()
    
    st.divider()
    st.info("💡 **座標說明：**\n- **X 軸 (跑法):** 0=領放, 5=中置, 10=後追\n- **Y 軸 (檔位):** 0=內欄, 5=二疊, 10=大外檔")

# --- 2. 數據輸入區 ---
st.header(f"📝 輸入第 {current_race_num} 場結果")

# 保留原本的連結功能
st.markdown(f"🔗 [點此開啟馬會走位圖網頁 (第 {current_race_num} 場參考)](https://racing.hkjc.com/racing/speedpro/chinese/formguide/formguide.html)")

rank_scores = {"第一名": 4, "第二名": 3, "第三名": 2, "第四名": 1}
current_input = []

# 使用 Tabs 來切換名次，保持介面整潔
tabs = st.tabs(list(rank_scores.keys()))

for i, (rank_name, score) in enumerate(rank_scores.items()):
    with tabs[i]:
        col_a, col_b = st.columns(2)
        with col_a:
            # 讓用戶透過 Slider 模擬點選座標
            pos_x = st.slider(f"{rank_name} 跑法 (左:領放 <-> 右:後追)", 0.0, 10.0, 5.0, step=0.5, key=f"x_{current_race_num}_{i}")
        with col_b:
            pos_y = st.slider(f"{rank_name} 檔位 (下:內欄 <-> 上:外檔)", 0.0, 10.0, 1.0, step=0.5, key=f"y_{current_race_num}_{i}")
        
        current_input.append({
            "場次": current_race_num,
            "名次": rank_name,
            "原始分數": score,
            "X": pos_x,
            "Y": pos_y
        })

if st.button("💾 儲存此場座標數據", type="primary", use_container_width=True):
    st.session_state.race_history.extend(current_input)
    st.rerun()

st.divider()

# --- 3. 數據處理與視覺化 ---
if st.session_state.race_history:
    df = pd.DataFrame(st.session_state.race_history)
    
    # 指數權重計算
    df['加權得分'] = df['原始分數'] * (1.1 ** df['場次'])

    # 繪製座標圖
    fig = go.Figure()

    # 繪製所有歷史點位，球體大小代表權重
    fig.add_trace(go.Scatter(
        x=df['X'], y=df['Y'],
        mode='markers+text',
        marker=dict(
            size=df['加權得分'] * 8,
            color=df['加權得分'],
            colorscale='Hot',
            showscale=True,
            line=dict(width=1, color='White')
        ),
        text=df['場次'].astype(str) + "場",
        textposition="top center",
        name="獲獎位置"
    ))

    # 計算加權中心點（即最佳範圍中心）
    avg_x = (df['X'] * df['加權得分']).sum() / df['加權得分'].sum()
    avg_y = (df['Y'] * df['加權得分']).sum() / df['加權得分'].sum()

    # 繪製「最佳位置範圍」圈圈
    fig.add_shape(type="circle",
        xref="x", yref="y",
        x0=avg_x-1.5, y0=avg_y-1.5, x1=avg_x+1.5, y1=avg_y+1.5,
        fillcolor="rgba(0, 255, 0, 0.2)",
        line_color="Lime",
        name="預測黃金地帶"
    )

    fig.update_layout(
        title=f"賽道偏差空間分布 (第 1-{current_race_num-1} 場累積)",
        xaxis=dict(title="跑法 (0:領放 ←→ 10:後追)", range=[-1, 11], gridcolor='gray'),
        yaxis=dict(title="檔位 (0:內欄 ←→ 10:外檔)", range=[-1, 11], gridcolor='gray', autorange="reversed"),
        height=600,
        template="plotly_dark",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- 4. 戰略建議與數據表 ---
    col_res1, col_res2 = st.columns([1, 2])
    
    with col_res1:
        st.subheader("🎯 核心偏差分析")
        
        # 定義描述文字
        def get_bias_desc(x, y):
            x_desc = "前方領放" if x < 3.5 else ("中游推進" if x < 7 else "大後方衝刺")
            y_desc = "貼欄省腳程" if y < 3.5 else ("二、三疊望空" if y < 7 else "外疊大包抄")
            return x_desc, y_desc

        x_txt, y_txt = get_bias_desc(avg_x, avg_y)
        
        st.success(f"**建議跑法：** {x_txt}")
        st.success(f"**建議取線：** {y_txt}")
        st.info(f"中心座標：X={avg_x:.2f}, Y={avg_y:.2f}")

    with col_res2:
        st.subheader("📋 原始紀錄清單")
        st.dataframe(df[['場次', '名次', 'X', 'Y', '加權得分']].sort_values(by='加權得分', ascending=False), hide_index=True)

else:
    st.info("👋 歡迎！請參考馬會走位圖後，在上方標記前四名的位置座標。")
