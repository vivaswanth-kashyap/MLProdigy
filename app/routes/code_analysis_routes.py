import os
from dotenv import load_dotenv
from openai import OpenAI
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import esprima

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

code_analysis_routes = Blueprint('code_analysis_routes', __name__)

def static_analysis(code):
    try:
        tree = esprima.parse(code)
        analysis = {
            "num_functions": 0,
            "num_arrow_functions": 0,
            "num_variables": 0,
            "array_operations": [],
            "loops": [],
            "conditionals": 0,
            "unique_identifiers": set()
        }

        def traverse(node):
            if isinstance(node, dict):
                node_type = node.get('type')
                if node_type == 'VariableDeclaration':
                    analysis["num_variables"] += len(node.get('declarations', []))
                    for decl in node.get('declarations', []):
                        if decl.get('id', {}).get('name'):
                            analysis["unique_identifiers"].add(decl['id']['name'])
                elif node_type in ['FunctionDeclaration', 'FunctionExpression']:
                    analysis["num_functions"] += 1
                    if node.get('id', {}).get('name'):
                        analysis["unique_identifiers"].add(node['id']['name'])
                elif node_type == 'ArrowFunctionExpression':
                    analysis["num_arrow_functions"] += 1
                elif node_type == 'CallExpression':
                    callee = node.get('callee', {})
                    if callee.get('type') == 'MemberExpression':
                        prop = callee.get('property', {})
                        if prop.get('name') in ['map', 'filter', 'reduce', 'forEach']:
                            analysis["array_operations"].append(prop.get('name'))
                elif node_type in ['ForStatement', 'WhileStatement', 'DoWhileStatement', 'ForInStatement', 'ForOfStatement']:
                    analysis["loops"].append(node_type)
                elif node_type in ['IfStatement', 'SwitchStatement', 'ConditionalExpression']:
                    analysis["conditionals"] += 1
                elif node_type == 'Identifier':
                    analysis["unique_identifiers"].add(node.get('name'))

                for value in node.values():
                    traverse(value)
            elif isinstance(node, list):
                for item in node:
                    traverse(item)

        traverse(tree)
        analysis["unique_identifiers"] = list(analysis["unique_identifiers"])
        return analysis
    except Exception as e:
        return {"error": f"An error occurred during static analysis: {str(e)}"}

def ai_analysis(code, static_results):
    try:
        prompt = f"""
        Analyze the following JavaScript code and provide insights:
        
        {code}
        
        Static analysis results:
        {static_results}
        
        Please provide a detailed analysis including:
        1. Code quality assessment
        2. Potential improvements and best practices
        3. Performance considerations
        4. Security concerns (if any)
        5. Readability and maintainability suggestions
        6. Any design patterns or anti-patterns identified
        7. Suggestions for error handling and edge cases
        8. Scalability considerations
        
        Format your response as a JSON object with these categories as keys.
        """

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Using GPT-4 for more advanced analysis
            messages=[
                {"role": "system", "content": "You are an expert code analyst providing detailed JavaScript code reviews."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        return {"error": f"An error occurred during AI analysis: {str(e)}"}

@code_analysis_routes.route('/analyze', methods=['POST', 'OPTIONS'])
@cross_origin(origin='http://localhost:3000', methods=['POST', 'OPTIONS'])
def analyze_code():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response

    try:
        print("Received POST request for code analysis")
        data = request.json
        code = data.get('code')
        print(f"Received code: {code[:100]}...")  # Print first 100 characters of code

        if not code or not isinstance(code, str) or code.strip() == '':
            print("Invalid code received")
            return jsonify({"error": "Invalid code. Please provide a non-empty string."}), 400

        print("Performing static analysis")
        static_results = static_analysis(code)
        print(f"Static analysis results: {static_results}")

        print("Performing AI analysis")
        ai_results = ai_analysis(code, static_results)
        print(f"AI analysis results: {ai_results[:100]}...")  # Print first 100 characters of AI results

        combined_analysis = {
            "static_analysis": static_results,
            "ai_analysis": ai_results
        }

        print("Sending combined analysis")
        return jsonify(combined_analysis)
    except Exception as error:
        print(f"Error in POST /analyze: {error}")
        return jsonify({
            "error": "An error occurred while analyzing the code.",
            "details": str(error)
        }), 500