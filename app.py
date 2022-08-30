import random  # import random
import sqlite3  # import sqlite
from flask import Flask, render_template, request, url_for, flash, redirect  # import flask
from werkzeug.exceptions import abort  # import abort
from datetime import datetime  # import datetime
import hashlib  # import hashlib
import subprocess  # import subprocess

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Sompie69420'
hash_seed = '54e7ca378874d8f376500a8fff8ad6f4cd8623cbe46b9056e619a511b4d50761'  # hash seed

# OC
uuid = subprocess.check_output('wmic csproduct get uuid').decode().split('\n')[1].strip()


# Random password generator
def random_reset_pass():
    passwords = {'DonBosco2022', 'sompie', 'cookie', 'E104', 'blubmaster'}
    password = random.choice(tuple(passwords))
    return password


# Connection
def get_db_connection():
    conn = sqlite3.connect('identifier.sqlite')
    conn.row_factory = sqlite3.Row
    return conn


# Naam functie
def get_user():
    ip = request.remote_addr
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE ip = ?", (ip,)).fetchall()
    conn.close()
    return user


# Get functies
# Gebruiker
def get_gebruiker(gebruiker_id):
    conn = get_db_connection()
    gebruiker = conn.execute("SELECT * FROM users WHERE id = ?", (gebruiker_id,)).fetchone()
    conn.close()

    if gebruiker is None:
        abort(404)
    return gebruiker


# Component
def get_comp(stock_id):
    conn = get_db_connection()
    stock = conn.execute("SELECT * FROM stock S LEFT JOIN locatie L ON S.id_locatie = L.locatie_id WHERE id_item = ?",
                         (stock_id,)).fetchone()
    conn.close()
    return stock

# Magazijn items
def get_item(mag_id):
    conn = get_db_connection()
    mag = conn.execute("SELECT * FROM magazijn M LEFT JOIN locatie l on M.locatie_id = l.locatie_id WHERE id_mag = ?",
                       (mag_id,)).fetchone()
    conn.close()
    return mag


# Password Hashing
def sha256(input, seed):
  return hashlib.sha256((str(input) + str(seed)).encode('utf-8')).hexdigest()


# |-------------|
# |    login    |
# |-------------|
# runt functie bij elke gebeurtenis
@app.before_request
def logincheck():
    # Alleen voor deze functies
    if request.endpoint in ['home', 'stocktype', 'type_create', 'stock', 'stock_create', 'stock_edit',
                            'stock_info', 'magazijn', 'magazijn_create', 'magazijn_edit', 'magazijn_info',
                            'magazijn_leen', 'magazijn_leen_barcode', 'gebruikers', 'gebruiker_edit',
                            'gebruiker_create', 'reset', 'locatie', 'locatie_create', 'locatie_info']:
        ip = request.remote_addr  # neemt ip van user
        conn = get_db_connection()  # connect met database
        ipconf = conn.execute('SELECT * FROM users where inlog = ? and ip = ?', ("Ja", ip)).fetchone()  # kijkt of ip ingelogd is

        if ipconf is None:  # als ip is ingelogd
            flash("U bent uitgelogd")  # flash dat persoon is uitgelogd
            return redirect(url_for('login'))  # brengt user naar de login pagina


@app.route('/Logout', methods=('GET', 'POST'))
def logout():
    ip = request.remote_addr  # haalt ip van user
    conn = get_db_connection()  # connect met database
    conn.execute('UPDATE users SET ip = ?, inlog = ?, inlogtijd = ? WHERE ip = ?',
                 ('', 'Neen', '', ip))  # pakt inlog ip en inlogtijd en zet deze op '' ook zet hij inlog op 'Neen'
    conn.commit()  # zorgt dat de update gebeurt
    conn.close()  # breekt de connectie met de database
    return redirect(url_for('login'))  # brengt de user naar de login screen


@app.route('/<int:gebruiker_id>/Logout On ID', methods=('GET', 'POST'))
def logoutid(gebruiker_id):  # pakt id van de user
    conn = get_db_connection()  #connect met database
    conn.execute('UPDATE users SET ip = ?, inlog = ?, inlogtijd = ? WHERE id= ?',
                 ('', 'Neen', '', gebruiker_id))  # waar de id gelijk is als dat van de user word aangepast naar logout modus in database
    conn.commit()  # zorgt dat de update gebeurt
    conn.close()  # verbreekt de connectie met databse
    return redirect(url_for('gebruikers'))  # brengt admin user naar gebruikers


# Main route
@app.route('/', methods=('GET', 'POST'))
def login():
    ip = request.remote_addr  # haalt ip van user
    now = datetime.now()  # haalt tijd op
    tijd = now.strftime('%d-%m-%Y, %H:%M')  # zet tijd in juiste format
    conn = get_db_connection()  # maakt verbinding met database
    ipconf = conn.execute('SELECT ip FROM users where inlog = ?', ('Ja',)).fetchall()  # kijkt of ip al ingelogd is

# kijkt of ip al gebruikt word bij een account
    for ips in ipconf:
        if ips[0] == ip:  # als ip al gebruikt word stuur gebruiker naar home
            return redirect(url_for('home'))

    if request.method == 'POST':
        wachtwoord_hash = sha256(request.form['wachtwoord'], hash_seed)  # pakt password en hashd het
        naam = request.form['naam'].title()  # pakt naam en zet alles kleine letter behalve eerste letter

        if not naam:  # als er geen naam is geef error
            flash('Geef een naam!')

        elif not wachtwoord_hash:  # als geen wachtwoord is geef error
            flash('Geef een wachtoord!')
        else:
            user = conn.execute('SELECT * FROM users where voornaam = ? and wachtwoord = ?',
                                (naam, wachtwoord_hash,)).fetchone()  # neemt alle gebruiker met naam en wachtwoord
            if user is None:  # als geen gebruiker is geef error
                flash('De combinatie van de naam en het wachtwoord bestaat niet!')
            else:
                conn.execute('UPDATE users SET ip = ?, inlog = ?, inlogtijd = ? WHERE voornaam = ? AND wachtwoord = ?',
                             (ip, "Ja", tijd, naam, wachtwoord_hash,)).fetchone()
                # update user naar login modus in databse met inlogtijd en inlog ip
                conn.commit()  # zorgt dat update gebeurt
                resetcheck = conn.execute("SELECT reset FROM users WHERE voornaam = ? AND wachtwoord = ?",
                                          (naam, wachtwoord_hash)).fetchall()
                # kijkt of account gereset is
                for r in resetcheck:
                    if r[0] == 'Neen':  # als account niet gereset is breng user naar home
                        return redirect(url_for('home'))
                    else:
                        return redirect(url_for('reset'))  # anders breng user naar reset page

            conn.close()  # verbreek connectie database
    return render_template('inlog.html')  # rendert de login pagina

