"""
Create dummy service classes for empty service files
"""

from pathlib import Path

def create_dummy_service(filepath: Path):
    """Create a dummy service class"""
    service_name = filepath.stem.replace('_', ' ').title().replace(' ', '')
    
    content = f'''"""
{service_name} - To be implemented
"""

class {service_name}:
    """Placeholder service class"""
    pass
'''
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Created dummy {service_name}")
        return True
    except Exception as e:
        print(f"✗ Error creating {service_name}: {e}")
        return False

def main():
    services_dir = Path(__file__).parent / "services"
    
    empty_services = []
    for service_file in services_dir.glob("*_service.py"):
        try:
            with open(service_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content or 'class' not in content:
                empty_services.append(service_file)
        except Exception as e:
            print(f"Error checking {service_file}: {e}")
    
    print(f"\nFound {len(empty_services)} empty service files\n")
    
    created = 0
    for service_file in empty_services:
        if create_dummy_service(service_file):
            created += 1
    
    print(f"\nCreated {created} dummy service classes")

if __name__ == "__main__":
    main()
