import datetime
def handleError(message,code=201):
    return {
        'metadata':{
            'code':code,
            'message':message
        }
    }

def handleErrorAdmin(message,code=201):
    return {
        'metaData':{
            'code':code,
            'message':message
        }
    }


def validasiTglLahir(date_text):
    try:
        date = datetime.date.fromisoformat(date_text)
        if(date_text < str(datetime.datetime.now().date())):
            return True
        return False
    except ValueError:
        return False

def validasiTgl(date_text):
    try:
        date = datetime.date.fromisoformat(date_text)
        return True
    except ValueError:
        return False

def validasiHariIni(date_text):
    try:
        date = datetime.date.fromisoformat(date_text)
        if(date_text != str(datetime.datetime.now().date())):
            return False
        return True
    except ValueError:
        return False

def validasiBackDate(date_text):
    try:
        date = datetime.date.fromisoformat(date_text)
        if(date_text < str(datetime.datetime.now().date())):
            return False
        return True
    except ValueError:
        return False

def isFullOfInteger(nomor:str):
    try:
        int(nomor)
        return True
    except:
        return False

def isVariableIsXDigits(nomor:str,digit:int):
    if(len(nomor) == digit):
        return True
    return False

def checkVariableKosong(nomor:str):
    if nomor == '':
        return False
    return True

def validasiJadwalMelebihiJam(jadwal):
    jadwalAkhir = jadwal.split('-')[1] # 12.00
    tglSaatIni = datetime.datetime.today().strftime('%Y-%m-%d') # 2023-02-08
    tglJadwal = str(tglSaatIni) +' ' +jadwalAkhir # 2023-02-08 12:00
    try:
        jadwalTerakhir = datetime.datetime.strptime(tglJadwal, '%Y-%m-%d %H:%M').strftime('%Y-%m-%d %H:%M')
    except:
        jadwalTerakhir = datetime.datetime.strptime(tglJadwal, '%Y-%m-%d %H.%M').strftime('%Y-%m-%d %H:%M')
    
    now = datetime.datetime.now()
    print(now)
    tglSaatIni = now.strftime('%Y-%m-%d %H:%M') #tgl saat ini + jam
    return tglSaatIni < jadwalTerakhir # cek jika jam saat ini kurang dari jadwal terakhir
