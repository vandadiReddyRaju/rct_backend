from flask import Flask, request, jsonify
from flask_cors import CORS
from helpers import llm_call, llm_call_with_image  # import needed functions

app = Flask(__name__)
CORS(app)

@app.route('/run-api', methods=['POST'])
def run_api():
    data = request.get_json()

    system_prompt = data.get("system_prompt")
    user_prompt = data.get("user_prompt")
    # optional: base64 images
    images = data.get("images", [])

    try:
        # Choose the correct function based on your inputs
        if images:
            result = llm_call_with_image(system_prompt, user_prompt, images)
        else:
            result = llm_call(system_prompt, user_prompt)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)