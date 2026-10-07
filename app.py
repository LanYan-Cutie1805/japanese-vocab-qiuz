import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime
import streamlit.components.v1 as components

DB_FILE = "marionette_db.xlsx"
st.set_page_config(
    page_title="Japanese Vocab Quiz",
    page_icon="🇯🇵",
    layout="centered"
)
# Custom answer card style
st.markdown(
    """
    <style>
    .stButton>button {
        background-color: #f0f0f0;
        border: 1px solid #ccc;
        color: #333;
        font-size: 30 px;
    }
    .stButton>button:hover {
        background-color: #e0e0e0;
    }

    button[aria-label="Close"]{
        display : none;}
    </style>
    """,
    unsafe_allow_html=True
)

# Load the database
@st.cache_data
def load_database():
    df = pd.read_excel(DB_FILE)
    df = df.dropna(subset=["vocab", "hiragana", "meaning"])
    available_categories = df["category"].dropna().astype(str).unique().tolist()
    return df, available_categories

df, available_categories = load_database()

# Session state initialization
if "current_word" not in st.session_state:
    st.session_state.current_word = None
if "answers" not in st.session_state:
    st.session_state.answers = []
if "answered" not in st.session_state:
    st.session_state.answered = False
if "selected_answer" not in st.session_state:
    st.session_state.selected_answer = None
if "score" not in st.session_state:
    st.session_state.score = 0
if "question_number" not in st.session_state:
    st.session_state.question_number = 0
if "study_start_time" not in st.session_state:
    st.session_state.study_start_time = datetime.now()
if "study_end_time" not in st.session_state:
    st.session_state.study_end_time = None
if "remaining_words" not in st.session_state:
    st.session_state.remaining_words = set()
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
if "selected_category" not in st.session_state:
    st.session_state.selected_category = []
if "quiz_finished" not in st.session_state:
    st.session_state.quiz_finished = False
if "selected_level" not in st.session_state:
    st.session_state.selected_level =[]
if "level_dialog_open" not in st.session_state:
    st.session_state.level_dialog_open = False

@st.dialog("Quiz Setup")
def category_dialog():
    st.write("Select the categories you want to study:")
    selected = st.multiselect(
        "Categories",
        options=available_categories,
        label_visibility="collapsed"
    )
    st.write("")

    if st.button("Start Quiz", use_container_width=True, 
                 type="primary"):
        if len(selected) == 0:
            st.warning("Please select at least one category.")
        else:
        
            st.session_state.selected_category = selected
            st.session_state.quiz_started = True

            selected_df = df[df["category"].isin(selected)]
            st.session_state.remaining_words = set(selected_df["ID"].tolist())

            st.session_state.current_word = None
            st.session_state.answers = []
            st.session_state.answered = False
            st.session_state.selected_answer = None
            st.session_state.score = 0
            st.session_state.question_number = 0
            st.session_state.study_start_time = datetime.now()
            st.session_state.study_end_time = None
            st.session_state.quiz_finished = False
            st.rerun()

if not st.session_state.quiz_started:
    category_dialog()
    st.stop()

quiz_df = df[df["category"].isin(
    st.session_state.selected_category
)].copy()

# Check wether there are enough vocab words
if len(quiz_df) < 4:
    st.warning(
        "Not enough vocab words in the selected categories. "
        "Please select more categories."
    )
    st.stop()

@st.dialog("Level Setup")
def level_dialog():
    st.write("Select the level:")
    selected = st.radio(
        "JLPT Level",["N5", "N4"],
        index=None,
        label_visibility="collapsed"
    )
    if st.button(
        "Apply Level",
        use_container_width=True,
        type="primary",
    ):
        if selected is None:
            st.warning("Please select a level")
        else:
            st.session_state.selected_level = selected
            st.rerun()

# Create new question
def create_question():
    if st.session_state.quiz_finished:
        return

    if len(st.session_state.remaining_words) == 0:
        st.session_state.quiz_finished = True
        st.session_state.study_end_time = datetime.now()
        return

    available_words = quiz_df[
        quiz_df["ID"].isin(st.session_state.remaining_words)]
    word = available_words.sample(1).iloc[0]

    correct_answer = str(word["meaning"])

    other_words = quiz_df[quiz_df["ID"] != word["ID"]]

    possible_wrong_answers = (
        other_words["meaning"]
        .dropna()
        .astype(str)
        .drop_duplicates()
    )

    wrong_answers = (possible_wrong_answers.sample(3)
                     .tolist())

    answers = wrong_answers + [correct_answer]

    random.shuffle(answers)

    st.session_state.current_word = word
    st.session_state.answers = answers
    st.session_state.answered = False
    st.session_state.selected_answer = None
    st.session_state.question_number += 1

# Initial question
if st.session_state.current_word is None:
    create_question()

if st.session_state.current_word is None:
    st.stop()

