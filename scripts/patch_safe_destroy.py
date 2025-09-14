from pathlib import Path
p=Path('1.1.0_birha.py')
s=p.read_text(encoding='utf-8')
old = (
"                    if getattr(self, '_word_driver_active', False) and getattr(self, '_word_driver_in_progress', False):\n"
"                        try:\n"
"                            self._word_driver_cancel_current()\n"
"                        except Exception:\n"
"                            pass\n"
)
new = (
"                    if getattr(self, '_abw_suppress_driver_cancel_once', False):\n"
"                        try:\n"
"                            self._abw_suppress_driver_cancel_once = False\n"
"                        except Exception:\n"
"                            pass\n"
"                    elif getattr(self, '_word_driver_active', False) and getattr(self, '_word_driver_in_progress', False):\n"
"                        try:\n"
"                            self._word_driver_cancel_current()\n"
"                        except Exception:\n"
"                            pass\n"
)
if old in s:
    s=s.replace(old,new)
    p.write_text(s, encoding='utf-8')
    print('Updated safe destroy suppression.')
else:
    print('Pattern not found; no change.')
