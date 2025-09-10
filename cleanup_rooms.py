#!/usr/bin/env python3
"""
Clean up duplicate exam rooms in the database
"""

import sqlite3

def cleanup_rooms():
    conn = sqlite3.connect('enhanced_students.db')
    
    try:
        # Get current rooms
        print("Current rooms before cleanup:")
        rooms = conn.execute('SELECT id, room_number, building FROM exam_rooms ORDER BY room_number, id').fetchall()
        for room in rooms:
            print(f"  ID {room[0]}: {room[1]} - {room[2]}")
        
        # Remove all rooms except the 4 specified ones
        conn.execute('DELETE FROM exam_rooms WHERE room_number NOT IN ("SF26", "SF20", "SF8", "FF19")')
        print(f"\nRemoved rooms not in allowed list")
        
        # Remove duplicates for each allowed room
        rooms_to_keep = ['SF26', 'SF20', 'SF8', 'FF19']
        for room_num in rooms_to_keep:
            # Get all IDs for this room number
            room_ids = conn.execute('SELECT id FROM exam_rooms WHERE room_number = ? ORDER BY id', (room_num,)).fetchall()
            
            if len(room_ids) > 1:
                # Keep the first one, delete the rest
                first_id = room_ids[0][0]
                ids_to_delete = [str(row[0]) for row in room_ids[1:]]
                print(f"For {room_num}: keeping ID {first_id}, deleting IDs: {', '.join(ids_to_delete)}")
                
                for room_id in ids_to_delete:
                    conn.execute('DELETE FROM exam_rooms WHERE id = ?', (room_id,))
        
        conn.commit()
        
        # Verify the cleanup
        print("\nFinal rooms after cleanup:")
        final_rooms = conn.execute('SELECT id, room_number, building, capacity FROM exam_rooms ORDER BY room_number').fetchall()
        print(f"Total rooms: {len(final_rooms)}")
        for room in final_rooms:
            print(f"  ID {room[0]}: {room[1]} - {room[2]} (Capacity: {room[3]})")
            
        return len(final_rooms) == 4
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = cleanup_rooms()
    if success:
        print("\n✅ Room cleanup completed successfully!")
    else:
        print("\n❌ Room cleanup failed!")
