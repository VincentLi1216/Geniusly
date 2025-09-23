import os
from openai import OpenAI
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

# 從環境變數取得 API Key
api_key = os.getenv("OPENAI_API_KEY")

# 初始化 OpenAI client
client = OpenAI(api_key=api_key)

def get_topic_suggestions(user_interest: str, model: str = "gpt-4.1-mini") -> list[str]:
    """
    根據使用者的學習方向，請 AI 提供聚焦後的主題建議清單
    """
    system_prompt = "You are a creative tutor. Your job is to suggest 5 fun, specific, and engaging video topics that are good for a short educational skit."
    user_prompt = f"The user wants to learn about: {user_interest}\nPlease suggest 5 possible video topics."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    return response.choices[0].message.content


def build_message_list(system_prompt: str, topic: str):
    """
    建立 OpenAI chat message list
    - system: 固定 Family Guy 對話風格
    - user:   輸入想要的主題
    """
    user_prompt = f"Topic: {topic}\nWrite the script."

    message_list = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    return message_list


def chat_with_openai(message_list: list[dict], model: str = "gpt-4.1-mini") -> str:
    """
    與 OpenAI 模型對話的函式
    """
    response = client.chat.completions.create(
        model=model,
        messages=message_list
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    # Step 1: 使用者輸入學習興趣
    user_interest = input("你想要學什麼？ ")

    # Step 2: AI 提供主題清單
    suggestions = get_topic_suggestions(user_interest)
    print("\n可行的影片主題清單:")
    print(suggestions)

    # Step 3: 使用者選一個主題
    chosen_topic = input("\n請從上面選一個主題: ")

    # Step 4: 生成 Family Guy 風格對話
    system_prompt = """You are to roleplay as characters from Family Guy in a short script (about 1 minute long).

Characters:
- Stewie: sarcastic, highly intelligent baby, curious, asks sharp questions.
- Peter: goofy, clueless father, often makes silly analogies but sometimes stumbles into the right explanation.

Rules:
1. Dialogue should alternate between Stewie and Peter, starting with Stewie asking a question.
2. Keep it short and snappy, like a cartoon skit (10-12 lines total).
3. Humor is essential—Peter's answers should be funny, sometimes absurd, but loosely tied to the real explanation.
4. Stewie should occasionally roast Peter's stupidity but also clarify the correct idea.
5. The script must feel like a Family Guy cutaway gag: sarcastic, humorous, and fast-paced.
6. Output format:
   Stewie: …
   Peter: …

Do not include narration or stage directions—just pure dialogue.
"""

    messages = build_message_list(system_prompt, chosen_topic)
    reply = chat_with_openai(messages)
    print("\n=== 生成的腳本 ===")
    print(reply)
