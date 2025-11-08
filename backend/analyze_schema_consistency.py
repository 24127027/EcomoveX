"""
Script to analyze schema consistency issues
"""
import os
import re
from pathlib import Path

def analyze_schemas():
    """Analyze all schema files for consistency issues"""
    
    print("=" * 80)
    print("SCHEMA CONSISTENCY ANALYSIS")
    print("=" * 80)
    
    issues = []
    
    # Check authentication_schema.py
    auth_path = Path("c:/Users/mduy/source/repos/EcomoveX/backend/schemas/authentication_schema.py")
    if auth_path.exists():
        content = auth_path.read_text(encoding='utf-8')
        if content.count('token_type: str = "bearer"') > 1:
            issues.append({
                "file": "authentication_schema.py",
                "type": "CRITICAL",
                "issue": "Duplicate field 'token_type' in AuthenticationResponse",
                "line": "Lines 31-32"
            })
    
    # Check for inconsistent naming patterns
    schema_files = list(Path("c:/Users/mduy/source/repos/EcomoveX/backend/schemas").glob("*.py"))
    
    naming_patterns = {
        "snake_case_fields": 0,
        "camelCase_fields": 0,
        "model_config": 0,
        "Config": 0,
    }
    
    for file_path in schema_files:
        if file_path.name == "__init__.py":
            continue
            
        content = file_path.read_text(encoding='utf-8')
        
        # Check for model_config vs Config
        if "model_config = ConfigDict" in content:
            naming_patterns["model_config"] += 1
        if "class Config:" in content:
            naming_patterns["Config"] += 1
    
    # Print issues
    if issues:
        print("\nCRITICAL ISSUES FOUND:")
        print("-" * 80)
        for issue in issues:
            print(f"\nFile: {issue['file']}")
            print(f"Type: {issue['type']}")
            print(f"Issue: {issue['issue']}")
            print(f"Location: {issue['line']}")
    
    # Print naming patterns
    print("\n" + "=" * 80)
    print("NAMING PATTERN ANALYSIS")
    print("=" * 80)
    print(f"\nPydantic V2 style (model_config = ConfigDict): {naming_patterns['model_config']} files")
    print(f"Pydantic V1 style (class Config): {naming_patterns['Config']} files")
    
    if naming_patterns['model_config'] > 0 and naming_patterns['Config'] > 0:
        print("\n⚠️  WARNING: Mixed Pydantic V1 and V2 config styles detected!")
        print("   Recommendation: Standardize to Pydantic V2 (model_config = ConfigDict)")
    
    # Check carbon_schema.py structure
    print("\n" + "=" * 80)
    print("CARBON SCHEMA SPECIFIC CHECKS")
    print("=" * 80)
    
    carbon_path = Path("c:/Users/mduy/source/repos/EcomoveX/backend/schemas/carbon_schema.py")
    if carbon_path.exists():
        content = carbon_path.read_text(encoding='utf-8')
        
        # Check for incomplete Config classes
        if "class Config:\n        \n" in content or "class Config:\n        " in content:
            print("\n⚠️  WARNING: Empty Config class found in carbon_schema.py")
            print("   Should have json_schema_extra with examples")
    
    # Summary
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print("""
1. Fix duplicate 'token_type' field in authentication_schema.py
2. Standardize Pydantic config style:
   - Use: model_config = ConfigDict(from_attributes=True)
   - Instead of: class Config: orm_mode = True
3. Ensure all Request schemas have json_schema_extra with examples
4. Use consistent field naming: snake_case
5. All Response schemas should have model_config = ConfigDict(from_attributes=True)
    """)
    
    return issues

if __name__ == "__main__":
    analyze_schemas()
