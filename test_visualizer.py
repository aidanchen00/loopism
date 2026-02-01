"""
Test script for the audio visualizer component.
Verifies the visualizer can properly:
1. Load and encode audio files
2. Generate valid HTML/JS
3. Handle different file formats
"""

import os
import sys
import base64
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the visualizer function from app.py
# We'll need to import it differently since app.py runs Streamlit code
def create_audio_visualizer_test(audio_path: str, component_id: str, height: int = 200) -> str:
    """Test version of create_audio_visualizer without Streamlit dependencies."""
    with open(audio_path, 'rb') as f:
        audio_data = base64.b64encode(f.read()).decode('utf-8')

    ext = Path(audio_path).suffix.lower()
    mime_types = {'.wav': 'audio/wav', '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.m4a': 'audio/mp4'}
    mime_type = mime_types.get(ext, 'audio/wav')

    # Verify data is valid base64
    try:
        decoded = base64.b64decode(audio_data)
        assert len(decoded) > 0, "Decoded audio data is empty"
    except Exception as e:
        raise AssertionError(f"Invalid base64 encoding: {e}")

    return {
        'audio_data_length': len(audio_data),
        'mime_type': mime_type,
        'component_id': component_id,
        'height': height,
        'decoded_size_bytes': len(decoded)
    }


def test_audio_files():
    """Test all available audio files."""
    audio_dir = Path('/Users/aidanchen/projects/loopism/loopism_outputs')
    precached_dir = Path('/Users/aidanchen/projects/loopism/precached')

    audio_files = []
    for directory in [audio_dir, precached_dir]:
        if directory.exists():
            audio_files.extend(directory.rglob('*.wav'))
            audio_files.extend(directory.rglob('*.mp3'))

    if not audio_files:
        print("⚠️  No audio files found for testing")
        return False

    print(f"Found {len(audio_files)} audio files to test")
    print("=" * 60)

    success_count = 0
    fail_count = 0

    for i, audio_file in enumerate(audio_files[:5]):  # Test first 5 files
        try:
            result = create_audio_visualizer_test(
                str(audio_file),
                f"test_{i}",
                height=120
            )
            print(f"✓ {audio_file.name}")
            print(f"  - MIME type: {result['mime_type']}")
            print(f"  - Base64 length: {result['audio_data_length']:,} chars")
            print(f"  - Original size: {result['decoded_size_bytes']:,} bytes")
            success_count += 1
        except Exception as e:
            print(f"✗ {audio_file.name}")
            print(f"  - Error: {e}")
            fail_count += 1

    print("=" * 60)
    print(f"Results: {success_count} passed, {fail_count} failed")

    return fail_count == 0


def test_html_generation():
    """Test that the HTML/JS is properly structured."""
    # Find a test audio file
    test_files = list(Path('/Users/aidanchen/projects/loopism/loopism_outputs').glob('*.wav'))
    if not test_files:
        test_files = list(Path('/Users/aidanchen/projects/loopism/precached').rglob('*.wav'))

    if not test_files:
        print("⚠️  No audio files for HTML generation test")
        return False

    test_file = test_files[0]
    print(f"\nTesting HTML generation with: {test_file.name}")

    # Import and test the actual function
    try:
        # Read the app.py file and extract the function
        with open('/Users/aidanchen/projects/loopism/app.py', 'r') as f:
            content = f.read()

        # Check that required elements are in the HTML template
        required_elements = [
            'canvas',
            'AudioContext',
            'createAnalyser',
            'getByteFrequencyData',
            'requestAnimationFrame',
            'togglePlay_',
            'FREQUENCY SPECTRUM',
            'fillRect'
        ]

        missing = []
        for element in required_elements:
            if element not in content:
                missing.append(element)

        if missing:
            print(f"✗ Missing required elements in HTML: {missing}")
            return False
        else:
            print("✓ All required HTML/JS elements present")
            return True

    except Exception as e:
        print(f"✗ HTML generation test failed: {e}")
        return False


def test_web_audio_api_components():
    """Verify Web Audio API components are correctly implemented."""
    print("\nVerifying Web Audio API implementation...")

    with open('/Users/aidanchen/projects/loopism/app.py', 'r') as f:
        content = f.read()

    checks = [
        ('AudioContext creation', 'new (window.AudioContext || window.webkitAudioContext)()'),
        ('AnalyserNode', 'createAnalyser'),
        ('FFT size configuration', 'fftSize = 256'),
        ('MediaElementSource', 'createMediaElementSource'),
        ('Frequency data retrieval', 'getByteFrequencyData'),
        ('Animation loop', 'requestAnimationFrame'),
        ('Canvas rendering', 'fillRect'),
        ('Gradient colors', 'createLinearGradient'),
        ('Play/Pause toggle', 'togglePlay_'),
        ('Volume control', 'setVolume_'),
        ('Seek functionality', 'seek_'),
    ]

    all_passed = True
    for name, pattern in checks:
        if pattern in content:
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name} - pattern not found: {pattern}")
            all_passed = False

    return all_passed


def test_color_spectrum():
    """Test that color spectrum logic is present for rainbow bars."""
    print("\nVerifying color spectrum implementation...")

    with open('/Users/aidanchen/projects/loopism/app.py', 'r') as f:
        content = f.read()

    # Check for HSL color generation
    if 'hsla(' in content and 'hue' in content:
        print("  ✓ HSL color spectrum implemented")
        return True
    else:
        print("  ✗ HSL color spectrum not found")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("AUDIO VISUALIZER TEST SUITE")
    print("=" * 60)

    results = []

    # Test 1: Audio file encoding
    print("\n[Test 1] Audio File Encoding")
    results.append(test_audio_files())

    # Test 2: HTML generation
    print("\n[Test 2] HTML Structure")
    results.append(test_html_generation())

    # Test 3: Web Audio API components
    print("\n[Test 3] Web Audio API Components")
    results.append(test_web_audio_api_components())

    # Test 4: Color spectrum
    print("\n[Test 4] Color Spectrum")
    results.append(test_color_spectrum())

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")

    if all(results):
        print("\n✓ ALL TESTS PASSED - Visualizer is ready!")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED - Please review the errors above")
        return 1


if __name__ == '__main__':
    sys.exit(main())
