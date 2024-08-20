# ========== Python 环境准备 ========== #

import streamlit as st
import base64
import requests
import utilities
import implementation
import psycopg2
import json
from implementation import save_conversation_log
import psycopg2
import urllib.parse

# 数据库连接函数
def connect_db():
    return psycopg2.connect(
        dbname="ai_therapist",
        user="postgres",
        password="1996310ljkb",
        host="8.tcp.cpolar.cn",
        port="10580"
    ) 
agent_implementation = implementation.AgentImplementation()
# ========== 页面设置 ========== #

# 设置页面标题
st.set_page_config(page_title="AI 咨询师", layout="wide")
# 将标题放置在页面顶端
st.markdown("<h1 style='text-align: center; font-size: 42px;color:#F5F5F5'>🤖 AI 咨询师</h1>", unsafe_allow_html=True)

# 更改对话框背景
def main_bg(main_bg):
    main_bg_ext = "png"
    st.markdown(
        f"""
         <style>
         .stApp {{
             background: url(data:image/{main_bg_ext};base64,{base64.b64encode(open(main_bg, "rb").read()).decode()});
             background-size: cover;
             background-position: center; /* 调整背景图片位置 */
         }}
         </style>
         """,
        unsafe_allow_html=True
    )

# 调用背景图片函数
main_bg('main.png')

# 更改侧边栏样式
def sidebar_bg(side_bg):
   side_bg_ext = 'png'
   st.markdown(
      f"""
      <style>
      [data-testid="stSidebar"] > div:first-child {{
          background: url(data:image/{side_bg_ext};base64,{base64.b64encode(open(side_bg, "rb").read()).decode()});
      }}
      </style>
      """,
      unsafe_allow_html=True,
   )

# 调用侧边栏背景图片函数
sidebar_bg('side.png')

# 在侧边栏添加不同的机器人栏
st.sidebar.header("")

