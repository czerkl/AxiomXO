import math

# Константы для игрока и бота
USER = 'X'
BOT = 'O'
EMPTY = '.'

def get_best_move(board, difficulty="hard"):
    """
    board: список из 9 элементов, например ['.', 'X', 'O', ...]
    difficulty: уровень сложности
    """
    import random
    
    free_cells = [i for i, cell in enumerate(board) if cell == EMPTY]
    
    if not free_cells:
        return None

    # Уровень EASY: просто рандом
    if difficulty == "easy":
        return random.choice(free_cells)

    # Уровень MEDIUM: 50/50 идеальный ход или рандом
    if difficulty == "medium":
        if random.random() < 0.5:
            return random.choice(free_cells)
        # Если не рандом, то идет логика Hard ниже

    # Уровень HARD: Алгоритм Минимакс
    best_score = -math.inf
    move = None
    
    for i in free_cells:
        board[i] = BOT
        score = minimax(board, 0, False)
        board[i] = EMPTY
        if score > best_score:
            best_score = score
            move = i
    return move

def check_winner(b):
    win_coord = ((0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6))
    for pair in win_coord:
        if b[pair[0]] == b[pair[1]] == b[pair[2]] and b[pair[0]] != EMPTY:
            return b[pair[0]]
    if EMPTY not in b:
        return 'tie'
    return None

def minimax(board, depth, is_maximizing):
    res = check_winner(board)
    if res == BOT: return 10 - depth
    if res == USER: return depth - 10
    if res == 'tie': return 0

    if is_maximizing:
        best_score = -math.inf
        for i in range(9):
            if board[i] == EMPTY:
                board[i] = BOT
                score = minimax(board, depth + 1, False)
                board[i] = EMPTY
                best_score = max(score, best_score)
        return best_score
    else:
        best_score = math.inf
        for i in range(9):
            if board[i] == EMPTY:
                board[i] = USER
                score = minimax(board, depth + 1, True)
                board[i] = EMPTY
                best_score = min(score, best_score)
        return best_score