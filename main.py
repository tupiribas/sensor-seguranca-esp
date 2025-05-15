# import time
# import mpu6050
# from machine import I2C, Pin
# import math

# print('\n\n')

# # Configuração dos pinos I2C
# scl_pin = Pin(13, Pin.OUT)
# sda_pin = Pin(12, Pin.OUT)
# i2c = I2C(scl=scl_pin, sda=sda_pin)
# accelerometer = mpu6050.accel(i2c)

# # Configuração do pino do buzzer
# # Substitua 16 pelo pino GPIO ao qual seu buzzer está conectado
# buzzer_pin = Pin(16, Pin.OUT)

# # Fase de linha de base
# num_leituras_base = 100
# delay_ms_base = 20
# magnitudes_base = []
# print("Estabelecendo linha de base...")
# for _ in range(num_leituras_base):
#     accel_values = accelerometer.get_values()
#     acx = accel_values['AcX']
#     acy = accel_values['AcY']
#     acz = accel_values['AcZ']
#     magnitude = math.sqrt(acx**2 + acy**2 + acz**2)
#     magnitudes_base.append(magnitude)
#     time.sleep_ms(delay_ms_base)

# linha_base = sum(magnitudes_base) / len(magnitudes_base)
# print("Linha de base estabelecida:", linha_base)

# # Fase de monitoramento
# limiar_desvio = 500  # Ajuste este valor de acordo com seus testes
# delay_ms_monitor = 100
# movimento_detectado = False
# tempo_alarme = 2000  # Tempo em milissegundos que o alarme soará

# print("Monitorando movimento...")
# while True:
#     accel_values = accelerometer.get_values()
#     acx = accel_values['AcX']
#     acy = accel_values['AcY']
#     acz = accel_values['AcZ']
#     magnitude_atual = math.sqrt(acx**2 + acy**2 + acz**2)

#     desvio = abs(magnitude_atual - linha_base)

#     if desvio > limiar_desvio and not movimento_detectado:
#         print("MOVIMENTO DETECTADO! Desvio:", desvio)
#         movimento_detectado = True
#         # Ativa o buzzer (HIGH) - pode precisar ser 0 dependendo da conexão
#         buzzer_pin.value(1)
#         tempo_inicio_alarme = time.ticks_ms()
#     elif movimento_detectado and (time.ticks_ms() - tempo_inicio_alarme > tempo_alarme):
#         buzzer_pin.value(0)  # Desativa o buzzer (LOW)
#         movimento_detectado = False
#         print("Alarme desligado.")
#     elif not movimento_detectado:
#         # Garante que o buzzer esteja desligado quando não há movimento
#         buzzer_pin.value(0)

#     print("Desvio:", desvio, "Alarme ativo:", movimento_detectado)
#     time.sleep_ms(delay_ms_monitor)
from machine import Pin, PWM
import time

buzzer_pin = Pin(4, Pin.OUT)  # Define o pino do buzzer como um pino digital comum
buzzer_pwm = PWM(buzzer_pin)  # Inicializa o PWM no pino

frequencia = 1000  # Frequência do som em Hertz (pode variar)
duty_cycle = 600   # Ciclo de trabalho (de 0 a 1023, controla o volume)

buzzer_pwm.freq(frequencia)
buzzer_pwm.duty(duty_cycle)

time.sleep(5)  # O buzzer soará por 5 segundos

buzzer_pwm.deinit()  # Desliga o PWM no pino
