from typing import List,Optional
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table, MetaData, Date
from app.api.database.db import engine, Base
from datetime import date


metadata = MetaData(engine)
metadata.reflect()

class AuthBpjsIn(BaseModel):
    username        : str
    password        : str

class AuthBpjsOut(BaseModel):
    token           : str

class AntrianPoli(BaseModel):
    norm : Optional[str] = None
    nama            : Optional[str] = None

class AntrianPoliIn(AntrianPoli):
    nomorkartu      : Optional[str] = None
    nik             : Optional[str] = None
    nohp            : Optional[str] = None
    kodepoli        : Optional[str] = None
    tanggalperiksa  : Optional[str] = None
    kodedokter      : Optional[int] = None
    jampraktek      : Optional[str] = None
    jeniskunjungan  : Optional[int] = None
    nomorreferensi  : Optional[str] = None
    kuotajkn        : Optional[str] = None
    # nama            : Optional[str] = None

class AntrianPoliOut(AntrianPoli):
    nomorantrean    : Optional[str] = None
    angkaantrean    : Optional[int] = None
    kodebooking     : Optional[str] = None
    namapoli        : Optional[str] = None
    namadokter      : Optional[str] = None
    estimasidilayani: Optional[int] = None
    sisakuotajkn    : Optional[int] = None
    kuotajkn        : Optional[int] = None
    sisakuotanonjkn : Optional[int] = None
    kuotanonjkn     : Optional[int] = None
    keterangan      : Optional[str] = None


class Statusantrian(BaseModel):
    kodepoli        : str
    kodedokter      : int
    tanggalperiksa  : str
    jampraktek      : str

    class Config:
        orm_mode = True

class Ambilantrian(BaseModel):
    jenispasien     : Optional[str] = 'JKN'
    nomorkartu      : str
    nik             : str
    nohp            : str
    kodepoli        : str
    norm            : str
    tanggalperiksa  : str
    kodedokter      : str
    jampraktek      : str
    jeniskunjungan  : int
    nomorreferensi  : str
    namadokter      : Optional[str] = ''
    namapoli        : Optional[str] = ''
    nama            : Optional[str] = ''
    estimasidilayani: Optional[str] = ''
    sisakuotajkn    : Optional[str] = ''
    kuotajkn        : Optional[str] = ''
    sisakuotanonjkn : Optional[str] = ''
    kuotanonjkn     : Optional[str] = ''
    pasienbaru      : Optional[str] = None

    class Config:
        orm_mode = True


class AmbilantrianDebug(BaseModel):
    jenispasien     : Optional[str] = 'JKN'
    nomorkartu      : str
    nik             : str
    nohp            : str
    kodepoli        : str
    norm            : str
    tanggalperiksa  : str
    kodedokter      : str
    jampraktek      : str
    jeniskunjungan  : int
    nomorreferensi  : str
    namadokter      : Optional[str] = ''
    namapoli        : Optional[str] = ''
    nama            : Optional[str] = ''
    estimasidilayani: Optional[str] = ''
    sisakuotajkn    : Optional[str] = ''
    kuotajkn        : Optional[str] = ''
    sisakuotanonjkn : Optional[str] = ''
    kuotanonjkn     : Optional[str] = ''
    pasienbaru      : Optional[str] = None
    id_poli         : Optional[str] = ''

    class Config:
        orm_mode = True

class BatalAntrian(BaseModel):
    kodebooking     : str
    keterangan      : str

    class Config:
        orm_mode = True


class ChekinAntrian(BaseModel):
    kodebooking : str
    waktu       : int

    class Config:
        orm_mode = True


class Pasienbaru(BaseModel):
    nomorkartu      : str
    nik             : str
    nomorkk         : str
    nama            : str
    jeniskelamin    : str
    tanggallahir    : str
    nohp            : str
    alamat          : str
    kodeprop        : str
    namaprop        : str
    kodedati2       : str
    namadati2       : str
    kodekec         : str
    namakec         : str
    kodekel         : str
    namakel         : str
    rw              : str
    rt              : str

    class Config:
        orm_mode = True

    
class Pasienbarunew(BaseModel):
    nomorkartu      : str
    nama             : str
    kategori         : str
    kodepoli        : str
    kodedokter    :  Optional[str] = None

    class Config:
        orm_mode = True

class Sisaantrian(BaseModel):
    kodebooking     : str
    class Config:
        orm_mode = True

class Jadwaloperasirs(BaseModel):
    tanggalawal     : Optional[str] = None
    tanggalakhir    : Optional[str] = None

    class Config:
        orm_mode = True

class Jadwaloperasipasien(BaseModel):
    nopeserta : Optional[str] = None
    class Config : 
        orm_mode = True



# bpjs ws hit - update jadwal dokter
# added @aldi
# 1:49 PM 6/22/2023
class Jadwal(BaseModel):
    hari: str
    buka: str
    tutup: str

class UpdateJadwalDokter(BaseModel):
    kodepoli: str
    kodesubspesialis: str
    kodedokter: int
    jadwal: List[Jadwal]


class TambahAntrian(BaseModel):
    kodebooking: str
    jenispasien: str
    nomorkartu: str
    nik: str
    nohp: str
    kodepoli: str
    namapoli: str
    pasienbaru: int
    norm: str
    tanggalperiksa: str
    kodedokter: int
    namadokter: str
    jampraktek: str
    jeniskunjungan: int
    nomorreferensi: str
    nomorantrean: str
    angkaantrean: int
    estimasidilayani: int
    sisakuotajkn: int
    kuotajkn: int
    sisakuotanonjkn: int
    kuotanonjkn: int
    keterangan: str

class TambahAntrianFarmasi(BaseModel):
    kodebooking: str
    jenisresep: str
    nomorantrean: int
    keterangan: str


class UpdateWaktu(BaseModel):
    kodebooking: str
    taskid: int
    waktu: int

class BatalAntrian(BaseModel):
    kodebooking: str
    keterangan: str

class TaskId(BaseModel):
    kodebooking: str

class AmbilAntreanFarmasi(BaseModel):
    kodebooking: str
    jenisresep: Optional[str] = None
    nomorantrean: Optional[int] = None
    keterangan: Optional[str] = None
