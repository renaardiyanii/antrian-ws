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
    url = f"select no_medrec,nama,no_cm from data_pasien where TRIM(no_kartu) = TRIM('{norm}')"
    return db.execute(url).first()


@sanitize_input
async def caridatapasiennik(db:Session,nik:str):
    url = f"select no_medrec,nama,no_cm from data_pasien where no_identitas = '{nik}'"
    return db.execute(url).first()

@sanitize_input
async def caridatapasienno_cm(db:Session,nik:str):
    url = f"select no_medrec,nama,no_cm from data_pasien where no_cm = '{nik}'"
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

    urlnew = f"""
    -- Bagian 1: Untuk pasien dari IRNA ANTRIAN
SELECT 
    COALESCE(
        (SELECT du.noreservasi FROM daftar_ulang_irj du WHERE du.no_register = c.no_register_asal), 
        c.noreservasi
    ) AS kodebooking,
    a.tgl_jadwal_ok AS tanggaloperasi,
    COALESCE(
        (SELECT po.jenis_tindakan FROM pemeriksaan_operasi po WHERE po.no_register = a.no_register LIMIT 1), 
        '-'
    ) AS jenis_tindakan,
    COALESCE(
        (SELECT p.poli_bpjs FROM daftar_ulang_irj du JOIN poliklinik p ON du.id_poli = p.id_poli WHERE du.no_register = c.no_register_asal LIMIT 1),
        '-'
    ) AS kodepoli,
    COALESCE(
        (SELECT p.nm_poli FROM daftar_ulang_irj du JOIN poliklinik p ON du.id_poli = p.id_poli WHERE du.no_register = c.no_register_asal LIMIT 1),
        '-'
    ) AS namapoli,
    a.status AS terlaksana, 
    (EXTRACT(EPOCH FROM a.xupdate) * 1000)::bigint AS lastupdate,
    b.no_kartu AS nopeserta
FROM 
    operasi_header a,
    data_pasien b, 
    irna_antrian c
WHERE 
    a.no_reservasi = c.noreservasi
    AND b.no_medrec = c.no_medrec
    -- Mengubah filter menjadi rentang tanggal
    AND a.tgl_jadwal_ok BETWEEN '{tglawal}' AND '{tglakhir}'

UNION

-- Bagian 2: Untuk pasien dari PASIEN IRI (Rawat Inap)
SELECT 
    COALESCE(
        (SELECT du.noreservasi FROM daftar_ulang_irj du WHERE du.no_register = c.noregasal), 
        a.no_register
    ) AS kodebooking,
    a.tgl_jadwal_ok AS tanggaloperasi,
    COALESCE(
        (SELECT po.jenis_tindakan FROM pemeriksaan_operasi po WHERE po.no_register = a.no_register LIMIT 1), 
        '-'
    ) AS jenis_tindakan,
    COALESCE(
        (SELECT p.poli_bpjs FROM daftar_ulang_irj du JOIN poliklinik p ON du.id_poli = p.id_poli WHERE du.no_register = c.noregasal LIMIT 1),
        '-'
    ) AS kodepoli,
    COALESCE(
        (SELECT p.nm_poli FROM daftar_ulang_irj du JOIN poliklinik p ON du.id_poli = p.id_poli WHERE du.no_register = c.noregasal LIMIT 1),
        '-'
    ) AS namapoli,
    a.status AS terlaksana, 
    (EXTRACT(EPOCH FROM a.xupdate) * 1000)::bigint AS lastupdate,
    b.no_kartu AS nopeserta
FROM 
    operasi_header a, 
    data_pasien b, 
    pasien_iri c
WHERE 
    a.no_register = c.no_ipd
    AND b.no_medrec = c.no_medrec
    -- Mengubah filter menjadi rentang tanggal
    AND a.tgl_jadwal_ok BETWEEN '{tglawal}' AND '{tglakhir}'

UNION

-- Bagian 3: Untuk pasien dari DAFTAR ULANG IRJ (Rawat Jalan)
SELECT 
    COALESCE(c.noreservasi, c.no_register) AS kodebooking,
    a.tgl_jadwal_ok AS tanggaloperasi,
    COALESCE(
        (SELECT po.jenis_tindakan FROM pemeriksaan_operasi po WHERE po.no_register = a.no_register LIMIT 1), 
        '-'
    ) AS jenis_tindakan,
    COALESCE(
        (SELECT p.poli_bpjs FROM poliklinik p WHERE p.id_poli = c.id_poli LIMIT 1),
        '-'
    ) AS kodepoli,
    COALESCE(
        (SELECT p.nm_poli FROM poliklinik p WHERE p.id_poli = c.id_poli LIMIT 1),
        '-'
    ) AS namapoli,
    a.status AS terlaksana, 
    (EXTRACT(EPOCH FROM a.xupdate) * 1000)::bigint AS lastupdate,
    b.no_kartu AS nopeserta
FROM 
    operasi_header a, 
    data_pasien b, 
    daftar_ulang_irj c
WHERE 
    a.no_register = c.no_register
    AND b.no_medrec = c.no_medrec
    -- Mengubah filter menjadi rentang tanggal
    AND a.tgl_jadwal_ok BETWEEN '{tglawal}' AND '{tglakhir}';
    """
    return db.execute(urlnew).all()

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

    urlnew = f"""
    -- Bagian 1: Untuk pasien dari IRNA ANTRIAN
SELECT 
    COALESCE(
        (SELECT du.noreservasi FROM daftar_ulang_irj du WHERE du.no_register = c.no_register_asal), 
        c.noreservasi
    ) AS kodebooking,
    a.tgl_jadwal_ok AS tanggaloperasi,
    COALESCE(
        (SELECT po.jenis_tindakan FROM pemeriksaan_operasi po WHERE po.no_register = a.no_register LIMIT 1), 
        '-'
    ) AS jenis_tindakan,
    COALESCE(
        (SELECT p.poli_bpjs FROM daftar_ulang_irj du JOIN poliklinik p ON du.id_poli = p.id_poli WHERE du.no_register = c.no_register_asal LIMIT 1),
        '-'
    ) AS kodepoli,
    COALESCE(
        (SELECT p.nm_poli FROM daftar_ulang_irj du JOIN poliklinik p ON du.id_poli = p.id_poli WHERE du.no_register = c.no_register_asal LIMIT 1),
        '-'
    ) AS namapoli,
    a.status AS terlaksana, 
    (EXTRACT(EPOCH FROM a.xupdate) * 1000)::bigint AS lastupdate,
    b.no_kartu AS nopeserta
FROM 
    operasi_header a,
    data_pasien b, 
    irna_antrian c
WHERE 
    a.no_reservasi = c.noreservasi
    AND b.no_medrec = c.no_medrec
    -- Mengubah filter menjadi berdasarkan nomor peserta
    AND b.no_kartu = '{nopeserta}'

UNION

-- Bagian 2: Untuk pasien dari PASIEN IRI (Rawat Inap)
SELECT 
    COALESCE(
        (SELECT du.noreservasi FROM daftar_ulang_irj du WHERE du.no_register = c.noregasal), 
        a.no_register
    ) AS kodebooking,
    a.tgl_jadwal_ok AS tanggaloperasi,
    COALESCE(
        (SELECT po.jenis_tindakan FROM pemeriksaan_operasi po WHERE po.no_register = a.no_register LIMIT 1), 
        '-'
    ) AS jenis_tindakan,
    COALESCE(
        (SELECT p.poli_bpjs FROM daftar_ulang_irj du JOIN poliklinik p ON du.id_poli = p.id_poli WHERE du.no_register = c.noregasal LIMIT 1),
        '-'
    ) AS kodepoli,
    COALESCE(
        (SELECT p.nm_poli FROM daftar_ulang_irj du JOIN poliklinik p ON du.id_poli = p.id_poli WHERE du.no_register = c.noregasal LIMIT 1),
        '-'
    ) AS namapoli,
    a.status AS terlaksana, 
    (EXTRACT(EPOCH FROM a.xupdate) * 1000)::bigint AS lastupdate,
    b.no_kartu AS nopeserta
FROM 
    operasi_header a, 
    data_pasien b, 
    pasien_iri c
WHERE 
    a.no_register = c.no_ipd
    AND b.no_medrec = c.no_medrec
    -- Mengubah filter menjadi berdasarkan nomor peserta
    AND b.no_kartu = '{nopeserta}'

UNION

-- Bagian 3: Untuk pasien dari DAFTAR ULANG IRJ (Rawat Jalan)
SELECT 
    COALESCE(c.noreservasi, c.no_register) AS kodebooking,
    a.tgl_jadwal_ok AS tanggaloperasi,
    COALESCE(
        (SELECT po.jenis_tindakan FROM pemeriksaan_operasi po WHERE po.no_register = a.no_register LIMIT 1), 
        '-'
    ) AS jenis_tindakan,
    COALESCE(
        (SELECT p.poli_bpjs FROM poliklinik p WHERE p.id_poli = c.id_poli LIMIT 1),
        '-'
    ) AS kodepoli,
    COALESCE(
        (SELECT p.nm_poli FROM poliklinik p WHERE p.id_poli = c.id_poli LIMIT 1),
        '-'
    ) AS namapoli,
    a.status AS terlaksana, 
    (EXTRACT(EPOCH FROM a.xupdate) * 1000)::bigint AS lastupdate,
    b.no_kartu AS nopeserta
FROM 
    operasi_header a, 
    data_pasien b, 
    daftar_ulang_irj c
WHERE 
    a.no_register = c.no_register
    AND b.no_medrec = c.no_medrec
    -- Mengubah filter menjadi berdasarkan nomor peserta
    AND b.no_kartu = '{nopeserta}';
    """
    return db.execute(urlnew).all()
 
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
async def checkPasienExistNik(db:Session,nomorkartu):
    db_antrian = db.execute(f"SELECT no_cm FROM data_pasien where no_identitas = '{nomorkartu}'").first()
    return db_antrian

