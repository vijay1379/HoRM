from flask import Flask, render_template, send_from_directory, request, redirect, url_for, jsonify, flash, session
import os
import pandas as pd
import json
import requests

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'  # Change this in production

# Vercel compatibility: Expose app as the WSGI application
application = app

# Flask will automatically look for templates in 'templates/' and static files in 'static/'

def load_attendance_data():
    """Load and process attendance data from CSV"""
    try:
        # Use absolute path for Vercel compatibility
        csv_path = os.path.join(os.path.dirname(__file__), 'data', 'processed_attendance.csv')
        df = pd.read_csv(csv_path)
        
        # Clean and prepare the data
        employees = []
        for _, row in df.iterrows():
            # Convert efficiency to percentage if it's in decimal
            efficiency = float(row['efficiency'])
            if efficiency <= 1:
                efficiency = efficiency * 100
            
            # Convert punctuality to percentage if it's in decimal
            punctuality = float(row['punctuality'])
            if punctuality <= 1:
                punctuality = punctuality * 100
            
            # Calculate attendance rate (assuming 100% - absenteeism)
            attendance = 100 - (float(row['absenteeism_days']) * 2)  # Rough calculation
            attendance = max(0, min(100, attendance))  # Ensure it's between 0-100
            
            # Use the actual name from the CSV
            name = row['Name'] if pd.notna(row['Name']) else f"Employee {row['Fake_Id']}"
            
            # Create monthly performance data (simulated based on efficiency)
            base_score = efficiency
            monthly = []
            for i in range(12):
                # Add some variance around the base efficiency
                variance = (i % 3 - 1) * 5  # ±5 variance
                score = max(60, min(100, base_score + variance))
                monthly.append(int(score))
            
            # Map CSV clusters to website display clusters based on new order
            # CSV: 0=Consistent Performer, 1=Late Starter, 2=Erratic/At-Risk, 3=Silent Overworker
            # Website: 1=Consistent Performer(Green), 2=Silent Overworker(Orange), 3=Late Starter(Orange), 4=Erratic/At-Risk(Red)
            csv_cluster = int(row['Cluster'])
            cluster_mapping = {
                0: 1,  # Consistent Performer → Website Cluster 1 (Green)
                1: 3,  # Late Starter → Website Cluster 3 (Orange)
                2: 4,  # Erratic / At-Risk → Website Cluster 4 (Red)
                3: 2   # Silent Overworker → Website Cluster 2 (Orange)
            }
            
            # Extract work hours data - use the numeric columns, not the time-formatted ones
            cafeteria_hours = float(row.get('cafeteria_hours', 0))
            ooo_hours = float(row.get('avg_ooo_hours', 0))
            office_hours = float(row.get('avg_office_hours', 0))
            break_hours = float(row.get('avg_break_hours', 0))
            
            # Extract absenteeism and burnout data for risk assessment
            absenteeism_days = float(row.get('absenteeism_days', 0))
            burnout_hours = float(row.get('burnout_hours', 0))
            
            employee = {
                'id': str(row['Fake_Id']),
                'name': name,
                'designation': row['Designation'],
                'efficiency': int(efficiency),
                'attendance': int(attendance),
                'bayHours': round(float(row['bay_hours']), 1),
                'cafeteriaHours': cafeteria_hours,
                'oooHours': ooo_hours,
                'officeHours': office_hours,
                'breakHours': break_hours,
                'score': int(efficiency),  # Performance score is based on efficiency
                'trend': 5 if efficiency > 75 else -2,  # Simple trend calculation
                'cluster': cluster_mapping[csv_cluster],  # Map CSV cluster to website cluster
                'clusterType': row['Behavior_Type'],  # Use the actual behavior type from CSV
                'punctuality': int(punctuality),
                'monthly': monthly,
                'accountCode': row['Account_code'],
                'recruitment_type': row['Recruitment_Type'],
                'absenteeism_days': absenteeism_days,  # Required for risk assessment
                'burnout_hours': burnout_hours  # Required for risk assessment
            }
            employees.append(employee)
        
        return employees
    except Exception as e:
        import traceback
        print(f"Error loading CSV data: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        # Return mock data as fallback
        return [
            {
                'id': '789012', 'name': 'John Doe', 'designation': 'Senior Software Engineer',
                'efficiency': 92, 'attendance': 95, 'bayHours': 7.5, 'cafeteriaHours': 0.5, 'oooHours': 0.8,
                'officeHours': 8.0, 'breakHours': 1.0, 'score': 85, 'trend': 5, 
                'cluster': 2, 'clusterType': 'Consistent Performer', 'punctuality': 95,
                'monthly': [82, 88, 85, 90, 85, 88, 92, 85, 80, 88, 85, 90]
            }
        ]

@app.route('/')
def index():
    """Serve the main index page"""
    return render_template('index.html')

@app.route('/index.html')
def index_html():
    """Serve index.html directly"""
    return render_template('index.html')

@app.route('/login.html')
def login():
    """Serve the login page"""
    return render_template('login.html')

@app.route('/test_filters.html')
def test_filters():
    """Serve the filter test page"""
    return send_from_directory('.', 'test_filters.html')

@app.route('/dashboard.html')
def dashboard():
    """Serve the dashboard page - requires authentication"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/employee-view.html')
def employee_view():
    """Serve the employee view page - requires authentication"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('employee-view.html')

@app.route('/api/employees')
def get_employees():
    """API endpoint to get all employee data"""
    employees = load_attendance_data()
    return jsonify(employees)

@app.route('/api/employee/<employee_id>')
def get_employee(employee_id):
    """API endpoint to get specific employee data"""
    employees = load_attendance_data()
    employee = next((emp for emp in employees if emp['id'] == employee_id), None)
    if employee:
        return jsonify(employee)
    return jsonify({'error': 'Employee not found'}), 404

@app.route('/api/search_employee')
def search_employee():
    """API endpoint to search employees by ID or name"""
    query = request.args.get('q', '').lower()
    employees = load_attendance_data()
    
    if not query:
        return jsonify({'error': 'Query parameter required'}), 400
    
    # Search by ID or name
    matching_employees = []
    for emp in employees:
        if (query in emp['id'].lower() or 
            query in emp['name'].lower() or 
            query in emp['designation'].lower() or
            query == emp['id'].lower()):  # Exact ID match
            matching_employees.append(emp)
    
    return jsonify(matching_employees)

@app.route('/api/organization_data')
def get_organization_data():
    """API endpoint to get organization-level aggregated data"""
    try:
        # Use absolute path for Vercel compatibility
        csv_path = os.path.join(os.path.dirname(__file__), 'data', 'processed_attendance.csv')
        df = pd.read_csv(csv_path)
        
        # Group by department (using a combination of designation and account code)
        department_data = []
        
        # Group by designation for department-level analysis
        grouped = df.groupby(['Designation', 'Account_code']).agg({
            'Fake_Id': 'count',  # Employee count
            'efficiency': 'mean',
            'punctuality': 'mean',
            'bay_hours': 'mean',
            'absenteeism_days': 'mean',
            'Cluster': 'mode'
        }).reset_index()
        
        for _, row in grouped.iterrows():
            # Calculate department name based on designation
            dept_name = {
                'AL': 'Management',
                'TDS': 'Technical Delivery',
                'SSE': 'Senior Engineering',
                'SE': 'Software Engineering'
            }.get(row['Designation'], 'Other')
            
            efficiency = float(row['efficiency'])
            if efficiency <= 1:
                efficiency = efficiency * 100
                
            punctuality = float(row['punctuality'])
            if punctuality <= 1:
                punctuality = punctuality * 100
            
            # Calculate attendance rate
            attendance = max(0, min(100, 100 - (float(row['absenteeism_days']) * 2)))
            
            # Determine burnout risk
            burnout_risk = 'Low'
            if efficiency < 60 or attendance < 85:
                burnout_risk = 'High'
            elif efficiency < 75 or attendance < 90:
                burnout_risk = 'Medium'
            
            dept_data = {
                'name': f"{dept_name} ({row['Account_code']})",
                'accountCode': row['Account_code'],
                'designation': row['Designation'],
                'employees': int(row['Fake_Id']),
                'efficiency': int(efficiency),
                'attendance': int(attendance),
                'burnoutRisk': burnout_risk
            }
            department_data.append(dept_data)
        
        return jsonify(department_data)
        
    except Exception as e:
        print(f"Error loading organization data: {e}")
        # Return mock data as fallback
        return jsonify([
            {'name': 'IT Development (TM)', 'accountCode': 'TM', 'designation': 'SSE', 'employees': 45, 'efficiency': 88, 'attendance': 96, 'burnoutRisk': 'Low'},
            {'name': 'HR (TM)', 'accountCode': 'TM', 'designation': 'AL', 'employees': 12, 'efficiency': 92, 'attendance': 98, 'burnoutRisk': 'Low'}
        ])

@app.route('/api/recommendations/<employee_id>')
def get_recommendations(employee_id):
    """API endpoint to get personalized recommendations for an employee"""
    try:
        # Get employee data
        employees = load_attendance_data()
        employee = next((emp for emp in employees if emp['id'] == employee_id), None)
        
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        # Integrate with Gemini API for AI-powered recommendations
        try:
            gemini_recommendations = call_gemini_api(employee)
            if gemini_recommendations:
                return jsonify(gemini_recommendations)
        except Exception as e:
            print(f"Gemini API call failed: {e}")
        
        # Return empty to trigger client-side intelligent recommendations as fallback
        return jsonify([]), 204
        
    except Exception as e:
        print(f"Error getting recommendations for employee {employee_id}: {e}")
        return jsonify({'error': 'Unable to generate recommendations'}), 500

def generate_llm_recommendations(behavior_type, metrics, cluster_avg=None):
    """
    Generate 3 concise HR recommendations using Gemini API (REST request),
    ensuring the output is a JSON object.
    """
    # Get API key from environment variable
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY not found in environment variables")
        return "❌ API key not configured. Please set GEMINI_API_KEY environment variable."

    # Gemini model endpoint - Using 'gemini-2.0-flash-exp' for structured output
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

    # Build dynamic, context-rich prompt
    emp_lines = "\n".join([f"- {k.replace('_',' ').title()}: {v}" for k, v in metrics.items()])
    cluster_lines = ""
    if cluster_avg:
        cluster_lines = "\n".join([f"- {k.replace('_',' ').title()}: {v}" for k, v in cluster_avg.items()])

    # REVISED PROMPT for short, crisp recommendations
    prompt = f"""
    You are an HR analyst. Create 3 brief Next Best Actions for this employee.

    Behavior Cluster: {behavior_type}

    Employee Metrics:
    {emp_lines}

    Cluster Averages (Peer Group):
    {cluster_lines}

    Guidelines:
    - Provide EXACTLY 3 recommendations
    - For each recommendation:
        * Start with an emoji (✅,💬,🔍,🚀,📈)
        * Give a short action point (max 6-8 words)
        * Follow with "Why:" and a brief explanation
    - Be direct, specific and actionable
    - Focus on: coaching, wellness, recognition, or workload
    
    Format for each point:
    [emoji] [Action point]
    Why: [Brief explanation of why this action is recommended]
    
    IMPORTANT: Follow this format strictly for all 3 points.
    """

    # Prepare payload for Gemini
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY
    }

    # Send request to Gemini
    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        response.raise_for_status()
        result = response.json()

        # Extract model text response
        if "candidates" in result and len(result["candidates"]) > 0:
            # Get the text response which should be 3 recommendations
            response_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            return response_text
        else:
            return "⚠️ No valid response from Gemini model."
    except Exception as e:
        return f"❌ Gemini API Error: {str(e)}"

