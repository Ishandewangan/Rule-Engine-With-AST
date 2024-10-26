# Rule Engine with AST

A simple web-based rule engine using Flask and AST (Abstract Syntax Tree) for creating, combining, and evaluating rules.

## Features
- **Create Rules**: Define logical rules with conditions and operators.
- **Combine Rules**: Merge rules using `AND` or `OR`.
- **Evaluate Rules**: Test rules with custom JSON data.
- **Edit/Delete Rules**: Update or delete existing rules.

## Requirements
- Python 3.7+
- Flask (see `requirements.txt`)

## Installation
1. **Clone the Repository**:
   ```bash
   git clone <repository_url>
   cd rule-engine-ast
   
2. **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # For Windows: `venv\Scripts\activate`

  3. **Install Dependencies**:
     ```bash
     pip install -r requirements.txt

  4. **Install Dependencies**:
     ```bash
     python app.py

  Open http://127.0.0.1:5000 in your browser to access the UI. 

  ## API Endpoints
- **POST /api/rules**: Create rule
- **PUT /api/rules/{id}**: Update rule
- **DELETE /api/rules/{id}**: Delete rule
- **POST /api/combine**: Combine rules
- **POST /api/evaluate**: Evaluate rule
- **POST /api/evaluate/combine**: Evaluate combined rules

      
