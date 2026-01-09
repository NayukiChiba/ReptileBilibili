import csv


def write2csv(file, row):
    with open(file, mode='a', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(row)


def write_head(file, heads):
    with open(file, mode='a', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(heads)  # 写入表头


def read_csv(file):
    data = []
    with open(file, newline='', encoding='utf-8-sig') as csvfile:
        csv_reader = csv.reader(csvfile)
        next(csv_reader)  # 跳过表头
        for row in csv_reader:
            data.append(row)
    return data
