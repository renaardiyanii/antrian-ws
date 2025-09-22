from typing import List,Union
from fastapi import Header,APIRouter,HTTPException,Depends
import app.api.validation.validation as validation
import app.api.models.models as models
import app.api.database.db_manager as db_manager
import app.api.validation.auth_handler as auth_handler
import app.api.controller.service as service
from sqlalchemy.orm import Session
from app.api.database.db import engine,Session
import pytz
from datetime import timedelta
import datetime

# for db_ekamek
from app.api.database import db_manager_ekamek
from app.api.database.db_ekamek import engine as engineEkamek,Session as SessionEkamek
from fastapi.responses import HTMLResponse
import app.api.controller.bpjs as bpjs

ws_bpjs = APIRouter()
models.Base.metadata.create_all(bind=engine)
models.Base.metadata.create_all(bind=engineEkamek)

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

def get_db_ekamek():
    db = SessionEkamek()
    try:
        yield db
    finally:
        db.close()

@ws_bpjs.get('/refpoli')
def refpoli():
    url = f'ref/poli'
    response = bpjs.get(url,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/')
    return response

@ws_bpjs.get('/refdokter')
def refdokter():
    url = f'ref/dokter'
    response = bpjs.get(url,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/')
    return response

@ws_bpjs.get('/jadwaldokter/kodepoli/{param1}/tanggal/{param2}')
def jadwaldokter(param1:str,param2:str):
    url = f'jadwaldokter/kodepoli/{param1}/tanggal/{param2}'
    response = bpjs.get(url,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/')
    return response

@ws_bpjs.get('/refpolifinger')
def referensipolifinger():
    return bpjs.get('/ref/poli/fp','https://apijkn.bpjs-kesehatan.go.id/antreanrs')

# @ws_bpjs.get('/ref/pasien/fp/identitas/{nik}/{noka}/noidentitas/{noidentitas}')
# def referensipasienfinger(nik:str,noka:str,noidentitas:str):
#     data = service.getantrol(f'/ref/pasien/fp/identitas/{nik}/{noka}/noidentitas/{noidentitas}')
#     return data

@ws_bpjs.get('/ref/pasien/fp/identitas/{param}/noidentitas/{noidentitas}')
def referensipasienfinger(param:str,noidentitas:str):
    return bpjs.get(f'/ref/pasien/fp/identitas/{param}/noidentitas/{noidentitas}','https://apijkn.bpjs-kesehatan.go.id/antreanrs')

@ws_bpjs.post('/jadwaldokter/updatejadwaldokter')
def updatejadwaldokter(payload:models.UpdateJadwalDokter):
    return bpjs.post('/jadwaldokter/updatejadwaldokter',payload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)


@ws_bpjs.post('/antrean/add')
def tambahAntrian(payload:models.TambahAntrian):
    return bpjs.post('antrean/add',payload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)

@ws_bpjs.post('/antrean/farmasi/add')
def tambahAntrianFarmasi(payload:models.TambahAntrianFarmasi):
    return bpjs.post('/antrean/farmasi/add',payload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)

@ws_bpjs.post('/antrean/updatewaktu')
def updateWaktu(payload:models.UpdateWaktu):
    twe = bpjs.post('/antrean/updatewaktu',payload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    print(twe)
    return twe

@ws_bpjs.post('/antrean/batal')
def antreanBatal(payload:models.BatalAntrian):
    return bpjs.post('antrean/batal',payload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)

@ws_bpjs.post('/antrean/getlisttask')
def getListTask(payload:models.TaskId):
    return bpjs.post('antrean/getlisttask',payload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)

@ws_bpjs.get('/dashboard/waktutunggu/tanggal/{pm1}/waktu/{pm2}')
def DashboardPertgl(pm1:str,pm2:str):
    return bpjs.get(f'/dashboard/waktutunggu/tanggal/{pm1}/waktu/{pm2}','https://apijkn.bpjs-kesehatan.go.id/antreanrs')

@ws_bpjs.get('/dashboard/waktutunggu/bulan/{Parameter1}/tahun/{Parameter2}/waktu/{Parameter3}')
def DashboardBulanTahun(Parameter1:str,Parameter2:str,Parameter3:str):
    return bpjs.get(f'/dashboard/waktutunggu/bulan/{Parameter1}/tahun/{Parameter2}/waktu/{Parameter3}','https://apijkn.bpjs-kesehatan.go.id/antreanrs')

@ws_bpjs.get('/antrean/pendaftaran/tanggal/{tanggal}')
def ListAntrianPertgl(tanggal:str):
    return bpjs.get(f'antrean/pendaftaran/tanggal/{tanggal}','https://apijkn.bpjs-kesehatan.go.id/antreanrs/')


@ws_bpjs.get('/antrean/pendaftaran/kodebooking/{kodebooking}')
def CariKodeBooking(kodebooking:str):
    return bpjs.get(f'antrean/pendaftaran/kodebooking/{kodebooking}','https://apijkn.bpjs-kesehatan.go.id/antreanrs/')

@ws_bpjs.get('/antrean/pendaftaran/aktif')
def AntreanBelumDilayani():
    return bpjs.get(f'antrean/pendaftaran/aktif','https://apijkn.bpjs-kesehatan.go.id/antreanrs/')

@ws_bpjs.get('/antrean/pendaftaran/kodepoli/{kodepoli}/kodedokter/{kodedokter}/hari/{hari}/jampraktek/{jampraktek}')
def AntreanBelumDilayaniPerPeriode(kodepoli:str,kodedokter:str,hari:str,jampraktek:str):
    return bpjs.get(f'antrean/pendaftaran/kodepoli/{kodepoli}/kodedokter/{kodedokter}/hari/{hari}/jampraktek/{jampraktek}','https://apijkn.bpjs-kesehatan.go.id/antreanrs/')
