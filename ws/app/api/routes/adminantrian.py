from typing import List,Union
from fastapi import Header, APIRouter,HTTPException,Depends

from app.api.database import db_manager
import datetime
from sqlalchemy.orm import Session
from app.api.database.db import engine,Session
import app.api.models.models as models
from app.api.controller.service import cekPoliDokter
import app.api.controller.service as service
import app.api.validation.validation as validation
from app.api.controller import bpjs,bpjs_vclaim
import pytz
import time
import json

adminantrian = APIRouter()
models.Base.metadata.create_all(bind=engine)


# for db_ekamek
from app.api.database import db_manager_ekamek
from app.api.database.db_ekamek import engine as engineEkamek,Session as SessionEkamek
from fastapi.responses import HTMLResponse

def milliseconds():
    from datetime import datetime, timezone, timedelta

    # Set the timezone to Asia/Jakarta
    jakarta_timezone = timezone(timedelta(hours=7))  # UTC+7

    # Get the current time in the specified timezone
    current_time = datetime.now(jakarta_timezone)

    # Convert to milliseconds since the epoch
    timestamp_milliseconds = int(current_time.timestamp() * 1000)
    return timestamp_milliseconds

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



@adminantrian.get('/statusantrianpertgl/{tanggalawal}/{tanggalakhir}')
async def statusantrianpertgl(tanggalawal:str,tanggalakhir:str,db:Session = Depends(get_db)):
    result = await db_manager.statusantrianpertgl(db = db,tanggalawal = tanggalawal,tanggalakhir = tanggalakhir)
 
    return {
        'metadata':{
            'code':200,
            'message':'Ok'
        },
        'response':result
    }

@adminantrian.get('/statusantrianpertglselesai/{tanggalawal}/{tanggalakhir}')
async def statusantrianpertglselesai(tanggalawal:str,tanggalakhir:str,db:Session = Depends(get_db)):
    result = await db_manager.statusantrianpertglselesai(db = db,tanggalawal = tanggalawal,tanggalakhir = tanggalakhir)
 
    return {
        'metadata':{
            'code':200,
            'message':'Ok'
        },
        'response':result
    }

@adminantrian.get('/statusantrianpertglbatal/{tanggalawal}/{tanggalakhir}')
async def statusantrianpertglbatal(tanggalawal:str,tanggalakhir:str,db:Session = Depends(get_db)):
    result = await db_manager.statusantrianpertglbatal(db = db,tanggalawal = tanggalawal,tanggalakhir = tanggalakhir)
 
    return {
        'metadata':{
            'code':200,
            'message':'Ok'
        },
        'response':result
    }

@adminantrian.get('/prosesantrian/{kodebooking}/{flag}')
async def prosesantrian(kodebooking:str,flag:str,db: Session = Depends(get_db)):
    # disini update task id setiap proses antrian ke ws bpjs
    payload = {
        'kodebooking': kodebooking,
        'taskid': flag,
        'waktu': milliseconds()
    }
    newPayload = models.UpdateWaktu(**payload)
    task_id = bpjs.post('antrean/updatewaktu',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    await db_manager.insert_taskid(db,kodebooking,'Hit Task Id '+flag,json.dumps(payload),json.dumps(task_id),"SUKSES" if task_id['metadata']['code'] == 200 else "GAGAL")
    
    if task_id['metadata']['code'] != 200:
        return task_id


    get = await db_manager.prosesantrian(db= db,kodebooking = kodebooking,flag=flag)
    if get>0:
        return {
            'metadata':{
                'message':'Ok',
                'code':200
            }
        }
    return {
        'metadata':{
            'message':'Gagal',
            'code':201
        }
    }

@adminantrian.get('/prosesantriantgl/{kodebooking}/{flag}/{tgl}')
async def prosesantriantgl(kodebooking: str, flag: str, tgl: str, db: Session = Depends(get_db)):
    try:
        # Parsing tgl string ke datetime object
        dt = datetime.datetime.strptime(tgl, '%Y-%m-%d %H:%M:%S')
        millis = int(dt.timestamp() * 1000)
    except ValueError:
        return {
            'metadata': {
                'message': 'Format tanggal tidak valid. Gunakan format Y-m-d H:i:s',
                'code': 400
            }
        }

    payload = {
        'kodebooking': kodebooking,
        'taskid': flag,
        'waktu': millis
    }

    newPayload = models.UpdateWaktu(**payload)
    task_id = bpjs.post(
        'antrean/updatewaktu',
        newPayload,
        'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',
        True
    )

    await db_manager.insert_taskid(
        db, kodebooking, 'Hit Task Id ' + flag,
        json.dumps(payload), json.dumps(task_id),
        "SUKSES" if task_id['metadata']['code'] == 200 else "GAGAL"
    )

    if task_id['metadata']['code'] != 200:
        return task_id

    get = await db_manager.prosesantrian(db=db, kodebooking=kodebooking, flag=flag)
    if get > 0:
        return {
            'metadata': {
                'message': 'Ok',
                'code': 200
            }
        }

    return {
        'metadata': {
            'message': 'Gagal',
            'code': 201
        }
    }

@adminantrian.post('/batalantrian')
async def batalantrean(payload:models.BatalAntrian,db: Session = Depends(get_db)):
    # disini update task id setiap proses antrian ke ws bpjs
    task_id = bpjs.post('antrean/batal',payload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    # if task_id['metadata']['code'] != 200:
    #     return task_id


    get = await db_manager.carikodebookingdanupdate(db= db,payload=payload)
    return get
    # if get['']:
    #     return {
    #         'metadata':{
    #             'message':'Ok',
    #             'code':200
    #         }
    #     }
    # return {
    #     'metadata':{
    #         'message':'Gagal',
    #         'code':201
    #     }
    # }

@adminantrian.post('/panggil_admisi')
async def panggil_admisi(payload:models.BatalAntrian,db: Session = Depends(get_db)):
    
    get = await db_manager.prosesantrian(db= db,kodebooking=payload.kodebooking,flag='2')
    if get>0:
        return {
            'metadata':{
                'message':'Ok',
                'code':200
            }
        }
    return {
        'metadata':{
            'message':'Gagal',
            'code':201
        }
    }

@adminantrian.post('/v2/ambilantrian')
async def ambilantrian(payload:models.Ambilantrian,db: Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):

    # cek pasien dari db ekamek
    norm = 0
    cekPasien = await db_manager_ekamek.caridatapasien(db_ekamek,payload.nomorkartu)
    if not cekPasien: # tandanya pasien gaada
        # cek di pasien baru daftar di antrol
        cekPasienBaru = await db_manager.cekPasienBaruExist(db = db,nomorkartu = payload.nomorkartu,norm='1')
        if not cekPasienBaru:
            return {
                'metaData' :{
                    'message': 'Data pasien ini tidak ditemukan, silahkan Melakukan Registrasi Pasien Baru',
                    'code':202
                }
            } 
        else:
            namaPasien = cekPasienBaru.nama   
            payload.pasienbaru = '1'
            norm = cekPasienBaru.norm

    else:
        norm = cekPasien[2]
        namaPasien = cekPasien[1]
    
    # check pernah daftar atau belum jika pernah maka bukan pasien baru
    cekPasienBarulama = await db_manager.cekPasienbarulama(db= db,nomorkartu = payload.nomorkartu)
    if not cekPasienBarulama:
        payload.pasienbaru = '1'

    checkExist = await db_manager.checkAntrianExist(db,payload.nomorkartu,payload.tanggalperiksa)
    if checkExist:
        return validation.handleErrorAdmin('Nomor Antrean Hanya Dapat Diambil 1 Kali Pada Tanggal Yang Sama')
    
    cekPoli = await db_manager_ekamek.carinamapoli(db_ekamek,payload.kodepoli)
    if not cekPoli:
        return validation.handleErrorAdmin('Poli Tidak Ditemukan')

    cekDokterDanJadwal = service.cekjadwaldokter(payload.kodepoli,payload.tanggalperiksa)
    if not cekDokterDanJadwal:
        return validation.handleErrorAdmin('Koneksi dengan WS BPJS Antrian Cek Jadwal Dokter Gagal!')
    
    if cekDokterDanJadwal['metadata']['code'] != 200:
        return validation.handleErrorAdmin(cekDokterDanJadwal['metadata']['message'])
    
    resultJadwalDokter = {}
    for val in cekDokterDanJadwal['response']:
        print(val)
        if val['kodedokter'] == int(payload.kodedokter):
            resultJadwalDokter = val

    if resultJadwalDokter == {}:
        # return validation.handleErrorAdmin('Jadwal Dokter Tidak Ditemukan Pada Tanggal Tersebut!')
        return validation.handleErrorAdmin(f"Jadwal Dokter Tersebut Belum Tersedia,Silahkan Reschedule Tanggal dan Jam Praktek Lainnya")



    cekDokter = await db_manager_ekamek.carinamadokter(db_ekamek,payload.kodedokter)
    if not cekDokter:
        return validation.handleErrorAdmin('Kode Dokter Tidak sesuai')

    payload.namadokter = resultJadwalDokter['namadokter']
    payload.namapoli = resultJadwalDokter['namasubspesialis']
    payload.nama = namaPasien

    cekTotalAntrian = await db_manager.cekTotalAntrian(db=db,kodehfis = payload.kodedokter,pertgl=payload.tanggalperiksa)
    # estimasi waktu dilayani
    totalAntrian = int(cekTotalAntrian['count'])
    if totalAntrian == 0:
        totalAntrian = 1
    waktuTotalAntrian = (1 if totalAntrian == 0 else totalAntrian) * 10 # (satu pelayanan itu 10 menit)
    strWaktuPelayananMulai = payload.tanggalperiksa + ' 08:00:00'
    waktuPelayananMulai = datetime.datetime.strptime(strWaktuPelayananMulai, '%Y-%m-%d %H:%M:%S')

    validasiPeriksaHariIni = validation.validasiHariIni(payload.tanggalperiksa)
    if validasiPeriksaHariIni:
        splitJadwalJamMulaiSelesai = validation.validasiJadwalMelebihiJam(payload.jampraktek)
        # if not splitJadwalJamMulaiSelesai:
        #     return validation.handleErrorAdmin(f"Pendaftaran Ke Poli ({resultJadwalDokter['namasubspesialis']}) Sudah Tutup Jam {payload.jampraktek.split('-')[1]}")

        # added feature
        # cek jika pasien mendaftar selama pelayanan berlangsung ( misal jam 08.00 waktu mulai)
        # dan pasien mendaftar di jam 09:00 maka waktu kira kira dilayani di jam 09: ditambah dengan menit total
        # antrian yang akan dilayani
        # if()
        # jakarta_timezone = pytz.timezone('Asia/Jakarta')
        now = datetime.datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        dt_string = datetime.datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
        # print(dt_string)
        # print('-----ini-----')
        
        # jika pasien masuuuk melebih jam praktek maka lanjutkan jam praktek + count berapa tersisa antrian
        if dt_string>waktuPelayananMulai:
            waktuPelayananMulai = dt_string
        # end added
    
    estimasidilayani = waktuPelayananMulai + datetime.timedelta(minutes = waktuTotalAntrian)
    estimasidilayani = round(int(estimasidilayani.timestamp()) * 1000)
    payload.estimasidilayani = estimasidilayani
    payload.sisakuotajkn = int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian)
    payload.kuotajkn = int(resultJadwalDokter['kapasitaspasien'])
    payload.sisakuotanonjkn = int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian)
    payload.kuotanonjkn = int(resultJadwalDokter['kapasitaspasien'])

    try:
        # Attempt to convert the date string to a datetime object
        tanggalperiksa_date = datetime.datetime.strptime(payload.tanggalperiksa, '%Y-%m-%d')
    except ValueError:
        # Handle the case where the date string is not a valid date
        return validation.handleErrorAdmin("Tanggal Periksa Tidak Valid")
        # Handle this error as appropriate for your application


    insert = await db_manager.insert_antrian_poli_onsite(db= db,payload = payload)
    if isinstance(insert, dict):
        return 
        
    # get detil peserta
    # /Peserta/nokartu/{parameter 1}/tglSEP/{parameter 2}
    # getdetilpeserta = bpjs_vclaim.get_vclaim('/Peserta/nokartu/'+payload.nokartu+'/tglSEP/' + payload.tanggalperiksa)

    # get rujukan by no kartu
    # BASE URL}/{Service Name}/Rujukan/Peserta/{parameter}
    # {BASE URL}/{Service Name}/Rujukan/RS/Peserta/{parameter}

    # jumlah sep
    # {BASE URL}/{Service Name}/Rujukan/JumlahSEP/{Parameter 1}/{Parameter 2}

    # get id poli by poli_bpjs
    # poliklinik.poli_bpjs -> id_poli

    # get id_dokter by dokter npjs
    # data_d

    # 

    # update antrian online v.2
    # 22/09/2024 17:19
    # insert ke api -> antrol/insert_daftar_ulang_new POST 
    reqdata = {
        "reservasi": insert.kodebooking,
        "no_medrec": norm,
        "xcreate": "ANTROL_ONSITE",
        "kelasrawat": "1", #? dari data peserta
        "asalrujukan": "1", #? dari data rujukan
        "tglrujukan": "2024-09-12", #? dari data rujukan
        "ppkrujukan": "03110502", #? dari data rujukan
        "jns_kunj": "LAMA", 
        "namafaskes": "GAMBOK", #? dari data rujukan
        "prb": "PRB : DM, JT", #? dari data peserta
        "online": "0", 
        "noreservasi": "", #kodebooking
        "noreg_asal_konsul": "",
        "tgl_kunjungan": payload.tanggalperiksa,
        "cara_bayar": "BPJS",
        "cara_dtg": "SENDIRI",
        "cara_kunj": "RUJUKAN PUSKESMAS", #dari data rujukan #"RUJUKAN PUSKESMAS","RUJUKAN RS"
        "no_bpjs": payload.nomorkartu,
        "id_kontraktor": "1",
        "no_sep": "", 
        "no_rujukan": "031105020924P000004", #dari data rujukan
        "tujuan_kunj": "0", #otomatis kan bisa
        "kd_penunjang": "", #otomatis kan bisa
        "assesment_pel": "", #otomatis kan bisa
        "nosurat_skdp_sep": "", #otomatis kan bisa
        "dpjp_suratkontrol": "", #otomatis kan bisa
        "alber": "sakit",
        "pasdatDg": "klg",
        "jenis_kecelakaan": "",
        "lokasi_kecelakaan": "",
        "kll_tgl_kejadian": "",
        "kll_ketkejadian": "",
        "hubungan": "",
        "id_poli": "BH00~MAT", #ambil dari poliklinik
        "id_dokter": "56-298316-dr. Putrigusti Admira, Sp. M",#ambil dari data_dokter
        "dokter_bpjs": "298316-Tenaga Medis 298316",
        "diagnosa": "A18.5@Tuberculosis of eye",#ambil dari rujukan
        "id_diagnosa": "",
        "kelas_pasien": "II", #ambil dari rujukan
        "no_telp": "",
        "catatan": "",
        "cetak_kartu1": ""
    }

    return {
        'response':{
            'nomorantrean':insert.nomorantrian, #2 digit nama poli didepan + max dari antrian per poli per dokter + 1 
            'angkaantrean':insert.angkaantrean, #max dari antrian per poli per dokter + 1 
            'kodebooking':insert.kodebooking, #nomr + angkaantrean 
            'namapoli':resultJadwalDokter['namasubspesialis'], #nm_poli <- poliklinik
            'norm': norm, #nomr
            'namadokter': resultJadwalDokter['namadokter'], #nm_dokter <- data_dokter
            'estimasidilayani':estimasidilayani, # timestamp epoch tanggal_periksa: jam pelayanan awal  + (jumlah pasien * 15 menit)
            'sisakuotajkn': int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian), #50 - jml antrian bpjs poli 
            'kuotajkn':int(resultJadwalDokter['kapasitaspasien']), #nomr
            'sisakuotanonjkn':int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian), #50 - jml antrian non bpjs poli 
            'kuotanonjkn':int(resultJadwalDokter['kapasitaspasien']), #nomr
            'keterangan':'', #nomr
            
        },
        'metaData': {
            'message':'Ok',
            'code':200
        }
    }


@adminantrian.get('/vclaim_debug')
async def vclaim_debug(db: Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):

 # get detil peserta
    # /Peserta/nokartu/{parameter 1}/tglSEP/{parameter 2}
    getdetilpeserta = bpjs_vclaim.get_vclaim('/Peserta/nokartu/'+'0002042972807'+'/tglSEP/' + '2024-10-10')
    print(getdetilpeserta)
    return {'ok'}
    # get rujukan by no kartu
    # BASE URL}/{Service Name}/Rujukan/Peserta/{parameter}
    # {BASE URL}/{Service Name}/Rujukan/RS/Peserta/{parameter}

    # jumlah sep
    # {BASE URL}/{Service Name}/Rujukan/JumlahSEP/{Parameter 1}/{Parameter 2}

    # get id poli by poli_bpjs
    # poliklinik.poli_bpjs -> id_poli

    # get id_dokter by dokter npjs
    # data_d