if st.session_state.quiz_finished:
    #st.success("🎉 Congratulations! You've completed the quiz.")
    total_words = len(quiz_df)
    accuracy = (
        st.session_state.score /
        st.session_state.question_number * 100
        if st.session_state.question_number > 0 else 0
    )

    study_duration = (
        st.session_state.study_end_time - st.session_state.study_start_time
    )

    total_seconds = int(study_duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"

    st.header("📊 Quiz Results:")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Questions", st.session_state.question_number)
    with col2:
        st.metric("Accuracy", f"{accuracy:.1f}%")
    with col3:
        st.metric("Study Duration", formatted_time)
    if st.button(
    "🔄 Start New Quiz",
    use_container_width=True,
    type="primary"
):

        st.session_state.current_word = None
        st.session_state.answers = []
        st.session_state.answered = False
        st.session_state.selected_answer = None

        st.session_state.score = 0
        st.session_state.question_number = 0

        st.session_state.study_start_time = datetime.now()
        st.session_state.study_end_time = None

        st.session_state.remaining_words = set()

        st.session_state.selected_category = []

        st.session_state.quiz_started = False
        st.session_state.quiz_finished = False

        st.rerun()

else:
    
    # Header
    st.title("字 Japanese Vocab Quiz")
    st.write("Welcome! Choose the correct meaning for each word.")
    #st.caption("Powered by marionette_db and Hyposelenia Repetitive Algorithm (HRA).")
    
    mastered = (len(quiz_df) - len(st.session_state.remaining_words)
                )
    current_question = min(
        mastered + 1, len(quiz_df)
    )

    st.caption(
        f"📝 Question :{current_question}/{len(quiz_df)}"
    )

    # Vocab display
    word = st.session_state.current_word
    st.markdown(
        f"""
        <div style="text-align: center; padding: 10px 1px;">
            <div style="font-size: 48px; font-weight: bold;">
                {word['vocab']}
            </div>
            <div style="font-size: 24px; 
            margin-top: 8px;
            display: inline-block;
            padding: 4px 8px;
            background-color: #1f5f8b;
            border-radius: 10px;
            color: #e8f4ff;
            font-weight: 500;">
                {word['hiragana']}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Answer buttons
    st.write("### Choose the correct meaning:")
    answers = st.session_state.answers

    for i in range (0, len(answers), 2):
        col1, col2 = st.columns(2)
        with col1:
            answer = answers[i]

            if st.button(
                answer,
                key=f"answer_{i}",
                use_container_width=True,
                disabled=st.session_state.answered
            ):
                st.session_state.selected_answer = answer
                st.session_state.answered = True

                st.rerun()

        with col2:
            answer = answers[i + 1]
            if st.button(
                answer,
                key=f"answer_{i + 1}",
                use_container_width=True,
                disabled=st.session_state.answered
            ):
                st.session_state.selected_answer = answer
                st.session_state.answered = True
                st.rerun()


    # Result
    if st.session_state.answered:
        correct_answer = str(word["meaning"])
        selected_answer = st.session_state.selected_answer

        if selected_answer == correct_answer:
            st.success("Correct! 🎉")
            st.session_state.remaining_words.discard(word["ID"])
            st.session_state.score += 1
            time.sleep(1)
        else:
            st.error(f"Incorrect! ❌ The correct answer is: {correct_answer}")
            time.sleep(1.5)  

        create_question()
        st.rerun()

# Sidebar
with st.sidebar:
    st.header("Stats")

    st.write(f"📚 Vocabulary: **{len(quiz_df)}**")

    if st.session_state.question_number > 0:
        accuracy = (st.session_state.score / st.session_state.question_number) * 100
        st.write(f"🎯 Accuracy: **{accuracy:.2f}%**")

    st.write(f"⏱️ Study Time")
    start_timestamp = (st.session_state.study_start_time.timestamp())

    if st.session_state.study_end_time is not None:
        end_timestamp = (
            st.session_state.study_end_time.timestamp())
    else:
        end_timestamp = None
        
    
    components.html(
        f"""
        <div style="
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        font-family: monospace;
        color: white;
        padding: 10px;
        ">
        <span id="timer">00:00:00</span>
        </div>

        <script>
        const startTime = {start_timestamp} * 1000; // Convert to milliseconds
        const endTime = {f"{end_timestamp} * 1000"
        if end_timestamp is not None
        else "null"
        };

        function updateTimer() {{
        const now = endTime !== null
            ? endTime
            : Date.now();
        const elapsed = Math.floor((now - startTime) / 1000);
        const hours = String(Math.floor(elapsed / 3600)).padStart(2, '0');
        const minutes = String(Math.floor((elapsed % 3600) / 60)).padStart(2, '0');
        const seconds = String(elapsed % 60).padStart(2, '0');

        const formattedTime = `${{hours}}:${{minutes}}:${{seconds}}`;
        document.getElementById('timer').textContent = formattedTime;
        }}
        updateTimer();
        if (endTime == null) {{
        setInterval(updateTimer, 1000);
        }}
        </script>
    

        """,
        height=55,
    )
    st.divider()

    if st.button("Reset Quiz", use_container_width=True):
        st.session_state.current_word = None
        st.session_state.answers = []
        st.session_state.answered = False
        st.session_state.selected_answer = None
        st.session_state.score = 0
        st.session_state.question_number = 0
        st.session_state.study_start_time = datetime.now()
        st.session_state.remaining_words = set()
        st.session_state.selected_category = []
        st.session_state.quiz_started = False
        st.session_state.quiz_finished = False
        st.rerun()