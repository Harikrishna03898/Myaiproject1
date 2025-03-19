from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
import sqlite3
import os
# Secure MongoDB Connection
MONGO_URI = "mongodb+srv://reshma:G2M13xyy25MYQ6DG@card-cluster.ii6jw.mongodb.net/"
client = MongoClient(MONGO_URI)

# Database & Collections
db = client['chatbot_db']
user_emp_collection = db['user_emp']

def get_user_emp_by_id_and_time(employee_id):
    try:
        emp_id = employee_id  # Ensure correct input
        if not emp_id.isalnum():  # Validate ID format
            return []

        time_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)  # Time filter (last 5 minutes)
        # logging.info(f"Fetching records for Employee ID: {emp_id} within the last 5 minutes.")

        query = {"emp_id": emp_id, "created_at": {"$gte": time_threshold}}  # Filter by ID and time range
        records = list(user_emp_collection.find(query, {"_id": 0}).sort("created_at", -1))  # Sort by latest entries
        
        if records:
            # logging.info(f"\nFiltered Records for Employee {emp_id} in the last 5 minutes:\n" )
            # + pp.pformat(records)
            return records
        else:
            # logging.info(f"\nNo records found for Employee {emp_id} in the last 5 minutes.")
            return []

    except Exception as e:
        # logging.error(f"Error fetching filtered records: {e}")
        return []


def fetch_recent_interactions_by_user(user_id,user_name):
   
    # Lists to store the results
    user_inputs = []
    final_responses = []
    lines = []
    command_id = None

    try:
        results = get_user_emp_by_id_and_time(user_id)
        try:
            command_id = results[0]['command_id']
        except:
            command_id = 'Invalid'
    

        # Populate the lists
        for row in reversed(results):
            user_inputs.append(row['user_input'])  # user_input
            final_responses.append(row['AI_output'])  # final_response
        
        print(f"Recent interactions for user ID {user_id} fetched successfully!")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
 
    # Loop through the lists and format each pair
    for user_input, final_response in zip(user_inputs, final_responses):
        lines.append(f"{user_name}: {user_input}")
        lines.append(f"AI: {final_response}")

    # Join the lines using os.linesep
    multiline_string = os.linesep.join(lines)
    conversation_dict = {'conversation':multiline_string, 'command_id':command_id}
    return conversation_dict

def insert_user_emp(emp_id, user_input, AI_output, command_id):
    record = {
        "emp_id": emp_id,
        "created_at": datetime.now(timezone.utc),
        "user_input": user_input,
        "AI_output": AI_output,
        "command_id": command_id
    }
    try:
        user_emp_collection.insert_one(record)
        # logging.info(f"Inserted record for emp_id: {emp_id}")
        return record
    except Exception as e:
        # logging.error(f"Error inserting record: {e}")
        print('error at insert_user_emp')
        return None

if __name__ == "__main__":
    emp_id , user_input, AI_output, command_id = 'i340','hi 3rd time ','Hello 3rd time', '1'

    # answer = insert_user_emp(emp_id, user_input, AI_output, command_id)
    answer = fetch_recent_interactions_by_user('i340','Reshma')
    print(answer)