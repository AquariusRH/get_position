import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 設定頁面
st.set_page_config(page_title="賽馬座標偏差分析器", layout="wide")

# 1. 初始化數據紀錄
if 'race_history' not in st.session_state:
    st.session_state.race_history = []

st.title("🐎 賽馬座標偏差分析 (官方走位圖邏輯版)")

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
    st.info("💡 **座標映射說明：**\n- **X 軸:** 右(0) = 領放 / 左(10) = 後追\n- **Y 軸:** 下(0) = 內欄 / 上(10) = 外疊")

# --- 2. 數據輸入區 ---
st.header(f"📝 輸入第 {current_race_num} 場結果")

# 保留連結
st.markdown(f"🔗 [點此開啟馬會走位圖網頁 (第 {current_race_num} 場參考)](https://racing.hkjc.com/racing/speedpro/chinese/formguide/formguide.html)")

rank_scores = {"第一名": 4, "第二名": 3, "第三名": 2, "第四名": 1}
current_input = []

# 輸入介面
tabs = st.tabs(list(rank_scores.keys()))

for i, (rank_name, score) in enumerate(rank_scores.items()):
    with tabs[i]:
        st.write(f"請根據走位圖位置標記 **{rank_name}**：")
        col_x, col_y = st.columns(2)
        with col_x:
            # 符合走位圖：數值越小越靠右(領放)
            pos_x = st.slider(f"水平位置 (0:最右/領放 ←→ 10:最左/後追)", 0.0, 10.0, 5.0, step=0.5, key=f"x_{current_race_num}_{i}")
        with col_y:
            # 數值越小越靠下(內欄)
            pos_y = st.slider(f"垂直位置 (0:最下/內欄 ←→ 10:最上/外疊)", 0.0, 10.0, 1.0, step=0.5, key=f"y_{current_race_num}_{i}")
        
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
    
    # 指數加權計算 (以場次為底)
    df['加權得分'] = df['原始分數'] * (1.1 ** df['場次'])

    # 繪製圖表
    fig = go.Figure()

    # 歷史數據點
    fig.add_trace(go.Scatter(
        x=df['X'], y=df['Y'],
        mode='markers+text',
        marker=dict(
            size=df['加權得分'] * 10,
            color=df['加權得分'],
            colorscale='YlOrRd',
            showscale=True,
            line=dict(width=1, color='white')
        ),
        text=df['場次'].astype(str),
        textposition="middle center",
        name="獲獎位置"
    ))

    # 計算加權中心 (最佳範圍)
    avg_x = (df['X'] * df['加權得分']).sum() / df['加權得分'].sum()
    avg_y = (df['Y'] * df['加權得分']).sum() / df['加權得分'].sum()

    # 繪製建議範圍 (綠色光圈)
    fig.add_shape(type="circle",
        xref="x", yref="y",
        x0=avg_x-1.2, y0=avg_y-1.2, x1=avg_x+1.2, y1=avg_y+1.2,
        fillcolor="rgba(0, 255, 0, 0.25)",
        line=dict(color="Lime", width=2),
    )

    fig.update_layout(
        title="🏃 賽道偏差熱力圖 (方向：→ 右方為終點)",
        xaxis=dict(
            title="← 後追 (左) | 領放 (右) →", 
            range=[10.5, -0.5], # 反轉 X 軸，讓 0 在右邊
            gridcolor='rgba(255,255,255,0.1)'
        ),
        yaxis=dict(
            title="內欄 (下) ↑ 外疊 (上)", 
            range=[-0.5, 10.5], 
            gridcolor='rgba(255,255,255,0.1)'
        ),
        height=600,
        template="plotly_dark",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- 4. 結果分析 ---
    res_l, res_r = st.columns([1, 2])
    with res_l:
        st.subheader("🎯 趨勢總結")
        
        # 根據座標給予文字建議
        horz = "前領/貼欄" if avg_x < 3 else ("中游" if avg_x < 7 else "後放/外疊")
        st.metric("當前跑法重心", horz)
        
        st.success(f"建議鎖定：X={avg_x:.1f} (橫向), Y={avg_y:.1f} (縱向) 附近的馬匹。")

    with res_r:
        st.subheader("📋 數據修訂 (可點擊修改內容)")
        edited_df = st.data_editor(df[['場次', '名次', 'X', 'Y', '加權得分']], num_rows="fixed")

else:
    st.info("💡 請對照上方走位圖，將前四名馬匹的位置標註在座標軸上。")
