#!/usr/bin/env python3
"""
Dropdown Verification Script
Verifies that only the 4 required rooms (SF26, SF20, SF8, FF19) appear in dropdowns
"""

import sqlite3

def verify_room_dropdowns():
    """Verify room dropdowns contain only required rooms"""
    print("🔍 Verifying Room Dropdowns...")
    
    conn = sqlite3.connect('enhanced_students.db')
    cursor = conn.cursor()
    
    # Get rooms (same query as used in the app)
    rooms = cursor.execute('SELECT * FROM exam_rooms ORDER BY room_number').fetchall()
    
    required_rooms = ['FF19', 'SF20', 'SF26', 'SF8']
    found_rooms = [room[1] for room in rooms]  # room_number is at index 1
    
    print(f"Expected rooms: {required_rooms}")
    print(f"Found rooms: {found_rooms}")
    
    # Check if we have exactly the required rooms
    if set(found_rooms) == set(required_rooms):
        print("✅ PASS: Dropdowns contain exactly the required rooms")
        
        # Show details
        print("\nRoom Details:")
        for room in rooms:
            print(f"  • {room[1]} - {room[2]} (Capacity: {room[3]}, ID: {room[0]})")
        
        return True
    else:
        missing = set(required_rooms) - set(found_rooms)
        extra = set(found_rooms) - set(required_rooms)
        
        if missing:
            print(f"❌ FAIL: Missing rooms: {missing}")
        if extra:
            print(f"❌ FAIL: Extra rooms: {extra}")
        
        return False
    
    conn.close()

def verify_assignments_updated():
    """Verify existing assignments use valid room IDs"""
    print("\n🔧 Verifying Room Assignments...")
    
    conn = sqlite3.connect('enhanced_students.db')
    cursor = conn.cursor()
    
    # Get valid room IDs
    cursor.execute('SELECT id, room_number FROM exam_rooms')
    valid_rooms = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Check index range assignments
    cursor.execute('SELECT id, room_id FROM index_range_assignments')
    assignments = cursor.fetchall()
    
    if not assignments:
        print("ℹ️  No index range assignments found")
        return True
    
    all_valid = True
    for assignment in assignments:
        room_id = assignment[1]
        if room_id in valid_rooms:
            print(f"✅ Assignment {assignment[0]} uses valid room: {valid_rooms[room_id]} (ID: {room_id})")
        else:
            print(f"❌ Assignment {assignment[0]} uses invalid room ID: {room_id}")
            all_valid = False
    
    # Check exam sessions
    cursor.execute('SELECT id, title, room_id FROM exam_sessions WHERE room_id IS NOT NULL')
    sessions = cursor.fetchall()
    
    for session in sessions:
        room_id = session[2]
        if room_id in valid_rooms:
            print(f"✅ Session '{session[1]}' uses valid room: {valid_rooms[room_id]} (ID: {room_id})")
        else:
            print(f"❌ Session '{session[1]}' uses invalid room ID: {room_id}")
            all_valid = False
    
    conn.close()
    return all_valid

def verify_dropdown_functionality():
    """Verify dropdown functionality by simulating backend queries"""
    print("\n📋 Verifying Dropdown Backend Queries...")
    
    conn = sqlite3.connect('enhanced_students.db')
    cursor = conn.cursor()
    
    try:
        # Simulate admin_index_assignments route query
        rooms = cursor.execute('SELECT * FROM exam_rooms ORDER BY room_number').fetchall()
        print(f"✅ admin_index_assignments query: Found {len(rooms)} rooms")
        
        # Simulate exam session creation query  
        rooms2 = cursor.execute('SELECT * FROM exam_rooms ORDER BY room_number').fetchall()
        print(f"✅ exam_sessions query: Found {len(rooms2)} rooms")
        
        # Verify all rooms have required fields
        for room in rooms:
            if len(room) >= 4 and room[1] and room[2]:  # room_number and building exist
                continue
            else:
                print(f"❌ Room {room[0]} missing required fields")
                return False
        
        print("✅ All rooms have required fields for dropdowns")
        return True
        
    except Exception as e:
        print(f"❌ Query error: {e}")
        return False
    finally:
        conn.close()

def main():
    """Run all verification tests"""
    print("🚀 Room Dropdown Verification Suite")
    print("=" * 50)
    
    tests = [
        verify_room_dropdowns,
        verify_assignments_updated, 
        verify_dropdown_functionality
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 VERIFICATION RESULTS")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Room dropdowns now contain only: SF26, SF20, SF8, FF19")
        print("✅ Existing assignments updated to use valid rooms")
        print("✅ Backend queries working correctly")
        print("\n🔗 Affected areas:")
        print("  • Admin → Index Range Assignments (room selection)")
        print("  • Admin → Exam Sessions (room selection)")
        print("  • Any other forms that select exam rooms")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        print("Please check the issues above and re-run verification")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
