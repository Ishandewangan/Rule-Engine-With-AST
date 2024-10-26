import re
from flask import Flask, request, jsonify, render_template
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

class Node:
    def __init__(self, node_type, left=None, right=None, value=None):
        self.node_type = node_type
        self.left = left
        self.right = right
        self.value = value

def create_rule(rule_string):
    tokens = re.findall(r'\w+|[<>]=?|[()]{1}|AND|OR', rule_string)

    def parse_expression(index):
        if index >= len(tokens):
            return None, index

        if tokens[index] == '(':
            index += 1
            left_node, index = parse_expression(index)
            operator = tokens[index]
            index += 1
            right_node, index = parse_expression(index)
            index += 1  # Skip ')'
            return Node("operator", left_node, right_node, operator), index

        elif tokens[index].isalnum() or '=' in tokens[index] or '<' in tokens[index] or '>' in tokens[index]:
            operand = tokens[index]
            index += 1

            if index < len(tokens) and tokens[index] in ('<', '>', '<=', '>='):
                operator = tokens[index]
                index += 1

                if index < len(tokens):
                    right_operand = tokens[index]
                    index += 1

                    return Node("operator", Node("operand", value=operand), Node("operand", value=right_operand), operator), index

            return Node("operand", value=operand), index

        return None, index

    ast, _ = parse_expression(0)
    return ast

def evaluate_rule(ast, data):
    if ast is None:
        return False

    if ast.node_type == "operand":
        if '=' in ast.value:
            key, value = ast.value.split('=')
            key = key.strip()
            value = value.strip().strip('"')
            if key in data:
                return data[key] == value
            return False

        left = ast.value
        if left in data:
            return data[left]

    if ast.node_type == "operator":
        left_eval = evaluate_rule(ast.left, data)
        right_eval = evaluate_rule(ast.right, data)

        if ast.value == "AND":
            return left_eval and right_eval
        elif ast.value == "OR":
            return left_eval or right_eval

    if ast.node_type == "operator" and isinstance(ast.left, Node) and isinstance(ast.right, Node):
        left_value = data.get(ast.left.value)
        right_value = float(ast.right.value)

        if left_value is not None:
            if ast.value == '>':
                return left_value > right_value
            elif ast.value == '<':
                return left_value < right_value
            elif ast.value == '>=':
                return left_value >= right_value
            elif ast.value == '<=':
                return left_value <= right_value

    return False

def combine_rules(rule_strings, combine_type):
    combined_root = None
    for rule in rule_strings:
        ast = create_rule(rule)
        if combined_root is None:
            combined_root = ast
        else:
            combined_root = Node("operator", combined_root, ast, combine_type)  # Combine with the specified type
    return combined_root

app = Flask(__name__)

# Store rules in an in-memory dictionary for simplicity
rules = {}

@app.route('/')
def index():
    return render_template('index.html', rules=rules)

@app.route('/api/rules', methods=['POST'])
def create_rule_endpoint():
    data = request.json
    rule_string = data.get('rule_string')

    if not rule_string:
        return jsonify({"error": "rule_string is required."}), 400

    rule_id = len(rules) + 1
    rules[rule_id] = rule_string

    logging.info(f"Rule created: {rule_id} -> {rule_string}")
    return jsonify({"message": "Rule created successfully!", "rule_id": rule_id}), 201

@app.route('/api/rules/<int:rule_id>', methods=['PUT'])
def update_rule(rule_id):
    if rule_id not in rules:
        return jsonify({"error": "Rule not found"}), 404

    data = request.json
    rule_string = data.get('rule_string')

    if not rule_string:
        return jsonify({"error": "rule_string is required."}), 400

    rules[rule_id] = rule_string

    logging.info(f"Rule updated: {rule_id} -> {rule_string}")
    return jsonify({"message": "Rule updated successfully!"})

@app.route('/api/rules/<int:rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    if rule_id not in rules:
        return jsonify({"error": "Rule not found"}), 404

    del rules[rule_id]
    logging.info(f"Rule deleted: {rule_id}")
    return jsonify({"message": "Rule deleted successfully!"})

@app.route('/api/combine', methods=['POST'])
def combine():
    data = request.json
    rule_ids = data.get('rule_ids')
    combine_type = data.get('combine_type')

    if not rule_ids or not combine_type:
        return jsonify({"error": "Both rule_ids and combine_type are required."}), 400

    # Retrieve rule strings for the selected rule IDs
    rule_strings = [rules[int(rule_id)] for rule_id in rule_ids if int(rule_id) in rules]

    if len(rule_strings) < 2:
        return jsonify({"error": "At least two rules are required to combine."}), 400

    # Combine the selected rules
    combined_ast = combine_rules(rule_strings, combine_type)
    combined_rule_string = f" {combine_type} ".join(rule_strings)

    # Store the combined rule
    combined_rule_id = len(rules) + 1
    rules[combined_rule_id] = combined_rule_string

    logging.info(f"Combined rules: {combined_rule_id} -> {combined_rule_string}")
    return jsonify({"message": "Rules combined successfully!", "combined_rule_id": combined_rule_id}), 201

@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    data = request.json.get("data")
    rule_id = request.json.get("rule_id")

    # Validate rule_id
    try:
        rule_id = int(rule_id)
    except ValueError:
        return jsonify({"result": False}), 400  # Return False on invalid rule ID

    if rule_id not in rules:
        return jsonify({"result": False}), 404  # Return False if rule not found

    rule_string = rules[rule_id]

    # Create the AST for the rule
    try:
        ast = create_rule(rule_string)
    except Exception as e:
        logging.error(f"Error creating AST: {e}")  # Log the error
        return jsonify({"result": False}), 400  # Return False if AST creation fails

    # Evaluate the rule with the given data
    try:
        result = evaluate_rule(ast, data)
    except Exception as e:
        logging.error(f"Error during evaluation: {e}")  # Log the error
        return jsonify({"result": False}), 400  # Return False on evaluation error

    return jsonify({"result": result})  # Returns True or False based on evaluation

@app.route('/api/evaluate/combine', methods=['POST'])
def evaluate_combined():
    data = request.json.get("data")
    rule_ids = request.json.get("rule_ids")
    combine_type = request.json.get("combine_type")

    if not rule_ids or not combine_type:
        return jsonify({"error": "Both rule_ids and combine_type are required."}), 400

    # Retrieve rule strings for the selected rule IDs
    rule_strings = [rules[int(rule_id)] for rule_id in rule_ids if int(rule_id) in rules]

    if len(rule_strings) < 2:
        return jsonify({"error": "At least two rules are required to combine."}), 400

    # Combine the selected rules
    combined_ast = combine_rules(rule_strings, combine_type)

    # Evaluate the combined rule with the given data
    try:
        result = evaluate_rule(combined_ast, data)
    except Exception as e:
        logging.error(f"Error during evaluation: {e}")  # Log the error
        return jsonify({"result": False}), 400  # Return False on evaluation error

    return jsonify({"result": result})  # Returns True or False based on evaluation

if __name__ == '__main__':
    app.run(debug=True)