# |------------|
# |    Home    |
# |------------|


@app.route('/Home', methods=('GET', 'POST'))
def home():
    user = get_user()  # neemt user info
    conn = get_db_connection()  # connect met database
    stock = conn.execute("SELECT * FROM stock S INNER JOIN locatie L ON S.id_locatie = L.locatie_id WHERE aantal < 10")  # selecteerd alles van stock waar aantal minder is dan 10
    uitgeleend = conn.execute("SELECT * FROM mlog M inner join users u on u.id = M.user_id INNER JOIN magazijn M2 ON "  # selecteerd alles van magazijn dat is uitgeleend
                              "M2.id_mag = M.item_id where datumin = 'None'")
    return render_template('home.html', stock=stock, user=user, uitgeleend=uitgeleend)  # renderd de login pagina

# |------------|
# |    Stock   |
# |------------|


@app.route('/Stock Type', methods=('GET', 'POST'))
def stocktype():
    user = get_user()  # neemt user info
    conn = get_db_connection()  # connect met database
    types = conn.execute("SELECT * FROM stypes")  #conn selecteerd alle stock types

    return render_template('stocktype.html', types=types, user=user)  # renderd de login pagina


@app.route('/<int:type_id>/Type Delete', methods=('GET', 'POST'))
def type_del(type_id):  # neemt type id
    conn = get_db_connection()  # connect met database
    ip = request.remote_addr  # pakt ip van user
    check = conn.execute("SELECT * FROM users WHERE ip = ? AND rang = '2'", (ip,)).fetchone()  # kijkt of user die inglogd is de juiste rang heeft

    if check is None:  # als ze geen rang hebben geef error
        flash("U hebt geen toegang voor het verwijderen van Types")
        return redirect(url_for('stocktype'))
    conn.execute("DELETE FROM stypes WHERE stype_id = ?", (type_id,)).fetchone()  # anders delete waar type id gelijk is
    conn.commit()  # zorgt voor de delete
    conn.close()  # verbreekt de connectie
    return redirect(url_for('stocktype'))


@app.route('/Type Create', methods=('GET', 'POST'))
def type_create():
    user = get_user()  # haalt user info
    conn = get_db_connection()  # connect met database
    ip = request.remote_addr  # haalt ip van de user
    check = conn.execute("SELECT * FROM users WHERE ip = ? AND rang = '2'", (ip,)).fetchone()  # kijkt of user juiste rang heeft

    if check is None:  # als niet juist rang is geef error
        flash("U hebt geen toegang voor aanmaken van een type")
        return redirect(url_for('stock'))
    if request.method == 'POST':  # als create button word gebruikt
        naam = request.form['naam'].title()
        check = conn.execute("SELECT * FROM stypes WHERE naam = ?", (naam,)).fetchone() # selecteer alle types
        if not not check:  # als type bestaat geef error
            flash("Dit Type betaat al")
        elif not naam:  # als geen benaming geef error
            flash("Geef een type benaming")
        else:  # anders voeg type toe aan database
            conn.execute("INSERT INTO stypes (naam) VALUES (?)", (naam,))
            conn.commit()
            return redirect(url_for('stocktype'))
    return render_template('stocktypecreate.html', user=user)


@app.route('/Componenten', methods=('GET', 'POST'))
def stock():
    user = get_user()  # neemt info van user
    conn = get_db_connection()  # maakt verbinding met database
    stocks = conn.execute("SELECT * FROM stock S LEFT JOIN locatie L ON S.id_locatie = L.locatie_id "
                          "ORDER BY type, naam, barcode")  # selecteer stock gesorteerd op type naam en barcode
    return render_template('stock.html', user=user, stocks=stocks)


@app.route('/Componenten Create', methods=('GET', 'POST'))
def stock_create():
    user = get_user()  # neemt info van user
    conn = get_db_connection()  # maakt verbinding met database
    types = conn.execute("SELECT * FROM stypes ORDER BY naam").fetchall()  # selecteerd alle types
    locaties = conn.execute("SELECT * FROM locatie ORDER BY lokaal,kast").fetchall()  # selecteerd alle locaties
    ip = request.remote_addr  # pakt ip van user
    check = conn.execute("SELECT * FROM users WHERE ip = ? AND rang = '2'", (ip,)).fetchone() # kijkt of user juiste rang heeft

    if check is None:  # als geen juiste rang is geef error
        flash("U hebt geen toegang voor het aanmaken van componenten")
        return redirect(url_for('stock'))
    if request.method == 'POST':
        naam = request.form['naam']
        barcode = request.form['barcode']
        aantal = request.form['aantal']
        type = request.form['type']
        locatie = request.form['locatie']

        if not naam:  # als geen naam geef error
            flash("Geef component naam")
        elif not aantal:  #app als geen aantal geef error
            flash("Geef een aantal")
        elif not type:  # als geen type geef error
            flash("Geef een type")
        else:  # anders voeg item toe aan database
            conn.execute("INSERT INTO stock (naam, barcode, aantal, type, id_locatie) VALUES (?,?,?,?,?)",
                         (naam, barcode, aantal, type, locatie))
            conn.commit()
            conn.close()
            return redirect(url_for('stock'))
    return render_template('stockcreate.html', types=types, locaties=locaties, user=user)