@adminantrian.post('/ambilantriannonregister')
async def ambilantrian(payload:models.Ambilantrian,db: Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):
    
    # cek pasien dari db ekamek
    norm = 0
    cekPasien = await db_manager_ekamek.caridatapasien(db_ekamek,payload.nomorkartu)
    if not cekPasien: # tandanya pasien gaada
        # cek di pasien baru daftar di antrol
        cekPasienBaru = await db_manager.cekPasienBaruExist(db = db,nomorkartu = payload.nomorkartu,norm='1')
        if not cekPasienBaru:
            return {
                'metaData' :{
                    'message': 'Data pasien ini tidak ditemukan, silahkan Melakukan Registrasi Pasien Baru',
                    'code':202
                }
            } 
        else:
            namaPasien = cekPasienBaru.nama   
            payload.pasienbaru = '1'
            norm = cekPasienBaru.norm

    else:
        norm = cekPasien[2]
        namaPasien = cekPasien[1]
    
    # check pernah daftar atau belum jika pernah maka bukan pasien baru
    cekPasienBarulama = await db_manager.cekPasienbarulama(db= db,nomorkartu = payload.nomorkartu)
    if not cekPasienBarulama:
        payload.pasienbaru = '1'

    checkExist = await db_manager.checkAntrianExist(db,payload.nomorkartu,payload.tanggalperiksa)
    if checkExist:
        return validation.handleErrorAdmin('Nomor Antrean Hanya Dapat Diambil 1 Kali Pada Tanggal Yang Sama')
    
    cekPoli = await db_manager_ekamek.carinamapoli(db_ekamek,payload.kodepoli)
    if not cekPoli:
        return validation.handleErrorAdmin('Poli Tidak Ditemukan')

    cekDokterDanJadwal = service.cekjadwaldokter(payload.kodepoli,payload.tanggalperiksa)
    if not cekDokterDanJadwal:
        return validation.handleErrorAdmin('Koneksi dengan WS BPJS Antrian Cek Jadwal Dokter Gagal!')
    
    if cekDokterDanJadwal['metadata']['code'] != 200:
        return validation.handleErrorAdmin(cekDokterDanJadwal['metadata']['message'])
    
    resultJadwalDokter = {}
    for val in cekDokterDanJadwal['response']:
        print(val)
        if val['kodedokter'] == int(payload.kodedokter):
            resultJadwalDokter = val

    if resultJadwalDokter == {}:
        # return validation.handleErrorAdmin('Jadwal Dokter Tidak Ditemukan Pada Tanggal Tersebut!')
        return validation.handleErrorAdmin(f"Jadwal Dokter Tersebut Belum Tersedia,Silahkan Reschedule Tanggal dan Jam Praktek Lainnya")



    cekDokter = await db_manager_ekamek.carinamadokter(db_ekamek,payload.kodedokter)
    if not cekDokter:
        return validation.handleErrorAdmin('Kode Dokter Tidak sesuai')

    payload.namadokter = resultJadwalDokter['namadokter']
    payload.namapoli = resultJadwalDokter['namasubspesialis']
    payload.nama = namaPasien

    cekTotalAntrian = await db_manager.cekTotalAntrian(db=db,kodehfis = payload.kodedokter,pertgl=payload.tanggalperiksa)
    # estimasi waktu dilayani
    totalAntrian = int(cekTotalAntrian['count'])
    if totalAntrian == 0:
        totalAntrian = 1
    waktuTotalAntrian = (1 if totalAntrian == 0 else totalAntrian) * 10 # (satu pelayanan itu 10 menit)
    strWaktuPelayananMulai = payload.tanggalperiksa + ' 08:00:00'
    waktuPelayananMulai = datetime.datetime.strptime(strWaktuPelayananMulai, '%Y-%m-%d %H:%M:%S')

    validasiPeriksaHariIni = validation.validasiHariIni(payload.tanggalperiksa)
    if validasiPeriksaHariIni:
        splitJadwalJamMulaiSelesai = validation.validasiJadwalMelebihiJam(payload.jampraktek)
        # if not splitJadwalJamMulaiSelesai:
        #     return validation.handleErrorAdmin(f"Pendaftaran Ke Poli ({resultJadwalDokter['namasubspesialis']}) Sudah Tutup Jam {payload.jampraktek.split('-')[1]}")

        # added feature
        # cek jika pasien mendaftar selama pelayanan berlangsung ( misal jam 08.00 waktu mulai)
        # dan pasien mendaftar di jam 09:00 maka waktu kira kira dilayani di jam 09: ditambah dengan menit total
        # antrian yang akan dilayani
        # if()
        # jakarta_timezone = pytz.timezone('Asia/Jakarta')
        now = datetime.datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        dt_string = datetime.datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
        # print(dt_string)
        # print('-----ini-----')
        
        # jika pasien masuuuk melebih jam praktek maka lanjutkan jam praktek + count berapa tersisa antrian
        if dt_string>waktuPelayananMulai:
            waktuPelayananMulai = dt_string
        # end added
    
    estimasidilayani = waktuPelayananMulai + datetime.timedelta(minutes = waktuTotalAntrian)
    estimasidilayani = round(int(estimasidilayani.timestamp()) * 1000)
    payload.estimasidilayani = estimasidilayani
    payload.sisakuotajkn = int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian)
    payload.kuotajkn = int(resultJadwalDokter['kapasitaspasien'])
    payload.sisakuotanonjkn = int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian)
    payload.kuotanonjkn = int(resultJadwalDokter['kapasitaspasien'])

    try:
        # Attempt to convert the date string to a datetime object
        tanggalperiksa_date = datetime.datetime.strptime(payload.tanggalperiksa, '%Y-%m-%d')
    except ValueError:
        # Handle the case where the date string is not a valid date
        return validation.handleErrorAdmin("Tanggal Periksa Tidak Valid")
        # Handle this error as appropriate for your application


    insert = await db_manager.insert_antrian_poli_onsite(db= db,payload = payload)
    if isinstance(insert, dict):
        return insert

    bodyreq = {
        'nomorkartu': payload.nomorkartu,
        'kodepoli': payload.kodepoli,
        'jeniskunjungan': payload.jeniskunjungan,
        'nomorreferensi':payload.nomorreferensi,
        'kodedokter':payload.kodedokter,
        'kodebooking':insert.kodebooking,
        'norm':norm,
        'tanggalperiksa':payload.tanggalperiksa,
        'kodepoli':payload.kodepoli,
        'noantrian':insert.angkaantrean
    }
    # return bodyreq
    # reqdata = await insert_daftar_ulang(bodyreq,db_ekamek)
    await db_manager_ekamek.tambahhistoryantriandirect(db=db_ekamek,kodebooking=insert.kodebooking)

    # update antrian online v.2
    # 22/09/2024 17:19
    # insert ke api -> antrol/insert_daftar_ulang_new POST 
    # reqdata = {
    #     "reservasi": insert.kodebooking,
    #     "no_medrec": norm,
    #     "xcreate": "ANTROL_ONSITE",
    #     "kelasrawat": "1", #?
    #     "asalrujukan": "1", #?
    #     "tglrujukan": "2024-09-12", #?
    #     "ppkrujukan": "03110502", #?
    #     "jns_kunj": "LAMA", #?
    #     "namafaskes": "GAMBOK", #? 
    #     "prb": "PRB : DM, JT", #?
    #     "online": "0", 
    #     "noreservasi": "",
    #     "noreg_asal_konsul": "",
    #     "tgl_kunjungan": payload.tanggalperiksa,
    #     "cara_bayar": "BPJS",
    #     "cara_dtg": "SENDIRI",
    #     "cara_kunj": "RUJUKAN PUSKESMAS", #"RUJUKAN PUSKESMAS","RUJUKAN RS"
    #     "no_bpjs": payload.nomorkartu,
    #     "id_kontraktor": "1",
    #     "no_sep": "",
    #     "no_rujukan": "031105020924P000004",
    #     "tujuan_kunj": "0",
    #     "kd_penunjang": "",
    #     "assesment_pel": "",
    #     "nosurat_skdp_sep": "",
    #     "dpjp_suratkontrol": "",
    #     "alber": "sakit",
    #     "pasdatDg": "klg",
    #     "jenis_kecelakaan": "",
    #     "lokasi_kecelakaan": "",
    #     "kll_tgl_kejadian": "2024-09-22",
    #     "kll_ketkejadian": "",
    #     "hubungan": "",
    #     "id_poli": "BH00~MAT",
    #     "id_dokter": "56-298316-dr. Putrigusti Admira, Sp. M",
    #     "dokter_bpjs": "298316-Tenaga Medis 298316",
    #     "diagnosa": "A18.5@Tuberculosis of eye",
    #     "id_diagnosa": "",
    #     "kelas_pasien": "II",
    #     "no_telp": "1111111111111",
    #     "catatan": "",
    #     "cetak_kartu1": "130003"
    # }

    return {
        'response':{
            'nomorantrean':insert.nomorantrian, #2 digit nama poli didepan + max dari antrian per poli per dokter + 1 
            'angkaantrean':insert.angkaantrean, #max dari antrian per poli per dokter + 1 
            'kodebooking':insert.kodebooking, #nomr + angkaantrean 
            'namapoli':resultJadwalDokter['namasubspesialis'], #nm_poli <- poliklinik
            'norm': norm, #nomr
            'namadokter': resultJadwalDokter['namadokter'], #nm_dokter <- data_dokter
            'estimasidilayani':estimasidilayani, # timestamp epoch tanggal_periksa: jam pelayanan awal  + (jumlah pasien * 15 menit)
            'sisakuotajkn': int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian), #50 - jml antrian bpjs poli 
            'kuotajkn':int(resultJadwalDokter['kapasitaspasien']), #nomr
            'sisakuotanonjkn':int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian), #50 - jml antrian non bpjs poli 
            'kuotanonjkn':int(resultJadwalDokter['kapasitaspasien']), #nomr
            'keterangan':'', #nomr
            
        },
        'metaData': {
            'message':'Ok',
            'code':200
        }
    }



@adminantrian.post('/ambilantrian')
async def ambilantrian(payload:models.Ambilantrian,db: Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):
    
    # cek pasien dari db ekamek
    norm = 0
    cekPasien = await db_manager_ekamek.caridatapasien(db_ekamek,payload.nomorkartu)
    if not cekPasien: # tandanya pasien gaada
        # cek di pasien baru daftar di antrol
        cekPasienBaru = await db_manager.cekPasienBaruExist(db = db,nomorkartu = payload.nomorkartu,norm='1')
        if not cekPasienBaru:
            return {
                'metaData' :{
                    'message': 'Data pasien ini tidak ditemukan, silahkan Melakukan Registrasi Pasien Baru',
                    'code':202
                }
            } 
        else:
            namaPasien = cekPasienBaru.nama   
            payload.pasienbaru = '1'
            norm = cekPasienBaru.norm

    else:
        norm = cekPasien[2]
        namaPasien = cekPasien[1]
    
    # check pernah daftar atau belum jika pernah maka bukan pasien baru
    cekPasienBarulama = await db_manager.cekPasienbarulama(db= db,nomorkartu = payload.nomorkartu)
    if not cekPasienBarulama:
        payload.pasienbaru = '1'

    checkExist = await db_manager.checkAntrianExist(db,payload.nomorkartu,payload.tanggalperiksa)
    if checkExist:
        return validation.handleErrorAdmin('Nomor Antrean Hanya Dapat Diambil 1 Kali Pada Tanggal Yang Sama')
    
    cekPoli = await db_manager_ekamek.carinamapoli(db_ekamek,payload.kodepoli)
    if not cekPoli:
        return validation.handleErrorAdmin('Poli Tidak Ditemukan')

    cekDokterDanJadwal = service.cekjadwaldokter(payload.kodepoli,payload.tanggalperiksa)
    if not cekDokterDanJadwal:
        return validation.handleErrorAdmin('Koneksi dengan WS BPJS Antrian Cek Jadwal Dokter Gagal!')
    
    if cekDokterDanJadwal['metadata']['code'] != 200:
        return validation.handleErrorAdmin(cekDokterDanJadwal['metadata']['message'])
    
    resultJadwalDokter = {}
    for val in cekDokterDanJadwal['response']:
        print(val)
        if val['kodedokter'] == int(payload.kodedokter):
            resultJadwalDokter = val

    if resultJadwalDokter == {}:
        # return validation.handleErrorAdmin('Jadwal Dokter Tidak Ditemukan Pada Tanggal Tersebut!')
        return validation.handleErrorAdmin(f"Jadwal Dokter Tersebut Belum Tersedia,Silahkan Reschedule Tanggal dan Jam Praktek Lainnya")



    cekDokter = await db_manager_ekamek.carinamadokter(db_ekamek,payload.kodedokter)
    if not cekDokter:
        return validation.handleErrorAdmin('Kode Dokter Tidak sesuai')

    payload.namadokter = resultJadwalDokter['namadokter']
    payload.namapoli = resultJadwalDokter['namasubspesialis']
    payload.nama = namaPasien

    cekTotalAntrian = await db_manager.cekTotalAntrian(db=db,kodehfis = payload.kodedokter,pertgl=payload.tanggalperiksa)
    # estimasi waktu dilayani
    totalAntrian = int(cekTotalAntrian['count'])
    if totalAntrian == 0:
        totalAntrian = 1
    waktuTotalAntrian = (1 if totalAntrian == 0 else totalAntrian) * 10 # (satu pelayanan itu 10 menit)
    strWaktuPelayananMulai = payload.tanggalperiksa + ' 08:00:00'
    waktuPelayananMulai = datetime.datetime.strptime(strWaktuPelayananMulai, '%Y-%m-%d %H:%M:%S')

    validasiPeriksaHariIni = validation.validasiHariIni(payload.tanggalperiksa)
    if validasiPeriksaHariIni:
        splitJadwalJamMulaiSelesai = validation.validasiJadwalMelebihiJam(payload.jampraktek)
        # if not splitJadwalJamMulaiSelesai:
        #     return validation.handleErrorAdmin(f"Pendaftaran Ke Poli ({resultJadwalDokter['namasubspesialis']}) Sudah Tutup Jam {payload.jampraktek.split('-')[1]}")

        # added feature
        # cek jika pasien mendaftar selama pelayanan berlangsung ( misal jam 08.00 waktu mulai)
        # dan pasien mendaftar di jam 09:00 maka waktu kira kira dilayani di jam 09: ditambah dengan menit total
        # antrian yang akan dilayani
        # if()
        # jakarta_timezone = pytz.timezone('Asia/Jakarta')
        now = datetime.datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        dt_string = datetime.datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
        # print(dt_string)
        # print('-----ini-----')
        
        # jika pasien masuuuk melebih jam praktek maka lanjutkan jam praktek + count berapa tersisa antrian
        if dt_string>waktuPelayananMulai:
            waktuPelayananMulai = dt_string
        # end added
    
    estimasidilayani = waktuPelayananMulai + datetime.timedelta(minutes = waktuTotalAntrian)
    estimasidilayani = round(int(estimasidilayani.timestamp()) * 1000)
    payload.estimasidilayani = estimasidilayani
    payload.sisakuotajkn = int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian)
    payload.kuotajkn = int(resultJadwalDokter['kapasitaspasien'])
    payload.sisakuotanonjkn = int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian)
    payload.kuotanonjkn = int(resultJadwalDokter['kapasitaspasien'])

    try:
        # Attempt to convert the date string to a datetime object
        tanggalperiksa_date = datetime.datetime.strptime(payload.tanggalperiksa, '%Y-%m-%d')
    except ValueError:
        # Handle the case where the date string is not a valid date
        return validation.handleErrorAdmin("Tanggal Periksa Tidak Valid")
        # Handle this error as appropriate for your application


    insert = await db_manager.insert_antrian_poli_onsite(db= db,payload = payload)
    if isinstance(insert, dict):
        return insert

    bodyreq = {
        'nomorkartu': payload.nomorkartu,
        'kodepoli': payload.kodepoli,
        'jeniskunjungan': payload.jeniskunjungan,
        'nomorreferensi':payload.nomorreferensi,
        'kodedokter':payload.kodedokter,
        'kodebooking':insert.kodebooking,
        'norm':norm,
        'tanggalperiksa':payload.tanggalperiksa,
        'kodepoli':payload.kodepoli,
        'noantrian':insert.angkaantrean
    }
    # return bodyreq
    reqdata = await insert_daftar_ulang(bodyreq,db_ekamek)

    # update antrian online v.2
    # 22/09/2024 17:19
    # insert ke api -> antrol/insert_daftar_ulang_new POST 
    # reqdata = {
    #     "reservasi": insert.kodebooking,
    #     "no_medrec": norm,
    #     "xcreate": "ANTROL_ONSITE",
    #     "kelasrawat": "1", #?
    #     "asalrujukan": "1", #?
    #     "tglrujukan": "2024-09-12", #?
    #     "ppkrujukan": "03110502", #?
    #     "jns_kunj": "LAMA", #?
    #     "namafaskes": "GAMBOK", #? 
    #     "prb": "PRB : DM, JT", #?
    #     "online": "0", 
    #     "noreservasi": "",
    #     "noreg_asal_konsul": "",
    #     "tgl_kunjungan": payload.tanggalperiksa,
    #     "cara_bayar": "BPJS",
    #     "cara_dtg": "SENDIRI",
    #     "cara_kunj": "RUJUKAN PUSKESMAS", #"RUJUKAN PUSKESMAS","RUJUKAN RS"
    #     "no_bpjs": payload.nomorkartu,
    #     "id_kontraktor": "1",
    #     "no_sep": "",
    #     "no_rujukan": "031105020924P000004",
    #     "tujuan_kunj": "0",
    #     "kd_penunjang": "",
    #     "assesment_pel": "",
    #     "nosurat_skdp_sep": "",
    #     "dpjp_suratkontrol": "",
    #     "alber": "sakit",
    #     "pasdatDg": "klg",
    #     "jenis_kecelakaan": "",
    #     "lokasi_kecelakaan": "",
    #     "kll_tgl_kejadian": "2024-09-22",
    #     "kll_ketkejadian": "",
    #     "hubungan": "",
    #     "id_poli": "BH00~MAT",
    #     "id_dokter": "56-298316-dr. Putrigusti Admira, Sp. M",
    #     "dokter_bpjs": "298316-Tenaga Medis 298316",
    #     "diagnosa": "A18.5@Tuberculosis of eye",
    #     "id_diagnosa": "",
    #     "kelas_pasien": "II",
    #     "no_telp": "1111111111111",
    #     "catatan": "",
    #     "cetak_kartu1": "130003"
    # }

    return {
        'response':{
            'nomorantrean':insert.nomorantrian, #2 digit nama poli didepan + max dari antrian per poli per dokter + 1 
            'angkaantrean':insert.angkaantrean, #max dari antrian per poli per dokter + 1 
            'kodebooking':insert.kodebooking, #nomr + angkaantrean 
            'namapoli':resultJadwalDokter['namasubspesialis'], #nm_poli <- poliklinik
            'norm': norm, #nomr
            'namadokter': resultJadwalDokter['namadokter'], #nm_dokter <- data_dokter
            'estimasidilayani':estimasidilayani, # timestamp epoch tanggal_periksa: jam pelayanan awal  + (jumlah pasien * 15 menit)
            'sisakuotajkn': int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian), #50 - jml antrian bpjs poli 
            'kuotajkn':int(resultJadwalDokter['kapasitaspasien']), #nomr
            'sisakuotanonjkn':int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian), #50 - jml antrian non bpjs poli 
            'kuotanonjkn':int(resultJadwalDokter['kapasitaspasien']), #nomr
            'keterangan':'', #nomr
            
        },
        'metaData': {
            'message':'Ok',
            'code':200
        }
    }