def call_gemini_api(employee_data):
    """
    Function to call Gemini API for generating personalized recommendations
    """
    try:
        # Prepare metrics dictionary from employee data
        metrics = {
            'efficiency': f"{employee_data.get('efficiency', 0)}%",
            'attendance': f"{employee_data.get('attendance', 0)}%",
            'bay_hours': f"{employee_data.get('bayHours', 0)} hrs/day",
            'punctuality': f"{employee_data.get('punctuality', 0)}%",
            'designation': employee_data.get('designation', 'Unknown'),
            'performance_score': employee_data.get('score', 0)
        }
        
        behavior_type = employee_data.get('clusterType', 'Unknown')
        
        # Get cluster averages (simplified for now)
        cluster_avg = {
            'efficiency': '85%',
            'attendance': '90%',
            'bay_hours': '7.5 hrs/day',
            'punctuality': '88%'
        }
        
        # Call the LLM recommendations function
        raw_recommendations = generate_llm_recommendations(behavior_type, metrics, cluster_avg)
        
        if raw_recommendations and not raw_recommendations.startswith('❌') and not raw_recommendations.startswith('⚠️'):
            # Parse the text response into structured recommendations
            structured_recommendations = parse_gemini_text_to_json(raw_recommendations)
            
            if structured_recommendations:
                print(f"Generated {len(structured_recommendations)} Gemini recommendations for {employee_data.get('name', 'Unknown')}")
                return structured_recommendations
        
        print(f"Gemini API response: {raw_recommendations}")
        return None
        
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

