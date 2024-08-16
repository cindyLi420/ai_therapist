
import agents
import utilities
import os
from langchain_openai import ChatOpenAI
import psycopg2
import streamlit as st

os.environ["OPENAI_API_KEY"] = 'sk-Z2FKFpmzJc9u7riW14F200F520C542B1AdD5FfA7E6684d4b'
os.environ["OPENAI_API_BASE"] = 'https://api.xty.app/v1'



def save_conversation_log(username, userinput, conversation_history_client, conversation_history, stage_history,last_history):
    conn = psycopg2.connect(
        dbname="ai_therapist",
        user="postgres",
        password="1996310ljkb",
        host="6.tcp.cpolar.cn",
        port="12302"
    )
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO therapist_conversation_logs (username, userinput, conversation_history_client, conversation_history, stage_history, last_history)
        VALUES (%s, %s, %s, %s, %s,%s)
    """, (username, userinput, conversation_history_client, conversation_history, stage_history, last_history))

    conn.commit()
    cursor.close()
    conn.close()

class AgentImplementation():
    """
    机器人实作
    """

    def __init__(self):
        self.chat_model = ChatOpenAI(model='gpt-4o',temperature=0.2, openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.stage_analyzer = agents.StageAnalyzer.from_llm(self.chat_model, verbose=True)
        #self.automatic_thoughts_analyzer = agents.AutomaticThoughtsAnalyzer.from_llm(self.chat_model, verbose=True)

    def get_stage_analyzer(self):
        return self.stage_analyzer
    
    def get_automatic_thoughts_analyzer(self):
        return self.automatic_thoughts_analyzer

    def generate_conversation(self, username ,userinput, conversation_history_client, conversation_history, stage_history, last_history):

        # 階段识别机器人
        stage_number = 1
        result_stage_analyzer_chain = self.stage_analyzer.invoke({'stage_history': stage_history, 
                                                                'conversation_history': conversation_history,
                                                                'last_history': last_history
                                                                })
        stage_number = int(result_stage_analyzer_chain["text"])

        # 自動化思惟機器人
        automatic_thoughts = ""
        automatic_thoughts_number = 0

        if stage_number == 12:
            if  conversation_history != "" :
                result_automatic_thoughts_analyzer = self.automatic_thoughts_analyzer.invoke({'conversation_history_client': conversation_history_client})
                automatic_thoughts_number = int(result_automatic_thoughts_analyzer["text"])
                if automatic_thoughts_number > 0:
                    automatic_thoughts = agents.automatic_thoughts[automatic_thoughts_number]

                conversation_generator = agents.ConversationGeneratorWithAutomaticThoughtsChecking.from_llm(self.chat_model, verbose=True)
                result_conversation_chain = conversation_generator.invoke({'current_stage': stage_number, 
                                                                    'current_stage_purpose': agents.stage_purpose[stage_number],
                                                                    'current_stage_instruction': agents.stage_instruction[stage_number],
                                                                    'automatic_thoughts': automatic_thoughts,
                                                                    'conversation_history': conversation_history,                                                       
                                                                    })
        else:
            conversation_generator = agents.ConversationGenerator.from_llm(self.chat_model, verbose=True)
            result_conversation_chain = conversation_generator.invoke({'current_stage': stage_number, 
                                                                    'current_stage_purpose': agents.stage_purpose[stage_number],
                                                                    'current_stage_instruction': agents.stage_instruction[stage_number],
                                                                    'conversation_history_client':conversation_history_client,
                                                                    'conversation_history':conversation_history,
                                                                    'last_history':last_history,
                                                                    })



            save_conversation_log(
            username,
            userinput,
            conversation_history,
            result_conversation_chain["text"],
            stage_number,
            last_history
        )
    
        return result_conversation_chain["text"],stage_number