active_connections = []
active_games = []

def get_stats():
    return len(active_connections), len(active_games)

def get_users(users):
    return list(users.keys())

def delete_user(users, email):
    if email in users:
        del users[email]
        return True
    return False

def stop_games():
    for g in active_games:
        g.running = False