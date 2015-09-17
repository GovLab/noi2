'''
NoI Utils

Utility Functions
'''

import csv


def csv_reader(path_to_file):
    """
    Read a CSV with headers, yielding a dict for each row.
    """
    with open(path_to_file, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            yield row
