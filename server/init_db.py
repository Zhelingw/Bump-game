import sqlite3
import os


def init_db():
    # Get the absolute path to the database and SQL files
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    data_dir = os.path.join(parent_dir, "data")
    db_path = os.path.join(data_dir, "information.sqlite")
    sql_file_path = os.path.join(data_dir, "information.sql")

    print(f"Creating database at: {db_path}")
    print(f"Looking for SQL file at: {sql_file_path}")

    try:
        # Connect to database in data directory
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        with open(sql_file_path, "r") as sql_file:
            sql_script = sql_file.read()

        # Execute the SQL script
        cursor.executescript(sql_script)

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

        print("Database initialized successfully!")

    except FileNotFoundError:
        print(f"Error: Could not find the SQL file at {sql_file_path}")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    init_db()
