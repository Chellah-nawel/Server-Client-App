import threading
from server import demarrer_serveur
from interface import App

if __name__ == "__main__":

    # Lancer le serveur
    thread_serveur = threading.Thread(target=demarrer_serveur, daemon=True)# le thread s'arrete automatiquement quand on ferme la fenetre
    thread_serveur.start()
    print("[MAIN] Serveur lancé dans un thread")

    #lancer l'interface graphique
    print("[MAIN] Lancement de l'interface...")
    app = App()
    app.mainloop()

    print("[MAIN] Programme terminé")
