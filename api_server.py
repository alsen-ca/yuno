from flask import Flask, request, jsonify
from qa_engine import QACore

app = Flask(__name__)
qa_core = QACore("data_qa")

@app.route("/query", methods=["POST"])
def handle_query():
    data = request.get_json()
    query = data.get("query", "")
    results = qa_core.find_matches(query)
    response = []
    for pct, entry in results:
        response.append({
            "question": entry.get("question"),
            "answer": entry.get("answer"),
            "match": pct
        })
    return jsonify({"results": response})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