# async def insertpasienbaru(db:Session,payload:models.Pasienbaru):
#     try:
#         current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         query_max_no_cm = db.execute(
#             "SELECT IFNULL(MAX(a.no_cm)+1, 1000000) AS last_cm FROM (SELECT * FROM data_pasien) AS a"
#         ).first()
#         next_no_cm = query_max_no_cm.last_cm
#         db.execute(f"""INSERT INTO data_pasien 
#             (no_kartu,no_identitas,no_kk,nama,sex,tgl_lahir,
#             no_hp,alamat,rw,rt,tgl_daftar,xupdate,xuser,no_cm)
#              VALUES ('{payload.nomorkartu}', '{payload.nik}','{payload.nomorkk}',
#              '{payload.nama}','{payload.jeniskelamin}','{payload.tanggallahir}',
#              '{payload.nohp}','{payload.alamat}','{payload.rw}','{payload.rt}',
#              '{current_time}','{current_time}','ANTROL','{next_no_cm}')"""
#         )
#         db.commit()
#         refreshed_result = db.execute(
#             f"SELECT no_cm FROM data_pasien WHERE no_kartu = '{payload.nomorkartu}'"
#         ).first()
#         return refreshed_result # Indicates successful insertion
#     except Exception as e:
#         db.rollback()  # Rollback changes if an exception occurs
#         print(f"Error inserting data: {e}")
#         return False  # Indicates failure

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
        
        nocm = str(refreshed_result[0]).rjust(6, '0')
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



