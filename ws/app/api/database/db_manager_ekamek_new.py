from sqlalchemy.orm import Session
from app.api.database.db_ekamek import engine,Session
import app.api.models.models as models
models.Base.metadata.create_all(bind=engine)
import app.api.database.generate as generate
import datetime
from functools import wraps
import re



# added untuk terhindar dari hack character
def sanitize_input(func):
    @wraps(func)
    async def wrapper(db: Session, *args, **kwargs):
        sanitized_args = [re.sub(r'[^a-zA-Z0-9]', '', str(arg)) for arg in args]
        sanitized_kwargs = {key: re.sub(r'[^a-zA-Z0-9]', '', str(value)) for key, value in kwargs.items()}
        return await func(db, *sanitized_args, **sanitized_kwargs)

    return wrapper

@sanitize_input
async def daftarulang(db:Session,kodebooking:str):
    query = db.execute(f"SELECT a.no_register,(SELECT CASE WHEN b.racikan = '1' THEN 'Racikan' ELSE 'Non Racikan' END AS racikan_status FROM resep_pasien b WHERE b.no_register = a.no_register limit 1) FROM daftar_ulang_irj a where a.noreservasi = '{kodebooking}'").first()
    return query

@sanitize_input
async def carinamapoli(db:Session,poli:str):
    url = f"SELECT id_poli FROM poliklinik WHERE poli_bpjs ='{poli}' "
    return db.execute(url).first()

@sanitize_input
async def carinamadokter(db:Session,kodedokter:str):
    url = f"select nm_dokter,id_dokter from data_dokter where kode_dpjp_bpjs = '{kodedokter}'"
    return db.execute(url).first()

@sanitize_input
async def caridatapasien(db:Session,norm:str):
    if norm == '':
        return None
    url = f"select no_medrec,nama,no_cm from data_pasien where no_kartu = '{norm}'"
    return db.execute(url).first()


@sanitize_input
async def caridatapasiennik(db:Session,nik:str):
    url = f"select no_medrec,nama,no_cm from data_pasien where no_identitas = '{nik}'"
    return db.execute(url).first()

@sanitize_input
async def jadwaloperasirs(db:Session,tglawal:str,tglakhir:str):
    url = f"""
    SELECT 
    --no_register as kodebooking,
    --(no_register as kodebooking),
    case when (select noreservasi as kodebooking from daftar_ulang_irj where daftar_ulang_irj.no_register = pemeriksaan_operasi.no_register)
    	is not null then (select noreservasi as kodebooking from daftar_ulang_irj where daftar_ulang_irj.no_register = pemeriksaan_operasi.no_register)
    else (select no_register as kodebooking)
	end,
    TO_CHAR(tgl_kunjungan,'YYYY-MM-dd') as tanggaloperasi,jenis_tindakan as jenistindakan,
    case when SUBSTRING(no_register,0,3) = 'RI' then
    (select (select poli_bpjs from daftar_ulang_irj left join poliklinik on poliklinik.id_poli = daftar_ulang_irj.id_poli where no_register = noregasal) from pasien_iri where no_ipd = pemeriksaan_operasi.no_register ) else 
    (select (select poli_bpjs from poliklinik where poliklinik.id_poli = daftar_ulang_irj.id_poli) from daftar_ulang_irj where no_register = pemeriksaan_operasi.no_register)
    end as kodepoli,

    case when SUBSTRING(no_register,0,3) = 'RI' then
    (select (select nm_poli from daftar_ulang_irj left join poliklinik on poliklinik.id_poli = daftar_ulang_irj.id_poli where no_register = noregasal) from pasien_iri where no_ipd = pemeriksaan_operasi.no_register ) else 
    (select (select nm_poli from poliklinik where poliklinik.id_poli = daftar_ulang_irj.id_poli) from daftar_ulang_irj where no_register = pemeriksaan_operasi.no_register)
    end as namapoli,
    COALESCE(terlaksana::integer,0) as terlaksana,
    (select no_kartu from data_pasien where no_medrec = pemeriksaan_operasi.no_medrec) as nopeserta,
    --extract(epoch from tgl_kunjungan) as lastupdate
	(select (EXTRACT(epoch FROM tgl_kunjungan) * 1000)::bigint as lastupdate from daftar_ulang_irj where daftar_ulang_irj.no_register = pemeriksaan_operasi.no_register) 
    FROM "pemeriksaan_operasi"
	where to_char(tgl_kunjungan,'YYYYMMdd') >= '{tglawal}' and to_char(tgl_kunjungan,'YYYYMMdd') <= '{tglakhir}'
    """
    return db.execute(url).all()


