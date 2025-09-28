import os
import json

class QALoader:
    def __init__(self, folderpath):
        self.folderpath = folderpath

    def load_all(self):
        qa_list = []
        for filename in os.listdir(self.folderpath):
            if filename.endswith(".json"):
                filepath = os.path.join(self.folderpath, filename)
                qa_list.extend(self.load_file(filepath))
        return qa_list

    def load_file(self, filepath):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                for entry in data:
                    if "weights" not in entry:
                        entry["weights"] = {
                            w: 1.0 for w in entry["question"].lower().split()
                        }
                return data
        except Exception:
            return []

    def save_topic(self, topic, entries):
        filepath = os.path.join(self.folderpath, f"{topic}.json")
        with open(filepath, "w") as f:
            json.dump(entries, f, indent=2)


class SynonymManager:
    def __init__(self, filepath):
        self.synonyms = self.load(filepath)

    def load(self, filepath):
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return json.load(f)
        return {}

    def get(self, word):
        return self.synonyms.get(word, [])


class Scorer:
    def __init__(self, synonym_manager):
        self.synonyms = synonym_manager

    def score(self, query, entry):
        query_words = query.lower().split()
        weights = entry.get("weights", {})
        score = 0
        for word in query_words:
            # exact match
            score += weights.get(word, 0)
            # synonyms
            for syn in self.synonyms.get(word):
                score += weights.get(syn, 0)
        return score




class QAEngine:
    WEIGHT_MIN = 0.2
    WEIGHT_MAX = 4.0
    WEIGHT_STEP = 0.2

    def __init__(self, folderpath, synonyms_file="/home/hamination/yuno/synonyms.json"):
        self.loader = QALoader(folderpath)
        self.synonyms = SynonymManager(synonyms_file)
        self.scorer = Scorer(self.synonyms)
        self.folderpath = folderpath
        self.qa_list = self.loader.load_all()


    def find_matches(self, query, top_n=5, qa_list=None):
        if qa_list is None:
            qa_list = self.qa_list

        scored = [
            (self.scorer.score(query, entry), entry)
            for entry in qa_list
            if self.scorer.score(query, entry) > 0
        ]

        if not scored:
            return []

        scored.sort(key=lambda x: x[0], reverse=True)
        max_score = scored[0][0]

        results = []
        for s, entry in scored[:top_n]:
            pct = round((s / max_score) * 100, 1)
            results.append((pct, entry))
        return results


    def update_weights(self, feedback_list):
        """
        feedback_list: list of tuples (entry, +1/-1, query_words)
        """
        for entry, fb, query_words in feedback_list:
            if "weights" not in entry:
                entry["weights"] = {}
            for w in query_words:
                old_w = entry["weights"].get(w, 1.0)
                delta = self.WEIGHT_STEP
                if fb > 0:
                    new_w = min(self.WEIGHT_MAX, old_w + delta)
                else:
                    new_w = max(self.WEIGHT_MIN, old_w - delta)
                entry["weights"][w] = new_w

        # Save per-topic files
        topic_map = {}
        for entry in self.qa_list:
            topic = entry.get("topic", "default")
            topic_map.setdefault(topic, []).append(entry)
        for topic, entries in topic_map.items():
            self.loader.save_topic(topic, entries)

    def add_entry(self, entry):
        if "weights" not in entry or not entry["weights"]:
            entry["weights"] = {
                w: 1.0 for w in entry["question"].lower().split()
            }

        self.qa_list.append(entry)

        topic = entry.get("topic", "default")
        filename = f"{topic}.json"
        filepath = os.path.join(self.folderpath, filename)

        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
            except Exception:
                data = []
        else:
            data = []

        data.append({
            "topic": entry["topic"],
            "question": entry["question"],
            "answer": entry["answer"],
            "weights": entry["weights"]
        })

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        print(f"Saved new entry to {filepath}")
