from core.session import Session
s = Session()
for i in ['session_1781013002', 'session_1781013445', 'session_001', 'session_1781014109', 'session_1781013273', 'session_1781016002', 'session_1781013151', 'session_1781014810', 'session_1781013936']:
    s.delete_session(session_id=i)
