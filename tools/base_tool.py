from tools.file_reader import FILE_READER_TOOLS,FILE_READER_HANDLERS
from tools.code_viewer import CODE_VIEWER_TOOLS,CODE_VIEWER_HANDLERS
from mcp_tools.mcp_tool import BROWSER_TOOLS,BROWSER_HANDLERS
from tools.skills import LOAD_SKILL_TOOL,handle_load_skill


react_tool=FILE_READER_TOOLS+CODE_VIEWER_TOOLS+BROWSER_TOOLS+[LOAD_SKILL_TOOL]
react_handlers={
    **FILE_READER_HANDLERS,
    **CODE_VIEWER_HANDLERS,
    **BROWSER_HANDLERS,
    "load_skill": handle_load_skill,
}

reflect_tool=[]
reflect_handlers={
}

plan_tool=[]
plan_handlers={}
executor_tool=FILE_READER_TOOLS+CODE_VIEWER_TOOLS
executor_handlers={
    **FILE_READER_HANDLERS,
    **CODE_VIEWER_HANDLERS,
}
