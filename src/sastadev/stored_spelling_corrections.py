import os
import sqlite3
from sastadev.conf import settings
from sastadev.childesspellingcorrector import children_correctspelling


create_table = """
CREATE TABLE IF NOT EXISTS spellingcorrections (
    wrong_word text PRIMARY KEY, 
    corrected_words text
);
"""

insert_row = """
INSERT INTO spellingcorrections (wrong_word, corrected_words) VALUES(?,?)"""

retrieval_statement = """
SELECT * FROM spellingcorrections"""

sql_storage_statements = [create_table]

def read_stored_spelling_corrections(filename) -> dict:
    result_dict = {}
    try:
        with sqlite3.connect(filename) as conn:
            cursor = conn.cursor()
            cursor.execute(retrieval_statement)
            rows = cursor.fetchall()
            for row in rows:
                result_dict[row[0]] = eval(row[1])
    except sqlite3.OperationalError as e:
        settings.LOGGER.warning(f"Failed to open database {filename}: {e}")

    return result_dict

def store_spelling_corrections(corrections:dict, filename):
    try:
        with sqlite3.connect(filename) as conn:
            cursor = conn.cursor()
            for statement in sql_storage_statements:
                cursor.execute(statement)

            for wrong_word, corrected_words  in corrections.items():
                cursor.execute(insert_row, (wrong_word, corrected_words))

            # commit the changes
            conn.commit()
    except sqlite3.OperationalError as e:
        settings.LOGGER.warning(f"Failed to open database {filename}: {e}")



def tryme():
    wrong_word_list1 = ['ziekonhuis', 'peelkaal', 'pobreren']
    wrong_word_list2 = ['diretceur', 'peelkaal', 'grages', 'zunige', 'ziekanhuis']

    filename = 'test_stored_corrections.db'
    store_path = os.path.join(settings.SD_DIR, 'data', 'stored_spelling_corrections')
    if not os.path.exists(store_path):
        os.makedirs(store_path)
    fullname = os.path.join(store_path, filename)

    # read the stored corrections
    stored_spelling_correction_dict = read_stored_spelling_corrections(fullname)

    new_spelling_correction_dict = {}
    for wrong_word_list in [wrong_word_list1, wrong_word_list2]:
        for wrong_word in wrong_word_list:
            corrections = children_correctspelling(wrong_word, stored_spelling_correction_dict, max=5)
            if wrong_word not in stored_spelling_correction_dict:
                new_spelling_correction_dict[wrong_word] = str(corrections)



    store_spelling_corrections(new_spelling_correction_dict, fullname)


    newdict = read_stored_spelling_corrections(fullname)
    junk = 0
    pass

if __name__ == '__main__':
    tryme()



