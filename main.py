import streamlit as st
import sqlite3

st.set_page_config(page_title="TU BookShare", page_icon="📕")

# Function to create a connection to the SQLite database
def create_connection():
    conn = sqlite3.connect('book_lending.db')
    return conn

# Function to initialize the database tables
def init_db():
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                owner TEXT NOT NULL,
                FOREIGN KEY (owner) REFERENCES users(username)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                requester TEXT,
                FOREIGN KEY (book_id) REFERENCES books(id),
                FOREIGN KEY (requester) REFERENCES users(username)
            )
        ''')
        conn.commit()

def main():
    # Custom CSS for styling
    st.markdown("""
    <style>
        body {
            background-color: #f0f2f5;
            font-family: 'Helvetica Neue', sans-serif;
        }
        .title {
            text-align: center;
            color: #333;
            font-size: 40px;
            margin-bottom: 20px;
        }
        .sidebar .sidebar-content {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 20px;
        }
        .stButton>button {
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
            cursor: pointer;
        }
        .stButton>button:hover {
            background-color: #0056b3;
        }
        .book-title {
            font-weight: bold;
            color: #007bff;
        }
        .success {
            color: #28a745;
        }
        .error {
            color: #dc3545;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="title">TU BookShare📖</div>', unsafe_allow_html=True)
    init_db()  # Initialize the database


    # User Authentication
    menu = ["Login", "Register", "Credits"]
    choice = st.sidebar.selectbox("Select Activity", menu)

    if choice == "Register":
        register_user()
    elif choice == "Login":
        current_user = login_user()
        if current_user:
            st.session_state.current_user = current_user
            user_dashboard(current_user)
    elif choice == "Credits":
        show_credits()

    if 'current_user' in st.session_state:
        user_dashboard(st.session_state.current_user)

def register_user():
    st.subheader("Register")
    username = st.text_input("Phone Number", key="register_username")
    password = st.text_input("Password", type='password', key="register_password")
    if st.button("Register", key="register_button"):
        with create_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                st.success("User registered successfully!", icon="✅")
            except sqlite3.IntegrityError:
                st.error("User already exists!", icon="❌")

def login_user():
    st.subheader("Login")
    username = st.text_input("Phone NUmber", key="login_username")
    password = st.text_input("Password", type='password', key="login_password")
    if st.button("Login", key="login_button"):
        with create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
            user = cursor.fetchone()
            if user:
                st.success("Logged in as {}".format(username), icon="✅")
                return username
            else:
                st.error("Invalid username or password", icon="❌")
    return None

def user_dashboard(username):
    st.sidebar.title("Dashboard")
    st.sidebar.subheader("Logged in as {}".format(username))
    
    # Logout button
    if st.sidebar.button("Logout"):
        del st.session_state.current_user
        st.success("Logged out successfully!", icon="✅")
        st.experimental_rerun()

    # Book Management
    st.subheader("Your Books")
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM books WHERE owner = ?", (username,))
        user_books = cursor.fetchall()

    if user_books:
        for book in user_books:
            book_title = book[0]
            col1, col2 = st.columns([1, 1])
            col1.markdown(f'<span class="book-title">{book_title}</span>', unsafe_allow_html=True)
            if col2.button(f"Delete {book_title}", key=f"delete_{username}_{book_title}"):
                with create_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM books WHERE title = ? AND owner = ?", (book_title, username))
                    conn.commit()
                st.success(f"Deleted {book_title}", icon="✅")
                st.experimental_rerun()  # Refresh to show updated list
    else:
        st.write("No books added yet.")

    new_book = st.text_input("Add a new book", key="new_book_input")
    if st.button("Add Book", key="add_book_button"):
        if new_book:
            with create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO books (title, owner) VALUES (?, ?)", (new_book, username))
                conn.commit()
            st.success(f"Added {new_book}", icon="✅")
            st.experimental_rerun()  # Refresh to show updated list

    # Book Pool
    st.subheader("All Available Books")
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, owner FROM books")
        all_books = cursor.fetchall()

    search_query = st.text_input("Search for a book", key="search_book_input")
    filtered_books = [book for book in all_books if search_query.lower() in book[1].lower()]

    for book_id, book_title, owner in filtered_books:
        st.write(book_title)
        if st.button(f"Request {book_title}", key=f"request_{username}_{book_title}"):
            with create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO requests (book_id, requester) VALUES (?, ?)", (book_id, username))
                conn.commit()
            st.success(f"Requested {book_title}", icon="✅")
            st.experimental_rerun()  # Refresh to show updated request

    # Handling Requests
    st.subheader("Your Book Requests")
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM books WHERE owner = ?", (username,))
        user_books = cursor.fetchall()

        for book_id, book_title in user_books:
            cursor.execute("SELECT requester FROM requests WHERE book_id = ?", (book_id,))
            requesters = cursor.fetchall()
            if requesters:
                st.write(f"{book_title} - Requested by: {', '.join([req[0] for req in requesters])}")
                for requester in requesters:
                    req_username = requester[0]
                    if st.button(f"Accept {req_username} for {book_title}", key=f"accept_{username}_{req_username}_{book_title}"):
                        with create_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM requests WHERE book_id = ? AND requester = ?", (book_id, req_username))
                            conn.commit()
                        st.success(f"Accepted {req_username}'s request for {book_title}", icon="✅")
                        st.experimental_rerun()  # Refresh to show updated request
                    if st.button(f"Reject {req_username} for {book_title}", key=f"reject_{username}_{req_username}_{book_title}"):
                        with create_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM requests WHERE book_id = ? AND requester = ?", (book_id, req_username))
                            conn.commit()
                        st.success(f"Rejected {req_username}'s request for {book_title}", icon="✅")
                        st.experimental_rerun()  # Refresh to show updated request

def show_credits():
    st.title("Credits")
    st.write("This application was developed by **Anchit Das**.")
    st.subheader("Connect with me:")
    st.markdown("[Instagram](https://www.instagram.com/anchitknows/)")  # Replace with actual Instagram ID
    st.markdown("[LinkedIn](https://www.linkedin.com/in/itsanchitdas/)")  # Replace with actual LinkedIn profile



if __name__ == "__main__":
    main()
