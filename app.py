import streamlit as st
import os
import time
import json
import telebot
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from pypdf import PdfReader

# Set up Telegram Bot
recipient_user_id = os.environ['RECIPIENT_USER_ID']
bot_token = os.environ['BOT_TOKEN']
bot = telebot.TeleBot(bot_token)

# Retrieve the API keys from the environment variables
CLAUDE_API_KEY = os.environ["ANTHROPIC_API_KEY"]

anthropic = Anthropic(api_key=CLAUDE_API_KEY)

file = open('quizgen.txt','r')
prompt = file.read()
file.close()

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
      input_text = prompt + "<SOURCE>\n\n" + raw_text + "</SOURCE>\n\n"
    
      message = anthropic.messages.create(
        model = "claude-3-opus-20240229",
        max_tokens = 4096,
        temperature = 0,
        system = "",
        messages = [
          {  
            "role": "user",
            "content": input_text
          },
          {
            "role": "assistant",
            "content": "["
          }
        ]
      )
      output_text = "[" + message.content[0].text
      end = time.time()

      quiz = json.loads(output_text)
      print(quiz)
      
      container = st.container(border=True)
      container.write(output_text)
      container.write("Time to generate: " + str(round(end-start,2)) + " seconds")
      bot.send_message(chat_id=recipient_user_id, text="QuizGen")
      st.download_button(':floppy_disk:', output_text)
  except:
    st.error(" Error occurred when running model", icon="🚨")
