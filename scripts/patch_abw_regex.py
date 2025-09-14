import re
from pathlib import Path
p=Path('1.1.0_birha.py')
s=p.read_text(encoding='utf-8')
# Replace resolver lines with regex
s=re.sub(r"_resolve_col\(df,\s*COL_NUMBER,\s*'Number / \?\?\?',\s*'Number'\)",
         "_resolve_col(df, COL_NUMBER, 'Number / ਵਚਨ', 'Number')", s)
s=re.sub(r"_resolve_col\(df,\s*COL_GRAMMAR,\s*'Grammar / \?\?\?\?\?\?',\s*'Grammar Case / \?\?\?\?\?\?',\s*'Grammar'\)",
         "_resolve_col(df, COL_GRAMMAR, 'Grammar / ਵਯਾਕਰਣ', 'Grammar Case / ਵਯਾਕਰਣ', 'Grammar')", s)
s=re.sub(r"_resolve_col\(df,\s*COL_GENDER,\s*'Gender / \?\?\?\?',\s*'Gender'\)",
         "_resolve_col(df, COL_GENDER, 'Gender / ਲਿੰਗ', 'Gender')", s)
# Fix combined entry/pos_type: split at backtick-n
s=s.replace("entry = getattr(self, \"current_detailed_entry\", {}) or {}`n        pos_type =",
            "entry = getattr(self, \"current_detailed_entry\", {}) or {}\n        pos_type =")
# Update detailed vars
s=re.sub(r"self\.detailed_number_var\s*=\s*tk\.StringVar\(value=entry\['Number / \?\?\?'\]\)",
         "self.detailed_number_var  = tk.StringVar(value=(entry.get(COL_NUMBER)  if isinstance(entry, dict) else None) or 'NA')", s)
s=re.sub(r"self\.detailed_grammar_var\s*=\s*tk\.StringVar\(value=entry\['Grammar / \?\?\?\?\?\?'\]\)",
         "self.detailed_grammar_var = tk.StringVar(value=(entry.get(COL_GRAMMAR) if isinstance(entry, dict) else None) or '')", s)
s=re.sub(r"self\.detailed_gender_var\s*=\s*tk\.StringVar\(value=entry\['Gender / \?\?\?\?'\]\)",
         "self.detailed_gender_var  = tk.StringVar(value=(entry.get(COL_GENDER)  if isinstance(entry, dict) else None) or 'NA')", s)
# Labels
s=s.replace('"Number / ???:', '"Number / ਵਚਨ:')
s=s.replace('"Grammar Case / ??????:', '"Grammar Case / ਵਯਾਕਰਣ:')
s=s.replace('"Gender / ????:', '"Gender / ਲਿੰਗ:')
p.write_text(s, encoding='utf-8')
print('Patched via regex.')
