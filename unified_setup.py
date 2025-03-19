from flask import Flask, render_template, request, jsonify, send_from_directory
from mongodb_handler import MongoDBHandler
import pandas as pd
from requests.auth import HTTPBasicAuth
import requests
import json
import os

app = Flask(__name__)
app.static_folder = 'static'
db_handler = MongoDBHandler()

# Add this new function
def apply_table_modifications(df, modifications):
    """Apply modifications to the DataFrame"""
    if not modifications:
        return df
    
    # Remove dropped columns
    if 'drops' in modifications:
        df = df.drop(columns=modifications['drops'])
    
    # Rename columns
    if 'renames' in modifications:
        df = df.rename(columns=modifications['renames'])
    
    # Change data types
    if 'dtypes' in modifications:
        for col, dtype in modifications['dtypes'].items():
            try:
                if dtype == 'convertedDate':
                    df[col] = df[col].apply(lambda x: pd.to_datetime(int(x[6:-2]), unit='ms').date() if isinstance(x, str) and x.startswith('/Date(') else x)
                else:
                    df[col] = df[col].astype(dtype)
            except Exception as e:
                print(f"Error converting column {col} to {dtype}: {str(e)}")
    
    return df

# Modify the fetch_odata_preview function
def fetch_odata_preview(url, modifications=None):
    try:
        username = 'ananth'
        password = 'Gan25e$hA'
        response = requests.get(f"{url}?$format=json", auth=HTTPBasicAuth(username, password))
        response.raise_for_status()
        
        data = response.json()
        if 'd' in data:
            main_data = data['d'].get('results', [])
        elif 'value' in data:
            main_data = data['value']
        else:
            main_data = data
        
        df = pd.DataFrame(main_data)
        if '__metadata' in df.columns:
            df.drop(columns=['__metadata'], inplace=True)
        
        # Apply modifications if provided
        if modifications:
            df = apply_table_modifications(df, modifications)
            
        return {
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.astype(str).to_dict(),
            'preview_data': df.head().to_dict('list')  # Include preview data
        }
    except Exception as e:
        return {'error': str(e)}

def generate_sql_schema(table_name, columns, dtypes):
    sql_types = {
        'object': 'TEXT',
        'int64': 'INTEGER',
        'float64': 'FLOAT',
        'datetime64': 'DATETIME',
        'bool': 'BOOLEAN',
        'convertedDate': 'DATE'
    }
    
    schema = f"CREATE TABLE {table_name} (\n"
    cols = []
    for col in columns:
        sql_type = sql_types.get(dtypes[col], 'TEXT')
        cols.append(f"    {col} {sql_type}")
    
    schema += ",\n".join(cols)
    schema += "\n);"
    return schema

@app.route('/')
def index():
    return render_template('unified_setup.html')

# Update the preview_odata route
@app.route('/preview_odata', methods=['POST'])
def preview_odata():
    try:
        url = request.json.get('url')
        modifications = request.json.get('modifications')
        
        if not url:
            return jsonify({'error': 'URL is required'})
            
        result = fetch_odata_preview(url, modifications)
        print('Preview result:', result)  # Debug log
        return jsonify(result)
    except Exception as e:
        print('Preview error:', str(e))  # Debug log
        return jsonify({'error': str(e)})

