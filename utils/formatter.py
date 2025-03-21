def format_sessions_message(sessions):
    # if not sessions:
    #     return "На Вашем счету нет доступных сессий"
    
    def get_access_form(count):
        if count % 10 == 1 and count % 100 != 11:
            return "доступ"
        elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
            return "доступа"
        else:
            return "доступов"
    
    parts = [
        f"{session.count} {get_access_form(session.count)} на {session.length} минут"
        for session in sessions
    ]
    
    return f"На Вашем счету {', '.join(parts)}"