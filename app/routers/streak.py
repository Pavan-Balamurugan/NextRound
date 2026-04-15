"""
Streak & Consistency tracking + Daily Coding Challenge.
POST /api/streak/ping       — call on every login/app open
GET  /api/streak/me         — streak info + consistency score (0-100)
GET  /api/streak/challenge  — get a fresh challenge each session
POST /api/streak/challenge/submit — submit answer, updates streak if correct
"""
from datetime import date, timedelta
import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.deps import get_db, get_current_user
from app.models import User
from app.schemas import StreakOut

router = APIRouter(prefix="/api/streak", tags=["streak"])

# ---------------------------------------------------------------------------
# Challenge bank — DSA, DBMS, OS, CN, OOP, Algorithms
# ---------------------------------------------------------------------------
CHALLENGES = [
    # Arrays / Hashing
    {
        "id": 1,
        "title": "Two Sum",
        "description": "Given an array [2, 7, 11, 15] and target = 9, which two indices sum to the target?",
        "choices": ["[0, 1]", "[1, 2]", "[0, 2]", "[2, 3]"],
        "answer": 0,
        "explanation": "nums[0] + nums[1] = 2 + 7 = 9. Classic hash-map problem — O(n) solution.",
        "topic": "Arrays / Hashing",
    },
    {
        "id": 2,
        "title": "Big-O of Binary Search",
        "description": "What is the time complexity of binary search on a sorted array of n elements?",
        "choices": ["O(n)", "O(log n)", "O(n log n)", "O(1)"],
        "answer": 1,
        "explanation": "Binary search halves the search space each step → O(log n).",
        "topic": "Algorithms",
    },
    {
        "id": 3,
        "title": "Linked List — Reverse",
        "description": "To reverse a singly linked list in-place, what is the minimum number of pointers you need?",
        "choices": ["1", "2", "3", "4"],
        "answer": 2,
        "explanation": "You need `prev` and `curr` (and temporarily `next`). Most solutions track 3 pointers total but 2 state variables are the minimum.",
        "topic": "Linked Lists",
    },
    {
        "id": 4,
        "title": "Stack — Valid Parentheses",
        "description": "Which string is NOT a valid parentheses sequence?",
        "choices": ["(())", "()[]{}", "([)]", "{[]}"],
        "answer": 2,
        "explanation": "([)] is invalid — the inner brackets cross. Use a stack: push opens, pop and match on close.",
        "topic": "Stacks",
    },
    {
        "id": 5,
        "title": "Tree Height",
        "description": "A complete binary tree has 7 nodes. What is its height (number of edges on the longest root-to-leaf path)?",
        "choices": ["2", "3", "4", "6"],
        "answer": 0,
        "explanation": "7 nodes = 3 levels (1 + 2 + 4). Height = levels - 1 = 2.",
        "topic": "Trees",
    },
    {
        "id": 6,
        "title": "SQL — JOIN type",
        "description": "Which JOIN returns all rows from the left table even if there is no match in the right?",
        "choices": ["INNER JOIN", "RIGHT JOIN", "LEFT JOIN", "CROSS JOIN"],
        "answer": 2,
        "explanation": "LEFT JOIN keeps all left-table rows; unmatched right columns are NULL.",
        "topic": "DBMS / SQL",
    },
    {
        "id": 7,
        "title": "OS — Deadlock Condition",
        "description": "Which of these is NOT one of the four necessary conditions for deadlock?",
        "choices": ["Mutual Exclusion", "Hold and Wait", "Preemption", "Circular Wait"],
        "answer": 2,
        "explanation": "The four conditions are: Mutual Exclusion, Hold & Wait, No Preemption, Circular Wait. Preemption *prevents* deadlock.",
        "topic": "Operating Systems",
    },
    {
        "id": 8,
        "title": "Fibonacci — DP",
        "description": "Using bottom-up dynamic programming, fib(6) = ?",
        "choices": ["6", "8", "13", "5"],
        "answer": 1,
        "explanation": "fib sequence: 0,1,1,2,3,5,8 → fib(6) = 8 (0-indexed).",
        "topic": "Dynamic Programming",
    },
    {
        "id": 9,
        "title": "Graph — BFS vs DFS",
        "description": "Which algorithm is best for finding the SHORTEST path in an unweighted graph?",
        "choices": ["DFS", "BFS", "Dijkstra", "Bellman-Ford"],
        "answer": 1,
        "explanation": "BFS explores layer by layer — the first time it reaches a node is via the shortest path (fewest edges).",
        "topic": "Graphs",
    },
    {
        "id": 10,
        "title": "OOP — Polymorphism",
        "description": "When a subclass provides a specific implementation of a method already defined in its superclass, this is called…",
        "choices": ["Overloading", "Encapsulation", "Overriding", "Abstraction"],
        "answer": 2,
        "explanation": "Method overriding is runtime polymorphism — the subclass replaces the parent's implementation.",
        "topic": "OOP",
    },
    {
        "id": 11,
        "title": "Hashing — Collision",
        "description": "Which technique resolves hash collisions by storing multiple elements in a linked list at each bucket?",
        "choices": ["Open Addressing", "Linear Probing", "Chaining", "Double Hashing"],
        "answer": 2,
        "explanation": "Chaining stores all colliding keys in a linked list (or similar structure) at the same bucket index.",
        "topic": "Hashing",
    },
    {
        "id": 12,
        "title": "Sorting — Stability",
        "description": "Which sorting algorithm is NOT stable by default?",
        "choices": ["Merge Sort", "Bubble Sort", "Heap Sort", "Insertion Sort"],
        "answer": 2,
        "explanation": "Heap Sort is not stable — heap operations can change the relative order of equal elements.",
        "topic": "Sorting",
    },
    {
        "id": 13,
        "title": "String — Palindrome",
        "description": "What is the time complexity of checking if a string of length n is a palindrome using two pointers?",
        "choices": ["O(n²)", "O(n log n)", "O(n)", "O(1)"],
        "answer": 2,
        "explanation": "Two pointers start at each end and meet in the middle — O(n) time, O(1) space.",
        "topic": "Strings",
    },
    {
        "id": 14,
        "title": "DBMS — Normalization",
        "description": "A table is in 3NF when it is in 2NF AND…",
        "choices": [
            "Has no partial dependencies",
            "Has no transitive dependencies",
            "Has no multivalued dependencies",
            "Every attribute is a candidate key",
        ],
        "answer": 1,
        "explanation": "3NF removes transitive dependencies (non-key attribute depending on another non-key attribute).",
        "topic": "DBMS",
    },
    {
        "id": 15,
        "title": "Network — HTTP Status",
        "description": "Which HTTP status code means 'resource not found'?",
        "choices": ["200", "301", "404", "500"],
        "answer": 2,
        "explanation": "404 Not Found — the server couldn't locate the requested resource.",
        "topic": "Computer Networks",
    },
    {
        "id": 16,
        "title": "Queue — Circular",
        "description": "In a circular queue of size n, how many elements can actually be stored to distinguish full from empty?",
        "choices": ["n", "n+1", "n-1", "n/2"],
        "answer": 2,
        "explanation": "Circular queues commonly store n-1 elements — one slot is kept empty to differentiate full from empty states.",
        "topic": "Queues",
    },
    {
        "id": 17,
        "title": "Recursion — Base Case",
        "description": "What is the output of factorial(0) if defined recursively with base case `if n==0: return 1`?",
        "choices": ["0", "1", "undefined", "Error"],
        "answer": 1,
        "explanation": "factorial(0) = 1 by definition (empty product). This is the base case that stops recursion.",
        "topic": "Recursion",
    },
    {
        "id": 18,
        "title": "Bit Manipulation",
        "description": "What does `n & (n-1)` do?",
        "choices": [
            "Checks if n is odd",
            "Clears the lowest set bit of n",
            "Sets the lowest zero bit of n",
            "Returns n mod 2",
        ],
        "answer": 1,
        "explanation": "n & (n-1) clears the rightmost set bit. If the result is 0, n is a power of two.",
        "topic": "Bit Manipulation",
    },
    {
        "id": 19,
        "title": "Greedy — Activity Selection",
        "description": "In the activity selection problem, which greedy criterion gives the optimal solution?",
        "choices": [
            "Select by earliest start time",
            "Select by shortest duration",
            "Select by earliest finish time",
            "Select by latest start time",
        ],
        "answer": 2,
        "explanation": "Picking the activity that finishes earliest leaves maximum room for remaining activities.",
        "topic": "Greedy",
    },
    {
        "id": 20,
        "title": "Space Complexity",
        "description": "What is the space complexity of a recursive DFS on a graph with V vertices and E edges?",
        "choices": ["O(1)", "O(E)", "O(V)", "O(V + E)"],
        "answer": 2,
        "explanation": "The call stack can go as deep as V (in the worst case a path through all vertices) → O(V) space.",
        "topic": "Graphs",
    },
    # Additional questions to increase variety
    {
        "id": 21,
        "title": "DBMS — ACID",
        "description": "Which ACID property ensures that a transaction is treated as a single unit — either all operations succeed or none do?",
        "choices": ["Consistency", "Isolation", "Durability", "Atomicity"],
        "answer": 3,
        "explanation": "Atomicity means all-or-nothing. If any part of the transaction fails, the entire transaction is rolled back.",
        "topic": "DBMS",
    },
    {
        "id": 22,
        "title": "OS — Page Replacement",
        "description": "Which page replacement algorithm suffers from Belady's anomaly (more frames → more page faults)?",
        "choices": ["LRU", "Optimal", "FIFO", "LFU"],
        "answer": 2,
        "explanation": "FIFO can experience Belady's anomaly. LRU and Optimal do not.",
        "topic": "Operating Systems",
    },
    {
        "id": 23,
        "title": "CN — OSI Model",
        "description": "At which OSI layer does routing between networks happen?",
        "choices": ["Layer 2 — Data Link", "Layer 3 — Network", "Layer 4 — Transport", "Layer 5 — Session"],
        "answer": 1,
        "explanation": "The Network layer (Layer 3) handles logical addressing and routing. Routers operate at this layer.",
        "topic": "Computer Networks",
    },
    {
        "id": 24,
        "title": "Tree — BST Property",
        "description": "In a Binary Search Tree, for any node N, which statement is always true?",
        "choices": [
            "Left child > N > Right child",
            "Left child < N < Right child",
            "Left child = N = Right child",
            "N > all nodes in the tree",
        ],
        "answer": 1,
        "explanation": "BST property: all values in left subtree < node < all values in right subtree.",
        "topic": "Trees",
    },
    {
        "id": 25,
        "title": "DP — Longest Common Subsequence",
        "description": "LCS of 'ABCBDAB' and 'BDCABA' has length?",
        "choices": ["3", "4", "5", "6"],
        "answer": 1,
        "explanation": "LCS is 'BCBA' or 'BDAB' — both length 4. Classic O(mn) DP problem.",
        "topic": "Dynamic Programming",
    },
    {
        "id": 26,
        "title": "OOP — SOLID: Single Responsibility",
        "description": "The Single Responsibility Principle states that a class should have…",
        "choices": [
            "Only one method",
            "Only one reason to change",
            "Only one parent class",
            "Only one constructor",
        ],
        "answer": 1,
        "explanation": "SRP: A class should have only one reason to change — meaning it should have only one job/responsibility.",
        "topic": "OOP",
    },
    {
        "id": 27,
        "title": "Arrays — Dutch National Flag",
        "description": "The Dutch National Flag algorithm sorts an array of 0s, 1s, and 2s in O(n) time. How many pointers does it use?",
        "choices": ["1", "2", "3", "4"],
        "answer": 2,
        "explanation": "It uses 3 pointers: low, mid, and high. Elements are partitioned in a single pass.",
        "topic": "Arrays / Sorting",
    },
    {
        "id": 28,
        "title": "SQL — GROUP BY",
        "description": "Which clause is used to filter groups after a GROUP BY in SQL?",
        "choices": ["WHERE", "FILTER", "HAVING", "ON"],
        "answer": 2,
        "explanation": "HAVING filters groups after aggregation; WHERE filters rows before grouping.",
        "topic": "DBMS / SQL",
    },
    {
        "id": 29,
        "title": "Graph — Minimum Spanning Tree",
        "description": "Which algorithm builds an MST by always picking the smallest edge that does NOT form a cycle?",
        "choices": ["Dijkstra's", "Bellman-Ford", "Prim's", "Kruskal's"],
        "answer": 3,
        "explanation": "Kruskal's algorithm sorts all edges and greedily adds the smallest edge that doesn't create a cycle, using a Union-Find structure.",
        "topic": "Graphs",
    },
    {
        "id": 30,
        "title": "OS — Scheduling",
        "description": "Which CPU scheduling algorithm can lead to starvation of low-priority processes?",
        "choices": ["Round Robin", "FCFS", "Priority Scheduling", "SJF (non-preemptive)"],
        "answer": 2,
        "explanation": "Priority Scheduling can starve low-priority processes if high-priority processes keep arriving. Solution: aging.",
        "topic": "Operating Systems",
    },
]


