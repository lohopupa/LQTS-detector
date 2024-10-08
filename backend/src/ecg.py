import csv
import math
import numpy as np
import random as rd
import os

def parse_name(name):
    file = name.split("/")[-1].split("_")[0]
    sex, qt, pp = name.split("/")[-1].split("_")[1:]
    pp = int(pp.split(".")[0])
    return file, sex, qt, pp


def transformd_dataset(in_dir, out_dir, function):
    files = [i for i in os.listdir(in_dir) if i.endswith(".csv")]

    os.makedirs(out_dir, exist_ok=True)

    for file in files:
        header, data = read_file(os.path.join(in_dir, file))
        data = [function(i) for i in data]
        write_file(os.path.join(out_dir, file), header, data)

def write_file(filepath, headers, data):
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        writer.writerows(list(zip(*data)))


def read_file(filepath):
    with open(filepath, 'r') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)
        data = list(zip(*[map(float, row) for row in reader]))
    return headers, data

def get_time(data):
    return np.array([i * 0.002 for i in range(len(data[0]))])

def filter_data(data, filter_func):
    return [filter_func(d) for d in data]

def exponential_filter(data):
    alpha = 0.1
    sdata = [data[0]]

    for i in range(1, len(data)):
        smoothed_value = alpha * data[i] + (1 - alpha) * sdata[-1]
        sdata.append(smoothed_value)
    return sdata

def get_R_peaks(timeECG, waveData, threshold_ratio=0.7):
    assert len(timeECG) == len(waveData), "data and time should be the same length"
    
    interval = max(waveData) - min(waveData)
    threshold = threshold_ratio*interval + min(waveData)
    maxima = []
    maxima_indices = []
    mxs_indices = []
    banner = False
    
    for i in range(0, len(waveData)):
            
        if waveData[i] >= threshold:
            banner = True
            maxima_indices.append(i)
            maxima.append(waveData[i])
            
        elif banner == True and waveData[i] < threshold:
            index_local_max = maxima.index(max(maxima))
            mxs_indices.append(maxima_indices[index_local_max])
            maxima = []
            maxima_indices = []
            banner = False     

    return mxs_indices

def get_QS_complex(data, r_peaks):
    qs = []
    ss = []
    T = 40
    for R_peak_i in r_peaks:
        left_interval = data[R_peak_i-T:R_peak_i]
        right_interval = data[R_peak_i:R_peak_i+T]
        if len(left_interval) > 0 and len(right_interval) >  0:
            qs.append(R_peak_i - T + (list(left_interval).index(min(left_interval))) )
            ss.append(R_peak_i + (list(right_interval).index(min(right_interval))) )
    return qs, ss

def get_T_complex(data, time_data, r_peaks, s_peaks):
    nn = 100
    t_wave_begin = []
    interval_der = 50
    time_derivative_vec = []
    for mxs_i in range(0, len(r_peaks)):
        
        for i in range(0, nn-5):
            try:
                index = s_peaks[mxs_i] + nn + i
                aux = (data[index+interval_der]-data[index])/(time_data[index+interval_der] - time_data[index])
                time_derivative_vec.append(aux) 
                
                if aux > 0.0:
                    t_wave_begin.append(index)
                    break
            except:
                continue

    nn = 100
    t_wave_end = []
    interval_der = 200
    time_derivative_vec = [0]
    for mxs_i in range(0, len(r_peaks)):
        
        for i in range(0, nn-5):
            try:
                index = s_peaks[mxs_i] + nn + i
                aux = (data[index+interval_der]-data[index])/(time_data[index+interval_der] - time_data[index])
                time_derivative_vec.append(aux) 

                if time_derivative_vec[i] > 0 and time_derivative_vec[i-1] < 0: 
                    t_wave_end.append(index)
                    break
            except:
                continue
    return t_wave_begin, t_wave_end

def avg(arr):
        return [math.floor(sum(i)/len(i)) for i in zip(*arr)]


def get_peaks(data):
    data = filter_data(data, exponential_filter)
    time_data = get_time(data)

    rss = []
    qss = []
    tss = []
    leafs = [0, 1, 5, 9, 10, 11]
    for id, leaf in enumerate(data):
        rs = get_R_peaks(time_data, leaf)
        qs, ss = get_QS_complex(leaf, rs)
        _, ts = get_T_complex(leaf, time_data, rs, ss)
        if id in leafs:
            rss.append(rs)
            qss.append(qs)
            tss.append(ts)
    
    srs = avg(rss)
    sqs = avg(qss)
    sts = avg(tss)
    return srs, sqs, sts

def qtc_bazett(qt, rr):
    return qt / math.sqrt(rr/1000)

def qtc_friderici(qt, rr):
    return qt / math.pow(rr/1000, 1/3)

def qtc_saige(qt, rr):
    return qt + (.154 * (1 - rr/1000)) * 1000

