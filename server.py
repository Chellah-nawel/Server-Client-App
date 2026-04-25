#cree un bout de socket serveur
import socket

server=socket.socket()
server.bind(('localhost', 12345))#####################comment savoir le port d'ecoute?#####################
server.listen(1) #le serveur attend une connexion
adress, connexion =server.accept()