"""
Integration test for complete PlannerAgent flow
Tests the full pipeline: expansion → distribution → validation

Usage:
    python test_planner_agent_integration.py
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.agents.planner_agent import PlannerAgent
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from database.db import Base


async def create_test_db_session():
    """Create a test database session"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return async_session()


def print_separator(title: str = ""):
    """Print a visual separator"""
    if title:
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}\n")
    else:
        print(f"\n{'-'*80}\n")


async def test_planner_agent(test_case: Dict[str, Any]):
    """Test PlannerAgent with a test case"""
    case_name = test_case.get('case_name', 'Unnamed')
    description = test_case.get('description', '')
    plan_data = test_case.get('plan', {})
    expected = test_case.get('expected_behavior', '')
    
    print_separator(f"TEST: {case_name}")
    print(f"📝 Description: {description}")
    print(f"✅ Expected: {expected}\n")
    
    # Input summary
    destinations = plan_data.get('destinations', [])
    print(f"📥 INPUT:")
    print(f"   Plan: {plan_data.get('place_name')}")
    print(f"   Dates: {plan_data.get('start_date')} → {plan_data.get('end_date')}")
    print(f"   Destinations: {len(destinations)}")
    
    # Count by type
    type_counts = {}
    for dest in destinations:
        dest_type = dest.get('destination_type') or dest.get('type', 'unknown')
        type_counts[dest_type] = type_counts.get(dest_type, 0) + 1
    
    for dest_type, count in sorted(type_counts.items()):
        print(f"      • {dest_type}: {count}")
    
    # Create agent and run
    db = await create_test_db_session()
    agent = PlannerAgent(db)
    
    try:
        result = await agent._run_sub_agents(plan_data, action="optimize")
        
        warnings = result.get('warnings', [])
        modifications = result.get('modifications', [])
        distributed_plan = result.get('distributed_plan', {})
        
        print(f"\n📤 OUTPUT:")
        
        # Show warnings
        if warnings:
            print(f"\n   ⚠️  Warnings ({len(warnings)}):")
            for warning in warnings:
                agent_name = warning.get('agent', 'unknown')
                message = warning.get('message', 'No message')
                print(f"      • [{agent_name}] {message}")
        else:
            print(f"\n   ✅ No warnings")
        
        # Show modifications
        if modifications:
            print(f"\n   🔄 Modifications ({len(modifications)}):")
            
            # Group by source
            by_source = {}
            for mod in modifications:
                source = mod.get('source', 'unknown')
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append(mod)
            
            for source, mods in by_source.items():
                print(f"      [{source}] {len(mods)} modification(s)")
                for mod in mods[:3]:
                    field = mod.get('field', '?')
                    print(f"         - {field}: {mod.get('suggestion', 'modified')}")
                if len(mods) > 3:
                    print(f"         ... and {len(mods) - 3} more")
        else:
            print(f"\n   ✅ No modifications needed")
        
        # Show distributed plan
        if distributed_plan:
            distributed_destinations = distributed_plan.get('destinations', [])
            print(f"\n   📋 Distributed Plan:")
            print(f"      Total destinations: {len(distributed_destinations)}")
            
            # Count by type (including repeated)
            type_counts_out = {}
            repeated_count = 0
            for dest in distributed_destinations:
                dest_type = dest.get('destination_type') or dest.get('type', 'unknown')
                type_counts_out[dest_type] = type_counts_out.get(dest_type, 0) + 1
                if dest.get('is_repeated'):
                    repeated_count += 1
            
            print(f"\n      By type:")
            for dest_type, count in sorted(type_counts_out.items()):
                print(f"         • {dest_type}: {count}")
            
            if repeated_count > 0:
                print(f"      Repeated destinations: {repeated_count}")
            
            # Distribution by day
            by_day = {}
            for dest in distributed_destinations:
                day = dest.get('visit_date', 'Unscheduled')
                if day not in by_day:
                    by_day[day] = {'morning': 0, 'afternoon': 0, 'evening': 0, 'unscheduled': 0}
                
                slot = dest.get('time_slot', 'unscheduled')
                if slot in by_day[day]:
                    by_day[day][slot] += 1
                else:
                    by_day[day]['unscheduled'] += 1
            
            print(f"\n      By day:")
            for day, slots in sorted(by_day.items()):
                total_day = sum(slots.values())
                print(f"         {day} ({total_day} dest):")
                for slot, count in slots.items():
                    if count > 0:
                        print(f"            {slot}: {count}")
        
        print(f"\n✅ Test completed successfully")
        await db.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        await db.close()
        return False


async def run_all_integration_tests():
    """Run all integration tests"""
    print_separator("🧪 PLANNER AGENT INTEGRATION TEST SUITE")
    
    # Load test data
    test_file = Path(__file__).parent / "test_data" / "plan_test_cases.json"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return
    
    with open(test_file, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    test_cases = test_data.get('test_cases', [])
    print(f"📦 Loaded {len(test_cases)} test case(s)\n")
    
    # Run tests
    results = []
    for idx, test_case in enumerate(test_cases, 1):
        print(f"\n{'#'*80}")
        print(f"# Integration Test {idx}/{len(test_cases)}")
        print(f"{'#'*80}")
        
        success = await test_planner_agent(test_case)
        results.append({
            'case': test_case.get('case_name', f'Test {idx}'),
            'success': success
        })
        
        await asyncio.sleep(0.1)
    
    # Print summary
    print_separator("📊 INTEGRATION TEST SUMMARY")
    
    total = len(results)
    passed = sum(1 for r in results if r['success'])
    failed = total - passed
    
    print(f"Total tests: {total}")
    print(f"Passed: ✅ {passed}")
    print(f"Failed: ❌ {failed}")
    print(f"Success rate: {(passed/total*100) if total > 0 else 0:.1f}%")
    
    print(f"\n📋 Detailed Results:")
    for result in results:
        status = '✅' if result['success'] else '❌'
        print(f"   {status} {result['case']}")


if __name__ == "__main__":
    asyncio.run(run_all_integration_tests())
