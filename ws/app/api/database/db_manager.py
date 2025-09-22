from sqlalchemy.orm import Session
from app.api.database.db import engine,Session
import app.api.models.models as models
models.Base.metadata.create_all(bind=engine)
import app.api.database.generate as generate
import datetime
from app.api.controller import bpjs
import json

def milliseconds():
    from datetime import datetime, timezone, timedelta

    # Set the timezone to Asia/Jakarta
    jakarta_timezone = timezone(timedelta(hours=7))  # UTC+7

    # Get the current time in the specified timezone
    current_time = datetime.now(jakarta_timezone)

    # Convert to milliseconds since the epoch
    timestamp_milliseconds = int(current_time.timestamp() * 1000)
    return timestamp_milliseconds

async def get_auth(db: Session,username:str,password:str):
    query = db.execute(f"SELECT username from auth_bpjs where username = '{username}' and password='{password}'").first()
    return query


async def insert_antrian_poli_onsite_lama(db:Session,payload:models.AntrianPoliIn,noantrian:int):
    db_antrian = generate.AntrianPoli(**payload.dict())
    db.add(db_antrian)
    db.commit()
    db.refresh(db_antrian)
    print('masuk sini-----')
    print(db_antrian.kodebooking)
    print('masuk sini------')
    # nomorantrian = db_antrian.kodepoli + '-' + str(noantrian).zfill(3)
    # kodebookingbaru = '0311R001'+ db_antrian.tanggalperiksa.strftime('%Y%m%d') +db_antrian.kodepoli+str(noantrian).zfill(3)
    # db.execute(f"UPDATE antrian_poli set angkaantrean={noantrian},nomorantrian='{nomorantrian}',kodebooking = '{kodebookingbaru }'where kodebooking = '{db_antrian.kodebooking}'")
    # db.commit()
    
    # db_antrian.angkaantrean = noantrian
    # db_antrian.nomorantrian = db_antrian.kodepoli + '-' + str(noantrian).zfill(3)
    # db_antrian.kodebooking = '0311R001'+ db_antrian.tanggalperiksa.strftime('%Y%m%d') +db_antrian.kodepoli+str(noantrian).zfill(3) 

    # disini daftar kan ke ws bpjs juga
    payloads = {
        "kodebooking": db_antrian.kodebooking,
        "jenispasien": payload.jenispasien,
        "nomorkartu": db_antrian.nomorkartu,
        "nik": db_antrian.nik,
        "nohp": db_antrian.nohp,
        "kodepoli": db_antrian.kodepoli,
        "namapoli": db_antrian.namapoli,
        "pasienbaru": 0 if db_antrian.pasienbaru is None else 1,
        "norm": db_antrian.norm,
        "tanggalperiksa": db_antrian.tanggalperiksa.strftime('%Y-%m-%d'),
        "kodedokter": db_antrian.kodedokter,
        "namadokter": db_antrian.namadokter,
        "jampraktek": db_antrian.jampraktek,
        "jeniskunjungan": db_antrian.jeniskunjungan,
        "nomorreferensi": db_antrian.nomorreferensi,
        "nomorantrean": db_antrian.nomorantrian,
        "angkaantrean": db_antrian.angkaantrean,
        "estimasidilayani": db_antrian.estimasidilayani,
        "sisakuotajkn": db_antrian.sisakuotajkn,
        "kuotajkn": db_antrian.kuotajkn,
        "sisakuotanonjkn": db_antrian.sisakuotanonjkn,
        "kuotanonjkn": db_antrian.kuotanonjkn,
        "keterangan": "Peserta harap 30 menit lebih awal guna pencatatan administrasi."
    }
    print(payloads)
    # HIT BPJS
    # newPayload = models.TambahAntrian(**payloads)
    # # print(newPayload)
    # hit_ambil_antrian = bpjs.post('/antrean/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    # # print(hit_ambil_antrian)
    # if hit_ambil_antrian['metadata']['code'] == 201:
    #     # print('masuk sini')
    #     # jika pasien nomor kartu tidak ditemukan, maka daftar pasien baru
    #     if hit_ambil_antrian['metadata']['message'] == 'Nomor kartu tidak terdaftar.':
    #         payloads['pasienbaru'] = 1
    #         newPayload = models.TambahAntrian(**payloads)
    #         # print(newPayload)
    #         hit_ambil_antrian_2 = bpjs.post('/antrean/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    #         # print(hit_ambil_antrian_2)
    #         if hit_ambil_antrian_2['metadata']['code'] == 200:
    #             return db_antrian
    #         else:
    #             db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
    #             db.commit()
    #             return hit_ambil_antrian_2

    #     db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
    #     db.commit()
    #     return hit_ambil_antrian
    # # e
    newPayload = models.TambahAntrian(**payloads)
    hit_ambil_antrian = bpjs.post('antrean/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    if hit_ambil_antrian['metadata']['code'] == 201:
        # print('masuk sini')
        # jika pasien nomor kartu tidak ditemukan, maka daftar pasien baru
        if hit_ambil_antrian['metadata']['message'] == 'Nomor kartu tidak terdaftar.':
            payloads['pasienbaru'] = 1
            newPayload = models.TambahAntrian(**payloads)
            # print(newPayload)
            hit_ambil_antrian_2 = bpjs.post('antrean/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
            # print(hit_ambil_antrian_2)
            if hit_ambil_antrian_2['metadata']['code'] == 200:
                db.execute(f"UPDATE antrian_poli set hitws='1' where kodebooking = '{db_antrian.kodebooking}'")
                db.commit()

                return db_antrian
            else:
                db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
                db.commit()
                return hit_ambil_antrian_2

        if hit_ambil_antrian['metadata']['message'] == 'data nomorreferensi  belum sesuai.':
            db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
            db.commit()
            return hit_ambil_antrian
        db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
        db.commit()
        return hit_ambil_antrian
    # e
    # add
    from datetime import datetime, timezone, timedelta

    # Set the timezone to Asia/Jakarta
    jakarta_timezone = timezone(timedelta(hours=7))  # UTC+7

    # Get the current time in the specified timezone
    current_time = datetime.now(jakarta_timezone)

    # Convert to milliseconds since the epoch
    timestamp_milliseconds = int(current_time.timestamp() * 1000)
    # end
    payload = {
        'kodebooking': db_antrian.kodebooking,
        'taskid': '3',
        'waktu': timestamp_milliseconds
    }
    checkins = models.UpdateWaktu(**payload)
    task_id = bpjs.post('antrean/updatewaktu',checkins,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    await insert_taskid(db,db_antrian.kodebooking,'Hit Task Id 3',json.dumps(payload),json.dumps(task_id),"SUKSES" if task_id['metadata']['code'] == 200 else "GAGAL")

    db.execute(f"update antrian_poli set flag = '3' where kodebooking = '{db_antrian.kodebooking}';").rowcount
    db.commit()
    db.execute(f"UPDATE antrian_poli set hitws='1' where kodebooking = '{db_antrian.kodebooking}'")
    db.commit()
    return db_antrian



async def insert_antrian_poli_onsite_lama_debug_prod(db:Session,payload:models.AntrianPoliIn,noantrian:int):
    db_antrian = generate.AntrianPoli(**payload.dict())
    
    db.add(db_antrian)
    db.commit()
    db.refresh(db_antrian)
    print('masuk sini-----')
    print(db_antrian.kodebooking)
    print('masuk sini------')
    nomorantrian = db_antrian.kodepoli + '-' + str(noantrian).zfill(3)
    kodebookingbaru = '0311R001' + db_antrian.tanggalperiksa.strftime('%y%m%d') + db_antrian.kodepoli + str(noantrian).zfill(3)
    # kodebookingbaru = '0311R001'+ db_antrian.tanggalperiksa.strftime('%Y%m%d') +db_antrian.kodepoli+str(noantrian).zfill(3)
    db.execute(f"UPDATE antrian_poli set angkaantrean={noantrian},nomorantrian='{nomorantrian}',kodebooking = '{kodebookingbaru }'where kodebooking = '{db_antrian.kodebooking}'")
    db.commit()
    db.refresh(db_antrian)
    
    # db_antrian.angkaantrean = noantrian
    # db_antrian.nomorantrian = db_antrian.kodepoli + '-' + str(noantrian).zfill(3)
    # db_antrian.kodebooking = '0311R001'+ db_antrian.tanggalperiksa.strftime('%Y%m%d') +db_antrian.kodepoli+str(noantrian).zfill(3) 

    # disini daftar kan ke ws bpjs juga
    payloads = {
        "kodebooking": db_antrian.kodebooking,
        "jenispasien": payload.jenispasien,
        "nomorkartu": db_antrian.nomorkartu,
        "nik": db_antrian.nik,
        "nohp": db_antrian.nohp,
        "kodepoli": db_antrian.kodepoli,
        "namapoli": db_antrian.namapoli,
        "pasienbaru": 0 if db_antrian.pasienbaru is None else 1,
        "norm": db_antrian.norm,
        "tanggalperiksa": db_antrian.tanggalperiksa.strftime('%Y-%m-%d'),
        "kodedokter": db_antrian.kodedokter,
        "namadokter": db_antrian.namadokter,
        "jampraktek": db_antrian.jampraktek,
        "jeniskunjungan": 3 if db_antrian.jeniskunjungan == 4 else db_antrian.jeniskunjungan,
        "nomorreferensi": db_antrian.nomorreferensi,
        "nomorantrean": db_antrian.nomorantrian,
        "angkaantrean": db_antrian.angkaantrean,
        "estimasidilayani": db_antrian.estimasidilayani,
        "sisakuotajkn": db_antrian.sisakuotajkn,
        "kuotajkn": db_antrian.kuotajkn,
        "sisakuotanonjkn": db_antrian.sisakuotanonjkn,
        "kuotanonjkn": db_antrian.kuotanonjkn,
        "keterangan": "Peserta harap 30 menit lebih awal guna pencatatan administrasi."
    }
    # return False
    # HIT BPJS
    # newPayload = models.TambahAntrian(**payloads)
    # # print(newPayload)
    # hit_ambil_antrian = bpjs.post('/antrean/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    # # print(hit_ambil_antrian)
    # if hit_ambil_antrian['metadata']['code'] == 201:
    #     # print('masuk sini')
    #     # jika pasien nomor kartu tidak ditemukan, maka daftar pasien baru
    #     if hit_ambil_antrian['metadata']['message'] == 'Nomor kartu tidak terdaftar.':
    #         payloads['pasienbaru'] = 1
    #         newPayload = models.TambahAntrian(**payloads)
    #         # print(newPayload)
    #         hit_ambil_antrian_2 = bpjs.post('/antrean/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    #         # print(hit_ambil_antrian_2)
    #         if hit_ambil_antrian_2['metadata']['code'] == 200:
    #             return db_antrian
    #         else:
    #             db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
    #             db.commit()
    #             return hit_ambil_antrian_2

    #     db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
    #     db.commit()
    #     return hit_ambil_antrian
    # # e
    newPayload = models.TambahAntrian(**payloads)
    # print(newPayload)
    # print("OHINI")
    hit_ambil_antrian = bpjs.post('antrean/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    if hit_ambil_antrian['metadata']['code'] == 201:
        # print('masuk sini')
        # jika pasien nomor kartu tidak ditemukan, maka daftar pasien baru
        if hit_ambil_antrian['metadata']['message'] == 'Nomor kartu tidak terdaftar.':
            payloads['pasienbaru'] = 1
            newPayload = models.TambahAntrian(**payloads)
            # print(newPayload)
            hit_ambil_antrian_2 = bpjs.post('antrean/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
            # print(hit_ambil_antrian_2)
            if hit_ambil_antrian_2['metadata']['code'] == 200:
                db.execute(f"UPDATE antrian_poli set hitws='1' where kodebooking = '{db_antrian.kodebooking}'")
                db.commit()

                return db_antrian
            else:
                db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
                db.commit()
                return hit_ambil_antrian_2

        if hit_ambil_antrian['metadata']['message'] == 'data nomorreferensi  belum sesuai.':
            db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
            db.commit()
            return hit_ambil_antrian
        db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
        db.commit()
        return hit_ambil_antrian
    # e
    # add
    from datetime import datetime, timezone, timedelta

    # Set the timezone to Asia/Jakarta
    jakarta_timezone = timezone(timedelta(hours=7))  # UTC+7

    # Get the current time in the specified timezone
    current_time = datetime.now(jakarta_timezone)

    # Convert to milliseconds since the epoch
    timestamp_milliseconds = int(current_time.timestamp() * 1000)
    # end
    payload = {
        'kodebooking': db_antrian.kodebooking,
        'taskid': '3',
        'waktu': timestamp_milliseconds
    }
    checkins = models.UpdateWaktu(**payload)
    task_id = bpjs.post('antrean/updatewaktu',checkins,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    await insert_taskid(db,db_antrian.kodebooking,'Hit Task Id 3',json.dumps(payload),json.dumps(task_id),"SUKSES" if task_id['metadata']['code'] == 200 else "GAGAL")


    db.execute(f"update antrian_poli set flag = '3' where kodebooking = '{db_antrian.kodebooking}';").rowcount
    db.commit()
    db.execute(f"UPDATE antrian_poli set hitws='1' where kodebooking = '{db_antrian.kodebooking}'")
    db.commit()
    return db_antrian



async def insert_antrian_poli_onsite_lama_debug(db:Session,payload:models.AntrianPoliIn,noantrian:int):
    db_antrian = generate.AntrianPoli(**payload.dict())
    db.add(db_antrian)
    db.commit()
    db.refresh(db_antrian)
    print('masuk sini-----')
    print(db_antrian.kodebooking)
    print('masuk sini------')
    nomorantrian = db_antrian.kodepoli + '-' + str(noantrian).zfill(3)
    kodebookingbaru = '0311R001' + db_antrian.tanggalperiksa.strftime('%y%m%d') + db_antrian.kodepoli + str(noantrian).zfill(3)
    # kodebookingbaru = '0311R001'+ db_antrian.tanggalperiksa.strftime('%Y%m%d') +db_antrian.kodepoli+str(noantrian).zfill(3)
    db.execute(f"UPDATE antrian_poli set angkaantrean={noantrian},nomorantrian='{nomorantrian}',kodebooking = '{kodebookingbaru }'where kodebooking = '{db_antrian.kodebooking}'")
    db.commit()
    db.refresh(db_antrian)
    
    # db_antrian.angkaantrean = noantrian
    # db_antrian.nomorantrian = db_antrian.kodepoli + '-' + str(noantrian).zfill(3)
    # db_antrian.kodebooking = '0311R001'+ db_antrian.tanggalperiksa.strftime('%Y%m%d') +db_antrian.kodepoli+str(noantrian).zfill(3) 

    # print( 3 if db_antrian.jeniskunjungan == 4 else db_antrian.jeniskunjungan)
    # return False
    # disini daftar kan ke ws bpjs juga
    payloads = {
        "kodebooking": db_antrian.kodebooking,
        "jenispasien": payload.jenispasien,
        "nomorkartu": db_antrian.nomorkartu,
        "nik": db_antrian.nik,
        "nohp": db_antrian.nohp,
        "kodepoli": db_antrian.kodepoli,
        "namapoli": db_antrian.namapoli,
        "pasienbaru": 0 if db_antrian.pasienbaru is None else 1,
        "norm": db_antrian.norm,
        "tanggalperiksa": db_antrian.tanggalperiksa.strftime('%Y-%m-%d'),
        "kodedokter": db_antrian.kodedokter,
        "namadokter": db_antrian.namadokter,
        "jampraktek": db_antrian.jampraktek,
        "jeniskunjungan": 3 if db_antrian.jeniskunjungan == 4 else db_antrian.jeniskunjungan,
        "nomorreferensi": db_antrian.nomorreferensi,
        "nomorantrean": db_antrian.nomorantrian,
        "angkaantrean": db_antrian.angkaantrean,
        "estimasidilayani": db_antrian.estimasidilayani,
        "sisakuotajkn": db_antrian.sisakuotajkn,
        "kuotajkn": db_antrian.kuotajkn,
        "sisakuotanonjkn": db_antrian.sisakuotanonjkn,
        "kuotanonjkn": db_antrian.kuotanonjkn,
        "keterangan": "Peserta harap 30 menit lebih awal guna pencatatan administrasi."
    }
    print(payloads)
    # HIT BPJS
    # newPayload = models.TambahAntrian(**payloads)
    # # print(newPayload)
    # hit_ambil_antrian = bpjs.post('/antrean/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    # # print(hit_ambil_antrian)
    # if hit_ambil_antrian['metadata']['code'] == 201:
    #     # print('masuk sini')
    #     # jika pasien nomor kartu tidak ditemukan, maka daftar pasien baru
    #     if hit_ambil_antrian['metadata']['message'] == 'Nomor kartu tidak terdaftar.':
    #         payloads['pasienbaru'] = 1
    #         newPayload = models.TambahAntrian(**payloads)
    #         # print(newPayload)
    #         hit_ambil_antrian_2 = bpjs.post('/antrean/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    #         # print(hit_ambil_antrian_2)
    #         if hit_ambil_antrian_2['metadata']['code'] == 200:
    #             return db_antrian
    #         else:
    #             db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
    #             db.commit()
    #             return hit_ambil_antrian_2

    #     db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
    #     db.commit()
    #     return hit_ambil_antrian
    # # e
    newPayload = models.TambahAntrian(**payloads)
    hit_ambil_antrian = bpjs.post('antrean/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    if hit_ambil_antrian['metadata']['code'] == 201:
        # print('masuk sini')
        # jika pasien nomor kartu tidak ditemukan, maka daftar pasien baru
        if hit_ambil_antrian['metadata']['message'] == 'Nomor kartu tidak terdaftar.':
            payloads['pasienbaru'] = 1
            newPayload = models.TambahAntrian(**payloads)
            # print(newPayload)
            hit_ambil_antrian_2 = bpjs.post('antrean/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
            # print(hit_ambil_antrian_2)
            if hit_ambil_antrian_2['metadata']['code'] == 200:
                db.execute(f"UPDATE antrian_poli set hitws='1' where kodebooking = '{db_antrian.kodebooking}'")
                db.commit()

                return db_antrian
            else:
                db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
                db.commit()
                return hit_ambil_antrian_2

        if hit_ambil_antrian['metadata']['message'] == 'data nomorreferensi  belum sesuai.':
            db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
            db.commit()
            return hit_ambil_antrian
        db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
        db.commit()
        return hit_ambil_antrian
    # e
    # add
    from datetime import datetime, timezone, timedelta

    # Set the timezone to Asia/Jakarta
    jakarta_timezone = timezone(timedelta(hours=7))  # UTC+7

    # Get the current time in the specified timezone
    current_time = datetime.now(jakarta_timezone)

    # Convert to milliseconds since the epoch
    timestamp_milliseconds = int(current_time.timestamp() * 1000)
    # end
    payload = {
        'kodebooking': db_antrian.kodebooking,
        'taskid': '3',
        'waktu': timestamp_milliseconds
    }
    checkins = models.UpdateWaktu(**payload)
    task_id = bpjs.post('antrean/updatewaktu',checkins,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    await insert_taskid(db,db_antrian.kodebooking,'Hit Task Id 3',json.dumps(payload),json.dumps(task_id),"SUKSES" if task_id['metadata']['code'] == 200 else "GAGAL")


    db.execute(f"update antrian_poli set flag = '3' where kodebooking = '{db_antrian.kodebooking}';").rowcount
    db.commit()
    db.execute(f"UPDATE antrian_poli set hitws='1' where kodebooking = '{db_antrian.kodebooking}'")
    db.commit()
    return db_antrian


async def insert_antrian_poli_onsite(db:Session,payload:models.AntrianPoliIn):
    db_antrian = generate.AntrianPoli(**payload.dict())
    db.add(db_antrian)
    db.commit()
    db.refresh(db_antrian)
    print('masuk sini-----')
    print(db_antrian.norm)
    print('masuk sini------')
    # disini daftar kan ke ws bpjs juga
    payloads = {
        "kodebooking": db_antrian.kodebooking,
        "jenispasien": payload.jenispasien,
        "nomorkartu": db_antrian.nomorkartu,
        "nik": db_antrian.nik,
        "nohp": db_antrian.nohp,
        "kodepoli": db_antrian.kodepoli,
        "namapoli": db_antrian.namapoli,
        "pasienbaru": 0 if db_antrian.pasienbaru is None else 1,
        "norm": db_antrian.norm,
        "tanggalperiksa": db_antrian.tanggalperiksa.strftime('%Y-%m-%d'),
        "kodedokter": db_antrian.kodedokter,
        "namadokter": db_antrian.namadokter,
        "jampraktek": db_antrian.jampraktek,
        "jeniskunjungan": db_antrian.jeniskunjungan,
        "nomorreferensi": db_antrian.nomorreferensi,
        "nomorantrean": db_antrian.nomorantrian,
        "angkaantrean": db_antrian.angkaantrean,
        "estimasidilayani": db_antrian.estimasidilayani,
        "sisakuotajkn": db_antrian.sisakuotajkn,
        "kuotajkn": db_antrian.kuotajkn,
        "sisakuotanonjkn": db_antrian.sisakuotanonjkn,
        "kuotanonjkn": db_antrian.kuotanonjkn,
        "keterangan": "Peserta harap 30 menit lebih awal guna pencatatan administrasi."
    }
    print(payloads)
    # HIT BPJS
    # newPayload = models.TambahAntrian(**payloads)
    # # print(newPayload)
    # hit_ambil_antrian = bpjs.post('/antrean/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    # # print(hit_ambil_antrian)
    # if hit_ambil_antrian['metadata']['code'] == 201:
    #     # print('masuk sini')
    #     # jika pasien nomor kartu tidak ditemukan, maka daftar pasien baru
    #     if hit_ambil_antrian['metadata']['message'] == 'Nomor kartu tidak terdaftar.':
    #         payloads['pasienbaru'] = 1
    #         newPayload = models.TambahAntrian(**payloads)
    #         # print(newPayload)
    #         hit_ambil_antrian_2 = bpjs.post('/antrean/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    #         # print(hit_ambil_antrian_2)
    #         if hit_ambil_antrian_2['metadata']['code'] == 200:
    #             return db_antrian
    #         else:
    #             db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
    #             db.commit()
    #             return hit_ambil_antrian_2

    #     db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
    #     db.commit()
    #     return hit_ambil_antrian
    # # e
    newPayload = models.TambahAntrian(**payloads)
    print(payloads)
    hit_ambil_antrian = bpjs.post('antrean/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    print(hit_ambil_antrian)
    if hit_ambil_antrian['metadata']['code'] == 201:
        # print('masuk sini')
        # jika pasien nomor kartu tidak ditemukan, maka daftar pasien baru
        if hit_ambil_antrian['metadata']['message'] == 'Nomor kartu tidak terdaftar.':
            payloads['pasienbaru'] = 1
            newPayload = models.TambahAntrian(**payloads)
            # print(newPayload)
            hit_ambil_antrian_2 = bpjs.post('antrean/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
            # print(hit_ambil_antrian_2)
            if hit_ambil_antrian_2['metadata']['code'] == 200:
                db.execute(f"UPDATE antrian_poli set hitws='1' where kodebooking = '{db_antrian.kodebooking}'")
                db.commit()

                return db_antrian
            else:
                db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
                db.commit()
                return hit_ambil_antrian_2

        if hit_ambil_antrian['metadata']['message'] == 'data nomorreferensi  belum sesuai.':
            db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
            db.commit()
            return hit_ambil_antrian
        db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
        db.commit()
        return hit_ambil_antrian
    # e
    # add
    from datetime import datetime, timezone, timedelta

    # Set the timezone to Asia/Jakarta
    jakarta_timezone = timezone(timedelta(hours=7))  # UTC+7

    # Get the current time in the specified timezone
    current_time = datetime.now(jakarta_timezone)

    # Convert to milliseconds since the epoch
    timestamp_milliseconds = int(current_time.timestamp() * 1000)
    # end
    payload = {
        'kodebooking': db_antrian.kodebooking,
        'taskid': '1',
        'waktu': timestamp_milliseconds
    }
    checkins = models.UpdateWaktu(**payload)
    task_id = bpjs.post('antrean/updatewaktu',checkins,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    await insert_taskid(db,db_antrian.kodebooking,'Hit Task Id 1',json.dumps(payload),json.dumps(task_id),"SUKSES" if task_id['metadata']['code'] == 200 else "GAGAL")


    db.execute(f"update antrian_poli set flag = '1' where kodebooking = '{db_antrian.kodebooking}';").rowcount
    db.commit()
    db.execute(f"UPDATE antrian_poli set hitws='1' where kodebooking = '{db_antrian.kodebooking}'")
    db.commit()
    return db_antrian


async def insert_antrian_poli(db:Session,payload:models.AntrianPoliIn,noantrian:int):
    db_antrian = generate.AntrianPoli(**payload.dict())
    db.add(db_antrian)
    db.commit()
    db.refresh(db_antrian)
    print('masuk sini-----')
    print(db_antrian.kodebooking)
    print('masuk sini------')
    nomorantrian = db_antrian.kodepoli + '-' + str(noantrian).zfill(3)
    kodebookingbaru = '0311R001' + db_antrian.tanggalperiksa.strftime('%y%m%d') + db_antrian.kodepoli + str(noantrian).zfill(3)
    # kodebookingbaru = '0311R001'+ db_antrian.tanggalperiksa.strftime('%Y%m%d') +db_antrian.kodepoli+str(noantrian).zfill(3)
    db.execute(f"UPDATE antrian_poli set angkaantrean={noantrian},nomorantrian='{nomorantrian}',kodebooking = '{kodebookingbaru }'where kodebooking = '{db_antrian.kodebooking}'")
    db.commit()
    db.refresh(db_antrian)


    # disini daftar kan ke ws bpjs juga
    payloads = {
        "kodebooking": db_antrian.kodebooking,
        "jenispasien": payload.jenispasien,
        "nomorkartu": db_antrian.nomorkartu,
        "nik": db_antrian.nik,
        "nohp": db_antrian.nohp,
        "kodepoli": db_antrian.kodepoli,
        "namapoli": db_antrian.namapoli,
        "pasienbaru": 0 if db_antrian.pasienbaru is None else 1,
        "norm": db_antrian.norm,
        "tanggalperiksa": db_antrian.tanggalperiksa.strftime('%Y-%m-%d'),
        "kodedokter": db_antrian.kodedokter,
        "namadokter": db_antrian.namadokter,
        "jampraktek": db_antrian.jampraktek,
        "jeniskunjungan": db_antrian.jeniskunjungan,
        "nomorreferensi": db_antrian.nomorreferensi,
        "nomorantrean": db_antrian.nomorantrian,
        "angkaantrean": db_antrian.angkaantrean,
        "estimasidilayani": db_antrian.estimasidilayani,
        "sisakuotajkn": db_antrian.sisakuotajkn,
        "kuotajkn": db_antrian.kuotajkn,
        "sisakuotanonjkn": db_antrian.sisakuotanonjkn,
        "kuotanonjkn": db_antrian.kuotanonjkn,
        "keterangan": "Peserta harap 30 menit lebih awal guna pencatatan administrasi."
    }
    print(payloads)
    # HIT BPJS
    # newPayload = models.TambahAntrian(**payloads)
    # # print(newPayload)
    # hit_ambil_antrian = bpjs.post('/antrean/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    # # print(hit_ambil_antrian)
    # if hit_ambil_antrian['metadata']['code'] == 201:
    #     # print('masuk sini')
    #     # jika pasien nomor kartu tidak ditemukan, maka daftar pasien baru
    #     if hit_ambil_antrian['metadata']['message'] == 'Nomor kartu tidak terdaftar.':
    #         payloads['pasienbaru'] = 1
    #         newPayload = models.TambahAntrian(**payloads)
    #         # print(newPayload)
    #         hit_ambil_antrian_2 = bpjs.post('/antrean/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    #         # print(hit_ambil_antrian_2)
    #         if hit_ambil_antrian_2['metadata']['code'] == 200:
    #             return db_antrian
    #         else:
    #             db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
    #             db.commit()
    #             return hit_ambil_antrian_2

    #     db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
    #     db.commit()
    #     return hit_ambil_antrian
    # # e
    # newPayload = models.TambahAntrian(**payloads)
    # hit_ambil_antrian = bpjs.post('/antrean/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    # if hit_ambil_antrian['metadata']['code'] == 201:
    #     # print('masuk sini')
    #     # jika pasien nomor kartu tidak ditemukan, maka daftar pasien baru
    #     if hit_ambil_antrian['metadata']['message'] == 'Nomor kartu tidak terdaftar.':
    #         payloads['pasienbaru'] = 1
    #         newPayload = models.TambahAntrian(**payloads)
    #         # print(newPayload)
    #         hit_ambil_antrian_2 = bpjs.post('/antrean/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    #         # print(hit_ambil_antrian_2)
    #         if hit_ambil_antrian_2['metadata']['code'] == 200:
    #             db.execute(f"UPDATE antrian_poli set hitws='1' where kodebooking = '{db_antrian.kodebooking}'")
    #             db.commit()

    #             return db_antrian
    #         else:
    #             db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
    #             db.commit()
    #             return hit_ambil_antrian_2

    #     if hit_ambil_antrian['metadata']['message'] == 'data nomorreferensi  belum sesuai.':
    #         db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
    #         db.commit()
    #         return hit_ambil_antrian
    #     db.execute(f"DELETE FROM antrian_poli where kodebooking = '{db_antrian.kodebooking}'")
    #     db.commit()
    #     return hit_ambil_antrian
    # # # e
    # db.execute(f"UPDATE antrian_poli set hitws='1' where kodebooking = '{db_antrian.kodebooking}'")
    # db.commit()

    # import time
    # # eksekusi untuk update flag
    # # jika pasien baru 
    # if db_antrian.pasienbaru is None:
    #     epoch_millis = int(time.time() * 1000)

    #     req = {
    #         'kodebooking': db_antrian.kodebooking,
    #         'taskid': '3',
    #         'waktu':epoch_millis
    #     }
    #     newPayload = models.UpdateWaktu(**req)
    #     task_id = bpjs.post('/antrean/updatewaktu',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    
    #     # update flag 3

    # else:
    #     # update flag 1
    #     epoch_millis = int(time.time() * 1000)

    #     req = {
    #         'kodebooking': db_antrian.kodebooking,
    #         'taskid': '1',
    #         'waktu':epoch_millis
    #     }
    #     newPayload = models.UpdateWaktu(**req)
    #     task_id = bpjs.post('/antrean/updatewaktu',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)

    #     epoch_millis2 = int(time.time() * 1000)

    #     req = {
    #         'kodebooking': db_antrian.kodebooking,
    #         'taskid': '2',
    #         'waktu':epoch_millis2
    #     }
    #     newPayload = models.UpdateWaktu(**req)
    #     task_id_2 = bpjs.post('/antrean/updatewaktu',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)

        
    # update flag 2
    # update flag 3


    return db_antrian


async def insert_antrian_farmasi(db:Session,payload:models.AmbilAntreanFarmasi,jenisfarmasi):
    if jenisfarmasi is not None:
        if jenisfarmasi[0] == 0:
            payload.jenisresep = 'Non Racikan'
        else:
            payload.jenisresep = 'Racikan'
    else:
        payload.jenisresep = 'Non Racikan'
    
    db_antrian = generate.AntrianFarmasi(**payload.dict())
    db.add(db_antrian)
    db.commit()
    db.refresh(db_antrian)

    # disini daftar kan ke ws bpjs juga
    payloads = {
        "kodebooking": db_antrian.kodebooking,
        "jenisresep": db_antrian.jenisresep,
        "nomorantrean":db_antrian.nomorantrean,
        "keterangan": "Keterangan Wajib Diisi" if db_antrian.keterangan is None else db_antrian.keterangan 
    }
    print(payloads)
    newPayload = models.AmbilAntreanFarmasi(**payloads)
    hit_ambil_antrian = bpjs.post('/antrean/farmasi/add',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    print(hit_ambil_antrian)
    return db_antrian

async def insertpasienbaru(db:Session,payload:models.Pasienbaru):
    db_antrian = generate.Pasienbaru(**payload.dict())
    db.add(db_antrian)
    db.commit()
    db.refresh(db_antrian)
    return db_antrian

async def checkPasienExist(db:Session,nomorkartu):
    db_antrian = db.execute(f"SELECT * FROM pasienbaru where nomorkartu = '{nomorkartu}'").first()
    return db_antrian

async def checkAntrianExist(db:Session,nomorkartu,tgl):
    db_antrian = db.execute(f"SELECT * FROM antrian_poli where nomorkartu='{nomorkartu}' and tanggalperiksa='{tgl}' and (flag not in ('99') or flag is null)").rowcount
    db.commit()
    return db_antrian

async def checkAntrianExistNoRm(db:Session,nomorkartu,tgl):
    db_antrian = db.execute(f"SELECT * FROM antrian_poli where norm='{nomorkartu}' and tanggalperiksa='{tgl}' and (flag not in ('99') or flag is null)").rowcount
    db.commit()
    return db_antrian

async def checkReferensiExist(db:Session,nomorreferensi):
    db_antrian = db.execute(f"SELECT * FROM antrian_poli where nomorreferensi='{nomorreferensi}' and (flag not in ('99') or flag is null)").rowcount
    db.commit()
    return db_antrian
    
    
async def carikodebooking(db: Session,payload: models.BatalAntrian):
    db_antrian = db.execute(f"SELECT * FROM antrian_poli where kodebooking = '{payload.kodebooking}'").first()
    return db_antrian

async def carikodebookingdanupdate(db:Session,payload:models.BatalAntrian):
    task_id = bpjs.post('/antrean/batal',payload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    if task_id is not None:
        if task_id['metadata']['code'] == 200:
            # menandakan update sukses dari bpjs
            db_antrian = db.execute(f"UPDATE antrian_poli set flag = '99',keterangan='{payload.keterangan}' where kodebooking = '{payload.kodebooking}'; ").rowcount
            db.commit()
            return {'metadata':{'code':200,'message':'Ok'}}
    # untuk keperluan development
    else:
        db_antrian = db.execute(f"UPDATE antrian_poli set flag = '99',keterangan='{payload.keterangan}' where kodebooking = '{payload.kodebooking}'; ").rowcount
        db.commit()
        return {'metadata':{'code':200,'message':'Ok'}}
    return task_id

async def carikodebookingdanhapus(db:Session,payload:models.BatalAntrian):
    db_antrian = db.execute(f"delete from antrian_poli where kodebooking = '{payload.kodebooking}'; ").rowcount
    db.commit()
    return db_antrian

async def caridkodebookingdancheckin(db: Session, payload : models.ChekinAntrian):
    check = db.execute(f"select pasienbaru,flag from antrian_poli where kodebooking = '{payload.kodebooking}'").first()
    waktus = payload.waktu
    if check is None:
        return {'metadata':{'code':201,'message':'Kode Booking Tidak Ditemukan'}}
    # jika pasienbaru tidak null => maka perlu update flag / task id ke 1 
    # if check[0] is not None:
    #     req = {
    #         'kodebooking': payload.kodebooking,
    #         'taskid': '1',
    #         'waktu': waktus
    #     }
    #     newPayload = models.UpdateWaktu(**req)
    #     task_id = bpjs.post('/antrean/updatewaktu',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    #     # print(task_id)
    #     if task_id['metadata']['code'] != 200:
    #         return task_id
        # if task_id['metadata']['code'] != 200:
        #     return 0
    import time

    epoch_millis2 = int(time.time() * 1000)

    req = {
        'kodebooking': payload.kodebooking,
        'taskid': '3',
        'waktu':epoch_millis2
    }
    newPayload = models.UpdateWaktu(**req)
    task_id_2 = bpjs.post('antrean/updatewaktu',newPayload,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',True)
    await insert_taskid(db,payload.kodebooking,'Hit Task Id 3',json.dumps(req),json.dumps(task_id_2),"SUKSES" if task_id_2['metadata']['code'] == 200 else "GAGAL")
    
        
        
    db_antrian = db.execute(f"UPDATE antrian_poli set flag = '3' where kodebooking = '{payload.kodebooking}'").rowcount
    db.commit()
    return {'metadata':{'code':200,'message':"Ok."}}

async def cekstatusantrian(db:Session,payload:models.Statusantrian,kapasitas_pasien):
    sql = f"""SELECT
        namapoli,
        namadokter,
        COUNT(*) FILTER(where flag != '99' or flag is null) AS totalantrean,
        COUNT(CASE WHEN kodedokter = '{payload.kodedokter}' AND kodepoli = '{payload.kodepoli}' AND tanggalperiksa = '{payload.tanggalperiksa}' AND (flag != '99' or flag is null) THEN 1 END) AS totalkuotajkn,
        COUNT(CASE WHEN kodedokter = '{payload.kodedokter}' AND tanggalperiksa = '{payload.tanggalperiksa}' AND ((flag != '99' and flag != '7') or flag is null) THEN 1 END) AS sisaantrian,
        MAX(CASE WHEN kodepoli = '{payload.kodepoli}' AND kodedokter = '{payload.kodedokter}' AND tanggalperiksa = '{payload.tanggalperiksa}' AND flag = '2' THEN nomorantrian END) AS antreanpanggil,
        MAX(sisakuotajkn) AS sisakuotajkn,
        {kapasitas_pasien} AS kuotajkn,
        {kapasitas_pasien} AS kuotanonjkn,
        MAX(sisakuotanonjkn) AS sisakuotanonjkn,
        '' AS keterangan
    FROM antrian_poli
    WHERE
        kodepoli = '{payload.kodepoli}' AND
        kodedokter = '{payload.kodedokter}' AND
        tanggalperiksa = '{payload.tanggalperiksa}' 
    GROUP BY namapoli, namadokter;
    """
    db_antrian = db.execute(sql).first()
    return db_antrian

async def ceksisaantrian(db:Session,payload:models.Sisaantrian):
    # dbantrian = db.execute(f"""SELECT nomorantrian,
    # namapoli,
    # namadokter,
    # (select count(*) * 600 as waktutunggu from antrian_poli a where a.kodedokter = antrian_poli.kodedokter and a.tanggalperiksa = antrian_poli.tanggalperiksa
	# 	and a.angkaantrean < antrian_poli.angkaantrean),
    # '' as keterangan,
    # kodedokter,
    # tanggalperiksa,
    # (select count(*) as sisaantrian from antrian_poli a where a.kodedokter = antrian_poli.kodedokter and a.tanggalperiksa = antrian_poli.tanggalperiksa
	# 	and a.angkaantrean < antrian_poli.angkaantrean),
    # (select nomorantrian as antreanpanggil from antrian_poli a where a.kodedokter = antrian_poli.kodedokter and a.tanggalperiksa = antrian_poli.tanggalperiksa
    # and flag = '2')
    # FROM antrian_poli
    # where kodebooking = '{payload.kodebooking}'""").first()

    dbantrian = db.execute(f"""SELECT nomorantrian,
    namapoli,
    namadokter,
    kodedokter,
    tanggalperiksa,
    (select count(*)  * 600 from antrian_poli a where a.kodedokter = antrian_poli.kodedokter and a.tanggalperiksa = antrian_poli.tanggalperiksa
    and a.id < antrian_poli.id and (a.flag != '99' or a.flag is null)
    ) as waktutunggu,
    '' as keterangan,
    (select count(*) as sisaantrian from antrian_poli a where a.kodedokter = antrian_poli.kodedokter and a.tanggalperiksa = antrian_poli.tanggalperiksa
            and a.angkaantrean < antrian_poli.angkaantrean and (a.flag != '99' or a.flag is null)),
            (select nomorantrian as antreanpanggil from antrian_poli a where a.kodedokter = antrian_poli.kodedokter and a.tanggalperiksa = antrian_poli.tanggalperiksa and flag = '2')
    from antrian_poli where kodebooking = '{payload.kodebooking}' and (flag != '99' or flag is null) """).first()
    return dbantrian

async def prosesantrian(db:Session, kodebooking : str,flag:str):
    dbantrian = db.execute(f"update antrian_poli set flag = '{flag}' where kodebooking = '{kodebooking}';").rowcount
    db.commit()
    return dbantrian

async def ambilpasienbaru(db:Session,nomorkartu : str):
    dbpasienbaru = db.execute(f"select * from pasienbaru where nomorkartu= '{nomorkartu}'").first()
    return dbpasienbaru

async def selesaiantrian(db:Session,kodebooking:str):
    dbantrian = db.execute(f"update antrian_poli set flag = '3' where kodebooking = '{kodebooking}';commit;").rowcount
    db.commit()
    return dbantrian


async def statusantrianpertgl(db:Session,tanggalawal:str,tanggalakhir:str):
    # dbantrian = db.execute(f"SELECT * from antrian_poli LEFT OUTER JOIN pasienbaru on pasienbaru.nomorkartu = antrian_poli.nomorkartu where tanggalperiksa <= '{tanggalakhir}' and tanggalperiksa >= '{tanggalawal}'").all()
    dbantrian = db.execute(f"SELECT * FROM antrian_poli where tanggalperiksa <= '{tanggalakhir}' and tanggalperiksa >= '{tanggalawal}'").all()
    return dbantrian


async def statusantrianpertglbatal(db:Session,tanggalawal:str,tanggalakhir:str):
    dbantrian = db.execute(f"SELECT * FROM antrian_poli where tanggalperiksa <= '{tanggalakhir}' and tanggalperiksa >= '{tanggalawal}' and flag = '99';").all()
    return dbantrian

async def statusantrianpertglselesai(db:Session,tanggalawal:str,tanggalakhir:str):
    dbantrian = db.execute(f"SELECT * FROM antrian_poli where tanggalperiksa <= '{tanggalakhir}' and tanggalperiksa >= '{tanggalawal}' and (flag = '6' or flag = '7');").all()
    return dbantrian

# fungsi untuk merubah tgl menjadi hari dalam bahasa indonesia.
# parameter : tgl 
# format : default Y-m-d / d-m-Y => "%d-%m-%Y"
def getHariBerdasarkanTgl(tgl,formats="%Y-%m-%d"):
    try:
        hari = datetime.datetime.strptime(tgl, formats).strftime('%A')
        dayConvert = {
            'Sunday':'MINGGU',
            'Monday':"SENIN",
            'Tuesday':"SELASA",
            "Wednesday":"RABU",
            "Thursday":"KAMIS",
            "Friday":"JUMAT",
            "Saturday":"SABTU",
        }
        return dayConvert.get(hari)
    except:
        return False

async def cariJadwalDokterByHfis(db:Session,tgl,kodehfis):
    hari = getHariBerdasarkanTgl(tgl)
    if not hari : 
        return hari

    sql = f"SELECT * FROM jadwal_hfis where kode_hfis='{kodehfis}' and hari = '{hari}';"
    return db.execute(sql).first()

async def cariJadwalDokter(db:Session,tgl,id_dokter):
    hari = getHariBerdasarkanTgl(tgl)
    if not hari : 
        return hari

    sql = f"SELECT * FROM jadwal_hfis where id_dokter='{id_dokter}' and hari = '{hari}';"
    return db.execute(sql).first()
    
async def cekPasienBaruExist(db:Session,nomorkartu,norm):
    try:
        # Try to convert the string to an integer
        norm = int(norm)
    except ValueError:
        return None

    cekPasienBaru = db.execute(f"SELECT * FROM pasienbaru where nomorkartu = '{nomorkartu}'").first()
    return cekPasienBaru

async def cekPasienBaruExistNik(db:Session,nik):
    cekPasienBaru = db.execute(f"SELECT * FROM pasienbaru where nik = '{nik}'").first()
    return cekPasienBaru

async def cekPasienbarulama(db:Session,nomorkartu):
    cekPasienbarulama = db.execute(f"SELECT * FROM antrian_poli where nomorkartu = '{nomorkartu}' and (flag !='99' or flag is null)").first()
    return cekPasienbarulama


async def cariJadwalPoli(db:Session, poliklinik,tgl):
    hari = getHariBerdasarkanTgl(tgl)
    if not hari:
        return False

    poli = db.execute(f"SELECT * FROM jadwal_hfis where poli_bpjs = '{poliklinik}' and hari = '{hari}'").all()
    return True if poli else False


async def grabAllDokter(db:Session):
    poli = db.execute("SELECT * FROM jadwal_hfis").all()
    return poli

async def updatePoli(db:Session,data,iddokter):
    poli = db.execute(f"update jadwal_hfis set poli_bpjs = '{data}' where jadwal_hfis.id_dokter = '{iddokter}'").rowcount
    db.commit()
    return poli


async def cekTotalAntrian(db:Session,kodehfis,pertgl:str=''):
    if pertgl != '':
        sql = f"select count(*) from antrian_poli where tanggalperiksa ='{pertgl}' and kodedokter = '{kodehfis}' and (flag != '99' or flag is null)"
    else:
        sql = f"select count(*) from antrian_poli where tanggalperiksa = TO_CHAR(now(),'YYYY-MM-dd') and kodedokter = '{kodehfis}'; and (flag != '99' or flag is null)"
    
    print(sql)
    return db.execute(sql).first()

async def cekTotalAntrianFarmasi(db:Session,kodebooking:str):
    sql = f"SELECT count(*) from antrian_farmasi where tanggal"


async def dataantreanproses(db:Session,poli:str,kodedokter:str):
    poli = db.execute(f"SELECT * FROM antrian_poli where kodepoli = '{poli}' and kodedokter='{kodedokter}' and tanggalperiksa = TO_CHAR(NOW(),'YYYY-MM-dd') and (flag not in ('2','3', '4') or flag is null)  order by angkaantrean asc").all()
    # print(poli)
    return poli


async def dataantreanperiksa(db:Session,poli:str,kodedokter:str):
    poli = db.execute(f"SELECT * FROM antrian_poli where kodepoli = '{poli}' and kodedokter='{kodedokter}' and tanggalperiksa = TO_CHAR(NOW(),'YYYY-MM-dd') and flag = '2'  order by angkaantrean asc").first()
    # print(poli)
    return poli

async def get_status_antrian_farmasi(db:Session,kodebooking:str):
    return db.execute(f"""SELECT jenisresep,
    (select count(*) from antrian_farmasi where TO_CHAR(tglperiksa,'YYYY-MM-DD') = TO_CHAR(now(),'YYYY-MM-DD')) as totalantrean,
    (select count(*) from antrian_farmasi a where TO_CHAR(a.tglperiksa,'YYYY-MM-DD') = TO_CHAR(now(),'YYYY-MM-DD')
    and a.nomorantrean < antrian_farmasi.nomorantrean and tindak is null) as sisaantrean,
    (select max(nomorantrean) from antrian_farmasi a where TO_CHAR(a.tglperiksa,'YYYY-MM-DD') = TO_CHAR(now(),'YYYY-MM-DD')
    and tindak is not null) as antreanpanggil,keterangan
    FROM antrian_farmasi where kodebooking = '{kodebooking}'""").first()

async def getJadwalDokterPerPoliPerDokterPerHari(db:Session,tanggal:str,poli:str,kodedokter:str):
    hari = 0
    try:
        date_object = datetime.datetime.strptime(tanggal, "%Y-%m-%d")
        day_name = date_object.strftime("%A")
        day_name_mapping = {
            "Monday": 1,
            "Tuesday": 2,
            "Wednesday": 3,
            "Thursday": 4,
            "Friday": 5,
            "Saturday": 6,
            "Sunday": 7,
        }
        hari = day_name_mapping.get(day_name, 0)
    except ValueError:
        return {'message':'tgl'}
        
    poli = db.execute(f"SELECT * FROM jadwaldokter where kodepoli = '{poli}' and kodedokter={kodedokter} and hari = {hari}").first()
    # print(poli)
    if poli:
        return dict(poli)
    return {'message':'null'}

async def deletepasienbaru(db:Session,norm:str):
    db_antrian = db.execute(f"delete from pasienbaru where norm = {norm}; ").rowcount
    db.commit()
    return db_antrian

    

async def listantrianbelumdiperiksa(db:Session,poli:str,dokter:str):
    return db.execute(f"""SELECT * FROM antrian_poli where kodepoli='{poli}' and kodedokter='{dokter}' and tanggalperiksa='{(datetime.datetime.today() ).strftime('%Y-%m-%d')}' 
    and (flag = '3') order by angkaantrean asc """).all()

    
async def listantrianbelumdiperiksafarmasi(db:Session):
    return db.execute(f"""SELECT * FROM antrian_poli WHERE tanggalperiksa='{datetime.datetime.today().strftime('%Y-%m-%d')}' 
    and (flag is null or flag ='6') order by angkaantrean asc """).all()

# deprecated
async def listantrianbelumdiperiksaadmisi(db:Session):
    return db.execute(f"""SELECT * FROM antrian_poli WHERE tanggalperiksa='{datetime.datetime.today().strftime('%Y-%m-%d')}' 
    and (flag is null or flag ='1') order by angkaantrean asc """).all()

async def listantrianbelumdiperiksaadmisinew(db:Session):
    return db.execute(f"""SELECT * FROM antrian_admisi WHERE TO_CHAR(tgl_kunjungan,'YYYY-MM-dd')='{datetime.datetime.today().strftime('%Y-%m-%d')}'
    and flag = '1' ORDER BY no_antrian ASC """).all()


async def listantriandiperiksaadmisinew(db:Session):
    return db.execute(f"""SELECT * FROM antrian_admisi WHERE TO_CHAR(tgl_kunjungan,'YYYY-MM-dd')='{datetime.datetime.today().strftime('%Y-%m-%d')}'
    and flag = '2' order by no_antrian DESC""").first()


# deprecated
async def listantriandiperiksaadmisi(db:Session):
    return db.execute(f"""SELECT * FROM antrian_poli where  tanggalperiksa='{datetime.datetime.today().strftime('%Y-%m-%d')}' 
    and flag ='2' order by angkaantrean desc""").first()

async def listantriandiperiksa(db:Session,poli:str,dokter:str):
    return db.execute(f"""SELECT * FROM antrian_poli where kodepoli='{poli}' and kodedokter='{dokter}' and tanggalperiksa='{(datetime.datetime.today()).strftime('%Y-%m-%d')}' 
    and flag ='4' order by angkaantrean desc""").first()

async def listantriandiperiksafarmasi(db:Session):
    return db.execute(f"""SELECT * FROM antrian_poli where tanggalperiksa='{datetime.datetime.today().strftime('%Y-%m-%d')}' 
    and flag ='7' order by angkaantrean desc""").first()


async def antrianfarmasi(db: Session):
    # Ambil no_antrian terakhir berdasarkan tanggal sekarang
    today = datetime.date.today()
    
    # Query untuk mencari nomor antrean terbesar di tanggal sekarang
    last_antrian = db.query(generate.AntrianAdmisi.no_antrian)\
                     .filter(generate.AntrianAdmisi.tgl_kunjungan == today)\
                     .order_by(generate.AntrianAdmisi.no_antrian.desc())\
                     .first()

    # Tentukan nomor antrean: jika tidak ada, mulai dari 1
    if last_antrian is None:
        no_antrian = 1
    else:
        no_antrian = last_antrian[0] + 1

    # Buat entri baru untuk antrian_admisi
    db_antrian = generate.AntrianAdmisi(
        no_antrian=no_antrian,
        tgl_kunjungan=today,
        flag='1',
        loket=None
    )
    
    # Simpan ke database
    db.add(db_antrian)
    db.commit()
    db.refresh(db_antrian)
    
    return db_antrian

async def insertantrianadmisi(db: Session):
    # Ambil no_antrian terakhir berdasarkan tanggal sekarang
    today = datetime.date.today()
    
    # Query untuk mencari nomor antrean terbesar di tanggal sekarang
    last_antrian = db.query(generate.AntrianAdmisi.no_antrian)\
                     .filter(generate.AntrianAdmisi.tgl_kunjungan == today)\
                     .order_by(generate.AntrianAdmisi.no_antrian.desc())\
                     .first()

    # Tentukan nomor antrean: jika tidak ada, mulai dari 1
    if last_antrian is None:
        no_antrian = 1
    else:
        no_antrian = last_antrian[0] + 1

    # Buat entri baru untuk antrian_admisi
    db_antrian = generate.AntrianAdmisi(
        no_antrian=no_antrian,
        tgl_kunjungan=today,
        flag='1',
        loket=None
    )
    
    # Simpan ke database
    db.add(db_antrian)
    db.commit()
    db.refresh(db_antrian)
    
    return db_antrian

async def insert_taskid(db: Session, kodebooking: str, hit: str, request: str, response: str, status: str):
    # Menggunakan RETURNING untuk mengambil id yang baru saja dimasukkan
    query = (
        f"INSERT INTO taskid (kodebooking, hit, request, response, status) "
        f"VALUES ('{kodebooking}', '{hit}', '{request}', '{response}', '{status}') RETURNING id;"
    )
    result = db.execute(query)
    db.commit()
    # Mengambil id hasil insert
    inserted_id = result.fetchone()[0]
    return inserted_id