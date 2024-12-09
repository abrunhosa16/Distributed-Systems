import threading  
import time 
import random 
import math 
import queue


def poisson_delay(lambda_):
    return -math.log(1.0 - random.random()) / lambda_

def get_random_operation():
    operations = ['add', 'sub', 'mul', 'div']
    return random.choice(operations)

def get_random_arguments():
    return {
        "number1": random.randint(0, 99),
        "number2": random.randint(0, 99)
    }

def generate_requests(lmbda, queue: queue.Queue):
    def request_loop():
        while True:
            delay = poisson_delay(lmbda)  # Calcula o atraso de Poisson
            time.sleep(delay * 60)  # Aguarda pelo tempo de atraso
            
            operation = get_random_operation()
            arguments = get_random_arguments()

            request = f"{operation} {arguments['number1']} {arguments['number2']}"

            # Cria uma solicitação
            queue.put(request)  # Adiciona a solicitação à fila

    # Inicia o loop de geração em uma thread separada
    generator_thread = threading.Thread(target=request_loop, daemon=True)
    generator_thread.start()