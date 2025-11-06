"""
Quick API Endpoints Reference
Auto-generated from router inspection
"""
from main import app

print("=" * 80)
print("📚 ECOMOVEX API - QUICK REFERENCE GUIDE")
print("=" * 80)
print()

routers = {}
for route in app.routes:
    if hasattr(route, 'tags') and hasattr(route, 'methods') and route.tags:
        tag = route.tags[0]
        if tag not in routers:
            routers[tag] = []
        routers[tag].append({
            'method': list(route.methods)[0],
            'path': route.path,
            'name': route.name
        })

# Generate markdown-style output
for tag, routes in sorted(routers.items()):
    if tag in ['Root', 'Health']:
        continue
        
    print(f"\n{'='*80}")
    print(f"## {tag.upper()}")
    print(f"{'='*80}")
    
    for r in sorted(routes, key=lambda x: (x['method'], x['path'])):
        method = r['method']
        path = r['path']
        name = r['name']
        
        # Determine auth requirement
        auth = "🔒" if "me" in path or "my" in name.lower() else "🔓"
        
        print(f"\n{auth} **{method}** `{path}`")
        print(f"   Function: {name}")

print("\n" + "=" * 80)
print("Legend:")
print("  🔒 = Authentication Required (JWT Token)")
print("  🔓 = Public Endpoint (No Auth)")
print("=" * 80)