@adminantrian.post('/ambilantrianlamaold')
async def ambilantrian(payload:models.Ambilantrian,db: Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):
    
    # cek pasien dari db ekamek
    norm = 0
    cekPasien = await db_manager_ekamek.caridatapasien(db_ekamek,payload.nomorkartu)
    if not cekPasien: # tandanya pasien gaada
        # cek di pasien baru daftar di antrol
        cekPasienBaru = await db_manager.cekPasienBaruExist(db = db,nomorkartu = payload.nomorkartu,norm='1')
        if not cekPasienBaru:
            return {
                'metaData' :{
                    'message': 'Data pasien ini tidak ditemukan, silahkan Melakukan Registrasi Pasien Baru',
                    'code':202
                }
            } 
        else:
            namaPasien = cekPasienBaru.nama   
            payload.pasienbaru = '1'
            norm = cekPasienBaru.norm

    else:
        norm = cekPasien[2]
        namaPasien = cekPasien[1]
    
    # check pernah daftar atau belum jika pernah maka bukan pasien baru
    cekPasienBarulama = await db_manager.cekPasienbarulama(db= db,nomorkartu = payload.nomorkartu)
    if not cekPasienBarulama:
        payload.pasienbaru = '1'

    checkExist = await db_manager.checkAntrianExist(db,payload.nomorkartu,payload.tanggalperiksa)
    if checkExist:
        return validation.handleErrorAdmin('Nomor Antrean Hanya Dapat Diambil 1 Kali Pada Tanggal Yang Sama')
    
    cekPoli = await db_manager_ekamek.carinamapoli(db_ekamek,payload.kodepoli)
    if not cekPoli:
        return validation.handleErrorAdmin('Poli Tidak Ditemukan')

    cekDokterDanJadwal = service.cekjadwaldokter(payload.kodepoli,payload.tanggalperiksa)
    if not cekDokterDanJadwal:
        return validation.handleErrorAdmin('Koneksi dengan WS BPJS Antrian Cek Jadwal Dokter Gagal!')
    
    if cekDokterDanJadwal['metadata']['code'] != 200:
        return validation.handleErrorAdmin(cekDokterDanJadwal['metadata']['message'])
    
    resultJadwalDokter = {}
    for val in cekDokterDanJadwal['response']:
        print(val)
        if val['kodedokter'] == int(payload.kodedokter):
            resultJadwalDokter = val

    if resultJadwalDokter == {}:
        # return validation.handleErrorAdmin('Jadwal Dokter Tidak Ditemukan Pada Tanggal Tersebut!')
        return validation.handleErrorAdmin(f"Jadwal Dokter Tersebut Belum Tersedia,Silahkan Reschedule Tanggal dan Jam Praktek Lainnya")



    cekDokter = await db_manager_ekamek.carinamadokter(db_ekamek,payload.kodedokter)
    if not cekDokter:
        return validation.handleErrorAdmin('Kode Dokter Tidak sesuai')

    payload.namadokter = resultJadwalDokter['namadokter']
    payload.namapoli = resultJadwalDokter['namasubspesialis']
    payload.nama = namaPasien

    cekTotalAntrian = await db_manager.cekTotalAntrian(db=db,kodehfis = payload.kodedokter,pertgl=payload.tanggalperiksa)
    # estimasi waktu dilayani
    totalAntrian = int(cekTotalAntrian['count'])
    if totalAntrian == 0:
        totalAntrian = 1
    waktuTotalAntrian = (1 if totalAntrian == 0 else totalAntrian) * 10 # (satu pelayanan itu 10 menit)
    strWaktuPelayananMulai = payload.tanggalperiksa + ' 08:00:00'
    waktuPelayananMulai = datetime.datetime.strptime(strWaktuPelayananMulai, '%Y-%m-%d %H:%M:%S')

    validasiPeriksaHariIni = validation.validasiHariIni(payload.tanggalperiksa)
    if validasiPeriksaHariIni:
        splitJadwalJamMulaiSelesai = validation.validasiJadwalMelebihiJam(payload.jampraktek)
        # if not splitJadwalJamMulaiSelesai:
        #     return validation.handleErrorAdmin(f"Pendaftaran Ke Poli ({resultJadwalDokter['namasubspesialis']}) Sudah Tutup Jam {payload.jampraktek.split('-')[1]}")

        # added feature
        # cek jika pasien mendaftar selama pelayanan berlangsung ( misal jam 08.00 waktu mulai)
        # dan pasien mendaftar di jam 09:00 maka waktu kira kira dilayani di jam 09: ditambah dengan menit total
        # antrian yang akan dilayani
        # if()
        # jakarta_timezone = pytz.timezone('Asia/Jakarta')
        now = datetime.datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        dt_string = datetime.datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
        # print(dt_string)
        # print('-----ini-----')
        
        # jika pasien masuuuk melebih jam praktek maka lanjutkan jam praktek + count berapa tersisa antrian
        if dt_string>waktuPelayananMulai:
            waktuPelayananMulai = dt_string
        # end added
    
    estimasidilayani = waktuPelayananMulai + datetime.timedelta(minutes = waktuTotalAntrian)
    estimasidilayani = round(int(estimasidilayani.timestamp()) * 1000)
    payload.estimasidilayani = estimasidilayani
    payload.sisakuotajkn = int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian)
    payload.kuotajkn = int(resultJadwalDokter['kapasitaspasien'])
    payload.sisakuotanonjkn = int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian)
    payload.kuotanonjkn = int(resultJadwalDokter['kapasitaspasien'])

    try:
        # Attempt to convert the date string to a datetime object
        tanggalperiksa_date = datetime.datetime.strptime(payload.tanggalperiksa, '%Y-%m-%d')
    except ValueError:
        # Handle the case where the date string is not a valid date
        return validation.handleErrorAdmin("Tanggal Periksa Tidak Valid")
        # Handle this error as appropriate for your application

    noantrians = await db_manager_ekamek.nomorantrian(db_ekamek,cekPoli[0],payload.tanggalperiksa,cekDokter[1])
    insert = await db_manager.insert_antrian_poli_onsite_lama(db= db,payload = payload,noantrian=noantrians[0])
    if isinstance(insert, dict):
        return insert

    bodyreq = {
        'nomorkartu': payload.nomorkartu,
        'kodepoli': payload.kodepoli,
        'jeniskunjungan': payload.jeniskunjungan,
        'nomorreferensi':payload.nomorreferensi,
        'kodedokter':payload.kodedokter,
        'kodebooking':insert.kodebooking,
        'norm':norm,
        'tanggalperiksa':payload.tanggalperiksa,
        'kodepoli':payload.kodepoli,
        'noantrian':insert.angkaantrean
    }
    # return bodyreq
    reqdata = await insert_daftar_ulang(bodyreq,db_ekamek)
    await db_manager_ekamek.tambahhistoryantriandirect(db=db_ekamek,kodebooking=insert.kodebooking)

    # update antrian online v.2
    # 22/09/2024 17:19
    # insert ke api -> antrol/insert_daftar_ulang_new POST 
    # reqdata = {
    #     "reservasi": insert.kodebooking,
    #     "no_medrec": norm,
    #     "xcreate": "ANTROL_ONSITE",
    #     "kelasrawat": "1", #?
    #     "asalrujukan": "1", #?
    #     "tglrujukan": "2024-09-12", #?
    #     "ppkrujukan": "03110502", #?
    #     "jns_kunj": "LAMA", #?
    #     "namafaskes": "GAMBOK", #? 
    #     "prb": "PRB : DM, JT", #?
    #     "online": "0", 
    #     "noreservasi": "",
    #     "noreg_asal_konsul": "",
    #     "tgl_kunjungan": payload.tanggalperiksa,
    #     "cara_bayar": "BPJS",
    #     "cara_dtg": "SENDIRI",
    #     "cara_kunj": "RUJUKAN PUSKESMAS", #"RUJUKAN PUSKESMAS","RUJUKAN RS"
    #     "no_bpjs": payload.nomorkartu,
    #     "id_kontraktor": "1",
    #     "no_sep": "",
    #     "no_rujukan": "031105020924P000004",
    #     "tujuan_kunj": "0",
    #     "kd_penunjang": "",
    #     "assesment_pel": "",
    #     "nosurat_skdp_sep": "",
    #     "dpjp_suratkontrol": "",
    #     "alber": "sakit",
    #     "pasdatDg": "klg",
    #     "jenis_kecelakaan": "",
    #     "lokasi_kecelakaan": "",
    #     "kll_tgl_kejadian": "2024-09-22",
    #     "kll_ketkejadian": "",
    #     "hubungan": "",
    #     "id_poli": "BH00~MAT",
    #     "id_dokter": "56-298316-dr. Putrigusti Admira, Sp. M",
    #     "dokter_bpjs": "298316-Tenaga Medis 298316",
    #     "diagnosa": "A18.5@Tuberculosis of eye",
    #     "id_diagnosa": "",
    #     "kelas_pasien": "II",
    #     "no_telp": "1111111111111",
    #     "catatan": "",
    #     "cetak_kartu1": "130003"
    # }

    return {
        'response':{
            'nomorantrean':insert.nomorantrian, #2 digit nama poli didepan + max dari antrian per poli per dokter + 1 
            'angkaantrean':insert.angkaantrean, #max dari antrian per poli per dokter + 1 
            'kodebooking':insert.kodebooking, #nomr + angkaantrean 
            'namapoli':resultJadwalDokter['namasubspesialis'], #nm_poli <- poliklinik
            'norm': norm, #nomr
            'namadokter': resultJadwalDokter['namadokter'], #nm_dokter <- data_dokter
            'estimasidilayani':estimasidilayani, # timestamp epoch tanggal_periksa: jam pelayanan awal  + (jumlah pasien * 15 menit)
            'sisakuotajkn': int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian), #50 - jml antrian bpjs poli 
            'kuotajkn':int(resultJadwalDokter['kapasitaspasien']), #nomr
            'sisakuotanonjkn':int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian), #50 - jml antrian non bpjs poli 
            'kuotanonjkn':int(resultJadwalDokter['kapasitaspasien']), #nomr
            'keterangan':'', #nomr
            
        },
        'metaData': {
            'message':'Ok',
            'code':200
        }
    }



@adminantrian.post('/ambilantrianlama')
async def ambilantrian(payload:models.Ambilantrian,db: Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):
    
    # cek pasien dari db ekamek
    norm = 0
    cekPasien = await db_manager_ekamek.caridatapasien(db_ekamek,payload.nomorkartu)
    if not cekPasien: # tandanya pasien gaada
        # cek di pasien baru daftar di antrol
        cekPasienBaru = await db_manager.cekPasienBaruExist(db = db,nomorkartu = payload.nomorkartu,norm='1')
        if not cekPasienBaru:
            return {
                'metaData' :{
                    'message': 'Data pasien ini tidak ditemukan, silahkan Melakukan Registrasi Pasien Baru',
                    'code':202
                }
            } 
        else:
            namaPasien = cekPasienBaru.nama   
            payload.pasienbaru = '1'
            norm = cekPasienBaru.norm

    else:
        norm = cekPasien[2]
        namaPasien = cekPasien[1]
    
    # check pernah daftar atau belum jika pernah maka bukan pasien baru
    cekPasienBarulama = await db_manager.cekPasienbarulama(db= db,nomorkartu = payload.nomorkartu)
    if not cekPasienBarulama:
        payload.pasienbaru = '1'

    checkExist = await db_manager.checkAntrianExist(db,payload.nomorkartu,payload.tanggalperiksa)
    if checkExist:
        return validation.handleErrorAdmin('Nomor Antrean Hanya Dapat Diambil 1 Kali Pada Tanggal Yang Sama')
    
    cekPoli = await db_manager_ekamek.carinamapoli(db_ekamek,payload.kodepoli)
   
    if not cekPoli:
        return validation.handleErrorAdmin('Poli Tidak Ditemukan')


    cekDokterDanJadwal = service.cekjadwaldokter(payload.kodepoli,payload.tanggalperiksa)
    if not cekDokterDanJadwal:
        return validation.handleErrorAdmin('Koneksi dengan WS BPJS Antrian Cek Jadwal Dokter Gagal!')
    
    if cekDokterDanJadwal['metadata']['code'] != 200:
        return validation.handleErrorAdmin(cekDokterDanJadwal['metadata']['message'])
    
    resultJadwalDokter = {}
    for val in cekDokterDanJadwal['response']:
        print(val)
        if val['kodedokter'] == int(payload.kodedokter):
            resultJadwalDokter = val

    if resultJadwalDokter == {}:
        # return validation.handleErrorAdmin('Jadwal Dokter Tidak Ditemukan Pada Tanggal Tersebut!')
        return validation.handleErrorAdmin(f"Jadwal Dokter Tersebut Belum Tersedia,Silahkan Reschedule Tanggal dan Jam Praktek Lainnya")



    cekDokter = await db_manager_ekamek.carinamadokter(db_ekamek,payload.kodedokter)
    if not cekDokter:
        return validation.handleErrorAdmin('Kode Dokter Tidak sesuai')

    payload.namadokter = resultJadwalDokter['namadokter']
    payload.namapoli = resultJadwalDokter['namasubspesialis']
    payload.nama = namaPasien

    cekTotalAntrian = await db_manager.cekTotalAntrian(db=db,kodehfis = payload.kodedokter,pertgl=payload.tanggalperiksa)
    # estimasi waktu dilayani
    totalAntrian = int(cekTotalAntrian['count'])
    if totalAntrian == 0:
        totalAntrian = 1
    waktuTotalAntrian = (1 if totalAntrian == 0 else totalAntrian) * 10 # (satu pelayanan itu 10 menit)
    strWaktuPelayananMulai = payload.tanggalperiksa + ' 08:00:00'
    waktuPelayananMulai = datetime.datetime.strptime(strWaktuPelayananMulai, '%Y-%m-%d %H:%M:%S')

    validasiPeriksaHariIni = validation.validasiHariIni(payload.tanggalperiksa)
    if validasiPeriksaHariIni:
        splitJadwalJamMulaiSelesai = validation.validasiJadwalMelebihiJam(payload.jampraktek)
        # if not splitJadwalJamMulaiSelesai:
        #     return validation.handleErrorAdmin(f"Pendaftaran Ke Poli ({resultJadwalDokter['namasubspesialis']}) Sudah Tutup Jam {payload.jampraktek.split('-')[1]}")

        # added feature
        # cek jika pasien mendaftar selama pelayanan berlangsung ( misal jam 08.00 waktu mulai)
        # dan pasien mendaftar di jam 09:00 maka waktu kira kira dilayani di jam 09: ditambah dengan menit total
        # antrian yang akan dilayani
        # if()
        # jakarta_timezone = pytz.timezone('Asia/Jakarta')
        now = datetime.datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        dt_string = datetime.datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
        # print(dt_string)
        # print('-----ini-----')
        
        # jika pasien masuuuk melebih jam praktek maka lanjutkan jam praktek + count berapa tersisa antrian
        if dt_string>waktuPelayananMulai:
            waktuPelayananMulai = dt_string
        # end added
    
    estimasidilayani = waktuPelayananMulai + datetime.timedelta(minutes = waktuTotalAntrian)
    estimasidilayani = round(int(estimasidilayani.timestamp()) * 1000)
    payload.estimasidilayani = estimasidilayani
    payload.sisakuotajkn = int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian)
    payload.kuotajkn = int(resultJadwalDokter['kapasitaspasien'])
    payload.sisakuotanonjkn = int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian)
    payload.kuotanonjkn = int(resultJadwalDokter['kapasitaspasien'])

    try:
        # Attempt to convert the date string to a datetime object
        tanggalperiksa_date = datetime.datetime.strptime(payload.tanggalperiksa, '%Y-%m-%d')
    except ValueError:
        # Handle the case where the date string is not a valid date
        return validation.handleErrorAdmin("Tanggal Periksa Tidak Valid")
        # Handle this error as appropriate for your application

    # masukan kondisi disini jika poli BR00
    # cek juga jika dokter tersebut merupakan dokter diana -> BQ00
    # kalo dokter hasnur rahmi -> BR00
    polis = cekPoli[0]

    if polis == 'BR00' and cekDokter[1] != 21:
        polis = 'BQ00'
    # print(cekDokter[1])
    # return False
    noantrians = await db_manager_ekamek.nomorantriandebug(db_ekamek,polis,payload.tanggalperiksa,cekDokter[1])
    # print(noantrians)
    # return False
    insert = await db_manager.insert_antrian_poli_onsite_lama_debug(db= db,payload = payload,noantrian=noantrians[0])
    if isinstance(insert, dict):
        return insert

    bodyreq = {
        'nomorkartu': payload.nomorkartu,
        'kodepoli': payload.kodepoli,
        'jeniskunjungan': payload.jeniskunjungan,
        'nomorreferensi':payload.nomorreferensi,
        'kodedokter':payload.kodedokter,
        'kodebooking':insert.kodebooking,
        'norm':norm,
        'tanggalperiksa':payload.tanggalperiksa,
        'noantrian':insert.angkaantrean
    }
    # return bodyreq
    reqdata = await insert_daftar_ulang(bodyreq,db_ekamek)
    await db_manager_ekamek.tambahhistoryantriandirect(db=db_ekamek,kodebooking=insert.kodebooking)

    # update antrian online v.2
    # 22/09/2024 17:19
    # insert ke api -> antrol/insert_daftar_ulang_new POST 
    # reqdata = {
    #     "reservasi": insert.kodebooking,
    #     "no_medrec": norm,
    #     "xcreate": "ANTROL_ONSITE",
    #     "kelasrawat": "1", #?
    #     "asalrujukan": "1", #?
    #     "tglrujukan": "2024-09-12", #?
    #     "ppkrujukan": "03110502", #?
    #     "jns_kunj": "LAMA", #?
    #     "namafaskes": "GAMBOK", #? 
    #     "prb": "PRB : DM, JT", #?
    #     "online": "0", 
    #     "noreservasi": "",
    #     "noreg_asal_konsul": "",
    #     "tgl_kunjungan": payload.tanggalperiksa,
    #     "cara_bayar": "BPJS",
    #     "cara_dtg": "SENDIRI",
    #     "cara_kunj": "RUJUKAN PUSKESMAS", #"RUJUKAN PUSKESMAS","RUJUKAN RS"
    #     "no_bpjs": payload.nomorkartu,
    #     "id_kontraktor": "1",
    #     "no_sep": "",
    #     "no_rujukan": "031105020924P000004",
    #     "tujuan_kunj": "0",
    #     "kd_penunjang": "",
    #     "assesment_pel": "",
    #     "nosurat_skdp_sep": "",
    #     "dpjp_suratkontrol": "",
    #     "alber": "sakit",
    #     "pasdatDg": "klg",
    #     "jenis_kecelakaan": "",
    #     "lokasi_kecelakaan": "",
    #     "kll_tgl_kejadian": "2024-09-22",
    #     "kll_ketkejadian": "",
    #     "hubungan": "",
    #     "id_poli": "BH00~MAT",
    #     "id_dokter": "56-298316-dr. Putrigusti Admira, Sp. M",
    #     "dokter_bpjs": "298316-Tenaga Medis 298316",
    #     "diagnosa": "A18.5@Tuberculosis of eye",
    #     "id_diagnosa": "",
    #     "kelas_pasien": "II",
    #     "no_telp": "1111111111111",
    #     "catatan": "",
    #     "cetak_kartu1": "130003"
    # }

    return {
        'response':{
            'nomorantrean':insert.nomorantrian, #2 digit nama poli didepan + max dari antrian per poli per dokter + 1 
            'angkaantrean':insert.angkaantrean, #max dari antrian per poli per dokter + 1 
            'kodebooking':insert.kodebooking, #nomr + angkaantrean 
            'namapoli':resultJadwalDokter['namasubspesialis'], #nm_poli <- poliklinik
            'norm': norm, #nomr
            'namadokter': resultJadwalDokter['namadokter'], #nm_dokter <- data_dokter
            'estimasidilayani':estimasidilayani, # timestamp epoch tanggal_periksa: jam pelayanan awal  + (jumlah pasien * 15 menit)
            'sisakuotajkn': int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian), #50 - jml antrian bpjs poli 
            'kuotajkn':int(resultJadwalDokter['kapasitaspasien']), #nomr
            'sisakuotanonjkn':int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian), #50 - jml antrian non bpjs poli 
            'kuotanonjkn':int(resultJadwalDokter['kapasitaspasien']), #nomr
            'keterangan':'', #nomr
            
        },
        'metaData': {
            'message':'Ok',
            'code':200
        }
    }

