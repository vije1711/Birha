from pathlib import Path
p=Path('1.1.0_birha.py')
lines=p.read_text(encoding='utf-8').splitlines()
out=[]
for ln in lines:
    s=ln
    if "_resolve_col(df, COL_NUMBER" in s:
        s = "        _num_col  = _resolve_col(df, COL_NUMBER, 'Number / ਵਚਨ', 'Number')"
    if "_resolve_col(df, COL_GRAMMAR" in s:
        s = "        _gram_col = _resolve_col(df, COL_GRAMMAR, 'Grammar / ਵਯਾਕਰਣ', 'Grammar Case / ਵਯਾਕਰਣ', 'Grammar')"
    if "_resolve_col(df, COL_GENDER" in s:
        s = "        _gen_col  = _resolve_col(df, COL_GENDER, 'Gender / ਲਿੰਗ', 'Gender')"
    if "self.detailed_number_var  = tk.StringVar(value=entry[\"Number / ???\"])" in s:
        s = "        self.detailed_number_var  = tk.StringVar(value=(entry.get(COL_NUMBER)  if isinstance(entry, dict) else None) or \"NA\")"
    if "self.detailed_grammar_var = tk.StringVar(value=entry[\"Grammar / ??????\"])" in s:
        s = "        self.detailed_grammar_var = tk.StringVar(value=(entry.get(COL_GRAMMAR) if isinstance(entry, dict) else None) or \"\")"
    if "self.detailed_gender_var  = tk.StringVar(value=entry[\"Gender / ????\"])" in s:
        s = "        self.detailed_gender_var  = tk.StringVar(value=(entry.get(COL_GENDER)  if isinstance(entry, dict) else None) or \"NA\")"
    if "_add_dropdown(1, \"Number / ???:" in s:
        s = s.replace("Number / ???:", "Number / ਵਚਨ:")
    if "_add_dropdown(2, \"Grammar Case / ??????:" in s:
        s = s.replace("Grammar Case / ??????:", "Grammar Case / ਵਯਾਕਰਣ:")
    if "_add_dropdown(3, \"Gender / ????:" in s:
        s = s.replace("Gender / ????:", "Gender / ਲਿੰਗ:")
    out.append(s)
p.write_text("\n".join(out)+"\n", encoding='utf-8')
print('Patched by line scan.')
