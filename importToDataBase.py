import sqlite3
import os
import re

def create_database(topic_name: str):
    db_name = f"{topic_name.lower()}.db"
    if os.path.exists(db_name):
        os.remove(db_name)  # Щоб створити з нуля

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            option_e TEXT,
            correct_option INTEGER
        )
    ''')

    conn.commit()
    conn.close()
    print(f"[OK] Базу даних {db_name} створено.")

def parse_and_insert_tests(txt_file: str, topic_name: str):
    db_name = f"{topic_name.lower()}.db"
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    with open(txt_file, "r", encoding="utf-8") as f:
        content = f.read()

    tests = content.strip().split('--')
    for test in tests:
        lines = test.strip().split('\n')
        question_lines = []
        options = []
        correct_option_index = None

        for line in lines:
            if re.match(r"^\d{3}\. ", line):  # Змінено на регулярний вираз для "111."
                # Перевіряємо, чи є позначка (+)
                if '(+)' in line:
                    clean_line = line.replace('(+)', '').strip()
                    correct_option_index = len(options) + 1  # 1-based indexing
                else:
                    clean_line = line.strip()
                options.append(clean_line[4:].strip())  # Видаляємо "111. "
            else:
                question_lines.append(line.strip())

        full_question = " ".join(question_lines)

        # Додаємо перевірки на порожні тести та тести без питань/відповідей
        if not full_question and not options:
            continue  # Пропускаємо порожні тести
        if not full_question or len(options) != 5 or correct_option_index is None:
            print(f"[УВАГА] Пропущено тест через помилковий формат:\n{test}")
            continue

        cursor.execute('''
            INSERT INTO questions (question, option_a, option_b, option_c, option_d, option_e, correct_option)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (full_question, *options, correct_option_index))

    conn.commit()
    conn.close()
    print(f"[OK] Дані з файлу '{txt_file}' імпортовано у базу '{db_name}'.")

#  Приклад використання
if __name__ == "__main__":
    topic = "DataBases/Exam/exAll"  # або будь-яка інша тема
    txt_path = "ForTextFiles/Exam/exAll.txt"  # твій .txt файл

    create_database(topic)
    parse_and_insert_tests(txt_path, topic)