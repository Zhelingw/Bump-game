# server.py
import bottle
import random
from play_algorithms import Hand, Game
import sqlite3
import os

SESSIONS = {}


def get_db():
    # Use the same path as in init_db.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    db_path = os.path.join(parent_dir, "data", "information.sqlite")
    return sqlite3.connect(db_path)


@bottle.get("/index.html")
def serve_index():
    return bottle.static_file("index.html", root="./client")


@bottle.get("/rules.html")
def serve_rules():
    return bottle.static_file("rules.html", root="./client")


@bottle.get("/login.html")
def serve_login():
    return bottle.static_file("login.html", root="./client")


@bottle.get("/")
def root_redirect():
    return bottle.static_file("splash.html", root="./client")


def choose_mode():
    # Serve or redirect to /choose_mode.html
    return bottle.static_file("choose_mode.html", root="./client")


@bottle.get("/choose_mode.html")
def choose_mode_html():
    return bottle.static_file("choose_mode.html", root="./client")


@bottle.get("/play.html")
def play_html():
    return bottle.static_file("play.html", root="./client")


@bottle.get("/static/<filename:path>")
def static_files(filename):
    return bottle.static_file(filename, root="./client")


@bottle.post("/new_game")
def new_game():
    data = bottle.request.json
    # Make sure we get the difficulty from the request and preserve its case
    difficulty = data.get("difficulty", "easy")
    print(f"New game started with difficulty: {difficulty}")  # Debug log
    username = data.get("username")

    session_id = str(random.randint(10000, 99999))
    player = Hand()
    system = Hand()
    game = Game(player, system)

    SESSIONS[session_id] = {
        "game": game,
        "player": player,
        "system": system,
        "difficulty": difficulty.strip(),  # Ensure no whitespace
        "username": username,
    }

    return {
        "session_id": session_id,
        "player_hands": player.numbers,
        "system_hands": system.numbers,
    }


@bottle.post("/move")
def move():
    data = bottle.request.json
    session_id = data.get("session_id")
    s_hand = data.get("system_hand")
    p_hand = data.get("player_hand")

    if not session_id or session_id not in SESSIONS:
        return {"error": "Invalid session_id"}
    game_data = SESSIONS[session_id]
    game = game_data["game"]
    player = game_data["player"]
    system = game_data["system"]

    # 1) player's bump
    player.bump(p_hand, system, s_hand)
    # Check for winner immediately after player's move
    if game.won(player):
        update_game_stats(session_id, "player")
        return {
            "player_hands": player.numbers,
            "system_hands": system.numbers,
            "winner": "Player",
        }
    if game.won(system):
        update_game_stats(session_id, "system")
        return {
            "player_hands": player.numbers,
            "system_hands": system.numbers,
            "winner": "System",
        }

    return {
        "player_hands": player.numbers,
        "system_hands": system.numbers,
        "turn": "Your turn!",
    }


@bottle.get("/create_account.html")
def serve_create_account():
    return bottle.static_file("create_account.html", root="./client")


@bottle.post("/create_account")
def create_account():
    data = bottle.request.json
    username = data.get("username")
    password = data.get("password")

    db = get_db()
    cursor = db.cursor()

    try:
        # Check if username already exists
        cursor.execute("SELECT UserName FROM Player WHERE UserName = ?", (username,))
        if cursor.fetchone():
            return {"error": "Username already exists"}

        # Get next ID
        cursor.execute("SELECT MAX(ID) FROM Player")
        result = cursor.fetchone()
        next_id = 1 if result[0] is None else result[0] + 1

        # Insert new player
        cursor.execute(
            "INSERT INTO Player (ID, UserName, PassWord) VALUES (?, ?, ?)",
            (next_id, username, password),
        )

        # Initialize Summary entries for all three difficulty levels
        for level in range(1, 4):  # 1=Easy, 2=Moderate, 3=Hard
            cursor.execute(
                """
                INSERT INTO Summary (PlayerID, Level, TimesPlayed, WinCount, TieCount)
                VALUES (?, ?, 0, 0, 0)
            """,
                (next_id, level),
            )

        db.commit()

        return {"success": True}

    except sqlite3.Error as e:
        return {"error": str(e)}

    finally:
        db.close()


@bottle.post("/verify_login")
def verify_login():
    data = bottle.request.json
    username = data.get("username")
    password = data.get("password")

    db = get_db()
    cursor = db.cursor()

    try:
        # Check if username and password match
        cursor.execute(
            "SELECT * FROM Player WHERE UserName = ? AND PassWord = ?",
            (username, password),
        )
        if cursor.fetchone():
            return {"success": True}
        else:
            return {"error": "Invalid credentials"}

    except sqlite3.Error as e:
        return {"error": str(e)}

    finally:
        db.close()


@bottle.get("/history.html")
def serve_history():
    return bottle.static_file("history.html", root="./client")


