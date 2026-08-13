import asyncio
import sys
from services.transcript.pipeline import TranscriptPipeline

async def main():
    # Test video requested by user
    test_url = "https://www.youtube.com/watch?v=JxgmHe2NyeY"
    
    try:
        # Request English since we don't know the exact languages available 
        result = await TranscriptPipeline.process_video(test_url, requested_language="en")
        
        print("\n--- Final Pipeline Result ---")
        for key, val in result.items():
            if key == 'artifacts':
                print("Artifacts generated:")
                for ext, path in val.items():
                    print(f" - {ext.upper()}: {path}")
            else:
                print(f"{key}: {val}")
                
        print("\nTEST PASSED: Phase 1 Transcript Layer successfully implemented!")
        
    except Exception as e:
        print(f"\nTEST FAILED: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
