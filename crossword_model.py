import numpy as np
import logging
from numba import njit

# ---------------------------------------------------------
# NUMBA JIT COMPILED CORE (cache=False prevents old bugs)
# ---------------------------------------------------------

@njit(cache=False)
def _can_place(grid, word, r, c, d, H, W, L, is_first):
    if d == 0: # Horizontal
        if c < 0 or c + L > W or r < 0 or r >= H: return False
        if not is_first:
            if c > 0 and grid[r, c - 1] != 0: return False
            if c + L < W and grid[r, c + L] != 0: return False
        dr, dc = 0, 1
        pr, pc = 1, 0
    else: # Vertical
        if r < 0 or r + L > H or c < 0 or c >= W: return False
        if not is_first:
            if r > 0 and grid[r - 1, c] != 0: return False
            if r + L < H and grid[r + L, c] != 0: return False
        dr, dc = 1, 0
        pr, pc = 0, 1

    has_int = is_first
    for i in range(L):
        cr = r + dr * i
        cc = c + dc * i
        cell_val = grid[cr, cc]
        word_val = word[i]

        if cell_val == word_val:
            has_int = True
        elif cell_val == 0:
            for s in (-1, 1):
                nr = cr + pr * s
                nc = cc + pc * s
                if 0 <= nr < H and 0 <= nc < W:
                    if grid[nr, nc] != 0:
                        return False
        else:
            return False 
            
    return has_int

@njit(cache=False)
def _do_place(grid, word, r, c, d, L):
    if d == 0:
        for i in range(L): grid[r, c + i] = word[i]
    else:
        for i in range(L): grid[r + i, c] = word[i]

@njit(cache=False)
def _do_remove(grid, word, r, c, d, L):
    if d == 0:
        for i in range(L): grid[r, c + i] = 0
    else:
        for i in range(L): grid[r + i, c] = 0

@njit(cache=False)
def _restore_state(grid, state, word_arr, num_placed, max_L):
    for i in range(num_placed):
        w_idx = state[i, 0]
        pr = state[i, 1]
        pc = state[i, 2]
        pd = state[i, 3]
        word = word_arr[w_idx]
        L = 0
        while L < max_L and word[L] != 0: L += 1
        _do_place(grid, word, pr, pc, pd, L)

