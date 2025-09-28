import os
import json

class QAEngine:
    WEIGHT_MIN = 0.2
    WEIGHT_MAX = 4.0
    WEIGHT_STEP = 0.2

    SYNONYMS = {
        "create": ["new", "add"],
        "new": ["create", "add"],
        "app": ["application"],
        "application": ["app"],
        "repo": ["repository"],
        "repository": ["repo"]
    }

    def __init__(self, folderpath):
        self.folderpath = folderpath
        self.qa_list = self.load_qa_folder(folderpath)

    def load_qa_folder(self, folderpath):
        qa_list = []
        for filename in os.listdir(folderpath):
            if filename.endswith(".json"):
                filepath = os.path.join(folderpath, filename)
                qa_list.extend(self.load_qa_file(filepath))
        return qa_list

    def load_qa_file(self, filepath):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                for entry in data:
                    if "weights" not in entry:
                        entry["weights"] = {w:1.0 for w in entry["question"].lower().split()}
                return data
        except Exception:
            return []

    def score(self, query, entry):
        query_words = query.lower().split()
        weights = entry.get("weights", {})
        #return sum(weights.get(w,0) for w in query_words)

        score = 0
        for word in query_words:
            # exact match
            score += weights.get(word, 0)
            # check synonyms
            for syn in self.SYNONYMS.get(word, []):
                score += weights.get(syn, 0)
        return score

    def find_matches(self, query, top_n, qa_list=None):
        if qa_list is None:
            qa_list = self.qa_list

        scored = [(self.score(query, entry), entry) for entry in qa_list if self.score(query, entry) > 0]
        if not scored:
            return []

        scored.sort(key=lambda x: x[0], reverse=True)
        max_score = scored[0][0]
        results = []
        for s, entry in scored[:top_n]:
            pct = round((s/max_score)*100, 1)
            results.append((pct, entry))
        return results


    def update_weights(self, feedback_list):
        """
        feedback_list: list of tuples (entry, +1/-1, query_words)
        Only updates weights for keywords in the query.
        """
        for entry, fb, query_words in feedback_list:
            if "weights" not in entry:
                entry["weights"] = {}
            for w in query_words:
                old_w = entry["weights"].get(w,1.0)
                delta = self.WEIGHT_STEP
                if fb > 0:
                    new_w = min(self.WEIGHT_MAX, old_w + delta)
                else:
                    new_w = max(self.WEIGHT_MIN, old_w - delta)
                entry["weights"][w] = new_w

        # Persist changes to JSON files by topic
        topic_map = {}
        for entry in self.qa_list:
            topic = entry.get("topic","default")
            topic_map.setdefault(topic,[]).append(entry)
        for topic, entries in topic_map.items():
            filepath = os.path.join(self.folderpath, f"{topic}.json")
            with open(filepath,"w") as f:
                json.dump(entries,f,indent=2)

    def add_entry(self, entry):
        """
        entry: dict with keys:
            - topic (str)
            - question (str)
            - answer (str)
            - weights (dict, optional)
        """
        # Ensure weights exist
        if "weights" not in entry or not entry["weights"]:
            entry["weights"] = {w: 1.0 for w in entry["question"].lower().split()}

        # Add to memory
        self.qa_list.append(entry)

        # Persist to topic file
        topic = entry.get("topic", "default")
        filename = f"{topic}.json"
        filepath = os.path.join(self.folderpath, filename)

        # Load existing data
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
            except Exception:
                data = []
        else:
            data = []

        # Append new entry and save
        data.append({
            "topic": entry["topic"],
            "question": entry["question"],
            "answer": entry["answer"],
            "weights": entry["weights"]
        })

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        print(f"Saved new entry to {filepath}")