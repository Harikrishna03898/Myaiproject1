from conversation_hanlder import fetch_recent_interactions_by_user
from all_utitlity import extract_sql_code
from odataextraction import fetch_data_from_url
from project_data import get_project_formatted
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime
import google.generativeai as genai
import sqlite3
import pandas as pd
import os
import re
from mongodb_handler import MongoDBHandler

genai.configure(api_key="AIzaSyDw9k3Y_1l7nlQ2xvwJIhtLNPhiTKHaJvw")
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = "AIzaSyDw9k3Y_1l7nlQ2xvwJIhtLNPhiTKHaJvw"

class SqlAgent:
    def __init__(self, user_id, user_name,human_question,project_id,project_info,table_dict,access_dict,users_dict,table_id=None,access_id=None,filters_dict=None):
        self.user_id = user_id
        self.user_name = user_name
        self.human_question = human_question
        self.table_id = table_id
        self.project_id = project_id
        self.project_info = project_info
        self.table_dict = table_dict
        self.access_dict = access_dict
        self.filters_dict = filters_dict
        self.users_dict = users_dict
        self.access_id = access_id
        self.filters_dict = filters_dict

 
    #step 1 - get conversation - previous , 
    def get_conversation(self):
        print('entered get conversation')
        conversation_dict = fetch_recent_interactions_by_user(self.user_id, self.user_name)

        return conversation_dict
    
# step 2 - use that conversation and get database question ( rephrased and the format number) , 
    def reframe_question(self,conversation,access_id,human_question):
            # print('entered reframe question')
            llm = ChatGoogleGenerativeAI(
                api_key="AIzaSyDw9k3Y_1l7nlQ2xvwJIhtLNPhiTKHaJvw",
                model="gemini-2.0-flash-exp",
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2,
            )
            rephrase_disctiptions = {1:"a fully formed Database question for the followup message[ additionally convert the pronouns to nouns in the message]",
                                    5:"a fully formed Database question for my followup message [ Don't use my name in the Database question instead of name use I or my pronouns.]"}
            
            rephrase_instruction = rephrase_disctiptions.get(access_id,"based on conversation form a full question for last message")

            json_schema = {
                "title": "followup",
                "description": "a simple question rephrase and format numbering.",
                "type": "object",
                "properties": {
                    "database_question": {
                        "type": "string",
                        "description": rephrase_instruction,
                        "default": None,
                    },
                    "format": {
                        "type": "string",
                        "description": "answer format: pick anyone from 1,2,3,4 to choose the response format (1 - one line, 2- paragraph, 3- list, 4- table)",
                    },
                },
                "required": ["format"],
            }

            structured_llm = llm.with_structured_output(json_schema)
            conv = f'this is complete conversation: {conversation}, now followup message is: {human_question}.'
            structured_output = structured_llm.invoke(conv)
            
            database_question = structured_output[0]['args'].get('database_question')
            format_number = structured_output[0]['args'].get('format')

            rephrase_dict = {'database_question':database_question,'format_number':format_number}
            return rephrase_dict 
 
# step 3 - get table name and access id from useing that get schema . 
    def get_schema(self):
        schema = self.table_dict[self.table_id]
        return schema
    
#step 4 : get sql query from ai
    def get_sql_query(self,schema,database_question):
            instruction_query = "Just write one SQL query for this:[ Note - don't use names directly , if you want to use names ( if only user asked by giving the name in input ) use, like operator with % symbol and make the given name and name in table to lower case  instead of = symbol][Note 2 - example row will help to understand how to handle and fetch columns specifically for dates][Note - avoid giving complex query , write minimal select queries with less parameters possible.]"
            query_model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=instruction_query)
            query_chat = query_model.start_chat()

            prompt = f' [reference time - today is :{datetime.now()}] , Schema: {schema} Query: {database_question} '
            sql_query = query_chat.send_message(prompt)

            sql_code = extract_sql_code(sql_query.text)
            sql_function_query = ''
            for code in sql_code:
                sql_function_query = code

            return sql_function_query
    