@app.route('/<int:stock_id>/Componenten Edit', methods=('GET', 'POST'))
def stock_edit(stock_id):  # neemt stock id
    user = get_user()  # neemt info van users
    comp = get_comp(stock_id)  # neemt info van component
    conn = get_db_connection()  # maakt connectie met database
    ip = request.remote_addr  # neemt ip van users
    check = conn.execute("SELECT * FROM users WHERE ip = ? AND rang = '2'", (ip,)).fetchone()  # kijkt of user juiste rang heeft

    if check is None:  # als niet juiste rang geef error
        flash("U hebt geen toegang voor het aanpassen van componenten")
        return redirect(url_for('stock'))
    types = conn.execute("SELECT * FROM stypes ORDER BY naam").fetchall()  # neem alle types gesorteerd op naam
    locaties = conn.execute("SELECT * FROM locatie ORDER BY lokaal,kast").fetchall()  # neem alle locaties gesorteerd op lokaal en kastnummer

    if request.method == 'POST':
        naam = request.form['naam']
        barcode = request.form['barcode']
        aantal = request.form['aantal']
        type = request.form['type']
        locatie = request.form['locatie']

        if not naam:  # als geen naam geef error
            flash("Geef component naam")
        elif not aantal:  # als geen aantal geef error
            flash("Geef een aantal")
        elif not type:  # als geen type geef error
            flash("Geef een type")
        else:
            conn.execute("UPDATE stock SET naam = ?, barcode = ?, aantal = ?, type = ?,id_locatie = ? "
                         "WHERE id_item = ?", (naam, barcode, aantal, type, locatie, stock_id,))
            # update stock waar itemid gelijk is
            conn.commit()  # zorgt voor de update
            conn.close()  # verbreekt connectie met database
            return redirect(url_for('stock'))
    return render_template('stockedit.html', types=types, locaties=locaties, comp=comp, user=user)


@app.route('/<int:stock_id>/Componenten Delete', methods=('GET', 'POST'))
def stock_del(stock_id):  #neemt stock id
    conn = get_db_connection()  # connect met databse
    ip = request.remote_addr  # neemt ip van users
    check = conn.execute("SELECT * FROM users WHERE ip = ? AND rang = '2'", (ip,)).fetchone()  # kijkt of user juiste rang heeft

    if check is None:  # als user niet juiste rang heeft geef error
        flash("U hebt geen toegang voor het verwijderen van componenten")
        return redirect(url_for('stock'))
    conn.execute("DELETE FROM stock WHERE id_item = ?", (stock_id,)).fetchone()  # delete waar stock id gelijk is
    conn.commit()  # zorgt dat stock delete word
    conn.execute("DELETE FROM slog WHERE id_item = ?", (stock_id,)).fetchone()  # delete log van stock id
    conn.commit()  # zorgt dat log delete word
    conn.close()  # verbreek connectie met database
    return redirect(url_for('stock'))


@app.route('/<int:stock_id>/Component Remove')
def stock_remove(stock_id):  # neemt id van stock
    conn = get_db_connection()  # connect met database
    ip = request.remote_addr  # neemt ip van user
    checkblock = conn.execute("SELECT * FROM users WHERE ip = ? AND block = 'Ja'", (ip,)).fetchone()  # kijkt of user geblockeerd is
    if checkblock: # als user geblockeerd is geef error
        flash("Uw account is geblockeerd")
        return redirect(url_for('stock'))
    aantal = conn.execute("SELECT aantal FROM stock WHERE id_item = ?", (stock_id,)).fetchone()[0]  # selecteerd aantal van item waar stock id gelijk is
    if aantal != 0:  # als aantal niet nul is neem 1 aantal waar stock id gelijk is
        conn.execute("UPDATE stock SET aantal = aantal-1 WHERE id_item = ?", (stock_id,))
        conn.commit()
        user = get_user() # neemt user info
        now = datetime.now()  # pakt datum
        tijd = now.strftime('%d-%m-%Y, %H:%M')  # zet datum in juiste format

        for i in user:
            user_id = i[0]  # neemt user id
        conn = get_db_connection()
        check = conn.execute("SELECT * FROM slog WHERE id_item = ? AND id_user = ?", (stock_id, user_id,)).fetchone()  # selecteerd alles van stock log
        if not check: # als nog geen log is gemaakt maak er 1
            conn.execute("INSERT INTO slog (id_user, id_item, aantal, datum) values (?,?,?,?)",
                         (user_id, stock_id, 0, tijd))
            conn.commit()
            # update de log
        conn.execute("UPDATE slog SET aantal = aantal +1, datum = ? WHERE id_item = ? AND id_user = ?",
                     (tijd, stock_id, user_id))
        conn.commit()
    else: # als er 0 stock is en de knop word gebruikt geef error
        flash("Je kan niet minder dan 0 in een stock hebben")
    conn.close()  # verbreek connectie met database
    return redirect(url_for('stock'))


@app.route('/<int:stock_id>/Component Add')
def stock_add(stock_id):  # neemt id van stock
    user = get_user()  # neemt info van user
    now = datetime.now()  # neemt datum
    tijd = now.strftime('%d-%m-%Y, %H:%M')  # zet datum in juiste format
    for i in user:
        user_id = i[0]  # neemt id van user
    conn = get_db_connection()  # connect met database
    i = conn.execute("SELECT aantal FROM slog WHERE id_item = ? AND id_user = ?", (stock_id, user_id,)).fetchall()  # selecteer aantal van de user
    for aantal2 in i:
        aantal = aantal2[0]
    if not i: # als nog geen stock log bestaat maak 1 aan
        conn.execute("INSERT INTO slog (id_user, id_item, aantal, datum) values (?,?,?,?)",
                     (user_id, stock_id, 0, tijd))
        conn.commit()
    elif aantal != "0":  # als aantal 0 is
        check = conn.execute("SELECT * FROM slog WHERE id_item = ? AND id_user = ?", (stock_id, user_id,)).fetchone()  # selecteer alles van stock log waar item id is en user id is
        if not check:  # als log bestaat maak een log
            conn.execute("INSERT INTO slog (id_user, id_item, aantal, datum) values (?,?,?,?)",
                         (user_id, stock_id, 0, tijd))
            conn.commit()
        conn.execute("UPDATE slog SET aantal = aantal -1, datum = ? WHERE id_item = ? AND id_user = ?",
                     (tijd, stock_id, user_id))  # neemt 1 aantal van de user in de log
        conn.commit()
        conn.execute("UPDATE stock SET aantal = aantal+1 WHERE id_item = ?", (stock_id,))  # geeft 1 item terug in stock
        conn.commit()
        conn.close()  # verbreek connectie met database
    return redirect(url_for('stock'))


@app.route('/<int:stock_id>/Component Log')
def stock_info(stock_id):  # neemt stock info
    user = get_user()  # neemt user info
    users = get_user()  # neemt info van user voor log
    stocks = get_comp(stock_id)  # neemt info van stock
    conn = get_db_connection()  # maakt connectie met database
    logs = conn.execute("SELECT * FROM slog S inner join users U on id_user=U.id "
                 "INNER JOIN stock S2 ON S.id_item=S2.id_item WHERE S2.id_item = ?", (stock_id,)).fetchall()
    # selecteer alles van stock log waar stock id gelijk is
    return render_template('stockinfo.html', stocks=stocks, users=users, logs=logs, user=user)


