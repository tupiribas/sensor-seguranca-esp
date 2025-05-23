from network import WLAN, STA_IF
from time import sleep
from machine import Pin, unique_id
from utime import gmtime, mktime, localtime
from ntptime import settime
from urequests import post
from ujson import dumps

CHIP_ID = unique_id()

SSID = 'VIVOFIBRA-WIFI6-B760'
SENHA = '7AFH73Yq39AF4AN'

TOKEN = 'gGhTWgsXkhw3gvh3lI6L'
# Endpoint HTTP do ThingsBoard
URL = 'https://thingsboard.cloud/api/v1/{}/telemetry'.format(TOKEN)
HEADERS = {'Content-Type': 'application/json'}


def sincronizar_hora_ntp():
    '''
        Necessário, pois o ESP3266 me fornece apenas a data atual da sua 
        fabricação
    '''
    try:
        settime()
        print('Hora sincronizada via NTP')
    except OSError as e:
        print(f'Erro ao sincronizar hora via NTP: {e}')


def formatar_utc_tempoatual(tempojunto_lista):
    '''Formatar no horário ISO do tempo atual'''
    ano, mes, dia, hora, minuto, segundo, _, _ = tempojunto_lista
    return "{:02d}/{:02d}/{:04d} - {:02d}:{:02d}:{:02d}".format(
        dia, mes, ano, hora, minuto, segundo)


def obter_hora_local_salvador():
    """Obtém o timestamp UTC e ajusta para o horário de Salvador (UTC-3)."""
    utc_tuple = gmtime()
    # Subtrai 3 horas (3 * 3600 segundos) do timestamp Unix
    timestamp_local_unix = mktime(utc_tuple) - (3 * 3600)
    return localtime(timestamp_local_unix)


def formatar_chip_id(chip_id: bytes):
    return ''.join([':{:02x}'.format(b) for b in chip_id]).upper().lstrip(':')


payload = {
    "group_id": 5,
    "original_filename": 'roteiro_extensao.pdf',
    "file_hash_sha256": '493B4630E41348B12F3C4C664D70BCD91B56B6C37E3CFDB8248500705E1DE06D',
    "download_link": 'https://drive.google.com/open?id=1C5TI6AEwAU2vqJxoUVnT6vdv3yfPG6Uh&usp=drive_fs',
    "submission_timestamp_utc": formatar_utc_tempoatual(
        obter_hora_local_salvador()
    ),
    "chip_id": formatar_chip_id(chip_id=CHIP_ID)
}


def conectar_wifi():
    wlan = WLAN(STA_IF)
    if not wlan.isconnected():
        print('Conectando ao Wi-Fi')
        try:
            wlan.active(True)
            wlan.connect(SSID, SENHA)
            while not wlan.isconnected():
                print(end='.')
                sleep(1)
            print('Conectado ao Wi-Fi!')
            ip_info = wlan.ifconfig()
            print('Endereço IP:', ip_info)
            sleep(2)
            return wlan
        except Exception as e:
            print(f'Falha ao conectar ao Wi-Fi. Erro: {e}')
    else:
        print("Você já está conectado! Tentando reconectar para obter novo IP")


def publicar_mensagem():
    try:
        response = post(
            url=URL, headers=HEADERS, data=dumps(payload))
        print('Enviado: ', payload, '| Status: ', response.status_code)
        response.close()
    except Exception as e:
        print('Falha ao enviar informações para o servidor: ERROR >>> ', e)
    sleep(5)


led = Pin(2, Pin.OUT)

# Execução principal
wlan = conectar_wifi()

try:
    if wlan.isconnected():
        sincronizar_hora_ntp()
        publicar_mensagem()
except Exception as e:
    print('Serviço ou Wi-Fi desconectado. Tentando reconectar...')
    print(f'Erro inesperado no loop principal: {e}')
sleep(5)
