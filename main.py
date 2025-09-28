#!/usr/bin/env python3

import os
from repl import REPL
from qa_engine import QAEngine

def main():
    qa_folder = "/home/hamination/yuno/data_qa"
    os.makedirs(qa_folder, exist_ok=True)

    qa_system = QAEngine(qa_folder)
    repl = REPL(qa_system)
    repl.start()

if __name__ == "__main__":
    main()
