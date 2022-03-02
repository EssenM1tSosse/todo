from flask import Flask                                 # Flask selbst
from flask import Response                              # vereinfacht das Absenden einer Antwort
from flask import json                                  # vereinfacht den Zugriff auf JSON-Daten
from flask import jsonify                               # vereinfacht das Erstellen von JSON-Daten
from flask import request                               # für einen vereinfachten Abruf der vom Client übermittelten Daten
from flask import escape                                # schützt vor XSS-Angriffe
from flask_jwt_extended import JWTManager               # für die Konfiguartion der JWT-Erweiterung
from flask_jwt_extended import create_access_token      # zur Anmeldung eines Benutzers
from flask_jwt_extended import get_jwt_identity         # Identifizierung eines Benutzers durch Abruf des access_token
from flask_jwt_extended import jwt_required             # Absicherung der Endpunkte, die nur angemeldet erreichbar sein sollen
import os                                               # für den Zugriff auf das Dateisystem (hier: database.db)
import datetime                                         # zur Definition, wie lange ein Access Token gültig sein darf
import uuid                                             # zur Generierung von GUIDs
import sqlite3                                          # für die Herstellung einer Verbindung zur Datenbank
from termcolor import colored                           # farbige Hervorhebungen für besser lesbare Ausgaben im Terminal
from flask_cors import CORS                             # [DEV] Vorraussetzung, um mit dem Swagger-Editor arbeiten zu können (Cross-Origin-Resource-Sharing)


#################
# VORBEREITUNGEN:
#################

# Vorbereitungen: zum Einfärben von wichtigen Konsolenausgaben mit colored():
os.system('color')

# Vorbereitungen: Wenn keine SQLite-Datenbank existiert, erstelle eine neue Datenbank-Datei ...
if not os.path.isfile('database.db'):
    print (colored('Die Datenbank (database.db) konnt nicht gefunden werden und wird jetzt neu erstellt!', 'blue'))
    connection = sqlite3.connect('database.db')
    # Erstelle die Tabellen:
    connection.execute('CREATE TABLE `user` (`user_id` TEXT, `name` TEXT, `password` TEXT)')
    connection.execute('CREATE TABLE `list` (`list_id` TEXT, `user_id` TEXT, `name` TEXT)')
    connection.execute('CREATE TABLE `entry` (`entry_id` TEXT, `list_id` TEXT, `eintrag` TEXT)')
    connection.close()
else:
    # Überprüfe, ob sich die Datenbank verbinden lässt:
    try:
        connection = sqlite3.connect('database.db')
        print(colored('Datenbankverbindung überprüfen ... OK!', 'green'))
    except Error as e:
        print(colored(e,'red'))

# Vorbereitungen: erzeuge das Objekt, um Flask zu initialisieren:
app = Flask(__name__)

# Vorbereitungen: geheimer Schlüssel der Flask-JWT-Extended Erweiterung
app.config["JWT_SECRET_KEY"] = '\xc0\xe8P\xc3G\xc8\xb3\x1f\x02\x82C:\x050\xd7l"\xdcuR\x95\xa7\xe8\x99'
jwt = JWTManager(app)

# Cross Origin Resource Sharing zum Testen mit editor.swagger.io zulassen:
CORS(app)

#####################
# Benutzerverwaltung:
#####################

# Meldet einen Benutzer an:
@app.route('/login/', methods = ['POST'])
def login():
    # Lese die empfangenen JSON-Daten ein:
    receivedjson= json.loads(request.data.decode('utf-8'))
    # Lese Benutzername und Passwort aus den JSON-Daten aus - mit escape() gegen XSS-Angriffe):
    name = escape(receivedjson['name'])
    password = escape(receivedjson['password'])
    # überprüfe auf Übereinstimmung mit der Datenbank:
    statement = "SELECT * FROM user WHERE name='"+str(name)+"' AND password='"+str(password)+"'"
    result = executeDB("get", statement)
    # Wenn der Login gültig ist...
    if len(result) == 1:
        user_id = result[0][0]
        # Erstelle einen Access-Token/JSON-Web-Token für den Benutzer: 
        access_token = create_access_token(identity=user_id, expires_delta=datetime.timedelta(days=1))
        return jsonify(access_token=access_token)
    else:
        #return "", "401 Benutzername und/oder Passwort sind falsch."
        return Response(response="Benutzername und/oder Passwort sind falsch.", status=401, content_type="text/html")
    
    
    
