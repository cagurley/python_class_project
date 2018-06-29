# -*- coding: utf-8 -*-
"""
Created on Thu Jun 28 12:30:46 2018

@author: CAGurley
"""

import csv
import re
import sqlite3


def _parse_lmpd_hc_csv():
    rows = []
    with open('LMPD_OP_BIAS_7.csv') as raw_hc_data:
        reader = csv.reader(raw_hc_data)
        for row in reader:
            stripped_row = []
            for entry in row:
                stripped_row.append(entry.strip().upper())
            rows.append(stripped_row)
    for row in rows:
        if row[15] == 'LVIL':
            row[15] = 'LOUISVILLE'

    header = rows.pop(0)
    for counter, name in enumerate(header):
        name = re.sub(r'\s+', r'_', name)
        header[counter] = re.sub(r'\W+', r'', name)

    return header, rows


def _declare_col_types(header, rows):
    try:
        lengths = {len(header)}
        for row in rows:
            lengths.add(len(row))
        if len(lengths) != 1:
            raise IndexError("Row length mismatch")
    except IndexError:
        print("Header and rows must all be of equal length")
    else:
        col_counter = 0
        col_types = []
        while col_counter < len(header):
            int_row_counter = 1
            for row in rows:
                if (bool(re.search(r'^\d+$', row[col_counter]))
                        and int_row_counter < len(rows)):
                    int_row_counter += 1
                    continue
                elif (bool(re.search(r'^\d+$', row[col_counter]))
                        and int_row_counter >= len(rows)):
                    if (col_counter == 0
                            and re.search(r'ID$', header[col_counter], re.I)):
                        col_types.append('INTEGER PRIMARY KEY')
                    else:
                        col_types.append('INTEGER')
                    break
                else:
                    col_types.append('TEXT')
                    break
            col_counter += 1
        return col_types


def _compile_ct_statement(header, col_types, table_name):
    try:
        if re.search(r'\W+', table_name) is not None:
            raise ValueError("Table name error")
    except ValueError:
        print(
            "Table name must consist only of letters, digits, and underscores."
        )
    else:
        table_name = table_name.upper()
        counter = 0
        statement_center = ''
        while counter < len(header):
            statement_center += (
                "\n    "
                + header[counter]
                + " "
                + col_types[counter]
                + ","
            )
            counter += 1
        statement_center = statement_center.rstrip(',')
        ct_statement = (
            "CREATE TABLE IF NOT EXISTS "
            + table_name
            + "("
            + statement_center
            + "\n);"
        )
        return ct_statement


header, rows = _parse_lmpd_hc_csv()
column_types = _declare_col_types(header, rows)
hc_values = []
for row in rows:
    hc_values.append(tuple(row))
hc_table_name = 'LOU_HATE_CRIMES'
hc_create_statement = _compile_ct_statement(
    header, column_types, hc_table_name
)
print(hc_create_statement)

conn = sqlite3.connect('lou_hate_crime_database.db')
cur = conn.cursor()
try:
    cur.execute("DROP TABLE IF EXISTS {};".format(hc_table_name))
    cur.execute(hc_create_statement)
    cur.executemany("""
                    INSERT INTO {}
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """.format(hc_table_name), hc_values)
    conn.commit()
finally:
    conn.rollback()
    cur.close()
    conn.close()