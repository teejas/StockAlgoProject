import os
import numpy as np
import csv
import pandas as pd
import time
import shutil
from config.config import Config

#constants
config_data = Config()
basePath = config_data.get('paths', 'raw_data_kibot')
clean_path = config_data.get('paths', 'clean_data_kibot')
labels_name = config_data.get('paths', 'labels_file')

keep_attrs = config_data.get('kibot', 'clean_settings', 'keep_attrs')
base_symbol = config_data.get('kibot', 'clean_settings', 'base')
interval = config_data.get('kibot', 'clean_settings', 'interval')

date_index = config_data.get('kibot', 'row_values', 'date')
time_index = config_data.get('kibot', 'row_values', 'time')

# create clean attribute list
attr_list = []
for key, value in keep_attrs.iteritems():
    attr_list.append((config_data.get('kibot', 'row_values', key), key, value))

# clean and/or create output dir
if os.path.exists(clean_path):
    print 'cleaning old data...'  # may need to change this if we need to append
    shutil.rmtree(clean_path)
if not os.path.exists(clean_path):
    print 'creating output path ({})'.format(clean_path)
    os.makedirs(clean_path)

# helper functions
def get_timestamp(row_date, row_time):
    return int(time.mktime(time.strptime('{} {}'.format(row_date, row_time), '%m/%d/%Y %H:%M')))

def isolate_attrs(row):
    isolated = []
    timestamp = get_timestamp(row[date_index], row[time_index])
    isolated.append(timestamp)
    for attr in attr_list:
        isolated.append(row[attr[0]])
    return isolated

def generate_row(timestamp, prev=None, post=None):
    def process(index, behavior):
        if behavior == 'previous':
            return prev[-1][index]
        if behavior == 'next':
            return post[0][index]
        else:
            return behavior

    generated = [timestamp]
    i = 0
    for attr in attr_list:
        i += 1
        generated.append(process(i, attr[2]))
    return generated

csv_header = ['timestamp'] + list(x[1] for x in attr_list)
def clean_base(table):
    timestamps = []
    cleaned = []
    cleaned.append(csv_header)

    row = isolate_attrs(table.next())
    cleaned.append(row)
    timestamps.append(row[0])

    for row in table:
        isolated = isolate_attrs(row)

        time_delta = isolated[0] - timestamps[-1]
        if time_delta == interval:
            cleaned.append(isolated)
            timestamps.append(isolated[0])
            continue

        if time_delta < interval:
            continue # no explicitly defined behavior yet
        if time_delta > interval:
            while timestamps[-1] + interval < isolated[0]:
                gen_row = generate_row(timestamps[-1] + interval, cleaned)
                cleaned.append(gen_row)
                timestamps.append(gen_row[0])

            cleaned.append(isolated)
            timestamps.append(isolated[0])

    return timestamps, cleaned

def isolate_table(table):
    isolated = []
    for row in table:
        isolated.append(isolate_attrs(row))
    return isolated

def clean_against(timestamps, isolated):
    time_delta = isolated[0][0] - timestamps[0]
    if not time_delta % interval == 0:
        return None
    if time_delta > 0:
        while not isolated[0][0] - timestamps[0] == 0:
            generated = generate_row(isolated[0][0] - interval, prev=[isolated[0]])
            isolated = [generated] + isolated
    if time_delta < 0:
        while not isolated[0][0] - timestamps[0] == 0:
            isolated = isolated[1:]

    i = 0
    while not len(timestamps) == len(isolated):
        if i == len(timestamps):
            isolated = isolated[:len(timestamps)]
            break
        if i >= len(isolated):
            while len(isolated) < len(timestamps):
                isolated.append(generate_row(isolated[-1][0] + interval, isolated))

        time_delta = isolated[i][0] - timestamps[i]
        if not time_delta % interval == 0:
            return None

        if time_delta == 0:
            i += 1
            continue

        while time_delta < 0:
            isolated.pop(i)
            time_delta = isolated[i][0] - timestamps[i]

        while time_delta > 0:
            isolated.insert(i, generate_row(isolated[i][0] - interval, isolated[:i]))
            time_delta = isolated[i][0] - timestamps[i]

    return [csv_header] + isolated

# clean base file
with open(os.path.join(basePath, '{}.csv'.format(base_symbol)), 'r') as fd:
    csv_data = csv.reader(fd)
    timestamps, clean_data = clean_base(csv_data)

filename = os.path.join(clean_path, '{}.csv'.format(base_symbol))
with open(filename, 'wb') as fd:
    print 'writing {}...'.format(filename)
    writer = csv.writer(fd)
    for row in clean_data:
        writer.writerow(row)
    print 'finished writing {}'.format(filename)

# clean the rest of the files against base timestamps
for filename in os.listdir(basePath):
    if not os.path.splitext(filename)[-1].lower() == '.csv':
        continue
    if filename.lower() == '{}.csv'.format(base_symbol):
        continue

    print 'cleaning {}...'.format(filename)
    with open(os.path.join(basePath, filename), 'r') as fd:
        csv_data = csv.reader(fd)
        isolated = isolate_table(csv_data)

    cleaned = clean_against(timestamps, isolated)
    if not cleaned:
        print 'Error cleaning {}'.format(filename)
    else:
        with open(os.path.join(clean_path, filename), 'wb') as fd:
            print 'writing {}...'.format(filename)
            writer = csv.writer(fd)
            for row in cleaned:
                writer.writerow(row)
            print 'finished writing {}'.format(filename)