#######################
# ERSTELLUNG VON DATEN:
#######################

# erstellt eine neue Todo-Liste:
@app.route('/list/', methods=['POST'])
@jwt_required()
def createList():
    # identifiziere den Benutzer
    user_id = get_jwt_identity()
    # Lese die empfangenen JSON-Daten ein:
    receivedjson= json.loads(request.data.decode('utf-8'))
    name = escape(receivedjson['name'])
    # erstelle eine GUID für die neue Liste:
    list_id = str(uuid.uuid4())
    # speichere alles in der Datenbank:
    statement = "INSERT INTO list (list_id, user_id, name) VALUES ('"+str(list_id)+"', '"+str(user_id)+"', '"+str(name)+"')"
    executeDB("set", statement)
    # Erzeuge ein Dictionary für die Antwort-Daten ...
    jsondata = {}
    # ... und speichere darin den Name der Liste und die list_id:
    jsondata["name"] = name
    jsondata["list_id"] = list_id
    # Wandle das Dictionary zu JSON um:
    response = jsonify(dict(jsondata))
    # Setze den Status-Code für die Antwort:
    response.status_code = 200
    # Sende die Antwort:
    return response



# erstellt einen neuen Eintrag in einer Todo-Liste:
@app.route('/list/<list_id>/entry/', methods=['POST'])
@jwt_required()
def createEntry(list_id):
    # identifiziere den Benutzer
    user_id = get_jwt_identity()
    # hole die Ziel-Liste aus der Route:   
    list_id = f'{escape(str(list_id))}'
    # hole den Inhalt des Eintrages aus den JSON-Daten:
    receivedjson= json.loads(request.data.decode('utf-8'))
    # Lese die empfangenen JSON-Daten ein:
    eintrag = escape(receivedjson['eintrag'])
    # erstelle eine GUID für den neuen Eintrag:
    entry_id = str(uuid.uuid4())
    # speichere alles in der Datenbank:
    statement = "INSERT INTO entry (entry_id, list_id, eintrag) VALUES ('"+str(entry_id)+"', '"+str(list_id)+"', '"+str(eintrag)+"')"
    executeDB("set", statement)
    # Erzeuge ein Dictionary für die Antwort-Daten ...
    jsondata = {}
    # ... und speichere darin den Name der Liste und list_id:
    jsondata["entry_id"] = entry_id
    jsondata["list_id"] = list_id
    # Wandle das Dictionary zu JSON um:
    response = jsonify(dict(jsondata))
    # Setze den Status-Code für die Antwort:
    response.status_code = 200
    # Sende die Antwort:
    return response
    
    
    
# erstelle einen neuen Benutzer:
@app.route('/user/',methods = ['POST'])
def createUser():
    # Lese die empfangenen JSON-Daten ein:
    receivedjson= json.loads(request.data.decode('utf-8'))
    # Lese Benutzername und Passwort aus den JSON-Daten aus - mit escape() gegen XSS-Angriffe):
    name = escape(receivedjson['name'])
    password = escape(receivedjson['password'])
    # prüfe, ob der Benutzer bereits existiert:
    statement = "SELECT name FROM user WHERE name='"+str(name)+"'"
    result = executeDB("get", statement)
    # Wenn der Name bereits vergeben ist...
    if len(result) > 0:
        return Response(response="Benutzername existiert bereits.", status=500, content_type="text/html")
    else:
        # generiere eine GUID für den neuen Benutzer:
        user_id = str(uuid.uuid4())
        # speichere alles in der Datenbank:
        statement = "INSERT INTO user (user_id, name, password) VALUES ('"+str(user_id)+"', '"+str(name)+"', '"+str(password)+"')"
        executeDB("set", statement)
        # Erzeuge ein Dictionary für die Antwort-Daten ...
        jsondata = {}
        # ... und speichere darin Benutzername und user_id:
        jsondata["name"] = name
        jsondata["user_id"] = user_id
        # Wandle das Dictionary zu JSON um:
        response = jsonify(dict(jsondata))
        # Setze den Status-Code für die Antwort:
        response.status_code = 200
        # Sende die Antwort:
        return response



#####################
# AUSLESEN VON DATEN:
#####################

