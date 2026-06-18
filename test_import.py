import sys
sys.path.insert(0, r'C:\Users\Пользователь\Desktop\ya pidoras')
try:
    import src.bot.handlers.admin
    print("Import succeeded")
except Exception as e:
    print(e)
    import traceback
    traceback.print_exc()