@sanitize_input
async def jadwaloperasirs2(db:Session,nopeserta:str):
    url = f"""
   
    SELECT 
    --(no_register as kodebooking),
    case when (select noreservasi as kodebooking from daftar_ulang_irj where daftar_ulang_irj.no_register = pemeriksaan_operasi.no_register)
    	is not null then (select noreservasi as kodebooking from daftar_ulang_irj where daftar_ulang_irj.no_register = pemeriksaan_operasi.no_register)
    else (select no_register as kodebooking)
	end,
    TO_CHAR(tgl_kunjungan,'YYYY-MM-dd') as tanggaloperasi,jenis_tindakan as jenistindakan,
    case when SUBSTRING(no_register,0,3) = 'RI' then
    (select (select poli_bpjs from daftar_ulang_irj left join poliklinik on poliklinik.id_poli = daftar_ulang_irj.id_poli where no_register = noregasal) from pasien_iri where no_ipd = pemeriksaan_operasi.no_register ) else 
    (select (select poli_bpjs from poliklinik where poliklinik.id_poli = daftar_ulang_irj.id_poli) from daftar_ulang_irj where no_register = pemeriksaan_operasi.no_register)
    end as kodepoli,

    case when SUBSTRING(no_register,0,3) = 'RI' then
    (select (select nm_poli from daftar_ulang_irj left join poliklinik on poliklinik.id_poli = daftar_ulang_irj.id_poli where no_register = noregasal) from pasien_iri where no_ipd = pemeriksaan_operasi.no_register ) else 
    (select (select nm_poli from poliklinik where poliklinik.id_poli = daftar_ulang_irj.id_poli) from daftar_ulang_irj where no_register = pemeriksaan_operasi.no_register)
    end as namapoli,
    COALESCE(terlaksana::integer,0) as terlaksana,
    (select no_kartu from data_pasien where no_medrec = pemeriksaan_operasi.no_medrec) as nopeserta,
    --(select EXTRACT(epoch FROM tgl_kunjungan) * 1000) as lastupdate
    (select (EXTRACT(epoch FROM tgl_kunjungan) * 1000)::bigint as lastupdate from daftar_ulang_irj where daftar_ulang_irj.no_register = pemeriksaan_operasi.no_register) 

    FROM "pemeriksaan_operasi" left join data_pasien on data_pasien.no_medrec = pemeriksaan_operasi.no_medrec
	where no_kartu = '{nopeserta}';
    """
    return db.execute(url).all()
 
@sanitize_input
async def grab_antrian_farmasi(db:Session,kodebooking:str):
    url = f"""
    SELECT (select count(*)
    from resep_dokter 
    where no_register = daftar_ulang_irj.no_register 
    and racikan is not null) FROM daftar_ulang_irj 
    where noreservasi = '{kodebooking}';
    """
    return db.execute(url).first()

@sanitize_input
async def checkPasienExist(db:Session,nomorkartu):
    db_antrian = db.execute(f"SELECT no_cm FROM data_pasien where no_kartu = '{nomorkartu}'").first()
    return db_antrian

@sanitize_input
async def cekBerapaBanyakKunjungan(db:Session,nomedrec):
    db_antrian = db.execute(f"SELECT count(*) FROM daftar_ulang_irj where no_medrec = '{nomedrec}'").first()
    return db_antrian

async def insertpasienbaru(db:Session,payload:models.Pasienbaru):
    try:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # query_max_no_cm = db.execute(
        #     "SELECT IFNULL(MAX(a.no_cm)+1, 1000000) AS last_cm FROM (SELECT * FROM data_pasien) AS a"
        # ).first()
        # next_no_cm = query_max_no_cm.last_cm
        db.execute(f"""INSERT INTO data_pasien 
            (no_kartu,no_identitas,no_kk,nama,sex,tgl_lahir,
            no_hp,alamat,rw,rt,tgl_daftar,xupdate,xuser)
             VALUES ('{payload.nomorkartu}', '{payload.nik}','{payload.nomorkk}',
             '{payload.nama}','{payload.jeniskelamin}','{payload.tanggallahir}',
             '{payload.nohp}','{payload.alamat}','{payload.rw}','{payload.rt}',
             '{current_time}','{current_time}','ANTROL')"""
        )
        db.commit()
        refreshed_result = db.execute(
            f"SELECT no_medrec FROM data_pasien WHERE no_kartu = '{payload.nomorkartu}'"
        ).first()
        # print(refreshed_result)
        
        nocm = str(refreshed_result[0]).rjust(8, '0')
        print(nocm)
        db.execute(f"""UPDATE data_pasien set no_cm = '{nocm}'
             where no_medrec = {refreshed_result[0]}"""
        )
        db.commit()
        return nocm # Indicates successful insertion
    except Exception as e:
        db.rollback()  # Rollback changes if an exception occurs
        print(f"Error inserting data: {e}")
        return False  # Indicates failure