async def insert_daftar_ulang_new_sept_2025(payload,db_ekamek):
    from datetime import timezone, timedelta

    # Set the timezone to Asia/Jakarta
    jakarta_timezone = timezone(timedelta(hours=7))  # UTC+7

    # get detil peserta
    # /Peserta/nokartu/{parameter 1}/tglSEP/{parameter 2}
    # Mendapatkan tanggal saat ini
    now = datetime.datetime.now(jakarta_timezone)
    # Mengubah ke format Y-m-d
    date_string = now.strftime("%Y-%m-%d")
    getdetilpeserta = bpjs_vclaim.get_vclaim('/Peserta/nokartu/'+payload['nomorkartu']+'/tglSEP/' + date_string)
    
    kelasrawat = 'II'
    if getdetilpeserta['response']['peserta']['hakKelas']['kode'] == '2':
        kelasrawat = 'II'
    elif getdetilpeserta['response']['peserta']['hakKelas']['kode'] == '3':
        kelasrawat = 'III'
    else:
        kelasrawat = 'I'

    # Initialize rujukan data variables
    asal_faskes = '2'  # Default RS
    tgl_kunjungan_rujukan = date_string
    ppk_rujukan_kode = '0311R001'  # Kode RS Anda
    ppk_rujukan_nama = 'RSUD dr. M. Soewandhie Surabaya'  # Nama RS Anda
    no_kunjungan_rujukan = ''
    diagnosa_rujukan_kode = 'Z51.1'  # Default diagnosa kontrol
    diagnosa_rujukan_nama = 'Kemoterapi untuk neoplasma'

    # get rujukan by no kartu - hanya untuk jeniskunjungan selain 4
    if payload['jeniskunjungan'] != 4:
        getdetilrujukan = bpjs_vclaim.get_vclaim('/Rujukan/Peserta/'+payload['nomorkartu'])
        
        # Update rujukan data from API response
        asal_faskes = getdetilrujukan['response']['asalFaskes']
        tgl_kunjungan_rujukan = getdetilrujukan['response']['rujukan']['tglKunjungan']
        ppk_rujukan_kode = getdetilrujukan['response']['rujukan']['provPerujuk']['kode']
        ppk_rujukan_nama = getdetilrujukan['response']['rujukan']['provPerujuk']['nama']
        no_kunjungan_rujukan = getdetilrujukan['response']['rujukan']['noKunjungan']
        diagnosa_rujukan_kode = getdetilrujukan['response']['rujukan']['diagnosa']['kode']
        diagnosa_rujukan_nama = getdetilrujukan['response']['rujukan']['diagnosa']['nama']
    else:
        # Untuk jeniskunjungan 4 (pasca rawat inap), set rujukan manual
        # Anda bisa mengambil data ini dari payload atau set default
        if 'rujukan_manual' in payload:
            asal_faskes = payload['rujukan_manual'].get('asal_faskes', '2')
            tgl_kunjungan_rujukan = payload['rujukan_manual'].get('tgl_kunjungan', date_string)
            ppk_rujukan_kode = payload['rujukan_manual'].get('ppk_kode', '0311R001')
            ppk_rujukan_nama = payload['rujukan_manual'].get('ppk_nama', 'RSUD dr. M. Soewandhie Surabaya')
            no_kunjungan_rujukan = payload['rujukan_manual'].get('no_kunjungan', '')
            diagnosa_rujukan_kode = payload['rujukan_manual'].get('diagnosa_kode', 'Z51.1')
            diagnosa_rujukan_nama = payload['rujukan_manual'].get('diagnosa_nama', 'Pemeriksaan kesehatan rutin')

    tujuan_kunj = '0'
    kd_penunjang = ''
    assesment_pel = ''
    nosurat_skdp_sep = ''
    dpjp_suratkontrol = ''
    catatan = ''
    
    # jenis kunjungan=>  
    # 1 = rujukan fktp
    # 2 = internal
    # 3 = kontrol
    # 4 = rujukan rs / pasca rawat inap
    if payload['jeniskunjungan'] == 2:
        tujuan_kunj = '0'
        kd_penunjang = ''
        assesment_pel = '1'
        nosurat_skdp_sep = ''
        dpjp_suratkontrol = ''
        catatan = f"Rujuk internal dari poli {payload['namapoli']}"
    elif payload['jeniskunjungan'] == 3:
        tujuan_kunj = '2'
        kd_penunjang = ''
        assesment_pel = '5'
        nosurat_skdp_sep = payload['nomorreferensi']
        dpjp_suratkontrol = payload['kodedokter']
    elif payload['jeniskunjungan'] == 4:
        tujuan_kunj = '0'
        kd_penunjang = ''
        assesment_pel = '5'  # Atau sesuai kebutuhan
        nosurat_skdp_sep = payload['nomorreferensi']
        dpjp_suratkontrol = payload['kodedokter']
        catatan = f"Pasca rawat inap - kontrol rutin"
        # force ganti ke 3 (jika masih diperlukan)
        payload['jeniskunjungan'] = 3

    # get id_dokter by dokter bpjs
    cekdokter = await db_manager_ekamek.caridatadokter(db_ekamek,payload['kodedokter'])
    
    no_medrecs = await db_manager_ekamek.carinomedrecberdasarnorm(db_ekamek,payload['norm'])

    idpoli = payload['id_poli']
    iddokter = str(cekdokter[0])

    # Tentukan cara_kunj berdasarkan asal faskes
    cara_kunj = "RUJUKAN PUSKESMAS" if asal_faskes == '1' else "RUJUKAN RS"

    reqdata = {
        "reservasi": payload['kodebooking'],
        "no_medrec": no_medrecs[0],
        "xcreate": "ANTROL_ONSITE",
        "kelasrawat": getdetilpeserta['response']['peserta']['hakKelas']['kode'],
        "asalrujukan": asal_faskes,
        "tglrujukan": tgl_kunjungan_rujukan,
        "ppkrujukan": ppk_rujukan_kode,
        "jns_kunj": "LAMA", 
        "namafaskes": ppk_rujukan_nama,
        "prb": '' if getdetilpeserta['response']['peserta']['informasi']['prolanisPRB'] is None else getdetilpeserta['response']['peserta']['informasi']['prolanisPRB'],
        "online": "0", 
        "noreservasi": payload['kodebooking'],
        "noreg_asal_konsul": "",
        "tgl_kunjungan": payload['tanggalperiksa'],
        "cara_bayar": "BPJS",
        "cara_dtg": "SENDIRI",
        "cara_kunj": cara_kunj,
        "no_bpjs": payload['nomorkartu'],
        "id_kontraktor": "1",
        "no_sep": "", 
        "no_rujukan": no_kunjungan_rujukan,
        "tujuan_kunj": tujuan_kunj,
        "kd_penunjang": kd_penunjang,
        "assesment_pel": assesment_pel,
        "nosurat_skdp_sep": nosurat_skdp_sep,
        "dpjp_suratkontrol": dpjp_suratkontrol,
        "alber": "sakit",
        "pasdatDg": "klg",
        "jenis_kecelakaan": "",
        "lokasi_kecelakaan": "",
        "kll_tgl_kejadian": "",
        "kll_ketkejadian": "",
        "hubungan": "",
        "id_poli": idpoli + '~' + payload['kodepoli'],
        "id_dokter": iddokter + '-' + payload['kodedokter'] + '-' + cekdokter[1],
        "dokter_bpjs": payload['kodedokter'] + "-" + cekdokter[1],
        "diagnosa": diagnosa_rujukan_kode + "@" + diagnosa_rujukan_nama,
        "id_diagnosa": "",
        "kelas_pasien": kelasrawat,
        "no_telp": "",
        "catatan": catatan,
        "cetak_kartu1": "",
        'noantrian': payload['noantrian']
    }

    res = await insert_daftar_ulang_new_antrol(db_ekamek,reqdata)
    return res

async def insert_daftar_ulang_new_jul_2025(payload,db_ekamek):
    from datetime import timezone, timedelta

    # Set the timezone to Asia/Jakarta
    jakarta_timezone = timezone(timedelta(hours=7))  # UTC+7

    # get detil peserta
    # /Peserta/nokartu/{parameter 1}/tglSEP/{parameter 2}
    # Mendapatkan tanggal saat ini
    now = datetime.datetime.now(jakarta_timezone)
    # return now
    # Mengubah ke format Y-m-d
    date_string = now.strftime("%Y-%m-%d")
    getdetilpeserta = bpjs_vclaim.get_vclaim('/Peserta/nokartu/'+payload['nomorkartu']+'/tglSEP/' + date_string)
    # return getdetilpeserta
    kelasrawat = 'II'
    if getdetilpeserta['response']['peserta']['hakKelas']['kode'] == '2':
        kelasrawat = 'II'
    elif getdetilpeserta['response']['peserta']['hakKelas']['kode'] == '3':
        kelasrawat = 'III'
    else:
        kelasrawat = 'I'

    # get rujukan by no kartu
    # BASE URL}/{Service Name}/Rujukan/Peserta/{parameter}
    # {BASE URL}/{Service Name}/Rujukan/RS/Peserta/{parameter}
    getdetilrujukan = bpjs_vclaim.get_vclaim('/Rujukan/Peserta/'+payload['nomorkartu'])
    # return getdetilrujukan



    # get id poli by poli_bpjs
    # cekpoliklinik = await db_manager_ekamek.caridatapoliklinik(db_ekamek,payload['kodepoli'])
    tujuan_kunj = '0'
    kd_penunjang = ''
    assesment_pel = ''
    nosurat_skdp_sep = ''
    dpjp_suratkontrol = ''
    catatan = ''
    
    # jenis kunjungan=>  
    # 1 = rujukan fktp
    # 2 = internal
    # 3 = kontrol
    # 4 = rujukan rs
    if payload['jeniskunjungan'] == 2:
        tujuan_kunj = '0'
        kd_penunjang = ''
        assesment_pel = '1'
        nosurat_skdp_sep = ''
        dpjp_suratkontrol = ''
        catatan = f"Rujuk internal dari poli  {payload['namapoli']}"
    elif payload['jeniskunjungan'] == 3:
        tujuan_kunj = '2'
        kd_penunjang = ''
        assesment_pel = '5'
        nosurat_skdp_sep = payload['nomorreferensi']
        dpjp_suratkontrol = payload['kodedokter']
    elif payload['jeniskunjungan'] == 4:
        tujuan_kunj = '0'
        kd_penunjang = ''
        assesment_pel = ''
        nosurat_skdp_sep = payload['nomorreferensi']
        dpjp_suratkontrol = payload['kodedokter']
        catatan = f""
        # force ganti ke 3
        payload['jeniskunjungan'] = 3


    # get id_dokter by dokter npjs
    cekdokter = await db_manager_ekamek.caridatadokter(db_ekamek,payload['kodedokter'])
    # print(cekdokter)
    # return {'ok'}
    
    # data_d

    no_medrecs = await db_manager_ekamek.carinomedrecberdasarnorm(db_ekamek,payload['norm'])

    idpoli = payload['id_poli']
    iddokter = str(cekdokter[0])

    # cek jika poli DALAM2  dan dokter diana
    # if idpoli == 'BR00' and iddokter == '40':
    #     #pindahkan ke poli PENYAKIT DALAM
    #     idpoli = 'BQ00'
    reqdata = {
        "reservasi": payload['kodebooking'],
        "no_medrec": no_medrecs[0],
        "xcreate": "ANTROL_ONSITE",
        "kelasrawat": getdetilpeserta['response']['peserta']['hakKelas']['kode'], #? dari data peserta
        "asalrujukan": getdetilrujukan['response']['asalFaskes'], #? dari data rujukan
        "tglrujukan": getdetilrujukan['response']['rujukan']['tglKunjungan'], #? dari data rujukan
        "ppkrujukan": getdetilrujukan['response']['rujukan']['provPerujuk']['kode'], #? dari data rujukan
        "jns_kunj": "LAMA", 
        "namafaskes": getdetilrujukan['response']['rujukan']['provPerujuk']['nama'], #? dari data rujukan
        "prb": '' if getdetilpeserta['response']['peserta']['informasi']['prolanisPRB'] is None else getdetilpeserta['response']['peserta']['informasi']['prolanisPRB'], #? dari data peserta
        "online": "0", 
        "noreservasi": payload['kodebooking'], #kodebooking
        "noreg_asal_konsul": "",
        "tgl_kunjungan": payload['tanggalperiksa'],
        "cara_bayar": "BPJS",
        "cara_dtg": "SENDIRI",
        "cara_kunj": "RUJUKAN PUSKESMAS" if getdetilrujukan['response']['asalFaskes'] == '1' else "RUJUKAN RS", #dari data rujukan #"RUJUKAN PUSKESMAS","RUJUKAN RS"
        "no_bpjs": payload['nomorkartu'],
        "id_kontraktor": "1",
        "no_sep": "", 
        "no_rujukan": getdetilrujukan['response']['rujukan']['noKunjungan'], #dari data rujukan
        "tujuan_kunj": tujuan_kunj, #otomatis kan bisa
        "kd_penunjang": kd_penunjang, #otomatis kan bisa
        "assesment_pel": assesment_pel, #otomatis kan bisa
        "nosurat_skdp_sep": nosurat_skdp_sep, #otomatis kan bisa
        "dpjp_suratkontrol": dpjp_suratkontrol, #otomatis kan bisa
        "alber": "sakit",
        "pasdatDg": "klg",
        "jenis_kecelakaan": "",
        "lokasi_kecelakaan": "",
        "kll_tgl_kejadian": "",
        "kll_ketkejadian": "",
        "hubungan": "",
        "id_poli": idpoli + '~' + payload['kodepoli'], #ambil dari poliklinik
        "id_dokter": iddokter + '-' + payload['kodedokter'] + '-' + cekdokter[1],#ambil dari data_dokter
        "dokter_bpjs":  payload['kodedokter']  + "-" + cekdokter[1],
        "diagnosa": getdetilrujukan['response']['rujukan']['diagnosa']['kode'] + "@" + getdetilrujukan['response']['rujukan']['diagnosa']['nama'],#ambil dari rujukan
        "id_diagnosa": "",
        "kelas_pasien": kelasrawat, #ambil dari rujukan
        "no_telp": "",
        "catatan": catatan,
        "cetak_kartu1": "",
        'noantrian':payload['noantrian']
    }

    # res = requests.request("POST", 'http://192.168.56.102/antrol/api/insert_daftar_ulang_new_antrol', headers=headers, data=reqdata)
    # print(res.text)
    res = await insert_daftar_ulang_new_antrol(db_ekamek,reqdata)
    return res
    

# ini untuk ambil antrian lama debug dan yang sekarang aktif 
@adminantrian.post('/ambilantrianlamadebug')
async def ambilantrianlamadebug(payload:models.AmbilantrianDebug,db: Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):
    
    # cek pasien dari db ekamek
    norm = 0
    cekPasien = await db_manager_ekamek.caridatapasien(db_ekamek,payload.nomorkartu)
    if not cekPasien: # tandanya pasien gaada
        # cek di pasien baru daftar di antrol
        cekPasienBaru = await db_manager.cekPasienBaruExist(db = db,nomorkartu = payload.nomorkartu,norm='1')
        if not cekPasienBaru:
            return {
                'metaData' :{
                    'message': 'Data pasien ini tidak ditemukan, silahkan Melakukan Registrasi Pasien Baru',
                    'code':202
                }
            } 
        else:
            namaPasien = cekPasienBaru.nama   
            payload.pasienbaru = '1'
            norm = cekPasienBaru.norm

    else:
        norm = cekPasien[2]
        namaPasien = cekPasien[1]
    
    # check pernah daftar atau belum jika pernah maka bukan pasien baru
    cekPasienBarulama = await db_manager.cekPasienbarulama(db= db,nomorkartu = payload.nomorkartu)
    if not cekPasienBarulama:
        payload.pasienbaru = '1'

    checkExist = await db_manager.checkAntrianExist(db,payload.nomorkartu,payload.tanggalperiksa)
    if checkExist:
        return validation.handleErrorAdmin('Nomor Antrean Hanya Dapat Diambil 1 Kali Pada Tanggal Yang Sama')
    

    cekDokter = await db_manager_ekamek.carinamadokter_new(db_ekamek,payload.kodedokter)
    if not cekDokter:
        return validation.handleError('Kode Dokter Tidak sesuai')
        
    # if cekDokter[2] is None or cekDokter[2] == '':
    #     return validation.handleError('Kode Poli Tidak Ditemukan')

    cekPoli = payload.id_poli
    if not cekPoli:
        return validation.handleErrorAdmin('Poli Tidak Ditemukan')


    cekDokterDanJadwal = service.cekjadwaldokter(payload.kodepoli,payload.tanggalperiksa)
    if not cekDokterDanJadwal:
        return validation.handleErrorAdmin('Koneksi dengan WS BPJS Antrian Cek Jadwal Dokter Gagal!')
    
    if cekDokterDanJadwal['metadata']['code'] != 200:
        return validation.handleErrorAdmin(cekDokterDanJadwal['metadata']['message'])
    
    resultJadwalDokter = {}
    for val in cekDokterDanJadwal['response']:
        print(val)
        if val['kodedokter'] == int(payload.kodedokter):
            resultJadwalDokter = val

    if resultJadwalDokter == {}:
        # return validation.handleErrorAdmin('Jadwal Dokter Tidak Ditemukan Pada Tanggal Tersebut!')
        return validation.handleErrorAdmin(f"Jadwal Dokter Tersebut Belum Tersedia,Silahkan Reschedule Tanggal dan Jam Praktek Lainnya")

    payload.namadokter = resultJadwalDokter['namadokter']
    payload.namapoli = resultJadwalDokter['namasubspesialis']
    payload.nama = namaPasien

    cekTotalAntrian = await db_manager.cekTotalAntrian(db=db,kodehfis = payload.kodedokter,pertgl=payload.tanggalperiksa)
    # estimasi waktu dilayani
    totalAntrian = int(cekTotalAntrian['count'])
    if totalAntrian == 0:
        totalAntrian = 1
    waktuTotalAntrian = (1 if totalAntrian == 0 else totalAntrian) * 10 # (satu pelayanan itu 10 menit)
    strWaktuPelayananMulai = payload.tanggalperiksa + ' 08:00:00'
    waktuPelayananMulai = datetime.datetime.strptime(strWaktuPelayananMulai, '%Y-%m-%d %H:%M:%S')

    validasiPeriksaHariIni = validation.validasiHariIni(payload.tanggalperiksa)
    if validasiPeriksaHariIni:
        splitJadwalJamMulaiSelesai = validation.validasiJadwalMelebihiJam(payload.jampraktek)
        # if not splitJadwalJamMulaiSelesai:
        #     return validation.handleErrorAdmin(f"Pendaftaran Ke Poli ({resultJadwalDokter['namasubspesialis']}) Sudah Tutup Jam {payload.jampraktek.split('-')[1]}")

        # added feature
        # cek jika pasien mendaftar selama pelayanan berlangsung ( misal jam 08.00 waktu mulai)
        # dan pasien mendaftar di jam 09:00 maka waktu kira kira dilayani di jam 09: ditambah dengan menit total
        # antrian yang akan dilayani
        # if()
        # jakarta_timezone = pytz.timezone('Asia/Jakarta')
        now = datetime.datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        dt_string = datetime.datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
        # print(dt_string)
        # print('-----ini-----')
        
        # jika pasien masuuuk melebih jam praktek maka lanjutkan jam praktek + count berapa tersisa antrian
        if dt_string>waktuPelayananMulai:
            waktuPelayananMulai = dt_string
        # end added
    
    estimasidilayani = waktuPelayananMulai + datetime.timedelta(minutes = waktuTotalAntrian)
    estimasidilayani = round(int(estimasidilayani.timestamp()) * 1000)
    payload.estimasidilayani = estimasidilayani
    payload.sisakuotajkn = int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian)
    payload.kuotajkn = int(resultJadwalDokter['kapasitaspasien'])
    payload.sisakuotanonjkn = int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian)
    payload.kuotanonjkn = int(resultJadwalDokter['kapasitaspasien'])

    try:
        # Attempt to convert the date string to a datetime object
        tanggalperiksa_date = datetime.datetime.strptime(payload.tanggalperiksa, '%Y-%m-%d')
    except ValueError:
        # Handle the case where the date string is not a valid date
        return validation.handleErrorAdmin("Tanggal Periksa Tidak Valid")
        # Handle this error as appropriate for your application

    polis = cekPoli

    noantrians = await db_manager_ekamek.nomorantriandebug(db_ekamek,polis,payload.tanggalperiksa,cekDokter[1])
    del payload.id_poli
    insert = await db_manager.insert_antrian_poli_onsite_lama_debug(db= db,payload = payload,noantrian=noantrians[0])
    print("ASDASD")
    print(insert)
    if isinstance(insert, dict):
        return insert

    bodyreq = {
        'nomorkartu': payload.nomorkartu,
        'kodepoli': payload.kodepoli,
        'id_poli': polis,
        'namapoli':resultJadwalDokter['namasubspesialis'],
        'jeniskunjungan': payload.jeniskunjungan,
        'nomorreferensi':payload.nomorreferensi,
        'kodedokter':payload.kodedokter,
        'kodebooking':insert.kodebooking,
        'norm':norm,
        'tanggalperiksa':payload.tanggalperiksa,
        'noantrian':insert.angkaantrean
    }
    # return bodyreq
    reqdata = await insert_daftar_ulang_new_jul_2025(bodyreq,db_ekamek)
    await db_manager_ekamek.tambahhistoryantriandirect(db=db_ekamek,kodebooking=insert.kodebooking)

    # update antrian online v.2
    # 22/09/2024 17:19
    # insert ke api -> antrol/insert_daftar_ulang_new POST 
    # reqdata = {
    #     "reservasi": insert.kodebooking,
    #     "no_medrec": norm,
    #     "xcreate": "ANTROL_ONSITE",
    #     "kelasrawat": "1", #?
    #     "asalrujukan": "1", #?
    #     "tglrujukan": "2024-09-12", #?
    #     "ppkrujukan": "03110502", #?
    #     "jns_kunj": "LAMA", #?
    #     "namafaskes": "GAMBOK", #? 
    #     "prb": "PRB : DM, JT", #?
    #     "online": "0", 
    #     "noreservasi": "",
    #     "noreg_asal_konsul": "",
    #     "tgl_kunjungan": payload.tanggalperiksa,
    #     "cara_bayar": "BPJS",
    #     "cara_dtg": "SENDIRI",
    #     "cara_kunj": "RUJUKAN PUSKESMAS", #"RUJUKAN PUSKESMAS","RUJUKAN RS"
    #     "no_bpjs": payload.nomorkartu,
    #     "id_kontraktor": "1",
    #     "no_sep": "",
    #     "no_rujukan": "031105020924P000004",
    #     "tujuan_kunj": "0",
    #     "kd_penunjang": "",
    #     "assesment_pel": "",
    #     "nosurat_skdp_sep": "",
    #     "dpjp_suratkontrol": "",
    #     "alber": "sakit",
    #     "pasdatDg": "klg",
    #     "jenis_kecelakaan": "",
    #     "lokasi_kecelakaan": "",
    #     "kll_tgl_kejadian": "2024-09-22",
    #     "kll_ketkejadian": "",
    #     "hubungan": "",
    #     "id_poli": "BH00~MAT",
    #     "id_dokter": "56-298316-dr. Putrigusti Admira, Sp. M",
    #     "dokter_bpjs": "298316-Tenaga Medis 298316",
    #     "diagnosa": "A18.5@Tuberculosis of eye",
    #     "id_diagnosa": "",
    #     "kelas_pasien": "II",
    #     "no_telp": "1111111111111",
    #     "catatan": "",
    #     "cetak_kartu1": "130003"
    # }

    return {
        'response':{
            'nomorantrean':insert.nomorantrian, #2 digit nama poli didepan + max dari antrian per poli per dokter + 1 
            'angkaantrean':insert.angkaantrean, #max dari antrian per poli per dokter + 1 
            'kodebooking':insert.kodebooking, #nomr + angkaantrean 
            'namapoli':resultJadwalDokter['namasubspesialis'], #nm_poli <- poliklinik
            'norm': norm, #nomr
            'namadokter': resultJadwalDokter['namadokter'], #nm_dokter <- data_dokter
            'estimasidilayani':estimasidilayani, # timestamp epoch tanggal_periksa: jam pelayanan awal  + (jumlah pasien * 15 menit)
            'sisakuotajkn': int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian), #50 - jml antrian bpjs poli 
            'kuotajkn':int(resultJadwalDokter['kapasitaspasien']), #nomr
            'sisakuotanonjkn':int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian), #50 - jml antrian non bpjs poli 
            'kuotanonjkn':int(resultJadwalDokter['kapasitaspasien']), #nomr
            'keterangan':'', #nomr
            
        },
        'metaData': {
            'message':'Ok',
            'code':200
        }
    }