async def insertpasienbarunewnonjkn(db:Session,payload:models.Pasienbarunew):
    try:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # query_max_no_cm = db.execute(
        #     "SELECT IFNULL(MAX(a.no_cm)+1, 1000000) AS last_cm FROM (SELECT * FROM data_pasien) AS a"
        # ).first()
        # next_no_cm = query_max_no_cm.last_cm
        db.execute(f"""INSERT INTO data_pasien 
            (no_identitas,nama,xupdate,xuser)
             VALUES ('{payload.nomorkartu}', 
             '{payload.nama}','{current_time}','ANTROL')"""
        )
        db.commit()
        refreshed_result = db.execute(
            f"SELECT no_medrec FROM data_pasien WHERE no_identitas = '{payload.nomorkartu}'"
        ).first()
        # print(refreshed_result)
        
        nocm = str(refreshed_result[0]).rjust(6, '0')
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


async def insertpasienbarunew(db:Session,payload:models.Pasienbarunew):
    try:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # query_max_no_cm = db.execute(
        #     "SELECT IFNULL(MAX(a.no_cm)+1, 1000000) AS last_cm FROM (SELECT * FROM data_pasien) AS a"
        # ).first()
        # next_no_cm = query_max_no_cm.last_cm
        db.execute(f"""INSERT INTO data_pasien 
            (no_kartu,nama,xupdate,xuser)
             VALUES ('{payload.nomorkartu}', 
             '{payload.nama}','{current_time}','ANTROL')"""
        )
        db.commit()
        refreshed_result = db.execute(
            f"SELECT no_medrec FROM data_pasien WHERE no_kartu = '{payload.nomorkartu}'"
        ).first()
        # print(refreshed_result)
        
        nocm = str(refreshed_result[0]).rjust(6, '0')
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


