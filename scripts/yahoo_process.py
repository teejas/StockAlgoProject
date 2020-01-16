# import sys
# from yahoo_finance import Share
# from collections import deque
from PIL import Image
# import cv2
import os
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import csv
from numpy.random import choice
import finsymbols as symbols
import pandas as pd

#constants
basePath = "../data/raw/yahoo/S&P500/"
imagePath = "../data/processed/S&P500/"
labels_name = "labels.txt"

# helper functions
def get_data_from_csv(fname):
    high_Price = []
    adj_Close = []
    volume = []

    if os.path.splitext(fname)[-1].lower() == '.csv':
        with open(fname, 'rb') as csvFile:
            stockCSV = csv.reader(csvFile)
            stockCSV.next()
            for row in stockCSV:
                high_Price.append(row[1])
                adj_Close.append(row[8])
                volume.append(row[5])

    return high_Price, adj_Close, volume

def scale_data(data_list):
    data_array = np.array(data_list)
    data_array = np.reshape(data_array, (-1,1))
    scaler = MinMaxScaler(feature_range=(0, 255))
    scaler.fit(data_array)
    scaled_data = scaler.transform(data_array)
    return scaled_data

def convert_to_images(open_data, close_data, vol_data):
    picture_list = []
    label_list = []
    percentage_growth = []

    count = 0

    for i in range(len(open_data)): # since this is for i in range it will produce a sliding window
        open_pic = open_data[i:i+224]
        close_pic = close_data[i:i+224]
        vol_pic = vol_data[i:i+224]

        if not len(open_pic) == 224:
            continue

        open_2D = np.array([open_pic] * 224)
        close_2D = np.array([close_pic] * 224)
        vol_2D = np.array([vol_pic] * 224)
        final_pic = np.dstack((open_2D, close_2D, vol_2D))

        if len(open_data) > (i + 259):
            picture_list.append(final_pic)
            denom = max(float(open_data[i+224]), 0.001)
            if open_data[i + 224] < open_data[i + 259]:
                label_list.append(1)
                percent = float(open_data[i+259] - open_data[i+224]) / denom
                percentage_growth.append(percent)
            else:
                label_list.append(0)
                percent = float(open_data[i+259] - open_data[i+224]) / denom
                percentage_growth.append(percent)

    return picture_list, label_list, percentage_growth

# process SPY
high_priceSP, close_priceSP, volSP = get_data_from_csv(os.path.join(basePath, 'SPY.csv'))

scaled_high = scale_data(high_priceSP)
scaled_high = np.flip(scaled_high, axis=0)

scaled_closed = scale_data(close_priceSP)
scaled_closed = np.flip(scaled_closed, axis=0)

scaled_vol = scale_data(volSP)
scaled_vol = np.flip(scaled_vol, axis=0)

pictures, labels, growthSP = convert_to_images(scaled_high, scaled_closed, scaled_vol)

# process everything else
if not os.path.exists(imagePath):
    os.makedirs(imagePath)

completedTickers = []
skippedTickers = []

SP500ticker = list(i['symbol'] for i in symbols.get_sp500_symbols())
with open(os.path.join(imagePath, labels_name), 'w+') as fd:
    numProc = 0
    while(numProc < 5):
        stockTicker = SP500ticker.pop(0)
        numProc += 1

        high_price, close_price, vol = get_data_from_csv(os.path.join(basePath, stockTicker + '.csv'))
        if len(high_price) != len(high_priceSP) or len(close_price) != len(close_priceSP) or len(volSP) != len(vol):
            print("len not equal, stockTicker: " + stockTicker + str(len(high_price)))
            skippedTickers.append(stockTicker)
            continue

        scaled_high = scale_data(high_price)
        scaled_high = np.flip(scaled_high, axis=0)

        scaled_closed = scale_data(close_price)
        scaled_closed = np.flip(scaled_closed, axis=0)

        scaled_vol = scale_data(vol)
        scaled_vol = np.flip(scaled_vol, axis=0)

        pictures, labels, growth = convert_to_images(scaled_high, scaled_closed, scaled_vol)

        total = 0
        count = [0, 0, 0]
        for picture in pictures:
            out_name = stockTicker + str(total) + '.png'
            im = Image.fromarray(np.uint8(picture))
            im.save(os.path.join(imagePath, out_name))
            # cv2.imwrite(os.path.join(imagePath, out_name), np.uint8(picture))

            if growth[total] <= 0:
                difLabel = "0"
                count[0] += 1
            elif growth[total] < growthSP[total]:
                difLabel = "1"
                count[1] += 1
            else:
                difLabel = "2"
                count[2] += 1

            fd.write(out_name + " " + difLabel + "\n")
            total += 1

        completedTickers.append(stockTicker)

# equate label amounts for images
labels_df = pd.read_table(os.path.join(imagePath, labels_name), sep=" ", names=["img", "label"])
print(labels_df.head())

zero = labels_df.loc[labels_df['label'] == 0.0]
one = labels_df.loc[labels_df['label'] == 1.0]
two = labels_df.loc[labels_df['label'] == 2.0]
zero = (zero.reset_index()).drop('index', axis=1)
one = (one.reset_index()).drop('index', axis=1)
two = (two.reset_index()).drop('index', axis=1)
print(zero.head())
print(one.head())
print(two.head())
min_len = min(len(zero), len(one), len(two))
zero_dellen = len(zero) - min_len
one_dellen = len(one) - min_len
two_dellen = len(two) - min_len
zero_todelete = choice(range(len(zero)), size=zero_dellen, replace=False)
one_todelete = choice(range(len(one)), size=one_dellen, replace=False)
two_todelete = choice(range(len(two)), size=two_dellen, replace=False)
print("minimum len: " + str(min_len))
print("zero orig len: " + str(len(zero)) + " len to delete: " + str((len(zero_todelete))))
print(zero_todelete)
print("one orig len: " + str(len(one)) + " len to delete: " + str((one_dellen)))
print(one_todelete)
print("two orig len: " + str(len(two)) + " len to delete: " + str((two_dellen)))
print(two_todelete)
zero_lbls = zero.drop(zero.index[zero_todelete])
zero_lbls = (zero_lbls.reset_index()).drop('index', axis=1)
print(zero_lbls.head())
print("zero new len: " + str(len(zero_lbls)))
one_lbls = one.drop(one.index[one_todelete])
one_lbls = (one_lbls.reset_index()).drop('index', axis=1)
two_lbls = two.drop(two.index[two_todelete])
two_lbls = (two_lbls.reset_index()).drop('index', axis=1)
print(one_lbls.head())
print("one new len: " + str(len(one_lbls)))
print(two_lbls.head())
print("two new len: " + str(len(two_lbls)))