# |----------------|
# |    Magazijn    |
# |----------------|
@app.route('/Magazijn', methods=('GET', 'POST'))
def magazijn():
    user = get_user()  # neemt user info
    conn = get_db_connection()  # connect met database
    magazijns = conn.execute("SELECT * FROM magazijn M inner join locatie l on M.locatie_id = l.locatie_id ORDER BY "
                             "uitgeleend DESC, L.lokaal, L.kast, M.naam")  # neemt alle info van magazijn gesorteerd op lokaal kast en naam
    if request.method == 'POST':
        barcode = request.form.get('barcode')  # vraagt barcode
        check = conn.execute("SELECT * FROM magazijn WHERE barcode = ?", (barcode,)).fetchone()  # selecteer alles waar barcode gelijk is
        if not check:  # als geen check geer error
            flash("Er bestaat geen item met deze barcode")
            return render_template('magazijn.html', user=user, magazijns=magazijns)
        elif check != 'None':  # anders ga naar magazijn leen
            return redirect(url_for('magazijn_leen_barcode', barcode=barcode))
    return render_template('magazijn.html', user=user, magazijns=magazijns)


@app.route('/Magazijn Create', methods=('GET', 'POST'))
def magazijn_create():
    user = get_user()  # neemt alle info van user
    conn = get_db_connection()  # connect met database
    locaties = conn.execute("SELECT * FROM locatie ORDER BY lokaal,kast").fetchall()  # neemt alle locaties
    ip = request.remote_addr  # neemt ip van user
    check = conn.execute("SELECT * FROM users WHERE ip = ? AND rang = '2'", (ip,)).fetchone()  # kijkt of user juiste rang heeft

    if check is None:  # als user niet juiste rang heeft geef error
        flash("U hebt geen toegang voor het aanmaken van magazijn items")
        return redirect(url_for('stock'))
    if request.method == 'POST':
        naam = request.form['naam']
        barcode = request.form['barcode']
        locatie = request.form['locatie']

        barcheck = conn.execute("SELECT barcode FROM magazijn WHERE barcode = ?", (barcode,)).fetchall()  # kijkt of barcode al bestaat

        if barcheck:  # als barcode bestaat geef error
            flash("Deze barcode bestaat al")

        elif not naam:  # als geen naam geef error
            flash("Geef item naam")
        else:
            conn.execute("INSERT INTO magazijn (naam, barcode, locatie_id) VALUES (?,?,?)",
                         (naam, barcode, locatie,))  # steekt item in magazijn
            conn.commit()
            conn.close()  # verbreekt connectie database
            return redirect(url_for('magazijn'))
    return render_template('magazijncreate.html', locaties=locaties, user=user)


@app.route('/<int:magazijn_id>/Magazijn Edit', methods=('GET', 'POST'))
def magazijn_edit(magazijn_id):  # pakt magazijn id
    user = get_user()  # neemt user info
    conn = get_db_connection()  # connect met database
    ip = request.remote_addr  # patk ip van user
    check = conn.execute("SELECT * FROM users WHERE ip = ? AND rang = '2'", (ip,)).fetchone()  # kijkt of user juiste rang heeft

    if check is None:  # als user niet juiste rang heeft geef error
        flash("U hebt geen toegang voor het aanpassen van Magazijn Items")
        return redirect(url_for('magazijn'))
    item = get_item(magazijn_id)
    locaties = conn.execute("SELECT * FROM locatie ORDER BY lokaal,kast").fetchall()  # pakt alle locaties

    if request.method == 'POST':
        naam = request.form['naam']
        barcode = request.form['barcode']
        locatie = request.form['locatie']

        if not naam:  # als naam niet bestaat geef error
            flash("Geef item naam")
        elif not barcode:  # als geen barcode geef error
            flash("Geef barcode")
        elif not locatie:  # als geen locatie geef error
            flash("Geef locatie")
        else:  # anders update item
            conn.execute("UPDATE magazijn SET naam = ?, barcode = ?, locatie_id = ? WHERE id_mag = ?",
                         (naam, barcode, locatie, magazijn_id,))
            conn.commit()
            conn.close()  # verbreek connectie met database
            return redirect(url_for('magazijn'))
    return render_template('magazijnedit.html', locaties=locaties, item=item, user=user)


@app.route('/<int:magazijn_id>/Magazijn Log/', methods=('post', 'get'))
def magazijn_info(magazijn_id):  # pakt id van magazijn
    user = get_user()  # pakt user info
    users = get_user()  # pakt user info voor log
    magazijn = get_item(magazijn_id)  # pakt magazijn item info
    conn = get_db_connection()  # maak connectie met database

    if request.method == 'POST':
        logid = request.form['logid']  # vraagt id op
    else:
        logid = 0  # anders zet id op 0

    logs = conn.execute("SELECT * FROM mlog M inner join users U on M.user_id=U.id "
                 "INNER JOIN magazijn M2 ON M.item_id = M2.id_mag WHERE M2.id_mag = ? ORDER BY datumuit DESC",
                        (magazijn_id,)).fetchall()  # selecteer alles van magazijn log gesorteerd op datum uit

    log = conn.execute("SELECT * FROM mlog M inner join users U on M.user_id=U.id "
                       "INNER JOIN magazijn M2 ON M.item_id = M2.id_mag INNER JOIN locatie l on "
                       "M2.locatie_id = l.locatie_id WHERE M.id = ?", (logid,)).fetchone()
    # selecteer alles van magazijn log waar id hetzelfde is
    return render_template('magazijninfo.html', magazijn=magazijn, users=users, user=user, logs=logs, log=log)


