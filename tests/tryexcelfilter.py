from xlsx import mkworkbook
## too difficult must be integrated in xlsx mkworkbook and  xlsx_writerow

header = ['data1', 'data2', 'infor']

data = [[1, 2, 'yes'],
        [3, 4, 'yes'],
        [5, 6, 'no'],
        [7, 8, 'no']
        ]

outfullname = 'testfilter.xlsx'

wb = mkworkbook(outfullname, [header], data, freeze_panes=(1,0))
ws = wb.get_worksheet_by_name('Sheet1')

# Set the autofilter.
worksheet.autofilter('A1:D51')

# Add the filter criteria. The placeholder "Region" in the filter is
# ignored and can be any string that adds clarity to the expression.
worksheet.filter_column(0, 'Region == East')

# Hide the rows that don't match the filter criteria.
row = 1
for row_data in (data):
    region = row_data[0]

    # Check for rows that match the filter.
    if region == 'East':
        # Row matches the filter, display the row as normal.
        pass
    else:
        # We need to hide rows that don't match the filter.
        worksheet.set_row(row, options={'hidden': True})

    worksheet.write_row(row, 0, row_data)

    # Move on to the next worksheet row.
    row += 1
wb.close()