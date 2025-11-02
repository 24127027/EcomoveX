"""
Quick test script to verify the integration layer is working correctly.
Run this to check if all imports and basic functionality work.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test that all integration modules can be imported."""
    print("Testing imports...")
    
    try:
        from integration.map_api import GoogleMapsClient, get_maps_client
        print("  ✅ map_api imports successful")
    except Exception as e:
        print(f"  ❌ map_api import failed: {e}")
        return False
    
    try:
        from integration.chatbot_api import OpenAIClient, GeminiClient, ChatbotHelper
        print("  ✅ chatbot_api imports successful")
    except Exception as e:
        print(f"  ❌ chatbot_api import failed: {e}")
        return False
    
    try:
        from integration.carbon_api import CarbonInterfaceClient, CustomCarbonCalculator
        print("  ✅ carbon_api imports successful")
    except Exception as e:
        print(f"  ❌ carbon_api import failed: {e}")
        return False
    
    return True


def test_config():
    """Test that configuration is loaded."""
    print("\nTesting configuration...")
    
    try:
        from utils.config import settings
        
        # Check if API key fields exist (they might be empty)
        assert hasattr(settings, 'GOOGLE_MAPS_API_KEY')
        assert hasattr(settings, 'OPENAI_API_KEY')
        assert hasattr(settings, 'GEMINI_API_KEY')
        assert hasattr(settings, 'CARBON_INTERFACE_API_KEY')
        assert hasattr(settings, 'AI_PROVIDER')
        
        print("  ✅ All configuration fields present")
        
        # Show which keys are configured
        keys_status = {
            "GOOGLE_MAPS_API_KEY": "✅ Set" if settings.GOOGLE_MAPS_API_KEY else "⚠️  Empty",
            "OPENAI_API_KEY": "✅ Set" if settings.OPENAI_API_KEY else "⚠️  Empty",
            "GEMINI_API_KEY": "✅ Set" if settings.GEMINI_API_KEY else "⚠️  Empty",
            "CARBON_INTERFACE_API_KEY": "✅ Set" if settings.CARBON_INTERFACE_API_KEY else "⚠️  Empty",
        }
        
        print("\n  API Keys Status:")
        for key, status in keys_status.items():
            print(f"    {key}: {status}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False


def test_custom_carbon_calculator():
    """Test the custom carbon calculator (no API key needed)."""
    print("\nTesting Custom Carbon Calculator...")
    
    try:
        from integration.carbon_api import CustomCarbonCalculator
        
        calculator = CustomCarbonCalculator()
        
        # Test basic calculation
        emissions = calculator.calculate_transport_emissions(
            transport_mode="train",
            distance_km=100,
            passengers=1
        )
        
        assert isinstance(emissions, float)
        assert emissions > 0
        print(f"  ✅ Train emissions (100 km): {emissions} kg CO2")
        
        # Test comparison
        comparison = calculator.compare_transport_options(
            distance_km=100,
            transport_modes=["train", "car_electric", "flight_economy"]
        )
        
        assert len(comparison) == 3
        assert "train" in comparison
        print(f"  ✅ Transport comparison: {comparison}")
        
        # Test eco score
        score = calculator.get_eco_score(emissions)
        assert "score" in score
        assert "rating" in score
        print(f"  ✅ Eco score: {score['score']}/100 ({score['rating']})")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Custom carbon calculator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_client_initialization():
    """Test that clients can be initialized (even without API keys)."""
    print("\nTesting client initialization...")
    
    try:
        from integration.map_api import GoogleMapsClient
        from integration.chatbot_api import OpenAIClient
        from integration.carbon_api import CarbonInterfaceClient
        
        # Just test initialization, not actual API calls
        maps_client = GoogleMapsClient()
        print("  ✅ GoogleMapsClient initialized")
        await maps_client.close()
        
        openai_client = OpenAIClient()
        print("  ✅ OpenAIClient initialized")
        await openai_client.close()
        
        carbon_client = CarbonInterfaceClient()
        print("  ✅ CarbonInterfaceClient initialized")
        await carbon_client.close()
        
        return True
        
    except Exception as e:
        print(f"  ❌ Client initialization failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("🧪 EcomoveX Integration Layer Test Suite")
    print("=" * 70)
    
    results = []
    
    # Test 1: Imports
    results.append(("Imports", test_imports()))
    
    # Test 2: Configuration
    results.append(("Configuration", test_config()))
    
    # Test 3: Custom Carbon Calculator (no API key needed)
    results.append(("Custom Carbon Calculator", test_custom_carbon_calculator()))
    
    # Test 4: Client Initialization
    results.append(("Client Initialization", asyncio.run(test_client_initialization())))
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 All tests passed! Integration layer is ready to use.")
        print("\n  Next steps:")
        print("    1. Add your API keys to backend/local.env")
        print("    2. Check integration/examples.py for usage examples")
        print("    3. Integrate into your service layer")
    else:
        print("\n  ⚠️  Some tests failed. Please check the errors above.")
    
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