@app.route('/<int:magazijn_id>/Magazijn Delete', methods=('GET', 'POST'))
def magazijn_del(magazijn_id):  # neem magazijn id
    conn = get_db_connection()  # connect met database
    ip = request.remote_addr  # neemt ip van user
    check = conn.execute("SELECT * FROM users WHERE ip = ? AND rang = '2'", (ip,)).fetchone()  # kijkt of user juiste rang heeft

    if check is None:  # als user geen juiste rang heeft geef error
        flash("U hebt geen toegang voor het verwijderen van Magazijn Items")
        return redirect(url_for('magazijn'))
    conn.execute("DELETE FROM magazijn WHERE id_mag = ?", (magazijn_id,)).fetchone()
    conn.commit()  # delete magazijn item
    conn.execute("DELETE FROM mlog WHERE item_id = ?", (magazijn_id,)).fetchone()
    conn.commit()  # delete magazijn log
    conn.close()
    return redirect(url_for('magazijn'))


@app.route('/<int:magazijn_id>/Magazijn Lenen', methods=('GET', 'POST'))
def magazijn_leen(magazijn_id):  # pak magazijn id
    user = get_user()  # pakt user info
    ip = request.remote_addr  # pakt ip van user
    now = datetime.now()  # pakt datum
    tijd = now.strftime('%d-%m-%Y, %H:%M')  # zet datum in juiste format
    item = get_item(magazijn_id)  # neemt item info
    users = get_user()  # pakt user info voor magazijn log
    for useri in users:
        user1 = useri[0]  # pakt id van user
    conn = get_db_connection()  # connect met database
    check = conn.execute("SELECT uitgeleend FROM magazijn WHERE id_mag = ?", (magazijn_id,)).fetchone()[0]  # kijkt of item is uitgeleend

    checkblock = conn.execute("SELECT * FROM users WHERE ip = ? AND block = 'Ja'", (ip,)).fetchone()  # kijkt of user geblockt is
    if checkblock:  # als user is geblockd geef error
        flash("Uw account is geblockeerd")
        return redirect(url_for('magazijn'))

    elif request.method == 'POST':
        project = request.form['project']
        gebruik = request.form['gebruik']
        if check == "Neen":  # als item niet uitgeleend is zet hem op uitgeleend en zet data is de magazijn log
            conn.execute("UPDATE magazijn SET uitgeleend = 'Ja' WHERE id_mag = ?", (magazijn_id,))
            conn.commit()
            conn.execute("INSERT INTO mlog (user_id, project, gebruik, datumuit, item_id) VALUES (?,?,?,?,?)",
                         (user1, project, gebruik, tijd, magazijn_id,))
            conn.commit()
            conn.close()
            return redirect(url_for('magazijn'))
    return render_template('magazijnleen.html', item=item, user=user, users=useri, tijd=tijd)


@app.route('/Barcode/Magazijn Leen', methods=('GET', 'POST'))
def magazijn_leen_barcode():
    user = get_user()  # pakt user info
    conn = get_db_connection()  # connect met database
    ip = request.remote_addr  # pakt ip van user
    barcode = request.args.get('barcode', None)  # vraagt barcode van andere app route
    users = get_user()[0]  # pakt id van user
    user2 = get_user()  # pakt info van users
    for useri in user2:
        user3 = useri
    now = datetime.now()  # pakt tijd
    tijd = now.strftime('%d-%m-%Y, %H:%M')  # zet tijd in juiste format
    item = conn.execute("SELECT * FROM magazijn inner join locatie l on magazijn.locatie_id = l.locatie_id WHERE "
                        "barcode = ?", (barcode,)).fetchone()  # selecteer alles van magazijn waar barcode gelijk is
    magazijn_id = conn.execute("SELECT id_mag FROM magazijn WHERE barcode = ?", (barcode,)).fetchone()[0]  # Selecteer id van magazijn waar barcode is
    check = conn.execute("SELECT uitgeleend FROM magazijn WHERE barcode = ?", (barcode,)).fetchone()[0]  # kijkt of item uitgeleend is

    checkblock = conn.execute("SELECT * FROM users WHERE ip = ? AND block = 'Ja'", (ip,)).fetchone()  # kijkt of user geblockd is
    if checkblock:  # als user geblockd is geef error
        flash("Uw account is geblockeerd")
        return redirect(url_for('magazijn'))

    elif request.method == 'POST':
        project = request.form['project']
        gebruik = request.form['gebruik']
        if check == "Neen":  # als item niet is uitgeleend zet item op uitgeleend en zet magazijn log goed
            conn.execute("UPDATE magazijn SET uitgeleend = 'Ja' WHERE barcode = ?", (barcode,))
            conn.commit()
            conn.execute("INSERT INTO mlog (user_id, project, gebruik, datumuit, item_id) VALUES (?,?,?,?,?)",
                         (user3[0], project, gebruik, tijd, magazijn_id,))
            conn.commit()
            conn.close()
            return redirect(url_for('magazijn'))
    return render_template('magazijnleenbarcode.html', user=user, item=item, users=users, barcode=barcode, tijd=tijd)


@app.route('/<int:magazijn_id>/Magazijn Terug', methods=('GET', 'POST'))
def magazijn_terug(magazijn_id):  # pakt id van magazijn
    now = datetime.now()  # pakt datum
    tijd = now.strftime('%d-%m-%Y, %H:%M')  # zet datum in juiste format
    users = get_user()  # pakt user info
    for useri in users:
        user = useri[0]
    conn = get_db_connection()  # connect met database
    check = conn.execute("SELECT uitgeleend FROM magazijn WHERE id_mag = ?",(magazijn_id,)).fetchone()[0]  # kijkt of item is uitgeleend
    account = conn.execute("SELECT user_id FROM mlog WHERE item_id = ? ORDER BY datumuit DESC",(magazijn_id,)).fetchone()[0]  # kijkt of juiste user is
    admin = conn.execute("SELECT rang FROM users WHERE id = ?",(user,)).fetchone()[0]  # kijkt of user admin is
    if account == user or admin == '2':  # als user juist is of user admin is geef toestemming voor terug brengen
        if check == "Ja":  # zet magazijn item terug op leenbaar
            conn.execute("UPDATE magazijn SET uitgeleend = 'Neen' WHERE id_mag = ?",(magazijn_id,))
            conn.commit()
            conn.execute("UPDATE mlog SET datumin = ? WHERE item_id = ? AND datumin = 'None'",(tijd, magazijn_id,))
            conn.commit()
            conn.close()
            return redirect(url_for('magazijn'))
    elif account != user:  # als user niet de rechten heeft geef error
        flash("U heeft dit item niet geleend")
    return redirect(url_for('magazijn'))



# |------------------|
# |    gebruikers    |
# |------------------|

