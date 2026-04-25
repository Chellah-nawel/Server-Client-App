#cree un bout de socket serveur
import socket

server=socket.socket()
server.bind(('localhost', 12345))#####################comment savoir le port d'ecoute?#####################
server.listen(1) #le serveur attend une connexion
adress, connexion =server.accept() ###########################comment savoir l'adresse du client?#####################

#recevoir la certificat du client
client_certificate = connexion.recv(1024) ####################ca signifie quoi le 1024?#####################
