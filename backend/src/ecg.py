import csv
import math
import numpy as np
import random as rd
import scipy.signal as signal
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

def get_R_peaks(waveData, threshold_ratio=0.6):
    # return detect_r_peaks(waveData, samplerate)
    svel = [i[1] - i[0] for i in zip(waveData[1:], waveData[:-1])]
    vel = [abs(v) for v in svel] 
    amp = max(vel) - min(vel)
    threshold = threshold_ratio * amp + min(vel)
    # mxs = []

    # for i in range(len(vel)):
    maxima = []
    maxima_indices = []
    mxs_indices = []
    banner = False
    
    for i in range(0, len(vel)):
            
        if vel[i] >= threshold:
            banner = True
            maxima_indices.append(i)
            maxima.append(vel[i])
            
        elif banner == True and vel[i] < threshold:
            index_local_max = maxima.index(max(maxima))
            mxs_indices.append(maxima_indices[index_local_max])
            maxima = []
            maxima_indices = []
            banner = False     

    t = 50
    mm = []
    for m in mxs_indices:
        if len(mm) == 0:
            mm.append(m)
        else:
            if m - mm[-1] < t:
                pass
            else:
                mm.append(m)
    r = 30
    sign = svel[mm[0]] < 0
    for i in range(len(mm)):
        start = max(mm[i] - r, 0)
        end = min(mm[i] + r, len(waveData))
        sl = waveData[start:end]
        if(len(sl) == 0):
            continue
        if sign:
            v = max(sl)
            if v > threshold:
                mm[i] = sl.index(v) + start
            else:
                mm[i] = None
        else:
            v = min(sl)
            if v < threshold:
                mm[i] = sl.index(v) + start
            else:
                mm[i] = None
    mm = list(filter(lambda x: x is not None, mm))
    return mm, sign
    # return mxs_indices

def get_QS_complex(data, r_peaks, sign):
    qs = []
    ss = []
    T = 25
    f = min if sign else max
    for R_peak_i in r_peaks:
        left_interval = data[R_peak_i-T:R_peak_i]
        right_interval = data[R_peak_i:R_peak_i+T]
        if len(left_interval) > 0 and len(right_interval) >  0:
            qs.append(R_peak_i - T + (list(left_interval).index(f(left_interval))) )
            ss.append(R_peak_i + (list(right_interval).index(f(right_interval))) )
    return qs, ss

def get_T_complex(data, time_data, r_peaks, s_peaks):
    nn = 70
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

    rt = {}
    interval_der = 200
    time_derivative_vec = [0]
    for mxs_i in range(0, len(r_peaks)):
        
        for i in range(0, nn-5):
            try:
                index = s_peaks[mxs_i] + nn + i
                aux = (data[index+interval_der]-data[index])/(time_data[index+interval_der] - time_data[index])
                time_derivative_vec.append(aux) 

                if time_derivative_vec[i] > 0 and time_derivative_vec[i-1] < 0: 
                    rt[mxs_i] = index
                    t_wave_end.append(index)
                    break
            except:
                continue
    return t_wave_begin, t_wave_end, rt

def avg(arr):
        return [math.floor(sum(i)/len(i)) for i in zip(*arr)]


def get_peaks(data):
    time_data = get_time(data)

    rss = []
    qss = []
    tss = []
    for id, leaf in enumerate(data):
        rs, s  = get_R_peaks(leaf)
        qs, ss = get_QS_complex(leaf, rs, s)
        _, _, rts = get_T_complex(leaf, time_data, rs, ss)

        rss.append([rs[i] for i in rts.keys()])
        qss.append([qs[i] for i in rts.keys()])
        tss.append(rts.values())

    ml = max(list(map(len, rss)))
    rss = [i for i in rss if len(i) == ml]
    qss = [i for i in qss if len(i) == ml]
    tss = [i for i in tss if len(i) == ml]

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



def thresholding_algo(y, lag, threshold, influence):
    signals = np.zeros(len(y))
    filteredY = np.array(y)
    avgFilter = [0]*len(y)
    stdFilter = [0]*len(y)
    avgFilter[lag - 1] = np.mean(y[0:lag])
    stdFilter[lag - 1] = np.std(y[0:lag])
    peaks_x = []

    for i in range(lag, len(y)):
        if abs(y[i] - avgFilter[i-1]) > threshold * stdFilter[i-1]:
            if y[i] > avgFilter[i-1]:
                signals[i] = 1
            else:
                signals[i] = -1

            peaks_x.append(i)
            filteredY[i] = influence * y[i] + (1 - influence) * filteredY[i-1]
            avgFilter[i] = np.mean(filteredY[(i-lag+1):i+1])
            stdFilter[i] = np.std(filteredY[(i-lag+1):i+1])
        else:
            signals[i] = 0
            filteredY[i] = y[i]
            avgFilter[i] = np.mean(filteredY[(i-lag+1):i+1])
            stdFilter[i] = np.std(filteredY[(i-lag+1):i+1])

    return peaks_x

def detect_r_peaks(ecg_signal, sampling_rate):
    # Bandpass filter the ECG signal
    lowcut = 5.0
    highcut = 15.0
    nyquist = 0.5 * sampling_rate
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = signal.butter(1, [low, high], btype="band")
    filtered_ecg = signal.filtfilt(b, a, ecg_signal)

    # Differentiation
    diff_ecg = np.diff(filtered_ecg)

    # Squaring
    squared_ecg = diff_ecg ** 2

    # Moving window integration
    window_size = int(0.12 * sampling_rate)
    integrated_ecg = np.convolve(squared_ecg, np.ones(window_size) / window_size, mode="same")

    # Peak detection
    peaks, _ = signal.find_peaks(integrated_ecg, distance=sampling_rate / 2.5, height=np.mean(integrated_ecg))
    
    return peaks

def estimate_sampling_rate(time_vector):
        return 1 / np.mean(np.diff(time_vector))