@app.route('/Gebruikers', methods=('GET','POST'))
def gebruikers():
    ip = request.remote_addr  # pakt ip van user
    user = get_user()  # pakt info van user
    conn = get_db_connection()  # connect met database
    check = conn.execute("SELECT * FROM users WHERE ip = ? AND rang = '2'", (ip,)).fetchone()  # check of user juiste rang heeft

    if check is None:  # als user geen juiste rang heeft geef error
        flash("U hebt geen toegang tot gebruikers")
        return redirect(url_for('home'))
    gebruikers = conn.execute("SELECT * FROM users ORDER BY inlog,groep,voornaam").fetchall()  # selecteer alles van users gesorteerd op inlog groep en naam
    return render_template('gebruikers.html', user = user, gebruikers = gebruikers)


@app.route('/<int:gebruiker_id>/Gebruiker Edit', methods=('GET', 'POST'))
def gebruiker_edit(gebruiker_id):  # pakt user id
    user = get_user()  # pakt user info
    gebruiker = get_gebruiker(gebruiker_id)  # pakt user info via user id
    conn = get_db_connection()  # connect database
    ip = request.remote_addr  # pakt ip van user
    check = conn.execute("SELECT * FROM users WHERE ip = ? AND rang = '2'", (ip,)).fetchone()  # kijkt of user juiste rang heeft

    if check is None:  # als user geen juiste rang heeft geef error
        flash("U hebt geen toegang voor het aanpassen van gebruikers")
        return redirect(url_for('home'))
    groep = conn.execute("SELECT DISTINCT groep FROM users WHERE groep NOT IN "
                         "('6TI-ICT', '5TI-ICT', 'Leerkracht', 'Collega', 'Extern', '')").fetchall()
    # selecteer distinct groep van users behalve de hardcode users

    if request.method == 'POST':
        naam = request.form['naam']
        achternaam = request.form['achternaam']
        groep = request.form['group']
        andere = request.form['andere']

        if not naam:  # als geen naam geef error
            flash("Naam is verplicht")

        elif not achternaam:  # als geen achternaam geef error
            flash("Achternaam is verplicht")

        elif not groep:  # als geen groep geef error
            flash("Kies een groep")

        elif groep == "other":  # als groep value other is pak value van input balk
            if not andere:  # als geen andere groep geef error
                flash("Geef een andere groep")
            else:
                # update de user
                conn.execute("UPDATE users SET voornaam = ?, achternaam = ?, rang = '1' , groep = ? WHERE id = ?",
                             (naam, achternaam, andere, gebruiker_id,))
                conn.commit()
                return redirect(url_for('gebruikers'))

        elif groep == "Leerkracht":
            # als groep leerkracht is zet rang op 2
            conn.execute("UPDATE users SET voornaam = ?, achternaam = ?, rang = '2',groep = ? WHERE id = ?",
                         (naam, achternaam, groep, gebruiker_id,))
            conn.commit()
            return redirect(url_for('gebruikers'))

        elif groep == "Collega":
            # als groep collega is zet rang op 2
            conn.execute("UPDATE users SET voornaam = ?, achternaam = ?, rang = '2',groep = ? WHERE id = ?",
                         (naam, achternaam, groep, gebruiker_id,))
            conn.commit()
            return redirect(url_for('gebruikers'))

        else:
            # anders zet rang 1
            conn.execute("UPDATE users SET voornaam = ?, achternaam = ?, rang = '1', groep = ? WHERE id = ?",
                         (naam, achternaam, groep, gebruiker_id,))
            conn.commit()
            return redirect(url_for('gebruikers'))
    conn.close()  # verbreek connectie
    return render_template('gebruikeredit.html', user=user, gebruiker=gebruiker, groep=groep)


@app.route('/<int:gebruiker_id>/Gebruiker Delete', methods=('GET', 'POST'))
def gebruiker_del(gebruiker_id):  # pakt user id
    conn = get_db_connection()  # maakt connectie met database
    ip = request.remote_addr  # pakt ip van user
    check = conn.execute("SELECT * FROM users WHERE ip = ? AND rang = '2'", (ip,)).fetchone()  # kijk oft user juiste rang heeft
    magcheck = conn.execute("SELECT * FROM users U INNER JOIN mlog m on U.id = m.user_id WHERE"  # kijkt of user geen item meer heeft
                            " user_id = ? AND datumin ='None'",(gebruiker_id,)).fetchone()
    stockcheck = conn.execute("SELECT * FROM users U INNER JOIN slog S ON U.id = S.id_user WHERE"  # kijkt of user geen stock meer heeft
                              " id_user = ? AND aantal != '0'",(gebruiker_id,)).fetchone()

    if magcheck:  # als nog item is geleend geef error
        flash("Deze gebruiker heeft nog iets uitgeleend")
        return redirect(url_for('gebruikers'))
    elif stockcheck:  # als nog stock is geleend geef error
        flash("Deze gebruiker heeft nog stock geleend")
        return redirect(url_for('gebruikers'))
    elif check is None:  # als gebruiker geen juiste rang heeft geef error
        flash("U hebt geen toegang voor het verwijderen van gebruikers")
        return redirect(url_for('home'))
    conn.execute("DELETE FROM users WHERE id = ?", (gebruiker_id,)).fetchone()  # anders delete users
    conn.commit()
    conn.close()
    return redirect(url_for('gebruikers'))


