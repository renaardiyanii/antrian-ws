from sqlalchemy import BigInteger, Boolean, CHAR, Column, Date, DateTime, Float, ForeignKey, Identity, Integer, JSON, Numeric, SmallInteger, String, Table, Text, Time, text
from sqlalchemy.dialects.postgresql import INTERVAL, TIMESTAMP
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()
metadata = Base.metadata

auth_bpjs = Table(
        'auth_bpjs',
        metadata,
        Column('id',Integer,primary_key = True),
        Column('username',String(50)),
        Column('password',String(250)),
)


class AntrianPoli(Base):
    __tablename__ = 'antrian_poli'

    id = Column(Integer, primary_key=True, server_default=text("nextval('antrian_poli_id_seq'::regclass)"))
    nomorkartu = Column(String(50))
    nik = Column(String(50))
    nohp = Column(String(15))
    kodepoli = Column(String(10))
    norm = Column(String(50))
    tanggalperiksa = Column(String(50))
    kodedokter = Column(Integer)
    jampraktek = Column(String(40))
    jeniskunjungan = Column(Integer)
    nomorreferensi = Column(String(50))
    nomorantrian = Column(String(50))
    angkaantrean = Column(String(50))
    kodebooking = Column(String(50))
    estimasidilayani = Column(String(50))
    sisakuotajkn = Column(String(50))
    kuotajkn = Column(String(50))
    sisakuotanonjkn = Column(String(50))
    kuotanonjkn = Column(String(50))
    flag = Column(String(1))
    namapoli = Column(String(255))
    namadokter = Column(String(255))
    nama = Column(String(255))
    pasienbaru = Column(String(255))
    jenispasien = Column(String(255))
    

class Pasienbaru(Base):
    __tablename__ = 'pasienbaru'

    norm = Column(Integer, primary_key=True, server_default=text("nextval('pasienbaru_norm_seq'::regclass)"))
    nomorkartu = Column(String(50))
    nik = Column(String(50))
    nomorkk = Column(String(50))
    nama = Column(String(100))
    jeniskelamin = Column(String(1))
    tanggallahir = Column(String(50))
    nohp = Column(String(20))
    alamat = Column(String(100))
    kodeprop = Column(String(10))
    namaprop = Column(String(50))
    kodedati2 = Column(String(10))
    namadati2 = Column(String(50))
    kodekec = Column(String(10))
    namakec = Column(String(50))
    kodekel = Column(String(10))
    namakel = Column(String(50))
    rw = Column(String(5))
    rt = Column(String(5))


class AntrianFarmasi(Base):
    __tablename__ = 'antrian_farmasi'

    id = Column(Integer, primary_key=True, server_default=text("nextval('antrian_farmasi_id_seq'::regclass)"))
    kodebooking = Column(String(50))
    nomorantrean = Column(Integer)
    keterangan = Column(String(255))
    jenisresep = Column(String(255))

class JadwalDokter(Base):
    __tablename__ = 'jadwaldokter'

    id = Column(Integer, primary_key=True, server_default=text("nextval('jadwaldokter_id_seq'::regclass)"))
    kodesubspesialis = Column(String(50))
    hari = Column(Integer)
    kapasitaspasien = Column(Integer)
    libur = Column(Integer)
    namahari = Column(String(50))
    jadwal = Column(String(255))
    namasubspesialis = Column(String(255))
    namadokter = Column(String(255))
    kodepoli = Column(String(50))
    namapoli = Column(String(255))
    kodedokter = Column(Integer)

class AntrianAdmisi(Base):
    __tablename__ = 'antrian_admisi'

    id = Column(Integer, primary_key=True, server_default=text("nextval('antrian_admisi_id_seq'::regclass)"))
    no_antrian = Column(Integer)
    tgl_kunjungan = Column(Date)
    flag = Column(String(2))
    loket = Column(String(10))
    status = Column(String(20))  # Tambahan kolom status untuk badge antrian
    waktu_panggil = Column(DateTime)  # Tambahan kolom waktu panggil

# antrian_poli = Table(
#         'antrian_poli',
#         metadata,
#         Column('id',Integer,primary_key = True),
#         Column('nomorkartu',String(50)),
#         Column('nik',String(50)),
#         Column('nohp',String(15)),
#         Column('kodepoli',String(10)),
#         Column('norm',String(20)),
#         Column('tanggalperiksa',String(50)),
#         Column('kodedokter',Integer),
#         Column('jampraktek',String(40)),
#         Column('jeniskunjungan',Integer),
#         Column('nomorreferensi',String(50)),
#         Column('nomorantrian',String(50)),
#         Column('angkaantrean',String(50)),
#         Column('kodebooking',String(50)),
#         Column('estimasidilayani',String(50)),
#         Column('sisakuotajkn',String(50)),
#         Column('kuotajkn',String(50)),
#         Column('sisakuotanonjkn',String(50)),
#         Column('kuotanonjkn',String(50)),
# )



