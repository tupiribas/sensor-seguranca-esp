import network
import time
import machine

from config import WIFI_SSID, WIFI_PASSWORD

def conectar_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Conectando ao WiFi...')
        wlan.connect(ssid, password)
        tempo_max = 20
        while not wlan.isconnected() and tempo_max > 0:
            print('.', end='')
            time.sleep(1)
            tempo_max -= 1
        if not wlan.isconnected():
            print('Falha ao conectar ao Wifi. Reiniciando...')
            machine.reset() # Reinicia o ESP8266 se não conectar
    else:
        print('Já está conectado ao WiFi.\nEndereco IP: \n', wlan.ifconfig()[0])
    print('\nConectando ao WiFi:', wlan.ifconfig())
    return wlan

# Conecta ao Wifi ao iniciar
try:
    conectar_wifi(WIFI_SSID, WIFI_PASSWORD)
except Exception as e:
    # Segunda tentativa de conexão
    print(f'Erro no boot.py: {e}')
    print('Reiniciando em 5 segundos...')
    time.sleep(5)
