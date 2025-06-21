def is_booking_valid(data):
    return True  # สำหรับทดสอบไปก่อน

def save_booking(data):
    print(f"Saved booking: {data}")
    return True  # จำลองว่าบันทึกได้สำเร็จ

def save_booking(data):
    file = "bookings.json"
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = []

    existing.append(data)
    with open(file, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
