from collections import defaultdict
from sastadev.xlsx import xlsx_writerow
from typing import List
from xlsxwriter import Workbook

comma = ','
hyphen = '-'
identity_function = lambda x: x

def get_item_list(item_str: str, sep:str=comma, range_sep:str=hyphen, sort_key=int,
                  mk_item=identity_function, well_formed=lambda x: True) -> list:
    results = []
    parts = item_str.split(sep)
    for part in parts:
        if range_sep in part:
            range_parts = part.split(range_sep)
            if len(range_parts) == 2:
                range_start = range_parts[0]
                range_end = range_parts[1]
                if not well_formed(range_start):
                    print(f'Ill-formed item: {range_start}')
                    exit(-1)
                if not well_formed(range_end):
                    print(f'Ill-formed item: {range_end}')
                    exit(-1)
                if sort_key(range_start) > sort_key(range_end):
                    print(f'Item range start lower than Item range end: {range_start} - {range_end}')
                    exit(-1)
                range_start_int = sort_key(range_start)
                range_end_int = sort_key(range_end) + 1
                new_items = [mk_item(i) for i in range(range_start_int, range_end_int)]
                results += new_items
            else:
                print(f'Ill-formed item range: {part}')
        elif well_formed(part):
            results.append(int(part))
        else:
            print(f'Ill-formed item: {part}')
    return results


def get_key(row: list, key_columns: List[int]) -> tuple:
    key_tuple = (row[i] for i in key_columns)
    return tuple(key_tuple)

def table2dict(table, key_columns: List[int]) -> dict:
    out_dict = {}
    for row in table:
        key = get_key(row, key_columns)
        out_dict[key] = row
    return out_dict



def write_tables(wb:Workbook, results_table, ref_table, headers, columns: str, key_cols=None,
                 sheet_name='Sheet1', separator_rows=[[]]) -> Workbook:

    green_format = wb.add_format({'bg_color':'green'})
    red_format = wb.add_format({'bg_color': 'red'})
    bold = wb.add_format({'bold': True})

    # check if the tables have the same shape

    # turn the columns into a list of integers
    column_list = get_item_list(columns)

    # get the key column list
    key_column_list = get_item_list(key_cols)

    # get results_dict
    results_dict = table2dict(results_table, key_column_list)

    # get ref-dict
    ref_dict = table2dict(ref_table, key_column_list)


    # compute the difference dict
    diff_dict = defaultdict(list)
    done_keys = []
    for key in results_dict:
        res_row = results_dict[key]
        if key in ref_dict:
            diff_row = []
            done_keys.append(key)
            ref_row = ref_dict[key]
            for i, el in enumerate(res_row):
                if i in column_list:
                    new_el = str(float(el) - float(ref_row[i]))
                else:
                    new_el = el
                diff_row.append(new_el)
        else:
            diff_row = res_row
        diff_dict[key] = diff_row
    for key in ref_dict:
        if key not in done_keys:
            ref_row = ref_dict[key]
            for i, el in enumerate(ref_row):
                if i in column_list:
                    new_el = str(-float(el)) if el != '' else el
                else:
                    new_el = el
                diff_row.append(new_el)
            diff_dict[key] = diff_row

    ws = wb.add_worksheet(sheet_name)
    ws.freeze_panes(len(headers), 1)

    row_ctr = 0

    # write the headers
    for row in headers:
        xlsx_writerow(ws, row_ctr, row, format=bold)
        row_ctr += 1

    # write the results table with colors
    sorted_keys = sorted(diff_dict.keys())
    for row_nr, key in enumerate(sorted_keys):
        if key not in results_dict:
            continue
        res_row = results_dict[key]
        diff_row = diff_dict[key]
        for col_nr, el in enumerate(res_row):
            if col_nr in column_list:
                out_val = float(res_row[col_nr]) if res_row[col_nr] != '' else res_row[col_nr]
                if float(diff_row[col_nr]) > 0.0:
                    ws.write(row_ctr, col_nr, out_val, green_format)
                elif float(diff_row[col_nr]) < 0.0:
                    ws.write(row_ctr, col_nr, out_val, red_format)
                else:
                    ws.write(row_ctr, col_nr, out_val)
            else:
                ws.write(row_ctr, col_nr, res_row[col_nr])
        row_ctr += 1






    # write the separator row(s)
    for row in separator_rows:
        ws.write_row(row_ctr, 0, row)
        row_ctr += 1

    # write the ref table
    for key in sorted_keys:
        if key not in ref_dict:
            continue
        row = ref_dict[key]
        for col_nr, el in enumerate(row):
            if col_nr in column_list:
                out_val = float(row[col_nr]) if row[col_nr] != '' else row[col_nr]
                ws.write(row_ctr, col_nr, out_val)
            else:
                ws.write(row_ctr, col_nr, row[col_nr])
        row_ctr += 1

    # write the separator row(s)
    for row in separator_rows:
        ws.write_row(row_ctr, 0, row)
        row_ctr += 1

    # write the difference table
    for key in sorted_keys:
        if key not in diff_dict:
            continue
        row = diff_dict[key]
        for col_nr, el in enumerate(row):
            if col_nr in column_list:
                out_val = float(row[col_nr]) if row[col_nr] != '' else row[col_nr]
                ws.write(row_ctr, col_nr, out_val)
            else:
                ws.write(row_ctr, col_nr, row[col_nr])
        row_ctr += 1

    ws.autofilter(0, 0, row_ctr, col_nr)

    return wb




# the next tables are for testing
results_table = [['S003', '23.4', '77.8', '55.6', 'xxx', '38.3', '77.5', '64.2'],
                 ['S004', '63.1', '66.7', '64.6', 'yyy', '68.3', '67.4', '67.7']]

ref_table = [['S003', '21.4', '75.8', '53.6', 'xxx', '35.3', '81.5', '61.2'],
                 ['S004', '61.1', '64.7', '62.6', 'yyy', '68.3', '66.4', '67.4']]


def main():
#    cols = get_item_list('1-3,5-7')
#    print(cols)
     outfilename = 'table_comparison_test.xlsx'
     header = ['qid', 'br', 'bp', 'bf1', 'XXX', 'sr', 'sp', 'sf1']
     wb = Workbook(outfilename)
     wb = write_tables(wb, results_table, ref_table, [header], columns='1-3,5-7', key_cols='0')
     wb.close()





if __name__ == '__main__':
    main()