# step 5 - get data from database using user id and filters dictionary 
    def db_flow(self, SQL_question: str, schema: str) -> str:
        try:
            match = re.search(r"CREATE TABLE (\w+)", schema)
            if match:
                table_name = match.group(1)
            else:
                table_name = 'Material_Details'

            # Use MongoDB handler to fetch data
            MDB = MongoDBHandler()
            df = MDB.get_odata_data(
                project_id=self.project_id, 
                table_id=self.table_id,
                user_id=self.user_id  # Pass user_id for filtering
            )
        
            
            if df.empty:
                raise Exception("No data retrieved from OData service")
            
            if "Warning" in df.columns:
                warning_dict = {}
                for column in df.columns:
                    warning_dict[column] = df[column].tolist()
                return df,warning_dict,df.to_string()

            # Create in-memory SQLite database
            conn = sqlite3.connect(':memory:')
            df.to_sql(table_name, conn, index=False, if_exists='replace')

            # Execute query
            pysqldf = pd.read_sql_query(SQL_question, conn)
            conn.close()

            # Convert results to dictionary
            result_dict = {}
            for column in pysqldf.columns:
                result_dict[column] = pysqldf[column].tolist()

            return pysqldf, result_dict, pysqldf.to_string()

        except Exception as e:
            print(f"Error in db_flow: {str(e)}")
            raise

    # step 5 - pass the answer dataframe to a reasoning model to get final answer so all steps are each functions maybe 
    def reason_answer(self,answer,sql_function_query,access_id):
        today = datetime.now()
        humanize_instruction = "Based on the Conversation Humanize the given answer, don't write sql code or any other code just humanize the answer"
        human_model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-01-21", system_instruction=humanize_instruction)
        humanize_chat = human_model.start_chat()
        reasoning_discriptions = {1:f"question: {self.human_question}, sql query executed - {sql_function_query}, response from database - {answer}, AI response - ? You are a HR and here user(from management) asked a question and we have answer from database, using this answer form a reply one line or one paragraph. [ now : {today}]",
                                  5:f"question: {self.human_question}, sql query executed - {sql_function_query}, response from database - {answer}, AI response - ? You are a HR who answers for employees question ( answer only related and here user asked a question and we have answer from database, using this answer form a reply one line or one paragraph. [ now : {today}]"}
        reasoning_insturction = reasoning_discriptions[access_id]
        humanize_response = humanize_chat.send_message(reasoning_insturction)          
        answer = humanize_response.text
        return answer

    def set_table_id(self,table_id):
        if self.table_id is None:
            if table_id == 'Invalid':
                self.table_id = 0
            else:
                self.table_id = table_id
        else:
            self.table_id = self.table_id

    def run_agent(self):
        conversation_dict = self.get_conversation()
        conversation , table_id= conversation_dict['conversation'] , conversation_dict['command_id']
        self.set_table_id(table_id)
        print(f'conversation is : {conversation} and table id is : {table_id}')

         
        rephrase_dict = self.reframe_question(conversation=conversation, access_id=self.access_id, human_question= self.human_question)
        database_question , format_number = rephrase_dict['database_question'] , rephrase_dict['format_number']
        print('database question:',database_question)

        schema = self.get_schema()
        sql_question = self.get_sql_query(schema,database_question)
        print('sql question:',sql_question)

        answer , answer_dict , answer_string = self.db_flow(sql_question, schema=schema)
        print(f'answer from db is : {answer}')
        answer = self.reason_answer(answer_string,sql_question,self.access_id)


        return answer,answer_dict
    

if __name__ == "__main__":
    
    MDB = MongoDBHandler()
    project_dict = MDB.get_project_complete_info('Inventory Management (IM) -1')
    # project_dict = get_project_formatted('Business Partner (BP) & Customer Management - 1')    
    # print(project_dict,type(project_dict))
    user_id , user_name , human_question , table_id , access_id , filters_dict = 'i319','ankith','how many plants we have',1,1,None
    project_id = project_dict['project_id']
    project_info = project_dict['project_info']
    table_dict = project_dict['table_dict']
    access_dict = project_dict['access_dict']
    filters_dict = project_dict['filters_dict']
    users_dict = project_dict['users_dict']
    user_instance = SqlAgent(user_id, user_name, human_question,table_id=table_id,access_id=access_id,filters_dict=filters_dict,project_id=project_id,project_info=project_info,table_dict=table_dict,access_dict=access_dict,users_dict=users_dict)
    answer,answer_dict = user_instance.run_agent()
    print(f'final response is :',answer,answer_dict,type(answer_dict))



