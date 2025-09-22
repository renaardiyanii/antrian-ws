import os
import httpx
from app.api.controller.bpjs import get,post
from app.api.controller.bpjs_vclaim import get_vclaim
import os
import requests,json
# CAST_SERVICE_HOST_URL = os.getenv('SERVICE_WS_EKAMEK')
CAST_SERVICE_HOST_URL = ''




def getantrol(url):
    response = get(url,'https://apijkn.bpjs-kesehatan.go.id/antreanrs')
    return response

def postantrol(url,data,encodes=None):
    response = post(url,data,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/',encodes)
    return response

def ceknokartu(nokartu):
    print(CAST_SERVICE_HOST_URL)
    r = httpx.get(f'{CAST_SERVICE_HOST_URL}cekpasien/no_kartu/{nokartu}')
    return True if r.json() else False



def tambahantrean(data):
    url = 'antrean/add'
    response = post(url,data,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/')
    return response


def ceknorujukan(no_rujukan:str)-> dict:
    response = get_vclaim('/Rujukan/{}'.format(no_rujukan))
    # return response
    if response['metaData']['code'] == '200':
        return response
    response = get_vclaim(f'/Rujukan/RS/{no_rujukan}')
    return response

def cekjadwaldokter(poli , tgl):
    url = f'jadwaldokter/kodepoli/{poli}/tanggal/{tgl}'
    response = get(url,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/')
    # print(response)
    return response

def cekdokter():
    url = f'ref/dokter'
    response = get(url,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/')
    return response

def cekpoli():
    url = f'ref/poli'
    response = get(url,'https://apijkn.bpjs-kesehatan.go.id/antreanrs/')
    print(response)
    return response

def ispoliavailable(poli:str):
    r = httpx.get(f'{CAST_SERVICE_HOST_URL}poli/{poli}')
    return True if r.json() else False


def cekstatusantrian(p):
    # print(CAST_SERVICE_HOST_URL)
    # headers = {'Content-Type':'application/json'}
    # r = httpx.post(f'{CAST_SERVICE_HOST_URL}statusantrian', data={
    #     'kodepoli': p.kodepoli,
    #     'kodedokter': p.kodedokter,
    #     'tanggalperiksa': p.tanggalperiksa,
    #     'jampraktek': p.jampraktek,
    #     },headers = headers)
    r = requests.post(f'{CAST_SERVICE_HOST_URL}statusantrian',data = json.dumps({
        'kodepoli': p.kodepoli,
        'kodedokter': p.kodedokter,
        'tanggalperiksa': p.tanggalperiksa,
        'jampraktek': p.jampraktek,
        }))
    return r.json()

def cekDataPasien(nomorkartu,nik,norm):
    r = requests.post(f'{CAST_SERVICE_HOST_URL}caripasien',data = json.dumps({
        'nomorkartu':nomorkartu,
        'nik':nik,
        'norm':norm
    }))
    return r.json()


def carinamapoli(kodepolibpjs):
    r = requests.get(f'{CAST_SERVICE_HOST_URL}carinamapoli/{kodepolibpjs}')
    return r.json()

def carinamadokter(kodedokterhfis):
    r = requests.get(f"{CAST_SERVICE_HOST_URL}carinamadokter/{kodedokterhfis}")
    return r.json()


def cekJadwalOperasi(tglawal,tglakhir):
    r = requests.post(f'{CAST_SERVICE_HOST_URL}jadwaloperasirs',data = json.dumps({
        'tanggalawal':tglawal,
        'tanggalakhir':tglakhir
    }))
    return r.json()

def cekJadwalOperasiPasien(nopeserta):
    r = requests.post(f'{CAST_SERVICE_HOST_URL}jadwaloperasipasien',data = json.dumps({
        'nopeserta':nopeserta
    }))
    return r.json()

def cekPoliDokter(iddokter):
    r = requests.get(f'{CAST_SERVICE_HOST_URL}cekpolidokterbpjs/{iddokter}')
    return r

def validasiNoka(nokartu,norujukan):
    r = requests.get(f'http://localhost/simrs_rsomh_v3/api/api/cekrujukankartu?nokartu={nokartu}&norujukan={norujukan}')
    return r