@sanitize_input
async def caridatapoliklinik(db:Session,poli_bpjs):
    db_antrian = db.execute(f"SELECT id_poli,nm_poli from poliklinik where poliklinik.poli_bpjs = '{poli_bpjs}'").first()
    return db_antrian

@sanitize_input
async def caridatadokter(db:Session,dokter_bpjs):
    db_antrian = db.execute(f"SELECT id_dokter,nm_dokter from data_dokter where data_dokter.kode_dpjp_bpjs = '{dokter_bpjs}'").first()
    return db_antrian


@sanitize_input
async def carinomedrecberdasarnorm(db:Session,no_cm):
    db_antrian = db.execute(f"SELECT no_medrec from data_pasien where no_cm = '{no_cm}'").first()
    return db_antrian


@sanitize_input
async def generateumur(db:Session,no_medrec):
    return db.execute(f"""SELECT
					DATE_PART( 'year', now( ) ) - DATE_PART( 'year', tgl_lahir ) AS umurday,
					EXTRACT(YEAR FROM age(tgl_lahir)) AS tahun, 
					EXTRACT(MONTH FROM age(tgl_lahir)) AS bulan,
					EXTRACT(DAY FROM age(tgl_lahir)) AS hari,
					age( now(), tgl_lahir ) 
				FROM
					data_pasien 
				WHERE
					no_medrec = '{no_medrec}'""").first()


@sanitize_input
async def get_detail_tindakan_new(db:Session,idtindakan):
    return db.execute(f"""SELECT
					idtindakan,
					nmtindakan,
					tarif,
					tmno 
				FROM
					jenis_tindakan_new 
				WHERE
					idtindakan = '{idtindakan}'""").first()


@sanitize_input
async def get_vtot(db:Session,noregister):
    return db.execute(f"""SELECT vtot FROM daftar_ulang_irj where no_register='{noregister}'""").first()


async def update_vtot(db:Session, data:dict):
    insert_query = f"""
            UPDATE daftar_ulang_irj 
            SET vtot = {data['vtot']}
            WHERE no_register = '{data['no_register']}'
        """
    db.execute(insert_query)
    
    # Step 7: Commit the transaction
    db.commit()
    return True


async def insert_tindakan(db:Session, data:dict):
    insert_query = f"""
            INSERT INTO pelayanan_poli (
            no_register,
            idtindakan, 
            tgl_kunjungan,
            nmtindakan,
            tmno,
            biaya_tindakan,
            biaya_alkes,
            qtyind,
            vtot
            )
            VALUES (
                '{data["no_register"]}',
                '{data["idtindakan"]}',
                '{data["tgl_kunjungan"]}',
                '{data["nmtindakan"]}',
                '{data["tmno"]}',
                '{data["biaya_tindakan"]}',
                '{data["biaya_alkes"]}',
                '{data["qtyind"]}',
                '{data["vtot"]}'
            )
        """
    db.execute(insert_query)
    
    # Step 7: Commit the transaction
    db.commit()
    return True

