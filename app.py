import streamlit as st
import os
import time
import telebot
from pydantic import BaseModel
from openai import OpenAI
from pypdf import PdfReader
from st_copy_to_clipboard import st_copy_to_clipboard

# Set up Telegram Bot
recipient_user_id = os.environ['RECIPIENT_USER_ID']
bot_token = os.environ['BOT_TOKEN']
bot = telebot.TeleBot(bot_token)

# Retrieve the API keys from the environment variables
CLIENT_API_KEY = os.environ['OPENAI_API_KEY']
client = OpenAI(api_key=CLIENT_API_KEY)

class Answer(BaseModel):
    label: str
    answer: str

class Question(BaseModel):
    question: str
    answers: list[Answer]
    correct_answer: str

class QuizResponse(BaseModel):
    questions: list[Question]

quiz_prompt = """You are tasked with creating a multiple-choice quiz based on the provided text:

Your goal is to create a quiz consisting of 10 high-quality questions that test understanding of the provided text. Each question in the quiz must adhere to the following format:

1. A clear and concise question.
2. Four answer options, labeled A, B, C, and D.
3. One correct answer clearly identified for each question.

When creating the quiz, follow these guidelines:

1. Ensure that the questions cover important information from various parts of the text.
2. Make the questions challenging but fair, focusing on key concepts rather than minor details.
3. Create plausible incorrect answer choices that might tempt a quiz taker who doesn't fully understand the material.
4. Vary the types of questions (e.g., factual recall, concept application, cause-and-effect relationships) to test different aspects of understanding.

Format your output as follows:

Q1: [Insert question here]
A. [Option A]
B. [Option B]
C. [Option C]
D. [Option D]
Correct Answer: [Insert correct answer letter]

Q2: [Insert question here]
A. [Option A]
B. [Option B]
C. [Option C]
D. [Option D]
Correct Answer: [Insert correct answer letter]

[Continue this format for all 10 questions]

Now, carefully read through the provided text and create 10 multiple-choice questions based on its content. Ensure that your questions and answer choices are clear, concise, and directly related to the information in the text."""

st.set_page_config(page_title="Quiz Generator", page_icon=":sunglasses:",)
st.write("**Quiz Generator**")

uploaded_file = st.file_uploader("Upload a PDF to generate a quiz:", type = "pdf")
raw_text = ""
if uploaded_file is not None:
  doc_reader = PdfReader(uploaded_file)
  for i, page in enumerate(doc_reader.pages):
    text = page.extract_text()
    if text:
      raw_text = raw_text + text + "\n"

  try:
    with st.spinner("Running AI Model..."):
      start = time.time()
      completion = client.beta.chat.completions.parse(model="gpt-4o-2024-08-06",
                                                      messages=[{"role": "system", "content": quiz_prompt},
                                                                {"role": "user", "content": raw_text}],
                                                      response_format=QuizResponse, temperature = 0)
      message = completion.choices[0].message

      TotalQuizOutput = ""
      index = 1
      for q in message.parsed.questions:
          QuizOutput = "**Question " + str(index) + ": " + q.question + "**  \n"
          for a in q.answers:
            QuizOutput = QuizOutput + a.label + ". " + a.answer + "  \n"
          st.markdown(QuizOutput)
          ca = "**Correct Answer: " + q.correct_answer + "**"
          with st.expander("Click for Correct Answer to Question " + str(index)):
              st.markdown(ca)
          QuizOutput = QuizOutput + ca
          index = index + 1
          TotalQuizOutput = TotalQuizOutput + "<Question>\n" + QuizOutput + "\n</Question>\n\n" 
      end = time.time()
      
      st.balloons()
      st.write("Time to generate: " + str(round(end-start,2)) + " seconds")

      start = time.time()
      completion_check = client.chat.completions.create(model="gpt-4o",
                                                            messages=[{"role": "system", "content": "Check the accuracy of the questions in the <Question> tags against the input text contained in the <input_text> tags. Start your answer by providing a percentage score of the accuracy, where 100% means total accuracy."},
                                                                      {"role": "user", "content": TotalQuizOutput + "<input_text>\n" + raw_text + "\n</input_text>"}], temperature = 0)
      check_message = completion_check.choices[0].message.content
      with st.expander("Click to review the accuracy of the quiz"):
          st.write(check_message)
      end = time.time()
      
      st.snow()  
      st.write("Time to generate: " + str(round(end-start,2)) + " seconds")
        
      #container = st.container(border=True)
      #container.write(QuizOutput)
      #container.write("Time to generate: " + str(round(end-start,2)) + " seconds")
      bot.send_message(chat_id=recipient_user_id, text="QuizGen")
      st_copy_to_clipboard(TotalQuizOutput)
  except:
    st.error(" Error occurred when running model", icon="🚨")