# ini untuk ambil antrian lama debug dan yang sekarang aktif 
@adminantrian.post('/ambilantrianlamadebugprod')
async def ambilantrianlamadebugprod(payload:models.AmbilantrianDebug,db: Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):
    
    # cek pasien dari db ekamek
    norm = 0
    cekPasien = await db_manager_ekamek.caridatapasien(db_ekamek,payload.nomorkartu)
    if not cekPasien: # tandanya pasien gaada
        # cek di pasien baru daftar di antrol
        cekPasienBaru = await db_manager.cekPasienBaruExist(db = db,nomorkartu = payload.nomorkartu,norm='1')
        if not cekPasienBaru:
            return {
                'metaData' :{
                    'message': 'Data pasien ini tidak ditemukan, silahkan Melakukan Registrasi Pasien Baru',
                    'code':202
                }
            } 
        else:
            namaPasien = cekPasienBaru.nama   
            payload.pasienbaru = '1'
            norm = cekPasienBaru.norm

    else:
        norm = cekPasien[2]
        namaPasien = cekPasien[1]
    
    # check pernah daftar atau belum jika pernah maka bukan pasien baru
    cekPasienBarulama = await db_manager_ekamek.cekPasienbarulama(db= db_ekamek,nomorkartu = payload.nomorkartu)
    if not cekPasienBarulama:
        payload.pasienbaru = '1'

    checkExist = await db_manager.checkAntrianExist(db,payload.nomorkartu,payload.tanggalperiksa)
    if checkExist:
        return validation.handleErrorAdmin('Nomor Antrean Hanya Dapat Diambil 1 Kali Pada Tanggal Yang Sama')
    

    cekDokter = await db_manager_ekamek.carinamadokter_new(db_ekamek,payload.kodedokter)
    if not cekDokter:
        return validation.handleError('Kode Dokter Tidak sesuai')
        
    # if cekDokter[2] is None or cekDokter[2] == '':
    #     return validation.handleError('Kode Poli Tidak Ditemukan')

    cekPoli = payload.id_poli
    if not cekPoli:
        return validation.handleErrorAdmin('Poli Tidak Ditemukan')


    cekDokterDanJadwal = service.cekjadwaldokter(payload.kodepoli,payload.tanggalperiksa)
    if not cekDokterDanJadwal:
        return validation.handleErrorAdmin('Koneksi dengan WS BPJS Antrian Cek Jadwal Dokter Gagal!')
    
    if cekDokterDanJadwal['metadata']['code'] != 200:
        return validation.handleErrorAdmin(cekDokterDanJadwal['metadata']['message'])
    
    resultJadwalDokter = {}
    for val in cekDokterDanJadwal['response']:
        print(val)
        if val['kodedokter'] == int(payload.kodedokter):
            resultJadwalDokter = val

    if resultJadwalDokter == {}:
        # return validation.handleErrorAdmin('Jadwal Dokter Tidak Ditemukan Pada Tanggal Tersebut!')
        return validation.handleErrorAdmin(f"Jadwal Dokter Tersebut Belum Tersedia,Silahkan Reschedule Tanggal dan Jam Praktek Lainnya")

    payload.namadokter = resultJadwalDokter['namadokter']
    payload.namapoli = resultJadwalDokter['namasubspesialis']
    payload.nama = namaPasien

    cekTotalAntrian = await db_manager.cekTotalAntrian(db=db,kodehfis = payload.kodedokter,pertgl=payload.tanggalperiksa)
    # estimasi waktu dilayani
    totalAntrian = int(cekTotalAntrian['count'])
    if totalAntrian == 0:
        totalAntrian = 1
    waktuTotalAntrian = (1 if totalAntrian == 0 else totalAntrian) * 10 # (satu pelayanan itu 10 menit)
    strWaktuPelayananMulai = payload.tanggalperiksa + ' 08:00:00'
    waktuPelayananMulai = datetime.datetime.strptime(strWaktuPelayananMulai, '%Y-%m-%d %H:%M:%S')

    validasiPeriksaHariIni = validation.validasiHariIni(payload.tanggalperiksa)
    if validasiPeriksaHariIni:
        splitJadwalJamMulaiSelesai = validation.validasiJadwalMelebihiJam(payload.jampraktek)
        # if not splitJadwalJamMulaiSelesai:
        #     return validation.handleErrorAdmin(f"Pendaftaran Ke Poli ({resultJadwalDokter['namasubspesialis']}) Sudah Tutup Jam {payload.jampraktek.split('-')[1]}")

        # added feature
        # cek jika pasien mendaftar selama pelayanan berlangsung ( misal jam 08.00 waktu mulai)
        # dan pasien mendaftar di jam 09:00 maka waktu kira kira dilayani di jam 09: ditambah dengan menit total
        # antrian yang akan dilayani
        # if()
        # jakarta_timezone = pytz.timezone('Asia/Jakarta')
        now = datetime.datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        dt_string = datetime.datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
        # print(dt_string)
        # print('-----ini-----')
        
        # jika pasien masuuuk melebih jam praktek maka lanjutkan jam praktek + count berapa tersisa antrian
        if dt_string>waktuPelayananMulai:
            waktuPelayananMulai = dt_string
        # end added
    
    estimasidilayani = waktuPelayananMulai + datetime.timedelta(minutes = waktuTotalAntrian)
    estimasidilayani = round(int(estimasidilayani.timestamp()) * 1000)
    payload.estimasidilayani = estimasidilayani
    payload.sisakuotajkn = int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian)
    payload.kuotajkn = int(resultJadwalDokter['kapasitaspasien'])
    payload.sisakuotanonjkn = int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian)
    payload.kuotanonjkn = int(resultJadwalDokter['kapasitaspasien'])

    try:
        # Attempt to convert the date string to a datetime object
        tanggalperiksa_date = datetime.datetime.strptime(payload.tanggalperiksa, '%Y-%m-%d')
    except ValueError:
        # Handle the case where the date string is not a valid date
        return validation.handleErrorAdmin("Tanggal Periksa Tidak Valid")
        # Handle this error as appropriate for your application

    polis = cekPoli

    noantrians = await db_manager_ekamek.nomorantriandebug(db_ekamek,polis,payload.tanggalperiksa,cekDokter[1])
    del payload.id_poli
    insert = await db_manager.insert_antrian_poli_onsite_lama_debug_prod(db= db,payload = payload,noantrian=noantrians[0])
    # print("ASDASD")
    # print(insert)
    if isinstance(insert, dict):
        return insert

    # return False

    bodyreq = {
        'nomorkartu': payload.nomorkartu,
        'kodepoli': payload.kodepoli,
        'id_poli': polis,
        'namapoli':resultJadwalDokter['namasubspesialis'],
        'jeniskunjungan': 3 if payload.jeniskunjungan == 4 else payload.jeniskunjungan,
        'nomorreferensi':payload.nomorreferensi,
        'kodedokter':payload.kodedokter,
        'kodebooking':insert.kodebooking,
        'norm':norm,
        'tanggalperiksa':payload.tanggalperiksa,
        'noantrian':insert.angkaantrean
    }
    # return bodyreq
    reqdata = await insert_daftar_ulang_new_jul_2025(bodyreq,db_ekamek)
    await db_manager_ekamek.tambahhistoryantriandirect(db=db_ekamek,kodebooking=insert.kodebooking)

    # update antrian online v.2
    # 22/09/2024 17:19
    # insert ke api -> antrol/insert_daftar_ulang_new POST 
    # reqdata = {
    #     "reservasi": insert.kodebooking,
    #     "no_medrec": norm,
    #     "xcreate": "ANTROL_ONSITE",
    #     "kelasrawat": "1", #?
    #     "asalrujukan": "1", #?
    #     "tglrujukan": "2024-09-12", #?
    #     "ppkrujukan": "03110502", #?
    #     "jns_kunj": "LAMA", #?
    #     "namafaskes": "GAMBOK", #? 
    #     "prb": "PRB : DM, JT", #?
    #     "online": "0", 
    #     "noreservasi": "",
    #     "noreg_asal_konsul": "",
    #     "tgl_kunjungan": payload.tanggalperiksa,
    #     "cara_bayar": "BPJS",
    #     "cara_dtg": "SENDIRI",
    #     "cara_kunj": "RUJUKAN PUSKESMAS", #"RUJUKAN PUSKESMAS","RUJUKAN RS"
    #     "no_bpjs": payload.nomorkartu,
    #     "id_kontraktor": "1",
    #     "no_sep": "",
    #     "no_rujukan": "031105020924P000004",
    #     "tujuan_kunj": "0",
    #     "kd_penunjang": "",
    #     "assesment_pel": "",
    #     "nosurat_skdp_sep": "",
    #     "dpjp_suratkontrol": "",
    #     "alber": "sakit",
    #     "pasdatDg": "klg",
    #     "jenis_kecelakaan": "",
    #     "lokasi_kecelakaan": "",
    #     "kll_tgl_kejadian": "2024-09-22",
    #     "kll_ketkejadian": "",
    #     "hubungan": "",
    #     "id_poli": "BH00~MAT",
    #     "id_dokter": "56-298316-dr. Putrigusti Admira, Sp. M",
    #     "dokter_bpjs": "298316-Tenaga Medis 298316",
    #     "diagnosa": "A18.5@Tuberculosis of eye",
    #     "id_diagnosa": "",
    #     "kelas_pasien": "II",
    #     "no_telp": "1111111111111",
    #     "catatan": "",
    #     "cetak_kartu1": "130003"
    # }

    return {
        'response':{
            'nomorantrean':insert.nomorantrian, #2 digit nama poli didepan + max dari antrian per poli per dokter + 1 
            'angkaantrean':insert.angkaantrean, #max dari antrian per poli per dokter + 1 
            'kodebooking':insert.kodebooking, #nomr + angkaantrean 
            'namapoli':resultJadwalDokter['namasubspesialis'], #nm_poli <- poliklinik
            'norm': norm, #nomr
            'namadokter': resultJadwalDokter['namadokter'], #nm_dokter <- data_dokter
            'estimasidilayani':estimasidilayani, # timestamp epoch tanggal_periksa: jam pelayanan awal  + (jumlah pasien * 15 menit)
            'sisakuotajkn': int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian), #50 - jml antrian bpjs poli 
            'kuotajkn':int(resultJadwalDokter['kapasitaspasien']), #nomr
            'sisakuotanonjkn':int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian), #50 - jml antrian non bpjs poli 
            'kuotanonjkn':int(resultJadwalDokter['kapasitaspasien']), #nomr
            'keterangan':'', #nomr
            
        },
        'metaData': {
            'message':'Ok',
            'code':200
        }
    }



async def insert_daftar_ulang(payload,db_ekamek):
    from datetime import timezone, timedelta

    # Set the timezone to Asia/Jakarta
    jakarta_timezone = timezone(timedelta(hours=7))  # UTC+7

    # get detil peserta
    # /Peserta/nokartu/{parameter 1}/tglSEP/{parameter 2}
    # Mendapatkan tanggal saat ini
    now = datetime.datetime.now(jakarta_timezone)
    # return now
    # Mengubah ke format Y-m-d
    date_string = now.strftime("%Y-%m-%d")
    getdetilpeserta = bpjs_vclaim.get_vclaim('/Peserta/nokartu/'+payload['nomorkartu']+'/tglSEP/' + date_string)
    # return getdetilpeserta
    kelasrawat = 'II'
    if getdetilpeserta['response']['peserta']['hakKelas']['kode'] == '2':
        kelasrawat = 'II'
    elif getdetilpeserta['response']['peserta']['hakKelas']['kode'] == '3':
        kelasrawat = 'III'
    else:
        kelasrawat = 'I'

    # get rujukan by no kartu
    # BASE URL}/{Service Name}/Rujukan/Peserta/{parameter}
    # {BASE URL}/{Service Name}/Rujukan/RS/Peserta/{parameter}
    getdetilrujukan = bpjs_vclaim.get_vclaim('/Rujukan/Peserta/'+payload['nomorkartu'])
    # return getdetilrujukan



    # get id poli by poli_bpjs
    cekpoliklinik = await db_manager_ekamek.caridatapoliklinik(db_ekamek,payload['kodepoli'])
    tujuan_kunj = '0'
    kd_penunjang = ''
    assesment_pel = ''
    nosurat_skdp_sep = ''
    dpjp_suratkontrol = ''
    catatan = ''
    
    # jenis kunjungan=>  
    # 1 = rujukan fktp
    # 2 = internal
    # 3 = kontrol
    # 4 = rujukan rs
    if payload['jeniskunjungan'] == 2:
        tujuan_kunj = '0'
        kd_penunjang = ''
        assesment_pel = '1'
        nosurat_skdp_sep = ''
        dpjp_suratkontrol = ''
        catatan = f"Rujuk internal dari poli  {cekpoliklinik[1]}"
    elif payload['jeniskunjungan'] == 3:
        tujuan_kunj = '2'
        kd_penunjang = ''
        assesment_pel = '5'
        nosurat_skdp_sep = payload['nomorreferensi']
        dpjp_suratkontrol = payload['kodedokter']


    # get id_dokter by dokter npjs
    cekdokter = await db_manager_ekamek.caridatadokter(db_ekamek,payload['kodedokter'])
    # print(cekdokter)
    # return {'ok'}
    
    # data_d
    no_medrecs = await db_manager_ekamek.carinomedrecberdasarnorm(db_ekamek,payload['norm'])

    idpoli = cekpoliklinik[0]
    iddokter = str(cekdokter[0])
 # cek jika poli DALAM2  dan dokter diana
    if idpoli == 'BR00' and iddokter == '40':
        #pindahkan ke poli PENYAKIT DALAM
        idpoli = 'BQ00'
    reqdata = {
        "reservasi": payload['kodebooking'],
        "no_medrec": no_medrecs[0],
        "xcreate": "ANTROL_ONSITE",
        "kelasrawat": getdetilpeserta['response']['peserta']['hakKelas']['kode'], #? dari data peserta
        "asalrujukan": getdetilrujukan['response']['asalFaskes'], #? dari data rujukan
        "tglrujukan": getdetilrujukan['response']['rujukan']['tglKunjungan'], #? dari data rujukan
        "ppkrujukan": getdetilrujukan['response']['rujukan']['provPerujuk']['kode'], #? dari data rujukan
        "jns_kunj": "LAMA", 
        "namafaskes": getdetilrujukan['response']['rujukan']['provPerujuk']['nama'], #? dari data rujukan
        "prb": '' if getdetilpeserta['response']['peserta']['informasi']['prolanisPRB'] is None else getdetilpeserta['response']['peserta']['informasi']['prolanisPRB'], #? dari data peserta
        "online": "0", 
        "noreservasi": payload['kodebooking'], #kodebooking
        "noreg_asal_konsul": "",
        "tgl_kunjungan": payload['tanggalperiksa'],
        "cara_bayar": "BPJS",
        "cara_dtg": "SENDIRI",
        "cara_kunj": "RUJUKAN PUSKESMAS" if getdetilrujukan['response']['asalFaskes'] == '1' else "RUJUKAN RS", #dari data rujukan #"RUJUKAN PUSKESMAS","RUJUKAN RS"
        "no_bpjs": payload['nomorkartu'],
        "id_kontraktor": "1",
        "no_sep": "", 
        "no_rujukan": getdetilrujukan['response']['rujukan']['noKunjungan'], #dari data rujukan
        "tujuan_kunj": tujuan_kunj, #otomatis kan bisa
        "kd_penunjang": kd_penunjang, #otomatis kan bisa
        "assesment_pel": assesment_pel, #otomatis kan bisa
        "nosurat_skdp_sep": nosurat_skdp_sep, #otomatis kan bisa
        "dpjp_suratkontrol": dpjp_suratkontrol, #otomatis kan bisa
        "alber": "sakit",
        "pasdatDg": "klg",
        "jenis_kecelakaan": "",
        "lokasi_kecelakaan": "",
        "kll_tgl_kejadian": "",
        "kll_ketkejadian": "",
        "hubungan": "",
        "id_poli": idpoli + '~' + payload['kodepoli'], #ambil dari poliklinik
        "id_dokter": str(cekdokter[0]) + '-' + payload['kodedokter'] + '-' + cekdokter[1],#ambil dari data_dokter
        "dokter_bpjs":  payload['kodedokter']  + "-" + cekdokter[1],
        "diagnosa": getdetilrujukan['response']['rujukan']['diagnosa']['kode'] + "@" + getdetilrujukan['response']['rujukan']['diagnosa']['nama'],#ambil dari rujukan
        "id_diagnosa": "",
        "kelas_pasien": kelasrawat, #ambil dari rujukan
        "no_telp": "",
        "catatan": catatan,
        "cetak_kartu1": "",
        'noantrian':payload['noantrian']
    }

    # res = requests.request("POST", 'http://192.168.56.102/antrol/api/insert_daftar_ulang_new_antrol', headers=headers, data=reqdata)
    # print(res.text)
    res = await insert_daftar_ulang_new_antrol(db_ekamek,reqdata)
    return res

