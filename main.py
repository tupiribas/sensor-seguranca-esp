import time
import math
from machine import I2C, Pin
import machine
import network
from umqtt.simple import MQTTClient
import ubinascii

print('\n--- Iniciando Projeto de Segurança de Objeto (Versão Final Otimizada) ---')



FEED_ACCEL_MAGNITUDE = "aceleracao-magnitude"
FEED_MOVIMENTO_STATUS = "movimento-status"
tempo_maximo = 2
# --- CLASSE ACCEL ---


class accel():
    def __init__(self, i2c, addr=0x68):
        self.iic = i2c
        self.addr = addr
        self.iic.start()
        self.iic.writeto(self.addr, bytearray([107, 0]))
        self.iic.stop()

    def get_raw_values(self):
        self.iic.start()
        a = self.iic.readfrom_mem(self.addr, 0x3B, 14)
        self.iic.stop()
        return a

    def bytes_to_int(self, firstbyte, secondbyte):
        if not firstbyte & 0x80:
            return firstbyte << 8 | secondbyte
        return - (((firstbyte ^ 255) << 8) | (secondbyte ^ 255) + 1)

    def get_values(self):
        raw_ints = self.get_raw_values()
        vals = {}
        vals["AcX"] = self.bytes_to_int(raw_ints[0], raw_ints[1])
        vals["AcY"] = self.bytes_to_int(raw_ints[2], raw_ints[3])
        vals["AcZ"] = self.bytes_to_int(raw_ints[4], raw_ints[5])
        vals["Tmp"] = self.bytes_to_int(
            raw_ints[6], raw_ints[7]) / 340.00 + 36.53
        vals["GyX"] = self.bytes_to_int(raw_ints[8], raw_ints[9])
        vals["GyY"] = self.bytes_to_int(raw_ints[10], raw_ints[11])
        vals["GyZ"] = self.bytes_to_int(raw_ints[12], raw_ints[13])
        return vals

# --- CLASSE ADABRUITMQTTCLIENT ---


class AdafruitMQTTClient:
    def __init__(self, username, key, server, port, keepalive=30) -> None:
        self.username = username
        self.key = key
        self.server = server
        self.port = port
        self.keepalive = keepalive
        self.client_id = "ESP8266_MUSEU_S"
        self.conectado = False
        self.client = None
        self.falhas_reconexao_consecutivas = 0
        self.MAX_FALHAS_RECONEXAO = 40

    def _reconectando(self):
        print("Tentando reconectar ao Adafruit IO...")
        # --- ADICIONADO PARA DEPURAR OS PARÂMETROS DE CONEXÃO ---
        print(f"  Client ID: {self.client_id}")
        print(f"  Username: {self.username}")
        print(f"  Server: {self.server}:{self.port}")
        # Para a chave, não imprima a chave real por segurança, mas seu comprimento:
        print(f"  Key Length: {len(self.key)} caracteres")
        # Fim da depuração

        try:
            self.client = MQTTClient(
                client_id=self.client_id,
                server=self.server,
                port=self.port,
                user=self.username,
                password=self.key,
                keepalive=self.keepalive,
                ssl=False  # Sem SSL, pois a porta é 1883
            )
            self.client.connect()
            self.conectado = True
            self.falhas_reconexao_consecutivas = 0
            print('Conectado ao Adafruit IO!')
            return True
        except Exception as e:
            print(f'Falha ao conectar MQTT: {e}')
            self.conectado = False
            self.falhas_reconexao_consecutivas += 1
            if self.falhas_reconexao_consecutivas >= self.MAX_FALHAS_RECONEXAO:
                print(
                    f"Limite de {self.MAX_FALHAS_RECONEXAO} falhas de reconexão MQTT atingido.")
                print(
                    "Verifique suas credenciais e conexão de internet. REINICIANDO PARA TENTAR NOVO CICLO.")
                time.sleep(5)  # Delay antes do reset para ver a mensagem
                machine.reset()  # Força o reset para um novo ciclo de conexão
            return False

    def conexao_aceita(self):
        if not self.conectado:
            # Aumenta o delay para 10 segundos antes de cada tentativa de reconexão
            time.sleep(10)
            return self._reconectando()
        return True

    def publicar(self, feed_name, dados):
        if not self.conectado:
            if not self.conexao_aceita():
                print(
                    'Não conectado ao MQTT, falha ao publicar após tentativa de reconexão.')
                return False

        caminho_feed = f"{self.username}/feeds/{feed_name}"
        try:
            self.client.publish(caminho_feed, str(dados))
            return True
        except Exception as e:
            print(f'Erro ao publicar no feed: "{feed_name}": \nERRO: ', e)
            self.conectado = False
            return False  # Falha ao publicar, indica para o loop principal que precisa reconectar

    def desconectar(self):
        if self.client and self.conectado:
            self.client.disconnect()
            self.conectado = False
            print("Desconectado do Adafruit.")

    def verificar_msg(self):
        try:
            if self.conectado:
                self.client.check_msg()
            else:
                self.conexao_aceita()
        except Exception as e:
            print(f"Erro ao verificar mensagens MQTT: {e}")
            self.conectado = False


