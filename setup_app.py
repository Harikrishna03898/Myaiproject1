from flask import Flask, render_template, request, flash, redirect, url_for
from tests_setups.setups import create_project
import secrets

app = Flask(__name__)
# Generate a secure random secret key
app.secret_key = secrets.token_hex(16)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_project', methods=['POST'])
def handle_project_creation():
    try:
        project_id = request.form['project_id']
        project_info = request.form['project_info']
        
        # Process tables into dictionary
        tables = request.form.getlist('tables[]')
        table_dict = {str(i): table for i, table in enumerate(tables) if table.strip()}

        # Process access dictionary
        access_keys = request.form.getlist('access_keys[]')
        access_values = request.form.getlist('access_values[]')
        access_dict = {str(k): v for k, v in zip(access_keys, access_values) if k and v}

        # Process filters dictionary
        filter_keys = request.form.getlist('filter_keys[]')
        filter_values = request.form.getlist('filter_values[]')
        filters_dict = {str(k): v for k, v in zip(filter_keys, filter_values) if k and v}

        # Process users dictionary
        user_keys = request.form.getlist('user_keys[]')
        user_values = request.form.getlist('user_values[]')
        users_dict = {k: str(v) for k, v in zip(user_keys, user_values) if k and v}

        # Create project in MongoDB
        result = create_project(
            project_id=project_id,
            project_info=project_info,
            table_dict=table_dict,
            access_dict=access_dict,
            filters_dict=filters_dict,
            users_dict=users_dict
        )

        if result:
            flash(f'Project created successfully! ID - {result}', 'success')
        else:
            flash('Failed to create project.', 'error')

    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        print(f"Error details: {str(e)}")  # Add logging for debugging

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=8080)