async def insert_daftar_ulang_nonjkn(payload,db_ekamek):
    from datetime import timezone, timedelta

    # Set the timezone to Asia/Jakarta
    jakarta_timezone = timezone(timedelta(hours=7))  # UTC+7

    # get detil peserta
    # /Peserta/nokartu/{parameter 1}/tglSEP/{parameter 2}
    # Mendapatkan tanggal saat ini
    now = datetime.datetime.now(jakarta_timezone)
    # return now
    # Mengubah ke format Y-m-d
    date_string = now.strftime("%Y-%m-%d")
    # getdetilpeserta = bpjs_vclaim.get_vclaim('/Peserta/nokartu/'+payload['nomorkartu']+'/tglSEP/' + date_string)
    # return getdetilpeserta
    kelasrawat = 'II'
    # if getdetilpeserta['response']['peserta']['hakKelas']['kode'] == '2':
    #     kelasrawat = 'II'
    # elif getdetilpeserta['response']['peserta']['hakKelas']['kode'] == '3':
    #     kelasrawat = 'III'
    # else:
    #     kelasrawat = 'I'

    # get rujukan by no kartu
    # BASE URL}/{Service Name}/Rujukan/Peserta/{parameter}
    # {BASE URL}/{Service Name}/Rujukan/RS/Peserta/{parameter}
    # getdetilrujukan = bpjs_vclaim.get_vclaim('/Rujukan/Peserta/'+payload['nomorkartu'])
    # return getdetilrujukan



    # get id poli by poli_bpjs
    cekpoliklinik = await db_manager_ekamek.caridatapoliklinik(db_ekamek,payload['kodepoli'])
    tujuan_kunj = '0'
    kd_penunjang = ''
    assesment_pel = ''
    nosurat_skdp_sep = ''
    dpjp_suratkontrol = ''
    
    # jenis kunjungan=>  
    # 1 = rujukan fktp
    # 2 = internal
    # 3 = kontrol
    # 4 = rujukan rs
    # if payload['jeniskunjungan'] == '2':
    #     tujuan_kunj = '0'
    #     kd_penunjang = ''
    #     assesment_pel = '1'
    #     nosurat_skdp_sep = ''
    #     dpjp_suratkontrol = ''
    # elif payload['jeniskunjungan'] == '3':
    #     tujuan_kunj = '2'
    #     kd_penunjang = ''
    #     assesment_pel = '5'
    #     nosurat_skdp_sep = payload['nomorreferensi']
    #     dpjp_suratkontrol = payload['kodedokter']


    # get id_dokter by dokter npjs
    cekdokter = await db_manager_ekamek.caridatadokter(db_ekamek,payload['kodedokter'])
    # print(cekdokter)
    # return {'ok'}
    
    # data_d
    no_medrecs = await db_manager_ekamek.carinomedrecberdasarnorm(db_ekamek,payload['norm'])


    reqdata = {
        "reservasi": payload['kodebooking'],
        "no_medrec": no_medrecs[0],
        "xcreate": "ANTROL_ONSITE",
        "kelasrawat": kelasrawat, #? dari data peserta
        "asalrujukan": '', #? dari data rujukan
        "tglrujukan": '', #? dari data rujukan
        "ppkrujukan": '', #? dari data rujukan
        "jns_kunj": "LAMA", 
        "namafaskes": '', #? dari data rujukan
        "prb": '', #? dari data peserta
        "online": "0", 
        "noreservasi": payload['kodebooking'], #kodebooking
        "noreg_asal_konsul": "",
        "tgl_kunjungan": payload['tanggalperiksa'],
        "cara_bayar": "UMUM",
        "cara_dtg": "SENDIRI",
        "cara_kunj": "SENDIRI", #dari data rujukan #"RUJUKAN PUSKESMAS","RUJUKAN RS"
        "no_bpjs": payload['nomorkartu'],
        "id_kontraktor": "1",
        "no_sep": "", 
        "no_rujukan": '', #dari data rujukan
        "tujuan_kunj": '', #otomatis kan bisa
        "kd_penunjang": '', #otomatis kan bisa
        "assesment_pel": '', #otomatis kan bisa
        "nosurat_skdp_sep":'', #otomatis kan bisa
        "dpjp_suratkontrol": '', #otomatis kan bisa
        "alber": "sakit",
        "pasdatDg": "klg",
        "jenis_kecelakaan": "",
        "lokasi_kecelakaan": "",
        "kll_tgl_kejadian": "",
        "kll_ketkejadian": "",
        "hubungan": "",
        "id_poli": cekpoliklinik[0] + '~' + payload['kodepoli'], #ambil dari poliklinik
        "id_dokter": str(cekdokter[0]) + '-' + payload['kodedokter'] + '-' + cekdokter[1],#ambil dari data_dokter
        "dokter_bpjs":  payload['kodedokter']  + "-" + cekdokter[1],
        "diagnosa": '',#ambil dari rujukan
        "id_diagnosa": "",
        "kelas_pasien": kelasrawat, #ambil dari rujukan
        "no_telp": "",
        "catatan": "",
        "cetak_kartu1": "",
        'noantrian':payload['noantrian']
    }

    # res = requests.request("POST", 'http://192.168.56.102/antrol/api/insert_daftar_ulang_new_antrol', headers=headers, data=reqdata)
    # print(res.text)
    res = await insert_daftar_ulang_new_antrol(db_ekamek,reqdata)
    return res


async def insert_daftar_ulang_new_antrol(db_ekamek,register):
    # print(register)
    daftarulangs = register.copy()
    # Penambahan tgl kunjungan karena butuh time juga
    register['tgl_kunjungan'] += ' ' + datetime.datetime.now().strftime('%H:%M:%S')

    if register['id_kontraktor'] == '':
        register['id_kontraktor'] = None

    umur = await db_manager_ekamek.generateumur(db_ekamek,register['no_medrec'])
    # register['umurrj'], register['ublnrj'], register['uharirj'] = umur
    register['umurrj'] = 0 if umur[0] is None else umur[0] 
    register['ublnrj'] = 0 if umur[2] is None else umur[2]
    register['uharirj'] =0 if umur[3] is None else  umur[3]

    register['id_poli'] = register['id_poli'][:4]
    register['id_dokter'] = register['id_dokter'].split('-')[0]
    register['diagnosa'] = register.get('diagnosa', '').split('@')[0]
    register['biayadaftar'] = 0
    register['vtot'] = 0
    register['xupdate'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Remove unnecessary fields
    unnecessary_fields = [
        'kekhususan_lainnya', 'kelasrawat', 'asalrujukan', 'tglrujukan', 'ppkrujukan', 
        'tujuan_kunj', 'flag_procedure', 'kd_penunjang', 'assesment_pel', 'nosurat_skdp_sep', 
        'dpjp_suratkontrol', 'no_telp', 'catatan', 'no_bpjs', 'alber', 'pasdatDg', 'jenis_kecelakaan', 
        'dokter_bpjs', 'id_diagnosa', 'cetak_kartu1', 'namafaskes', 'prb', 'katarak', 'cetak_kartu', 
        'ppkrujukan_jarkomdat', 'reservasi', 'antrol', 'nik', 'norm'
    ]
    for field in unnecessary_fields:
        register.pop(field, None)

    if daftarulangs.get('reservasi'):
        register['noreservasi'] = daftarulangs['reservasi']

    register['kll_tgl_kejadian'] = daftarulangs['tgl_kunjungan']
    id = await db_manager_ekamek.create_registration(db_ekamek,register)

    datat = {'no_register': id}
    # print(datat)
    # return id

    if register['cara_bayar'] == 'BPJS':
        datainput = daftarulangs.copy()
        if 'ppkrujukan_jarkomdat' in datainput:
            datainput['ppkrujukan'] = datainput['ppkrujukan_jarkomdat']

        input_bpjs = {
            'no_medrec': datainput['no_medrec'],
            'tgl_sep': datainput['tgl_kunjungan'],
            'no_register': id,
            'no_kartu': datainput['no_bpjs'],
            'kelasrawat': datainput['kelasrawat'],
            'asalrujukan': datainput['asalrujukan'],
            'tglrujukan': datainput['tglrujukan'] if datainput['cara_kunj'] != 'DATANG SENDIRI' else datainput['tgl_kunjungan'],
            'norujukan': datainput['no_rujukan'],
            'ppkrujukan': datainput['ppkrujukan'].split('@')[0],
            'diagawal': datainput['diagnosa'].split('@')[0],
            'politujuan': datainput['id_poli'].split('~')[1],
            'tujuankunj': datainput['tujuan_kunj'],
            'flagprocedure': datainput.get('flag_procedure', ''),
            'kdpenunjang': datainput.get('kd_penunjang', ''),
            'assesmentpel': datainput.get('assesment_pel', ''),
            'nosurat': datainput.get('nosurat_skdp_sep', ''),
            'dpjpsurat': datainput.get('dpjp_suratkontrol', ''),
            'dpjplayan': datainput['dpjp_suratkontrol'] if datainput['dpjp_suratkontrol'] else datainput['dokter_bpjs'].split('-')[0],
            'namadokter': datainput['dokter_bpjs'].split('-')[1],
            'namafaskes': datainput['namafaskes'],
            'user': datainput['xcreate'],
            'notelp': datainput['no_telp'],
            'catatan': datainput['catatan'],
            'prb': datainput['prb'],
            'katarak': datainput.get('katarak', '0'),
        }

        if datainput['tglrujukan'] == '':
            datainput['tglrujukan'] = datainput['tgl_sep']

        await db_manager_ekamek.register_bpjs(db_ekamek,input_bpjs)

    datat.update({
        'id_poli': register['id_poli'],
        'jenis_pasien': daftarulangs['jns_kunj'],
        'cara_bayar': daftarulangs['cara_bayar'],
        'cara_dtg': daftarulangs['cara_dtg']
    })

    await insert_tindakan(db_ekamek,datat)

    return id


async def insert_tindakan(db_ekamek,data1):
    
    user = "ANTRIAN_ONSITE"
    data = {
        'xuser': user,
        'xupdate': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'no_register': data1['no_register'],
        'id_poli': data1['id_poli']
    }
    
    if data['id_poli'] == 'BA00':
        if data1['jenis_pasien'] == 'BARU':
            detailtind = await db_manager_ekamek.get_detail_tindakan_new(db_ekamek,'1B0103')
            data.update({
                'idtindakan': '1B0103',
                'tgl_kunjungan': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'nmtindakan': detailtind[1],
                'tmno': detailtind[3],
                'biaya_tindakan': detailtind[2],
                'biaya_alkes': 0,
                'qtyind': '1',
                'vtot': int(detailtind[2]) + 0
            })
            await db_manager_ekamek.insert_tindakan(db_ekamek,data)

        detailtind = await db_manager_ekamek.get_detail_tindakan_new(db_ekamek,'1B0108')
        data.update({
            'idtindakan': '1B0108',
            'tgl_kunjungan': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'nmtindakan': detailtind[1],
            'tmno': detailtind[3],
            'biaya_tindakan': detailtind[2],
            'biaya_alkes': 0,
            'qtyind': '1',
            'vtot': int(detailtind[2]) + 0
        })
        await db_manager_ekamek.insert_tindakan(db_ekamek,data)

        vtot_sebelumnya = await db_manager_ekamek.get_vtot(db_ekamek,data1['no_register'])
        data_vtot = {
            'vtot': (int(vtot_sebelumnya[0]) if vtot_sebelumnya and vtot_sebelumnya[0] is not None else 0) + data['vtot'],
            'no_register': data1['no_register']
        }
        await db_manager_ekamek.update_vtot(db_ekamek,data_vtot)

    elif data['id_poli'] == 'BJ00':
        if data1['jenis_pasien'] == 'BARU':
            detailtind = await db_manager_ekamek.get_detail_tindakan_new(db_ekamek,'1B0104')
            data.update({
                'idtindakan': '1B0104',
                'bpjs': '1' if data1.get('cara_bayar') == 'BPJS' else '0',
                'tgl_kunjungan': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'nmtindakan': detailtind[1],
                'tmno': detailtind[3],
                'biaya_tindakan': detailtind[2],
                'biaya_alkes': 0,
                'qtyind': '1',
                'vtot': int(detailtind[2]) + 0
            })
            await db_manager_ekamek.insert_tindakan(db_ekamek,data)

        detailtind = await db_manager_ekamek.get_detail_tindakan_new(db_ekamek,'1B0102')
        data.update({
            'idtindakan': '1B0102',
            'tgl_kunjungan': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'nmtindakan': detailtind[1],
            'tmno': detailtind[3],
            'biaya_tindakan': detailtind[2],
            'biaya_alkes': 0,
            'qtyind': '1',
            'vtot': int(detailtind[2]) + 0
        })
        await db_manager_ekamek.insert_tindakan(db_ekamek,data)

        vtot_sebelumnya = await db_manager_ekamek.get_vtot(db_ekamek,data1['no_register'])
        data_vtot = {
            'vtot': (int(vtot_sebelumnya[0]) if vtot_sebelumnya and vtot_sebelumnya[0] is not None else 0) + data['vtot'],
            'no_register': data1['no_register']
        }
        await db_manager_ekamek.update_vtot(db_ekamek,data_vtot)

    elif data['id_poli'] in ['BU00', 'BG00']:
        if data1['jenis_pasien'] == 'BARU':
            detailtind = await db_manager_ekamek.get_detail_tindakan_new(db_ekamek,'1B0104')
            data.update({
                'idtindakan': '1B0104',
                'bpjs': '1' if data1.get('cara_bayar') == 'BPJS' else '0',
                'tgl_kunjungan': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'nmtindakan': detailtind[1],
                'tmno': detailtind[3],
                'biaya_tindakan': detailtind[2],
                'biaya_alkes': 0,
                'qtyind': '1',
                'vtot': int(detailtind[2]) + 0
            })
            await db_manager_ekamek.insert_tindakan(db_ekamek,data)

        detailtind = await db_manager_ekamek.get_detail_tindakan_new(db_ekamek,'1B0105')
        data.update({
            'idtindakan': '1B0105',
            'tgl_kunjungan': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'nmtindakan': detailtind[1],
            'tmno': detailtind[3],
            'biaya_tindakan': detailtind[2],
            'biaya_alkes': 0,
            'qtyind': '1',
            'vtot': int(detailtind[2]) + 0
        })
        await db_manager_ekamek.insert_tindakan(db_ekamek,data)

        vtot_sebelumnya = await db_manager_ekamek.get_vtot(data1['no_register'])
        data_vtot = {
            'vtot': (int(vtot_sebelumnya[0]) if vtot_sebelumnya and vtot_sebelumnya[0] is not None else 0) + data['vtot'],
            'no_register': data1['no_register']
        }
        await db_manager_ekamek.update_vtot(db_ekamek,data_vtot)

    else:
        if data1['jenis_pasien'] == 'BARU':
            detailtind = await db_manager_ekamek.get_detail_tindakan_new(db_ekamek,'1B0104')
            data.update({
                'idtindakan': '1B0104',
                'bpjs': '1' if data1.get('cara_bayar') == 'BPJS' else '0',
                'tgl_kunjungan': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'nmtindakan': detailtind[1],
                'tmno': detailtind[3],
                'biaya_tindakan': detailtind[2],
                'biaya_alkes': 0,
                'qtyind': '1',
                'vtot': int(detailtind[2]) + 0
            })
            await db_manager_ekamek.insert_tindakan(db_ekamek,data)

        detailtind = await db_manager_ekamek.get_detail_tindakan_new(db_ekamek,'1B0102')

        data.update({
            'idtindakan': '1B0107',
            'tgl_kunjungan': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'nmtindakan': detailtind[1],
            'tmno': detailtind[3],
            'biaya_tindakan': detailtind[2],
            'biaya_alkes': 0,
            'qtyind': '1',
            'vtot': int(detailtind[2]) + 0
        })
        await db_manager_ekamek.insert_tindakan(db_ekamek,data)

        vtot_sebelumnya = await db_manager_ekamek.get_vtot(db_ekamek,data1['no_register'])
        # print(vtot_sebelumnya)
        data_vtot = {
            'vtot': (int(vtot_sebelumnya[0]) if vtot_sebelumnya and vtot_sebelumnya[0] is not None else 0) + data['vtot'],
            'no_register': data1['no_register']
        }
        await db_manager_ekamek.update_vtot(db_ekamek,data_vtot)
    return True

@adminantrian.post('/ambilantriannonjkn')
async def ambilantrian(payload:models.Ambilantrian,db: Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):
    
    # cek pasien dari db ekamek
    norm = 0
    # cek apakah payload.nik = '0000000000000000';
    # jika ya, maka cari berdasarkan no_rm, jika tidak cari berdasarkan no_identitas
    if payload.nik == '0000000000000000':
        cekPasien = await db_manager_ekamek.caridatapasienno_cm(payload.norm)
    else:
        cekPasien = await db_manager_ekamek.caridatapasiennik(db_ekamek,payload.nik)
    if not cekPasien: # tandanya pasien gaada
        # cek di pasien baru daftar di antrol
        cekPasienBaru = await db_manager.cekPasienBaruExistNik(db = db,nik = payload.nik)
        if not cekPasienBaru:
            return {
                'metaData' :{
                    'message': 'Data pasien ini tidak ditemukan, silahkan Melakukan Registrasi Pasien Baru',
                    'code':202
                }
            } 
        else:
            namaPasien = cekPasienBaru.nama   
            payload.pasienbaru = '1'
            norm = cekPasienBaru.norm

    else:
        norm = cekPasien[2]
        namaPasien = cekPasien[1]

    checkExist = await db_manager.checkAntrianExistNoRm(db,payload.norm,payload.tanggalperiksa)
    if checkExist:
        return validation.handleErrorAdmin('Nomor Antrean Hanya Dapat Diambil 1 Kali Pada Tanggal Yang Sama')
    
    cekPoli = await db_manager_ekamek.carinamapoli(db_ekamek,payload.kodepoli)
    if not cekPoli:
        return validation.handleErrorAdmin('Poli Tidak Ditemukan')

    cekDokterDanJadwal = service.cekjadwaldokter(payload.kodepoli,payload.tanggalperiksa)
    if not cekDokterDanJadwal:
        return validation.handleErrorAdmin('Koneksi dengan WS BPJS Antrian Cek Jadwal Dokter Gagal!')
    
    if cekDokterDanJadwal['metadata']['code'] != 200:
        return validation.handleErrorAdmin(cekDokterDanJadwal['metadata']['message'])
    
    resultJadwalDokter = {}
    for val in cekDokterDanJadwal['response']:
        print(val)
        if val['kodedokter'] == int(payload.kodedokter):
            resultJadwalDokter = val

    if resultJadwalDokter == {}:
        # return validation.handleErrorAdmin('Jadwal Dokter Tidak Ditemukan Pada Tanggal Tersebut!')
        return validation.handleErrorAdmin(f"Jadwal Dokter Tersebut Belum Tersedia,Silahkan Reschedule Tanggal dan Jam Praktek Lainnya")



    cekDokter = await db_manager_ekamek.carinamadokter(db_ekamek,payload.kodedokter)
    if not cekDokter:
        return validation.handleErrorAdmin('Kode Dokter Tidak sesuai')

    payload.namadokter = resultJadwalDokter['namadokter']
    payload.namapoli = resultJadwalDokter['namasubspesialis']
    payload.nama = namaPasien

    cekTotalAntrian = await db_manager.cekTotalAntrian(db=db,kodehfis = payload.kodedokter,pertgl=payload.tanggalperiksa)
    # estimasi waktu dilayani
    totalAntrian = int(cekTotalAntrian['count'])
    if totalAntrian == 0:
        totalAntrian = 1
    waktuTotalAntrian = (1 if totalAntrian == 0 else totalAntrian) * 10 # (satu pelayanan itu 10 menit)
    strWaktuPelayananMulai = payload.tanggalperiksa + ' 08:00:00'
    waktuPelayananMulai = datetime.datetime.strptime(strWaktuPelayananMulai, '%Y-%m-%d %H:%M:%S')

    validasiPeriksaHariIni = validation.validasiHariIni(payload.tanggalperiksa)
    if validasiPeriksaHariIni:
        splitJadwalJamMulaiSelesai = validation.validasiJadwalMelebihiJam(payload.jampraktek)
        if not splitJadwalJamMulaiSelesai:
            return validation.handleErrorAdmin(f"Pendaftaran Ke Poli ({resultJadwalDokter['namasubspesialis']}) Sudah Tutup Jam {payload.jampraktek.split('-')[1]}")

        # added feature
        # cek jika pasien mendaftar selama pelayanan berlangsung ( misal jam 08.00 waktu mulai)
        # dan pasien mendaftar di jam 09:00 maka waktu kira kira dilayani di jam 09: ditambah dengan menit total
        # antrian yang akan dilayani
        # if()
        # jakarta_timezone = pytz.timezone('Asia/Jakarta')
        now = datetime.datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        dt_string = datetime.datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
        # print(dt_string)
        # print('-----ini-----')
        
        # jika pasien masuuuk melebih jam praktek maka lanjutkan jam praktek + count berapa tersisa antrian
        if dt_string>waktuPelayananMulai:
            waktuPelayananMulai = dt_string
        # end added
    
    estimasidilayani = waktuPelayananMulai + datetime.timedelta(minutes = waktuTotalAntrian)
    estimasidilayani = round(int(estimasidilayani.timestamp()) * 1000)
    payload.estimasidilayani = estimasidilayani
    payload.sisakuotajkn = int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian)
    payload.kuotajkn = int(resultJadwalDokter['kapasitaspasien'])
    payload.sisakuotanonjkn = int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian)
    payload.kuotanonjkn = int(resultJadwalDokter['kapasitaspasien'])

    try:
        # Attempt to convert the date string to a datetime object
        tanggalperiksa_date = datetime.datetime.strptime(payload.tanggalperiksa, '%Y-%m-%d')
    except ValueError:
        # Handle the case where the date string is not a valid date
        return validation.handleErrorAdmin("Tanggal Periksa Tidak Valid")
        # Handle this error as appropriate for your application


    # print(norm)
    # return False
    payload.norm = norm
    
    insert = await db_manager.insert_antrian_poli_onsite(db= db,payload = payload)
    if isinstance(insert, dict):
        return insert

    bodyreq = {
        'nomorkartu': payload.nomorkartu,
        'kodepoli': payload.kodepoli,
        'jeniskunjungan': payload.jeniskunjungan,
        'nomorreferensi':payload.nomorreferensi,
        'kodedokter':payload.kodedokter,
        'kodebooking':insert.kodebooking,
        'norm':norm,
        'tanggalperiksa':payload.tanggalperiksa,
        'kodepoli':payload.kodepoli,
        'noantrian':insert.angkaantrean
    }
    # return bodyreq
    reqdata = await insert_daftar_ulang_nonjkn(bodyreq,db_ekamek)


    return {
        'response':{
            'nomorantrean':insert.nomorantrian, #2 digit nama poli didepan + max dari antrian per poli per dokter + 1 
            'angkaantrean':insert.angkaantrean, #max dari antrian per poli per dokter + 1 
            'kodebooking':insert.kodebooking, #nomr + angkaantrean 
            'namapoli':resultJadwalDokter['namasubspesialis'], #nm_poli <- poliklinik
            'norm': norm, #nomr
            'namadokter': resultJadwalDokter['namadokter'], #nm_dokter <- data_dokter
            'estimasidilayani':estimasidilayani, # timestamp epoch tanggal_periksa: jam pelayanan awal  + (jumlah pasien * 15 menit)
            'sisakuotajkn': int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian), #50 - jml antrian bpjs poli 
            'kuotajkn':int(resultJadwalDokter['kapasitaspasien']), #nomr
            'sisakuotanonjkn':int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian), #50 - jml antrian non bpjs poli 
            'kuotanonjkn':int(resultJadwalDokter['kapasitaspasien']), #nomr
            'keterangan':'', #nomr
            
        },
        'metaData': {
            'message':'Ok',
            'code':200
        }
    }