# --- CLASSE MOVEMENTDETECTOR ---
class MovementDetector:
    def __init__(self, i2c_bus, limiar_desvio=300):
        self.accelerometer = accel(i2c_bus)
        self.limiar_desvio = limiar_desvio
        self.linha_base = 0
        self.calibrated = False

    def calibrate_baseline(self, num_readings=50, delay_ms=50):
        print("Estabelecendo linha de base para o sensor MPU6050...")
        total_magnitude = 0
        read_count = 0

        for i in range(num_readings):
            try:
                accel_values = self.accelerometer.get_values()
                magnitude = math.sqrt(
                    accel_values['AcX'] ** 2 + accel_values['AcY'] ** 2 +
                    accel_values['AcZ'] ** 2)
                total_magnitude += magnitude
                read_count += 1
                time.sleep_ms(delay_ms)
            except Exception as e:
                print(
                    f"Erro na leitura {i+1} durante a calibração: {e}. Pulando leitura.")

        if read_count > 0:
            self.linha_base = total_magnitude / read_count
            self.calibrated = True
            print(
                f"Linha de base estabelecida com {read_count} leituras: {self.linha_base:.2f}")
        else:
            print(
                "Não foi possível estabelecer a linha de base. Nenhuma leitura bem-sucedida.")
            self.calibrated = False
        return self.linha_base

    def check_for_movement(self):
        if not self.calibrated:
            return False, 0, 0

        try:
            accel_values = self.accelerometer.get_values()
            magnitude_atual = math.sqrt(
                accel_values['AcX'] ** 2 + accel_values['AcY'] ** 2 +
                accel_values['AcZ'] ** 2)
            desvio = abs(magnitude_atual - self.linha_base)

            is_moving = desvio > self.limiar_desvio
            return is_moving, desvio, magnitude_atual
        except Exception as e:
            print(
                f"Erro ao ler MPU6050 durante monitoramento: {e}. Revertendo status.")
            return False, 0, 0

    def get_current_magnitude(self):
        try:
            accel_values = self.accelerometer.get_values()
            return math.sqrt(
                accel_values['AcX'] ** 2 + accel_values['AcY'] ** 2 +
                accel_values['AcZ'] ** 2)
        except Exception as e:
            print(f"Erro ao obter magnitude atual: {e}")
            return 0

    def get_baseline(self):
        return self.linha_base


# --- LÓGICA DE CONEXÃO WI-FI ---
def conectar_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Conectando ao WiFi...')
        wlan.connect(ssid, password)
        max_attempts = 20
        while wlan.status() != network.STAT_GOT_IP and max_attempts > 0:
            print('.', end='')
            time.sleep(1)
            max_attempts -= 1

        if wlan.status() == network.STAT_GOT_IP:
            print('\nConectado ao WiFi com sucesso! Endereço IP:',
                  wlan.ifconfig()[0])
            return wlan
        else:
            print(
                f'\nFalha ao conectar ao WiFi. Status: {wlan.status()}. Reiniciando...')
            time.sleep(5)
            machine.reset()
    else:
        print('Já conectado ao WiFi. Endereço IP:', wlan.ifconfig()[0])
        return wlan


# --- Configuração de Pinagem do ESP8266 para I2C ---
I2C_SCL_PIN = Pin(13, Pin.OUT)
I2C_SDA_PIN = Pin(12, Pin.OUT)
i2c_bus = I2C(scl=I2C_SCL_PIN, sda=I2C_SDA_PIN)

# --- Instanciação de Objetos Globais ---
mqtt_client_instance = AdafruitMQTTClient(
    ADAFRUIT_AIO_USERNAME, ADAFRUIT_AIO_KEY, ADAFRUIT_AIO_SERVER,
    ADAFRUIT_AIO_PORT, keepalive=50)
detector = MovementDetector(i2c_bus, limiar_desvio=500)

# --- Fases do Programa Principal ---


def setup_main_program():
    print("Realizando setup inicial do programa principal...")

    conectar_wifi(WIFI_SSID, WIFI_PASSWORD)

    detector.calibrate_baseline(num_readings=50, delay_ms=50)

    if not mqtt_client_instance.conexao_aceita():
        # Não reinicia imediatamente aqui para depurar o problema de conexão MQTT
        print("Falha na conexão MQTT durante o setup. Programa não continuará no loop.")
        while True:  # Loop infinito para manter o ESP8266 ligado para depuração
            time.sleep(10)
            print("Aguardando correção de conexão MQTT...")


def loop_main_program():
    movimento_detectado_anteriormente = False

    print("Iniciando monitoramento do movimento...")
    while True:
        mqtt_client_instance.verificar_msg()

        is_moving, desvio_atual, magnitude_atual = detector.check_for_movement()

        # Publica a magnitude atual a cada `tempo_maximo` segundos
        mqtt_client_instance.publicar(
            FEED_ACCEL_MAGNITUDE, f"{magnitude_atual:.2f}")

        if is_moving and not movimento_detectado_anteriormente:
            print(
                f"ALERTA! MOVIMENTO DETECTADO! Desvio: {desvio_atual:.2f}. Magnitude: {magnitude_atual:.2f}")
            mqtt_client_instance.publicar(FEED_MOVIMENTO_STATUS, "1")
            movimento_detectado_anteriormente = True
        elif not is_moving and movimento_detectado_anteriormente:
            print("Movimento cessou. Resetando status.")
            mqtt_client_instance.publicar(FEED_MOVIMENTO_STATUS, "0")
            movimento_detectado_anteriormente = False

        # Agora, um único sleep para controlar a frequência do loop completo
        time.sleep(tempo_maximo)


# --- EXECUÇÃO PRINCIPAL DO PROGRAMA ---
if __name__ == '__main__':
    try:
        setup_main_program()
        loop_main_program()
    except Exception as e:
        print(f"Erro fatal no programa: {e}")
        print("Reiniciando o ESP8266 em 10 segundos para tentar novamente...")
        time.sleep(10)
        machine.reset()
