import socket, cv2, pickle, struct

client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
socket_adress = ('192.168.1.10', 9999)
client_socket.connect(socket_adress)
data = b""
payload_size = struct.calcsize("Q")

while True:
    while len(data) < payload_size:
        packet = client_socket.recv(2*1024)
        if not packet: break
        data += packet
    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack("Q", packed_msg_size)[0]
    while len(data) < msg_size:
        data += client_socket.recv(2*1024)
    frame_data = data[:msg_size]
    data = data[msg_size:]
    frame = pickle.loads(frame_data)
    cv2.imshow("Stream from {}".format(socket_adress), frame)
    if cv2.waitKey(1)  == ord(' '):
        break
    
client_socket.close()