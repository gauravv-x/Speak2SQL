from flask import Flask, render_template, request, jsonify
import mysql.connector
import pandas as pd
import os
import speech_recognition as sr
from nlp_model import text_to_sql
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'Uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# MySQL Configuration
db_config = {
    'user': 'root',
    'password': 'password',
    'host': 'localhost',
    'database': 'speak2query'
}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Connect to MySQL
def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if file and file.filename.endswith('.csv'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            # Read CSV with flexible parsing
            df = pd.read_csv(file_path, encoding='utf-8', sep=',', on_bad_lines='skip')
            
            # Clean data: drop rows with NaN or incorrect column counts
            df = df.dropna(how='all')  # Drop fully empty rows
            expected_columns = len(df.columns)
            df = df[df.apply(lambda row: len(row) == expected_columns, axis=1)]
            
            if df.empty:
                return jsonify({'error': 'CSV file is empty or contains no valid data'}), 400

            table_name = filename.split('.')[0].replace(' ', '_')
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Drop existing table to avoid conflicts
            cursor.execute(f'DROP TABLE IF EXISTS `{table_name}`')
            
            # Create table
            columns = ', '.join([f'`{col}` VARCHAR(255)' for col in df.columns])
            create_table_query = f'CREATE TABLE `{table_name}` ({columns})'
            cursor.execute(create_table_query)
            
            # Insert data
            for _, row in df.iterrows():
                if len(row) != expected_columns:
                    continue  # Skip invalid rows
                placeholders = ', '.join(['%s'] * len(row))
                insert_query = f'INSERT INTO `{table_name}` VALUES ({placeholders})'
                cursor.execute(insert_query, tuple(row.fillna('')))  # Replace NaN with empty string
            
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'message': 'File uploaded and table created', 'table_name': table_name})
        except pd.errors.ParserError as e:
            return jsonify({'error': f'CSV parsing failed: {str(e)}'}), 400
        except mysql.connector.Error as e:
            return jsonify({'error': f'MySQL error: {str(e)}'}), 500
    return jsonify({'error': 'Invalid file format'}), 400

@app.route('/query', methods=['POST'])
def process_query():
    input_type = request.form.get('input_type')
    table_name = request.form.get('table_name')
    
    if input_type == 'speech':
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                audio = recognizer.listen(source, timeout=5)
                query_text = recognizer.recognize_google(audio)
            except sr.UnknownValueError:
                return jsonify({'error': 'Could not understand speech'}), 400
            except sr.RequestError:
                return jsonify({'error': 'Speech recognition service unavailable'}), 500
    else:
        query_text = request.form.get('text_query')
        if not query_text:
            return jsonify({'error': 'Text query is empty'}), 400
    
    # Convert natural language to SQL
    try:
        sql_query = text_to_sql(query_text, table_name)
    except Exception as e:
        return jsonify({'error': f'NLP processing failed: {str(e)}'}), 500
    
    # Execute SQL query
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()
        return jsonify({'columns': columns, 'results': results, 'sql_query': sql_query})
    except mysql.connector.Error as e:
        return jsonify({'error': f'SQL error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)