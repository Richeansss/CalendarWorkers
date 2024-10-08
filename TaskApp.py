import sys
import sqlite3
import shutil
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QListWidget,
    QFormLayout, QLineEdit, QLabel, QTabWidget, QComboBox, QDateEdit, QTextBrowser, QHeaderView, QHBoxLayout,
    QTableWidgetItem, QTableWidget, QMessageBox
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QIcon, QGuiApplication

TASK_DONE = "green"
TASK_PROCESSING = "blue"
TASK_STOP = "red"


class TaskManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Менеджер задач')

        screen = QGuiApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()

        width_percent = 0.8
        height_percent = 0.8
        x_percent = 0.1
        y_percent = 0.1

        window_width = int(screen_width * width_percent)
        window_height = int(screen_height * height_percent)
        x_position = int(screen_width * x_percent)
        y_position = int(screen_height * y_percent)

        self.setGeometry(x_position, y_position, window_width, window_height)

        self.setWindowIcon(QIcon('gaz.ico'))

        # Общий стиль для всех QPushButton
        self.setStyleSheet("""
            QPushButton {
                background-color: #0079c2;
                color: white; /* Белый текст */
                border: none; /* Без границы */
                padding: 10px 20px; /* Отступы */
                text-align: center; /* Выравнивание текста по центру */
                text-decoration: none; /* Без подчеркивания */
                display: inline-block; /* Инлайн-блок */
                font-size: 16px; /* Размер шрифта */
                margin: 5px 2px; /* Отступы вокруг кнопки */
                border-radius: 5px; /* Скругленные углы */
            }
            QPushButton:hover {
                background-color: #45a049; /* Цвет при наведении */
            }
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.worker_tab = QWidget()
        self.task_tab = QWidget()
        self.calendar_tab = QWidget()
        self.setting_tab = QWidget()

        self.tabs.addTab(self.worker_tab, 'Работники')
        self.tabs.addTab(self.task_tab, 'Задачи')
        self.tabs.addTab(self.calendar_tab, 'Календарь')
        self.tabs.addTab(self.setting_tab, 'Настройки')

        self.setup_worker_tab()
        self.setup_task_tab()
        self.setup_calendar_tab()
        self.setup_setting_tab()

        # Connect tab change signal to data update method
        self.tabs.currentChanged.connect(self.update_data)

        # Initial data load
        self.update_data()

    def setup_worker_tab(self):
        self.worker_layout = QVBoxLayout()
        self.worker_list = QListWidget()
        self.worker_layout.addWidget(self.worker_list)

        self.worker_form = QFormLayout()
        self.worker_name_input = QLineEdit()
        self.worker_form.addRow(QLabel('Имя работника:'), self.worker_name_input)

        self.worker_buttons_layout = QVBoxLayout()
        self.add_worker_button = QPushButton('Добавить работника')
        self.remove_worker_button = QPushButton('Удалить работника')
        self.worker_buttons_layout.addWidget(self.add_worker_button)
        self.worker_buttons_layout.addWidget(self.remove_worker_button)

        self.worker_layout.addLayout(self.worker_form)
        self.worker_layout.addLayout(self.worker_buttons_layout)

        self.worker_tab.setLayout(self.worker_layout)

        # Connect buttons to methods
        self.add_worker_button.clicked.connect(self.add_worker)
        self.remove_worker_button.clicked.connect(self.remove_worker)

    def setup_task_tab(self):
        self.task_layout = QVBoxLayout()

        # Новый layout для комбобоксов
        self.task_filter_layout = QHBoxLayout()

        self.worker_combobox = QComboBox()
        self.worker_combobox.addItem('Все работники')
        self.worker_combobox.currentIndexChanged.connect(self.filter_tasks)

        self.task_combobox = QComboBox()
        self.task_combobox.addItem('Все задачи')
        self.task_combobox.currentIndexChanged.connect(self.filter_tasks)

        self.status_combobox = QComboBox()
        self.status_combobox.addItem('Все статусы')
        self.status_combobox.currentIndexChanged.connect(self.filter_tasks)

        self.task_filter_layout.addWidget(QLabel('Фильтр по работнику:'))
        self.task_filter_layout.addWidget(self.worker_combobox)
        self.task_filter_layout.addWidget(QLabel('Фильтр по задаче:'))
        self.task_filter_layout.addWidget(self.task_combobox)
        self.task_filter_layout.addWidget(QLabel('Фильтр по статусу:'))
        self.task_filter_layout.addWidget(self.status_combobox)

        # Добавляем layout для фильтров до таблицы
        self.task_layout.addLayout(self.task_filter_layout)

        # Таблица задач
        self.task_table = QTableWidget()
        self.task_layout.addWidget(self.task_table)

        self.task_form = QFormLayout()
        self.task_worker_layout = QHBoxLayout()
        self.add_worker_button = QPushButton('Добавить работника')
        self.remove_worker_button = QPushButton('Удалить работников')
        self.task_worker_layout.addWidget(self.add_worker_button)
        self.task_worker_layout.addWidget(self.remove_worker_button)

        self.task_title_input = QLineEdit()
        self.task_start_input = QDateEdit()
        self.task_end_input = QDateEdit()
        self.task_status_input = QComboBox()

        self.initialize_task_form()

        self.task_buttons_layout = QVBoxLayout()
        self.add_task_button = QPushButton('Добавить задачу')
        self.remove_task_button = QPushButton('Удалить задачу')
        self.task_buttons_layout.addWidget(self.add_task_button)
        self.task_buttons_layout.addWidget(self.remove_task_button)

        self.task_form.addRow(QLabel('Рабочие:'), self.task_worker_layout)
        self.task_form.addRow(QLabel('Название задачи:'), self.task_title_input)
        self.task_form.addRow(QLabel('Дата начала:'), self.task_start_input)
        self.task_form.addRow(QLabel('Дата конца:'), self.task_end_input)
        self.task_form.addRow(QLabel('Статус:'), self.task_status_input)

        self.task_layout.addLayout(self.task_form)
        self.task_layout.addLayout(self.task_buttons_layout)

        self.task_tab.setLayout(self.task_layout)

        # Connect buttons to methods
        self.add_task_button.clicked.connect(self.add_task)
        self.remove_task_button.clicked.connect(self.remove_task)
        self.add_worker_button.clicked.connect(self.add_worker_combobox)
        self.remove_worker_button.clicked.connect(self.remove_worker_combobox)

        # Load initial worker data
        self.add_initial_worker_combobox()
        self.load_workers_into_combobox()
        self.load_tasks_into_combobox()
        self.load_statuses_into_combobox()
        self.load_tasks()

    def filter_tasks(self):
        worker = self.worker_combobox.currentText()
        task = self.task_combobox.currentText()
        status = self.status_combobox.currentText()

        self.load_tasks(worker=worker, task=task, status=status)

    def load_statuses_into_combobox(self):
        statuses = self.load_statuses()
        self.status_combobox.clear()
        self.status_combobox.addItem('Все статусы')
        self.status_combobox.addItems(statuses)
        self.status_combobox.setMaximumWidth(400)

    def load_workers_into_combobox(self):
        workers = self.load_workers()
        self.worker_combobox.clear()
        self.worker_combobox.addItem('Все работники')
        self.worker_combobox.addItems([w[1] for w in workers])
        self.worker_combobox.setMaximumWidth(400)

    def load_tasks_into_combobox(self):
        tasks = self.load_tasks_for_load_tasks_into_combobox()
        self.task_combobox.clear()
        self.task_combobox.addItem('Все задачи')
        self.task_combobox.addItems([t[1] for t in tasks])
        self.task_combobox.setMaximumWidth(400)  # Пример ограничения ширины

    def load_statuses(self):
        query = 'SELECT DISTINCT status FROM tasks'
        statuses = self.execute_query(query)
        return [row[0] for row in statuses]

    def load_tasks_for_load_tasks_into_combobox(self):
        query = 'SELECT id, title FROM tasks'
        tasks = self.execute_query(query)
        return tasks

    def execute_query(self, query, params=(), fetchall=True):
        try:
            conn = sqlite3.connect('tasks.db')
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall() if fetchall else cursor.fetchone()
            conn.commit()
            return result
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при выполнении запроса: {e}")
            return []
        finally:
            conn.close()

    def setup_setting_tab(self):
        self.task_layout = QVBoxLayout()

        self.force_backup_button = QPushButton("Принудительно создать резервную копию", self.setting_tab)
        self.force_backup_button.clicked.connect(self.force_backup)

        self.task_layout.addWidget(self.force_backup_button)
        self.setting_tab.setLayout(self.task_layout)

        # self.setGeometry(300, 300, 800, 600)

    def force_backup(self):
        backup_tasks_db(force_backup=True)

    def add_worker_combobox(self):
        workers = self.load_workers()
        if workers:
            new_combobox = QComboBox()
            new_combobox.addItems([w[1] for w in workers])
            self.task_worker_layout.insertWidget(self.task_worker_layout.count() - 2,
                                                 new_combobox)  # Добавляем перед кнопкой удаления

    def add_initial_worker_combobox(self):
        workers = self.load_workers()
        if workers:
            initial_worker = QComboBox()
            initial_worker.addItems([w[1] for w in workers])
            self.task_worker_layout.insertWidget(0, initial_worker)  # Добавляем в начало layout

    def remove_worker_combobox(self):
        # Получаем все комбобоксы в layout
        widgets = []
        count = self.task_worker_layout.count()

        for i in range(count):
            item = self.task_worker_layout.itemAt(i)
            if item and isinstance(item.widget(), QComboBox):
                widgets.append(item.widget())

        # Удаляем все комбобоксы, кроме первого
        if len(widgets) > 1:
            for widget in widgets[1:]:  # Удаляем все кроме первого
                self.task_worker_layout.removeWidget(widget)
                widget.deleteLater()  # Освобождаем память
        else:
            print("Не могу удалить, поскольку должен оставаться хотя бы один комбобокс.")

    def setup_calendar_tab(self):
        self.calendar_layout = QVBoxLayout()

        # Worker selection combobox
        self.worker_filter_layout = QHBoxLayout()
        self.worker_filter_label = QLabel('Сортировать по работнику:')
        self.worker_filter_combobox = QComboBox()
        self.worker_filter_combobox.addItem('Все работники')
        self.worker_filter_combobox.currentIndexChanged.connect(self.filter_tasks_by_worker)

        self.worker_filter_layout.addWidget(self.worker_filter_label)
        self.worker_filter_layout.addWidget(self.worker_filter_combobox)
        self.calendar_layout.addLayout(self.worker_filter_layout)

        # Navigation Layout
        self.nav_layout = QHBoxLayout()
        self.prev_month_button = QPushButton('<< Предыдущий месяц')
        self.next_month_button = QPushButton('Следующий месяц >>')

        # Month and Year Label
        self.month_year_label = QLabel()
        self.month_year_label.setAlignment(Qt.AlignCenter)
        self.month_year_label.setStyleSheet("""
            font-weight: bold;
            text-transform: uppercase;
            font-size: 18px;
            color: #333;
            margin: 0 10px;
        """)

        self.nav_layout.addWidget(self.prev_month_button)
        self.nav_layout.addWidget(self.month_year_label)
        self.nav_layout.addWidget(self.next_month_button)
        self.calendar_layout.addLayout(self.nav_layout)

        # Calendar Table
        self.calendar_table = QTableWidget(6, 7)
        self.calendar_table.setHorizontalHeaderLabels(['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС'])
        self.calendar_table.horizontalHeader().setStretchLastSection(True)
        self.calendar_table.verticalHeader().setVisible(False)
        self.calendar_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.calendar_table.setSelectionMode(QTableWidget.NoSelection)

        # Create a widget to hold the calendar table and set stretch policy
        self.calendar_table_widget = QWidget()
        self.calendar_table_layout = QVBoxLayout(self.calendar_table_widget)
        self.calendar_table_layout.addWidget(self.calendar_table)
        self.calendar_table_layout.setStretch(0, 1)  # Ensure the table takes up remaining space

        self.calendar_layout.addWidget(self.calendar_table_widget)

        # Legend
        self.legend_label = QLabel()
        self.legend_label.setStyleSheet("border: none; padding: 5px; background-color: #f9f9f9;")
        self.legend_label.setFixedHeight(60)  # Fixed height for the legend
        self.calendar_layout.addWidget(self.legend_label)

        self.prev_month_button.clicked.connect(self.show_prev_month)
        self.next_month_button.clicked.connect(self.show_next_month)

        self.current_date = QDate.currentDate()
        self.show_month(self.current_date.year(), self.current_date.month())

        self.calendar_tab.setLayout(self.calendar_layout)

        # Load initial worker data into combobox
        self.load_worker_filter()

        # Update legend
        self.update_legend()

    def load_worker_filter(self):
        workers = self.load_workers()
        for worker in workers:
            self.worker_filter_combobox.addItem(worker[1])

    def filter_tasks_by_worker(self):
        self.show_month(self.current_date.year(), self.current_date.month())

    def initialize_task_form(self):
        self.task_start_input.setDisplayFormat('dd.MM.yyyy')
        self.task_start_input.setCalendarPopup(True)
        self.task_start_input.setDate(QDate.currentDate())

        self.task_end_input.setDisplayFormat('dd.MM.yyyy')
        self.task_end_input.setCalendarPopup(True)
        self.task_end_input.setDate(QDate.currentDate())

        self.task_status_input.addItems(['В процессе', 'Выполнено', 'Приостановлена'])

    def update_data(self):
        current_index = self.tabs.currentIndex()
        if current_index == 0:  # Workers tab
            self.load_workers()
        elif current_index == 1:  # Tasks tab
            workers = self.load_workers()  # Update worker combo boxes
            for i in range(
                    self.task_worker_layout.count() - 2):  # Обновляем все комбобоксы, кроме кнопки и кнопки удаления
                combo = self.task_worker_layout.itemAt(i).widget()
                if isinstance(combo, QComboBox):
                    combo.clear()
                    combo.addItems([w[1] for w in workers])
            self.load_tasks()
        elif current_index == 2:  # Calendar tab
            self.show_month(self.current_date.year(), self.current_date.month())

    def add_worker(self):
        name = self.worker_name_input.text().strip()
        if name:
            try:
                with sqlite3.connect('tasks.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO workers (name) VALUES (?)', (name,))
                    conn.commit()
                self.worker_name_input.clear()
                self.update_data()
            except Exception as e:
                print(f"Ошибка при добавлении работника: {e}")
        else:
            print("Имя работника не заполнено.")

    def remove_worker(self):
        selected_items = self.worker_list.selectedItems()
        if selected_items:
            selected_worker = selected_items[0].text()
            try:
                workers = self.load_workers()
                worker_id = next((w[0] for w in workers if w[1] == selected_worker), None)
                if worker_id:
                    with sqlite3.connect('tasks.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute('DELETE FROM workers WHERE id = ?', (worker_id,))
                        conn.commit()
                    self.update_data()
                else:
                    print(f"Не найден работник с именем: {selected_worker}")
            except Exception as e:
                print(f"Ошибка удаления работника: {e}")
        else:
            print("Работник не выбран.")

    def add_task(self):
        title = self.task_title_input.text().strip()
        start_date = self.task_start_input.date().toString('yyyy-MM-dd')
        end_date = self.task_end_input.date().toString('yyyy-MM-dd')
        status = self.task_status_input.currentText()

        if title:
            try:
                with sqlite3.connect('tasks.db') as conn:
                    cursor = conn.cursor()
                    # Вставляем задачу
                    cursor.execute(
                        'INSERT INTO tasks (title, start_date, end_date, status) VALUES (?, ?, ?, ?)',
                        (title, start_date, end_date, status)
                    )
                    task_id = cursor.lastrowid

                    # Получаем все комбобоксы работников
                    comboboxes = [self.task_worker_layout.itemAt(i).widget() for i in
                                  range(self.task_worker_layout.count() - 2)]
                    for combo in comboboxes:
                        worker_name = combo.currentText()
                        workers = self.load_workers()
                        worker_id = next((w[0] for w in workers if w[1] == worker_name), None)
                        if worker_id:
                            # Связываем задачу с работником
                            cursor.execute(
                                'INSERT INTO task_workers (task_id, worker_id) VALUES (?, ?)',
                                (task_id, worker_id)
                            )
                    conn.commit()
                self.task_title_input.clear()
                self.task_status_input.setCurrentIndex(0)
                self.update_data()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении задачи: {e}")
        else:
            QMessageBox.warning(self, "Ошибка", "Название задачи не заполнено.")

    def remove_task(self):
        selected_items = self.task_table.selectedItems()
        if selected_items:
            selected_row = selected_items[0].row()
            task_id = self.task_table.item(selected_row, 0).data(Qt.UserRole)
            try:
                with sqlite3.connect('tasks.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
                    conn.commit()
                self.update_data()
            except Exception as e:
                print(f"Ошибка при удалении задачи: {e}")
        else:
            print("Задача не выбрана.")

    def load_workers(self):
        try:
            with sqlite3.connect('tasks.db') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM workers')
                workers = cursor.fetchall()
            self.worker_list.clear()
            for worker in workers:
                self.worker_list.addItem(worker[1])
            return workers
        except Exception as e:
            print(f"Ошибка при загрузки таблицы Работники: {e}")
            return []

    def load_tasks(self, worker=None, task=None, status=None):
        try:
            conn = sqlite3.connect('tasks.db')
            cursor = conn.cursor()

            query = '''
        SELECT tasks.id, workers.name, tasks.title, tasks.start_date, tasks.end_date, tasks.status
        FROM tasks
        JOIN task_workers ON tasks.id = task_workers.task_id
        JOIN workers ON task_workers.worker_id = workers.id
        WHERE 1=1
        '''
            params = []

            if worker and worker != 'Все работники':
                query += ' AND workers.name = ?'
                params.append(worker)

            if task and task != 'Все задачи':
                query += ' AND tasks.title = ?'
                params.append(task)

            if status and status != 'Все статусы':
                query += ' AND tasks.status = ?'
                params.append(status)

            cursor.execute(query, params)
            tasks = cursor.fetchall()
            conn.close()

            self.task_table.clearContents()
            self.task_table.setRowCount(len(tasks))
            self.task_table.setColumnCount(5)
            self.task_table.setHorizontalHeaderLabels(['Работник', 'Задача', 'Дата начала', 'Дата конца', 'Статус'])

            status_items = ['В процессе', 'Выполнено', 'Приостановлена']

            for row_index, task in enumerate(tasks):
                for col_index in range(1, 6):
                    data = task[col_index]
                    if col_index == 3 or col_index == 4:
                        if isinstance(data, str):
                            try:
                                data = datetime.strptime(data, '%Y-%m-%d').strftime('%d.%m.%Y')
                            except ValueError:
                                data = 'Invalid Date'
                    if col_index == 5:
                        combo_box = QComboBox()
                        combo_box.addItems(status_items)
                        combo_box.setCurrentText(data)
                        combo_box.currentIndexChanged.connect(
                            lambda index, row=row_index: self.update_task_status(row, status_items[index]))
                        self.task_table.setCellWidget(row_index, col_index - 1, combo_box)
                    else:
                        item = QTableWidgetItem(str(data))
                        if col_index == 1:
                            item.setData(Qt.UserRole, task[0])  # Сохраняем ID задачи
                        self.task_table.setItem(row_index, col_index - 1, item)

            self.task_table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке задач: {e}")

    def showEvent(self, event):
        super().showEvent(event)
        self.task_table.resizeColumnsToContents()

    def update_task_status(self, row, new_status):
        try:
            task_id = self.task_table.item(row, 0).data(Qt.UserRole)
            conn = sqlite3.connect('tasks.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE tasks SET status = ? WHERE id = ?', (new_status, task_id))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating task status: {e}")

    def show_month(self, year, month):
        self.current_date = QDate(year, month, 1)
        days_in_month = self.current_date.daysInMonth()
        first_day_of_month = self.current_date.dayOfWeek() - 1

        # Определите количество строк, необходимых для отображения дней месяца
        num_rows = (days_in_month + first_day_of_month + 6) // 7

        # Обновите количество строк в таблице
        self.calendar_table.setRowCount(num_rows)  # Не добавляем строку для легенды

        # Очистите таблицу
        self.calendar_table.clearContents()

        # Обновляем заголовок месяца и года
        self.month_year_label.setText(self.current_date.toString('MMMM yyyy'))

        selected_worker = self.worker_filter_combobox.currentText()

        for i in range(1, days_in_month + 1):
            day_date = QDate(year, month, i)
            tasks = self.get_tasks_for_date(day_date.toString('yyyy-MM-dd'))

            if selected_worker != 'Все работники':
                tasks = [task for task in tasks if task[1] == selected_worker]

            # Создаем HTML контент для даты
            html_task_details = f"<div style='font-size: 16px; font-weight: bold; color: #333;'>{i}</div>"
            if tasks:
                task_details = "<br>".join([
                    f"{get_status_color_dot(task[5])} <b>{task[1]}</b>: {task[2]}"
                    for task in tasks
                ])
                html_task_details += f"<div style='margin-top: 5px;'>{task_details}</div>"

            # Создаем QTextBrowser для отображения задач
            text_browser = QTextBrowser()
            text_browser.setHtml(html_task_details)

            # Форматируем выходные и сегодняшний день
            column = (i + first_day_of_month - 1) % 7
            if column in [5, 6]:  # СБ и ВС
                text_browser.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
                # Удаляем задачи в выходные, но показываем число
                text_browser.setHtml(f"<div style='font-size: 16px; font-weight: bold; color: #333;'>{i}</div>")
            elif day_date == QDate.currentDate():
                text_browser.setStyleSheet("background-color: #e3f2fd; border: 1px solid #90caf9;")  # Нежно-голубой цвет
            else:
                text_browser.setStyleSheet("border: 1px solid #ccc;")

            # Устанавливаем виджет в ячейку таблицы
            row = (i + first_day_of_month - 1) // 7
            column = (i + first_day_of_month - 1) % 7
            self.calendar_table.setCellWidget(row, column, text_browser)

        # Настроим размеры заголовков таблицы
        self.calendar_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.calendar_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.calendar_table.resizeRowsToContents()

        # Обновляем легенду под таблицей
        self.update_legend()

    def update_legend(self):
        # Update legend text
        legend_text = """
        <div style="font-size: 16px; margin-top: 2px; color: #555;">
            <b>Статус задачи:</b><br>
            <span style="color: green;">&#9679;</span> Выполнено
            <span style="color: red;">&#9679;</span> Приостановлена 
            <span style="color: blue;">&#9679;</span> В процессе
        </div>
        """
        self.legend_label.setText(legend_text)

    def get_tasks_for_date(self, date_str):
        try:
            with sqlite3.connect('tasks.db') as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT tasks.id, workers.name, tasks.title, tasks.start_date, tasks.end_date, tasks.status '
                    'FROM tasks '
                    'JOIN task_workers ON tasks.id = task_workers.task_id '
                    'JOIN workers ON task_workers.worker_id = workers.id '
                    'WHERE tasks.start_date <= ? AND tasks.end_date >= ?',
                    (date_str, date_str)
                )
                tasks = cursor.fetchall()
                return tasks
        except Exception as e:
            print(f"Error fetching tasks for date {date_str}: {e}")
            return []

    def show_prev_month(self):
        self.current_date = self.current_date.addMonths(-1)
        self.show_month(self.current_date.year(), self.current_date.month())

    def show_next_month(self):
        self.current_date = self.current_date.addMonths(1)
        self.show_month(self.current_date.year(), self.current_date.month())


def create_color_dot_pixmap(color, size=10):
    """Создает QPixmap с точкой нужного цвета."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)  # Делает фон прозрачным
    painter = QPainter(pixmap)
    painter.setBrush(QColor(color))
    painter.drawEllipse(0, 0, size, size)  # Рисуем круг (точку)
    painter.end()
    return pixmap


def get_status_color_dot(status):
    color_map = {
        "Выполнено": TASK_DONE,
        "Приостановлена": TASK_STOP,
        "В процессе": TASK_PROCESSING  # Придуманный статус для "в процессе"
    }
    color = color_map.get(status, "gray")  # По умолчанию - серый цвет
    return f'<span style="color:{color};">&#9679;</span>'


def backup_tasks_db(force_backup=False):
    db_path = 'tasks.db'

    # Определите формат для папки резервных копий
    backup_folder_name = datetime.now().strftime("backup_%d_%m_%Y")
    backup_folder = os.path.join('backups', backup_folder_name)
    os.makedirs(backup_folder, exist_ok=True)  # Создаем папку для резервных копий, если её нет

    # Определите путь для резервной копии
    backup_path = os.path.join(backup_folder, f'tasks_backup_{datetime.now().strftime("%H%M%S")}.db')

    # Проверьте, существует ли уже резервная копия
    if not any(fname.startswith('tasks_backup') for fname in os.listdir(backup_folder)) or force_backup:
        try:
            shutil.copy(db_path, backup_path)
            print(f"Резервная копия создана: {backup_path}")
        except Exception as e:
            print(f"Ошибка при создании резервной копии: {e}")
    else:
        print("Резервная копия уже существует, пропуск создания.")


def is_even_day():
    day = datetime.now().day
    return day


def has_backup_been_made():
    day = datetime.now().day
    backup_folder = f'backup_{day}'
    return os.path.exists(backup_folder) and len(os.listdir(backup_folder)) > 0


def perform_daily_backup():
    if is_even_day() and not has_backup_been_made():
        backup_tasks_db()


def main():
    perform_daily_backup()


if __name__ == '__main__':
    main()
    app = QApplication(sys.argv)
    window = TaskManager()
    window.show()
    sys.exit(app.exec_())