async def create_registration(db: Session, data: dict):
    # try:
        # Start a new transaction
    # db.begin()
    # Simulate the query for generating 'no_register'
    no_register_query = """
        SELECT 'RJ' || TO_CHAR(now(),'YY') || LPAD((CAST(COALESCE((
            SELECT RIGHT(MAX(no_register), 6) FROM daftar_ulang_irj), '000001') AS INTEGER) + 1)::VARCHAR, 6, '0') AS no_register
    """
    no_register_result = db.execute(no_register_query).first()
    no_register = no_register_result['no_register'] if no_register_result else None

    # Step 3: Insert `poli_ke`
    poli_ke_query = f"""
        SELECT (COUNT(*)) + 1 AS count_poli
        FROM daftar_ulang_irj AS a
        LEFT JOIN poliklinik AS b ON a.id_poli = b.id_poli
        WHERE a.no_medrec = {data['no_medrec']}
        AND TO_CHAR(a.tgl_kunjungan, 'YYYY-MM-DD') = TO_CHAR(now(), 'YYYY-MM-DD')
    """
    poli_ke_result = db.execute(poli_ke_query).first()
    poli_ke = poli_ke_result['count_poli'] if poli_ke_result else 1

    # Step 4: Set the remaining fields in `data`
    data['no_register'] = no_register
    data['poli_ke'] = poli_ke
    print(data)
    # return data
    try:
        no_antrian = int(data.get("noantrian", 1))
    except ValueError:
        no_antrian = 1
    # data['no_antran'] = data['noantrian']

    # Step 5: Insert the registration data
    insert_query = f"""
        INSERT INTO daftar_ulang_irj (
    no_register, 
    tgl_kunjungan,
    jns_kunj,
    ublnrj,
    uharirj,
    umurrj,
    cara_kunj,
    asal_rujukan,
    no_rujukan,
    kelas_pasien,
    cara_bayar,
    id_poli,
    status,
    no_sep,
    cetak_kwitansi,
    xupdate,
    xuser,
    diagnosa,
    no_antrian,
    poli_ke,
    kll_tgl_kejadian,
    id_dokter,
    no_medrec,
    id_kontraktor,
    noreservasi,
    cara_dtg
    )
    VALUES (
        '{data.get("no_register", "")}',
        '{data.get("tgl_kunjungan", "")}',
        '{data.get("jns_kunj", "")}',
        '{int(data.get("ublnrj", 0))}',
        '{int(data.get("uharirj", 0))}',
        '{int(data.get("umurrj", 0))}',
        '{data.get("cara_kunj", "")}',
        '{data.get("asal_rujukan", "")}',
        '{data.get("no_rujukan", "")}',
        '{data.get("kelas_pasien", "")}',
        '{data.get("cara_bayar", "")}',
        '{data.get("id_poli", "")}',
        '0',
        '',
        '0',
        '{data.get("xupdate", "")}',
        '1',
        '{data.get("diagnosa", "")}',
        '{no_antrian}',
        '{data.get("poli_ke", "")}',
        '{data.get("kll_tgl_kejadian", "")}',
        '{data.get("id_dokter", "")}',
        '{data.get("no_medrec", "")}',
        '{data.get("id_kontraktor", "")}',
        '{data.get("noreservasi", "")}',
        '{data.get("cara_dtg", "")}'
    )
    """
    db.execute(insert_query)
    
    # Step 7: Commit the transaction
    db.commit()

    return data['no_register']

    # except Exception as e:
    #     # Rollback transaction if there was an error
    #     db.rollback()
    #     return False
        # raise HTTPException(status_code=500, detail=f"Transaction failed: {str(e)}")
    