# liefert alle Todo-Listen eines angemeldeten Benutzers:
@app.route('/list/', methods=['GET'])
@jwt_required()
def getLists():
    # identifiziere den Benutzer
    user_id = get_jwt_identity()
    # rufe alle Todo-Listen aus der Datenbank ab:
    statement = "SELECT list_id, name FROM list WHERE user_id='"+str(user_id)+"'"
    result = executeDB("get", statement)
    if len(result) == 0:
        return Response(response="Es konnten keine Todo-Listen gefunden werden.", status=404, content_type="text/html")
    else:
        # Speichere alle Ergebnisse in einer Liste:
        entries= []
        for tupel in result:
            thisdict = {"list_id":tupel[0], "name":tupel[1]} 
            entries.append(thisdict)
        jsondata = {}
        # füge die Daten zusammen:
        jsondata["entries"] = entries
        # Wandle die Daten zu JSON um:
        response = jsonify(jsondata)
        # Setze den Status-Code für die Antwort:
        response.status_code = 200
        # Sende die Antwort:
        return response



# liefert alle Einträge einer Todo-Liste:
@app.route('/list/<list_id>', methods=['GET'])
@jwt_required()
def getEntries(list_id):
    # identifiziere den Benutzer
    user_id = get_jwt_identity()
    # hole die Ziel-Liste aus der Route:   
    list_id = f'{escape(str(list_id))}'
    # rufe alle Einträge der Todo-Liste aus der Datenbank ab:
    statement = "SELECT entry_id, eintrag FROM entry WHERE list_id='"+str(list_id)+"'"
    result = executeDB("get", statement)
    if len(result) == 0:
        return Response(response="Die Liste konnte nicht gefunden werden.", status=404, content_type="text/html")
    else:
        # Speichere alle Ergebnisse in einer Liste:
        entries= []
        for tupel in result:
            thisdict = {"entry_id":tupel[0], "eintrag":tupel[1]} 
            entries.append(thisdict)
        jsondata = {}
        # füge die Daten zusammen:
        jsondata["list_id"] = list_id
        jsondata["entries"] = entries
        # Wandle die Daten zu JSON um:
        response = jsonify(jsondata)
        # Setze den Status-Code für die Antwort:
        response.status_code = 200
        # Sende die Antwort:
        return response



# liefert eine Liste aller Benutzer zurück:
@app.route('/users/', methods=['GET'])
@jwt_required()
def getUser():
    # identifiziere den Benutzer
    user_id = get_jwt_identity()
    # rufe alle Benutzer aus der Datenbank ab:
    statement = "SELECT user_id, name FROM user"
    result = executeDB("get", statement)
    if len(result) == 0:
        return Response(response="Es konnten keine Benutzer gefunden werden.", status=404, content_type="text/html")
    else:
        # Speichere alle Ergebnisse in einer Liste:
        entries= []
        for tupel in result:
            thisdict = {"user_id":tupel[0], "name":tupel[1]} 
            entries.append(thisdict)
        jsondata = {}
        # füge die Daten zusammen:
        jsondata["entries"] = entries
        # Wandle die Daten zu JSON um:
        response = jsonify(jsondata)
        # Setze den Status-Code für die Antwort:
        response.status_code = 200
        # Sende die Antwort:
        return response



######################
# Verändern von Daten:
######################

# Aktualisiert einen bestehenden Eintrag:
@app.route('/list/<list_id>/entry/<entry_id>', methods=['POST'])
@jwt_required()
def updateEntry(list_id, entry_id):
    # identifiziere den Benutzer
    user_id = get_jwt_identity()
    # ermittle die list_id des Eintrages
    statement = "SELECT list_id FROM entry WHERE entry_id = '"+str(entry_id)+"'"
    result = executeDB("get", statement)
    list_id = result[0][0]
    # ermittle die user_id der Liste
    statement = "SELECT user_id FROM list WHERE list_id = '"+str(list_id)+"'"
    result = executeDB("get", statement)
    user_db = result[0][0]
    # Ist der Benutzer auch Besitzer des Eintrags? ... dann führe die Änderungen durch:
    if user_db == user_id:
        # Lese die empfangenen JSON-Daten ein:
        receivedjson= json.loads(request.data.decode('utf-8'))
        # Lese den neuen Eintragstext aus - mit escape() gegen XSS-Angriffe):
        newEntry = str(escape(receivedjson['eintrag']))
        # aktualisiere den Eintrag in der Datenbank:
        statement = "UPDATE entry SET eintrag = '"+newEntry+"' WHERE entry_id = '"+str(entry_id)+"'"
        executeDB("set", statement)
        return Response(response="Der Eintrag wurde geändert", status=200, content_type="text/html")
    else:
        return Response(response="Interner Serverfehler.", status=500, content_type="text/html")



