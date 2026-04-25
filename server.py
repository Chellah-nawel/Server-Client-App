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

#recevoir la cle de session du client chiffree avec la cle publique du serveur
encrypted_key = connexion.recv(4096)

#dechiffrer la cle de session avec la cle privee du serveur
# session_key = rsa_decrypt(encrypted_key, private_key) ############## comment recuperer la cle privee du serveur?#####################