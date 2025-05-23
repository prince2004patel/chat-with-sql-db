import streamlit as st
from pathlib import Path
import os
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from sqlalchemy import create_engine
import sqlite3
from langchain_groq import ChatGroq
from urllib.parse import quote_plus

st.set_page_config(page_title="LangChain: Chat with SQL DB", page_icon="🦜")
st.title("🦜 LangChain: Chat with SQL DB")

# Constants for database types
SQLITE = "USE_SQLITE"
MYSQL = "USE_MYSQL"

# Database choice options
radio_opt = ["Use SQLite Database from Local System", "Connect to MySQL Database"]
selected_opt = st.sidebar.radio(label="Choose the DB which you want to chat with", options=radio_opt)

# Database configuration based on selection
if radio_opt.index(selected_opt) == 0:
    db_uri = SQLITE
    # Allow user to upload a SQLite file or input a path
    db_selection_method = st.sidebar.radio(
        "How would you like to select your SQLite database?",
        ["Upload a SQLite file", "Provide path to SQLite file"]
    )
    
    if db_selection_method == "Upload a SQLite file":
        uploaded_file = st.sidebar.file_uploader("Upload SQLite Database", type=["db", "sqlite", "sqlite3"])
        if uploaded_file is not None:
            # Save the uploaded file to a temporary location
            with open("temp_db.sqlite", "wb") as f:
                f.write(uploaded_file.getbuffer())
            db_path = "temp_db.sqlite"
        else:
            db_path = None
    else:
        db_path = st.sidebar.text_input("Enter path to SQLite database file")
        if db_path and not os.path.exists(db_path):
            st.sidebar.error(f"File not found: {db_path}")
            db_path = None
        
else:  # MySQL option
    db_uri = MYSQL
    mysql_host = st.sidebar.text_input("Provide MySQL Host")
    mysql_user = st.sidebar.text_input("MySQL User")
    mysql_password = st.sidebar.text_input("MySQL password", type="password")
    mysql_db = st.sidebar.text_input("MySQL database")

# API key input
api_key = st.sidebar.text_input(label="Groq API Key", type="password")

# Show information messages if needed
if radio_opt.index(selected_opt) == 0 and not db_path:
    st.info("Please select or provide the path to your SQLite database")
elif radio_opt.index(selected_opt) == 1 and not (db_uri and mysql_host and mysql_user and mysql_password and mysql_db):
    st.info("Please enter all required MySQL connection details")

if not api_key:
    st.info("Please add your Groq API key")

# LLM model initialization
if api_key:
    llm = ChatGroq(groq_api_key=api_key, model_name="Llama3-8b-8192", streaming=True)

@st.cache_resource(ttl="2h")
def configure_db(db_uri, db_path=None, mysql_host=None, mysql_user=None, mysql_password=None, mysql_db=None):
    if db_uri == SQLITE:
        if not db_path:
            st.error("Please provide a valid SQLite database file")
            st.stop()
        
        db_path = Path(db_path).absolute()
        st.sidebar.success(f"Connected to SQLite database: {db_path}")
        
        # Create a connection to the SQLite database
        creator = lambda: sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        return SQLDatabase(create_engine("sqlite:///", creator=creator))
    
    elif db_uri == MYSQL:
        if not (mysql_host and mysql_user and mysql_password and mysql_db):
            st.error("Please provide all MySQL connection details")
            st.stop()
        
        encoded_password = quote_plus(mysql_password)
        db_url = f"mysql+mysqlconnector://{mysql_user}:{encoded_password}@{mysql_host}/{mysql_db}"
        st.sidebar.success(f"Connected to MySQL database: {mysql_db} at {mysql_host}")
        return SQLDatabase(create_engine(db_url))

# Initialize database connection
if api_key and ((db_uri == SQLITE and db_path) or (db_uri == MYSQL and mysql_host and mysql_user and mysql_password and mysql_db)):
    if db_uri == SQLITE:
        db = configure_db(db_uri, db_path=db_path)
    else:
        db = configure_db(db_uri, mysql_host=mysql_host, mysql_user=mysql_user, mysql_password=mysql_password, mysql_db=mysql_db)
    
    # Initialize toolkit and agent
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True
    )


    # Chat interface
    if "messages" not in st.session_state or st.sidebar.button("Clear message history"):
        st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    user_query = st.chat_input(placeholder="Ask anything from the database")
    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        st.chat_message("user").write(user_query)

        with st.chat_message("assistant"):
            streamlit_callback = StreamlitCallbackHandler(st.container())
            response = agent.run(user_query, callbacks=[streamlit_callback])
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.write(response)