def _get_session_challenge(user_id: int) -> dict:
    """Pick a pseudo-random challenge based on user_id + today's date.
    This means each user gets a potentially different question,
    and it changes each calendar day."""
    today = date.today()
    seed = user_id * 366 + today.year * 100 + today.timetuple().tm_yday
    idx = seed % len(CHALLENGES)
    return CHALLENGES[idx]


def _get_random_challenge(user_id: int, exclude_id: int = None) -> dict:
    """Pick a truly random challenge (for practice / refresh).
    Avoids the excluded id if possible."""
    pool = [c for c in CHALLENGES if c["id"] != exclude_id] if exclude_id else CHALLENGES
    return random.choice(pool)


# ---------------------------------------------------------------------------
# Streak helpers
# ---------------------------------------------------------------------------

def _compute_consistency(login_history: list) -> int:
    if not login_history:
        return 0
    today = date.today()
    cutoff = today - timedelta(days=29)
    active_days = sum(1 for d in login_history if d and date.fromisoformat(d) >= cutoff)
    return min(100, round((active_days / 30) * 100))


def record_login(user: User) -> None:
    today_str = date.today().isoformat()
    history = list(user.login_history or [])
    if history and history[-1] == today_str:
        return
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()
    if user.last_login_date == yesterday_str:
        user.current_streak = (user.current_streak or 0) + 1
    else:
        user.current_streak = 1
    user.longest_streak = max(user.longest_streak or 0, user.current_streak)
    user.last_login_date = today_str
    history.append(today_str)
    seen = list(dict.fromkeys(history))
    cutoff = (date.today() - timedelta(days=29)).isoformat()
    history = [d for d in seen if d >= cutoff]
    user.login_history = history


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/ping", response_model=StreakOut)
def ping(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    record_login(current)
    db.commit()
    db.refresh(current)
    consistency = _compute_consistency(current.login_history or [])
    return StreakOut(
        current_streak=current.current_streak or 0,
        longest_streak=current.longest_streak or 0,
        consistency_score=consistency,
        login_history=current.login_history or [],
    )


@router.get("/me", response_model=StreakOut)
def get_streak(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    consistency = _compute_consistency(current.login_history or [])
    return StreakOut(
        current_streak=current.current_streak or 0,
        longest_streak=current.longest_streak or 0,
        consistency_score=consistency,
        login_history=current.login_history or [],
    )


@router.get("/challenge")
def get_challenge(current: User = Depends(get_current_user)):
    """Return a fresh challenge for this session. Each user gets a different
    question derived from their user_id + today's date. No 'already_solved'
    gating — students can attempt once per session for streak credit."""
    c = _get_session_challenge(current.id)
    today_str = date.today().isoformat()
    # already_solved = solved the challenge today (streak already credited)
    already_solved = getattr(current, "last_challenge_date", None) == today_str
    return {
        "id": c["id"],
        "title": c["title"],
        "description": c["description"],
        "choices": c["choices"],
        "topic": c["topic"],
        "already_solved": already_solved,
        "today": today_str,
    }


@router.get("/challenge/new")
def get_new_challenge(current: User = Depends(get_current_user)):
    """Get a fresh random challenge (for practice — no streak update)."""
    today_str = date.today().isoformat()
    current_c = _get_session_challenge(current.id)
    c = _get_random_challenge(current.id, exclude_id=current_c["id"])
    return {
        "id": c["id"],
        "title": c["title"],
        "description": c["description"],
        "choices": c["choices"],
        "topic": c["topic"],
        "already_solved": False,
        "today": today_str,
        "practice_mode": True,
    }


class ChallengeSubmit(BaseModel):
    choice_index: int
    challenge_id: int  # which challenge was answered


@router.post("/challenge/submit")
def submit_challenge(
    payload: ChallengeSubmit,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    # Find the challenge by id
    challenge = next((c for c in CHALLENGES if c["id"] == payload.challenge_id), None)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    correct = payload.choice_index == challenge["answer"]
    today_str = date.today().isoformat()

    streak_updated = False
    if correct:
        # Only count once per day for streak purposes
        if getattr(current, "last_challenge_date", None) != today_str:
            record_login(current)
            current.last_challenge_date = today_str
            db.commit()
            db.refresh(current)
            streak_updated = True

    consistency = _compute_consistency(current.login_history or [])
    return {
        "correct": correct,
        "explanation": challenge["explanation"],
        "correct_answer": challenge["choices"][challenge["answer"]],
        "streak_updated": streak_updated,
        "current_streak": current.current_streak or 0,
        "consistency_score": consistency,
    }