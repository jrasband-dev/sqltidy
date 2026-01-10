sql = open("SQL Files/Cleaned/old.sql").read()
from sqltidy.rules.general import AliasStyleABCRule

rule = AliasStyleABCRule()
scopes = rule._extract_cte_scopes(sql)
print(f"Found {len(scopes)} scopes")
for i, (content, start, end) in enumerate(scopes):
    print(f"\nScope {i}: starts at {start}, ends at {end}")
    print(f"Content preview: {content[:150]}...")
    print(f"Content ends with: ...{content[-50:]}")