@app.route('/save_project', methods=['POST'])
def save_project():
    try:
        data = request.json
        result = db_handler.save_project(data)
        return jsonify({'status': 'success', 'message': 'Project saved successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/view_projects')
def view_projects():
    projects = db_handler.get_all_projects()
    return render_template('view_projects.html', projects=projects)

@app.route('/add_user', methods=['POST'])
def add_user():
    try:
        user_data = request.json
        db_handler.add_user(user_data)
        return jsonify({'status': 'success', 'message': 'User added successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/add_access_policy', methods=['POST'])
def add_access_policy():
    try:
        policy_data = request.json
        db_handler.save_access_policy(policy_data)
        return jsonify({'status': 'success', 'message': 'Access policy added successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/get_project_tables', methods=['POST'])
def get_project_tables():
    try:
        project_id = request.json.get('project_id')
        project = db_handler.get_project(project_id)
        if project and 'tables' in project:
            return jsonify({'status': 'success', 'tables': project['tables']})
        return jsonify({'status': 'error', 'message': 'Project or tables not found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/get_table_columns', methods=['POST'])
def get_table_columns():
    try:
        project_id = request.json.get('project_id')
        table_id = request.json.get('table_id')
        project = db_handler.get_project(project_id)
        
        if project and 'tables' in project:
            table = next((t for t in project['tables'] if t['table_id'] == table_id), None)
            if table:
                return jsonify({'status': 'success', 'columns': table.get('columns', [])})
        
        return jsonify({'status': 'error', 'message': 'Table not found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# Add new route to get existing project data
@app.route('/get_project/<project_id>')
def get_project(project_id):
    project = db_handler.get_project(project_id)
    if project:
        return jsonify({'status': 'success', 'data': project})
    return jsonify({'status': 'error', 'message': 'Project not found'})

# Add this new route
@app.route('/get_projects_list')
def get_projects_list():
    try:
        projects = db_handler.get_all_projects()
        return jsonify({
            'status': 'success',
            'projects': [{
                'project_id': p['project_id'],
                'name': p['name']
            } for p in projects]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# Add new route to get preview data with modifications
@app.route('/preview_with_modifications', methods=['POST'])
def preview_with_modifications():
    try:
        url = request.json.get('url')
        modifications = request.json.get('modifications')
        result = fetch_odata_preview(url, modifications)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/generate_schema', methods=['POST'])
def generate_schema():
    try:
        data = request.json
        schema = generate_sql_schema(
            data['table_name'],
            data['columns'],
            data['dtypes']
        )
        return jsonify({'schema': schema})
    except Exception as e:
        return jsonify({'error': str(e)})

# Add this new route for serving template files
@app.route('/static/templates/<path:filename>')
def serve_template(filename):
    return send_from_directory(os.path.join(app.static_folder, 'templates'), filename)

# Add these new routes

@app.route('/delete_project/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    try:
        result = db_handler.delete_project(project_id)
        return jsonify({'status': 'success', 'message': 'Project deleted successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# Update the get_users route

@app.route('/get_users')
def get_users():
    try:
        users = db_handler.get_all_users()
        if users is None:
            users = []
        return jsonify({
            'status': 'success',
            'users': users
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# Update the get_access_policies route

@app.route('/get_access_policies')
def get_access_policies():
    try:
        policies = db_handler.get_all_policies()
        if policies is None:
            policies = []
        return jsonify({
            'status': 'success',
            'policies': policies
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# Add this new route

@app.route('/get_access_policy/<access_id>')
def get_access_policy(access_id):
    try:
        policy = db_handler.get_access_policy(access_id)
        if policy:
            return jsonify({'status': 'success', 'data': policy})
        return jsonify({'status': 'error', 'message': 'Policy not found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# Add new route for deleting access policy
@app.route('/delete_access_policy/<access_id>', methods=['DELETE'])
def delete_access_policy(access_id):
    try:
        result = db_handler.delete_access_policy(access_id)
        return jsonify({
            'status': 'success', 
            'message': 'Access policy deleted successfully'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# Add new route to get all projects
@app.route('/get_projects')
def get_projects():
    try:
        projects = db_handler.get_all_projects()
        return jsonify({
            'status': 'success',
            'projects': projects
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

# Add new route to validate user
@app.route('/validate_user', methods=['POST'])
def validate_user():
    try:
        data = request.json
        user = db_handler.validate_user(data['user_id'], data['password'])
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

# Add these new routes

@app.route('/delete_user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        result = db_handler.delete_user(user_id)
        return jsonify({
            'status': 'success',
            'message': 'User deleted successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })
        
if __name__ == '__main__':
    app.run(debug=True, port=5000)