@adminantrian.post('/ambilantriannonjknlama')
async def ambilantrian(payload:models.Ambilantrian,db: Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):
    
    # cek pasien dari db ekamek
    norm = 0
    # cek apakah payload.nik = '0000000000000000';
    # jika ya, maka cari berdasarkan no_rm, jika tidak cari berdasarkan no_identitas
    if payload.nik == '0000000000000000':
        cekPasien = await db_manager_ekamek.caridatapasienno_cm(payload.norm)
    else:
        cekPasien = await db_manager_ekamek.caridatapasiennik(db_ekamek,payload.nik)
    if not cekPasien: # tandanya pasien gaada
        # cek di pasien baru daftar di antrol
        cekPasienBaru = await db_manager.cekPasienBaruExistNik(db = db,nik = payload.nik)
        if not cekPasienBaru:
            return {
                'metaData' :{
                    'message': 'Data pasien ini tidak ditemukan, silahkan Melakukan Registrasi Pasien Baru',
                    'code':202
                }
            } 
        else:
            namaPasien = cekPasienBaru.nama   
            payload.pasienbaru = '1'
            norm = cekPasienBaru.norm

    else:
        norm = cekPasien[2]
        namaPasien = cekPasien[1]

    checkExist = await db_manager.checkAntrianExistNoRm(db,payload.norm,payload.tanggalperiksa)
    if checkExist:
        return validation.handleErrorAdmin('Nomor Antrean Hanya Dapat Diambil 1 Kali Pada Tanggal Yang Sama')
    
    cekPoli = await db_manager_ekamek.carinamapoli(db_ekamek,payload.kodepoli)
    if not cekPoli:
        return validation.handleErrorAdmin('Poli Tidak Ditemukan')

    cekDokterDanJadwal = service.cekjadwaldokter(payload.kodepoli,payload.tanggalperiksa)
    if not cekDokterDanJadwal:
        return validation.handleErrorAdmin('Koneksi dengan WS BPJS Antrian Cek Jadwal Dokter Gagal!')
    
    if cekDokterDanJadwal['metadata']['code'] != 200:
        return validation.handleErrorAdmin(cekDokterDanJadwal['metadata']['message'])
    
    resultJadwalDokter = {}
    for val in cekDokterDanJadwal['response']:
        print(val)
        if val['kodedokter'] == int(payload.kodedokter):
            resultJadwalDokter = val

    if resultJadwalDokter == {}:
        # return validation.handleErrorAdmin('Jadwal Dokter Tidak Ditemukan Pada Tanggal Tersebut!')
        return validation.handleErrorAdmin(f"Jadwal Dokter Tersebut Belum Tersedia,Silahkan Reschedule Tanggal dan Jam Praktek Lainnya")



    cekDokter = await db_manager_ekamek.carinamadokter(db_ekamek,payload.kodedokter)
    if not cekDokter:
        return validation.handleErrorAdmin('Kode Dokter Tidak sesuai')

    payload.namadokter = resultJadwalDokter['namadokter']
    payload.namapoli = resultJadwalDokter['namasubspesialis']
    payload.nama = namaPasien

    cekTotalAntrian = await db_manager.cekTotalAntrian(db=db,kodehfis = payload.kodedokter,pertgl=payload.tanggalperiksa)
    # estimasi waktu dilayani
    totalAntrian = int(cekTotalAntrian['count'])
    if totalAntrian == 0:
        totalAntrian = 1
    waktuTotalAntrian = (1 if totalAntrian == 0 else totalAntrian) * 10 # (satu pelayanan itu 10 menit)
    strWaktuPelayananMulai = payload.tanggalperiksa + ' 08:00:00'
    waktuPelayananMulai = datetime.datetime.strptime(strWaktuPelayananMulai, '%Y-%m-%d %H:%M:%S')

    validasiPeriksaHariIni = validation.validasiHariIni(payload.tanggalperiksa)
    if validasiPeriksaHariIni:
        splitJadwalJamMulaiSelesai = validation.validasiJadwalMelebihiJam(payload.jampraktek)
        if not splitJadwalJamMulaiSelesai:
            return validation.handleErrorAdmin(f"Pendaftaran Ke Poli ({resultJadwalDokter['namasubspesialis']}) Sudah Tutup Jam {payload.jampraktek.split('-')[1]}")

        # added feature
        # cek jika pasien mendaftar selama pelayanan berlangsung ( misal jam 08.00 waktu mulai)
        # dan pasien mendaftar di jam 09:00 maka waktu kira kira dilayani di jam 09: ditambah dengan menit total
        # antrian yang akan dilayani
        # if()
        # jakarta_timezone = pytz.timezone('Asia/Jakarta')
        now = datetime.datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        dt_string = datetime.datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
        # print(dt_string)
        # print('-----ini-----')
        
        # jika pasien masuuuk melebih jam praktek maka lanjutkan jam praktek + count berapa tersisa antrian
        if dt_string>waktuPelayananMulai:
            waktuPelayananMulai = dt_string
        # end added
    
    estimasidilayani = waktuPelayananMulai + datetime.timedelta(minutes = waktuTotalAntrian)
    estimasidilayani = round(int(estimasidilayani.timestamp()) * 1000)
    payload.estimasidilayani = estimasidilayani
    payload.sisakuotajkn = int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian)
    payload.kuotajkn = int(resultJadwalDokter['kapasitaspasien'])
    payload.sisakuotanonjkn = int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian)
    payload.kuotanonjkn = int(resultJadwalDokter['kapasitaspasien'])

    try:
        # Attempt to convert the date string to a datetime object
        tanggalperiksa_date = datetime.datetime.strptime(payload.tanggalperiksa, '%Y-%m-%d')
    except ValueError:
        # Handle the case where the date string is not a valid date
        return validation.handleErrorAdmin("Tanggal Periksa Tidak Valid")
        # Handle this error as appropriate for your application


    insert = await db_manager.insert_antrian_poli_onsite_lama(db= db,payload = payload)
    if isinstance(insert, dict):
        return insert

    bodyreq = {
        'nomorkartu': payload.nomorkartu,
        'kodepoli': payload.kodepoli,
        'jeniskunjungan': payload.jeniskunjungan,
        'nomorreferensi':payload.nomorreferensi,
        'kodedokter':payload.kodedokter,
        'kodebooking':insert.kodebooking,
        'norm':norm,
        'tanggalperiksa':payload.tanggalperiksa,
        'kodepoli':payload.kodepoli,
        'noantrian':insert.angkaantrean
    }
    # return bodyreq
    reqdata = await insert_daftar_ulang_nonjkn(bodyreq,db_ekamek)


    return {
        'response':{
            'nomorantrean':insert.nomorantrian, #2 digit nama poli didepan + max dari antrian per poli per dokter + 1 
            'angkaantrean':insert.angkaantrean, #max dari antrian per poli per dokter + 1 
            'kodebooking':insert.kodebooking, #nomr + angkaantrean 
            'namapoli':resultJadwalDokter['namasubspesialis'], #nm_poli <- poliklinik
            'norm': norm, #nomr
            'namadokter': resultJadwalDokter['namadokter'], #nm_dokter <- data_dokter
            'estimasidilayani':estimasidilayani, # timestamp epoch tanggal_periksa: jam pelayanan awal  + (jumlah pasien * 15 menit)
            'sisakuotajkn': int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian), #50 - jml antrian bpjs poli 
            'kuotajkn':int(resultJadwalDokter['kapasitaspasien']), #nomr
            'sisakuotanonjkn':int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian), #50 - jml antrian non bpjs poli 
            'kuotanonjkn':int(resultJadwalDokter['kapasitaspasien']), #nomr
            'keterangan':'', #nomr
            
        },
        'metaData': {
            'message':'Ok',
            'code':200
        }
    }



@adminantrian.post('/pasienbaru')
async def pasienbaru(payload:models.Pasienbaru,db: Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):

    if not validation.checkVariableKosong(payload.nomorkartu):
        return validation.handleError('Nomor Kartu Belum Diisi')

    # validasi jika nomor kartu == 13 dan validasi jika nomor kartu numeric semua
    if not validation.isVariableIsXDigits(payload.nomorkartu,13) or not validation.isFullOfInteger(payload.nomorkartu):
        return validation.handleError('Format Nomor Kartu Tidak Sesuai')
    
    if not validation.checkVariableKosong(payload.nik):
        return validation.handleError('NIK Belum Diisi')

    # validasi jika nomor kartu == 13
    if not validation.isVariableIsXDigits(payload.nik,16) or not validation.isFullOfInteger(payload.nik):
        return validation.handleError('Format NIK Tidak Sesuai')

    if not validation.checkVariableKosong(payload.nomorkk):
        return validation.handleError('Nomor KK Belum Diisi')

    if not validation.checkVariableKosong(payload.nama):
        return validation.handleError('Nama Belum Diisi')

    if not validation.checkVariableKosong(payload.jeniskelamin):
        return validation.handleError('Jenis Kelamin Belum Diisi')

    if not validation.checkVariableKosong(payload.tanggallahir):
        return validation.handleError('Tanggal Lahir Belum Diisi')

    if not validation.checkVariableKosong(payload.alamat):
        return validation.handleError('Alamat Belum Diisi')

    if not validation.checkVariableKosong(payload.kodeprop):
        return validation.handleError('Kode Propinsi Belum Diisi')

    if not validation.checkVariableKosong(payload.namaprop):
        return validation.handleError('Nama Propinsi Belum Diisi')

    if not validation.checkVariableKosong(payload.kodedati2):
        return validation.handleError('Kode Dati 2 Belum Diisi')

    if not validation.checkVariableKosong(payload.namadati2):
        return validation.handleError('Dati 2 Belum Diisi')

    if not validation.checkVariableKosong(payload.kodekec):
        return validation.handleError('Kode Kecamatan Belum Diisi')

    if not validation.checkVariableKosong(payload.namakec):
        return validation.handleError('Kecamatan Belum Diisi')

    if not validation.checkVariableKosong(payload.kodekel):
        return validation.handleError('Kode Kelurahan Belum Diisi')

    if not validation.checkVariableKosong(payload.namakel):
        return validation.handleError('Kelurahan Belum Diisi')

    if not validation.checkVariableKosong(payload.rt):
        return validation.handleError('RT Belum Diisi')

    if not validation.checkVariableKosong(payload.rw):
        return validation.handleError('RW Belum Diisi')

    # validasi format tgl lahir tidak sesuai atau lebih dari hari ini
    if not validation.validasiTglLahir(payload.tanggallahir):
        return validation.handleError('Format Tanggal Lahir Tidak Sesuai')

    # checkExist = await db_manager.checkPasienExist(db,payload.nomorkartu)
    # if checkExist:
    #     return validation.handleError('Data Peserta Sudah Pernah Dientrikan')

    # insert = await db_manager.insertpasienbaru(db = db,payload = payload)
    # return {
    #     'response':{
    #         'norm':f'{"{:08d}".format(insert.norm)}'
    #     },
    #     'metadata':{
    #         'message':'Harap datang ke admisi untuk melengkapi data rekam medis',
    #         'code':200
    #     }
    # }
     # ini untuk uat mobile jkn di off kan
    checkExist = await db_manager_ekamek.checkPasienExist(db_ekamek,payload.nomorkartu)
    if checkExist:
        return {
        'response':{
            'norm':f'{checkExist[0]}'
        },
        'metadata':{
            'message':'Harap datang ke admisi untuk melengkapi data rekam medis',
            'code':200
        }
    }

    # sampe sini

    insert = await db_manager_ekamek.insertpasienbaru(db = db_ekamek,payload = payload)
    return {
        'response':{
            'norm':f'{insert[0]}'
        },
        'metadata':{
            'message':'Harap datang ke admisi untuk melengkapi data rekam medis',
            'code':200
        }
    }




@adminantrian.get('/dashboardantrianfarmasi')
async def dashboardantrianfarmasi(db:Session=Depends(get_db)):
    res = []
    result = await db_manager.listantrianbelumdiperiksafarmasi(db = db)
    pasiendilayani = await db_manager.listantriandiperiksafarmasi(db=db)
    pasien = []
    for j in result:
        pasien.append({
                'nourut':j[12],
                'nomorantrian':j[12],
                'nama':j[22],
                'norm':j[5]
        })
    if result is not None:
        res.append({
            'pasiendilayani':{
                'nourut':pasiendilayani[12] if pasiendilayani is not None else '',
                'nomorantrian':pasiendilayani[12] if pasiendilayani is not None else '',
                'nama':pasiendilayani[22] if pasiendilayani is not None else '',
                'norm':pasiendilayani[5] if pasiendilayani is not None else ''
            },
            'pasien':pasien
        })
        

    # print(cekDokterDanJadwal['response'])

    return res


@adminantrian.get('/dashboardantrianadmisi')
async def dashboardantrianadmisi(db:Session=Depends(get_db)):
    res = []
    result = await db_manager.listantrianbelumdiperiksaadmisinew(db = db)
    pasiendilayani = await db_manager.listantriandiperiksaadmisinew(db=db)
    pasien = []

    # Process daftar antrian menunggu
    for j in result:
        pasien.append({
            'nourut': j[1],
            'nomorantrian': j[1],
            'status': j.status if hasattr(j, 'status') else 'menunggu',
            'loket': j.loket if hasattr(j, 'loket') else None
        })

    # Process antrian yang sedang dilayani
    pasiendilayani_data = {}
    if pasiendilayani is not None:
        pasiendilayani_data = {
            'nourut': pasiendilayani[1],
            'nomorantrian': pasiendilayani[1],
            'loket': pasiendilayani.loket if hasattr(pasiendilayani, 'loket') else None,
            'status': pasiendilayani.status if hasattr(pasiendilayani, 'status') else 'dipanggil'
        }

    if result is not None:
        res.append({
            'pasiendilayani': pasiendilayani_data,
            'pasien': pasien
        })

    return res


@adminantrian.get('/dashboardantrian/{poli}')
async def dashboardantrian(poli:str,db:Session = Depends(get_db)):
    res = []
    from datetime import timezone, timedelta

    # Set the timezone to Asia/Jakarta
    jakarta_timezone = timezone(timedelta(hours=7))  # UTC+7
    print(poli)

    # ambil dokter yang ada di antrian saat ini
    cekDokterDanJadwal = service.cekjadwaldokter(poli,(datetime.datetime.today()).strftime('%Y-%m-%d'))
    if cekDokterDanJadwal['metadata']['code'] !=200:
        return validation.handleError('Dokter Tidak Ada Jadwal!')
    for i in cekDokterDanJadwal['response']:
        result = await db_manager.listantrianbelumdiperiksa(db = db,poli = poli,dokter = i['kodedokter'])
        pasiendilayani = await db_manager.listantriandiperiksa(db=db,poli=poli,dokter=i['kodedokter'])
        pasien = []
        for j in result:
            pasien.append({
                    'nourut':j[12],
                    'nomorantrian':j[12],
                    'nama':j[22],
                    'norm':j[5]
            })
        if result is not None:
            res.append({
                'dokter':i['namadokter'],
                'poli':i['namasubspesialis'],
                'pasiendilayani':{
                    'nourut':pasiendilayani[12] if pasiendilayani is not None else '',
                    'nomorantrian':pasiendilayani[12] if pasiendilayani is not None else '',
                    'nama':pasiendilayani[22] if pasiendilayani is not None else '',
                    'norm':pasiendilayani[5] if pasiendilayani is not None else ''
                },
                'pasien':pasien
            })
        

    # print(cekDokterDanJadwal['response'])

    return res


