from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import RealDictCursor
import csv
import re
from datetime import datetime
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

app = Flask(__name__)
# app.secret_key = 

# app.config.update(
#     MAIL_SERVER=
#     MAIL_PORT=
#     MAIL_USE_TLS=
#     MAIL_USERNAME=
#     MAIL_PASSWORD=
# )

# mail = Mail(app)
# s = URLSafeTimedSerializer(app.secret_key)


# Use the provided DATABASE_URL
# DATABASE_URL = 

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


def remove_null_chars(value):
    if isinstance(value, str):
        return value.replace('\0', '')
    return value

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                          (id SERIAL PRIMARY KEY,
                           username TEXT NOT NULL UNIQUE,
                           email TEXT NOT NULL UNIQUE,
                           password TEXT NOT NULL,
                           date_created TIMESTAMP NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS books
                          (id SERIAL PRIMARY KEY,
                           book_id TEXT NOT NULL,
                           title TEXT NOT NULL,
                           author TEXT NOT NULL,
                           language TEXT NOT NULL,
                           genres TEXT NOT NULL,
                           pages INTEGER,
                           firstPublishDate TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS movies
                          (id SERIAL PRIMARY KEY,
                           movie_id TEXT NOT NULL,
                           title TEXT NOT NULL,
                           original_language TEXT,
                           original_title TEXT,
                           director TEXT,
                           genres TEXT,
                           country TEXT,
                           spoken_languages TEXT,
                           keywords TEXT,
                           release_date TEXT,
                           release_year INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS music
                          (id SERIAL PRIMARY KEY,
                           music_id TEXT NOT NULL,
                           title TEXT NOT NULL,
                           artist_name TEXT NOT NULL,
                           genres TEXT,
                           release_date TEXT)''')
        conn.commit()

def import_books():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        with open('data/books_db.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                pages = re.sub(r'\D', '', row['pages'])
                pages = int(pages) if pages else None
                cursor.execute('''INSERT INTO books (book_id, title, author, language, genres, pages, firstPublishDate)
                                  VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING''',
                               (row['book_id'], row['title'], row['author'], row['language'], row['genres'], pages,
                                row['firstPublishDate']))
        conn.commit()

def import_movies():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        with open('data/movies_db.csv', 'r', encoding='ISO-8859-1') as file:
            reader = csv.DictReader(file)
            for row in reader:
                release_year = re.sub(r'\D', '', row['release_year'])
                release_year = int(release_year) if release_year else None
                
                movie_id = remove_null_chars(row['movie_id'])
                title = remove_null_chars(row['title'])
                original_language = remove_null_chars(row['original_language'])
                original_title = remove_null_chars(row['original_title'])
                director = remove_null_chars(row['director'])
                genres = remove_null_chars(row['genres'])
                country = remove_null_chars(row['country'])
                spoken_languages = remove_null_chars(row['spoken_languages'])
                keywords = remove_null_chars(row['keywords'])
                release_date = remove_null_chars(row['release_date'])

                cursor.execute('''INSERT INTO movies (movie_id, title, original_language, original_title, director, genres, country, spoken_languages, keywords, release_date, release_year)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING''',
                                (movie_id, title, original_language, original_title, director, genres, country, spoken_languages, keywords, release_date, release_year))
        conn.commit()

def import_music():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        with open('data/music_db.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                cursor.execute('''INSERT INTO music (music_id, title, artist_name, genres, release_date)
                                  VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING''',
                               (row['music_id'], row['title'], row['artist_name'], row['genres'], row['release_date']))
        conn.commit()

init_db()

# def is_password_valid(password):
#     if len(password) < 8:
#         return False, "Password must be at least 8 characters long."
#     if not re.search(r'[a-z]', password):
#         return False, "Password must contain at least one lowercase letter."
#     if not re.search(r'[A-Z]', password):
#         return False, "Password must contain at least one uppercase letter."
#     if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
#         return False, "Password must contain at least one special character."
#     return True, ""

def is_password_valid(password):
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    return True, "Password is valid."


# Routes
@app.route('/')
def index():
    return render_template('login.html')


def send_confirmation_email(email, username):
    token = s.dumps(email, salt='email-confirm')
    link = url_for('confirm_email', token=token, _external=True)
    msg = Message('Confirm Your Email', sender='your_email@gmail.com', recipients=[email])
    msg.body = f'Hi {username},\n\nPlease click the link to confirm your email address:\n{link}\n\nThank you!'
    mail.send(msg)

@app.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600) 
    except SignatureExpired:
        return '<h1 style="font-family: \'Inter\', sans-serif;">The token is expired!</h1>'
    except BadSignature:
        return '<h1 style="font-family: \'Inter\', sans-serif;">Invalid token!</h1>'
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET confirmed = TRUE WHERE email = %s", (email,))
        conn.commit()
    
    return '''
    <h1 style="font-family: 'Inter', sans-serif;">Email confirmed! You can log in now.</h1>
    <a href="/login" style="font-family: 'Inter', sans-serif; color: #FF4500; text-decoration: none;">Back to login page</a>
    '''

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validate username length
        if len(username) > 17:
            return jsonify({'success': False, 'message': 'Username must not exceed 17 characters!'})

        # Validate password
        is_valid, message = is_password_valid(password)
        if not is_valid:
            return jsonify({'success': False, 'message': message})

        # Check if passwords match
        if password != confirm_password:
            return jsonify({'success': False, 'message': 'Passwords do not match!'})

        # Check if username or email is already taken
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            existing_username = cursor.fetchone()
            if existing_username:
                return jsonify({'success': False, 'message': 'Username is already taken!'})

            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            existing_email = cursor.fetchone()
            if existing_email:
                return jsonify({'success': False, 'message': 'Email is already taken!'})

            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            date_created = datetime.now()

            cursor.execute("INSERT INTO users (username, email, password, date_created, confirmed) VALUES (%s, %s, %s, %s, %s)",
                           (username, email, hashed_password, date_created, False))
            cursor.execute("SELECT currval(pg_get_serial_sequence('users','id'))")
            user_id = cursor.fetchone()['currval']
            cursor.execute(f'''CREATE TABLE user_{user_id}_table
                               (id SERIAL PRIMARY KEY,
                                pos_id TEXT,
                                title_id TEXT,
                                title TEXT,
                                type TEXT,
                                rating REAL,
                                comment TEXT,
                                date_added TIMESTAMP)''')
            conn.commit()
        
        send_confirmation_email(email, username)
        return jsonify({'success': True, 'message': 'Registration successful!\nPlease check your email\nto confirm your account.'})

    return render_template('register.html')

# def is_password_valid(password):
#     if len(password) < 8:
#         return False, "Password must be at least 8 characters long."
#     if not re.search(r"[a-z]", password):
#         return False, "Password must contain at least one lowercase letter."
#     if not re.search(r"[A-Z]", password):
#         return False, "Password must contain at least one uppercase letter."
#     if not re.search(r"\d", password):
#         return False, "Password must contain at least one digit."
#     if not re.search(r"[!@#$%^&*(),.?\":{}|<>[\]\/'~`+=_-]", password):
#         return False, "Password must contain at least one special character."
#     return True, "Password is valid."

def is_password_valid(password):
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    return True, "Password is valid."


from flask import jsonify, request, flash, redirect, url_for, render_template, session

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

        if user:
            if not user['confirmed']:
                message = 'Your email address is not confirmed. Please check your email to confirm your account.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': message})
                flash(message, 'error')
                return redirect(url_for('login'))

            if check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': True, 'redirect': url_for('homepage')})
                return redirect(url_for('homepage'))
            else:
                message = 'Invalid email or password!'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': message})
                flash(message, 'error')
        else:
            message = 'Invalid email or password!'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': message})
            flash(message, 'error')

    return render_template('login.html')


@app.route('/homepage', methods=['GET', 'POST'])
def homepage():
    if 'user_id' in session:
        user_id = session['user_id']
        with get_db_connection() as conn:
            cursor = conn.cursor()

            if request.method == 'POST':
                if 'book_id' in request.form:
                    book_id = request.form['book_id']
                    cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
                    book = cursor.fetchone()

                    if book:
                        cursor.execute(f"SELECT * FROM user_{user_id}_table WHERE title_id = %s", (book['book_id'],))
                        existing_book = cursor.fetchone()
                        if not existing_book:
                            cursor.execute(f"SELECT COUNT(*) FROM user_{user_id}_table")
                            count = cursor.fetchone()['count'] + 1
                            pos_id = f"{user_id}_{count}"
                            date_added = datetime.now()
                            cursor.execute(f'''INSERT INTO user_{user_id}_table 
                                               (pos_id, title_id, title, type, rating, comment, date_added)
                                               VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                                           (pos_id, book['book_id'], book['title'], 'book', None, "", date_added))
                            conn.commit()
                            flash('Book added to your shelf!', 'success')
                        else:
                            flash('Book already exists in your shelf!', 'error')

                if 'movie_id' in request.form:
                    movie_id = request.form['movie_id']
                    cursor.execute("SELECT * FROM movies WHERE movie_id = %s", (movie_id,))
                    movie = cursor.fetchone()

                    if movie:
                        cursor.execute(f"SELECT * FROM user_{user_id}_table WHERE title_id = %s", (movie['movie_id'],))
                        existing_movie = cursor.fetchone()
                        if not existing_movie:
                            cursor.execute(f"SELECT COUNT(*) FROM user_{user_id}_table")
                            count = cursor.fetchone()['count'] + 1
                            pos_id = f"{user_id}_{count}"
                            date_added = datetime.now()
                            cursor.execute(f'''INSERT INTO user_{user_id}_table 
                                               (pos_id, title_id, title, type, rating, comment, date_added)
                                               VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                                           (pos_id, movie['movie_id'], movie['title'], 'movie', None, "", date_added))
                            conn.commit()
                            flash('Movie added to your shelf!', 'success')
                        else:
                            flash('Movie already exists in your shelf!', 'error')

                if 'music_id' in request.form:
                    music_id = request.form['music_id']
                    cursor.execute("SELECT * FROM music WHERE music_id = %s", (music_id,))
                    music = cursor.fetchone()

                    if music:
                        cursor.execute(f"SELECT * FROM user_{user_id}_table WHERE title_id = %s", (music['music_id'],))
                        existing_music = cursor.fetchone()
                        if not existing_music:
                            cursor.execute(f"SELECT COUNT(*) FROM user_{user_id}_table")
                            count = cursor.fetchone()['count'] + 1
                            pos_id = f"{user_id}_{count}"
                            date_added = datetime.now()
                            cursor.execute(f'''INSERT INTO user_{user_id}_table 
                                               (pos_id, title_id, title, type, rating, comment, date_added)
                                               VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                                           (pos_id, music['music_id'], music['title'], 'music', None, "", date_added))
                            conn.commit()
                            flash('Music added to your shelf!', 'success')
                        else:
                            flash('Music already exists in your shelf!', 'error')

            cursor.execute(f'''
                SELECT u.*, b.author
                FROM user_{user_id}_table u
                JOIN books b ON u.title_id = b.book_id
                WHERE u.type = 'book'
                ORDER BY u.date_added DESC
                LIMIT 8
            ''')
            user_books = cursor.fetchall()

            cursor.execute(f'''
                SELECT u.*, m.director
                FROM user_{user_id}_table u
                JOIN movies m ON u.title_id = m.movie_id
                WHERE u.type = 'movie'
                ORDER BY u.date_added DESC
                LIMIT 8
            ''')
            user_movies = cursor.fetchall()

            cursor.execute(f'''
                SELECT u.*, m.artist_name
                FROM user_{user_id}_table u
                JOIN music m ON u.title_id = m.music_id
                WHERE u.type = 'music'
                ORDER BY u.date_added DESC
                LIMIT 8
            ''')
            user_music = cursor.fetchall()

            return render_template('homepage.html', username=session['username'],
                                   user_books=user_books, user_movies=user_movies, user_music=user_music)
    else:
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/search_books')
def search_books():
    query = request.args.get('query')
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT book_id, title, author 
            FROM books 
            WHERE title ILIKE %s OR author ILIKE %s
            ORDER BY book_id ASC
        """, ('%' + query + '%', '%' + query + '%'))
        books = cursor.fetchall()
    return jsonify(books)

@app.route('/search_movies')
def search_movies():
    query = request.args.get('query')
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT movie_id, title, director, release_year 
            FROM movies 
            WHERE title ILIKE %s OR director ILIKE %s
            ORDER BY movie_id ASC
        """, ('%' + query + '%', '%' + query + '%'))
        movies = cursor.fetchall()
    return jsonify(movies)

@app.route('/search_music')
def search_music():
    query = request.args.get('query')
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT music_id, title, artist_name 
            FROM music 
            WHERE title ILIKE %s OR artist_name ILIKE %s
            ORDER BY music_id ASC
        """, ('%' + query + '%', '%' + query + '%'))

        music = cursor.fetchall()
    return jsonify(music)


# To nie wiadomo czy zadziała w ogóle
@app.route('/search_everything')
def search_everything():
    query = request.args.get('query', '')
    type_filter = request.args.get('type', '')
    artist_filter = request.args.get('artist', '')
    year_filter = request.args.get('year', '')
    genres_filter = request.args.get('genres', '')
    
    # Domyślne sortowanie - jeśli typ to 'movie', 'music', lub 'book', odpowiednio sortuj
    if type_filter == 'movie':
        sort_by = request.args.get('sort_by', 'movie_id')
    elif type_filter == 'music':
        sort_by = request.args.get('sort_by', 'music_id')
    elif type_filter == 'book':
        sort_by = request.args.get('sort_by', 'book_id')
    else:
        # Jeśli nie ma filtru typu, sortuj po najniższym ID
        sort_by = request.args.get('sort_by', 'id')

    sort_order = request.args.get('sort_order', 'asc')  # Domyślnie sortowanie rosnące
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page

    user_id = session['user_id'] if 'user_id' in session else None
    user_items = {}

    if user_id:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT title_id, id FROM user_{user_id}_table")
            user_items = {item['title_id']: item['id'] for item in cursor.fetchall()}

    results = []
    sort_column_map = {
        'title': 'title',
        'artist': 'artist',
        'year': 'year',
        'movie_id': 'movie_id',
        'book_id': 'book_id',
        'music_id': 'music_id'
    }

    sort_column = sort_column_map.get(sort_by, 'id')
    order_clause = f"{sort_column} {'ASC' if sort_order == 'asc' else 'DESC'}"

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Search books
        if type_filter in ('', 'book'):
            cursor.execute(f"""
                SELECT 'Book' AS type, book_id AS id, title, author AS artist, firstPublishDate AS year, genres 
                FROM books 
                WHERE (title ILIKE %s OR author ILIKE %s) 
                AND (%s = '' OR author ILIKE %s)
                AND (%s = '' OR firstPublishDate ILIKE %s)
                AND (%s = '' OR genres ILIKE %s)
                ORDER BY {order_clause}
                LIMIT %s OFFSET %s
            """, (f'%{query}%', f'%{query}%', artist_filter, f'%{artist_filter}%', year_filter, f'%{year_filter}%', genres_filter, f'%{genres_filter}%', per_page, offset))
            books = cursor.fetchall()
            for book in books:
                book['user_table_id'] = user_items.get(book['id'])
                results.append(book)

        # Search movies
        if type_filter in ('', 'movie'):
            cursor.execute(f"""
                SELECT 'Movie' AS type, movie_id AS id, title, director AS artist, release_year AS year, genres 
                FROM movies 
                WHERE (title ILIKE %s OR director ILIKE %s)
                AND (%s = '' OR director ILIKE %s)
                AND (%s = '' OR release_year::TEXT ILIKE %s)
                AND (%s = '' OR genres ILIKE %s)
                ORDER BY {order_clause}
                LIMIT %s OFFSET %s
            """, (f'%{query}%', f'%{query}%', artist_filter, f'%{artist_filter}%', year_filter, f'%{year_filter}%', genres_filter, f'%{genres_filter}%', per_page, offset))
            movies = cursor.fetchall()
            for movie in movies:
                movie['user_table_id'] = user_items.get(movie['id'])
                results.append(movie)

        # Search music
        if type_filter in ('', 'music'):
            cursor.execute(f"""
                SELECT 'Music' AS type, music_id AS id, title, artist_name AS artist, release_date AS year, genres 
                FROM music 
                WHERE (title ILIKE %s OR artist_name ILIKE %s)
                AND (%s = '' OR artist_name ILIKE %s)
                AND (%s = '' OR release_date ILIKE %s)
                AND (%s = '' OR genres ILIKE %s)
                ORDER BY {order_clause}
                LIMIT %s OFFSET %s
            """, (f'%{query}%', f'%{query}%', artist_filter, f'%{artist_filter}%', year_filter, f'%{year_filter}%', genres_filter, f'%{genres_filter}%', per_page, offset))
            music = cursor.fetchall()
            for track in music:
                track['user_table_id'] = user_items.get(track['id'])
                results.append(track)

    total_pages = (len(results) + per_page - 1) // per_page

    return render_template('search_results.html', query=query, results=results, type=type_filter, artist=artist_filter, year=year_filter, genres=genres_filter, page=page, total_pages=total_pages, user_items=user_items, sort_by=sort_by, sort_order=sort_order)

@app.route('/add_item', methods=['POST'])
def add_item():
    if 'user_id' in session:
        user_id = session['user_id']
        data = request.get_json()
        item_id = data['item_id']
        item_type = data['item_type']

        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(f"SELECT * FROM user_{user_id}_table WHERE title_id = %s AND type = %s", (item_id, item_type))
            existing_item = cursor.fetchone()
            if existing_item:
                return jsonify(success=False, message="This item is already on YourShelf!")
            
            if item_type == 'book':
                cursor.execute("SELECT * FROM books WHERE book_id = %s", (item_id,))
                item = cursor.fetchone()
            elif item_type == 'movie':
                cursor.execute("SELECT * FROM movies WHERE movie_id = %s", (item_id,))
                item = cursor.fetchone()
            elif item_type == 'music':
                cursor.execute("SELECT * FROM music WHERE music_id = %s", (item_id,))
                item = cursor.fetchone()
            
            if item:
                cursor.execute(f"SELECT COUNT(*) FROM user_{user_id}_table")
                count = cursor.fetchone()['count'] + 1
                pos_id = f"{user_id}_{count}"
                date_added = datetime.now()
                cursor.execute(f'''INSERT INTO user_{user_id}_table 
                                   (pos_id, title_id, title, type, rating, comment, date_added)
                                   VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                               (pos_id, item[f'{item_type}_id'], item['title'], item_type, None, "", date_added))
                conn.commit()
                return jsonify(success=True)

    return jsonify(success=False), 403

@app.route('/delete_item', methods=['POST'])
def delete_item():
    if 'user_id' in session:
        user_id = session['user_id']
        data = request.get_json()
        item_id = data['item_id']
       
        print(f"Attempting to delete item with ID {item_id} for user {user_id}")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM user_{user_id}_table WHERE id = %s", (item_id,))
            conn.commit()
        
        print("Deletion successful")
        return jsonify(success=True)
    
    print("Deletion failed: User not authenticated")
    return jsonify(success=False), 403

@app.route('/update_rating', methods=['POST'])
def update_rating():
    if 'user_id' in session:
        user_id = session['user_id']
        data = request.get_json()
        update_id = data['update_id']
        rating = data['rating']

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''UPDATE user_{user_id}_table 
                               SET rating = %s 
                               WHERE id = %s''',
                           (rating, update_id))
            conn.commit()
        return jsonify(success=True)
    return jsonify(success=False), 403

@app.route('/books', methods=['GET', 'POST'])
def books():
    if 'user_id' in session:
        user_id = session['user_id']
        page = request.args.get('page', 1, type=int)
        per_page = 15
        offset = (page - 1) * per_page
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if request.method == 'POST' and 'update_id' in request.form:
                update_id = request.form['update_id']
                comment = request.form['comment']
                cursor.execute(f'''UPDATE user_{user_id}_table 
                                   SET comment = %s 
                                   WHERE id = %s''',
                               (comment, update_id))
                conn.commit()
                flash('Comment updated successfully!', 'success')

            cursor.execute(f'''
                SELECT u.*, b.author
                FROM user_{user_id}_table u
                JOIN books b ON u.title_id = b.book_id
                WHERE u.type = 'book'
                ORDER BY u.date_added DESC
                LIMIT %s OFFSET %s
            ''', (per_page, offset))
            user_books = cursor.fetchall()
            
            cursor.execute(f"SELECT COUNT(*) FROM user_{user_id}_table WHERE type = 'book'")
            total_books = cursor.fetchone()['count']
        
        total_pages = (total_books // per_page) + (1 if total_books % per_page > 0 else 0)
        
        # Get author information from the books table
        user_books_with_author = []
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for item in user_books:
                cursor.execute("SELECT author FROM books WHERE book_id = %s", (item['title_id'],))
                author = cursor.fetchone()
                if author:
                    user_books_with_author.append((*item.values(), author['author']))
                else:
                    user_books_with_author.append((*item.values(), 'Unknown Author'))
        
        return render_template('books.html', user_books=user_books_with_author, page=page, total_pages=total_pages)
    else:
        return redirect(url_for('index'))

@app.route('/movies', methods=['GET', 'POST'])
def movies():
    if 'user_id' in session:
        user_id = session['user_id']
        page = request.args.get('page', 1, type=int)
        per_page = 15
        offset = (page - 1) * per_page
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if request.method == 'POST' and 'update_id' in request.form:
                update_id = request.form['update_id']
                comment = request.form['comment']
                cursor.execute(f'''UPDATE user_{user_id}_table 
                                   SET comment = %s 
                                   WHERE id = %s''',
                               (comment, update_id))
                conn.commit()
                flash('Comment updated successfully!', 'success')

            cursor.execute(f'''
                SELECT u.*, m.director
                FROM user_{user_id}_table u
                JOIN movies m ON u.title_id = m.movie_id
                WHERE u.type = 'movie'
                ORDER BY u.date_added DESC
                LIMIT %s OFFSET %s
            ''', (per_page, offset))
            user_movies = cursor.fetchall()
            
            cursor.execute(f"SELECT COUNT(*) FROM user_{user_id}_table WHERE type = 'movie'")
            total_movies = cursor.fetchone()['count']
        
        total_pages = (total_movies // per_page) + (1 if total_movies % per_page > 0 else 0)
        
        return render_template('movies.html', user_movies=user_movies, page=page, total_pages=total_pages)
    else:
        return redirect(url_for('index'))


@app.route('/music', methods=['GET', 'POST'])
def music():
    if 'user_id' in session:
        user_id = session['user_id']
        page = request.args.get('page', 1, type=int)
        per_page = 15
        offset = (page - 1) * per_page
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if request.method == 'POST' and 'update_id' in request.form:
                update_id = request.form['update_id']
                comment = request.form['comment']
                cursor.execute(f'''UPDATE user_{user_id}_table 
                                   SET comment = %s 
                                   WHERE id = %s''',
                               (comment, update_id))
                conn.commit()
                flash('Comment updated successfully!', 'success')

            cursor.execute(f'''
                SELECT u.*, m.artist_name
                FROM user_{user_id}_table u
                JOIN music m ON u.title_id = m.music_id
                WHERE u.type = 'music'
                ORDER BY u.date_added DESC
                LIMIT %s OFFSET %s
            ''', (per_page, offset))
            user_music = cursor.fetchall()
            
            cursor.execute(f"SELECT COUNT(*) FROM user_{user_id}_table WHERE type = 'music'")
            total_music = cursor.fetchone()['count']
        
        total_pages = (total_music // per_page) + (1 if total_music % per_page > 0 else 0)
        
        return render_template('music.html', user_music=user_music, page=page, total_pages=total_pages)
    else:
        return redirect(url_for('index'))

@app.route('/update_comment', methods=['POST'])
def update_comment():
    if 'user_id' in session:
        user_id = session['user_id']
        data = request.get_json()
        update_id = data['update_id']
        comment = data['comment']

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''UPDATE user_{user_id}_table 
                               SET comment = %s 
                               WHERE id = %s''',
                           (comment, update_id))
            conn.commit()
        return jsonify(success=True)
    return jsonify(success=False), 403


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if user:
                # Generate a token for resetting the password
                token = s.dumps(email, salt='password-reset')
                
                # Construct the password reset link
                reset_link = url_for('reset_password', token=token, _external=True)
                
                # Send the password reset email
                msg = Message('Password Reset Request', sender='projectmyshelf@gmail.com', recipients=[email])
                msg.body = f'Dear {user["username"]},\n\nPlease click the link below to reset your password:\n{reset_link}\n\nIf you did not request a password reset, please ignore this email.'
                mail.send(msg)
                
                return jsonify({'success': True, 'message': 'A password reset link has been sent to your email address. Please check your inbox.'})
            else:
                return jsonify({'success': False, 'message': 'Email not found in our database.'})
    
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset', max_age=3600)  # Link valid for 1 hour
    except SignatureExpired:
        return '<h1>The token is expired!</h1>'
    except BadSignature:
        return '<h1>Invalid token!</h1>'

    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('reset_password', token=token))

        # Validate password strength
        is_valid, message = is_password_valid(password)
        if not is_valid:
            flash(message, 'error')
            return redirect(url_for('reset_password', token=token))

        # Update the user's password in the database
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, email))
            conn.commit()

        flash('Your password has been reset. You can now log in with your new password.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html')

@app.route('/search_user_books')
def search_user_books():
    if 'user_id' in session:
        user_id = session['user_id']
        query = request.args.get('query', '').lower()

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT u.id, u.title, b.author, u.date_added, u.rating, u.comment
                FROM user_{user_id}_table u
                JOIN books b ON u.title_id = b.book_id
                WHERE u.type = 'book' AND LOWER(u.title) LIKE %s
                ORDER BY u.date_added DESC
            ''', (f'%{query}%',))
            user_books = cursor.fetchall()

        return jsonify(user_books)
    else:
        return jsonify([]), 403

@app.route('/search_user_movies')
def search_user_movies():
    if 'user_id' in session:
        user_id = session['user_id']
        query = request.args.get('query', '').lower()

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT u.id, u.title, b.director, u.date_added, u.rating, u.comment
                FROM user_{user_id}_table u
                JOIN movies b ON u.title_id = b.movie_id
                WHERE u.type = 'movie' AND LOWER(u.title) LIKE %s
                ORDER BY u.date_added DESC
            ''', (f'%{query}%',))
            user_movies = cursor.fetchall()

        return jsonify(user_movies)
    else:
        return jsonify([]), 403
    

@app.route('/search_user_music')
def search_user_music():
    if 'user_id' in session:
        user_id = session['user_id']
        query = request.args.get('query', '').lower()

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT u.id, u.title, b.artist_name, u.date_added, u.rating, u.comment
                FROM user_{user_id}_table u
                JOIN music b ON u.title_id = b.music_id
                WHERE u.type = 'music' AND LOWER(u.title) LIKE %s
                ORDER BY u.date_added DESC
            ''', (f'%{query}%',))
            user_music = cursor.fetchall()

        return jsonify(user_music)
    else:
        return jsonify([]), 403


if __name__ == '__main__':
    app.run(debug=True)