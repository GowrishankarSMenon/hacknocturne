"""Quick test of the tree-based filesystem and command handler"""
from state_manager.file_system import VirtualFileSystem
from agents.command_handler import CommandHandler

fs = VirtualFileSystem()
ch = CommandHandler(fs)

tests = [
    ("pwd", "/home/user"),
    ("ls", None),  # Just check it doesn't crash
    ("cd Desktop", ""),
    ("pwd", "/home/user/Desktop"),
    ("ls", None),
    ("cd ..", ""),
    ("pwd", "/home/user"),
    ("mkdir testdir", ""),
    ("cd testdir", ""),
    ("pwd", "/home/user/testdir"),
    ("touch hello.txt", ""),
    ("ls", "hello.txt"),
    ("cat hello.txt", ""),
    ("cd ..", ""),
    ("rm -r testdir", ""),
    ("whoami", "user"),
    ("hostname", "ghostnet"),
    ("uname -a", None),
    ("id", None),
    ("ps", None),
    ("ifconfig", None),
    ("df", None),
    ("free -h", None),
]

passed = 0
failed = 0

for cmd, expected in tests:
    result = ch.execute(cmd)
    if expected is not None:
        if result.strip() == expected.strip():
            print(f"  ✓ {cmd} → {repr(result[:60])}")
            passed += 1
        else:
            print(f"  ✗ {cmd} → got {repr(result[:80])}, expected {repr(expected)}")
            failed += 1
    else:
        if isinstance(result, str):
            print(f"  ✓ {cmd} → ({len(result)} chars)")
            passed += 1
        else:
            print(f"  ✗ {cmd} → unexpected result type")
            failed += 1

print(f"\n{'='*40}")
print(f"Results: {passed} passed, {failed} failed")
if failed == 0:
    print("✅ All filesystem tests passed!")
else:
    print("⚠️ Some tests failed")
