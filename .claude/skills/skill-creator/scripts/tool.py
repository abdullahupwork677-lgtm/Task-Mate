#!/usr/bin/env python3
"""
Skill Creator Tool - Automate skill creation and upgrades

Commands:
  create-new-skill          - Create a brand new skill from scratch
  upgrade-existing-skill    - Upgrade documentation-only skill to expert-level
  validate-skill            - Validate skill structure and completeness
  list-skills               - List all available skills
  analyze-skill             - Analyze skill for improvement opportunities

Based on skill creation best practices and expert-level patterns
"""
import argparse, subprocess, sys, os, json
from pathlib import Path
from datetime import datetime

class Colors:
    GREEN, RED, YELLOW, BLUE, BOLD, END = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[1m', '\033[0m'

def print_success(msg): print(f"{Colors.GREEN}✓{Colors.END} {msg}")
def print_error(msg): print(f"{Colors.RED}✗{Colors.END} {msg}")
def print_warning(msg): print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")
def print_info(msg): print(f"{Colors.BLUE}ℹ{Colors.END} {msg}")
def print_header(msg): print(f"\n{Colors.BOLD}==> {msg}{Colors.END}")

def run_command(cmd: str, timeout: int = 300):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except: return 1, "", "Error"

def create_new_skill(args):
    print_header(f"Creating New Skill: {args.name}")

    skill_name = args.name
    skill_dir = Path(f".claude/skills/{skill_name}")

    # Check if skill already exists
    if skill_dir.exists():
        print_error(f"Skill already exists: {skill_name}")
        print_info("Use 'upgrade-existing-skill' to add automation")
        return 1

    # Create directory structure (Token-Efficient Pattern)
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "scripts").mkdir(exist_ok=True)
    (skill_dir / "reference").mkdir(exist_ok=True)  # For on-demand reference docs
    (skill_dir / "examples").mkdir(exist_ok=True)   # For code examples
    (skill_dir / "assets").mkdir(exist_ok=True)     # For templates/configs

    print_success(f"Created directory: {skill_dir}")
    print_success("Created folders: scripts/, reference/, examples/, assets/")

    # Generate tool.py template
    tool_py_content = f'''#!/usr/bin/env python3
"""
{skill_name.replace('-', ' ').title()} Tool

Commands:
  check-prerequisites  - Check if required tools are installed
  test                 - Comprehensive testing suite

TODO: Add more commands based on skill purpose
"""
import argparse, subprocess, sys

class Colors:
    GREEN, RED, YELLOW, BLUE, BOLD, END = '\\033[92m', '\\033[91m', '\\033[93m', '\\033[94m', '\\033[1m', '\\033[0m'

def print_success(msg): print(f"{{Colors.GREEN}}✓{{Colors.END}} {{msg}}")
def print_error(msg): print(f"{{Colors.RED}}✗{{Colors.END}} {{msg}}")
def print_info(msg): print(f"{{Colors.BLUE}}ℹ{{Colors.END}} {{msg}}")
def print_header(msg): print(f"\\n{{Colors.BOLD}}==> {{msg}}{{Colors.END}}")

def run_command(cmd: str, timeout: int = 300):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except: return 1, "", "Error"

def check_prerequisites(args):
    print_header("Checking Prerequisites")
    # TODO: Implement prerequisite checks
    print_success("Prerequisites OK")
    return 0

def run_tests(args):
    print_header("Comprehensive Testing")
    # TODO: Implement comprehensive tests
    print_success("All tests passed")
    return 0

def main():
    parser = argparse.ArgumentParser(description='{skill_name.replace("-", " ").title()} Tool')
    subparsers = parser.add_subparsers(dest='command')

    subparsers.add_parser('check-prerequisites')
    subparsers.add_parser('test')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    commands = {{
        'check-prerequisites': check_prerequisites,
        'test': run_tests
    }}

    return commands.get(args.command, lambda a: 1)(args)

if __name__ == '__main__':
    sys.exit(main())
'''

    tool_py_path = skill_dir / "scripts/tool.py"
    with open(tool_py_path, 'w') as f:
        f.write(tool_py_content)

    os.chmod(tool_py_path, 0o755)
    print_success(f"Created: {tool_py_path}")

    # Generate SKILL.md (Token-Efficient Format)
    skill_md_content = f'''---
name: {skill_name}
description: Complete [domain] automation with 8 commands - [command1], [command2], [command3], [command4], [command5], [command6], [command7], [command8]. Use when [use case scenario] without [expertise] needed ([X-Y]% time savings, [key benefit 1], [key benefit 2]).
---

# {skill_name.replace('-', ' ').title()}

**[Tagline] - No [expertise] needed!**

**Category:** [Category Name]
**Time Savings:** [X-Y]% reduction
**Quality:** Production-ready

---

## 📋 Quick Instructions

1. **[Step 1 Name]**
   ```text
   - [Description or condition 1]
   - [Description or condition 2]
   ```

2. **[Step 2 Name]**
   ```bash
   python3 scripts/tool.py [command] --[arg] [value]
   ```

3. **[Step 3 Name]**
   ```bash
   python3 scripts/tool.py [another-command]
   ```

4. **[Step 4 Name]**
   ```bash
   python3 scripts/tool.py test
   ```

---

## 🛠️ Commands (8 total)

**Location:** `scripts/tool.py`

```bash
python3 scripts/tool.py check-prerequisites
python3 scripts/tool.py [command1]
python3 scripts/tool.py [command2]
python3 scripts/tool.py [command3]
python3 scripts/tool.py [command4]
python3 scripts/tool.py [command5]
python3 scripts/tool.py [command6]
python3 scripts/tool.py test
```

---

## 📁 On-Demand Resources

### [Resource 1 Name]
- **File:** `reference/[filename].md`
- **When:** [When to load this]
- **Contains:** [What's inside]

### [Resource 2 Name]
- **File:** `examples/[filename].py`
- **When:** [When to load this]
- **Contains:** [What's inside]

### [Resource 3 Name]
- **File:** `reference/[filename].md`
- **When:** [When to load this]
- **Contains:** [What's inside]

---

## 🚀 Common Workflows

### Workflow 1: [Use Case Name]
```bash
# Step 1: [Description]
python3 scripts/tool.py [command1]

# Step 2: [Description]
python3 scripts/tool.py [command2]

# Step 3: [Description]
python3 scripts/tool.py test
```

### Workflow 2: [Use Case Name]
```bash
python3 scripts/tool.py [command3]
python3 scripts/tool.py [command4]
```

---

## 💡 Token Efficiency

**Before:** [X] lines (all embedded) ❌
**After:** ~[Y] lines (references only) ✅
**Savings:** [Z]% reduction!

---

**Status:** Production-ready ✅
**[Key benefit]!** [emoji]
'''

    skill_md_path = skill_dir / "SKILL.md"
    with open(skill_md_path, 'w') as f:
        f.write(skill_md_content)

    print_success(f"Created: {skill_md_path}")

    # Generate README.md (Token-Efficient Format)
    readme_content = f'''---
name: {skill_name}
description: Complete [domain] automation with 8 commands - [command1], [command2], [command3], [command4], [command5], [command6], [command7], [command8]. Use when [use case scenario] without [expertise] needed ([X-Y]% time savings, [key benefit 1], [key benefit 2]).
---

# {skill_name.replace('-', ' ').title()} - Quick Start

**[Tagline] - No [expertise] needed!**

## 🚀 Quick Usage

### 1. [Step 1 Name]
```bash
python3 scripts/tool.py check-prerequisites
```
**Output:** [Expected output]

### 2. [Step 2 Name]
```bash
python3 scripts/tool.py [command1] --[arg] [value]
```
**Output:** [Expected output]

### 3. [Step 3 Name]
```bash
python3 scripts/tool.py test
```

---

## 💡 Common Workflows

### Workflow 1: [Use Case Name]
```bash
1. python3 scripts/tool.py [command1]
2. python3 scripts/tool.py [command2]
3. python3 scripts/tool.py test
```

### Workflow 2: [Use Case Name]
```bash
python3 scripts/tool.py [command3]
python3 scripts/tool.py [command4]
```

---

## 🆘 Troubleshooting

### Issue 1: [Common Problem]
**Fix:** [Solution]

### Issue 2: [Common Problem]
**Fix:** [Solution]

---

## ✨ Features

- ✅ No [expertise] required
- ✅ [Key benefit 1]
- ✅ [Key benefit 2]
- ✅ Token-efficient
- ✅ Production-ready

---

**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}
**Status:** Production-ready ✅
**No [expertise] needed!** 🚀
'''

    readme_path = skill_dir / "README.md"
    with open(readme_path, 'w') as f:
        f.write(readme_content)

    print_success(f"Created: {readme_path}")

    # Create placeholder files in reference/, examples/, assets/
    (skill_dir / "reference/.gitkeep").touch()
    (skill_dir / "examples/.gitkeep").touch()
    (skill_dir / "assets/.gitkeep").touch()

    # Create README for reference folder
    ref_readme = skill_dir / "reference/README.md"
    with open(ref_readme, 'w') as f:
        f.write('''# Reference Documentation

**Purpose:** On-demand reference files loaded only when needed.

## Add Files Here:

- `[topic]-guide.md` - Best practices guides
- `[topic]-patterns.md` - Implementation patterns
- `common-errors.md` - Troubleshooting guide
- `[topic]-config.md` - Configuration examples

**Token Efficiency:** Reference files are only loaded when specifically needed, not upfront!
''')

    # Create README for examples folder
    ex_readme = skill_dir / "examples/README.md"
    with open(ex_readme, 'w') as f:
        f.write('''# Code Examples

**Purpose:** On-demand code examples loaded only when needed.

## Add Files Here:

- `[pattern]-example.py` - Complete code examples
- `[feature]-template.py` - Copy-paste templates
- `[integration]-setup.py` - Integration examples

**Token Efficiency:** Examples are only loaded when user needs them, not upfront!
''')

    # Create README for assets folder
    assets_readme = skill_dir / "assets/README.md"
    with open(assets_readme, 'w') as f:
        f.write('''# Assets

**Purpose:** Templates, configs, and other assets for on-demand use.

## Add Files Here:

- `[resource]-template.yaml` - Configuration templates
- `folder-structure.txt` - Directory layouts
- `checklist.md` - Validation checklists

**Token Efficiency:** Assets are only loaded when specifically needed!
''')

    print_success("Created placeholder files in reference/, examples/, assets/")

    print_header("Next Steps")
    print_info("1. Update YAML frontmatter in SKILL.md with comprehensive description")
    print_info("   - Include: when to use, trigger phrases, what it does, key benefits")
    print_info("2. Replace [placeholders] in SKILL.md with actual content")
    print_info("3. Implement 8 commands in scripts/tool.py")
    print_info("4. Add reference docs, examples, and assets to respective folders")
    print_info("5. Update README.md with real workflows and troubleshooting")
    print_info("6. Test: python3 scripts/tool.py test")
    print_info("")
    print_success("✅ Token-efficient skill structure created!")
    print_info("📚 Add code to reference/, examples/, assets/ folders (loaded on-demand)")

    return 0

def upgrade_existing_skill(args):
    print_header(f"Upgrading Skill to Expert-Level: {args.name}")

    skill_name = args.name
    skill_dir = Path(f".claude/skills/{skill_name}")

    # Check if skill exists
    if not skill_dir.exists():
        print_error(f"Skill not found: {skill_name}")
        print_info("Use 'create-new-skill' to create a new skill")
        return 1

    # Check if already has tool.py
    tool_py_path = skill_dir / "scripts/tool.py"
    if tool_py_path.exists():
        print_warning(f"Skill already has tool.py: {tool_py_path}")
        print_info("Skipping upgrade (already expert-level)")
        return 0

    # Create scripts directory
    (skill_dir / "scripts").mkdir(exist_ok=True)

    # Read existing SKILL.md to understand the skill
    skill_md_path = skill_dir / "SKILL.md"
    if not skill_md_path.exists():
        print_error("SKILL.md not found")
        return 1

    with open(skill_md_path, 'r') as f:
        skill_content = f.read()

    print_info("Analyzing existing documentation...")

    # Generate expert-level tool.py
    commands = args.commands if args.commands else [
        'check-prerequisites',
        'setup',
        'configure',
        'deploy',
        'test',
        'health-check',
        'troubleshoot',
        'cleanup'
    ]

    tool_py_content = f'''#!/usr/bin/env python3
"""
{skill_name.replace('-', ' ').title()} Tool - Expert-Level Automation

Commands:
'''

    for cmd in commands:
        tool_py_content += f"  {cmd:25} - TODO: Add description\\n"

    tool_py_content += '''
Based on best practices and expert patterns
"""
import argparse, subprocess, sys, os
from pathlib import Path

class Colors:
    GREEN, RED, YELLOW, BLUE, BOLD, END = '\\033[92m', '\\033[91m', '\\033[93m', '\\033[94m', '\\033[1m', '\\033[0m'

def print_success(msg): print(f"{Colors.GREEN}✓{Colors.END} {msg}")
def print_error(msg): print(f"{Colors.RED}✗{Colors.END} {msg}")
def print_warning(msg): print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")
def print_info(msg): print(f"{Colors.BLUE}ℹ{Colors.END} {msg}")
def print_header(msg): print(f"\\n{Colors.BOLD}==> {msg}{Colors.END}")

def run_command(cmd: str, timeout: int = 300):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except: return 1, "", "Error"

'''

    # Generate command functions
    for cmd in commands:
        func_name = cmd.replace('-', '_')
        tool_py_content += f'''def {func_name}(args):
    print_header("{cmd.replace('-', ' ').title()}")
    # TODO: Implement {cmd}
    print_success("{cmd} complete")
    return 0

'''

    # Generate main function
    tool_py_content += '''def main():
    parser = argparse.ArgumentParser(description='Expert-Level Automation Tool')
    subparsers = parser.add_subparsers(dest='command')

'''

    for cmd in commands:
        tool_py_content += f"    subparsers.add_parser('{cmd}')\n"

    tool_py_content += '''
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    commands = {
'''

    for cmd in commands:
        func_name = cmd.replace('-', '_')
        tool_py_content += f"        '{cmd}': {func_name},\n"

    tool_py_content += '''    }

    return commands.get(args.command, lambda a: 1)(args)

if __name__ == '__main__':
    sys.exit(main())
'''

    # Write tool.py
    with open(tool_py_path, 'w') as f:
        f.write(tool_py_content)

    os.chmod(tool_py_path, 0o755)
    print_success(f"Created: {tool_py_path}")
    print_info(f"Commands: {len(commands)}")

    # Update SKILL.md if needed
    print_info("Updating SKILL.md...")

    # Add upgrade notice if not already present
    if "Expert-Level Automation" not in skill_content:
        upgrade_notice = f"\n\n## 🚀 Expert-Level Automation (Upgraded)\n\n**Upgraded:** {datetime.now().strftime('%Y-%m-%d')}\n\n**Automation Added:** {len(commands)} commands in `scripts/tool.py`\n\n"

        # Insert after YAML frontmatter
        lines = skill_content.split('\n')
        yaml_end = 0
        for i, line in enumerate(lines):
            if i > 0 and line.strip() == '---':
                yaml_end = i + 1
                break

        lines.insert(yaml_end, upgrade_notice)
        skill_content = '\n'.join(lines)

        with open(skill_md_path, 'w') as f:
            f.write(skill_content)

        print_success("Updated SKILL.md with upgrade notice")

    print_header("Upgrade Complete")
    print_success(f"Skill upgraded to expert-level with {len(commands)} commands")
    print_info("Next steps:")
    print_info("1. Implement command functions in scripts/tool.py")
    print_info("2. Update README.md with command examples")
    print_info("3. Test: python3 scripts/tool.py test")

    return 0

def validate_skill(args):
    print_header(f"Validating Skill: {args.name}")

    skill_name = args.name
    skill_dir = Path(f".claude/skills/{skill_name}")

    if not skill_dir.exists():
        print_error(f"Skill not found: {skill_name}")
        return 1

    issues = []
    warnings = []

    # Check SKILL.md
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        with open(skill_md, 'r') as f:
            content = f.read()

        if not content.startswith('---\nname:'):
            issues.append("SKILL.md missing YAML frontmatter")

        if 'TODO' in content:
            warnings.append("SKILL.md contains TODO items")

        print_success("SKILL.md exists")
    else:
        issues.append("SKILL.md not found")

    # Check README.md
    readme = skill_dir / "README.md"
    if readme.exists():
        with open(readme, 'r') as f:
            content = f.read()

        if not content.startswith('---\nname:'):
            issues.append("README.md missing YAML frontmatter")

        print_success("README.md exists")
    else:
        warnings.append("README.md not found (recommended)")

    # Check tool.py
    tool_py = skill_dir / "scripts/tool.py"
    if tool_py.exists():
        # Check if executable
        if os.access(tool_py, os.X_OK):
            print_success("scripts/tool.py exists and is executable")
        else:
            warnings.append("scripts/tool.py not executable")

        # Count commands
        with open(tool_py, 'r') as f:
            content = f.read()

        command_count = content.count("subparsers.add_parser(")
        print_info(f"Commands implemented: {command_count}")

        if command_count < 4:
            warnings.append(f"Only {command_count} commands (recommended: 4-8)")
    else:
        warnings.append("scripts/tool.py not found (documentation-only skill)")

    # Print results
    print_header("Validation Results")

    if issues:
        print_error(f"Issues found: {len(issues)}")
        for issue in issues:
            print(f"  ❌ {issue}")
    else:
        print_success("No critical issues")

    if warnings:
        print_warning(f"Warnings: {len(warnings)}")
        for warning in warnings:
            print(f"  ⚠️  {warning}")

    if not issues and not warnings:
        print_success("✅ Skill is production-ready!")

    return 0 if not issues else 1

def list_skills(args):
    print_header("Available Skills")

    skills_dir = Path(".claude/skills")
    if not skills_dir.exists():
        print_error("Skills directory not found")
        return 1

    skills = sorted([d.name for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith('.')])

    print(f"\nTotal skills: {len(skills)}\n")

    for skill in skills:
        skill_dir = skills_dir / skill
        has_tool = (skill_dir / "scripts/tool.py").exists()
        has_skill_md = (skill_dir / "SKILL.md").exists()
        has_readme = (skill_dir / "README.md").exists()

        status = "✅ Expert" if has_tool else "📖 Docs"

        print(f"  {status:12} {skill}")

        if args.verbose:
            if has_skill_md:
                print(f"              ├── SKILL.md")
            if has_readme:
                print(f"              ├── README.md")
            if has_tool:
                print(f"              └── scripts/tool.py")
            print()

    # Summary
    expert_count = sum(1 for s in skills if (skills_dir / s / "scripts/tool.py").exists())
    docs_count = len(skills) - expert_count

    print(f"\n📊 Summary:")
    print(f"   Expert-level (with tool.py): {expert_count}")
    print(f"   Documentation-only: {docs_count}")

    if docs_count > 0:
        print(f"\n💡 Tip: Upgrade documentation-only skills with:")
        print(f"   python3 tool.py upgrade-existing-skill --name <skill-name>")

    return 0

def analyze_skill(args):
    print_header(f"Analyzing Skill: {args.name}")

    skill_name = args.name
    skill_dir = Path(f".claude/skills/{skill_name}")

    if not skill_dir.exists():
        print_error(f"Skill not found: {skill_name}")
        return 1

    print_info("Analyzing skill structure...")

    # File sizes
    skill_md = skill_dir / "SKILL.md"
    readme = skill_dir / "README.md"
    tool_py = skill_dir / "scripts/tool.py"

    if skill_md.exists():
        size = skill_md.stat().st_size
        lines = len(open(skill_md).readlines())
        print(f"SKILL.md: {lines} lines, {size} bytes")

    if readme.exists():
        size = readme.stat().st_size
        lines = len(open(readme).readlines())
        print(f"README.md: {lines} lines, {size} bytes")

    if tool_py.exists():
        size = tool_py.stat().st_size
        lines = len(open(tool_py).readlines())
        print(f"tool.py: {lines} lines, {size} bytes")

        # Analyze commands
        with open(tool_py, 'r') as f:
            content = f.read()

        commands = []
        for line in content.split('\n'):
            if "subparsers.add_parser(" in line:
                cmd = line.split("'")[1]
                commands.append(cmd)

        print(f"\nCommands ({len(commands)}):")
        for cmd in commands:
            print(f"  - {cmd}")

    # Improvement suggestions
    print_header("Improvement Suggestions")

    suggestions = []

    if not tool_py.exists():
        suggestions.append("Add scripts/tool.py for automation (80-90% time savings)")

    if tool_py.exists():
        with open(tool_py, 'r') as f:
            content = f.read()

        if "TODO" in content:
            suggestions.append("Complete TODO items in tool.py")

        command_count = content.count("subparsers.add_parser(")
        if command_count < 4:
            suggestions.append(f"Add more commands (current: {command_count}, recommended: 4-8)")

    if skill_md.exists():
        with open(skill_md, 'r') as f:
            content = f.read()

        if "TODO" in content:
            suggestions.append("Complete TODO items in SKILL.md")

        if not content.startswith('---\nname:'):
            suggestions.append("Add YAML frontmatter to SKILL.md")

    if not readme.exists():
        suggestions.append("Create README.md with quick start guide")

    if suggestions:
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
    else:
        print_success("No improvement suggestions - skill is well-structured!")

    return 0

def main():
    parser = argparse.ArgumentParser(description='Skill Creator Tool')
    subparsers = parser.add_subparsers(dest='command')

    # create-new-skill
    create_parser = subparsers.add_parser('create-new-skill', help='Create a brand new skill')
    create_parser.add_argument('--name', required=True, help='Skill name (e.g., my-awesome-skill)')

    # upgrade-existing-skill
    upgrade_parser = subparsers.add_parser('upgrade-existing-skill', help='Upgrade to expert-level')
    upgrade_parser.add_argument('--name', required=True, help='Skill name to upgrade')
    upgrade_parser.add_argument('--commands', nargs='+', help='Custom command list')

    # validate-skill
    validate_parser = subparsers.add_parser('validate-skill', help='Validate skill structure')
    validate_parser.add_argument('--name', required=True, help='Skill name to validate')

    # list-skills
    list_parser = subparsers.add_parser('list-skills', help='List all skills')
    list_parser.add_argument('--verbose', '-v', action='store_true', help='Show file structure')

    # analyze-skill
    analyze_parser = subparsers.add_parser('analyze-skill', help='Analyze skill for improvements')
    analyze_parser.add_argument('--name', required=True, help='Skill name to analyze')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        'create-new-skill': create_new_skill,
        'upgrade-existing-skill': upgrade_existing_skill,
        'validate-skill': validate_skill,
        'list-skills': list_skills,
        'analyze-skill': analyze_skill
    }

    return commands.get(args.command, lambda a: 1)(args)

if __name__ == '__main__':
    sys.exit(main())
