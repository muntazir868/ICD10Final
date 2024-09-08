from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
import logging
from bson import ObjectId
from databasemanager import DatabaseManager
from rulebaseapp import RulebaseApp
import datetime
import logging
import os
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Set a secret key for the session
app.secret_key = 'your_secret_key_here'  # Replace with a unique and secret key

# Configure logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# Initialize MongoDB client and access the Project1 database
try:
    db_manager = DatabaseManager('mongodb://172.16.105.132:27017/', 'ExpertSystem')
    rulebase_app = RulebaseApp(db_manager)
    lab_input_user_values_collection = db_manager.get_collection('User_Input_Lab_Values')
except Exception as e:
    app.logger.error(f"Error connecting to MongoDB: {e}")
    exit(1)

class Controller:
    """
    Controller class that handles the routing and logic for the Flask application.
    """

    @staticmethod
    @app.route('/')
    def index():
        """
        Renders the index page.
        """
        return render_template('index.html')

    @staticmethod
    @app.route('/about')
    def about():
        """
        Renders the about page.
        """
        return render_template('about.html')

    @staticmethod
    @app.route('/rulebase', methods=['GET', 'POST'])
    def rulebase():
        """
        Handles the rulebase page.
        - GET: Renders the rulebase page with mappings and ICD mappings.
        - POST: Saves the rulebase data and returns the result.
        """
        if request.method == 'POST':
            result = db_manager.save_rulebase(request)
            return jsonify(result), 200 if result['status'] == 'success' else 500

        # Fetch mappings JSON for GET request -- these are the mappings for the ICD names and their codes
        mappings_path = os.path.join(app.root_path, 'static', 'mappings.json')
        icd_mappings_path = os.path.join(app.root_path, 'static', 'sortedIcdMappings.json')

        with open(mappings_path, 'r') as mappings_file:
            mappings = json.load(mappings_file)

        with open(icd_mappings_path, 'r') as icd_mappings_file:
            icd_mappings = json.load(icd_mappings_file)

        return render_template('rulebase.html', mappings=mappings, icd_mappings=icd_mappings)
        
    @staticmethod
    @app.route('/lab_values', methods=['GET', 'POST'])
    def lab_values():
        """
        Handles the lab values page.
        - GET: Renders the lab values page.
        - POST: Saves the lab values data and returns the result.
        """
        if request.method == 'POST':
            result = db_manager.save_lab_values(request)
            return jsonify(result), 200 if result['status'] == 'success' else 500
        return render_template('lab_values.html')

    @staticmethod
    @app.route('/view_rulebase', methods=['GET'])
    def view_rulebase():
        """
        Renders the view rulebase page with all rules fetched from the database.
        """
        try:
            rules = rulebase_app.get_all_rules()
            return render_template('view_rulebase.html', rules=rules)
        except Exception as e:
            app.logger.error(f"Error fetching rules: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @staticmethod
    @app.route('/delete_rule/<disease_code>', methods=['POST'])
    def delete_rule(disease_code):
        """
        Deletes a rule based on the disease code and redirects to the view rulebase page.
        """
        try:
            rulebase_app.delete_rule(disease_code)
            return redirect(url_for('view_rulebase'))
        except Exception as e:
            app.logger.error(f"Error deleting rule: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/view_patient_data', methods=['GET', 'POST'])
def view_patient_data():
    """
    Handles the view patient data page.
    - GET: Renders the view patient data page with all patient data.
    - POST: Searches for a specific patient by ID and renders the page with the found patient data.
    """
    try:
        # Fetch all patient data from the User_Input_Lab_Values collection
        patient_data = list(lab_input_user_values_collection.find())
        
        # Sort patient data by patient ID
        patient_data.sort(key=lambda x: x['patient_id'])

        if request.method == 'POST':
            patient_id = request.form.get('patient_id')
            if patient_id:
                # Perform binary search to find the patient
                def binary_search(arr, target):
                    low, high = 0, len(arr) - 1
                    while low <= high:
                        mid = (low + high) // 2
                        if arr[mid]['patient_id'] == target:
                            return arr[mid]
                        elif arr[mid]['patient_id'] < target:
                            low = mid + 1
                        else:
                            high = mid - 1
                    return None
                
                found_patient = binary_search(patient_data, patient_id)
                if found_patient:
                    return render_template('view_patient_data.html', patient_data=[found_patient])
                else:
                    return render_template('view_patient_data.html', patient_data=[], message=f"Patient with ID {patient_id} not found.")

        return render_template('view_patient_data.html', patient_data=patient_data)
    except Exception as e:
        app.logger.error(f"Error fetching patient data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@app.route('/edit_rule/<rule_id>', methods=['GET'])
def edit_rule(rule_id):
    rule = rulebase_app.get_rule_by_id(rule_id)
    if rule:
        # Fetch mappings JSON for GET request -- these are the mappings for the ICD names and their codes
        mappings_path = os.path.join(app.root_path, 'static', 'mappings.json')
        icd_mappings_path = os.path.join(app.root_path, 'static', 'sortedIcdMappings.json')

        with open(mappings_path, 'r') as mappings_file:
            mappings = json.load(mappings_file)

        with open(icd_mappings_path, 'r') as icd_mappings_file:
            icd_mappings = json.load(icd_mappings_file)

        return render_template('edit_rule.html', rule=rule, mappings=mappings, icd_mappings=icd_mappings)
    else:
        flash('Rule not found', 'error')
        return redirect(url_for('view_rulebase'))
    
@app.route('/update_rule/<rule_id>', methods=['POST'])
def update_rule(rule_id):
    rule = rulebase_app.get_rule_by_id(rule_id)
    if not rule:
        flash('Rule not found', 'error')
        return redirect(url_for('view_rulebase'))

    # Update the rule with the form data
    rule.category = request.form['category']
    rule.disease_codes = request.form.getlist('disease_codes[]')
    rule.disease_names = request.form.getlist('disease_names[]')

    # Clear existing rules and conditions
    rule.rules = []

    # Iterate over the rules and conditions
    rule_count = len(request.form.getlist('conditions[1][]'))
    for rule_index in range(1, rule_count + 1):
        conditions = request.form.getlist(f'conditions[{rule_index}][]')
        parameters = request.form.getlist(f'parameters[{rule_index}][]')
        units = request.form.getlist(f'units[{rule_index}][]')
        age_min = request.form.getlist(f'age_min[{rule_index}][]')
        age_max = request.form.getlist(f'age_max[{rule_index}][]')
        genders = request.form.getlist(f'genders[{rule_index}][]')

        rule_entry = {
            'conditions': [],
            'rule_id': rule_index
        }

        for condition_index in range(len(conditions)):
            condition = {
                'type': conditions[condition_index],
                'parameter': parameters[condition_index],
                'unit': units[condition_index],
                'age_min': age_min[condition_index],
                'age_max': age_max[condition_index],
                'gender': genders[condition_index]
            }

            if conditions[condition_index] == 'range':
                condition['min_value'] = request.form.getlist(f'min_values[{rule_index}][]')[condition_index]
                condition['max_value'] = request.form.getlist(f'max_values[{rule_index}][]')[condition_index]
            elif conditions[condition_index] == 'comparison':
                condition['operator'] = request.form.getlist(f'operators[{rule_index}][]')[condition_index]
                condition['comparison_value'] = request.form.getlist(f'comparison_values[{rule_index}][]')[condition_index]
            elif conditions[condition_index] == 'time-dependent':
                condition['operator'] = request.form.getlist(f'operators[{rule_index}][]')[condition_index]
                condition['comparison_time_value'] = request.form.getlist(f'comparison_time_values[{rule_index}][]')[condition_index]
                condition['time'] = request.form.getlist(f'time_values[{rule_index}][]')[condition_index]

            rule_entry['conditions'].append(condition)

        rule.rules.append(rule_entry)

    # Save the updated rule
    result = rulebase_app.update_rule(rule_id, rule.category, rule.disease_names, rule.disease_codes, rule.rules)
    if result['status'] == 'success':
        flash('Rule updated successfully', 'success')
    else:
        flash('Failed to update rule', 'error')

    return redirect(url_for('view_rulebase'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)