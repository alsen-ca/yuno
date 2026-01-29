from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

client = MongoClient("mongodb://faqman-db:27017/")
db = client["faqman"]
qas = list(db.qas.find({}))
tags = list(db.tags.find({}))

def weighted_question_text(qa):
    tokens = []
    for item in qa["question_weights"]:
        count = int(round(item["weight"]))
        tokens.extend([item["word"]] * count)
    return " ".join(tokens)
documents = [
    weighted_question_text(qa) + " " + qa["answer"]
    for qa in qas
]


# Feature extraction
vectorizer = TfidfVectorizer()
X_docs = vectorizer.fit_transform(documents)

tag_id_to_name = {tag["_id"]: tag["en_og"].lower() for tag in tags}

def tag_boost(query, qas, boost_value=0.3):
    query = query.lower()
    boosts = np.zeros(len(qas))

    for i, qa in enumerate(qas):
        for tag_id in qa.get("tag_ids", []):
            tag_name = tag_id_to_name.get(tag_id)
            if tag_name and tag_name in query:
                boosts[i] += boost_value
                break

    return boosts

def find_similar(question, top_n=5, tag_boost_value=0.3):
    X_query = vectorizer.transform([question])
    text_sim = cosine_similarity(X_query, X_docs)[0]

    non_zero_idx = np.where(text_sim > 0)[0]
    if len(non_zero_idx) == 0:
        return []

    # 4. Apply tag boost only to non-zero text similarity QAs
    boosts = np.zeros(len(text_sim))
    for i in non_zero_idx:
        for tag_id in qas[i].get("tag_ids", []):
            tag_name = tag_id_to_name.get(tag_id)
            if tag_name and tag_name.lower() in question.lower():
                boosts[i] += tag_boost_value
                break

    final_scores = text_sim + boosts
    # Sort and pick top N
    sorted_idx = non_zero_idx[np.argsort(final_scores[non_zero_idx])[::-1]]
    top_idx = sorted_idx[:top_n]

    return [(qas[i], final_scores[i] * 100) for i in top_idx]



while True:
    q = input("Ask a question (or 'quit'): ")
    if q.lower() == "quit":
        break

    results = find_similar(q)
    for i, (qa, score) in enumerate(results, 1):
        print(f"{i}. ({score:.2f}%)")
        print(f"Q: {qa['question']}")
        print(f"A: {qa['answer']}\n")

