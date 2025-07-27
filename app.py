from flask import Flask, request, jsonify, render_template
import requests
import os
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("IBM_API_KEY")
if not API_KEY:
    raise Exception("IBM_API_KEY not found. Check your .env file.")


WATSONX_URL = "https://us-south.ml.cloud.ibm.com/ml/v1/deployments/83cb3407-2dd5-4dbe-b01d-05dd24251ff4/text/generation?version=2021-05-01"

@app.route("/")
def index():
    return render_template("frontpage.html")

def get_access_token():
    iam_url = "https://iam.cloud.ibm.com/identity/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = f"apikey={API_KEY}&grant_type=urn:ibm:params:oauth:grant-type:apikey"
    response = requests.post(iam_url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print("Failed to get access token:", response.text)
        raise Exception(f"Failed to get access token: {response.text}")

@app.route("/explain", methods=["POST"])
def explain_code():
    # Get code from request JSON
    user_input = request.json.get("code")
    print("USER INPUT:", user_input)
    if not user_input or not user_input.strip():
        return jsonify({"error": "No code provided."}), 400

    try:
        token = get_access_token()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
    "parameters": {
        "prompt_variables": {
            "code": user_input
        },
        "decoding_method": "greedy",
        "max_new_tokens": 256
    }
}


    print("PAYLOAD SENT TO WATSONX:", payload)

    response = requests.post(WATSONX_URL, headers=headers, json=payload)
    print("WATSONX RAW RESPONSE:", response.status_code, response.text)

    if response.status_code == 200:
        result = response.json()
        explanation = result.get("results", [{}])[0].get("generated_text", "No explanation generated.")
        return jsonify({"results": [{"generated_text": explanation}]})
    else:
        return jsonify({"error": response.text}), response.status_code

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()  # Load variables from .env
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

