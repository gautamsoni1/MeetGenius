def build_participants_with_time(report):

    participants = report.get("participants") or []  # 🔥 FIX NONE CRASH

    result = []

    for p in participants:

        time_data = p.get("time_data")

        if not isinstance(time_data, dict):
            time_data = {}

        join_time = time_data.get("join_time") or 0
        leave_time = time_data.get("leave_time") or 0

        result.append({
            "name": p.get("name", "Unknown"),
            "join_time": join_time,
            "leave_time": leave_time,
            "duration": max(0, leave_time - join_time)
        })

    return result