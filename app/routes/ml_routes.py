from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import esprima

ml_routes = Blueprint('ml_routes', __name__)


def analyze_code(code):
    try:
        tree = esprima.parse(code)
        analysis = {
            "num_functions": 0,
            "num_arrow_functions": 0,
            "num_variables": 0,
            "array_operations": [],
            "suggestions": []
        }

        def traverse(node):
            if isinstance(node, dict):
                if node.get('type') == 'VariableDeclaration':
                    analysis["num_variables"] += len(node.get('declarations', []))
                elif node.get('type') == 'FunctionDeclaration':
                    analysis["num_functions"] += 1
                elif node.get('type') == 'ArrowFunctionExpression':
                    analysis["num_arrow_functions"] += 1
                elif node.get('type') == 'CallExpression':
                    callee = node.get('callee', {})
                    if callee.get('type') == 'MemberExpression':
                        prop = callee.get('property', {})
                        if prop.get('name') in ['map', 'filter', 'reduce', 'forEach']:
                            analysis["array_operations"].append(prop.get('name'))

                for value in node.values():
                    traverse(value)
            elif isinstance(node, list):
                for item in node:
                    traverse(item)

        traverse(tree)

        # Generate suggestions
        if 'map' in analysis["array_operations"] and not any(op in analysis["array_operations"] for op in ['filter', 'reduce']):
            analysis["suggestions"].append("Consider using 'filter' or 'reduce' for more complex array transformations.")
        
        if analysis["num_arrow_functions"] > 0:
            analysis["suggestions"].append("Good use of arrow functions! They're great for short, simple functions.")
        
        if not analysis["array_operations"]:
            analysis["suggestions"].append("Consider using array methods like map, filter, or reduce for more functional programming style.")

        return analysis
    except Exception as e:
        return {"error": f"An error occurred while analyzing the code: {str(e)}"}

@ml_routes.route('/analyze-code', methods=['POST', 'OPTIONS'])
@cross_origin(origins=['http://localhost:3000'], methods=['POST', 'OPTIONS'])
def analyze_code_route():
    if request.method == 'OPTIONS':
        # Preflight request. Reply successfully:
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    code = request.json.get('code')
    if not code:
        return jsonify({"error": "No code provided"}), 400
    
    analysis = analyze_code(code)
    return jsonify(analysis)