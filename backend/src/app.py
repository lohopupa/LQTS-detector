from fastapi import APIRouter, UploadFile, File
from model import Model
import pandas as pd
import numpy as np
from io import BytesIO

router = APIRouter(prefix="/api")

model = Model()

@router.post("/file_query")
async def file_query(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        return {"error": "File should be csv!"}
    content = await file.read()
    print(type(file))
    try:
        ds = pd.read_csv(BytesIO(content))
        data = np.expand_dims(ds.values, axis=0)
        result = model.predict(data)
        
        return {"result": "QT интервал в норме" if result == 1 else "Обнаружен синдром удлиненного QT"}
    except Exception as e:
        print(e)
        return {"error": "Что-то пошло не так!"}