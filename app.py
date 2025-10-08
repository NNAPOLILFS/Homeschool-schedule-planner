# -------------------------
# --- Optimized Scheduling ---
# -------------------------
def schedule_planner(subjects, fixed, kids, days_of_week, start_time, end_time, time_increment):
    """
    subjects: dict per kid
    fixed: dict per kid
    """
    schedule = {day: {kid: [] for kid in kids} for day in days_of_week}
    unscheduled_subjects = []

    # --- Step 1: Place fixed commitments ---
    for kid in kids:
        for fc in fixed[kid]:
            day = fc["day"]
            start = fc["start"]
            end_fc = start + timedelta(minutes=fc["length"])
            schedule[day][kid].append((start, end_fc, fc["name"], "fixed", "⏰"))

    # Helper to find free slots per kid per day
    def get_free_slots(blocks, start_time, end_time, length, increment):
        slots = []
        current = start_time
        while current + timedelta(minutes=length) <= end_time:
            conflict = False
            for b in blocks:
                if not (current + timedelta(minutes=length) <= b[0] or current >= b[1]):
                    conflict = True
                    break
            if not conflict:
                slots.append(current)
            current += timedelta(minutes=increment)
        return slots

    # --- Step 2: Place subjects ---
    for kid in kids:
        for subj in subjects[kid]:
            name = subj["name"]
            length = subj["length"]
            sessions_needed = subj["sessions"]
            shared = subj["shared"]
            icon = subj["icon"]

            if shared:
                # Shared: find slots where ALL kids are free
                placed_count = 0
                for day in days_of_week:
                    # Compute free slots for each kid
                    free_per_kid = []
                    for k in kids:
                        free = get_free_slots(schedule[day][k], start_time, end_time, length, time_increment)
                        free_per_kid.append(set(free))
                    # Intersection = slots where all kids are free
                    common_slots = sorted(list(set.intersection(*free_per_kid)))
                    while common_slots and placed_count < sessions_needed:
                        slot = common_slots.pop(0)
                        for k in kids:
                            schedule[day][k].append((slot, slot + timedelta(minutes=length), name, "shared", icon))
                        placed_count += 1
                    if placed_count >= sessions_needed:
                        break
                if placed_count < sessions_needed:
                    unscheduled_subjects.append(f"{name} (shared)")

            else:
                # Individual subject
                placed_count = 0
                for day in days_of_week:
                    free_slots = get_free_slots(schedule[day][kid], start_time, end_time, length, time_increment)
                    while free_slots and placed_count < sessions_needed:
                        slot = free_slots.pop(0)
                        schedule[day][kid].append((slot, slot + timedelta(minutes=length), name, "individual", icon))
                        placed_count += 1
                    if placed_count >= sessions_needed:
                        break
                if placed_count < sessions_needed:
                    unscheduled_subjects.append(f"{name} ({kid})")

    # Sort each day's schedule by start time
    for day in days_of_week:
        for kid in kids:
            schedule[day][kid].sort(key=lambda x: x[0])

    return schedule, unscheduled_subjects
