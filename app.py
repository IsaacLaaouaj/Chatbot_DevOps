import flet as ft
import os
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain_groq import ChatGroq
from joblib import load, dump
from mem0 import MemoryClient
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
mem0_client = MemoryClient(api_key="m0-e6ULRDch78DmYrlBXGYGD2dN5I8jfTwDaQXR74cK")
try:
    memory = load('memoriememories/fletoMemory.joblib')
    print(memory)
except:
    memory = ConversationBufferMemory()

groq_chat = ChatGroq(groq_api_key=os.environ['GROQ_API_KEY'], model_name="llama-3.3-70b-versatile", temperature=0.2)
conversation = ConversationChain(llm=groq_chat, memory=memory)

def get_relevant_context(query: str) -> str:
    try:
        context = ""
        if mem0_client:
            response = mem0_client.search(
                query, 
                user_id="user",
                rerank=True,
                filter_memories=True,
                limit=5
            )
            
            print("\nRetrieved memories with relevance:")
            if isinstance(response, dict) and 'results' in response:
        
                for i, x in enumerate(response['results']):
                    relevance = x.get('score', 'N/A')
                    memory_text = x.get('memory', '')
                    print(f"{i+1}. [Score: {relevance}] Memory: {memory_text}\n")
                    if relevance == 'N/A' or float(relevance) > 0.3:
                        context += memory_text + "\n"
            elif isinstance(response, list):
        
                for i, x in enumerate(response):
                    if isinstance(x, dict):
                        memory_text = x.get('memory', x.get('content', str(x)))
                    else:
                        memory_text = str(x)
                    print(f"{i+1}. Memory: {memory_text}\n")
                    context += memory_text + "\n"
            else:
        
                print(f"1. Memory: {response}\n")
                context = str(response) + "\n"
            return context
    except Exception as e:
        print(f"Error retrieving context from mem0: {e}")
        print(f"Response type: {type(response)}")
        print(f"Response content: {response}")
    return ""

def save_and_exit(page: ft.Page):
    try:
        dump(memory, 'memories/fletoMemory.joblib')
        print("Memory saved successfully!")
    except Exception as e:
        print(f"Error saving memory: {e}")
    page.window.close()

def main(page: ft.Page):
    page.title = "Fleto"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.spacing = 20

    chat_history = ft.ListView(
        expand=1,
        spacing=10,
        padding=20,
        height=400,
        auto_scroll=True
    )

    user_input = ft.TextField(
        label="Your message",
        multiline=True,
        min_lines=1,
        max_lines=5,
        expand=True
    )

    def send_message(e):
        if not user_input.value:
            return


        chat_history.controls.append(
            ft.Text(
                f"You: {user_input.value}",
                color=ft.colors.BLUE_400
            )
        )


        context = get_relevant_context(user_input.value)
        print(context)
        

        if context:
            prompt = f"Known context about the question:\n{context}\n\nCurrent question: {user_input.value}"
        else:
            prompt = user_input.value


        response = conversation(prompt)
        ai_message = response['response']


        chat_history.controls.append(
            ft.Text(
                f"AI: {ai_message}",
                color=ft.colors.WHITE70
            )
        )


        messages = [
            {"role": "user", "content": user_input.value},
            {"role": "assistant", "content": ai_message}
        ]
        mem0_client.add(messages, user_id="user")


        user_input.value = ""
        page.update()

    send_button = ft.ElevatedButton(
        "Send",
        on_click=send_message,
        icon=ft.icons.SEND
    )

    save_button = ft.ElevatedButton(
        "Save & Exit",
        on_click=lambda e: save_and_exit(page),
        icon=ft.icons.SAVE,
        bgcolor=ft.colors.RED_400
    )

    input_row = ft.Row(
        controls=[
            user_input,
            send_button,
            save_button
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    page.add(
        ft.Text("Fleto Chato", size=30, weight=ft.FontWeight.BOLD),
        chat_history,
        input_row
    )

ft.app(target=main) 