async def register_bpjs(db:Session, data:dict):
    insert_query = f"""
            INSERT INTO bpjs_sep (
            no_medrec, 
            tgl_sep,
            no_register,
            no_kartu,
            kelasrawat,
            asalrujukan,
            tglrujukan,
            norujukan,
            ppkrujukan,
            diagawal,
            politujuan,
            tujuankunj,
            flagprocedure,
            kdpenunjang,
            assesmentpel,
            nosurat,
            dpjpsurat,
            dpjplayan,
            namadokter,
            namafaskes,
            "user",
            notelp,
            catatan,
            prb,
            katarak
            )
            VALUES (
                '{data["no_medrec"]}',
                '{data["tgl_sep"]}',
                '{data["no_register"]}',
                '{data["no_kartu"]}',
                '{data["kelasrawat"]}',
                '{data["asalrujukan"]}',
                '{data["tglrujukan"]}',
                '{data["norujukan"]}',
                '{data["ppkrujukan"]}',
                '{data["diagawal"]}',
                '{data["politujuan"]}',
                '{data["tujuankunj"]}',
                '{data["flagprocedure"]}',
                '{data["kdpenunjang"]}',
                '{data["assesmentpel"]}',
                '{data["nosurat"]}',
                '{data["dpjpsurat"]}',
                '{data["dpjplayan"]}',
                '{data["namadokter"]}',
                '{data["namafaskes"]}',
                '{data["user"]}',
                '{data["notelp"]}',
                '{data["catatan"]}',
                '{data["prb"]}',
                '{data["katarak"]}'
            )
        """
    db.execute(insert_query)
    
    # Step 7: Commit the transaction
    db.commit()
    return True
    

async def tambahhistoryantrian(db:Session, payload : models.ChekinAntrian):
    # ambil no_register berdasarkan kode booking
    no_register_query = f"""
        SELECT no_register
        FROM daftar_ulang_irj
        WHERE noreservasi = '{payload.kodebooking}'
    """
    no_register_result = db.execute(no_register_query).first()
    no_register = no_register_result['no_register'] if no_register_result else None


    insert_query = f"""
            INSERT INTO history_antrol (
            no_register,
            kodebooking,
            aksi)
            VALUES (
                '{no_register}',
                '{payload.kodebooking}',
                'checkin'
            )
        """
    db.execute(insert_query)
    
    # Step 7: Commit the transaction
    db.commit()
    return True

async def tambahhistoryantriandirect(db:Session, kodebooking: str):
    # ambil no_register berdasarkan kode booking
    no_register_query = f"""
        SELECT no_register
        FROM daftar_ulang_irj
        WHERE noreservasi = '{kodebooking}'
    """
    no_register_result = db.execute(no_register_query).first()
    no_register = no_register_result['no_register'] if no_register_result else None


    insert_query = f"""
            INSERT INTO history_antrol (
            no_register,
            kodebooking,
            aksi)
            VALUES (
                '{no_register}',
                '{kodebooking}',
                'checkin'
            )
        """
    db.execute(insert_query)
    
    # Step 7: Commit the transaction
    db.commit()
    return True


async def getnoantrianfarmasi(db: Session, kodebooking: str):
    # Step 1: Cek jika kodebooking adalah nomor RM dengan panjang 6
    if len(kodebooking) == 6:
        # Step 2: Ambil no_register dari tabel daftar_ulang_irj
        daftar_ulang_query = """
            SELECT noreservasi
            FROM daftar_ulang_irj
            WHERE no_medrec = :kodebooking
            ORDER BY no_register DESC
            LIMIT 1
        """
        daftar_ulang_result = db.execute(daftar_ulang_query, {"kodebooking": kodebooking}).first()
        
        if daftar_ulang_result:
            # Simpan hasil noreservasi ke variabel kodebooking
            kodebooking = daftar_ulang_result["noreservasi"]

    # Step 3: Cari noantrian di tabel history_antrol berdasarkan kodebooking
    no_register_query = """
        SELECT noantrian
        FROM history_antrol
        WHERE aksi = 'farmasi'
        AND kodebooking = :kodebooking
    """
    no_register_result = db.execute(no_register_query, {"kodebooking": kodebooking}).first()

    # Step 4: Jika data ditemukan, kembalikan noantrian; jika tidak, kembalikan None
    no_register = no_register_result["noantrian"] if no_register_result else None
    if no_register:
        # Step 4: Update kolom checkin_farmasi menjadi '1' untuk kodebooking terkait
        update_query = """
            UPDATE history_antrol
            SET checkin_farmasi = '1'
            WHERE aksi = 'farmasi'
            AND kodebooking = :kodebooking
        """
        db.execute(update_query, {"kodebooking": kodebooking})
        db.commit()  # Pastikan perubahan disimpan ke database

    # kemudian update history_antrol tersebut 

    return no_register


