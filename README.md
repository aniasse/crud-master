# Infrastructure de Microservices : Plateforme de Streaming

## 1. Vue d'ensemble du projet

Ce projet met en œuvre une infrastructure de microservices pour une plateforme de streaming de films. L'architecture est composée de trois services distincts, chacun s'exécutant dans sa propre machine virtuelle gérée par **Vagrant**.

-   **API Gateway (`gateway-vm`)** : Le point d'entrée unique pour toutes les requêtes client. Il achemine le trafic vers le service en aval approprié.
-   **Service d'Inventaire (`inventory-vm`)** : Une API CRUD RESTful pour gérer un catalogue de films. Il possède sa propre base de données PostgreSQL.
-   **Service de Facturation (`billing-vm`)** : Un travailleur en arrière-plan qui traite de manière asynchrone les commandes de facturation. Il consomme les messages d'une file d'attente **RabbitMQ** et possède sa propre base de données PostgreSQL.

Toutes les applications sont écrites en **Python** et gérées comme des services par **PM2**.

### Diagramme d'architecture

```
+----------------+      HTTP       +-------------------+      (accès direct à la bd) +--------------------+
|                |  /api/movies/*  |                   |--------------------------->|                    |
|  Client (Util.)|---------------> |    API Gateway    |                             |  movies_db (Postg) |
|                |                 |    (Flask)        |                             |                    |
+----------------+                 +-------------------+                             +--------------------+
       |
       | POST /api/billing                  |
       |                                    |
       v                                    v
+----------------+                 +-------------------+      (consommer message)    +--------------------+
|  (Corps JSON)  |                 |  File RabbitMQ    |--------------------------->|  Consommateur Fact. |
|                |                 |  (billing_queue)  |                             |      (Pika)        |
+----------------+                 +-------------------+                             +--------------------+
                                                                                           |
                                                                                           | (accès direct à la bd)
                                                                                           v
                                                                                    +--------------------+
                                                                                    |  billing_db (Postg)|
                                                                                    |                    |
                                                                                    +--------------------+
```

## 2. Pile technologique

-   **Virtualisation** : Vagrant
-   **Système d'exploitation** : Ubuntu 22.04 LTS
-   **Framework Web** : Flask (API Gateway, Service dInventaire)
-   **File dattente de messages** : RabbitMQ (avec Pika pour le client Python)
-   **Base de données** : PostgreSQL (avec SQLAlchemy et psycopg2)
-   **Gestionnaire de processus** : PM2

## 3. Configuration et installation

### Prérequis

