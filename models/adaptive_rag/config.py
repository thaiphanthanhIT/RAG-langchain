import os
import json 
def set_environment_variables(project_name):
    #filepath = "/app/API.json" # with docker, if you don't use docker, replace by your own filepath to API_key
    filepath = "D:/AI_intern/API.json"
    with open(filepath, 'r', encoding = 'utf-8') as f:
        APIs = json.load(f)
    os.environ['GOOGLE_API_KEY'] = APIs['GOOGLE_API_KEY']
    os.environ['FIREWORKS_API_KEY'] = APIs['FIREWORKS_API_KEY']
    os.environ['GROQ_API_KEY'] = APIs['GROQ_API_KEY']
    os.environ['TAVILY_API_KEY'] = APIs['TAVILY_API_KEY']
    os.environ['LANGCHAIN_API_KEY'] = APIs['LANGCHAIN_API_KEY']
    os.environ['OPENAI_API_KEY'] = APIs['OPEN_ROUTER_API_KEY']
    os.environ['LANGCHAIN_TRACING_V2'] = "true"
    os.environ['LANGCHAIN_PROJECT'] = project_name