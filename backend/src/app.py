import math
from fastapi import APIRouter, UploadFile, File
from model import Model, load_model_split
import pandas as pd
import numpy as np
from io import BytesIO
import ecg

router = APIRouter(prefix="/api")

# model = Model()
model2 = load_model_split()

@router.post("/file_query")
async def file_query(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        return {"error": "File should be csv!"}
    content = await file.read()
    try:
        ds = pd.read_csv(BytesIO(content))
        srs, sqs, sts = ecg.get_peaks(ds.T.values)
        if len(srs) == 0:
            return {
                "error": "Не получилось выделить R пики",
            }

        result = predict_split(ds)
        # text_result =  "QT интервал в норме" if result == 1 else "Обнаружен синдром удлиненного QT"
        text_result = "QT интервал в норме"
        if result == 0:
            text_result = "Обнаружен синдром удлиненного QT"
        elif result == 2:
            text_result = "Обнаружен синдром укороченного QT"

        qts = [(t - q) * 2 for q, t in zip(sqs, sts)]
        if len(qts) != 0:

            qt = sum(qts)/len(qts)
            if len(srs) > 1:
                rrs = []
                for i in range(len(srs) - 1):
                    rrs.append((srs[i+1] - srs[i]) * 2)
                rr = sum(rrs)/len(rrs)
                qtc_funcs = [ecg.qtc_bazett, ecg.qtc_friderici, ecg.qtc_saige]
                qtc = sum([f(qt, rr) for f in qtc_funcs])/len(qtc_funcs)
            else:
                rr = "Ошибка при вычислении"
                qtc = "Ошибка при вычислении"
            
        else:
            qt = "Ошибка при вычислении"
            rr = "Ошибка при вычислении"
            qtc = "Ошибка при вычислении"
            

        return {
            "result": text_result,
            "qs": sqs,
            "rs": srs,
            "ts": sts,
            "qt": qt,
            "rr": rr,
            "qtc": qtc
            }
    except Exception as e:
        print(e)
        return {"error": "Что-то пошло не так!"}
    

def predict_split(ds):
    data = ds.T.values
    time_data = ecg.get_time(data)
    rrs = []
    rs = ecg.get_R_peaks(time_data, data[0])
    for id, leaf in enumerate(data):
        qs, ss = ecg.get_QS_complex(leaf, rs)
        _, ts = ecg.get_T_complex(leaf, time_data, rs, ss)
        qts = zip(qs, ts)

        LENGTH = 512

        for qt_id, qt in enumerate(qts):
            q, t  = qt
            mid = q + (t - q) //  2
            left = mid - LENGTH // 2
            if left < 0:
                left = 0
            right = left + LENGTH
            if right >= len(leaf):
                right = len(leaf) - 1
                left = right - LENGTH
            rrs.append(leaf[left:right])

    pred = model2.predict(np.array(rrs))
    pred = [np.argmax(y, axis=None, out=None) for y in pred]
    return max(set(pred), key=pred.count)


# long, norm, short
# def predict_tile(ds):
#     srs, sqs, sts = ecg.get_peaks(ds.T.values)

#     start = srs[0]
#     end = srs[-1]
#     data = ds.values
#     # data = np.array(data).reshape(len(data[0]), 12)
#     data = data[start:end]
#     data = np.expand_dims(data, axis=0)
#     data = np.tile(data, (1, math.ceil(2500/data.shape[1]), 1))[:, :2500, :]
#     result = model.predict(data)
#     return result