@bottle.get("/get_history")
def get_history():
    username = bottle.request.query.get("username")

    db = get_db()
    cursor = db.cursor()

    try:
        # Get player ID
        cursor.execute("SELECT ID FROM Player WHERE UserName = ?", (username,))
        player = cursor.fetchone()
        if not player:
            return {"error": "Player not found"}

        player_id = player[0]

        # Get win counts for each level
        cursor.execute(
            """
            SELECT Level, TimesPlayed, WinCount, TieCount 
            FROM Summary 
            WHERE PlayerID = ?
        """,
            (player_id,),
        )

        results = cursor.fetchall()
        history = {}

        for level, played, wins, ties in results:
            if level == 1:
                history["easy"] = {"played": played, "wins": wins, "ties": ties}
            elif level == 2:
                history["moderate"] = {"played": played, "wins": wins, "ties": ties}
            elif level == 3:
                history["hard"] = {"played": played, "wins": wins, "ties": ties}

        return history

    except sqlite3.Error as e:
        return {"error": str(e)}

    finally:
        db.close()


def update_game_stats(session_id, winner):
    if session_id not in SESSIONS:
        return

    game_data = SESSIONS[session_id]
    difficulty = game_data.get("difficulty", "easy").strip()
    print(f"Updating stats for difficulty: {difficulty}")  # Debug log
    username = game_data.get("username")

    if not username:
        return

    # Convert difficulty to level number
    level = 1  # default easy
    if difficulty.lower() == "moderate":
        level = 2
    elif difficulty.lower() == "hard":
        level = 3
    print(f"Converted to level: {level}")  # Debug log

    db = get_db()
    cursor = db.cursor()

    try:
        # Get player ID
        cursor.execute("SELECT ID FROM Player WHERE UserName = ?", (username,))
        player = cursor.fetchone()
        if not player:
            return

        player_id = player[0]

        # Check if record exists
        cursor.execute(
            """
            SELECT TimesPlayed, WinCount, TieCount 
            FROM Summary 
            WHERE PlayerID = ? AND Level = ?
        """,
            (player_id, level),
        )

        result = cursor.fetchone()

        if result:
            times_played, win_count, tie_count = result
            if winner == "player":
                win_count += 1
            elif winner == "tie":
                tie_count += 1

            cursor.execute(
                """
                UPDATE Summary 
                SET TimesPlayed = ?, WinCount = ?, TieCount = ? 
                WHERE PlayerID = ? AND Level = ?
            """,
                (times_played + 1, win_count, tie_count, player_id, level),
            )
        else:
            # Create new record
            win_count = 1 if winner == "player" else 0
            tie_count = 1 if winner == "tie" else 0
            cursor.execute(
                """
                INSERT INTO Summary (PlayerID, Level, TimesPlayed, WinCount, TieCount)
                VALUES (?, ?, 1, ?, ?)
            """,
                (player_id, level, win_count, tie_count),
            )

        db.commit()

    except sqlite3.Error as e:
        print(f"Database error: {e}")

    finally:
        db.close()


@bottle.post("/system_move")
def system_move():
    data = bottle.request.json
    session_id = data.get("session_id")
    phase = data.get("phase", "simulate")  # "simulate" or "execute"

    if not session_id or session_id not in SESSIONS:
        return {"error": "Invalid session_id"}

    game_data = SESSIONS[session_id]
    game = game_data["game"]
    player = game_data["player"]
    system = game_data["system"]
    difficulty = game_data.get("difficulty", "easy")  # Default to easy if not set

    if phase == "simulate":
        # Make system's move based on difficulty
        if difficulty.lower() == "easy":
            move = game.system_turn_easy(system, player)
        elif difficulty.lower() == "moderate":
            move = game.system_turn_moderate(system, player)
        else:  # hard mode
            move = game.system_turn_hard(system, player)

        return {
            "player_hands": player.numbers,
            "system_hands": system.numbers,
            "move": move,
        }
    else:  # phase == "execute"
        from_hand = data.get("from_hand")
        to_hand = data.get("to_hand")
        game.execute_system_move(system, player, from_hand, to_hand)

        # Check winner after system's move
        if game.won(system):
            update_game_stats(session_id, "system")
            return {
                "player_hands": player.numbers,
                "system_hands": system.numbers,
                "winner": "System",
            }
        if game.won(player):
            update_game_stats(session_id, "player")
            return {
                "player_hands": player.numbers,
                "system_hands": system.numbers,
                "winner": "Player",
            }

        return {"player_hands": player.numbers, "system_hands": system.numbers}


@bottle.post("/game_tie")
def game_tie():
    data = bottle.request.json
    session_id = data.get("session_id")

    if not session_id or session_id not in SESSIONS:
        return {"error": "Invalid session_id"}

    update_game_stats(session_id, "tie")
    return {"success": True}


if __name__ == "__main__":
    bottle.run(host="localhost", port=8080, debug=True, reloader=True)
