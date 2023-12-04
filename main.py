import openai
import streamlit as st
import time
from PIL import Image
import base64
import os
import requests
from streamlit_lottie import st_lottie



# Inicializace
openai.api_key = st.secrets["API_KEY"]
assistant_id = st.secrets["ASSISTANT_ID"]

client = openai
def initialize_session():
    """Inicializuje session state pro Streamlit aplikaci a automaticky spouští chat."""
    if "start_chat" not in st.session_state:
        st.session_state.start_chat = True
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
        st.session_state.messages = []

    if "initial_message_sent" not in st.session_state:
        # Kontrola, zda už nebyla úvodní zpráva přidána
        if not any(message["content"] == "Ahoj, pojďme si zahát!" for message in st.session_state.messages):
            send_initial_message()
            st.session_state.initial_message_sent = True



def send_initial_message():
    """Odesílá počáteční zprávu do chatu."""
    initial_message = "Ahoj, pojďme si zahát!"
    st.session_state.messages = [{"role": "assistant", "content": initial_message}]
    send_message_to_openai(initial_message)




def exit_chat():
    """Ukončí chatovací session a vymaže historii chatu."""
    if st.button("Exit Chat"):
        st.session_state.messages = []  # Clear the chat history
        st.session_state.thread_id = None

# def handle_chat():
#     """Zpracovává logiku chatu, včetně zobrazování zpráv a zpracování uživatelských vstupů."""
#     # Zobrazit existující zprávy
#     display_messages()

#     # Zpracovat nový uživatelský vstup
#     user_input = st.text_input("Zadejte váš dotaz:", key="user_input")

#     if user_input:
#         send_message_to_openai(user_input)

        
    # display_messages()
    process_user_input()

def display_messages():
    """Zobrazuje zprávy v chatovacím rozhraní."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def process_user_input():
    """Zpracovává uživatelský vstup a odesílá jej do OpenAI."""
    prompt = st.chat_input("...")
    if prompt:
        st.write("Já :-):", prompt)

        send_message_to_openai(prompt)

def send_message_to_openai(prompt):
    """
    Odesílá uživatelskou zprávu do OpenAI a zpracovává odpověď.
    
    Args:
        prompt (str): Text zprávy odeslané uživatelem.
    """
    start_time = time.time()  # Začátek měření času

    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt
    )
    
    # Vytvoření a spuštění dotazu pro OpenAI
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=assistant_id,
    )

    # Čekání na dokončení dotazu
    while run.status != 'completed':
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id,
            run_id=run.id
        )

    end_time = time.time()  # Konec měření času
    response_time = end_time - start_time  # Výpočet doby odezvy
    st.write(f"Doba odezvy: {response_time:.2f} sekund")  # Zobrazení doby odezvy

    # Čekání na dokončení dotazu
    while run.status != 'completed':
        time.sleep(0.05)
        run = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id,
            run_id=run.id
        )

    # Získání všech zpráv z vlákna
    messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread_id
    )

    # Zpracování a zobrazení odpovědí asistenta
    assistant_messages_for_run = [
        message for message in messages 
        if message.run_id == run.id and message.role == "assistant"
    ]
    for message in assistant_messages_for_run:
        st.session_state.messages.append({"role": "assistant", "content": message.content[0].text.value})
        with st.chat_message("assistant"):
            st.markdown(message.content[0].text.value)
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"Chyba při načítání Lottie URL: {e}")
    except requests.exceptions.RequestException as e:
        st.error(f"Chyba požadavku: {e}")
    return None

# Nastavení Streamlit
st.set_page_config(page_title="Hádej, kdo jsem?", page_icon=":speech_balloon:")
st.title("Hádej, kdo jsem?")

current_directory = os.path.dirname(os.path.abspath(__file__))
img_path = os.path.join(current_directory, 'img1.png')
st.image(img_path, caption='', use_column_width=True)

# Načtení Lottie animace z URL
lottie_url = "https://lottie.host/ae43b28d-b082-4249-bc22-144e1ceed7f7/ebUqhkyptl.json"
lottie_json = load_lottieurl(lottie_url)

if lottie_json and ("lottie_loaded" not in st.session_state or not st.session_state.lottie_loaded):
    # Zobrazení Lottie animace s popiskem
    st_lottie(lottie_json, key="loading", height=200, width=200)
    st.text("Načítám hru...")
    st.session_state.lottie_loaded = True

model_choice = st.sidebar.selectbox(
    'Vyberte model:',
    ('gpt-4-1106-preview', 'gpt-3.5-turbo-16k'),
    index=1
)

initialize_session()
exit_chat()
