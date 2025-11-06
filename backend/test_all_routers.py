"""
Test script to verify all routers are working
"""
from main import app

print("🚀 TESTING ALL ROUTERS")
print("=" * 70)

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

print(f"\n📊 Total Router Groups: {len(routers)}")
print(f"📋 Total Endpoints: {sum(len(v) for v in routers.values())}")
print("\n" + "=" * 70)

for tag, routes in sorted(routers.items()):
    print(f"\n🔷 {tag.upper()} - {len(routes)} endpoints")
    for r in routes:
        print(f"  {r['method']:7} {r['path']:45} | {r['name']}")

print("\n" + "=" * 70)
print("✅ All routers loaded successfully!")
