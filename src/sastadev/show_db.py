import os
from sastadev.conf import settings
from sastadev.stored_spelling_corrections import read_stored_spelling_corrections
import sqlite3

def main():

    filename = 'children_storedcorrections.db'
    store_path = os.path.join(settings.SD_DIR, 'data', 'stored_spelling_corrections')
    # if not os.path.exists(store_path):
    #     os.makedirs(store_path)
    fullname = os.path.join(store_path, filename)

    stored_spelling_correction_dict = read_stored_spelling_corrections(fullname)
    for wrong_word, corrections in stored_spelling_correction_dict.items():
        print(wrong_word, corrections)

if __name__ == '__main__':
    main()

