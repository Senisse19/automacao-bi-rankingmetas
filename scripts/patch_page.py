import os

path = r"c:/Users/victor.senisse.GRUPOSTUDIO/Desktop/Plataforma BI/portal-dashboards-studio/src/app/reports/unidades/page.tsx"

with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "raw_data: u.raw_data" in line:
        continue
    new_lines.append(line)

with open(path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
    
print("Removed raw_data line.")
