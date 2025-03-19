from flask import Flask, render_template, request, jsonify
from sql_agent import SqlAgent
from project_data import get_project_formatted, odata_links  # Add odata_links import
from mongodb_handler import MongoDBHandler
from datetime import datetime
import numpy as np
import voyageai

app = Flask(__name__)
API_BUSINESS_PARTNER = '''
What is the supplier ID of the business partner '4'?
What is the business partner grouping for 'CHA Pvt. Ltd.'?
Which business partner was created by the user 'VIDYA'?
What is the SearchTerm1 value for the business partner 'Embassy India'?'''

API_SALES_ORDER_SRV='''
What is the total net amount for Sales Order '1'?
Who created the Sales Order '3', and on what date?
Which Sales Order has the highest total net amount?
What is the SalesOrganization value for all Sales Orders?
'''

API_PURCHASEORDER_PROCESS_SRV='''
How many unique Purchase Orders exist in the dataset?
Identify all GL Accounts used in these Purchase Orders.
Find all Purchase Orders where the Cost Center is empty.
List all Purchase Orders with a Net Amount greater than 10,000.
Identify which Cost Center has the highest total Net Amount.'''


response_dict = {"API_BUSINESS_PARTNER":API_BUSINESS_PARTNER,
                 "API_SALES_ORDER_SRV":API_SALES_ORDER_SRV,
                 "API_PURCHASEORDER_PROCESS_SRV":API_PURCHASEORDER_PROCESS_SRV}

tables = [
    '''CREATE TABLE Business_Partner (
    BusinessPartnerID TEXT,
    CustomerID TEXT,
    SupplierID TEXT,
    AcademicTitle TEXT,
    AuthorizationGroup TEXT,
    Category TEXT,
    FullName TEXT,
    Grouping TEXT,
    Name TEXT,
    UUID TEXT,
    CorrespondenceLanguage TEXT,
    CreatedByUser TEXT,
    CreationDate DATE,
    CreationTime DATETIME,
    FirstName TEXT,
    Language TEXT,
    LastChangeDate DATE,
    LastChangeTime DATETIME,
    LastChangedByUser TEXT,
    LastName TEXT,
    LegalEntityType TEXT,
    OrganizationName1 TEXT,
    OrganizationName2 TEXT,
    OrganizationName3 TEXT,
    OrganizationName4 TEXT,
    Org_Keyword TEXT,
    IsBlocked BOOLEAN,
    BusinessPartnerType TEXT,
    Country TEXT,
    IsMarkedForArchiving BOOLEAN,
    IsTradingPartner TEXT
);
''',
'''CREATE TABLE Customer (
    CustomerID TEXT,
    AuthorizationGroup TEXT,
    IsBilling_Blocked TEXT,
    CreatedByUser TEXT,
    CreationDate TEXT,
    AccountGroup TEXT,
    Classification TEXT,
    FullName TEXT,
    Name TEXT,
    IsDelivery_Blocked TEXT,
    Is_Person TEXT,
    IsOrder_Blocked TEXT,
    IsPosting_Blocked BOOLEAN,
    SupplierID TEXT,
    TaxNumber1 TEXT,
    TaxNumber2 TEXT,
    TaxNumber3 TEXT,
    TaxNumber4 TEXT,
    TaxNumber5 TEXT,
    TaxNumberType TEXT,
    VATRegistration_ID TEXT,
    DeletionIndicator BOOLEAN
);
''',
'''CREATE TABLE Supplier_Vendor (
    SupplierID TEXT,
    Alternative_AccountNumber TEXT,
    AuthorizationGroup TEXT,
    CreatedByUser TEXT,
    CreationDate DATE,
    CustomerID TEXT,
    IsPayment_Blocked BOOLEAN,
    IsPosting_Blocked BOOLEAN,
    IsPurchasing_Blocked BOOLEAN,
    AccountGroup TEXT,
    FullName TEXT,
    Name TEXT,
    VATRegistration_ID TEXT,
    DeletionIndicator BOOLEAN,
    Is_Supplier_Person TEXT,
    isProcurement_Blocked TEXT,
    TaxNumber1 TEXT,
    TaxNumber2 TEXT,
    TaxNumber3 TEXT,
    TaxNumber4 TEXT,
    TaxNumber5 TEXT,
    TaxNumberType TEXT
);

''']