@adminantrian.get('/dashboardantrian/multi/{polies}')
async def dashboardantrian_multi(polies: str, db: Session = Depends(get_db)):
    """
    Dashboard multi poli dengan format polies: "POLI1,POLI2,POLI3" max 5 poli
    """
    res = []
    from datetime import timezone, timedelta

    # Set the timezone to Asia/Jakarta
    jakarta_timezone = timezone(timedelta(hours=7))  # UTC+7

    # Parse poli list from comma separated string
    poli_list = [poli.strip() for poli in polies.split(',')][:5]  # Max 5 poli

    if not poli_list:
        return validation.handleError('Format poli tidak valid')

    # Data untuk menentukan grid besar (pemanggilan terakhir)
    latest_call_time = None
    latest_call_poli = None
    latest_call_doctor = None

    for poli in poli_list:
        print(f"Processing poli: {poli}")

        # ambil dokter yang ada di antrian saat ini untuk poli ini
        cekDokterDanJadwal = service.cekjadwaldokter(poli, (datetime.datetime.today()).strftime('%Y-%m-%d'))
        if cekDokterDanJadwal['metadata']['code'] != 200:
            # Skip poli yang tidak ada dokter jadwal
            continue

        for i in cekDokterDanJadwal['response']:
            result = await db_manager.listantrianbelumdiperiksa(db=db, poli=poli, dokter=i['kodedokter'])
            pasiendilayani = await db_manager.listantriandiperiksa(db=db, poli=poli, dokter=i['kodedokter'])

            pasien = []
            for j in result:
                pasien.append({
                    'nourut': j[12],
                    'nomorantrian': j[12],
                    'nama': j[22],
                    'norm': j[5]
                })

            # Cek waktu panggil terakhir untuk menentukan grid besar
            if pasiendilayani and len(pasiendilayani) > 13:  # Pastikan ada waktu_panggil
                current_call_time = pasiendilayani[13]  # Asumsi waktu_panggil di index 13
                if current_call_time and (latest_call_time is None or current_call_time > latest_call_time):
                    latest_call_time = current_call_time
                    latest_call_poli = poli
                    latest_call_doctor = i['namadokter']

            if result is not None:
                doctor_data = {
                    'dokter': i['namadokter'],
                    'poli': i['namasubspesialis'],
                    'kodepoli': poli,
                    'kodedokter': i['kodedokter'],
                    'is_latest_call': False,  # Will be set later
                    'pasiendilayani': {
                        'nourut': pasiendilayani[12] if pasiendilayani is not None else '',
                        'nomorantrian': pasiendilayani[12] if pasiendilayani is not None else '',
                        'nama': pasiendilayani[22] if pasiendilayani is not None else '',
                        'norm': pasiendilayani[5] if pasiendilayani is not None else '',
                        'waktu_panggil': pasiendilayani[13] if pasiendilayani is not None and len(pasiendilayani) > 13 else None
                    },
                    'pasien': pasien,
                    'total_antrian': len(pasien) + (1 if pasiendilayani else 0)
                }
                res.append(doctor_data)

    # Set flag untuk grid terbesar (pemanggilan terakhir)
    if latest_call_poli and latest_call_doctor:
        for doctor in res:
            if doctor['poli'] == latest_call_poli or doctor['dokter'] == latest_call_doctor:
                doctor['is_latest_call'] = True
                break

    return res


@adminantrian.post('/pasienbarunew')
async def pasienbaru(payload:models.Pasienbarunew,db: Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):

    if not validation.checkVariableKosong(payload.nomorkartu):
        return validation.handleError('Nomor Kartu Belum Diisi')

    # validasi jika nomor kartu == 13 dan validasi jika nomor kartu numeric semua
    if not validation.isVariableIsXDigits(payload.nomorkartu,13) or not validation.isFullOfInteger(payload.nomorkartu):
        return validation.handleError('Format Nomor Kartu Tidak Sesuai')
    
    if not validation.checkVariableKosong(payload.nama):
        return validation.handleError('Nama Belum Diisi')

    # ini untuk uat mobile jkn di off kan
    checkExist = await db_manager_ekamek.checkPasienExist(db_ekamek,payload.nomorkartu)
    if checkExist:
        return {
        'response':{
            'norm':f'{checkExist[0]}'
        },
        'metadata':{
            'message':'Harap datang ke admisi untuk melengkapi data rekam medis',
            'code':200
        }
    }

    # sampe sini

    insert = await db_manager_ekamek.insertpasienbarunew(db = db_ekamek,payload = payload)
    if not insert:
        return validation.handleError("Terjadi kesalahan pada sistem, silahkan dicoba lagi")

    # handling daftar antrian poli
    
    return {
        'response':{
            'norm':f'{insert}'
        },
        'metadata':{
            'message':'Harap datang ke admisi untuk melengkapi data rekam medis',
            'code':200
        }
    }


@adminantrian.post('/pasienbarunewnonjkn')
async def pasienbaru(payload:models.Pasienbarunew,db: Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):

    if not validation.checkVariableKosong(payload.nomorkartu):
        return validation.handleError('Nomor Kartu Belum Diisi')

    
    if not validation.checkVariableKosong(payload.nama):
        return validation.handleError('Nama Belum Diisi')

    # ini untuk uat mobile jkn di off kan
    checkExist = await db_manager_ekamek.checkPasienExistNik(db_ekamek,payload.nomorkartu)
    if checkExist:
        return {
        'response':{
            'norm':f'{checkExist[0]}'
        },
        'metadata':{
            'message':'Harap datang ke admisi untuk melengkapi data rekam medis',
            'code':200
        }
    }

    # sampe sini

    insert = await db_manager_ekamek.insertpasienbarunewnonjkn(db = db_ekamek,payload = payload)
    if not insert:
        return validation.handleError("Terjadi kesalahan pada sistem, silahkan dicoba lagi")

    # handling daftar antrian poli
    
    return {
        'response':{
            'norm':f'{insert}'
        },
        'metadata':{
            'message':'Harap datang ke admisi untuk melengkapi data rekam medis',
            'code':200
        }
    }



@adminantrian.post('/checkinantrian')
async def checkinantrian(payload:models.ChekinAntrian,x_token: Union[str, None] = Header(default=None),x_username: Union[str, None] = Header(default=None),db: Session = Depends(get_db),db_ekamek: SessionEkamek = Depends(get_db_ekamek)):
    get = await db_manager.caridkodebookingdancheckin(db= db,payload = payload) 
    await db_manager_ekamek.tambahhistoryantrian(db=db_ekamek,payload=payload)
    return get



@adminantrian.get('/v2/antrianfarmasi/{kodebooking}')
async def antrianfarmasi(
    kodebooking:str,
    db: Session = Depends(get_db),
    db_ekamek: SessionEkamek = Depends(get_db_ekamek)
):
    # Insert antrian admisi
    # await db_manager_ekamek.tambahhistoryantriandirectfarmasi(db=db_ekamek,kodebooking=kodebooking)

    # today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    insert = await db_manager_ekamek.getnoantrianfarmasi(db=db_ekamek,kodebooking=kodebooking)
    # Jika insert gagal
    # if not insert:
    #     return validation.handleError("Terjadi kesalahan pada sistem, silahkan coba lagi")

    # Response jika berhasil insert
    return {
        'response': {
            'noantrian': insert  # Akses nomor antrian dari hasil insert
        },
        'metadata': {
            'message': 'Harap datang ke admisi untuk melengkapi data rekam medis',
            'code': 200
        }
    }

@adminantrian.get('/v2/antrianadmisi')
async def antrianadmisi(
    db: Session = Depends(get_db),
    db_ekamek: SessionEkamek = Depends(get_db_ekamek)
):
    # Insert antrian admisi
    insert = await db_manager.insertantrianadmisi(db=db)
    
    # Jika insert gagal
    if not insert:
        return validation.handleError("Terjadi kesalahan pada sistem, silahkan coba lagi")

    # Response jika berhasil insert
    return {
        'response': {
            'noantrian': insert.no_antrian  # Akses nomor antrian dari hasil insert
        },
        'metadata': {
            'message': 'Harap datang ke admisi untuk melengkapi data rekam medis',
            'code': 200
        }
    }

import app.api.database.generate as generate
from sqlalchemy import asc
@adminantrian.get('/v2/getantrianadmisi')
async def antrianadmisi(
    db: Session = Depends(get_db),
    db_ekamek: SessionEkamek = Depends(get_db_ekamek)
):
     # Ambil tanggal hari ini
    today = datetime.date.today()

    # Query untuk mengambil semua antrean berdasarkan tanggal hari ini
    # Mengecualikan antrian yang dibatalkan (flag != '3') dan yang sudah dilayani (status != 'telah_dilayani')
    antrian_list = db.query(generate.AntrianAdmisi)\
                     .filter(generate.AntrianAdmisi.tgl_kunjungan == today)\
                     .filter(generate.AntrianAdmisi.flag != '3')\
                     .filter(generate.AntrianAdmisi.status != 'telah_dilayani')\
                     .order_by(asc(generate.AntrianAdmisi.no_antrian))\
                     .all()

    # Jika tidak ada data antrean
    if not antrian_list:
        return validation.handleError("Tidak ada antrean untuk hari ini")

    # Membuat response list dari hasil query
    response = []
    for antrian in antrian_list:
        response.append({
            'id': antrian.id,
            'no_antrian': antrian.no_antrian,
            'tgl_kunjungan': antrian.tgl_kunjungan,
            'flag': antrian.flag,
            'loket': antrian.loket,
            'status': antrian.status,  # Kolom status yang sudah ditambahkan
            'waktu_panggil': antrian.waktu_panggil  # Kolom waktu panggil
        })

    # Response jika berhasil mendapatkan data antrean
    return {
        'response': response,
        'metadata': {
            'message': f'Ditemukan {len(antrian_list)} antrean untuk hari ini',
            'code': 200
        }
    }



@adminantrian.get('/v2/updateflagantrian/{antrian_id}/{flag}/{loket}')
async def update_flag_antrian(
    antrian_id: int,
    flag: str,
    loket: str,
    db: Session = Depends(get_db)
):
    # Cari antrean berdasarkan ID
    antrian = db.query(generate.AntrianAdmisi).filter(generate.AntrianAdmisi.id == antrian_id).first()

    # Jika antrean tidak ditemukan
    if not antrian:
        raise HTTPException(status_code=404, detail="Antrean tidak ditemukan")

    # Perbarui nilai flag
    antrian.flag = flag
    antrian.loket = loket if loket != '0' else antrian.loket

    # Commit perubahan ke database
    db.commit()

    # Refresh data untuk memastikan pembaruan diterapkan
    db.refresh(antrian)

    # Response setelah update berhasil
    return {
        'response': {
            'id': antrian.id,
            'no_antrian': antrian.no_antrian,
            'tgl_kunjungan': antrian.tgl_kunjungan,
            'flag': antrian.flag,
            'loket': antrian.loket
        },
        'metadata': {
            'message': 'Flag antrean berhasil diperbarui',
            'code': 200
        }
    }



from datetime import date
from fastapi import Query

@adminantrian.get('/taskid')
async def gettaskid(
    tanggalawal: str = Query(None, description="Tanggal awal dalam format YYYY-MM-DD"),
    tanggalakhir: str = Query(None, description="Tanggal akhir dalam format YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    # Jika tidak diisi, gunakan tanggal hari ini
    if not tanggalawal:
        tanggalawal = date.today().strftime('%Y-%m-%d')
    if not tanggalakhir:
        tanggalakhir = date.today().strftime('%Y-%m-%d')
    
    # Contoh query SQL untuk mengambil data berdasarkan tanggal di kolom 'created'
    query = (
        "SELECT t.*, a.nama FROM taskid t "
        "JOIN antrian_poli a ON t.kodebooking = a.kodebooking "
        f"WHERE t.created::date BETWEEN '{tanggalawal}' AND '{tanggalakhir}'"
    )

    result = db.execute(query).fetchall()

    return {
        'metadata': {
            'code': 200,
            'message': 'Ok'
        },
        'response': [dict(row) for row in result]
    }


# async def handlingjkn(payload:models.Pasienbarunew,db: Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):
#     # cek pasien dari db ekamek
#     norm = 0
#     cekPasien = await db_manager_ekamek.caridatapasien(payload.nomorkartu)
    
#     if not cekPasien: # tandanya pasien gaada
#         return {
#                 'metaData' :{
#                     'message': 'Data pasien ini tidak ditemukan, silahkan Melakukan Registrasi Pasien Baru',
#                     'code':202
#                 }
#             }

#     else:
#         norm = cekPasien[2]
#         namaPasien = cekPasien[1]
#     tanggalperiksa = datetime.datetime.now().strftime('%Y-%m-%d')
#     checkExist = await db_manager.checkAntrianExistNoRm(db,cekPasien[0],tanggalperiksa)
#     if checkExist:
#         return validation.handleErrorAdmin('Nomor Antrean Hanya Dapat Diambil 1 Kali Pada Tanggal Yang Sama')
    
#     cekPoli = await db_manager_ekamek.carinamapoli(db_ekamek,payload.kodepoli)
#     if not cekPoli:
#         return validation.handleErrorAdmin('Poli Tidak Ditemukan')

#     cekDokterDanJadwal = service.cekjadwaldokter(payload.kodepoli,payload.tanggalperiksa)
#     if not cekDokterDanJadwal:
#         return validation.handleErrorAdmin('Koneksi dengan WS BPJS Antrian Cek Jadwal Dokter Gagal!')
    
#     if cekDokterDanJadwal['metadata']['code'] != 200:
#         return validation.handleErrorAdmin(cekDokterDanJadwal['metadata']['message'])
    
#     resultJadwalDokter = {}
#     for val in cekDokterDanJadwal['response']:
#         print(val)
#         if val['kodedokter'] == int(payload.kodedokter):
#             resultJadwalDokter = val

#     if resultJadwalDokter == {}:
#         # return validation.handleErrorAdmin('Jadwal Dokter Tidak Ditemukan Pada Tanggal Tersebut!')
#         return validation.handleErrorAdmin(f"Jadwal Dokter Tersebut Belum Tersedia,Silahkan Reschedule Tanggal dan Jam Praktek Lainnya")



#     cekDokter = await db_manager_ekamek.carinamadokter(db_ekamek,payload.kodedokter)
#     if not cekDokter:
#         return validation.handleErrorAdmin('Kode Dokter Tidak sesuai')

#     payload.namadokter = resultJadwalDokter['namadokter']
#     payload.namapoli = resultJadwalDokter['namasubspesialis']
#     payload.nama = namaPasien

#     cekTotalAntrian = await db_manager.cekTotalAntrian(db=db,kodehfis = payload.kodedokter,pertgl=payload.tanggalperiksa)
#     # estimasi waktu dilayani
#     totalAntrian = int(cekTotalAntrian['count'])
#     if totalAntrian == 0:
#         totalAntrian = 1
#     waktuTotalAntrian = (1 if totalAntrian == 0 else totalAntrian) * 10 # (satu pelayanan itu 10 menit)
#     strWaktuPelayananMulai = payload.tanggalperiksa + ' 08:00:00'
#     waktuPelayananMulai = datetime.datetime.strptime(strWaktuPelayananMulai, '%Y-%m-%d %H:%M:%S')

#     validasiPeriksaHariIni = validation.validasiHariIni(payload.tanggalperiksa)
#     if validasiPeriksaHariIni:
#         splitJadwalJamMulaiSelesai = validation.validasiJadwalMelebihiJam(payload.jampraktek)
#         if not splitJadwalJamMulaiSelesai:
#             return validation.handleErrorAdmin(f"Pendaftaran Ke Poli ({resultJadwalDokter['namasubspesialis']}) Sudah Tutup Jam {payload.jampraktek.split('-')[1]}")

#         # added feature
#         # cek jika pasien mendaftar selama pelayanan berlangsung ( misal jam 08.00 waktu mulai)
#         # dan pasien mendaftar di jam 09:00 maka waktu kira kira dilayani di jam 09: ditambah dengan menit total
#         # antrian yang akan dilayani
#         # if()
#         # jakarta_timezone = pytz.timezone('Asia/Jakarta')
#         now = datetime.datetime.now()
#         dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
#         dt_string = datetime.datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
#         # print(dt_string)
#         # print('-----ini-----')
        
#         # jika pasien masuuuk melebih jam praktek maka lanjutkan jam praktek + count berapa tersisa antrian
#         if dt_string>waktuPelayananMulai:
#             waktuPelayananMulai = dt_string
#         # end added
    
#     estimasidilayani = waktuPelayananMulai + datetime.timedelta(minutes = waktuTotalAntrian)
#     estimasidilayani = round(int(estimasidilayani.timestamp()) * 1000)
#     payload.estimasidilayani = estimasidilayani
#     payload.sisakuotajkn = int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian)
#     payload.kuotajkn = int(resultJadwalDokter['kapasitaspasien'])
#     payload.sisakuotanonjkn = int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian)
#     payload.kuotanonjkn = int(resultJadwalDokter['kapasitaspasien'])

#     try:
#         # Attempt to convert the date string to a datetime object
#         tanggalperiksa_date = datetime.datetime.strptime(payload.tanggalperiksa, '%Y-%m-%d')
#     except ValueError:
#         # Handle the case where the date string is not a valid date
#         return validation.handleErrorAdmin("Tanggal Periksa Tidak Valid")
#         # Handle this error as appropriate for your application


#     insert = await db_manager.insert_antrian_poli(db= db,payload = payload)
#     if isinstance(insert, dict):
#         return insert

#     return {
#         'response':{
#             'nomorantrean':insert.nomorantrian, #2 digit nama poli didepan + max dari antrian per poli per dokter + 1 
#             'angkaantrean':insert.angkaantrean, #max dari antrian per poli per dokter + 1 
#             'kodebooking':insert.kodebooking, #nomr + angkaantrean 
#             'namapoli':resultJadwalDokter['namasubspesialis'], #nm_poli <- poliklinik
#             'norm': norm, #nomr
#             'namadokter': resultJadwalDokter['namadokter'], #nm_dokter <- data_dokter
#             'estimasidilayani':estimasidilayani, # timestamp epoch tanggal_periksa: jam pelayanan awal  + (jumlah pasien * 15 menit)
#             'sisakuotajkn': int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian), #50 - jml antrian bpjs poli 
#             'kuotajkn':int(resultJadwalDokter['kapasitaspasien']), #nomr
#             'sisakuotanonjkn':int(resultJadwalDokter['kapasitaspasien']) - int(totalAntrian), #50 - jml antrian non bpjs poli 
#             'kuotanonjkn':int(resultJadwalDokter['kapasitaspasien']), #nomr
#             'keterangan':'', #nomr
            
#         },
#         'metaData': {
#             'message':'Ok',
#             'code':200
#         }
#     }

@adminantrian.post('/v2/panggilantrian')
async def panggilantrian(payload: models.PanggilAntrian, db: Session = Depends(get_db)):
    """
    Endpoint untuk memanggil antrian dengan informasi loket
    """
    try:
        # Update data antrian dengan loket dan status dipanggil
        updated = await db_manager.update_antrian_loket(
            db=db,
            antrian_id=payload.id,
            loket=payload.loket,
            status=payload.status
        )

        if updated > 0:
            return {
                'metadata': {
                    'code': 200,
                    'message': 'Antrian berhasil dipanggil'
                },
                'response': {
                    'id': payload.id,
                    'loket': payload.loket,
                    'no_antrian': payload.no_antrian,
                    'status': payload.status
                }
            }
        else:
            return {
                'metadata': {
                    'code': 400,
                    'message': 'Gagal memperbarui data antrian'
                }
            }

    except Exception as e:
        return {
            'metadata': {
                'code': 500,
                'message': f'Terjadi kesalahan: {str(e)}'
            }
        }

@adminantrian.post('/v2/updatestatus')
async def updatestatus(payload: models.UpdateStatusAntrian, db: Session = Depends(get_db)):
    """
    Endpoint untuk mengupdate status antrian (processed, completed)
    """
    try:
        # Update status antrian
        updated = await db_manager.update_status_antrian(
            db=db,
            antrian_id=payload.id,
            status=payload.status
        )

        if updated > 0:
            return {
                'metadata': {
                    'code': 200,
                    'message': 'Status antrian berhasil diupdate'
                },
                'response': {
                    'id': payload.id,
                    'status': payload.status
                }
            }
        else:
            return {
                'metadata': {
                    'code': 400,
                    'message': 'Gagal mengupdate status antrian'
                }
            }

    except Exception as e:
        return {
            'metadata': {
                'code': 500,
                'message': f'Terjadi kesalahan: {str(e)}'
            }
        }

@adminantrian.post('/v2/hapusantrian')
async def hapusantrian(payload: models.HapusAntrian, db: Session = Depends(get_db)):
    """
    Endpoint untuk menghapus antrian dari database
    """
    try:
        # Hapus antrian
        deleted = await db_manager.hapus_antrian(
            db=db,
            antrian_id=payload.id
        )

        if deleted > 0:
            return {
                'metadata': {
                    'code': 200,
                    'message': 'Antrian berhasil dihapus'
                },
                'response': {
                    'id': payload.id
                }
            }
        else:
            return {
                'metadata': {
                    'code': 400,
                    'message': 'Gagal menghapus antrian atau antrian tidak ditemukan'
                }
            }

    except Exception as e:
        return {
            'metadata': {
                'code': 500,
                'message': f'Terjadi kesalahan: {str(e)}'
            }
        }

