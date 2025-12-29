import os
print("✅ Python is working!")
print(f"✅ TOKEN exists: {'TOKEN' in os.environ}")
if 'TOKEN' in os.environ:
    print(f"✅ Token length: {len(os.environ['TOKEN'])}")
    print(f"✅ Token starts with: {os.environ['TOKEN'][:10]}...")
