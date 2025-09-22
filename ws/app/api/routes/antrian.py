from typing import List,Union
from fastapi import Header,APIRouter,HTTPException,Depends,Request
import app.api.validation.validation as validation
import app.api.models.models as models
import app.api.database.db_manager as db_manager
import app.api.validation.auth_handler as auth_handler
import app.api.controller.service as service
from sqlalchemy.orm import Session
from app.api.database.db import engine,Session
from app.api.controller import bpjs,bpjs_vclaim

import pytz
from datetime import timedelta
import datetime
from fastapi.exceptions import RequestValidationError

# for db_ekamek
from app.api.database import db_manager_ekamek
from app.api.database.db_ekamek import engine as engineEkamek,Session as SessionEkamek
from fastapi.responses import HTMLResponse

antrian = APIRouter()
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


@antrian.get('/token')
async def index(x_username: Union[str, None] = Header(default=None),x_password: Union[str, None] = Header(default=None),db: Session = Depends(get_db)):
    auth =  await db_manager.get_auth(db = db,username= x_username,password=x_password)
    if auth:
        return auth_handler.signJWT(x_username)

    return validation.handleError('Username/Password Tidak Valid')


@antrian.post('/statusantrian')
async def statusantrian(payload : models.Statusantrian,x_token: Union[str, None] = Header(default=None),x_username: Union[str, None] = Header(default=None),db:Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):
    auth = auth_handler.decodeJWT(x_token,x_username)
    if auth['message'] != 'OK':
        return validation.handleError(auth['message'])
    
    cekPoli = await db_manager_ekamek.carinamapoli(db_ekamek,payload.kodepoli)
    if not cekPoli:
        # return validation.handleError('Pendaftaran Ke Poli Ini Sedang Tutup')
        return validation.handleError('Poli tidak ditemukan')
    
    cekTgl = validation.validasiTgl(payload.tanggalperiksa)
    if not cekTgl:
        return validation.handleError('Format Tanggal Tidak Sesuai, format yang benar adalah yyyy-mm-dd')

    cekTglBackdate = validation.validasiBackDate(payload.tanggalperiksa)
    if not cekTglBackdate:
        return validation.handleError('Tanggal Periksa Tidak Berlaku')

    cekDokter = await db_manager_ekamek.carinamadokter(db_ekamek,payload.kodedokter)
    if not cekDokter:
        return validation.handleError('Kode Dokter Tidak sesuai')

    cekDokterDanJadwal = service.cekjadwaldokter(payload.kodepoli,payload.tanggalperiksa)
    print(cekDokterDanJadwal)
    if not cekDokterDanJadwal:
        return validation.handleError('Koneksi dengan WS BPJS Antrian Cek Jadwal Dokter Gagal!')
    if cekDokterDanJadwal['metadata']['code'] != 200:
        return validation.handleError('Poli tidak ditemukan')
    
    resultJadwalDokter = {}
    for val in cekDokterDanJadwal['response']:
        if val['kodedokter'] == payload.kodedokter:
            resultJadwalDokter = val

    if resultJadwalDokter == {}:
        return validation.handleError('Jadwal Dokter Tidak Ditemukan Pada Tanggal Tersebut!')

        # disini cek jadwal dokter dari db
        # cekJadwalDokterMappingDB = await db_manager.getJadwalDokterPerPoliPerDokterPerHari(db = db,tanggal=payload.tanggalperiksa,poli=payload.kodepoli,kodedokter=payload.kodedokter)
        # if cekJadwalDokterMappingDB['message'] == 'tgl':
        #     return validation.handleError('Format Tanggal Tidak Sesuai, format yang benar adalah yyyy-mm-dd')
        # if cekJadwalDokterMappingDB['message'] == 'null':
        #     return validation.handleError('Jadwal Dokter Tidak Ditemukan Pada Tanggal Tersebut!')
        # resultJadwalDokter = cekJadwalDokterMappingDB

    # print(resultJadwalDokter)


    # response from jadwal dokter
    # {
    #   "kodesubspesialis": "084",
    #   "hari": 3,
    #   "kapasitaspasien": 24,
    #   "libur": 0,
    #   "namahari": "RABU",
    #   "jadwal": "08:00-12:00",
    #   "namasubspesialis": "Neurobehaviour, MD, Neurogeriatri, dan Neurorestorasi",
    #   "namadokter": "Tenaga Medis 18154",
    #   "kodepoli": "SAR",
    #   "namapoli": "SARAF",
    #   "kodedokter": 18154
    # }

     # cek jika ada kondisi
    result = await db_manager.cekstatusantrian(db = db,payload = payload,kapasitas_pasien = resultJadwalDokter['kapasitaspasien'])
    # cek jika data ada . maka 
    if result :
        return {
            'metadata':{
                'code':200,
                'message':'Ok'
            },
            'response':{
                'namapoli':result['namapoli'],
                'namadokter':result['namadokter'],
                'totalantrean':result['totalantrean'],
                'sisaantrean':result['sisaantrian'],
                'antreanpanggil':'' if result['antreanpanggil'] is None else result['antreanpanggil'],
                'sisakuotajkn':int(resultJadwalDokter['kapasitaspasien']) - int(result['totalantrean']),
                'kuotajkn':resultJadwalDokter['kapasitaspasien'],
                'sisakuotanonjkn':int(resultJadwalDokter['kapasitaspasien']) - int(result['totalantrean']),
                'kuotanonjkn':resultJadwalDokter['kapasitaspasien'],
                'keterangan':""
            }
        } 
    

    return {
        'metadata':{
            'code':200,
            'message':'Ok'
        },
        'response':{
            'namapoli':resultJadwalDokter['namasubspesialis'],
            'namadokter':resultJadwalDokter['namadokter'],
            'totalantrean':0,
            'sisaantrean':resultJadwalDokter['kapasitaspasien'],
            'antreanpanggil':'',
            'sisakuotajkn':resultJadwalDokter['kapasitaspasien'],
            'kuotajkn':resultJadwalDokter['kapasitaspasien'],
            'sisakuotanonjkn':resultJadwalDokter['kapasitaspasien'],
            'kuotanonjkn':resultJadwalDokter['kapasitaspasien'],
            'keterangan':""
        }
    }
        