#  CREATE TABLE antrian_poli(
#      id SERIAL PRIMARY KEY,
#      nomorkartu VARCHAR(50),
#      nik VARCHAR(50),
#      nohp VARCHAR(15),
#      kodepoli VARCHAR(10),
#      norm VARCHAR(50),
#      tanggalperiksa VARCHAR(50),
#      kodedokter INTEGER,
#      jampraktek VARCHAR(40),
#      jeniskunjungan INTEGER,
#      nomorreferensi VARCHAR(50),
#      nomorantrian VARCHAR(50),
#      angkaantrean VARCHAR(50),
#      kodebooking VARCHAR(50),
#      estimasidilayani VARCHAR(50),
#      sisakuotajkn VARCHAR(50),
#      kuotajkn VARCHAR(50),
#      sisakuotanonjkn VARCHAR(50),
#      kuotanonjkn VARCHAR(50),
#      flag VARCHAR(100),
#      namapoli VARCHAR(255),
#      namadokter VARCHAR(255),
#      nama VARCHAR(255),
#      keterangan varchar,
#      pasienbaru varchar,
#      jenispasien varchar
#  );


#  CREATE TABLE pasienbaru (
#      norm SERIAL PRIMARY KEY,
#      nomorkartu VARCHAR(50),
#      nik VARCHAR(50),
#      nomorkk VARCHAR(50),
#      nama VARCHAR(100),
#      jeniskelamin CHAR(1),
#      tanggallahir VARCHAR(50),
#      nohp VARCHAR(20),
#      alamat VARCHAR(100),
#      kodeprop VARCHAR(10),
#      namaprop VARCHAR(50),
#      kodedati2 VARCHAR(10),
#      namadati2 VARCHAR(50),
#      kodekec VARCHAR(10),
#      namakec VARCHAR(50),
#      kodekel VARCHAR(10),
#      namakel VARCHAR(50),
#      rw VARCHAR(5),
#      rt VARCHAR(5)
#  );


# CREATE OR REPLACE FUNCTION "public"."init_antrian"()
#   RETURNS "pg_catalog"."trigger" AS $BODY$
# BEGIN
#     NEW.angkaantrean := COALESCE(
#         (SELECT COUNT(*)::integer+1 FROM antrian_poli 
#          WHERE kodepoli = NEW.kodepoli 
#            AND kodedokter = NEW.kodedokter 
#            AND TO_CHAR(tanggalperiksa, 'YYYY-MM-DD') = TO_CHAR(NEW.tanggalperiksa, 'YYYY-MM-DD')::text
#         ), 1
#     );

#     NEW.nomorantrian := NEW.kodepoli || '-' || LPAD(
#     COALESCE(
#         (SELECT COUNT(*)::integer + 1 FROM antrian_poli
#          WHERE kodepoli = NEW.kodepoli
#            AND kodedokter = NEW.kodedokter
#            AND TO_CHAR(tanggalperiksa, 'YYYY-MM-DD') = TO_CHAR(NEW.tanggalperiksa::date, 'YYYY-MM-DD')::text
#         ), 1
#     )::varchar, 3, '0');

#     NEW.kodebooking := TO_CHAR(NEW.tanggalperiksa, 'YYMMDD') || NEW.kodepoli || LPAD(
#     COALESCE(
#         (SELECT COUNT(*)::integer + 1 FROM antrian_poli
#          WHERE kodepoli = NEW.kodepoli
#            AND kodedokter = NEW.kodedokter
#            AND TO_CHAR(tanggalperiksa, 'YYYY-MM-DD') = TO_CHAR(NEW.tanggalperiksa::date, 'YYYY-MM-DD')::text
#         ), 1
#     )::varchar, 3, '0');

#     RETURN NEW;
# END;

# $BODY$
# LANGUAGE plpgsql VOLATILE COST 100;


# -- 

# CREATE TRIGGER before_insert_antrian
# BEFORE INSERT ON antrian_poli
# FOR EACH ROW
# EXECUTE FUNCTION init_antrian();


#  CREATE TABLE antrian_farmasi(
#  id serial,
#  kodebooking varchar,
#  nomorantrean int,
#  keterangan varchar,
#  tglperiksa date,
#  jenisresep varchar,
#  tindak varchar
#  );


# create table jadwaldokter(id serial,kodesubspesialis varchar,hari int,kapasitaspasien int,libur int,namahari varchar,jadwal varchar,namasubspesialis varchar,namadokter varchar,kodepoli varchar,namapoli varchar,kodedokter int);

# create table auth_bpjs(int serial primary key,username varchar, password varchar);
# insert into auth_bpjs(username,password) values('0304R002','12345');
