import os
from typing import Optional, TypedDict, Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# Fast api

app = FastAPI(title="Real Estate AI Lead Qualification Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# LLM model

model = ChatOpenAI(model='gpt-4o-mini', temperature = 0)



# Structured Output for user info: 

class User_State(BaseModel):
  location : str = Field(description = 'The location where customer intents to buy the property. It can be a city, state or country', default = None)
  budget: int = Field(description = 'Approximate budget or amount set aside by the customer for buying the property in Saudi Riyals', ge=0, default = None)
  property_type : Literal["Apartment", "Villa", "Commercial Space"] = Field(description = "Type of property the customer is looking to buy", default = None)
  Properties_interested : list[str] = Field(description = "Properties customer have shown interest in.", default = None)


extraction_model = model.with_structured_output(User_State, method="json_schema")


# Langgraph state
class chat_state(TypedDict):
  messages : list
  budget : Optional[int]
  property_type : Optional[str]


  #final response
  response : str



# Extract lead information
def extract_user_info(state: chat_state):
  conversation = "\n".join(
        [
            f"{message['role']}: {message['content']}"
            for message in state["messages"]
        ]
    )
  prompt = f"""
  You are a real estate sales lead qualification assistant.
  Extract customer requirements from the conversation below.
  Only extract information that the customer has actually provided.
  Rules:
  1. Do not add information not provided by the user.

  Conversation:
  {conversation}
  """

  result = extraction_model.invoke(prompt)
  
  return{
      "location" : result.location,
      "budget" : result.budget,
      "property_type" : result.property_type,
      "Properties_interested" : result.Properties_interested
      
  }

# Generate response

def generate_response(state: chat_state):
    location = state.get("location")
    budget = state.get("budget")
    property_type = state.get("property_type")
    properties_interested = state.get("Properties_interested")

    collected_information = f"""
    Location: {location}
    Budget: {budget}
    Property Type: {property_type}
    Properties Interested: {properties_interested}
    """

    prompt = f"""
    You are an AI real estate sales assistant.

    Your job is to qualify a potential property buyer.

    Collected information:
    {collected_information}

    Ask the customer for the MOST IMPORTANT missing piece of information.

    Priority:
    1. Location
    2. Property type
    3. Budget

    Rules:
    - Ask only ONE question at a time.
    - Keep the question conversational, professional, polite, and sales-oriented.
    - Do not ask for information that has already been provided.
    - Do not recommend properties yet.
    - Do not make up any property information.
    - If all three qualification details are available, thank the customer and
      say that you have enough information to help find suitable properties.
    """

    response = model.invoke(
        [
            SystemMessage(
                content="You are a professional real estate sales consultant."
            ),
            HumanMessage(content=prompt)
        ]
    )

    return {
        "response": response.content
    }

#### Building Graph

#Add nodes
graph.add_node("extract_user_info", extract_user_info)
graph.add_node("generate_response", generate_response)

#Add edges
graph.add_edge(START, "extract_user_info")
graph.add_edge("extract_user_info", "generate_response")
graph.add_edge("generate_response", END)


#Compile the model
Final_graph = graph.compile()


## API Requests model

class ChatRequest(BaseModel):

    message: str

    history: list = []

    lead: dict = {}

@app.post("/api/chat")
def chat(request: ChatRequest):

    messages = request.history.copy()

    messages.append(
        {
            "role": "user",
            "content": request.message
        }
    )

    initial_state = {
        "messages": messages,

        "property_type": request.lead.get(
            "property_type"
        ),

        "location": request.lead.get(
            "location"
        ),

        "budget": request.lead.get(
            "budget"
        ),
        "response": ""
    }

    result = Final_graph.invoke(initial_state)

    return {
        "response": result["response"],

        "lead": {
            "property_type": result.get("property_type"),
            "location": result.get("location"),
            "budget": result.get("budget"),
            "Properties_interested" : result,get("Properties_interested")
            
        }
    }

@app.get("/api")
def health():

    return {
        "status": "online",
        "service": "Real Estate AI Lead Qualification Chatbot"
    }