@antrian.post('/ambilantrian_old')
async def ambilantrian(payload:models.Ambilantrian,x_token: Union[str, None] = Header(default=None),x_username: Union[str, None] = Header(default=None),db: Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):
    auth = auth_handler.decodeJWT(x_token,x_username)
    if auth['message'] != 'OK':
        return validation.handleError(auth['message'])

    # cek pasien dari db ekamek
    norm = 0
    cekPasien = await db_manager_ekamek.caridatapasien(db_ekamek,payload.nomorkartu)
    if not cekPasien: # tandanya pasien gaada
        # cek di pasien baru daftar di antrol
        cekPasienBaru = await db_manager.cekPasienBaruExist(db = db,nomorkartu = payload.nomorkartu,norm = payload.norm)
        if not cekPasienBaru:
            return {
                'metadata' :{
                    'message': 'Data pasien ini tidak ditemukan, silahkan Melakukan Registrasi Pasien Baru',
                    'code':202
                }
            } 
        else:
            namaPasien = cekPasienBaru.nama   
            norm = cekPasienBaru.norm
            payload.pasienbaru = '1'
    else:
        namaPasien = cekPasien[1]
        norm = cekPasien[2]

    cekTgl = validation.validasiTgl(payload.tanggalperiksa)
    if not cekTgl:
        return validation.handleError('Format Tanggal Tidak Sesuai, format yang benar adalah yyyy-mm-dd')

    cekTglBackdate = validation.validasiBackDate(payload.tanggalperiksa)
    if not cekTglBackdate:
        return validation.handleError('Tanggal Periksa Tidak Berlaku')

    # check pernah daftar atau belum jika pernah maka bukan pasien baru
    cekPasienBarulama = await db_manager.cekPasienbarulama(db= db,nomorkartu = payload.nomorkartu)
    if not cekPasienBarulama:
        payload.pasienbaru = '1'
        
    checkExist = await db_manager.checkAntrianExist(db,payload.nomorkartu,payload.tanggalperiksa)
    if checkExist:
        return validation.handleError('Nomor Antrean Hanya Dapat Diambil 1 Kali Pada Tanggal Yang Sama')
    
    # checkReferensiExist = await db_manager.checkReferensiExist(db,payload.nomorreferensi)
    # if checkReferensiExist:
    #     return validation.handleError('Nomor Referensi Sudah Ada.')

    cekPoli = await db_manager_ekamek.carinamapoli(db_ekamek,payload.kodepoli)
    if not cekPoli:
        return validation.handleError('Poli Tidak Ditemukan')

    cekDokterDanJadwal = service.cekjadwaldokter(payload.kodepoli,payload.tanggalperiksa)
    if not cekDokterDanJadwal:
        return validation.handleError('Koneksi dengan WS BPJS Antrian Cek Jadwal Dokter Gagal!')
    
    if cekDokterDanJadwal['metadata']['code'] != 200:
        return validation.handleError(cekDokterDanJadwal['metadata']['message'])
    
    resultJadwalDokter = {}
    for val in cekDokterDanJadwal['response']:
        print(val)
        if val['kodedokter'] == int(payload.kodedokter):
            resultJadwalDokter = val

    if resultJadwalDokter == {}:
        # return validation.handleError('Jadwal Dokter Tidak Ditemukan Pada Tanggal Tersebut!')
        return validation.handleError(f"Jadwal Dokter Tersebut Belum Tersedia,Silahkan Reschedule Tanggal dan Jam Praktek Lainnya")



    cekDokter = await db_manager_ekamek.carinamadokter(db_ekamek,payload.kodedokter)
    if not cekDokter:
        return validation.handleError('Kode Dokter Tidak sesuai')

    payload.namadokter = resultJadwalDokter['namadokter']
    payload.namapoli = resultJadwalDokter['namasubspesialis']
    payload.nama = namaPasien

    cekTotalAntrian = await db_manager.cekTotalAntrian(db=db,kodehfis = payload.kodedokter,pertgl=payload.tanggalperiksa)
    # estimasi waktu dilayani
    totalAntrian = int(cekTotalAntrian['count']) + 1
    if totalAntrian == 0:
        totalAntrian = 1
    waktuTotalAntrian = (1 if totalAntrian == 0 else totalAntrian) * 10 # (satu pelayanan itu 10 menit)
    strWaktuPelayananMulai = payload.tanggalperiksa + ' '+ payload.jampraktek.split('-')[0] + ':00'
    waktuPelayananMulai = datetime.datetime.strptime(strWaktuPelayananMulai, '%Y-%m-%d %H:%M:%S')
    

    validasiPeriksaHariIni = validation.validasiHariIni(payload.tanggalperiksa)
    if validasiPeriksaHariIni:
        splitJadwalJamMulaiSelesai = validation.validasiJadwalMelebihiJam(payload.jampraktek)
        if not splitJadwalJamMulaiSelesai:
            return validation.handleError(f"Pendaftaran Ke Poli ({resultJadwalDokter['namasubspesialis']}) Sudah Tutup Jam {payload.jampraktek.split('-')[1]}")


        # added feature
        # cek jika pasien mendaftar selama pelayanan berlangsung ( misal jam 08.00 waktu mulai)
        # dan pasien mendaftar di jam 09:00 maka waktu kira kira dilayani di jam 09: ditambah dengan menit total
        # antrian yang akan dilayani
        # if()
        # jakarta_timezone = pytz.timezone('Asia/Jakarta')
        now = datetime.datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        dt_string = datetime.datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
        print(dt_string)
        print('-----ini-----')
        
        # jika pasien masuuuk melebih jam praktek maka lanjutkan jam praktek + count berapa tersisa antrian
        if dt_string>waktuPelayananMulai:
            waktuPelayananMulai = dt_string
        # end added

    estimasidilayani = waktuPelayananMulai + datetime.timedelta(minutes = waktuTotalAntrian)
    # estimasidilayani = int(estimasidilayani.timestamp())
    estimasidilayani = round(int(estimasidilayani.timestamp()) * 1000)
    # print(type(estimasidilayani))
    # return {'maintenance'}
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
        return validation.handleError("Tanggal Periksa Tidak Valid")
        # Handle this error as appropriate for your application

    # noantrians = await db_manager_ekamek.nomorantrian(db_ekamek,cekPoli[0],payload.tanggalperiksa,cekDokter[1])
    
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
    
    insert = await db_manager.insert_antrian_poli(db= db,payload = payload,noantrian=noantrians[0])
    if isinstance(insert, dict):
        return insert


    # tambahkan ke poli
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

    # return reqdata
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
        'metadata': {
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


@antrian.post('/sisaantrian')
async def sisaantrian(payload:models.Sisaantrian,x_token: Union[str, None] = Header(default=None),x_username: Union[str, None] = Header(default=None),db: Session = Depends(get_db)):
    auth = auth_handler.decodeJWT(x_token,x_username)
    if auth['message'] != 'OK':
        return validation.handleError(auth['message'])

    get = await db_manager.ceksisaantrian(db = db,payload= payload)
    if get is None : 
        return validation.handleError("Antrean Tidak Ditemukan")
    return {
        'response':{
            'nomorantrean':get['nomorantrian'],
            'namapoli':get['namapoli'],
            'namadokter':get['namadokter'],
            'sisaantrean':get['sisaantrian'],
            'antreanpanggil':'-' if get['antreanpanggil'] is None else get['antreanpanggil'],
            'waktutunggu':get['waktutunggu'],
            'keterangan':""
        },
        'metadata':{
            'code':200,
            'message':'Ok'
        }
    }


@antrian.post('/batalantrian')
async def batalantrian(payload:models.BatalAntrian,x_token: Union[str, None] = Header(default=None),x_username: Union[str, None] = Header(default=None),db: Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):
    auth = auth_handler.decodeJWT(x_token,x_username)
    if auth['message'] != 'OK':
        return validation.handleError(auth['message'])

    carikodebooking = await db_manager.carikodebooking(db = db,payload = payload)
    await db_manager_ekamek.batalantrianhmis(db=db_ekamek,kodebooking=payload.kodebooking)

    if not carikodebooking:
        return validation.handleError("Antrean Tidak Ditemukan")
    
    # delete from pasienbaru
    # deletepasienbaru = await db_manager.deletepasienbaru(db= db,norm = carikodebooking['norm'])

    if carikodebooking['flag'] is not None:
        if carikodebooking['flag'] == '99':
            return validation.handleError('Antrean Tidak Ditemukan atau Sudah Dibatalkan')
        return validation.handleError('Pasien Sudah Dilayani,Antrean Tidak Dapat Dibatalkan')

    get = await db_manager.carikodebookingdanupdate(db= db,payload = payload)
    return get



@antrian.post('/checkinantrian')
async def checkinantrian(payload:models.ChekinAntrian,x_token: Union[str, None] = Header(default=None),x_username: Union[str, None] = Header(default=None),db: Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):
    auth = auth_handler.decodeJWT(x_token,x_username)
    if auth['message'] != 'OK':
        return validation.handleError(auth['message'])

    await db_manager_ekamek.tambahhistoryantriandirect(db=db_ekamek,kodebooking=payload.kodebooking)
    get = await db_manager.caridkodebookingdancheckin(db= db,payload = payload) 
    return get
    # if get is None:
    #     return {
    #         'metadata':{
    #             'message':'Kode Booking Tidak Ditemukan',
    #             'code':201
    #         }
    #     }
    # if get>0:
    #     return {
    #         'metadata':{
    #             'message':'Ok',
    #             'code':200
    #         }
    #     }
    # return {
    #         'metadata':{
    #             'message':'Gagal',
    #             'code':201
    #         }
    #     }
    


@antrian.post('/pasienbaru')
async def pasienbaru(payload:models.Pasienbaru,x_token: Union[str, None] = Header(default=None),x_username: Union[str, None] = Header(default=None),db: Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):
    auth = auth_handler.decodeJWT(x_token,x_username)
    if auth['message'] != 'OK':
        return validation.handleError(auth['message'])


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
    # print(insert)
    return {
        'response':{
            'norm':f'{insert}'
        },
        'metadata':{
            'message':'Harap datang ke admisi untuk melengkapi data rekam medis',
            'code':200
        }
    }

@antrian.post('/ambilantreanfarmasi')
async def ambilAntreanFarmasi(payload:models.AmbilAntreanFarmasi,x_token: Union[str, None] = Header(default=None),x_username: Union[str, None] = Header(default=None),db:Session= Depends(get_db),db_ekamek: SessionEkamek = Depends(get_db_ekamek)):
    auth = auth_handler.decodeJWT(x_token,x_username)
    if auth['message'] != 'OK':
        return validation.handleError(auth['message'])

    # cek di db kodebooking ada ga 
    cekkodebooking = await db_manager.carikodebooking(db=db,payload=models.BatalAntrian(**{'kodebooking':payload.kodebooking,'keterangan':''}))
    if cekkodebooking is None:
        return validation.handleError('Kode Booking tidak ditemukan')
    if cekkodebooking[-6] == '99':
        return validation.handleError('Kode Booking tidak ditemukan')

    # grab farmasi tipe racikan / tidak 
    jenisfarmasi = await db_manager_ekamek.grab_antrian_farmasi(db = db_ekamek,kodebooking = payload.kodebooking)
    query = await db_manager.insert_antrian_farmasi(db = db,payload =payload,jenisfarmasi = jenisfarmasi)
    if query:
        return {
            "response": {
                "jenisresep": payload.jenisresep,
                "nomorantrean": 1 if query.nomorantrean is None else query.nomorantrean,
                "keterangan": "" if query.keterangan is None else query.keterangan
            },
            "metadata": {
                "message": "Ok",
                "code": 200
            }
        }

@antrian.post('/statusantrianfarmasi')
async def statusantrianfarmasi(payload:models.AmbilAntreanFarmasi,x_token: Union[str, None] = Header(default=None),x_username: Union[str, None] = Header(default=None),db:Session= Depends(get_db)):
    auth = auth_handler.decodeJWT(x_token,x_username)
    if auth['message'] != 'OK':
        return validation.handleError(auth['message'])
    query = await db_manager.get_status_antrian_farmasi(db = db,kodebooking=payload.kodebooking)
    if query is None:
        return validation.handleError('Kode Booking tidak ditemukan')
    return {
        "response": {
            "jenisresep": query[0],
            "totalantrean": query[1],
            "sisaantrean": query[2],
            "antreanpanggil": 0 if query[3] is None else query[3] ,
            "keterangan": '' if query[4] is None else query[4]
        },
        "metadata": {
            "message": "Ok",
            "code": 200
        }
    }
    


@antrian.post('/jadwaloperasirs')
async def jadwaloperasirs(payload:models.Jadwaloperasirs,x_token: Union[str, None] = Header(default=None),x_username: Union[str, None] = Header(default=None),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):
    auth = auth_handler.decodeJWT(x_token,x_username)
    if auth['message'] != 'OK':
        return validation.handleError(auth['message'])

    # validasi tgl akhir tidak boleh lebih kecil dari tanggal awal
    # try:
    tglawal = datetime.datetime.strptime(payload.tanggalawal, '%Y-%m-%d').strftime('%Y-%m-%d')
    tglakhir = datetime.datetime.strptime(payload.tanggalakhir, '%Y-%m-%d').strftime('%Y-%m-%d')
    if tglakhir < tglawal:
        return validation.handleError('Tanggal Akhir Tidak Boleh Lebih Kecil dari Tanggal Awal')
    cek = await db_manager_ekamek.jadwaloperasirs(db_ekamek,payload.tanggalawal,payload.tanggalakhir)
    return {
        "response": cek,
        "metadata": {
            "message": "Ok",
            "code": 200
        }
    }
    
    # except:
    #     return validation.handleError('Format Tanggal Tidak Sesuai, format yang benar adalah yyyy-mm-dd')

@antrian.post('/jadwaloperasipasien')
async def jadwaloperasipasien(payload:models.Jadwaloperasipasien,x_token: Union[str, None] = Header(default=None),x_username: Union[str, None] = Header(default=None),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):
    auth = auth_handler.decodeJWT(x_token,x_username)
    if auth['message'] != 'OK':
        return validation.handleError(auth['message'])

    if payload.nopeserta == '':
        return validation.handleError('Nomor Kartu Tidak Boleh Null')

    if len(payload.nopeserta) != 13:
        return validation.handleError('Nomor Kartu Tidak Valid')

    cek = await db_manager_ekamek.jadwaloperasirs2(db_ekamek,payload.nopeserta)
    if len(cek)>0:
        return {
            'response':cek[0],
            'metadata':{
                'code':200,
                'message':'Ok'
            }
        }
    return validation.handleError('Nomor Kartu Tidak Ditemukan')    

@antrian.post('/ambilantrian_older')
async def ambilantriandebug(payload:models.Ambilantrian,x_token: Union[str, None] = Header(default=None),x_username: Union[str, None] = Header(default=None),db: Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):
    auth = auth_handler.decodeJWT(x_token,x_username)
    if auth['message'] != 'OK':
        return validation.handleError(auth['message'])

    # cek pasien dari db ekamek
    norm = 0
    cekPasien = await db_manager_ekamek.caridatapasien(db_ekamek,payload.nomorkartu)
    if not cekPasien: # tandanya pasien gaada
        # cek di pasien baru daftar di antrol
        cekPasienBaru = await db_manager.cekPasienBaruExist(db = db,nomorkartu = payload.nomorkartu,norm = payload.norm)
        if not cekPasienBaru:
            return {
                'metadata' :{
                    'message': 'Data pasien ini tidak ditemukan, silahkan Melakukan Registrasi Pasien Baru',
                    'code':202
                }
            } 
        else:
            namaPasien = cekPasienBaru.nama   
            norm = cekPasienBaru.norm
            payload.pasienbaru = '1'
    else:
        namaPasien = cekPasien[1]
        norm = cekPasien[2]

    cekTgl = validation.validasiTgl(payload.tanggalperiksa)
    if not cekTgl:
        return validation.handleError('Format Tanggal Tidak Sesuai, format yang benar adalah yyyy-mm-dd')

    cekTglBackdate = validation.validasiBackDate(payload.tanggalperiksa)
    if not cekTglBackdate:
        return validation.handleError('Tanggal Periksa Tidak Berlaku')

    # check pernah daftar atau belum jika pernah maka bukan pasien baru
    cekPasienBarulama = await db_manager.cekPasienbarulama(db= db,nomorkartu = payload.nomorkartu)
    if not cekPasienBarulama:
        payload.pasienbaru = '1'
        
    checkExist = await db_manager.checkAntrianExist(db,payload.nomorkartu,payload.tanggalperiksa)
    if checkExist:
        return validation.handleError('Nomor Antrean Hanya Dapat Diambil 1 Kali Pada Tanggal Yang Sama')
    
    # checkReferensiExist = await db_manager.checkReferensiExist(db,payload.nomorreferensi)
    # if checkReferensiExist:
    #     return validation.handleError('Nomor Referensi Sudah Ada.')

    #  nm_dokter,id_dokter, id_poli
    cekDokter = await db_manager_ekamek.carinamadokter_new(db_ekamek,payload.kodedokter)
    if not cekDokter:
        return validation.handleError('Kode Dokter Tidak sesuai')
        
    if cekDokter[2] is None or cekDokter[2] == '':
        return validation.handleError('Kode Poli Tidak Ditemukan')

    cekPoli = [cekDokter[2]]
    if not cekPoli:
        return validation.handleError('Poli Tidak Ditemukan')

    cekDokterDanJadwal = service.cekjadwaldokter(payload.kodepoli,payload.tanggalperiksa)
    if not cekDokterDanJadwal:
        return validation.handleError('Koneksi dengan WS BPJS Antrian Cek Jadwal Dokter Gagal!')
    
    if cekDokterDanJadwal['metadata']['code'] != 200:
        return validation.handleError(cekDokterDanJadwal['metadata']['message'])
    
    # print("ASDASDASD")
    # print(cekDokterDanJadwal)
    # return {"OK"}

    resultJadwalDokter = {}
    for val in cekDokterDanJadwal['response']:
        print(val)
        if val['kodedokter'] == int(payload.kodedokter):
            resultJadwalDokter = val

    if resultJadwalDokter == {}:
        # return validation.handleError('Jadwal Dokter Tidak Ditemukan Pada Tanggal Tersebut!')
        return validation.handleError(f"Jadwal Dokter Tersebut Belum Tersedia,Silahkan Reschedule Tanggal dan Jam Praktek Lainnya")

    payload.namadokter = resultJadwalDokter['namadokter']
    payload.namapoli = resultJadwalDokter['namasubspesialis']
    payload.nama = namaPasien

    cekTotalAntrian = await db_manager.cekTotalAntrian(db=db,kodehfis = payload.kodedokter,pertgl=payload.tanggalperiksa)
    # estimasi waktu dilayani
    totalAntrian = int(cekTotalAntrian['count']) + 1
    if totalAntrian == 0:
        totalAntrian = 1
    waktuTotalAntrian = (1 if totalAntrian == 0 else totalAntrian) * 10 # (satu pelayanan itu 10 menit)
    strWaktuPelayananMulai = payload.tanggalperiksa + ' '+ payload.jampraktek.split('-')[0] + ':00'
    waktuPelayananMulai = datetime.datetime.strptime(strWaktuPelayananMulai, '%Y-%m-%d %H:%M:%S')
    

    validasiPeriksaHariIni = validation.validasiHariIni(payload.tanggalperiksa)
    if validasiPeriksaHariIni:
        splitJadwalJamMulaiSelesai = validation.validasiJadwalMelebihiJam(payload.jampraktek)
        if not splitJadwalJamMulaiSelesai:
            return validation.handleError(f"Pendaftaran Ke Poli ({resultJadwalDokter['namasubspesialis']}) Sudah Tutup Jam {payload.jampraktek.split('-')[1]}")


        # added feature
        # cek jika pasien mendaftar selama pelayanan berlangsung ( misal jam 08.00 waktu mulai)
        # dan pasien mendaftar di jam 09:00 maka waktu kira kira dilayani di jam 09: ditambah dengan menit total
        # antrian yang akan dilayani
        # if()
        # jakarta_timezone = pytz.timezone('Asia/Jakarta')
        now = datetime.datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        dt_string = datetime.datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
        print(dt_string)
        print('-----ini-----')
        
        # jika pasien masuuuk melebih jam praktek maka lanjutkan jam praktek + count berapa tersisa antrian
        if dt_string>waktuPelayananMulai:
            waktuPelayananMulai = dt_string
        # end added

    estimasidilayani = waktuPelayananMulai + datetime.timedelta(minutes = waktuTotalAntrian)
    # estimasidilayani = int(estimasidilayani.timestamp())
    estimasidilayani = round(int(estimasidilayani.timestamp()) * 1000)
    # print(type(estimasidilayani))
    # return {'maintenance'}
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
        return validation.handleError("Tanggal Periksa Tidak Valid")
        # Handle this error as appropriate for your application

    # noantrians = await db_manager_ekamek.nomorantrian(db_ekamek,cekPoli[0],payload.tanggalperiksa,cekDokter[1])
    
    # masukan kondisi disini jika poli BR00
    # cek juga jika dokter tersebut merupakan dokter diana -> BQ00
    # kalo dokter hasnur rahmi -> BR00
    polis = cekPoli[0]

    # if polis == 'BR00' and cekDokter[1] != 21:
    #     polis = 'BQ00'
    # print(cekDokter[1])
    # return False
    noantrians = await db_manager_ekamek.nomorantriandebug(db_ekamek,polis,payload.tanggalperiksa,cekDokter[1])
    # print(noantrians)
    
    insert = await db_manager.insert_antrian_poli(db= db,payload = payload,noantrian=noantrians[0])
    if isinstance(insert, dict):
        return insert


    # tambahkan ke poli
    bodyreq = {
        'nomorkartu': payload.nomorkartu,
        'kodepoli': payload.kodepoli,
        'id_poli': cekDokter[2], # id_poli <- poliklinik
        'namapoli':resultJadwalDokter['namasubspesialis'],
        'jeniskunjungan': payload.jeniskunjungan,
        'nomorreferensi':payload.nomorreferensi,
        'kodedokter':payload.kodedokter,
        'kodebooking':insert.kodebooking,
        'norm':norm,
        'tanggalperiksa':payload.tanggalperiksa,
        'noantrian':insert.angkaantrean,
    }
    # return bodyreq
    reqdata = await insert_daftar_ulang_new_jul_2025(bodyreq,db_ekamek)

    # return reqdata
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
        'metadata': {
            'message':'Ok',
            'code':200
        }
    }