st.markdown(
    """
    <style>
    .sidebar .sidebar-content {
        background-color: #f0f0f0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 添加HTML/CSS样式
st.markdown(
    """
    <style>
    .right-align-button {
        position: fixed;
        top: 50px; /* 将按钮向下移动到50px处 */
        right: 10px;
        z-index: 9999;
    }
    .right-align-button button {
        background-color: #77AABF; /* 按钮背景颜色 */
        color: white; /* 按钮文字颜色 */
        padding: 10px 20px; /* 按钮内边距 */
        font-size: 16px; /* 按钮字体大小 */
        border: none; /* 去掉按钮边框 */
        border-radius: 8px; /* 按钮圆角 */
        cursor: pointer; /* 鼠标移上去时显示小手标志 */
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1); /* 按钮阴影 */
    }
    .right-align-button button:hover {
        background-color: #45a049; /* 鼠标悬停时的背景颜色 */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ========== 功能实现 ========== #

# ========== 函数 ========== #
# 获取对话历史
def get_conversation_history(username):
    conn = psycopg2.connect(
        dbname="ai_therapist",
        user="postgres",
        password="1996310ljkb",
        host="8.tcp.cpolar.cn",
        port="10580"
    )
    cur = conn.cursor()

    query = """
    SELECT conversation_history_client, conversation_history 
    FROM therapist_conversation_logs 
    WHERE username = %s 
    ORDER BY id ASC;
    """
    cur.execute(query, (username,))
    result = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return result

# 检查用户名是否存在
def check_username_exists(username):
    conn = psycopg2.connect(
        dbname="ai_therapist",
        user="postgres",
        password="1996310ljkb",
        host="8.tcp.cpolar.cn",
        port="10580"
    )
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM therapist_conversation_logs WHERE username = %s", (username,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

# 分割对话历史
def split_conversation_history(conversation_history):
    split_history = []
    for client_bot_tuple in conversation_history:
        # 处理 conversation_history_client 字段
        client_history = client_bot_tuple[0].strip().split("\n")
        for line in client_history:
            if ": " in line:
                role, content = line.split(": ", 1)
                split_history.append({"role": role, "content": content})

    return split_history

# 将对话历史转换为字符串的函数
def conversation_history_to_string(conversation_history):
    conversation_str = ""
    for entry in conversation_history:
        role = entry["role"]
        content = entry["content"]
        conversation_str += f"{role}: {content}\n"
    return conversation_str


# 定义发送消息函数
def send_message():
    user_input = st.session_state['user_input']
    conversation_history = st.session_state["conversation_history"]
    conversation_history_client = st.session_state["conversation_history_client"]
    
    if user_input:
        with st.spinner("生成回复..."):
            # 添加用户输入到对话历史
            conversation_history.append({"role": "client", "content": user_input})
            print(conversation_history,"1")
            print("------------------------------------------")

            conversation_history_client.append({"role": "client", "content": user_input})
            print(conversation_history_client)
            print("------------------------------------------")
            # conversation_history.append(split_history)

            # 将对话历史限制为最近10次交互内容
            # conversation_history = conversation_history
            # conversation_history_client = conversation_history_client           
            # conversation_history = conversation_history[-10:]
            # conversation_history_client = conversation_history_client[-10:]

            # 将对话历史更新回 session_state
            st.session_state["conversation_history"] = conversation_history
            st.session_state["conversation_history_client"] = conversation_history_client

            # 生成并添加机器人回复
            conversation_history_string = conversation_history_to_string(conversation_history)
            conversation_history_client_string = conversation_history_to_string(conversation_history_client)
            
            stage_history_string = map(str, st.session_state["stage_history"])
            stage_history = ''.join(stage_history_string)

            # 再次将对话历史限制为最近10次交互内容
            last_history = conversation_history_client[-10:]
            st.session_state["last_history"] = last_history
            last_history_string = conversation_history_to_string(last_history)
            response, current_stage_number = agent_implementation.generate_conversation(username, user_input, conversation_history_client_string, conversation_history_string, stage_history, last_history_string)

            conversation_history.append({"role": "therapist", "content": response})
            print(conversation_history,"append")

            # 更新阶段历史
            st.session_state["stage_history"].append(current_stage_number)

        # 保存对话历史
        file_name = f"{username}_conversation_history.txt"
        save_conversation_to_file(file_name, conversation_history)
        
        # 清空输入框
        del st.session_state['user_input']
        st.session_state['user_input'] = ''
        st.experimental_rerun()

# 保存对话历史到本地文件
def save_conversation_to_file(filename, conversation_history):
    selected_case = st.session_state.get("selected_case", {"Case Number": "未选择"})
    with open(filename, 'w', encoding='utf-8') as f:  # 使用 'w' 模式以覆盖内容
        f.write(f"案例编号: {selected_case['Case Number']}\n")
        for chat in conversation_history:
            f.write(f"{chat['role']}: {chat['content']}\n")


# ========== 逻辑段落 ========== #


# Streamlit UI

if "conversation_history_client" not in st.session_state:
    st.session_state["conversation_history_client"] = []
 
if "conversation_history" not in st.session_state:
    st.session_state["conversation_history"] = []

if "stage_history" not in st.session_state:
    st.session_state["stage_history"] = []

if "last_history" not in st.session_state:
    st.session_state["last_history"] = []

# 在Streamlit应用中生成聊天历史记录字符串
conversation_str = conversation_history_to_string(st.session_state["conversation_history"])
# URL encode the conversation string to make it safe for URLs
conversation_str_encoded = urllib.parse.quote(conversation_str)

# 检查是否已经输入用户名
if 'username' not in st.session_state:
    with st.form(key='user_form'):
        col1, col2 = st.columns([0.8, 0.2])  # 设置列布局，分配输入框和按钮的宽度

        with col1:
            username_input = st.text_input("输入您的用户名", key="username_input", placeholder="用户名",)

        with col2:
            st.markdown(
            """
            <style>
            div.stButton > button {
                height: 2.5em; /* 调整高度 */
                width: 50%; /* 设置宽度为100% */
                margin-top: 0.7em; /* 调整垂直对齐 */
                padding: 0; /* 移除内边距 */
            }
            </style>
            """,
                unsafe_allow_html=True
            )
            # 表单的提交按钮
            submit_button = st.form_submit_button(label='提交')

    # 表单提交后，检查用户名是否已输入
    if submit_button:
        if username_input:
            st.session_state.username = username_input
            username = st.session_state.username
            st.rerun()  # 重新运行脚本，更新界面
        else:
            st.error("用户名不能为空")
else:
    # 使用输入的用户名
    username = st.session_state.username
    st.write(f"{st.session_state.username}已进入聊天室")
    if username:
        if check_username_exists(username):
            # 如果用户名存在，获取对话历史
            conversation_history_data = get_conversation_history(username)
            # 分割历史并存入会话状态
            st.session_state["conversation_history_client"] = split_conversation_history(conversation_history_data)
            conversation_history_client = st.session_state["conversation_history_client"]
        else:
            # 用户名不存在，初始化欢迎消息
            welcome_message = "您好，欢迎你的到来，让我们开始今天的心理咨询"
            st.session_state["conversation_history"] = [{"role": "therapist", "content": welcome_message}]

    # 设置对话框样式并显示对话内容
    for chat in st.session_state["conversation_history"]:
        if chat["role"] == "client":
            st.markdown(
                f"""
                <div style='text-align: right; margin-bottom: 20px;'>
                    <div style='font-size: 16px; color: #808080 ;'>👨‍⚕️ 来访者</div>
                    <div style='display: inline-block; background-color:#E0FFFF; padding: 10px; border-radius: 10px; font-size: 20px; margin-top: 5px; color: black;'>{chat['content']}</div>
                </div>
                """, 
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div style='text-align: left; margin-bottom: 20px;'>
                    <div style='font-size: 16px; color:#808080 ;'>🧑 咨询师</div>
                    <div style='display: inline-block; background-color: #FFFFFF; padding: 10px; border-radius: 10px; font-size: 20px; margin-top: 5px; color: black;'>{chat['content']}</div>
                </div>
                """, 
                unsafe_allow_html=True
            )

# 发送按钮，并在发送消息后保存历史记录
    with st.form(key="user_input_form", clear_on_submit=True):
        col3, col4 = st.columns([0.8, 0.2])
        
        # 用户输入框
        with col3:
            user_input = st.text_input(
                "开始你的对话吧:", 
                key="user_input", 
                placeholder="输入消息并按Enter发送"
            )
        
        # 发送按钮，并在发送消息后保存历史记录
        with col4:
            st.markdown(
                """
                <style>
                div.stButton > button {
                    height: 2.5em; /* 调整高度 */
                    width: 50%; /* 设置宽度为100% */
                    margin-top: 0.7em; /* 调整垂直对齐 */
                    padding: 0; /* 移除内边距 */
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            submit_button = st.form_submit_button(label="发送", on_click=send_message)

    # 在页面右上角放置下载按钮
    st.markdown(
        f"""
        <div class="right-align-button">
            <a href="data:text/plain;charset=utf-8,{conversation_str_encoded}" download="{username}_conversation_history.txt">
                <button>📥下载聊天历史</button>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )
# 设置对话框样式并显示对话内容


# ========== 开启新的对话 ========== #





