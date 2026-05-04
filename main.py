from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'eco_secret_2026'


def init_db():
    con = sqlite3.connect('db.sqlite')
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        points INTEGER DEFAULT 0
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        title TEXT,
        category TEXT,
        points INTEGER,
        completed_by_user TEXT DEFAULT ''
    )''')
    # Эко-задания (если пусто)
    cur.execute('SELECT COUNT(*) FROM tasks')
    if cur.fetchone()[0] == 0:
        tasks = [
            (1, 'Отказ от пластика сегодня', 'ежедневные', 10, ''),
            (2, 'Сортировка мусора', 'ежедневные', 5, ''),
            (3, 'Посадить дерево', 'еженедельные', 50, ''),
            (4, 'Велосипед вместо авто', 'ежедневные', 15, '')
        ]
        cur.executemany('INSERT INTO tasks VALUES (?,?,?,?,?)', tasks)
    con.commit()
    con.close()


@app.route('/', methods=['GET', 'POST'])
def index():
    # Проверяем сессию
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        uid = int(session['user_id'])
    except (ValueError, TypeError):
        session.clear()
        return redirect(url_for('login'))

    con = sqlite3.connect('db.sqlite')
    cur = con.cursor()

    # Баллы
    cur.execute('SELECT points FROM users WHERE id=?', (uid,))
    row = cur.fetchone()
    points = row[0] if row else 0

    # Tasks с безопасным доступом
    cur.execute('SELECT id, title, category, points, completed_by_user FROM tasks')
    all_tasks = cur.fetchall()
    completed_count = 0
    user_tasks = []
    for task in all_tasks:
        completed_by = task[4] or ''  # Безопасно!
        status = completed_by == str(uid)
        if status:
            completed_count += 1
        user_tasks.append((task[0], task[1], task[2], task[3], completed_by, status))

    progress = (completed_count / len(all_tasks)) * 100 if all_tasks else 0

    # Leaderboard
    cur.execute('SELECT username, points FROM users ORDER BY points DESC LIMIT 10')
    leaderboard = []
    for row in cur.fetchall():
        leaderboard.append((row[0], row[1] or 0))

    con.close()

    return render_template('index.html',
                           points=points,
                           tasks=user_tasks,
                           progress=progress,
                           leaderboard=leaderboard,
                           total_tasks=len(all_tasks),
                           uid=uid)


@app.route('/toggle_task/<int:task_id>')
def toggle_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        uid = int(session['user_id'])
    except:
        session.clear()
        return redirect(url_for('login'))

    con = sqlite3.connect('db.sqlite')
    cur = con.cursor()

    # Toggle
    cur.execute('SELECT completed_by_user, points FROM tasks WHERE id=?', (task_id,))
    task = cur.fetchone()
    if not task:
        con.close()
        return redirect(url_for('index'))

    completed_by, task_points = task
    if completed_by == str(uid):
        # Отменить
        cur.execute('UPDATE tasks SET completed_by_user=? WHERE id=?', ('', task_id))
        cur.execute('UPDATE users SET points = points - ? WHERE id=?', (task_points, uid))
    else:
        # Выполнить
        cur.execute('UPDATE tasks SET completed_by_user=? WHERE id=?', (str(uid), task_id))
        cur.execute('UPDATE users SET points = points + ? WHERE id=?', (task_points, uid))

    con.commit()
    con.close()
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        if not username:
            flash('Введите ник!')
            return redirect(url_for('login'))

        con = sqlite3.connect('db.sqlite')
        cur = con.cursor()
        cur.execute('SELECT id FROM users WHERE username=?', (username,))
        user_id = cur.fetchone()

        if not user_id:
            cur.execute('INSERT INTO users (username) VALUES (?)', (username,))
            con.commit()
            user_id = cur.lastrowid
        else:
            user_id = user_id[0]

        con.close()
        session['user_id'] = user_id  # ЧИСЛО!
        flash(f'Вошли как {username}')
        return redirect(url_for('index'))

    return '''
<!doctype html>
<html><head><title>Эко-Привычки</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" rel="stylesheet">
</head><body class="bg-gradient bg-success-subtle min-vh-100 d-flex align-items-center">
<div class="container">
    <div class="row justify-content-center">
        <div class="col-md-6 col-lg-4">
            <div class="card shadow-lg border-0">
                <div class="card-body p-5 text-center">
                    <i class="fas fa-leaf fa-3x text-success mb-4"></i>
                    <h2>Эко-Привычки</h2>
                    <p class="lead text-muted mb-4">Мотивируем к экологии!</p>
                    <form method="post">
                        <div class="mb-4">
                            <input name="username" class="form-control form-control-lg text-center" 
                                   placeholder="Ваш ник" required maxlength="20">
                        </div>
                        <button class="btn btn-success btn-lg w-100 py-3">
                            <i class="fas fa-rocket me-2"></i>Начать!
                        </button>
                    </form>
                    <div class="mt-4 small text-muted">
                        <i class="fas fa-check-circle text-success me-1"></i>
                        Авторегистрация • Баллы • Рейтинг
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body></html>
'''


@app.route('/logout')
def logout():
    session.clear()
    flash('До свидания!')
    return redirect(url_for('login'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='127.0.0.1', port=5000)