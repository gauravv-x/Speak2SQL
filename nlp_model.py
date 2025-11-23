import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Load environment variables from .env file
load_dotenv()

def text_to_sql(query_text, table_name):
    """
    Convert a natural language query to SQL using Hugging Face Inference API.
    
    Args:
        query_text (str): Natural language query (e.g., "Show all employees where age > 30")
        table_name (str): Name of the MySQL table (e.g., "employees")
    
    Returns:
        str: Generated SQL query
    """
    # Initialize Hugging Face Inference Client with API key
    api_key = os.getenv('HF_API_KEY')
    if not api_key:
        raise ValueError('Hugging Face API key not found. Set HF_API_KEY in .env file.')
    
    client = InferenceClient(api_key=api_key)
    
    # Create prompt for text-to-SQL
    prompt = (
        f"Convert the following natural language query to SQL for a table named '{table_name}': "
        f"{query_text}. Ensure the SQL is valid and uses backticks for table and column names."
    )
    
    try:
        # Call Hugging Face Inference API
        response = client.text_generation(
            prompt,
            model='t5-small'  # Placeholder; replace with a text-to-SQL model if available
        )
        sql_query = response.strip()
        
        # Basic validation to ensure the response is a SQL query
        if not sql_query.upper().startswith('SELECT'):
            raise ValueError('Generated SQL is invalid or not a SELECT query')
        
        return sql_query
    except Exception as e:
        raise ValueError(f'Hugging Face API error: {str(e)}')