from collections import defaultdict

def check_duplicates(file_path):
    packages = defaultdict(list)

    with open(file_path, 'r') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if "==" in line:
            package, version = line.split("==")
            packages[package.strip()].append(version.strip())

    duplicates = {pkg: versions for pkg, versions in packages.items() if len(versions) > 1}

    if duplicates:
        print("🔍 Duplicate packages found:")
        for pkg, versions in duplicates.items():
            print(f"{pkg}: {versions}")
    else:
        print("✅ No duplicate packages found!")

# Run the function on your requirements.txt
check_duplicates("requirements.txt")
