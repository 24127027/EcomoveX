"""
Quick fix script to remove Destination model usage from Pydantic schemas
"""

import re
from pathlib import Path

def fix_schema_file(filepath: Path):
    """Fix schema file by removing Destination import and replacing with Dict"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        content = re.sub(
            r'from models\.destination import Destination\n',
            '',
            content
        )
        
        content = re.sub(
            r': Destination = Field',
            r': Dict[str, float] = Field',
            content
        )
        
        content = re.sub(
            r': Optional\[Destination\] = Field',
            r': Optional[Dict[str, float]] = Field',
            content
        )
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Fixed {filepath.name}")
            return True
        else:
            print(f"  Skipped {filepath.name}")
            return False
            
    except Exception as e:
        print(f"✗ Error fixing {filepath}: {e}")
        return False

def main():
    schema_dir = Path(__file__).parent / "schemas"
    
    fixed = 0
    for schema_file in schema_dir.glob("*.py"):
        if fix_schema_file(schema_file):
            fixed += 1
    
    print(f"\nFixed {fixed} schema files")

if __name__ == "__main__":
    main()
