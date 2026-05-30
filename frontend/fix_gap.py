import re

file_path = r'c:\Users\shrey\OneDrive\Desktop\DTI - Copy\frontend\gap-analysis.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace 1
old_listener = r"""        skillInput\.addEventListener\('keydown', \(e\) => \{
            if \(e\.key === 'Enter'\) \{
                e\.preventDefault\(\);
                const val = skillInput\.value\.trim\(\);
                if \(val && !userSkills\.find\(s => s\.name\.toLowerCase\(\) === val\.toLowerCase\(\)\)\) \{
                    userSkills\.push\(\{ name: val, proficiency: 50 \}\);
                    skillInput\.value = '';
                    renderSkillTags\(\);
                    renderSliders\(\);
                \}
            \}
        \}\);"""

new_listener = r"""        function addCurrentSkill() {
            const val = skillInput.value.trim();
            if (val && !userSkills.find(s => s.name.toLowerCase() === val.toLowerCase())) {
                userSkills.push({ name: val, proficiency: 50 });
                skillInput.value = '';
                renderSkillTags();
                renderSliders();
            }
        }

        skillInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                addCurrentSkill();
            }
        });"""

content = re.sub(old_listener, new_listener, content, flags=re.MULTILINE)

# Replace 2
old_run = r"""        async function runGapAnalysis\(\) \{
            const role = document\.getElementById\('targetRole'\)\.value;"""

new_run = r"""        async function runGapAnalysis() {
            if (skillInput.value.trim()) {
                addCurrentSkill();
            }
            const role = document.getElementById('targetRole').value;"""

content = re.sub(old_run, new_run, content, flags=re.MULTILINE)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
