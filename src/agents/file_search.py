from langchain.chat_models import init_chat_model

import operator
from typing import Annotated, Optional
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field

class FileSearchState(MessagesState):

    file_path: str = Field(..., description="The path to the file that matches the search criteria.")
    


    
    
