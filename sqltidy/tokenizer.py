import re
from typing import List

TOKEN_RE = re.compile(
    r"\s+|\(|\)|,|\.|\*|\[|\]|<=|>=|<>|!=|=|<|>|;|\n|\r|\t|"
    r"'[^']*'|\"[^\"]*\"|\w+|\S"
)

def tokenize(sql: str) -> List[str]:
    tokens = TOKEN_RE.findall(sql)
    cleaned = []
    for t in tokens:
        if t is None:
            continue
        if t.strip() == "":
            continue
        cleaned.append(t)
    return cleaned
