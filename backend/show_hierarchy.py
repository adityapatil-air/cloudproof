from database import execute_query

resources = execute_query('SELECT resource_type, resource_id, parent_resource_id, state FROM resource_state ORDER BY last_updated', fetch=True)

print('=== RESOURCE HIERARCHY ===\n')

parents = [r for r in resources if not r['parent_resource_id']]
for p in parents:
    print(f"{p['resource_type']}: {p['resource_id']} ({p['state']})")
    children = [r for r in resources if r['parent_resource_id'] == p['resource_id']]
    for c in children:
        print(f"  -> {c['resource_type']}: {c['resource_id']} ({c['state']})")
    if children:
        print()