@app.route('/Gebruiker Create', methods=('GET', 'POST'))
def gebruiker_create():
    user = get_user()  # pak user info
    conn = get_db_connection()  # connectie database
    ip = request.remote_addr  # pakt ip user
    check = conn.execute("SELECT * FROM users WHERE ip = ? AND rang = '2'", (ip,)).fetchone()  # kijkf of user juiste rang heeft
    if check is None:  # als user geen juiste rang heeft geef error
        flash("U hebt geen toegang voor het aanmaken van gebruikers")
        return redirect(url_for('home'))
    gebruikers = conn.execute("SELECT DISTINCT groep FROM users WHERE groep NOT IN "
                              "('6TI-ICT', '5TI-ICT', 'Leerkracht', 'Collega', 'Extern', '')").fetchall()
    # pak alle groepen distinct behalve hardcode groepen

    if request.method == 'POST':
        naam = request.form['naam'].title()
        achternaam = request.form['achternaam']
        wachtwoord = request.form['wachtwoord']
        wachtwoordconf = request.form['wachtwoordconf']
        groep = request.form['group']
        andere = request.form['andere'].capitalize()

        wachtwoord_enc = sha256(wachtwoord, hash_seed)  # hash het wachtwoord

        if not naam:  # als geen naam geef error
            flash("Naam is verplicht")
        elif not achternaam:  # als geen achternaam geef error
            flash("Achternaam is verplicht")
        elif not wachtwoord:  # als geen wachtwoord geef error
            flash("Wachtwoord is verplicht")
        elif not wachtwoordconf:  # als geen wachtwooord conf geef error
            flash("Bevestig het wachtwoord")
        elif not groep:  # als geen groep geef error
            flash("Kies een groep")

        elif wachtwoordconf != wachtwoord:  # als wachtwoord niet overeen komt geef error
            flash("Wachtwoorden komen niet overeen")

        elif groep == "other":  # als groep value other is
            if not andere:  # als geen input geef error
                flash("Geef een andere groep")
            else:
                conn.execute("INSERT INTO users (voornaam, wachtwoord, achternaam, groep) values (?,?,?,?)",
                             (naam, wachtwoord_enc, achternaam, andere,))
                # maakt user met gekoze groep
                conn.commit()
                return redirect(url_for('gebruikers'))
        elif groep == "Leerkracht" or groep == "Collega":  # als groep leerkracht of collega is geef rang 2
            conn.execute("INSERT INTO users (voornaam, wachtwoord, achternaam, rang, groep) values (?,?,?,'2',?)",
                         (naam, wachtwoord_enc, achternaam, groep,))
            conn.commit()
            return redirect(url_for('gebruikers'))
        else:  # anders maak user met rang 1

            conn.execute("INSERT INTO users (voornaam, wachtwoord, achternaam, groep) values "
                         "(?,?,?,?)", (naam, wachtwoord_enc, achternaam, groep,))
            conn.commit()
            return redirect(url_for('gebruikers'))
    return render_template('gebruikercreate.html', user=user, gebruikers=gebruikers)


@app.route('/<int:gebruiker_id>/Gebruiker Info')
def gebruiker_info(gebruiker_id):  # pakt user id
    user = get_user()  # pak user info
    conn = get_db_connection()  # connect database
    gebruiker = get_gebruiker(gebruiker_id)  # neem info van gebruiker
    aantal = conn.execute("SELECT COUNT(*) FROM users U INNER JOIN mlog m on U.id = m.user_id WHERE"
                          " m.user_id = ? AND datumin = 'None'", (gebruiker_id,)).fetchone()[0]
    # neemt aantal van geleende items

    return render_template('gebruikerinfo.html', user=user, gebruiker=gebruiker, aantal=aantal)


@app.route('/<int:gebruiker_id>/Gebruiker Instellingen', methods=['GET', 'POST'])
def gebruiker_setting(gebruiker_id):  # neemt gebruiker id
    conn = get_db_connection()  # connect database
    user = get_user()  # neemt user info
    gebruiker = get_gebruiker(gebruiker_id)  # neem gebruiker info
    check = conn.execute("SELECT wachtwoord FROM users where id = ?",(gebruiker_id,)).fetchone()[0]  # neem oud wachtwoord
    if request.method == 'POST':
        naam = request.form['naam'].title()
        achternaam = request.form['achternaam']
        newpass = request.form['newpass']
        newpassconf = request.form['newpassconf']
        oldpass = request.form['oldpass']
        email = request.form['email']
        tel = request.form['tel']
        date = request.form['date']

        oldpass_enc = sha256(oldpass, hash_seed)  # hash oud password
        newpass_enc = sha256(newpass, hash_seed)  # hash new pass
        newpassconf_enc = sha256(newpassconf, hash_seed)  # has new passconf


        if not oldpass:  # als geen oude pass gegeven pas de rest aan
            conn.execute("UPDATE users SET voornaam = ?, achternaam = ?, email = ?,"
                         " telefoon = ?, geboorte = ? WHERE id = ?", (naam, achternaam, email,
                                                                      tel, date, gebruiker_id,))
            conn.commit()
            conn.close()
            return redirect(url_for('home'))
        elif oldpass_enc == check:  # als oud pass gegeven is en pass gelijk is met oud pass
                if newpass_enc == newpassconf_enc:  # als new pass en new passconf gelijk is update pass
                    conn.execute("UPDATE users SET voornaam = ?, achternaam = ?, wachtwoord = ?, email = ?,"
                                 " telefoon = ?, geboorte = ? WHERE id = ?", (naam, achternaam, newpass_enc, email,
                                                                              tel, date, gebruiker_id,))
                    conn.commit()
                    conn.close()
                    return redirect(url_for('home'))
                else:  # anders geef error
                    flash("Wachtwoord komt niet overeen met bevesteging")
                    return render_template('instellingen.html', user=user, gebruiker=gebruiker)
        elif oldpass_enc != check:  # als oud wachtwoord niet gelijk is geef error
            flash("Oud wachtwoord is incorrect")
            return render_template('instellingen.html', user=user, gebruiker=gebruiker)

    return render_template('instellingen.html', user=user, gebruiker=gebruiker)


@app.route('/<int:gebruiker_id>/Block')
def block(gebruiker_id):  # pak user id
    conn = get_db_connection()  # connect database
    conn.execute("UPDATE users SET block = 'Ja' WHERE id = ?", (gebruiker_id,))  # update user naar geblockd
    conn.commit()
    conn.close()
    return redirect(url_for('gebruikers'))

@app.route('/<int:gebruiker_id>/Unblock')
def unblock(gebruiker_id):  # pakt user id
    conn = get_db_connection()
    conn.execute("UPDATE users SET block = 'Neen' WHERE id = ?", (gebruiker_id,))  # update user naar unblock
    conn.commit()
    return redirect(url_for('gebruikers'))