-   [Vagrant](https://www.vagrantup.com/downloads)
-   [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
-   Un terminal ou une interface de ligne de commande.

### Instructions

1.  **Cloner le dépôt**
    ```sh
    git clone <url-du-depot>
    cd crud-master
    ```

2.  **Configurer les variables d'environnement**
    Créez un fichier `.env` en copiant le fichier d'exemple.
    ```sh
    cp .env.example .env
    ```
    Vous pouvez modifier les adresses IP ou les identifiants dans ce fichier si ncessaire, mais les valeurs par dfaut sont configures pour fonctionner directement.

3.  **Lancer linfrastructure**
    Cest l'tape principale. Vagrant lira le `Vagrantfile`, crera les trois machines virtuelles et excutera automatiquement les scripts de provisionnement pour installer toutes les dpendances, configurer les bases de donnes et dmarrer les applications avec PM2.
    ```sh
    vagrant up
    ```
    Ce processus prendra quelques minutes car il tlcharge limage Ubuntu et installe tous les logiciels.

4.  **Accder aux services**
    -   **API Gateway** : La passerelle est accessible depuis votre machine hte l'adresse `http://localhost:8080`.
    -   **Interface dadministration RabbitMQ** : Vous pouvez surveiller les files dattente RabbitMQ en naviguant vers `http://localhost:15672` dans votre navigateur Web. Utilisez les identifiants de votre fichier `.env` (dfaut : `rabbitmq_user` / `rabbitmq_password`).

## 4. Variables d'environnement requises

Les variables suivantes doivent tre dfinies dans le fichier `.env`.

| Variable                  | Description                                                | Valeur par dfaut      |
| :------------------------ | :--------------------------------------------------------- | :--------------------- |
| `INVENTORY_VM_IP`         | IP prive pour la VM dInventaire.                        | `192.168.56.11`        |
| `BILLING_VM_IP`           | IP prive pour la VM de Facturation.                       | `192.168.56.12`        |
| `INVENTORY_API_PORT`      | Port pour le service API dInventaire.                     | `8080`                 |
| `INVENTORY_DB_NAME`       | Nom de la base de donnes pour le service dInventaire.    | `movies_db`            |
| `INVENTORY_DB_USER`       | Utilisateur PostgreSQL pour la base de donnes dInventaire.| `inventory_user`       |
| `INVENTORY_DB_PASSWORD`   | Mot de passe de lutilisateur PostgreSQL dInventaire.     | `inventory_password`   |
| `BILLING_DB_NAME`         | Nom de la base de donnes pour le service de Facturation.  | `billing_db`           |
| `BILLING_DB_USER`         | Utilisateur PostgreSQL pour la base de donnes de Facturation.| `billing_user`         |
| `BILLING_DB_PASSWORD`     | Mot de passe de lutilisateur PostgreSQL de Facturation.   | `billing_password`     |
| `RABBITMQ_USER`           | Utilisateur RabbitMQ.                                      | `rabbitmq_user`        |
| `RABBITMQ_PASSWORD`     | Mot de passe RabbitMQ.                                     | `rabbitmq_password`    |
| `RABBITMQ_VHOST`          | Hte virtuel RabbitMQ pour cette application.              | `billing_vhost`        |
| `RABBITMQ_QUEUE`          | Nom de la file dattente pour les messages de facturation. | `billing_queue`        |

## 5. Test de lAPI

Tous les tests doivent tre kuts contre lAPI Gateway fonctionnant sur `http://localhost:8080`.

### Postman / OpenAPI

Vous pouvez importer le fichier `openapi.yaml` inclus dans ce projet directement dans Postman ou tout autre client API prenant en charge les spcifications OpenAPI 3.0. Cela gnra automatiquement une collection de toutes les requates disponibles.

-   Dans Postman : `Fichier > Importer > Tlcharger openapi.yaml`

### Exemples `curl` manuels

**Service dInventaire (`/api/movies`)**

1.  **Cr er un film**
    ```sh
    curl -X POST http://localhost:8080/api/movies \
         -H "Content-Type: application/json" \
         -d '{"title": "The Matrix", "description": "Un hacker informatique apprend des rebelles mystrieux la vraie nature de sa ralit."}'
    ```

2.  **Obtenir tous les films**
    ```sh
    curl http://localhost:8080/api/movies
    ```

3.  **Rechercher un film par titre**
    ```sh
    curl "http://localhost:8080/api/movies?title=matrix"
    ```

4.  **Obtenir un film par ID** (remplacez `1` par un ID valide)
    ```sh
    curl http://localhost:8080/api/movies/1
    ```

5.  **Mettre jour un film** (remplacez `1` par un ID valide)
    ```sh
    curl -X PUT http://localhost:8080/api/movies/1 \
         -H "Content-Type: application/json" \
         -d '{"title": "The Matrix Reloaded"}'
    ```
6.  **Supprimer un film par ID** (remplacez `1` par un ID valide)
    ```sh
    curl -X DELETE http://localhost:8080/api/movies/1
    ```

**Service de Facturation (`/api/billing`)**

1.  **Publier une commande de facturation**
    Cette requ te envoie un message la file dattente RabbitMQ.
    ```sh
    curl -X POST http://localhost:8080/api/billing \
         -H "Content-Type: application/json" \
         -d '{"user_id": "usr_123", "number_of_items": 3, "total_amount": 99.97}'
    ```
    Vous devriez recevoir une rponse immdiate `202 Accepted`. Vous pouvez ensuite consulter linterface dadministration de RabbitMQ (`http://localhost:15672`) pour voir le message consomm.

## 6. Test de rsilience

Une caractristique cl de cette architecture est sa rsilience. LAPI Gateway peut accepter les requ tes de facturation mme si le consommateur de facturation est hors service.

1.  **Connectez-vous en SSH la VM de facturation :**
    ```sh
    vagrant ssh billing-vm
    ```

2.  **Arr tez lapplication de consommation de facturation :**
    ```sh
    pm2 stop billing-consumer
    ```

3.  **Publiez plusieurs requ tes de facturation depuis votre machine hte :**
    Utilisez la commande `curl` de la section ci-dessus pour envoyer quelques commandes de facturation. LAPI Gateway devrait rpondre avec `202 Accepted` pour chacune delles.

4.  **Vrifiez la file dattente RabbitMQ :**
    Allez sur `http://localhost:15672`. Connectez-vous et consultez l'onglet "Queues". Vous verrez que `billing_queue` a des messages "Ready" en attente dtre consomms.

5.  **Redmarrez le consommateur de facturation :**
    De retour dans la session SSH de `billing-vm`, excutez :
    ```sh
    pm2 restart billing-consumer
    ```

6.  **Observez le rsultat :**
    Surveillez lintersface dadministration de RabbitMQ. Les messages en file dattente seront consomms par le travailleur redmarr et traits. Vous pouvez le vrifier en consultant les journaux du consommateur :
    ```sh
    pm2 logs billing-consumer
    ```
    Le consommateur traitera tous les messages qui ont t mis en file dattente pendant quil tait hors ligne.

## 7. Gestion de l'environnement

-   **SSH dans une VM** : `vagrant ssh <nom_de_la_vm>` (par exemple, `vagrant ssh gateway-vm`)
-   **Dtruire l'environnement** : Pour arr ter et supprimer toutes les VM et leurs ressources, excutez : `vagrant destroy -f`
-   **Re-provisionner** : Si vous apportez des modifications aux scripts de provisionnement, vous pouvez les rappliquer avec : `vagrant provision`
