import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from tests.test_carbon_integration import main

if __name__ == "__main__":
    print("🚀 Starting Carbon Service Integration Tests...\n")
    asyncio.run(main())
