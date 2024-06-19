import socket

# Configurações do servidor
HOST = '127.0.0.1'  
PORT = 8888         

# Função para iniciar o servidor
def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f'Servidor MQL4 esperando conexão em {HOST}:{PORT}...')
        conn, addr = s.accept()
        with conn:
            print(f'Conectado por {addr}')
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                # Decodifica a mensagem recebida
                message = data.decode('utf-8')
                print(f'Mensagem recebida do EA MQL4: {message}')
                
                # Lógica para responder ao EA (opcional)
                # Colocar lógica aqui
                
                # Enviar uma mensagem de confirmação
                response = 'Mensagem recebida pelo servidor Python'
                conn.sendall(response.encode('utf-8'))

if __name__ == "__main__":
    start_server()