async def tambahhistoryantriandirectfarmasi(db:Session, kodebooking: str):
    book = kodebooking
    if len(kodebooking) == 6:
        # Query untuk mengambil noreservasi berdasarkan no_medrec
        no_reservasi_query = f"""
            SELECT noreservasi
            FROM daftar_ulang_irj
            WHERE no_medrec = '{kodebooking}' ORDER BY no_register DESC
        """
        no_reservasi_result = db.execute(no_reservasi_query).first()
        book = no_reservasi_result['noreservasi'] if no_reservasi_result else None
    
    # ambil no_register berdasarkan kode booking
    no_register_query = f"""
        SELECT no_register
        FROM daftar_ulang_irj
        WHERE noreservasi = '{book}'
    """
    no_register_result = db.execute(no_register_query).first()
    no_register = no_register_result['no_register'] if no_register_result else None


    insert_query = f"""
            INSERT INTO history_antrol (
            no_register,
            kodebooking,
            aksi,noantrian
            )
            VALUES (
                '{no_register}',
                '{book}',
                'farmasi',
                (
                    SELECT COUNT(*) + 1
                    FROM history_antrol
                    WHERE to_char(dt, 'YYYY-MM-DD') = to_char(CURRENT_DATE, 'YYYY-MM-DD')
                    and aksi='farmasi'
                )
            )
        """
    db.execute(insert_query)
    
    # Step 7: Commit the transaction
    db.commit()
    return True


async def batalantrianhmis(db:Session, kodebooking: str):
    # ambil no_register berdasarkan kode booking
    no_register_query = f"""
        update daftar_ulang_irj
        set ket_pulang = 'BATAL_PELAYANAN_POLI'
        WHERE noreservasi = '{kodebooking}'
    """
    db.execute(no_register_query)
    
    # Step 7: Commit the transaction
    db.commit()
    return True

@sanitize_input
async def nomorantrian(db:Session,idpoli:str,tglkunjungan: str,iddokter: str):
    url = f"SELECT COUNT(*) + 1 FROM daftar_ulang_irj WHERE TO_CHAR(tgl_kunjungan, 'YYYY-MM-DD') = TO_CHAR('{tglkunjungan}'::date, 'YYYY-MM-DD') AND id_poli = '{idpoli}'"
    return db.execute(url).first()

@sanitize_input
async def nomorantriandebug(db:Session,idpoli:str,tglkunjungan: str,iddokter: str):
    url = f"SELECT COUNT(*) + 1 FROM daftar_ulang_irj WHERE TO_CHAR(tgl_kunjungan, 'YYYY-MM-DD') = TO_CHAR('{tglkunjungan}'::date, 'YYYY-MM-DD') AND id_poli = '{idpoli}' and id_dokter = {iddokter}"
    return db.execute(url).first()


# hasil nm_dokter,id_dokter, id_poli
@sanitize_input
async def carinamadokter_new(db:Session,kodedokter:str):
    url = f"select nm_dokter,id_dokter,(select id_poli from dokter_poli where dokter_poli.id_dokter = data_dokter.id_dokter limit 1) from data_dokter where kode_dpjp_bpjs = '{kodedokter}' and deleted = 0"
    return db.execute(url).first()

@sanitize_input
async def carinamadokter_new_v2(db:Session,kodedokter:str,poli_bpjs:str):
    url = f"""
    SELECT 
        d.nm_dokter,
        d.id_dokter,
        dp.id_poli
    FROM data_dokter d
    JOIN dokter_poli dp 
        ON dp.id_dokter = d.id_dokter
    JOIN poliklinik p 
        ON p.id_poli = dp.id_poli
    WHERE d.kode_dpjp_bpjs = '{kodedokter}'
    AND d.deleted = 0
    AND p.poli_bpjs = '{poli_bpjs}'
    LIMIT 1;

    """
    return db.execute(url).first()

async def cekPasienbarulama(db:Session,nomorkartu):
    cekPasienbarulama = db.execute(f"SELECT * FROM daftar_ulang_irj where no_medrec = (select dp.no_medrec from data_pasien as dp WHERE dp.no_kartu = '{nomorkartu}');").first()
    return cekPasienbarulama