@app.route('/<int:gebruiker_id>/Wachtwoord Reset')
def passreset(gebruiker_id):  # pak user id
    user = get_user()  # neem user info
    for i in user:
        user_id = i[0]
    conn = get_db_connection()  # connect database
    ip = request.remote_addr  # pakt user ip
    check = conn.execute("SELECT * FROM users WHERE ip = ? AND rang = '2'", (ip,)).fetchone()  # kijkt of user juiste rang heeft

    if check is None:  # als user geen juiste rang heeft geef error
        flash("U hebt geen toegang voor een passreset van gebruikers")
        return redirect(url_for('home'))
    if gebruiker_id == 0 and user_id != 0:  # als andere user wachtwoord van admin wil reseten geef error
        flash("Admin wacthwoord kan niet worden gereset door deze gebruiker")
        return redirect(url_for('gebruikers'))
    else:  # anders pak random wachtwoord en zet user pass op random wachtwoord
        wachtwoord = random_reset_pass()
        wachtwoord_hash = sha256(wachtwoord, hash_seed)
        conn.execute("UPDATE users SET wachtwoord = ?, reset = 'Ja' WHERE id = ?", (wachtwoord_hash, gebruiker_id,))
        # update user naar nieuw wachtwoord en zet user op gereset
        conn.commit()
        conn.close()  # verbreek connectie database
        flash("Het nieuwe wachtwoord is \"" + wachtwoord + "\" !")  # flash het nieuwe wachtwoord
        return redirect(url_for('gebruikers'))


@app.route('/Reset', methods=('POST', 'GET'))
def reset():
    users = get_user()  # pakt user info
    for user in users:
        user_id = user[0]
    if request.method == 'POST':
        wachtwoord = request.form['wachtwoord']
        wachtwoordconf = request.form['wachtwoordconf']

        wachtwoord_hash = sha256(wachtwoord, hash_seed)  # hash het wachtwoord

        if not wachtwoord:  # als geen wachtwoord geef error
            flash("Geef een nieuw wachtwoord")
        elif not wachtwoordconf:  # als geen conf wachtwoord geef error
            flash("Bevestig het nieuwe wachtwoord")
        elif wachtwoordconf != wachtwoord:  # als wachtwoord niet gelijk is aan conf wachtwoord geef error
            flash("Wachtwoord komt niet overeen met bevesteging")
        else:  # pas wachtworod aan en zet reset op neen
            conn = get_db_connection()
            conn.execute("UPDATE users SET wachtwoord = ?, reset = 'Neen' WHERE id = ?", (wachtwoord_hash, user_id,))
            conn.commit()
            flash("Wachtwoord gereset")
            return redirect(url_for('home'))
    return render_template("passreset.html", user=users)


# |---------------|
# |    locatie    |
# |---------------|
@app.route('/Locatie', methods=('GET', 'POST'))
def locatie():
    user = get_user()  # pak user info
    conn = get_db_connection()  # conenct met database
    locaties = conn.execute("SELECT * FROM locatie ORDER BY lokaal, kast").fetchall()  # selecteer alle locaties gesorteerd op lokaal en nummer
    conn.close()  # verbreek connectie
    return render_template('locatie.html', user=user, locaties=locaties)


@app.route('/Locatie Create', methods=('GET', 'POST'))
def locatie_create():
    user = get_user()  # pak user info
    conn = get_db_connection()  # maak connectie
    lokalen = conn.execute("SELECT DISTINCT lokaal FROM locatie ORDER BY lokaal ").fetchall()  # Selecteer alle lokalen van de locaties
    ip = request.remote_addr  # pakt ip van user
    check = conn.execute("SELECT * FROM users WHERE ip = ? AND rang = '2'", (ip,)).fetchone()  # kijkt of user juiste rang heeft

    if check is None:  # als user geen juiste rang heeft geef error
        flash("U hebt geen toegang voor het aanmaken van locaties")
        return redirect(url_for('stock'))
    if request.method == 'POST':
        kast = request.form['kast']
        lokaal = request.form['lokaal']
        andere = request.form['andere'].title()
        check = conn.execute("SELECT * FROM locatie WHERE lokaal = ? AND kast = ?", (lokaal, kast,)).fetchone()
        # selecteer alle locaties
        if not not check:  # kijkt of locatie al bestaat zo ja geef error
          flash("Deze locatie betaat al")
        elif not kast:  # als geen kast nummer gegeven is geef error
            flash("Geef een kast nummer")
        elif lokaal != "other":  # als lokaal value niet other is geef input balk
            conn.execute("INSERT INTO locatie (kast, lokaal) VALUES (?,?)", (kast, lokaal))
            conn.commit()
            return redirect(url_for('locatie'))
        else:
            if not andere:  # als geen andere gegeven is geef error
                flash("Geef ander lokaal")
            else:  # anders maak locatie
                conn.execute("INSERT INTO locatie (kast, lokaal) VALUES (?,?)", (kast, andere))
                conn.commit()
                return redirect(url_for('locatie'))
    return render_template("locatiecreate.html", user=user, lokalen=lokalen)


@app.route('/<int:locatie_id>/Locatie Delete', methods=('GET', 'POST'))
def locatie_del(locatie_id):  # pakt locatie id
    conn = get_db_connection()  # connect met database
    ip = request.remote_addr  # pakt user ip
    check = conn.execute("SELECT * FROM users WHERE ip = ? AND rang = '2'", (ip,)).fetchone()  # kijkt of user juiste rang heeft

    if check is None:  # als user geen juiste rang heeft geef error
        flash("U hebt geen toegang voor het verwijderen van Locaties")
        return redirect(url_for('locatie'))
    conn.execute("DELETE FROM locatie WHERE locatie_id = ?", (locatie_id,)).fetchone()  # anders verwijder locatie
    conn.commit()
    conn.close()
    return redirect(url_for('locatie'))


@app.route('/<int:locatie_id>/Locatie Info', methods=('GET', 'POST'))
def locatie_info(locatie_id):  # pak locatie id
    user = get_user()  # pak user info
    conn = get_db_connection()  # connect database
    locatie = conn.execute("SELECT * FROM locatie WHERE locatie_id = ?", (locatie_id,)).fetchone()  # neem alles van locatie waar id is gelijk
    inhouds = conn.execute("SELECT * FROM stock S LEFT JOIN locatie L ON S.id_locatie = L.locatie_id WHERE "
                           "L.locatie_id = ?", (locatie_id,)).fetchall()
    # selecteer alles van stock waar locatie gelijk is
    inhoudm = conn.execute("SELECT * FROM magazijn M INNER JOIN locatie L on M.locatie_id = L.locatie_id WHERE "
                           "L.locatie_id = ?", (locatie_id,)).fetchall()
    # selecteer alles van magazijn waar magazijn gelijk is
    conn.close()  # verbreek connectie met database
    return render_template('locatieinfo.html', locatie=locatie, inhouds=inhouds, inhoudm=inhoudm, user=user)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=6969)