# Aktualisiert den Namen einer bestehenden Todo-Liste:
@app.route('/list/<list_id>', methods=['POST'])
@jwt_required()
def updateListName(list_id):
    # identifiziere den Benutzer
    user_id = get_jwt_identity()
    # Lese die empfangenen JSON-Daten ein:
    receivedjson= json.loads(request.data.decode('utf-8'))
    # Lese den neuen Eintragstext aus - mit escape() gegen XSS-Angriffe):
    newName = str(escape(receivedjson['name']))
    # aktualisiere den Eintrag in der Datenbank:
    statement = "UPDATE list SET name = '"+newName+"' WHERE list_id = '"+str(list_id)+"' AND user_id = '"+user_id+"'"
    count = executeDB("set", statement)
    if count != 0:
        return Response(response="Der Listenname wurde aktualisiert.", status=200, content_type="text/html")
    else:
        return Response(response="Fehler beim Aktualisieren der Listenbezeichnung.", status=500, content_type="text/html")



####################
# Löschen von Daten:
####################

# Löscht einen Eintrag:
@app.route('/list/<list_id>/entry/<entry_id>', methods=['DELETE'])
@jwt_required()
def deleteEntry(list_id, entry_id):
    # identifiziere den Benutzer
    user_id = get_jwt_identity()
    # ermittle die list_id des Eintrages
    statement = "SELECT list_id FROM entry WHERE entry_id = '"+str(entry_id)+"'"
    result = executeDB("get", statement)
    list_id = result[0][0]
    # ermittle die user_id der Liste
    statement = "SELECT user_id FROM list WHERE list_id = '"+str(list_id)+"'"
    result = executeDB("get", statement)
    user_db = result[0][0]
    # Ist der Benutzer auch Besitzer des Eintrags? ... dann führe die Änderungen durch:
    if user_db == user_id:
        statement = "DELETE FROM entry WHERE entry_id = '"+str(entry_id)+"'"
        executeDB("set", statement)
        return Response(response="Der Eintrag wurde gelöscht.", status=200, content_type="text/html")
    else:
        return Response(response="Der Eintrag konnte nicht gefunden werden.", status=500, content_type="text/html")
  
  

# Löscht eine Todo-Liste mit all ihren Einträgen:
@app.route('/list/<list_id>', methods=['DELETE'])
@jwt_required()
def deleteList(list_id):
    # identifiziere den Benutzer
    user_id = get_jwt_identity()
    # ermittle die user_id des Eintrages
    statement = "SELECT user_id FROM list WHERE list_id = '"+str(list_id)+"'"
    result = executeDB("get", statement)
    user_db = result[0][0]
    if user_db == user_id:
        statement = "DELETE FROM entry WHERE list_id = '"+str(list_id)+"'"
        executeDB("set", statement)
        statement = "DELETE FROM list WHERE list_id = '"+str(list_id)+"'"
        executeDB("set", statement)
        return Response(response="Die Liste wurde gelöscht.", status=200, content_type="text/html")
    else:
        return Response(response="Die Liste konnte nicht gefunden werden.", status=404, content_type="text/html")
        


# Löscht einen Benutzer:
@app.route('/user/<user_id>', methods=['DELETE'])
@jwt_required()
def deleteUser(user_id):
    # identifiziere den Benutzer
    user_id = get_jwt_identity()
    statement = "DELETE FROM user WHERE user_id = '"+str(user_id)+"'"
    count = executeDB("set", statement)
    if count != 0:
        return Response(response="Der Benutzer wurde gelöscht.", status=200, content_type="text/html")
    else:
        return Response(response="Der Benutzer konnte nicht gefunden werden.", status=404, content_type="text/html")



#########################################################
# ausgelagerte Funktion zur Absetzung von SQL-Statements:
#########################################################
def executeDB(action, sql):
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()
    if (action=="set"): 
        cursor.execute(sql)
        connection.commit()
        count = cursor.rowcount
        connection.close()
        return count
    if (action=="get"):
        cursor.execute(sql)
        rows = cursor.fetchall()
        connection.close()
        return rows


# starte Flask-Server
if __name__ == '__main__':
    app.run(port=5000)
    
    
'''    
TODO: 

1. API-Spezifikation überarbeiten: Schemas und References!
2. Validierung und Error-Codes ausbauen
3. Lesbarkeit erhöhen
'''