def get_greeting_message(project_info):
    respone_greeting = f'''Welcome to {project_info['name']}!\n\n"
                {project_info['details']}\n\n
               
                • Type / to see available tables\n
                • Select a table to start querying\n

                • example questions {response_dict.get(project_info['name'],' Ask questions in natural language about the data')}'''
    return respone_greeting

def get_id_from_embeding(question):
    #load table embeds
    loaded_array = np.load('BP_1.npy')
    table_embeds = loaded_array.tolist()

    # Embed the query
    zoho = voyageai.Client(api_key="pa-D-h0u6XerwqiaY1VB5Xzxg9IpT54R8VD8rjWXIFtPDr") 
    question_embd = zoho.embed(
        [question], model="voyage-code-3", input_type="query"
    ).embeddings[0]
    
    #find similarities
    similarities = np.dot(table_embeds, question_embd)
    retrieved_id = np.argmax(similarities)
    # table_id =tables[retrieved_id]
    print(f'the table id from embeding is {retrieved_id}')

    return retrieved_id

@app.route('/')
def home():
    return render_template('chatapp.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        MDB = MongoDBHandler()
        data = request.json

        # Handle table selection message
        if data.get('type') == 'table_select':
            table_name = data.get('table_name', '')
            response_message = (
                f"📋 Selected table: {table_name}\n\n"
                "How can I help you with this table? You can:\n"
                "• Ask about specific columns\n"
                "• Query for data\n"
                "• Get table statistics\n"
                "• Ask about relationships with other tables"
            )
            return jsonify({
                'status': 'success',
                'response': response_message
            })

        # Handle greeting message when domain is selected
        if data.get('type') == 'greeting':
            project_id = data.get('project_id')
            project_dict = MDB.get_project_complete_info(project_id=project_id)
            project_info = project_dict['project_info']
            msg = get_greeting_message(project_info)
            
            greeting_message = (
               msg
            )
            
            return jsonify({
                'status': 'success',
                'response': greeting_message
            })

        # Regular chat flow
        project_id = data.get('project_id')
        user_id = data.get('user_id')
        human_question = data.get('message')
        table_id = data.get('table_id')
        
        # Get project data
        project_dict = MDB.get_project_complete_info(project_id)
        
        if int(table_id) == 1001:
            table_id = get_id_from_embeding(human_question)

        print(f'we got table id of {table_id}')
        
        
        # Create SQL Agent instance
        user_instance = SqlAgent(
            user_id=user_id,
            user_name='default_user',  # Default value as requested
            human_question=human_question,
            table_id=table_id,
            access_id=1,  # Default value as requested
            filters_dict=project_dict.get('filters_dict'),
            project_id=project_id,
            project_info=project_dict.get('project_info', {}),
            table_dict=project_dict.get('table_dict', {}),
            access_dict=project_dict.get('access_dict', {}),
            users_dict=project_dict.get('users_dict', {})
        )

        answer, answer_dict = user_instance.run_agent()

        return jsonify({
            'status': 'success',
            'response': answer,
            'tableData': answer_dict
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/get_table_options', methods=['POST'])
def get_table_options():
    try:
        MDB = MongoDBHandler()
        project_id = request.json.get('project_id')
        if not project_id:
            return jsonify({'error': 'Project ID required'})

        project_data = MDB.get_project_complete_info(project_id)
        if not project_data or 'project_info' not in project_data:
            return jsonify({'error': 'Project not found'})

        # Get tables from project_info
        tables = project_data['project_info'].get('tables', [])
        
        # Format options
        options = {}
        for table in tables:
            table_id = table.get('table_id')
            table_name = table.get('table_name')
            if table_id is not None and table_name:
                options[str(table_id)] = f"{table_id} - {table_name}"

        return jsonify(options)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/get_projects_list')
def get_projects_list():
    try:
        MDB = MongoDBHandler()
        projects = MDB.get_all_projects()
        return jsonify({
            'status': 'success',
            'projects': [{
                'project_id': p['project_id'],
                'name': p.get('name', p['project_id'])
            } for p in projects]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/validate_user', methods=['POST'])
def validate_user():
    try:
        MDB = MongoDBHandler()
        data = request.json
        user = MDB.validate_user(data['user_id'], data['password'])
        if user:
            return jsonify({
                'status': 'success',
                'access_id': user['access_id']
            })
        return jsonify({
            'status': 'error',
            'message': 'Invalid credentials'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/get_users')
def get_users():
    try:
        MDB = MongoDBHandler()
        users = MDB.get_all_users()
        return jsonify({
            'status': 'success',
            'users': users
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, port=5000)