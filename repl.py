import os
import readline
import shlex

class REPL:
    def __init__(self, qa_core):
        self.qa_core = qa_core
        self.last_results = []
        self.last_query_words = []

    def start(self):
        HISTORY_FILE = os.path.expanduser("./qa_repl_history")
        if os.path.exists(HISTORY_FILE):
            readline.read_history_file(HISTORY_FILE)
        readline.set_history_length(1000)

        print("Interactive Q&A. Type 'exit' to quit.")
        print("Commands:")
        print(" q --n=[number of matches](optional) -t <topic>(optional) -q(optional) <query>     -> find matches")
        print(" f -<n> < +|- >      -> feedback on last query, #n result")
        print(" data -t <topic> -q <question> -a <answer>       -> add new entry")
        print(" exit/quit       -> exit script\n")

        while True:
            raw = input("> ").strip()
            if not raw:
                continue
            if raw in ("exit", "quit"):
                print("\nExiting... Bye")
                break

            # Parse first token
            parts = raw.split(maxsplit=1)
            cmd = parts[0]
            args = parts[1] if len(parts) > 1 else ""

            if cmd == "q":
                self.handle_query(args)
            elif cmd == "f":
                self.handle_feedback(args)
            elif cmd == "data":
                self.handle_data(args)
            else:
                print("Unknown command.")
            print()

            readline.write_history_file(HISTORY_FILE)

    def handle_query(self, query):
        tokens = query.split()
        topic_filter = None
        top_n = 5

        idx = 0
        query_words = []
        while idx < len(tokens):
            token = tokens[idx]
            if token.startswith("--n="):
                try:
                    top_n = int(token.split("=")[1])
                except ValueError:
                    print(f"Invalid number for --n: {token}")
                    return
                idx += 1
            elif token == "-t" and idx + 1 < len(tokens):
                topic_filter = tokens[idx + 1]
                idx += 2
            else:
                query_words.append(token)
                idx += 1

        if not query_words:
            print("No query provided.")
            return

        query_str = " ".join(query_words)
        self.last_query_words = query_words

        # Filter QA list by topic if given
        if topic_filter:
            filtered_list = [entry for entry in self.qa_core.qa_list if entry.get("topic") == topic_filter]
        else:
            filtered_list = self.qa_core.qa_list

        results = self.qa_core.find_matches(query_str, top_n=top_n, qa_list=filtered_list)
        if not results:
            print("No matches found.")
            self.last_results = []
            return

        self.last_results = results
        print("==== Top results  ====")
        for idx, (pct, entry) in enumerate(results, start=1):
            topic = entry.get("topic", "default")
            question = entry.get("question", "")
            answer = entry.get("answer", "")
            answer = answer.replace("\\n", "\n")
            print(f"{idx}. {pct}% -> [{topic}] {question} ->        {answer}")


    def handle_feedback(self, args):
        if not self.last_results:
            print("No recent query results to give feedback on.")
            return

        tokens = args.split()
        if len(tokens) != 2:
            print("Usage: f -<result_number> <+|->")
            return

        num_token, fb_token = tokens
        if not num_token.startswith("-") or fb_token not in ("+", "-"):
            print("Usage: f -<result_number> <+|->")
            return

        try:
            idx = int(num_token[1:]) - 1  # convert to 0-based
            if idx < 0 or idx >= len(self.last_results):
                print("Invalid result number.")
                return
        except ValueError:
            print("Invalid result number.")
            return

        feedback_list = [(self.last_results[idx][1], 1 if fb_token == "+" else -1, self.last_query_words)]
        self.qa_core.update_weights(feedback_list)
        print(f"Feedback applied to result #{idx+1}")


    def handle_data(self, args):
        # Use shlex to parse like a shell
        tokens = shlex.split(args)
        topic = None
        question = None
        weights = []
        answer = None

        i = 0
        while i < len(tokens):
            if tokens[i] == "-t" and i+1 < len(tokens):
                topic = tokens[i+1]
                i += 2
            elif tokens[i] == "-q" and i+1 < len(tokens):
                question = tokens[i+1]
                i += 2
            elif tokens[i] == "-w" and i+2 < len(tokens):
                word = tokens[i+1]
                try:
                    weight = int(tokens[i+2])
                except ValueError:
                    print(f"Invalid weight: {tokens[i+2]}")
                    return
                weights.append((word, weight))
                i += 3
            elif tokens[i] == "-a" and i+1 < len(tokens):
                # rest is answer
                answer = " ".join(tokens[i+1:])
                break
            else:
                i += 1

        if not (topic and question and answer):
            print("Missing required fields. Usage:")
            print("  data -t <topic> -q <question> [-w word weight ...] -a <answer>")
            return

        # Build entry
        entry = {
            "topic": topic,
            "question": question,
            "weights": {w: wt for w, wt in weights},
            "answer": answer
        }
        self.qa_core.add_entry(entry)
        print(f"Added entry: {entry}")
            
