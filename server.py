#cree un bout de socket serveur
import socket

server=socket.socket()
server.bind(('localhost', 12345))#####################comment savoir le port d'ecoute?#####################
server.listen(1) #le serveur attend une connexion
adress, connexion =server.accept()

#envoyer la certificat du serveur au client
with open("server.crt", "rb") as f:
    connexion.send(f.read())

# La personne 3 te fournira une fonction comme :
# verified = verify_certificate(cert_client)
# if not verified:
#     connexion.close()  # certificat invalide, on coupe