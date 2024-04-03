import openai
from constants import BASE_URL, API_KEY, MODEL

def request():
    openai.base_url = BASE_URL
    openai.api_key = API_KEY
    context = []
    context.append({'role': 'user', 'content': 'hello, what is Defects4j.'})
    response = openai.chat.completions.create(model=MODEL, messages=context, logprobs = True, temperature = 0)
    response_text = response.choices[0].message.content
    context.append({'role': 'assistant', 'content': response_text})
    print(context)
    
if __name__ == '__main__':
    request()