@njit(cache=False)
def _find_placements(grid, word, state, word_arr, num_placed, H, W, L, max_L, max_placements, is_first):
    placements = np.zeros((max_placements, 3), dtype=np.int32)
    counts = np.zeros(max_placements, dtype=np.int32)
    num_valid = 0

    if is_first:
        if _can_place(grid, word, H // 2, (W - L) // 2, 0, H, W, L, True):
            placements[0] = [H // 2, (W - L) // 2, 0]
            counts[0] = 0
            return placements, counts, 1
        return placements, counts, 0

    for p in range(num_placed):
        pw_idx = state[p, 0]
        pr = state[p, 1]
        pc = state[p, 2]
        pd = state[p, 3]
        p_word = word_arr[pw_idx]
        pL = 0
        while pL < max_L and p_word[pL] != 0: pL += 1

        for i in range(pL):
            for j in range(L):
                if p_word[i] == word[j]:
                    if pd == 0: 
                        nr, nc, nd = pr - j, pc + i, 1
                    else:       
                        nr, nc, nd = pr + i, pc - j, 0
                    
                    if _can_place(grid, word, nr, nc, nd, H, W, L, False):
                        ints = 0
                        dr, dc = (0, 1) if nd == 0 else (1, 0)
                        for k in range(L):
                            if grid[nr + dr*k, nc + dc*k] == word[k]: ints += 1
                            
                        placements[num_valid] = [nr, nc, nd]
                        counts[num_valid] = ints
                        num_valid += 1
                        if num_valid >= max_placements: return placements, counts, num_valid
    return placements, counts, num_valid

@njit(cache=False)
def _random_playout(grid, word_arr, word_order, start_depth, num_words, H, W, max_L):
    temp_grid = grid.copy()
    score = 0
    remaining = num_words - start_depth
    if remaining == 0: return 0
    
    indices = np.arange(start_depth, num_words, dtype=np.int32)
    for i in range(remaining):
        j = np.random.randint(0, remaining - i) + i
        indices[i], indices[j] = indices[j], indices[i]
        
        w_idx = word_order[indices[i]]
        word = word_arr[w_idx]
        L = 0
        while L < max_L and word[L] != 0: L += 1
        if L < 2: continue
        
        placed = False
        for r in range(H):
            if placed: break
            for c in range(W):
                if placed: break
                cell_val = temp_grid[r, c]
                if cell_val == 0: continue
                for k in range(L):
                    if word[k] == cell_val:
                        nr = r - k
                        if _can_place(temp_grid, word, nr, c, 1, H, W, L, False):
                            _do_place(temp_grid, word, nr, c, 1, L)
                            score += 1
                            placed = True
                            break
                        nc = c - k
                        if _can_place(temp_grid, word, r, nc, 0, H, W, L, False):
                            _do_place(temp_grid, word, r, nc, 0, L)
                            score += 1
                            placed = True
                            break
    return score

@njit(cache=False)
def _mcts_backtrack(grid, word_arr, word_order, state, depth, H, W, max_L, num_words, max_placements, mcts_simulations):
    if depth == num_words:
        return True

    w_idx = word_order[depth]
    word = word_arr[w_idx]
    L = 0
    while L < max_L and word[L] != 0: L += 1
    if L < 2: 
        return _mcts_backtrack(grid, word_arr, word_order, state, depth + 1, H, W, max_L, num_words, max_placements, mcts_simulations)

    is_first = (depth == 0)
    placements, counts, num_valid = _find_placements(grid, word, state, word_arr, depth, H, W, L, max_L, max_placements, is_first)
    
    if num_valid == 0:
        return False

    mcts_scores = np.zeros(num_valid, dtype=np.int32)
    for i in range(num_valid):
        r, c, d = placements[i]
        _do_place(grid, word, r, c, d, L)
        
        total_score = 0
        for _ in range(mcts_simulations):
            total_score += _random_playout(grid, word_arr, word_order, depth + 1, num_words, H, W, max_L)
        mcts_scores[i] = total_score
        
        _do_remove(grid, word, r, c, d, L)
        _restore_state(grid, state, word_arr, depth, max_L)

    for i in range(num_valid):
        for j in range(i + 1, num_valid):
            if mcts_scores[j] > mcts_scores[i]:
                mcts_scores[i], mcts_scores[j] = mcts_scores[j], mcts_scores[i]
                placements[i], placements[j] = placements[j].copy(), placements[i].copy()

    for i in range(num_valid):
        r, c, d = placements[i]
        
        _do_place(grid, word, r, c, d, L)
        state[depth, 0] = w_idx
        state[depth, 1] = r
        state[depth, 2] = c
        state[depth, 3] = d
        
        if _mcts_backtrack(grid, word_arr, word_order, state, depth + 1, H, W, max_L, num_words, max_placements, mcts_simulations):
            return True
            
        _do_remove(grid, word, r, c, d, L)
        _restore_state(grid, state, word_arr, depth, max_L)

    return False

# ---------------------------------------------------------
# PYTHON WRAPPER
# ---------------------------------------------------------

class CrosswordSolver:
    def __init__(self, rows, cols, words, mcts_simulations=10):
        # FIX: Explicitly named rows/cols so they can NEVER swap
        self.rows = rows
        self.cols = cols
        self.words = sorted(list(set(w for w in words if len(w) > 1)), key=len, reverse=True)
        self.mcts_simulations = mcts_simulations
        
        self.max_word_len = max(len(w) for w in self.words) if self.words else 0
        self.word_arr = np.zeros((len(self.words), self.max_word_len), dtype=np.int8)
        
        for i, word in enumerate(self.words):
            for j, char in enumerate(word):
                self.word_arr[i, j] = ord(char.upper()) - 64 

        self.word_order = np.arange(len(self.words), dtype=np.int32)

    def solve(self):
        if not self.words:
            return False, []

        logging.info(f"Compiling Numba & solving {len(self.words)} words on {self.rows}x{self.cols} grid...")

        # FIX: Grid is strictly initialized as (rows, cols)
        grid = np.zeros((self.rows, self.cols), dtype=np.int8)
        state = np.zeros((len(self.words), 4), dtype=np.int32) 
        max_placements = 50 

        success = _mcts_backtrack(
            grid, self.word_arr, self.word_order, state, 
            0, self.rows, self.cols, self.max_word_len, 
            len(self.words), max_placements, self.mcts_simulations
        )

        placed_words = []
        if success:
            for i in range(len(self.words)):
                w_idx = state[i, 0]
                r, c, d = state[i, 1], state[i, 2], state[i, 3]
                direction = 'H' if d == 0 else 'V'
                placed_words.append((self.words[w_idx], int(r), int(c), direction))
            logging.info(f"SUCCESS: Numba placed {len(placed_words)} words.")
        else:
            logging.error("Failed to fit all words.")

        return success, placed_words