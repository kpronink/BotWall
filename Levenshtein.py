from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from new_bot_wall_post.app.config import w_watermark, b_watermark, akk_for_comment, list_groups, \
    SQLALCHEMY_DATABASE_URI, max_count_post, session_vk, vk_api

from new_bot_wall_post.app.models import Hash, Post, FakeUsers, Groups, Comments


engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True)
Session = sessionmaker(bind=engine)


def distance(a, b):
    """Calculates the Levenshtein distance between a and b."""
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a, b = b, a
        n, m = m, n

    current_row = range(n + 1)  # Keep current and previous row, not entire matrix
    for i in range(1, m + 1):
        previous_row, current_row = current_row, [i] + [0] * n
        for j in range(1, n + 1):
            add, delete, change = previous_row[j] + 1, current_row[j - 1] + 1, previous_row[j - 1]
            if a[j - 1] != b[i - 1]:
                change += 1
            current_row[j] = min(add, delete, change)

    return current_row[n]


session = Session()
hash_ = session.query(Hash).all()
for h in hash_:
    if isinstance(h.hash, str):
        current_row = distance(h.hash, 'ff8100000000ffff')
        if current_row <= 3:
            print(h.hash + ' - ff8100000000ffff ' + str(current_row))