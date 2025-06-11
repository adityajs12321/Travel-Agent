import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import core.model as model
from core.model import IntelTravelModel

st.title("Intelligent Travel Agent")

client_id = os.environ['AMADEUS_CLIENT_ID']
client_secret = os.environ['AMADEUS_CLIENT_SECRET']
model.set_access_token(client_id, client_secret)

question = st.chat_input()

if (question):
    print(question)
    model_new = IntelTravelModel()
    response = model_new.trip_planning(1, question)
    assistant_message = st.chat_message("assistant").empty()
    assistant_message.write(response)
    