def parse_gemini_text_to_json(text_response):
    """
    Parse Gemini text response into structured JSON format for the frontend
    """
    try:
        lines = text_response.strip().split('\n')
        recommendations = []
        
        current_rec = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line starts with an emoji (new recommendation)
            if any(emoji in line[:3] for emoji in ['✅', '💬', '🔍', '🚀', '📈', '⚡', '🎯', '💡', '🔥', '⭐']):
                # Save previous recommendation if exists
                if current_rec:
                    recommendations.append(current_rec)
                
                # Start new recommendation
                emoji = line[0] if line[0] in '✅💬🔍🚀📈⚡🎯💡🔥⭐' else '💡'
                title = line[1:].strip()
                
                # Map emoji to FontAwesome icon
                icon_mapping = {
                    '✅': 'fas fa-check-circle',
                    '💬': 'fas fa-comments',
                    '🔍': 'fas fa-search',
                    '🚀': 'fas fa-rocket',
                    '📈': 'fas fa-chart-line',
                    '⚡': 'fas fa-bolt',
                    '🎯': 'fas fa-target',
                    '💡': 'fas fa-lightbulb',
                    '🔥': 'fas fa-fire',
                    '⭐': 'fas fa-star'
                }
                
                current_rec = {
                    'icon': icon_mapping.get(emoji, 'fas fa-lightbulb'),
                    'title': title,
                    'description': '',
                    'priority': 'medium'  # Default priority
                }
                
            elif line.startswith('Why:') and current_rec:
                # Add description
                current_rec['description'] = line.replace('Why:', '').strip()
                
                # Determine priority based on keywords
                desc_lower = current_rec['description'].lower()
                if any(word in desc_lower for word in ['urgent', 'critical', 'immediate', 'risk', 'low performance']):
                    current_rec['priority'] = 'high'
                elif any(word in desc_lower for word in ['improve', 'enhance', 'develop', 'training']):
                    current_rec['priority'] = 'medium'
                else:
                    current_rec['priority'] = 'low'
        
        # Don't forget the last recommendation
        if current_rec:
            recommendations.append(current_rec)
        
        # Ensure we have valid recommendations
        valid_recommendations = []
        for rec in recommendations:
            if rec.get('title') and rec.get('description'):
                valid_recommendations.append(rec)
        
        return valid_recommendations[:4]  # Limit to 4 recommendations
        
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        return None

@app.route('/organisation-view.html')
def organisation_view():
    """Redirect to employee view since organization view is now integrated"""
    return redirect(url_for('employee_view'))

# Handle form submissions from login page
@app.route('/login', methods=['POST'])
def handle_login():
    """Handle login form submission with authentication"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Simple authentication - username: admin, password: password
    if username == 'admin' and password == 'password':
        session['logged_in'] = True
        session['username'] = username
        return redirect(url_for('dashboard'))
    else:
        # Authentication failed
        return render_template('login.html', error='Invalid username or password. Use admin/password to login.')

@app.route('/logout')
def logout():
    """Handle user logout"""
    session.clear()
    return redirect(url_for('index'))

# Vercel will handle the server startup, but keep this for local development
if __name__ == '__main__':
    
    # Use environment variable for port (Vercel compatibility)
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)