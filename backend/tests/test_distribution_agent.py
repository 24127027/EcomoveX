"""
Test script for DestinationDistributionAgent
Tests the agent's ability to:
1. Expand destinations based on daily needs (restaurants, accommodation)
2. Distribute destinations across date range
3. Assign appropriate time slots

Usage:
    python test_distribution_agent.py
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.agents.sub_agents.destination_distribution_agent import DestinationDistributionAgent
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from database.db import Base


async def create_test_db_session():
    """Create a test database session (using in-memory SQLite for testing)"""
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


def print_plan_summary(plan_data: Dict[str, Any], label: str = "Plan"):
    """Print a summary of plan data"""
    print(f"\n📋 {label}:")
    print(f"   Place: {plan_data.get('place_name')}")
    print(f"   Dates: {plan_data.get('start_date')} → {plan_data.get('end_date')}")
    
    start = datetime.strptime(str(plan_data.get('start_date')), "%Y-%m-%d").date()
    end = datetime.strptime(str(plan_data.get('end_date')), "%Y-%m-%d").date()
    days = (end - start).days + 1
    print(f"   Duration: {days} day(s)")
    print(f"   Budget: {plan_data.get('budget_limit', 0):,.0f} VND")
    
    destinations = plan_data.get('destinations', [])
    print(f"\n   📍 Destinations ({len(destinations)}):")
    
    # Count by type
    type_counts = {}
    repeated_count = 0
    for dest in destinations:
        dest_type = dest.get('destination_type') or dest.get('type', 'unknown')
        type_counts[dest_type] = type_counts.get(dest_type, 0) + 1
        if dest.get('is_repeated'):
            repeated_count += 1
    
    for dest_type, count in sorted(type_counts.items()):
        print(f"      • {dest_type}: {count}")
    
    if repeated_count > 0:
        print(f"      • (Repeated: {repeated_count})")


def print_destination_details(destinations: list, max_show: int = 10):
    """Print detailed destination list"""
    print(f"\n   📍 Destination Details:")
    
    for idx, dest in enumerate(destinations[:max_show], 1):
        dest_id = dest.get('destination_id', 'N/A')[:20]
        dest_type = dest.get('destination_type') or dest.get('type', 'unknown')
        note = dest.get('note', 'No note')
        visit_date = dest.get('visit_date', 'Not set')
        time_slot = dest.get('time_slot', 'Not set')
        order = dest.get('order_in_day', 'Not set')
        is_repeated = dest.get('is_repeated', False)
        repeat_idx = dest.get('repeat_index', '')
        
        repeat_marker = f" [REPEATED #{repeat_idx}]" if is_repeated else ""
        
        print(f"      {idx}. {note}")
        print(f"         Type: {dest_type} | Date: {visit_date} | Slot: {time_slot} | Order: {order}{repeat_marker}")
    
    if len(destinations) > max_show:
        print(f"      ... and {len(destinations) - max_show} more")


def print_distribution_by_day(destinations: list):
    """Print destinations grouped by day"""
    print(f"\n   📅 Distribution by Day:")
    
    by_day = {}
    for dest in destinations:
        visit_date = dest.get('visit_date', 'Unscheduled')
        if visit_date not in by_day:
            by_day[visit_date] = []
        by_day[visit_date].append(dest)
    
    for day, day_dests in sorted(by_day.items()):
        print(f"\n      {day} ({len(day_dests)} destinations):")
        
        # Group by time slot
        by_slot = {'morning': [], 'afternoon': [], 'evening': [], 'unscheduled': []}
        for dest in day_dests:
            slot = dest.get('time_slot', 'unscheduled')
            slot_key = slot if slot in by_slot else 'unscheduled'
            by_slot[slot_key].append(dest)
        
        for slot in ['morning', 'afternoon', 'evening', 'unscheduled']:
            slot_dests = by_slot[slot]
            if slot_dests:
                print(f"         {slot.upper()}:")
                for dest in slot_dests:
                    note = dest.get('note', 'Unknown')
                    dest_type = dest.get('destination_type') or dest.get('type', '?')
                    is_repeated = " (repeated)" if dest.get('is_repeated') else ""
                    print(f"            - {note} [{dest_type}]{is_repeated}")


async def test_single_case(agent: DestinationDistributionAgent, test_case: Dict[str, Any]):
    """Test a single test case"""
    case_name = test_case.get('case_name', 'Unnamed')
    description = test_case.get('description', '')
    plan_data = test_case.get('plan', {})
    expected = test_case.get('expected_behavior', '')
    
    print_separator(f"TEST: {case_name}")
    print(f"📝 Description: {description}")
    print(f"✅ Expected: {expected}")
    
    print_plan_summary(plan_data, "Input Plan")
    
    # Run the agent
    try:
        result = await agent.process(plan_data, action="distribute")
        
        success = result.get('success', False)
        message = result.get('message', 'No message')
        modifications = result.get('modifications', [])
        distributed = result.get('distributed_destinations', [])
        summary = result.get('distribution_summary', {})
        
        print(f"\n🤖 Agent Result:")
        print(f"   Success: {'✅' if success else '❌'} {success}")
        print(f"   Message: {message}")
        
        if summary:
            print(f"\n   📊 Distribution Summary:")
            print(f"      Total destinations: {summary.get('total_destinations', 0)}")
            print(f"      Total days: {summary.get('total_days', 0)}")
            print(f"      Days with destinations: {summary.get('days_with_destinations', 0)}")
            print(f"      Avg per day: {summary.get('avg_per_day', 0):.1f}")
        
        if modifications:
            print(f"\n   🔄 Modifications ({len(modifications)}):")
            for mod in modifications[:5]:
                source = mod.get('source', 'unknown')
                field = mod.get('field', 'unknown')
                print(f"      • {source}: {field} modified")
            if len(modifications) > 5:
                print(f"      ... and {len(modifications) - 5} more")
        
        if distributed:
            print_plan_summary(
                {**plan_data, 'destinations': distributed},
                "Output Plan (After Distribution)"
            )
            print_distribution_by_day(distributed)
        
        print(f"\n✅ Test completed successfully")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all test cases from JSON file"""
    print_separator("🧪 DESTINATION DISTRIBUTION AGENT TEST SUITE")
    
    # Load test data
    test_file = Path(__file__).parent / "test_data" / "plan_test_cases.json"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return
    
    with open(test_file, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    test_cases = test_data.get('test_cases', [])
    print(f"📦 Loaded {len(test_cases)} test case(s)\n")
    
    # Create agent
    db = await create_test_db_session()
    agent = DestinationDistributionAgent(db)
    
    # Run tests
    results = []
    for idx, test_case in enumerate(test_cases, 1):
        print(f"\n{'#'*80}")
        print(f"# Test {idx}/{len(test_cases)}")
        print(f"{'#'*80}")
        
        success = await test_single_case(agent, test_case)
        results.append({
            'case': test_case.get('case_name', f'Test {idx}'),
            'success': success
        })
        
        # Pause between tests
        await asyncio.sleep(0.1)
    
    # Print summary
    print_separator("📊 TEST SUMMARY")
    
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
    
    await db.close()


async def run_single_test_by_name(test_name: str):
    """Run a specific test by name"""
    # Load test data
    test_file = Path(__file__).parent / "test_data" / "plan_test_cases.json"
    
    with open(test_file, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    test_cases = test_data.get('test_cases', [])
    
    # Find test
    test_case = None
    for tc in test_cases:
        if test_name.lower() in tc.get('case_name', '').lower():
            test_case = tc
            break
    
    if not test_case:
        print(f"❌ Test case '{test_name}' not found")
        print(f"\nAvailable tests:")
        for tc in test_cases:
            print(f"   - {tc.get('case_name')}")
        return
    
    # Run test
    db = await create_test_db_session()
    agent = DestinationDistributionAgent(db)
    
    await test_single_case(agent, test_case)
    
    await db.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_name = " ".join(sys.argv[1:])
        asyncio.run(run_single_test_by_name(test_name))
    else:
        # Run all tests
        asyncio.run(run_all_tests())