@antrian.post('/ambilantrian')
async def ambilantrianv2(payload:models.Ambilantrian,x_token: Union[str, None] = Header(default=None),x_username: Union[str, None] = Header(default=None),db: Session = Depends(get_db),db_ekamek:SessionEkamek = Depends(get_db_ekamek)):
    auth = auth_handler.decodeJWT(x_token,x_username)
    if auth['message'] != 'OK':
        return validation.handleError(auth['message'])

    # cek pasien dari db ekamek
    norm = 0
    cekPasien = await db_manager_ekamek.caridatapasien(db_ekamek,payload.nomorkartu)
    if not cekPasien: # tandanya pasien gaada
        # cek di pasien baru daftar di antrol
        cekPasienBaru = await db_manager.cekPasienBaruExist(db = db,nomorkartu = payload.nomorkartu,norm = payload.norm)
        if not cekPasienBaru:
            return {
                'metadata' :{
                    'message': 'Data pasien ini tidak ditemukan, silahkan Melakukan Registrasi Pasien Baru',
                    'code':202
                }
            } 
        else:
            namaPasien = cekPasienBaru.nama   
            norm = cekPasienBaru.norm
            payload.pasienbaru = '1'
    else:
        namaPasien = cekPasien[1]
        norm = cekPasien[2]

    cekTgl = validation.validasiTgl(payload.tanggalperiksa)
    if not cekTgl:
        return validation.handleError('Format Tanggal Tidak Sesuai, format yang benar adalah yyyy-mm-dd')

    cekTglBackdate = validation.validasiBackDate(payload.tanggalperiksa)
    if not cekTglBackdate:
        return validation.handleError('Tanggal Periksa Tidak Berlaku')

    # check pernah daftar atau belum jika pernah maka bukan pasien baru
    cekPasienBarulama = await db_manager.cekPasienbarulama(db= db,nomorkartu = payload.nomorkartu)
    if not cekPasienBarulama:
        payload.pasienbaru = '1'
        
    checkExist = await db_manager.checkAntrianExist(db,payload.nomorkartu,payload.tanggalperiksa)
    if checkExist:
        return validation.handleError('Nomor Antrean Hanya Dapat Diambil 1 Kali Pada Tanggal Yang Sama')
    
    # checkReferensiExist = await db_manager.checkReferensiExist(db,payload.nomorreferensi)
    # if checkReferensiExist:
    #     return validation.handleError('Nomor Referensi Sudah Ada.')

    #  nm_dokter,id_dokter, id_poli
    cekDokter = await db_manager_ekamek.carinamadokter_new_v2(db_ekamek,payload.kodedokter,payload.kodepoli)
    if not cekDokter:
        return validation.handleError('Kode Dokter Tidak sesuai')
        
    if cekDokter[2] is None or cekDokter[2] == '':
        return validation.handleError('Kode Poli Tidak Ditemukan')

    cekPoli = [cekDokter[2]]
    if not cekPoli:
        return validation.handleError('Poli Tidak Ditemukan')

    cekDokterDanJadwal = service.cekjadwaldokter(payload.kodepoli,payload.tanggalperiksa)
    if not cekDokterDanJadwal:
        return validation.handleError('Koneksi dengan WS BPJS Antrian Cek Jadwal Dokter Gagal!')
    
    if cekDokterDanJadwal['metadata']['code'] != 200:
        return validation.handleError(cekDokterDanJadwal['metadata']['message'])
    
    # print("ASDASDASD")
    # print(cekDokterDanJadwal)
    # return {"OK"}

    resultJadwalDokter = {}
    for val in cekDokterDanJadwal['response']:
        print(val)
        if val['kodedokter'] == int(payload.kodedokter):
            resultJadwalDokter = val

    if resultJadwalDokter == {}:
        # return validation.handleError('Jadwal Dokter Tidak Ditemukan Pada Tanggal Tersebut!')
        return validation.handleError(f"Jadwal Dokter Tersebut Belum Tersedia,Silahkan Reschedule Tanggal dan Jam Praktek Lainnya")

    payload.namadokter = resultJadwalDokter['namadokter']
    payload.namapoli = resultJadwalDokter['namasubspesialis']
    payload.nama = namaPasien

    cekTotalAntrian = await db_manager.cekTotalAntrian(db=db,kodehfis = payload.kodedokter,pertgl=payload.tanggalperiksa)
    # estimasi waktu dilayani
    totalAntrian = int(cekTotalAntrian['count']) + 1
    if totalAntrian == 0:
        totalAntrian = 1
    waktuTotalAntrian = (1 if totalAntrian == 0 else totalAntrian) * 10 # (satu pelayanan itu 10 menit)
    strWaktuPelayananMulai = payload.tanggalperiksa + ' '+ payload.jampraktek.split('-')[0] + ':00'
    waktuPelayananMulai = datetime.datetime.strptime(strWaktuPelayananMulai, '%Y-%m-%d %H:%M:%S')
    

    validasiPeriksaHariIni = validation.validasiHariIni(payload.tanggalperiksa)
    if validasiPeriksaHariIni:
        splitJadwalJamMulaiSelesai = validation.validasiJadwalMelebihiJam(payload.jampraktek)
        if not splitJadwalJamMulaiSelesai:
            return validation.handleError(f"Pendaftaran Ke Poli ({resultJadwalDokter['namasubspesialis']}) Sudah Tutup Jam {payload.jampraktek.split('-')[1]}")


        # added feature
        # cek jika pasien mendaftar selama pelayanan berlangsung ( misal jam 08.00 waktu mulai)
        # dan pasien mendaftar di jam 09:00 maka waktu kira kira dilayani di jam 09: ditambah dengan menit total
        # antrian yang akan dilayani
        # if()
        # jakarta_timezone = pytz.timezone('Asia/Jakarta')
        now = datetime.datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        dt_string = datetime.datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
        print(dt_string)
        print('-----ini-----')
        
        # jika pasien masuuuk melebih jam praktek maka lanjutkan jam praktek + count berapa tersisa antrian
        if dt_string>waktuPelayananMulai:
            waktuPelayananMulai = dt_string
        # end added

    estimasidilayani = waktuPelayananMulai + datetime.timedelta(minutes = waktuTotalAntrian)
    # estimasidilayani = int(estimasidilayani.timestamp())
    estimasidilayani = round(int(estimasidilayani.timestamp()) * 1000)
    # print(type(estimasidilayani))
    # return {'maintenance'}
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
        return validation.handleError("Tanggal Periksa Tidak Valid")
        # Handle this error as appropriate for your application

    # noantrians = await db_manager_ekamek.nomorantrian(db_ekamek,cekPoli[0],payload.tanggalperiksa,cekDokter[1])
    
    # masukan kondisi disini jika poli BR00
    # cek juga jika dokter tersebut merupakan dokter diana -> BQ00
    # kalo dokter hasnur rahmi -> BR00
    polis = cekPoli[0]

    # if polis == 'BR00' and cekDokter[1] != 21:
    #     polis = 'BQ00'
    # print(cekDokter[1])
    # return False
    noantrians = await db_manager_ekamek.nomorantriandebug(db_ekamek,polis,payload.tanggalperiksa,cekDokter[1])
    # print(noantrians)
    
    insert = await db_manager.insert_antrian_poli(db= db,payload = payload,noantrian=noantrians[0])
    if isinstance(insert, dict):
        return insert


    # tambahkan ke poli
    bodyreq = {
        'nomorkartu': payload.nomorkartu,
        'kodepoli': payload.kodepoli,
        'id_poli': cekDokter[2], # id_poli <- poliklinik
        'namapoli':resultJadwalDokter['namasubspesialis'],
        'jeniskunjungan': payload.jeniskunjungan,
        'nomorreferensi':payload.nomorreferensi,
        'kodedokter':payload.kodedokter,
        'kodebooking':insert.kodebooking,
        'norm':norm,
        'tanggalperiksa':payload.tanggalperiksa,
        'noantrian':insert.angkaantrean,
    }
    # return bodyreq
    reqdata = await insert_daftar_ulang_new_jul_2025(bodyreq,db_ekamek)

    # return reqdata
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
        'metadata': {
            'message':'Ok',
            'code':200
        }
    }

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