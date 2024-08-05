import sqlite3


def create_db():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

    # Создание таблицы работников
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
        ''')

    # Создание таблицы задач
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            status TEXT NOT NULL
        )
        ''')

    # Создание промежуточной таблицы для связи задач с работниками
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_workers (
            task_id INTEGER,
            worker_id INTEGER,
            PRIMARY KEY (task_id, worker_id),
            FOREIGN KEY (task_id) REFERENCES tasks (id),
            FOREIGN KEY (worker_id) REFERENCES workers (id)
        )
        ''')

    conn.commit()
    conn.close()


create_db()
